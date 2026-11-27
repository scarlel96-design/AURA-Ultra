"""Safe Wear OS emulator runtime verification helper for AG-01 (R05 hardened).

Safety and verification invariants enforced by this module (AG01-AUD-04 & AG-01-R05):
1. Never downloads SDK packages or creates AVDs automatically.
2. Never uses `--force` in recommended `avdmanager create avd` commands so existing AVDs are never overwritten.
3. Refuses to target physical devices (non-`emulator-*` serials) or non-Wear AVDs (e.g. phone/tablet AVDs).
4. Before any device mutation (`adb install`), verifies:
   - Local APK file exists, SHA-256 matches `expected_apk_sha256` (when provided), is resource-only (`0 .dex`, `0 .so`),
     and compiled `AndroidManifest.xml` matches `expected_package`, `expected_wff_version`, and `minSdk`.
   - Running emulator reports a dedicated approved Wear AVD name matching `expected_avd_name`,
     `sys.boot_completed == "1"`, `ro.build.characteristics` contains `"watch"`, and `ro.build.version.sdk`
     satisfies both `>= required_min_sdk` and `== expected_api_level` (when specified).
5. Requires explicit `-s <emulator-serial>` and checks `returncode == 0` and timeout on EVERY `adb` command,
   including recovery/cleanup commands.
6. Active watch face selection (`verify_active_watchface_selected`):
   - Never falls back to another user's wallpaper binding when the current user has no binding (`UNKNOWN`).
   - Rejects user-scoped dumps lacking `mCurrentUserId`, conflicting `mCurrentUserId`, inactive history references
     (`previousPackage=`), package suffix collisions (`<pkg>.other`), conflicting active components, and unconfirmed
     WFF host dumpsys formats (`UNKNOWN` / `NOT_SELECTED`).
7. Power and display state (`parse_power_and_display_state`):
   - Collects ALL wakefulness values and ALL display states across BOTH `dumpsys power` and `dumpsys display`.
   - Any missing, conflicting, multi-display contradictory, or incoherent wakefulness/display combination
     (e.g. `Awake+DOZE`, `Dozing+ON`, `ON` vs `OFF` across power/display or multiple displays) returns `status="UNKNOWN"`.
   - `is_active` is True ONLY when `wakefulness == "Awake"` AND single consistent `display_state == "ON"`.
   - `is_aod` is True ONLY when `wakefulness in ("Dozing", "Asleep")` AND single consistent `display_state in ("DOZE", "DOZE_SUSPEND")`.
8. PNG & MP4 artifact integrity:
   - `validate_png_bytes`: validates full 8-byte PNG signature, chunk bounds, CRC-32 of every chunk, `IHDR` geometry/color
     fields, `IDAT` zlib decompression & exact scanline byte length (non-interlaced), `IEND`, and zero trailing bytes.
   - `validate_mp4_bytes`: validates size >= 1024 bytes and ISO BMFF `ftyp` header box.
9. Failure recovery & cleanup verification (`RecoveryFailureError`):
   - Always terminates and reaps (`kill` + `wait`) any lingering `screenrecord` process.
   - Verifies ADB exit code and timeout on recovery `KEYCODE_WAKEUP`, and re-checks `dumpsys power`/`display`
     to confirm final restoration to Active (`Awake + ON`).
   - Verifies ADB exit code and timeout on `rm -f <remote_video>` AND confirms remote file absence via `test ! -e`.
   - Never silently swallows recovery failures; raises `RecoveryFailureError` preserving both primary and recovery errors.
"""
import argparse
import hashlib
import json
import re
import struct
import subprocess
import sys
import time
import zipfile
import zlib
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

PACKAGE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+$")

ACTIVE_WALLPAPER_COMPONENT_RE = re.compile(
    r"^\s*mWallpaperComponent=ComponentInfo\{([A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+)/([^\}\s]+)\}\s*$"
)
CURRENT_USER_RE = re.compile(r"^\s*(?:mCurrentUserId|Current user ID)\s*[:=]\s*(\d+)\s*$")
USER_WALLPAPER_HEADER_RE = re.compile(r"^\s*(?:WallpaperData\b.*?\buserId=(\d+)\b|User\s+(\d+)\s*:)")

