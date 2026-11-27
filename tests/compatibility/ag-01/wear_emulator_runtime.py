"""Safe Wear OS emulator runtime verification helper for AG-01 (R04 hardened).

Safety and verification invariants enforced by this module (AG01-AUD-04 & AG-01-R04):
1. Never downloads SDK packages or creates AVDs automatically.
2. Never uses `--force` in recommended `avdmanager create avd` commands so existing AVDs are never overwritten.
3. Refuses to target physical devices (non-`emulator-*` serials) or non-Wear AVDs (e.g. phone/tablet AVDs).
4. Before any device mutation (`adb install`), verifies:
   - Local APK file exists, SHA-256 matches `expected_apk_sha256` (when provided), is resource-only (`0 .dex`, `0 .so`),
     and compiled `AndroidManifest.xml` matches `expected_package`, `expected_wff_version`, and `minSdk`.
   - Running emulator reports a dedicated approved Wear AVD name matching `expected_avd_name`,
     `sys.boot_completed == "1"`, `ro.build.characteristics` contains `"watch"`, and `ro.build.version.sdk`
     satisfies both `>= required_min_sdk` and `== expected_api_level` (when specified).
5. Requires explicit `-s <emulator-serial>` and checks `returncode == 0` and timeout on EVERY `adb` command.
6. Active watch face selection (`verify_active_watchface_selected`):
   - Never uses substring or loose `\b` regex matching across `dumpsys wallpaper`.
   - Parses the active current-user wallpaper component binding (`mWallpaperComponent=ComponentInfo{<pkg>/<cls>}`).
   - Rejects inactive/history references (`previousPackage=`, `fallback`, etc.) and package suffix collisions (`<pkg>.other`).
   - Returns `status="UNKNOWN", selected=False` if the active component or WFF host dumpsys format cannot be confirmed.
7. Power and display state (`parse_power_and_display_state`):
   - Requires BOTH `mWakefulness` and display state (`ON` / `DOZE` / `DOZE_SUSPEND` / `OFF`) to be explicitly parsed.
   - If either is `UNKNOWN`, returns `status="UNKNOWN", is_active=False, is_aod=False`.
   - `is_active` is True ONLY when `wakefulness == "Awake"` AND `display_state == "ON"`.
   - `is_aod` is True ONLY when `wakefulness in ("Dozing", "Asleep")` AND `display_state in ("DOZE", "DOZE_SUSPEND")`
     (`Dozing` + `OFF` is rejected as `is_aod=False`).
8. Transition recording and cleanup:
   - Verifies pulled MP4 exists, has non-trivial size, and contains a valid ISO BMFF `ftyp` header box.
   - Explicitly verifies final return to Active (`wakefulness == "Awake"` AND `display_state == "ON"`) after AOD capture.
   - Always terminates any lingering `screenrecord`, wakes display, and removes temporary `/sdcard/*.mp4` in `finally`.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from check_apk import analyzer_path, inspect_entries

WFF_MIN_SDK = {
    2: 34,
    3: 35,
    4: 36,
    5: 37,
}

ALLOWED_DEDICATED_WEAR_AVD_NAMES = {
    "aura_wear36_round",
    "aura_wear37_round",
    "aura_wear35_round",
    "aura_wear34_round",
}

PROHIBITED_AVD_NAMES = {
    "Medium_Phone_API_36.1",
    "Medium_Phone",
}

RECOMMENDED_WEAR_AVD_PLANS = [
    {
        "stage": 1,
        "wff_version": 4,
        "min_sdk": 36,
        "expected_api_level": 36,
        "avd_name": "aura_wear36_round",
        "package_id": "system-images;android-36;android-wear-signed;x86_64",
        "device_profile": "wearos_large_round",
        "priority": "P0 (Primary WFF 4: Variant continuity, Reference, Gyro)",
    },
    {
        "stage": 2,
        "wff_version": 5,
        "min_sdk": 37,
        "expected_api_level": 37,
        "avd_name": "aura_wear37_round",
        "package_id": "system-images;android-37.0;android-wear-signed;x86_64",
        "device_profile": "wearos_large_round",
        "priority": "P0 (Primary WFF 5: Group/ComplicationSlot blendMode)",
    },
    {
        "stage": 3,
        "wff_version": 3,
        "min_sdk": 35,
        "expected_api_level": 35,
        "avd_name": "aura_wear35_round",
        "package_id": "system-images;android-35-ext15;android-wear;x86_64",
        "device_profile": "wearos_large_round",
        "priority": "P1 (Optional expansion: WFF 3 Part blendMode static AOD)",
    },
    {
        "stage": 4,
        "wff_version": 2,
        "min_sdk": 34,
        "expected_api_level": 34,
        "avd_name": "aura_wear34_round",
        "package_id": "system-images;android-34;android-wear;x86_64",
        "device_profile": "wearos_large_round",
        "priority": "P1 (Optional expansion: WFF 2 baseline static AOD)",
    },
]

# Strict Android package identifier pattern (dot-separated Java identifiers)
PACKAGE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+$")

# Strict active wallpaper binding lines (anchored to line start after whitespace; never matches previousComponent/history)
ACTIVE_WALLPAPER_COMPONENT_RE = re.compile(
    r"^\s*mWallpaperComponent=ComponentInfo\{([A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+)/([^\}\s]+)\}\s*$"
)
CURRENT_USER_RE = re.compile(r"^\s*(?:mCurrentUserId|Current user ID)\s*[:=]\s*(\d+)\s*$")
USER_WALLPAPER_HEADER_RE = re.compile(r"^\s*WallpaperData\s+\S+\s+userId=(\d+)\b")

# Known declarative WFF system host packages that may bind a declarative watch face package via an explicit active field
KNOWN_WFF_HOST_PACKAGES = {
    "com.google.wear.watchface.runtime",
    "com.google.android.wearable.watchface.rwf",
    "com.android.systemui",
}
ACTIVE_WFF_BOUND_PACKAGE_RE = re.compile(
    r"^\s*(?:activeWatchFacePackage|mWatchFacePackage|boundWatchFacePackage)=([A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+)\s*$"
)


class UnsafeTargetError(RuntimeError):
    """Raised when a command attempts to touch a physical watch/phone, non-Wear AVD, or mismatched APK/device."""


class RuntimeVerificationIncompleteError(RuntimeError):
    """Raised when runtime state or dumpsys format is UNKNOWN/unconfirmed and cannot be approved as PASS."""


def validate_emulator_serial(serial):
    """Allow only Android emulator serials (emulator-<port>); hard-reject physical devices or blank serials."""
    if not serial or not re.fullmatch(r"emulator-\d+", serial.strip()):
        raise UnsafeTargetError(
            f"Refusing target serial '{serial}': only isolated Android emulators ('emulator-<port>') are allowed; "
            "physical watches/phones and implicit adb targeting without -s are prohibited."
        )
    return serial.strip()


def validate_dedicated_wear_avd_name(actual_avd_name, expected_avd_name=None):
    """Verify the running emulator's AVD name is an approved dedicated Wear OS AVD and never an existing phone AVD."""
    clean = (actual_avd_name or "").strip()
    if not clean:
        raise UnsafeTargetError("Refusing emulator: could not determine running AVD name (empty AVD name).")
    if clean in PROHIBITED_AVD_NAMES or "phone" in clean.lower() or "tablet" in clean.lower():
        raise UnsafeTargetError(
            f"Refusing AVD '{clean}': target is a prohibited phone/tablet AVD."
        )
    if clean not in ALLOWED_DEDICATED_WEAR_AVD_NAMES:
        raise UnsafeTargetError(
            f"Refusing AVD '{clean}': not in approved dedicated Wear OS AVD set {sorted(ALLOWED_DEDICATED_WEAR_AVD_NAMES)}."
        )
    if expected_avd_name and clean != expected_avd_name.strip():
        raise UnsafeTargetError(
            f"Running emulator AVD name '{clean}' does not match expected dedicated Wear AVD '{expected_avd_name.strip()}'."
        )
    return clean