KNOWN_WFF_HOST_PACKAGES = {
    "com.google.wear.watchface.runtime",
    "com.google.android.wearable.watchface.rwf",
    "com.android.systemui",
}
ACTIVE_WFF_BOUND_PACKAGE_RE = re.compile(
    r"^\s*(?:activeWatchFacePackage|mWatchFacePackage|boundWatchFacePackage)=([A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+)\s*$"
)

VALID_WAKEFULNESS_STATES = {"Awake", "Dozing", "Asleep", "Dreaming"}
VALID_DISPLAY_STATES = {"ON", "OFF", "DOZE", "DOZE_SUSPEND", "ON_SUSPEND", "VR"}

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_COLOR_CHANNELS = {
    0: (1, {1, 2, 4, 8, 16}),
    2: (3, {8, 16}),
    3: (1, {1, 2, 4, 8}),
    4: (2, {8, 16}),
    6: (4, {8, 16}),
}


class UnsafeTargetError(RuntimeError):
    """Raised when a command attempts to touch a physical watch/phone, non-Wear AVD, or mismatched APK/device."""


class RuntimeVerificationIncompleteError(RuntimeError):
    """Raised when runtime state or dumpsys format is UNKNOWN/unconfirmed and cannot be approved as PASS."""


class RecoveryFailureError(RuntimeError):
    """Raised when post-run or failure-path recovery/cleanup checks fail (never silently swallowed)."""

    def __init__(self, message, primary_error=None, recovery_errors=None, recovery_report=None):
        super().__init__(message)
        self.primary_error = primary_error
        self.recovery_errors = list(recovery_errors or [])
        self.recovery_report = dict(recovery_report or {})


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


def _extract_display_states(text, source_label):
    """Collect all display state occurrences (including multi-display entries) from a dumpsys text."""
    patterns = (
        re.compile(r"Display Power:\s*state=([A-Z_]+)\b"),
        re.compile(r"\bmScreenState=([A-Z_]+)\b"),
        re.compile(r"\bDisplay State:\s*([A-Z_]+)\b"),
        re.compile(r"\bmDisplayState=([A-Z_]+)\b"),
        re.compile(r"\bmGlobalDisplayState=([A-Z_]+)\b"),
        re.compile(r"DisplayDeviceInfo\{[^\n}]*?\bstate\s+([A-Z_]+)\b"),
    )
    found = []
    for pat in patterns:
        for match in pat.finditer(text or ""):
            found.append((source_label, match.group(1)))
    return found


def parse_power_and_display_state(dumpsys_power, dumpsys_display=""):
    """Strictly parse Awake vs Doze/AOD state from `dumpsys power` and `dumpsys display` (AG01-AUD-04 & R05).

    Rules:
    - Collects ALL `mWakefulness=` occurrences in `dumpsys power` and ALL display state occurrences across
      BOTH `dumpsys power` and `dumpsys display` (including multi-display entries).
    - Missing values, unknown tokens, multiple conflicting wakefulness values, or multiple conflicting display
      states (across power vs display or across multiple displays) ALWAYS return `status="UNKNOWN"`,
      `is_active=False`, `is_aod=False`.
    - Incoherent wakefulness/display combinations (e.g. `Awake` + `DOZE`, `Dozing` + `ON`, `Awake` + `OFF`)
      return `status="UNKNOWN"`, `is_active=False`, `is_aod=False`.
    - `is_active` is True ONLY when single consistent `wakefulness == "Awake"` AND single consistent `display_state == "ON"`.
    - `is_aod` is True ONLY when single consistent `wakefulness in ("Dozing", "Asleep")` AND single consistent
      `display_state in ("DOZE", "DOZE_SUSPEND")`.
    - `Dozing|Asleep` + `OFF` returns `status="SCREEN_OFF"`, `is_active=False`, `is_aod=False`.
    """
    wake_matches = re.findall(r"\bmWakefulness=([A-Za-z_]+)\b", dumpsys_power or "")
    unique_wakes = sorted(set(wake_matches))

    display_observations = (
        _extract_display_states(dumpsys_power, "power")
        + _extract_display_states(dumpsys_display, "display")
    )
    unique_displays = sorted({val for _, val in display_observations})

    # Detect multiple display IDs explicitly
    display_ids = sorted(set(
        re.findall(r"\b(?:Display Id|mDisplayId)\s*[:=]\s*(\d+)\b", (dumpsys_power or "") + "\n" + (dumpsys_display or ""))
    ))

    if len(unique_wakes) == 0:
        return {
            "status": "UNKNOWN",
            "wakefulness": "UNKNOWN",
            "display_state": unique_displays[0] if len(unique_displays) == 1 else ("CONFLICT" if len(unique_displays) > 1 else "UNKNOWN"),
            "observed_wakefulness": unique_wakes,
            "observed_display_states": unique_displays,
            "observed_display_ids": display_ids,
            "is_active": False,
            "is_aod": False,
            "reason": "No mWakefulness field found in dumpsys power",
        }
    if len(unique_wakes) > 1 or unique_wakes[0] not in VALID_WAKEFULNESS_STATES:
        return {
            "status": "UNKNOWN",
            "wakefulness": "CONFLICT" if len(unique_wakes) > 1 else unique_wakes[0],
            "display_state": unique_displays[0] if len(unique_displays) == 1 else ("CONFLICT" if len(unique_displays) > 1 else "UNKNOWN"),
            "observed_wakefulness": unique_wakes,
            "observed_display_states": unique_displays,
            "observed_display_ids": display_ids,
            "is_active": False,
            "is_aod": False,
            "reason": f"Conflicting or invalid mWakefulness values observed: {unique_wakes}",
        }
    wakefulness = unique_wakes[0]

    if len(unique_displays) == 0:
        return {
            "status": "UNKNOWN",
            "wakefulness": wakefulness,
            "display_state": "UNKNOWN",
            "observed_wakefulness": unique_wakes,
            "observed_display_states": unique_displays,
            "observed_display_ids": display_ids,
            "is_active": False,
            "is_aod": False,
            "reason": "No display state found in dumpsys power or dumpsys display",
        }
    if len(unique_displays) > 1 or unique_displays[0] not in VALID_DISPLAY_STATES:
        return {
            "status": "UNKNOWN",
            "wakefulness": wakefulness,
            "display_state": "CONFLICT" if len(unique_displays) > 1 else unique_displays[0],
            "observed_wakefulness": unique_wakes,
            "observed_display_states": unique_displays,
            "observed_display_ids": display_ids,
            "is_active": False,
            "is_aod": False,
            "reason": f"Conflicting or invalid display states observed across power/display or multiple displays: {display_observations}",
        }
    if len(display_ids) > 1 and len(display_observations) < len(display_ids):
        return {
            "status": "UNKNOWN",
            "wakefulness": wakefulness,
            "display_state": "INCOMPLETE_MULTI_DISPLAY",
            "observed_wakefulness": unique_wakes,
            "observed_display_states": unique_displays,
            "observed_display_ids": display_ids,
            "is_active": False,
            "is_aod": False,
            "reason": f"Multiple display IDs ({display_ids}) present without complete per-display state observations ({display_observations})",
        }
    display_state = unique_displays[0]

    if wakefulness == "Awake" and display_state == "ON":
        return {
            "status": "ACTIVE",
            "wakefulness": wakefulness,
            "display_state": display_state,
            "observed_wakefulness": unique_wakes,
            "observed_display_states": unique_displays,
            "observed_display_ids": display_ids,
            "is_active": True,
            "is_aod": False,
        }
    if wakefulness in ("Dozing", "Asleep") and display_state in ("DOZE", "DOZE_SUSPEND"):
        return {
            "status": "AOD",
            "wakefulness": wakefulness,
            "display_state": display_state,
            "observed_wakefulness": unique_wakes,
            "observed_display_states": unique_displays,
            "observed_display_ids": display_ids,
            "is_active": False,
            "is_aod": True,
        }
    if wakefulness in ("Dozing", "Asleep") and display_state == "OFF":
        return {
            "status": "SCREEN_OFF",
            "wakefulness": wakefulness,
            "display_state": display_state,
            "observed_wakefulness": unique_wakes,
            "observed_display_states": unique_displays,
            "observed_display_ids": display_ids,
            "is_active": False,
            "is_aod": False,
            "reason": f"Display is OFF while {wakefulness} (screen off, not AOD)",
        }

    return {
        "status": "UNKNOWN",
        "wakefulness": wakefulness,
        "display_state": display_state,
        "observed_wakefulness": unique_wakes,
        "observed_display_states": unique_displays,
        "observed_display_ids": display_ids,
        "is_active": False,
        "is_aod": False,
        "reason": f"Incoherent or transitional wakefulness/display combination: wakefulness={wakefulness}, display_state={display_state}",
    }