def validate_wear_avd_record(avd_record):
    """Ensure an AVD inventory record explicitly proves it is a Wear OS AVD and not a phone/tablet AVD."""
    name = (avd_record or {}).get("name", "")
    tag_abi = ((avd_record or {}).get("tag_abi") or "").lower()
    device = ((avd_record or {}).get("device") or "").lower()
    if "android-wear" not in tag_abi and "wearos" not in device:
        raise UnsafeTargetError(
            f"Refusing AVD '{name}': metadata (device='{avd_record.get('device')}', tag_abi='{avd_record.get('tag_abi')}') "
            "does not identify a Wear OS AVD. Existing phone/tablet AVDs must not be modified or targeted."
        )
    return name


def validate_wear_device_properties(characteristics, sdk_int_raw, required_min_sdk, expected_api_level=None):
    """Verify running emulator reports `watch` hardware characteristics and meets WFF minSdk & expected API level."""
    chars = {token.strip().lower() for token in (characteristics or "").split(",") if token.strip()}
    if "watch" not in chars:
        raise UnsafeTargetError(
            f"Refusing emulator: ro.build.characteristics='{characteristics}' does not contain 'watch'."
        )
    try:
        sdk_int = int((sdk_int_raw or "").strip())
    except ValueError as exc:
        raise UnsafeTargetError(f"Unparseable ro.build.version.sdk='{sdk_int_raw}'") from exc
    if sdk_int < required_min_sdk:
        raise UnsafeTargetError(
            f"Emulator API level {sdk_int} is lower than required minSdk {required_min_sdk}."
        )
    if expected_api_level is not None and sdk_int != int(expected_api_level):
        raise UnsafeTargetError(
            f"Emulator API level {sdk_int} does not match expected target API level {expected_api_level}."
        )
    return sdk_int