def verify_active_watchface_selected(dumpsys_wallpaper, expected_package):
    """Verify from `dumpsys wallpaper` that `expected_package` is the active current-user watch face (AG01-AUD-04 & R05).

    Strict rules:
    - Never falls back to another user's binding when the current user has no binding -> returns `status="UNKNOWN"`.
    - Rejects user-scoped dumps that omit `mCurrentUserId` or report conflicting `mCurrentUserId` -> `status="UNKNOWN"`.
    - Rejects inactive history lines (`previousPackage=`), suffix collisions (`<pkg>.other`), conflicting bindings,
      conflicting `boundWatchFacePackage` lines, and unconfirmed WFF host formats.
    """
    if not expected_package or not PACKAGE_ID_RE.fullmatch(expected_package):
        raise ValueError(f"expected_package must be a valid Android package name, got '{expected_package}'")

    lines = (dumpsys_wallpaper or "").splitlines()
    observed_current_users = []
    for line in lines:
        m_user = CURRENT_USER_RE.match(line)
        if m_user:
            observed_current_users.append(m_user.group(1))

    unique_current_users = sorted(set(observed_current_users))
    if len(unique_current_users) > 1:
        return {
            "status": "UNKNOWN",
            "selected": False,
            "expected_package": expected_package,
            "active_package": None,
            "active_component": None,
            "reason": f"Conflicting mCurrentUserId values in dumpsys wallpaper: {unique_current_users}",
        }
    current_user = unique_current_users[0] if unique_current_users else None

    section_user = None
    saw_user_header = False
    bindings = []
    for line in lines:
        m_header = USER_WALLPAPER_HEADER_RE.match(line)
        if m_header:
            saw_user_header = True
            section_user = m_header.group(1) if m_header.group(1) is not None else m_header.group(2)
            continue
        m_comp = ACTIVE_WALLPAPER_COMPONENT_RE.match(line)
        if m_comp:
            pkg, cls = m_comp.group(1), m_comp.group(2)
            bindings.append({
                "user_id": section_user,
                "package": pkg,
                "class_name": cls,
                "component": f"{pkg}/{cls}",
                "bound_wff_packages": [],
                "raw_line": line.strip(),
            })
            continue
        m_bound = ACTIVE_WFF_BOUND_PACKAGE_RE.match(line)
        if m_bound and bindings and bindings[-1]["user_id"] == section_user:
            bindings[-1]["bound_wff_packages"].append(m_bound.group(1))

    if not bindings:
        return {
            "status": "UNKNOWN",
            "selected": False,
            "expected_package": expected_package,
            "active_package": None,
            "active_component": None,
            "reason": "No active mWallpaperComponent=ComponentInfo{...} line found in dumpsys wallpaper",
        }

    has_user_sections = saw_user_header or any(b["user_id"] is not None for b in bindings)
    if has_user_sections and any(b["user_id"] is None for b in bindings):
        return {
            "status": "UNKNOWN",
            "selected": False,
            "expected_package": expected_package,
            "active_package": None,
            "active_component": None,
            "reason": "Mixed unscoped and user-scoped mWallpaperComponent bindings in dumpsys wallpaper",
        }
    if current_user is not None:
        if has_user_sections:
            user_filtered = [b for b in bindings if b["user_id"] == current_user]
            if not user_filtered:
                other_users = sorted({b["user_id"] for b in bindings if b["user_id"] is not None})
                return {
                    "status": "UNKNOWN",
                    "selected": False,
                    "expected_package": expected_package,
                    "active_package": None,
                    "active_component": None,
                    "reason": (
                        f"No active wallpaper binding found for current user {current_user} "
                        f"(refusing fallback to other users: {other_users})"
                    ),
                }
            bindings = user_filtered
        elif current_user != "0":
            return {
                "status": "UNKNOWN",
                "selected": False,
                "expected_package": expected_package,
                "active_package": None,
                "active_component": None,
                "reason": (
                    f"mCurrentUserId={current_user} is non-primary, but dumpsys wallpaper lacks userId sections "
                    "to confirm the binding belongs to the current user"
                ),
            }
    else:
        if has_user_sections:
            observed_users = sorted({b["user_id"] for b in bindings if b["user_id"] is not None})
            return {
                "status": "UNKNOWN",
                "selected": False,
                "expected_package": expected_package,
                "active_package": None,
                "active_component": None,
                "reason": (
                    f"User-scoped WallpaperData bindings ({observed_users}) present without mCurrentUserId; "
                    "cannot confirm which user is active"
                ),
            }

    # Verify each binding does not have conflicting boundWatchFacePackage values
    normalized_keys = set()
    for b in bindings:
        uniq_bound = sorted(set(b["bound_wff_packages"]))
        if len(uniq_bound) > 1:
            return {
                "status": "UNKNOWN",
                "selected": False,
                "expected_package": expected_package,
                "active_package": None,
                "active_component": None,
                "reason": f"Conflicting boundWatchFacePackage values on {b['component']}: {uniq_bound}",
            }
        b["bound_wff_package"] = uniq_bound[0] if uniq_bound else None
        normalized_keys.add((b["package"], b["class_name"], b["bound_wff_package"]))

    if len(normalized_keys) != 1:
        return {
            "status": "UNKNOWN",
            "selected": False,
            "expected_package": expected_package,
            "active_package": None,
            "active_component": None,
            "reason": f"Conflicting multiple active mWallpaperComponent bindings in dumpsys wallpaper: {[b['component'] for b in bindings]}",
        }

    active = bindings[0]
    active_pkg = active["package"]
    active_comp = active["component"]

    if active_pkg == expected_package:
        return {
            "status": "SELECTED",
            "selected": True,
            "expected_package": expected_package,
            "active_package": active_pkg,
            "active_component": active_comp,
            "user_id": current_user,
            "matched_lines": [active["raw_line"]],
        }

    if active_pkg in KNOWN_WFF_HOST_PACKAGES:
        bound_pkg = active["bound_wff_package"]
        if bound_pkg is None:
            return {
                "status": "UNKNOWN",
                "selected": False,
                "expected_package": expected_package,
                "active_package": active_pkg,
                "active_component": active_comp,
                "user_id": current_user,
                "reason": f"WFF host '{active_comp}' is active, but bound watch face package format is unconfirmed in dumpsys wallpaper",
            }
        if bound_pkg == expected_package:
            return {
                "status": "SELECTED",
                "selected": True,
                "expected_package": expected_package,
                "active_package": bound_pkg,
                "active_component": active_comp,
                "user_id": current_user,
                "matched_lines": [active["raw_line"], f"boundWatchFacePackage={bound_pkg}"],
            }
        return {
            "status": "NOT_SELECTED",
            "selected": False,
            "expected_package": expected_package,
            "active_package": bound_pkg,
            "active_component": active_comp,
            "user_id": current_user,
            "reason": f"WFF host '{active_comp}' is bound to '{bound_pkg}', not '{expected_package}'",
        }

    return {
        "status": "NOT_SELECTED",
        "selected": False,
        "expected_package": expected_package,
        "active_package": active_pkg,
        "active_component": active_comp,
        "user_id": current_user,
        "reason": f"Active mWallpaperComponent package is '{active_pkg}', not '{expected_package}'",
    }


def validate_png_bytes(data, min_width=1, min_height=1):
    """Validate complete PNG structure and integrity (ISO/IEC 15948) using Python stdlib only.

    Checks:
    1. Exact 8-byte PNG signature (`\\x89PNG\\r\\n\\x1a\\n`).
    2. Complete chunk framing without truncation or trailing bytes after `IEND`.
    3. CRC-32 checksum verification for EVERY chunk.
    4. First chunk is `IHDR` (13 bytes) with valid width/height/bit_depth/color_type/compression/filter/interlace.
    5. At least one `IDAT` chunk whose concatenated payload decompresses cleanly with `zlib.decompress`
       and matches exact uncompressed scanline byte length for non-interlaced PNGs.
    6. Last chunk is `IEND` (0 bytes).
    """
    if not isinstance(data, (bytes, bytearray)):
        raise RuntimeError("PNG capture output is not bytes")
    raw = bytes(data)
    if len(raw) < 33 or raw[:8] != PNG_SIGNATURE:
        raise RuntimeError("Invalid PNG signature or truncated PNG header")

    offset = 8
    chunk_count = 0
    ihdr = None
    saw_plte = False
    idat_parts = []
    saw_iend = False

    while offset < len(raw):
        if saw_iend:
            raise RuntimeError(f"Trailing {len(raw) - offset} garbage byte(s) found after PNG IEND chunk")
        if offset + 12 > len(raw):
            raise RuntimeError(f"Truncated PNG chunk header at offset {offset}")
        length = struct.unpack(">I", raw[offset:offset + 4])[0]
        chunk_type = raw[offset + 4:offset + 8]
        if not all(65 <= b <= 90 or 97 <= b <= 122 for b in chunk_type):
            raise RuntimeError(f"Invalid non-ASCII PNG chunk type {chunk_type!r} at offset {offset}")
        data_start = offset + 8
        data_end = data_start + length
        crc_end = data_end + 4
        if crc_end > len(raw):
            raise RuntimeError(f"Truncated PNG chunk {chunk_type.decode('ascii')} (declared {length} bytes)")
        chunk_data = raw[data_start:data_end]
        expected_crc = struct.unpack(">I", raw[data_end:crc_end])[0]
        actual_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise RuntimeError(
                f"PNG CRC-32 mismatch in chunk {chunk_type.decode('ascii')}: expected 0x{expected_crc:08x}, got 0x{actual_crc:08x}"
            )

        chunk_count += 1
        if chunk_count == 1:
            if chunk_type != b"IHDR" or length != 13:
                raise RuntimeError(f"First PNG chunk must be 13-byte IHDR, got {chunk_type!r} ({length} bytes)")
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(">IIBBBBB", chunk_data)
            if width < min_width or height < min_height:
                raise RuntimeError(f"Invalid PNG dimensions: {width}x{height} (min {min_width}x{min_height})")
            if color_type not in PNG_COLOR_CHANNELS:
                raise RuntimeError(f"Unsupported PNG color_type={color_type}")
            channels, allowed_depths = PNG_COLOR_CHANNELS[color_type]
            if bit_depth not in allowed_depths:
                raise RuntimeError(f"Invalid PNG bit_depth={bit_depth} for color_type={color_type}")
            if compression != 0 or filter_method != 0 or interlace not in (0, 1):
                raise RuntimeError(
                    f"Invalid PNG header flags: compression={compression}, filter={filter_method}, interlace={interlace}"
                )
            ihdr = {
                "width": width,
                "height": height,
                "bit_depth": bit_depth,
                "color_type": color_type,
                "channels": channels,
                "interlace": interlace,
            }
        elif chunk_type == b"IHDR":
            raise RuntimeError("Duplicate IHDR chunk found in PNG stream")
        elif chunk_type == b"PLTE":
            if length == 0 or length % 3 != 0 or length > 768:
                raise RuntimeError(f"Invalid PNG PLTE chunk length: {length}")
            saw_plte = True
        elif chunk_type == b"IDAT":
            if ihdr and ihdr["color_type"] == 3 and not saw_plte:
                raise RuntimeError("Indexed-color PNG (color_type=3) is missing required PLTE chunk before IDAT")
            idat_parts.append(chunk_data)
        elif chunk_type == b"IEND":
            if length != 0:
                raise RuntimeError(f"PNG IEND chunk must have 0 length, got {length}")
            saw_iend = True

        offset = crc_end

    if ihdr is None:
        raise RuntimeError("PNG missing IHDR chunk")
    if not idat_parts:
        raise RuntimeError("PNG missing IDAT image data chunk")
    if not saw_iend:
        raise RuntimeError("PNG missing terminating IEND chunk")

    try:
        decompressed = zlib.decompress(b"".join(idat_parts))
    except zlib.error as exc:
        raise RuntimeError(f"Corrupt PNG IDAT zlib stream: {exc}") from exc

    if ihdr["interlace"] == 0:
        bits_per_pixel = ihdr["channels"] * ihdr["bit_depth"]
        row_bytes = (ihdr["width"] * bits_per_pixel + 7) // 8
        stride = 1 + row_bytes
        expected_decompressed_len = ihdr["height"] * stride
        if len(decompressed) != expected_decompressed_len:
            raise RuntimeError(
                f"Corrupt PNG IDAT payload length: expected {expected_decompressed_len} decompressed bytes for "
                f"{ihdr['width']}x{ihdr['height']}, got {len(decompressed)}"
            )
        for row_idx in range(ihdr["height"]):
            filter_byte = decompressed[row_idx * stride]
            if filter_byte > 4:
                raise RuntimeError(
                    f"Invalid PNG scanline filter type {filter_byte} at row {row_idx} (must be 0..4)"
                )

    return {
        "width": ihdr["width"],
        "height": ihdr["height"],
        "bit_depth": ihdr["bit_depth"],
        "color_type": ihdr["color_type"],
        "chunk_count": chunk_count,
        "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
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
                    "(status=SELECTED; missing current-user binding, other-user fallback, inactive previousPackage, "
                    "suffix collisions, or UNKNOWN host formats are rejected)"
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
                "pass_criteria": "All commands rc=0, single consistent mWakefulness=Awake AND Display state=ON, full PNG CRC/IHDR/IDAT/IEND validated",
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
                    f"adb -s {safe_serial} shell test ! -e {remote_video}",
                ],
                "pass_criteria": (
                    "All commands rc=0; consistent Dozing|Asleep + DOZE|DOZE_SUSPEND confirmed before full-integrity ambient PNG; "
                    "final Awake+ON confirmed (including on failure recovery); pulled MP4 >= 1024 bytes with 'ftyp'; "
                    "recorder termination, remote rm -f, and absence test ! -e verified in finally"
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

    # Step 3: Verify active current-user watch face selection in dumpsys wallpaper
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

    # Step 4: Wake display, confirm Active (Awake + ON) state, and capture full-integrity Active PNG
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
    active_png_meta = validate_png_bytes(cap_active.stdout)
    active_png.write_bytes(cap_active.stdout)

    # Step 5: Record AOD transition, verify AOD, capture full-integrity Ambient PNG, restore Awake+ON,
    # pull & validate MP4, and ALWAYS verify recovery/cleanup results without swallowing errors
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
    ambient_png_meta = None
    video_size = None
    primary_error = None
    recovery_errors = []
    recovery_report = {
        "recorder_stopped": False,
        "awake_restored": False,
        "remote_file_removed": False,
    }

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
        ambient_png_meta = validate_png_bytes(cap_ambient.stdout)
        ambient_png.write_bytes(cap_ambient.stdout)

        sleep_fn(1.5)
        run_checked_adb(run_fn, ["shell", "input", "keyevent", "KEYCODE_WAKEUP"], timeout=15)
        sleep_fn(1.0)
        power_restored = parse_power_and_display_state(
            run_checked_adb(run_fn, ["shell", "dumpsys", "power"], timeout=30).stdout,
            run_checked_adb(run_fn, ["shell", "dumpsys", "display"], timeout=30).stdout,
        )
        if power_restored["status"] == "UNKNOWN":
            raise RuntimeVerificationIncompleteError(
                f"Post-AOD restored power/display state is UNKNOWN on {safe_serial}: {power_restored}"
            )
        if not power_restored["is_active"]:
            raise RuntimeError(
                f"Emulator {safe_serial} failed to return to Active (Awake+ON) state after AOD capture: {power_restored}"
            )

        try:
            rec_rc = recorder.wait(timeout=15)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"screenrecord did not exit within 15s timeout on {safe_serial}") from exc
        if rec_rc != 0:
            raise RuntimeError(f"screenrecord exited with non-zero returncode={rec_rc} on {safe_serial}")

        run_checked_adb(run_fn, ["pull", remote_video, str(local_video)], timeout=60)
        if not local_video.is_file():
            raise RuntimeError(f"Pulled transition video file is missing at {local_video}")
        try:
            video_size = validate_mp4_bytes(local_video.read_bytes())
        except Exception:
            local_video.unlink(missing_ok=True)
            raise
    except Exception as exc:
        primary_error = exc
    finally:
        # 1. Verify recorder process is fully terminated and reaped
        try:
            if recorder.poll() is None:
                recorder.terminate()
                try:
                    recorder.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    recorder.kill()
                    recorder.wait(timeout=5)
            else:
                recorder.wait(timeout=5)
            if recorder.poll() is None:
                recovery_errors.append("recorder_termination_failed: recorder process is still running after kill+wait")
            else:
                recovery_report["recorder_stopped"] = True
        except Exception as rec_exc:
            recovery_errors.append(f"recorder_termination_failed: {rec_exc}")

        # 2. Verify final Awake+ON restoration (including strict adb rc/timeout + dumpsys re-verification on recovery)
        if power_restored is not None and power_restored.get("is_active"):
            recovery_report["awake_restored"] = True
        else:
            try:
                run_checked_adb(run_fn, ["shell", "input", "keyevent", "KEYCODE_WAKEUP"], timeout=15)
                sleep_fn(0.5)
                recovered_state = parse_power_and_display_state(
                    run_checked_adb(run_fn, ["shell", "dumpsys", "power"], timeout=30).stdout,
                    run_checked_adb(run_fn, ["shell", "dumpsys", "display"], timeout=30).stdout,
                )
                recovery_report["recovered_state"] = recovered_state
                if recovered_state["is_active"]:
                    recovery_report["awake_restored"] = True
                else:
                    recovery_errors.append(
                        f"awake_recovery_failed: emulator did not confirm Awake+ON after recovery wakeup ({recovered_state})"
                    )
            except Exception as wake_exc:
                recovery_errors.append(f"awake_recovery_failed: {wake_exc}")

        # 3. Verify remote temporary MP4 deletion (adb rc/timeout + explicit absence check `test ! -e`)
        try:
            run_checked_adb(run_fn, ["shell", "rm", "-f", remote_video], timeout=15)
            run_checked_adb(run_fn, ["shell", "test", "!", "-e", remote_video], timeout=15)
            recovery_report["remote_file_removed"] = True
        except Exception as rm_exc:
            recovery_errors.append(f"remote_cleanup_failed: {rm_exc}")

    if recovery_errors:
        if primary_error is not None:
            raise RecoveryFailureError(
                f"Primary runtime error: {primary_error}; recovery verification also failed: {recovery_errors}",
                primary_error=primary_error,
                recovery_errors=recovery_errors,
                recovery_report=recovery_report,
            ) from primary_error
        raise RecoveryFailureError(
            f"Post-run cleanup/recovery verification failed: {recovery_errors}",
            primary_error=None,
            recovery_errors=recovery_errors,
            recovery_report=recovery_report,
        )

    if primary_error is not None:
        raise primary_error

    return {
        "serial": safe_serial,
        "avd_name": running_avd_name,
        "sdk_int": sdk_int,
        "apk_verification": apk_meta,
        "selection": selection,
        "active_state": power_active,
        "aod_state": power_aod,
        "restored_active_state": power_restored,
        "recovery_report": recovery_report,
        "active_png": str(active_png),
        "active_png_meta": active_png_meta,
        "active_png_sha256": active_png_meta["sha256"],
        "ambient_png": str(ambient_png),
        "ambient_png_meta": ambient_png_meta,
        "ambient_png_sha256": ambient_png_meta["sha256"],
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