def verify_local_apk_before_install(
    apk_path,
    expected_package,
    expected_wff_version,
    expected_apk_sha256=None,
    manifest_printer=None,
):
    """Verify APK existence, SHA-256, resource-only ZIP structure, package name, WFF version, and minSdk before adb install."""
    path = Path(apk_path)
    if not path.is_file():
        raise UnsafeTargetError(f"APK file does not exist: {path}")
    if not expected_package or not PACKAGE_ID_RE.fullmatch(expected_package):
        raise UnsafeTargetError(f"Invalid expected_package identifier: '{expected_package}'")
    if expected_wff_version not in WFF_MIN_SDK:
        raise UnsafeTargetError(f"Unsupported WFF version: {expected_wff_version}")

    apk_bytes = path.read_bytes()
    actual_sha256 = hashlib.sha256(apk_bytes).hexdigest()
    if expected_apk_sha256 and actual_sha256.lower() != expected_apk_sha256.strip().lower():
        raise UnsafeTargetError(
            f"APK SHA-256 mismatch before install: expected {expected_apk_sha256}, got {actual_sha256}"
        )

    with zipfile.ZipFile(path) as archive:
        entries = sorted(archive.namelist())
        entry_errors = inspect_entries(entries)
        if entry_errors:
            raise UnsafeTargetError(f"APK failed resource-only entry verification: {entry_errors}")
        watchface_xml_sha256 = hashlib.sha256(archive.read("res/raw/watchface.xml")).hexdigest()

    if manifest_printer is not None:
        manifest_xml = manifest_printer(path)
    else:
        analyzer = analyzer_path()
        proc = subprocess.run(
            [analyzer, "manifest", "print", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
        if proc.returncode != 0:
            raise UnsafeTargetError(f"apkanalyzer manifest print failed (rc={proc.returncode}): {proc.stderr.strip()}")
        manifest_xml = proc.stdout

    pkg_match = re.search(r'\bpackage="([^"]+)"', manifest_xml)
    actual_pkg = pkg_match.group(1) if pkg_match else ""
    if actual_pkg != expected_package:
        raise UnsafeTargetError(
            f"APK manifest package mismatch: expected '{expected_package}', got '{actual_pkg}'"
        )

    wff_match = re.search(
        r'android:name="com\.google\.wear\.watchface\.format\.version"\s+android:value="(\d+)"',
        manifest_xml,
    )
    actual_wff = int(wff_match.group(1)) if wff_match else None
    if actual_wff != expected_wff_version:
        raise UnsafeTargetError(
            f"APK manifest WFF version mismatch: expected #{expected_wff_version}, got #{actual_wff}"
        )

    min_sdk_match = re.search(r'android:minSdkVersion="(\d+)"', manifest_xml)
    actual_min_sdk = int(min_sdk_match.group(1)) if min_sdk_match else None
    required_min_sdk = WFF_MIN_SDK[expected_wff_version]
    if actual_min_sdk != required_min_sdk:
        raise UnsafeTargetError(
            f"APK manifest minSdkVersion mismatch: expected {required_min_sdk} for WFF#{expected_wff_version}, got {actual_min_sdk}"
        )

    if 'android:hasCode="false"' not in manifest_xml:
        raise UnsafeTargetError("APK manifest is missing android:hasCode=\"false\"")

    return {
        "apk_path": str(path),
        "apk_sha256": actual_sha256,
        "watchface_xml_sha256": watchface_xml_sha256,
        "package_id": actual_pkg,
        "wff_version": actual_wff,
        "min_sdk": actual_min_sdk,
    }


def parse_power_and_display_state(dumpsys_power, dumpsys_display=""):
    """Strictly parse Awake vs Doze/AOD state from `dumpsys power` and `dumpsys display` outputs (AG01-AUD-04).

    Rules:
    - Both `wakefulness` and `display_state` must be explicitly parsed from actual dumpsys fields.
    - If either is `UNKNOWN`, `status="UNKNOWN"`, `is_active=False`, `is_aod=False` (never approves UNKNOWN display).
    - `is_active` is True ONLY when `wakefulness == "Awake"` AND `display_state == "ON"`.
    - `is_aod` is True ONLY when `wakefulness in ("Dozing", "Asleep")` AND `display_state in ("DOZE", "DOZE_SUSPEND")`.
      (`Dozing` + `OFF` is screen-off, NOT AOD, so `is_aod=False`).
    """
    wake_match = re.search(r"^\s*mWakefulness=([A-Za-z_]+)\s*$", dumpsys_power or "", re.MULTILINE)
    if not wake_match:
        wake_match = re.search(r"\bmWakefulness=([A-Za-z_]+)\b", dumpsys_power or "")
    wakefulness = wake_match.group(1) if wake_match else "UNKNOWN"

    display_match = re.search(r"Display Power:\s*state=([A-Z_]+)\b", dumpsys_power or "")
    if not display_match:
        display_match = re.search(r"\bmScreenState=([A-Z_]+)\b", dumpsys_display or "")
    if not display_match:
        display_match = re.search(r"Display State:\s*([A-Z_]+)\b", dumpsys_display or "")
    display_state = display_match.group(1) if display_match else "UNKNOWN"

    if wakefulness == "UNKNOWN" or display_state == "UNKNOWN":
        return {
            "status": "UNKNOWN",
            "wakefulness": wakefulness,
            "display_state": display_state,
            "is_active": False,
            "is_aod": False,
        }

    is_active = wakefulness == "Awake" and display_state == "ON"
    is_aod = wakefulness in ("Dozing", "Asleep") and display_state in ("DOZE", "DOZE_SUSPEND")
    if is_active:
        status = "ACTIVE"
    elif is_aod:
        status = "AOD"
    else:
        status = "TRANSITION_OR_OFF"

    return {
        "status": status,
        "wakefulness": wakefulness,
        "display_state": display_state,
        "is_active": is_active,
        "is_aod": is_aod,
    }


def verify_active_watchface_selected(dumpsys_wallpaper, expected_package):
    """Verify from `dumpsys wallpaper` that `expected_package` is the active bound watch face (AG01-AUD-04).

    Never performs loose substring or regex `\b` searches across the dump.
    Extracts only the current user's active `mWallpaperComponent=ComponentInfo{<pkg>/<cls>}` record:
    - Rejects inactive history lines such as `previousPackage=<expected_package>`.
    - Rejects package prefix/suffix collisions such as `<expected_package>.other/.Face` (requires exact `==`).
    - If `mWallpaperComponent` is absent, ambiguous across users, or belongs to a WFF host without an explicit
      confirmed active package field, returns `status="UNKNOWN", selected=False`.
    """
    if not expected_package or not PACKAGE_ID_RE.fullmatch(expected_package):
        raise ValueError(f"expected_package must be a valid Android package name, got '{expected_package}'")

    lines = (dumpsys_wallpaper or "").splitlines()
    current_user = None
    for line in lines:
        m_user = CURRENT_USER_RE.match(line)
        if m_user:
            current_user = m_user.group(1)
            break

    # Parse per-user or top-level active mWallpaperComponent bindings
    section_user = None
    bindings = []
    for line in lines:
        m_header = USER_WALLPAPER_HEADER_RE.match(line)
        if m_header:
            section_user = m_header.group(1)
            continue
        m_comp = ACTIVE_WALLPAPER_COMPONENT_RE.match(line)
        if m_comp:
            pkg, cls = m_comp.group(1), m_comp.group(2)
            bindings.append({
                "user_id": section_user,
                "package": pkg,
                "class_name": cls,
                "component": f"{pkg}/{cls}",
                "bound_wff_package": None,
                "raw_line": line.strip(),
            })
            continue
        m_bound = ACTIVE_WFF_BOUND_PACKAGE_RE.match(line)
        if m_bound and bindings:
            bindings[-1]["bound_wff_package"] = m_bound.group(1)

    if not bindings:
        return {
            "status": "UNKNOWN",
            "selected": False,
            "expected_package": expected_package,
            "active_package": None,
            "active_component": None,
            "reason": "No active mWallpaperComponent=ComponentInfo{...} line found in dumpsys wallpaper",
        }

    if current_user is not None:
        user_filtered = [b for b in bindings if b["user_id"] in (current_user, None)]
        if user_filtered:
            bindings = user_filtered

    # If multiple bindings remain with different components, treat as ambiguous UNKNOWN
    unique_components = {(b["package"], b["class_name"], b["bound_wff_package"]) for b in bindings}
    if len(unique_components) != 1:
        return {
            "status": "UNKNOWN",
            "selected": False,
            "expected_package": expected_package,
            "active_package": None,
            "active_component": None,
            "reason": f"Ambiguous multiple mWallpaperComponent bindings in dumpsys wallpaper: {[b['component'] for b in bindings]}",
        }

    active = bindings[0]
    active_pkg = active["package"]
    active_comp = active["component"]

    # Case 1: Direct exact component package match (strict equality `==` prevents `.other` suffix collisions)
    if active_pkg == expected_package:
        return {
            "status": "SELECTED",
            "selected": True,
            "expected_package": expected_package,
            "active_package": active_pkg,
            "active_component": active_comp,
            "matched_lines": [active["raw_line"]],
        }

    # Case 2: Known WFF declarative host package
    if active_pkg in KNOWN_WFF_HOST_PACKAGES:
        bound_pkg = active["bound_wff_package"]
        if bound_pkg is None:
            return {
                "status": "UNKNOWN",
                "selected": False,
                "expected_package": expected_package,
                "active_package": active_pkg,
                "active_component": active_comp,
                "reason": f"WFF host '{active_comp}' is active, but bound watch face package format is unconfirmed in dumpsys wallpaper",
            }
        if bound_pkg == expected_package:
            return {
                "status": "SELECTED",
                "selected": True,
                "expected_package": expected_package,
                "active_package": bound_pkg,
                "active_component": active_comp,
                "matched_lines": [active["raw_line"], f"boundWatchFacePackage={bound_pkg}"],
            }
        return {
            "status": "NOT_SELECTED",
            "selected": False,
            "expected_package": expected_package,
            "active_package": bound_pkg,
            "active_component": active_comp,
            "reason": f"WFF host '{active_comp}' is bound to '{bound_pkg}', not '{expected_package}'",
        }

    # Case 3: Another watch face package is active (even if expected_package appears in previousPackage/history)
    return {
        "status": "NOT_SELECTED",
        "selected": False,
        "expected_package": expected_package,
        "active_package": active_pkg,
        "active_component": active_comp,
        "reason": f"Active mWallpaperComponent package is '{active_pkg}', not '{expected_package}'",
    }


def validate_mp4_bytes(data, min_size_bytes=1024):
    """Verify pulled screenrecord MP4 bytes are non-empty, meet minimum size, and carry an ISO BMFF `ftyp` box."""
    if not data or len(data) < min_size_bytes:
        raise RuntimeError(
            f"Invalid or truncated MP4 recording: size={0 if not data else len(data)} bytes (expected >= {min_size_bytes} bytes)"
        )
    if len(data) < 12 or data[4:8] != b"ftyp":
        raise RuntimeError("Invalid MP4 file header: missing ISO Base Media File Format 'ftyp' box at bytes 4..8")
    return len(data)


def build_safe_setup_commands(stage_plan):
    """Build safe, non-destructive setup commands (explicitly NO `--force` flag) for user approval."""
    pkg = stage_plan["package_id"]
    avd = stage_plan["avd_name"]
    dev = stage_plan["device_profile"]
    return [
        f'sdkmanager "{pkg}"',
        f'avdmanager create avd -n {avd} -k "{pkg}" -d {dev}',
        f"emulator -avd {avd} -no-snapshot -no-boot-anim",
    ]


def build_safe_runtime_verification_plan(
    serial,
    apk_path,
    package_id,
    wff_version,
    output_dir,
    expected_avd_name=None,
    expected_apk_sha256=None,
):
    """Generate an explicit `-s <serial>` step-by-step runtime verification command sequence."""
    safe_serial = validate_emulator_serial(serial)
    min_sdk = WFF_MIN_SDK[wff_version]
    default_avd = f"aura_wear{min_sdk}_round"
    avd_name = validate_dedicated_wear_avd_name(expected_avd_name or default_avd)
    out_dir = Path(output_dir).as_posix()
    apk_str = Path(apk_path).as_posix()
    remote_video = f"/sdcard/ag01_wff{wff_version}_aod_transition.mp4"
    return {
        "serial": safe_serial,
        "expected_avd_name": avd_name,
        "package_id": package_id,
        "wff_version": wff_version,
        "required_min_sdk": min_sdk,
        "expected_api_level": min_sdk,
        "expected_apk_sha256": expected_apk_sha256,
        "steps": [
            {
                "step": "0_precheck_local_apk_manifest_and_hash",
                "commands": [
                    f"apkanalyzer manifest print \"{apk_str}\"",
                ],
                "pass_criteria": (
                    f"APK exists, SHA-256 matches {expected_apk_sha256 or '<computed>'}, 0 .dex/0 .so, "
                    f"manifest package='{package_id}', WFF version='{wff_version}', minSdkVersion='{min_sdk}'"
                ),
            },
            {
                "step": "1_verify_wear_emulator_avd_and_props",
                "commands": [
                    f"adb -s {safe_serial} wait-for-device",
                    f"adb -s {safe_serial} shell getprop ro.boot.qemu.avd_name",
                    f"adb -s {safe_serial} shell getprop sys.boot_completed",
                    f"adb -s {safe_serial} shell getprop ro.build.characteristics",
                    f"adb -s {safe_serial} shell getprop ro.build.version.sdk",
                ],
                "pass_criteria": (
                    f"All commands rc=0, avd_name='{avd_name}', boot_completed=1, "
                    f"characteristics contains 'watch', sdk == {min_sdk}"
                ),
            },
            {
                "step": "2_install_isolated_apk",
                "commands": [
                    f"adb -s {safe_serial} install -r \"{apk_str}\"",
                    f"adb -s {safe_serial} shell pm list packages {package_id}",
                ],
                "pass_criteria": f"Both commands rc=0 and package:{package_id} present on {safe_serial}",
            },
            {
                "step": "3_select_and_confirm_watchface",
                "commands": [
                    f"adb -s {safe_serial} shell dumpsys package {package_id}",
                    f"adb -s {safe_serial} shell am start -a android.intent.action.MAIN -c android.intent.category.HOME",
                    f"# Select '{package_id}' in the Wear OS Watch Face Picker on {safe_serial}",
                    f"adb -s {safe_serial} shell dumpsys wallpaper",
                ],
                "pass_criteria": (
                    f"Active current-user mWallpaperComponent in dumpsys wallpaper explicitly matches '{package_id}' "
                    "(status=SELECTED; inactive previousPackage, suffix collisions, or UNKNOWN host formats are rejected)"
                ),
            },
            {
                "step": "4_capture_active_state",
                "commands": [
                    f"adb -s {safe_serial} shell input keyevent KEYCODE_WAKEUP",
                    f"adb -s {safe_serial} shell dumpsys power",
                    f"adb -s {safe_serial} shell dumpsys display",
                    f"adb -s {safe_serial} exec-out screencap -p > {out_dir}/active_wff{wff_version}.png",
                ],
                "pass_criteria": "All commands rc=0, mWakefulness=Awake AND Display state=ON confirmed before valid PNG capture",
            },
            {
                "step": "5_record_aod_transition_capture_ambient_and_restore_awake",
                "commands": [
                    f"adb -s {safe_serial} shell screenrecord --time-limit 8 {remote_video}  # background",
                    f"adb -s {safe_serial} shell input keyevent KEYCODE_SLEEP",
                    f"adb -s {safe_serial} shell dumpsys power",
                    f"adb -s {safe_serial} shell dumpsys display",
                    f"adb -s {safe_serial} exec-out screencap -p > {out_dir}/ambient_wff{wff_version}.png",
                    f"adb -s {safe_serial} shell input keyevent KEYCODE_WAKEUP",
                    f"adb -s {safe_serial} shell dumpsys power",
                    f"adb -s {safe_serial} shell dumpsys display",
                    f"adb -s {safe_serial} pull {remote_video} {out_dir}/transition_wff{wff_version}.mp4",
                    f"adb -s {safe_serial} shell rm -f {remote_video}",
                ],
                "pass_criteria": (
                    "All commands rc=0; mWakefulness in {Dozing,Asleep} AND Display state in {DOZE,DOZE_SUSPEND} "
                    "confirmed before ambient PNG; post-wakeup mWakefulness=Awake AND Display state=ON confirmed; "
                    "pulled MP4 >= 1024 bytes with valid 'ftyp' header; temporary remote file removed in finally"
                ),
            },
        ],
    }


def _default_adb_runner(adb_bin, serial, adb_args, timeout=30, binary=False):
    safe_serial = validate_emulator_serial(serial)
    return subprocess.run(
        [str(adb_bin), "-s", safe_serial, *adb_args],
        capture_output=True,
        text=not binary,
        encoding=None if binary else "utf-8",
        errors=None if binary else "replace",
        timeout=timeout,
        check=False,
    )


def run_checked_adb(run_fn, adb_args, timeout=30, binary=False):
    """Run an adb command via `run_fn` and strictly require `returncode == 0` and non-timed-out completion."""
    try:
        proc = run_fn(adb_args, timeout=timeout, binary=binary)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"ADB command timed out after {timeout}s: {' '.join(adb_args)}") from exc
    if proc.returncode != 0:
        stderr_val = proc.stderr.decode("utf-8", errors="replace") if isinstance(proc.stderr, bytes) else (proc.stderr or "")
        stdout_val = proc.stdout.decode("utf-8", errors="replace") if isinstance(proc.stdout, bytes) else (proc.stdout or "")
        raise RuntimeError(
            f"ADB command failed with returncode={proc.returncode}: {' '.join(adb_args)} "
            f"(stdout='{stdout_val.strip()}', stderr='{stderr_val.strip()}')"
        )
    return proc


def execute_runtime_verification(
    adb_bin,
    serial,
    apk_path,
    package_id,
    wff_version,
    output_dir,
    expected_avd_name=None,
    expected_api_level=None,
    expected_apk_sha256=None,
    runner=None,
    manifest_printer=None,
    recorder_factory=None,
    sleep_fn=time.sleep,
):
    """Execute safe runtime verification against an ALREADY-RUNNING isolated Wear OS emulator."""
    safe_serial = validate_emulator_serial(serial)
    min_sdk = WFF_MIN_SDK[wff_version]
    target_api = expected_api_level if expected_api_level is not None else min_sdk
    target_avd = validate_dedicated_wear_avd_name(expected_avd_name or f"aura_wear{min_sdk}_round")

    # Step 0: Pre-check local APK hash, resource-only entries, and compiled AndroidManifest BEFORE touching emulator
    apk_meta = verify_local_apk_before_install(
        apk_path=apk_path,
        expected_package=package_id,
        expected_wff_version=wff_version,
        expected_apk_sha256=expected_apk_sha256,
        manifest_printer=manifest_printer,
    )

    run_fn = runner or (
        lambda args, timeout=30, binary=False: _default_adb_runner(adb_bin, safe_serial, args, timeout=timeout, binary=binary)
    )

    # Step 1: Verify running emulator AVD name, boot status, watch characteristics, and SDK level
    avd_prop = run_checked_adb(run_fn, ["shell", "getprop", "ro.boot.qemu.avd_name"], timeout=15)
    running_avd_name = avd_prop.stdout.strip()
    if not running_avd_name:
        emu_avd = run_checked_adb(run_fn, ["emu", "avd", "name"], timeout=15)
        running_avd_name = emu_avd.stdout.splitlines()[0].strip() if emu_avd.stdout.strip() else ""
    validate_dedicated_wear_avd_name(running_avd_name, expected_avd_name=target_avd)

    boot = run_checked_adb(run_fn, ["shell", "getprop", "sys.boot_completed"], timeout=15)
    if boot.stdout.strip() != "1":
        raise RuntimeError(f"Emulator {safe_serial} ({running_avd_name}) is not booted (sys.boot_completed='{boot.stdout.strip()}')")

    chars = run_checked_adb(run_fn, ["shell", "getprop", "ro.build.characteristics"], timeout=15)
    sdk_raw = run_checked_adb(run_fn, ["shell", "getprop", "ro.build.version.sdk"], timeout=15)
    sdk_int = validate_wear_device_properties(
        chars.stdout.strip(),
        sdk_raw.stdout.strip(),
        required_min_sdk=min_sdk,
        expected_api_level=target_api,
    )

    # Step 2: Install verified APK and confirm package presence
    install = run_checked_adb(run_fn, ["install", "-r", str(apk_path)], timeout=120)
    if "Success" not in install.stdout:
        raise RuntimeError(f"APK install did not report Success on {safe_serial}: {install.stdout}")

    pm = run_checked_adb(run_fn, ["shell", "pm", "list", "packages", package_id], timeout=30)
    exact_pkg_line = f"package:{package_id}"
    if exact_pkg_line not in [line.strip() for line in pm.stdout.splitlines()]:
        raise RuntimeError(f"Installed package '{package_id}' not found in exact package list on {safe_serial}: {pm.stdout}")

    # Step 3: Verify active watch face selection in dumpsys wallpaper
    wallpaper = run_checked_adb(run_fn, ["shell", "dumpsys", "wallpaper"], timeout=30)
    selection = verify_active_watchface_selected(wallpaper.stdout, package_id)
    if selection["status"] == "UNKNOWN":
        raise RuntimeVerificationIncompleteError(
            f"Active watch face selection status is UNKNOWN on {safe_serial}: {selection.get('reason')}. "
            "Treating runtime verification as UNKNOWN/NOT RUN."
        )
    if not selection["selected"]:
        raise RuntimeError(
            f"Watch face '{package_id}' is installed on {safe_serial} but NOT active "
            f"(status={selection['status']}, active_component='{selection.get('active_component')}')."
        )

    # Step 4: Wake display, confirm Active (Awake + ON) state, and capture Active PNG
    run_checked_adb(run_fn, ["shell", "input", "keyevent", "KEYCODE_WAKEUP"], timeout=15)
    power_active = parse_power_and_display_state(
        run_checked_adb(run_fn, ["shell", "dumpsys", "power"], timeout=30).stdout,
        run_checked_adb(run_fn, ["shell", "dumpsys", "display"], timeout=30).stdout,
    )
    if power_active["status"] == "UNKNOWN":
        raise RuntimeVerificationIncompleteError(
            f"Active power/display state is UNKNOWN on {safe_serial}: {power_active}"
        )
    if not power_active["is_active"]:
        raise RuntimeError(f"Emulator {safe_serial} did not enter Active (Awake+ON) state: {power_active}")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    active_png = out / f"active_wff{wff_version}.png"
    cap_active = run_checked_adb(run_fn, ["exec-out", "screencap", "-p"], timeout=30, binary=True)
    if not isinstance(cap_active.stdout, (bytes, bytearray)) or not cap_active.stdout.startswith(b"\x89PNG"):
        raise RuntimeError(f"Failed to capture valid active PNG bytes on {safe_serial}")
    active_png.write_bytes(cap_active.stdout)

    # Step 5: Record AOD transition, verify AOD (Dozing + DOZE/DOZE_SUSPEND), capture Ambient PNG,
    # restore Awake (Awake + ON), verify pulled MP4, and ALWAYS clean up in finally
    remote_video = f"/sdcard/ag01_wff{wff_version}_aod_transition.mp4"
    local_video = out / f"transition_wff{wff_version}.mp4"
    ambient_png = out / f"ambient_wff{wff_version}.png"

    spawn_recorder = recorder_factory or (
        lambda: subprocess.Popen(
            [str(adb_bin), "-s", safe_serial, "shell", "screenrecord", "--time-limit", "8", remote_video],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    )
    recorder = spawn_recorder()
    power_aod = None
    power_restored = None
    try:
        sleep_fn(1.0)
        run_checked_adb(run_fn, ["shell", "input", "keyevent", "KEYCODE_SLEEP"], timeout=15)
        sleep_fn(2.0)
        power_aod = parse_power_and_display_state(
            run_checked_adb(run_fn, ["shell", "dumpsys", "power"], timeout=30).stdout,
            run_checked_adb(run_fn, ["shell", "dumpsys", "display"], timeout=30).stdout,
        )
        if power_aod["status"] == "UNKNOWN":
            raise RuntimeVerificationIncompleteError(
                f"AOD power/display state is UNKNOWN on {safe_serial}: {power_aod}"
            )
        if not power_aod["is_aod"]:
            raise RuntimeError(f"Emulator {safe_serial} did not enter valid AOD (Dozing + DOZE/DOZE_SUSPEND) state: {power_aod}")

        cap_ambient = run_checked_adb(run_fn, ["exec-out", "screencap", "-p"], timeout=30, binary=True)
        if not isinstance(cap_ambient.stdout, (bytes, bytearray)) or not cap_ambient.stdout.startswith(b"\x89PNG"):
            raise RuntimeError(f"Failed to capture valid ambient PNG bytes on {safe_serial}")
        ambient_png.write_bytes(cap_ambient.stdout)

        sleep_fn(1.5)
        run_checked_adb(run_fn, ["shell", "input", "keyevent", "KEYCODE_WAKEUP"], timeout=15)
        sleep_fn(1.0)
        power_restored = parse_power_and_display_state(
            run_checked_adb(run_fn, ["shell", "dumpsys", "power"], timeout=30).stdout,
            run_checked_adb(run_fn, ["shell", "dumpsys", "display"], timeout=30).stdout,
        )
        if not power_restored["is_active"]:
            raise RuntimeError(
                f"Emulator {safe_serial} failed to return to Active (Awake+ON) state after AOD capture: {power_restored}"
            )

        rec_rc = recorder.wait(timeout=15)
        if rec_rc != 0:
            raise RuntimeError(f"screenrecord exited with non-zero returncode={rec_rc} on {safe_serial}")

        run_checked_adb(run_fn, ["pull", remote_video, str(local_video)], timeout=60)
        if not local_video.is_file():
            raise RuntimeError(f"Pulled transition video file is missing at {local_video}")
        video_size = validate_mp4_bytes(local_video.read_bytes())
    finally:
        # Ensure recorder process is stopped, display is woken up, and remote temp video is ALWAYS removed
        if recorder.poll() is None:
            recorder.terminate()
            try:
                recorder.wait(timeout=5)
            except subprocess.TimeoutExpired:
                recorder.kill()
        if power_restored is None or not power_restored.get("is_active"):
            try:
                run_fn(["shell", "input", "keyevent", "KEYCODE_WAKEUP"], timeout=10, binary=False)
            except Exception:
                pass
        try:
            run_checked_adb(run_fn, ["shell", "rm", "-f", remote_video], timeout=15)
        except Exception:
            if power_restored is not None and power_restored.get("is_active"):
                raise

    return {
        "serial": safe_serial,
        "avd_name": running_avd_name,
        "sdk_int": sdk_int,
        "apk_verification": apk_meta,
        "selection": selection,
        "active_state": power_active,
        "aod_state": power_aod,
        "restored_active_state": power_restored,
        "active_png": str(active_png),
        "active_png_sha256": hashlib.sha256(active_png.read_bytes()).hexdigest(),
        "ambient_png": str(ambient_png),
        "ambient_png_sha256": hashlib.sha256(ambient_png.read_bytes()).hexdigest(),
        "transition_mp4": str(local_video),
        "transition_mp4_size_bytes": video_size,
        "transition_mp4_sha256": hashlib.sha256(local_video.read_bytes()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-only", action="store_true", help="Print safe runtime verification plan without touching any device")
    parser.add_argument("--serial", required=True, help="Explicit Android emulator serial (must match emulator-<port>)")
    parser.add_argument("--avd-name", default=None, help="Expected dedicated Wear OS AVD name (e.g. aura_wear36_round)")
    parser.add_argument("--apk", type=Path, required=True)
    parser.add_argument("--apk-sha256", default=None, help="Expected APK SHA-256 digest to verify before install")
    parser.add_argument("--package-id", required=True)
    parser.add_argument("--wff-version", type=int, choices=(2, 3, 4, 5), required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--adb", type=Path, default=Path("adb"))
    args = parser.parse_args()

    plan = build_safe_runtime_verification_plan(
        args.serial,
        args.apk,
        args.package_id,
        args.wff_version,
        args.out_dir,
        expected_avd_name=args.avd_name,
        expected_apk_sha256=args.apk_sha256,
    )
    if args.plan_only:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return

    res = execute_runtime_verification(
        args.adb,
        args.serial,
        args.apk,
        args.package_id,
        args.wff_version,
        args.out_dir,
        expected_avd_name=args.avd_name,
        expected_apk_sha256=args.apk_sha256,
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
