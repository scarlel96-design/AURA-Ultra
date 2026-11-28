"""Safe Wear OS emulator runtime verification helper for AG-01 (R06 hardened).

Safety and verification invariants enforced by this module (AG01-AUD-04 ~ AG01-AUD-09):
1. Never downloads SDK packages or creates AVDs automatically.
2. Never uses `--force` in recommended `avdmanager create avd` commands so existing AVDs are never overwritten.
3. Refuses to target physical devices (non-`emulator-*` serials) or non-Wear AVDs (e.g. phone/tablet AVDs).
4. Before any device mutation (`adb install`), verifies:
   - Existing evidence files (`active_wff*.png`, `ambient_wff*.png`, `transition_wff*.mp4`) do NOT already exist
     in `output_dir` (refuses overwrite via `EvidenceOverwriteError`, AG01-AUD-09).
   - Local APK file exists, SHA-256 matches `expected_apk_sha256` (when provided), is resource-only (`0 .dex`, `0 .so`),
     and compiled `AndroidManifest.xml` matches `expected_package`, `expected_wff_version`, and `minSdk`.
   - Running emulator reports a dedicated approved Wear AVD name matching `expected_avd_name`,
     `sys.boot_completed == "1"`, `ro.build.characteristics` contains `"watch"`, and `ro.build.version.sdk`
     satisfies both `>= required_min_sdk` and `== expected_api_level` (when specified).
5. Requires explicit `-s <emulator-serial>` and checks `returncode == 0` and timeout on EVERY `adb` command,
   including recovery/cleanup commands.
6. Active watch face selection (`verify_active_watchface_selected`):
   - Never falls back to another user's wallpaper binding when the current user has no binding (`UNKNOWN`).
   - Rejects user-scoped dumps lacking `mCurrentUserId`, conflicting `mCurrentUserId`, mixed scoped/unscoped dumps,
     non-primary unscoped dumps, inactive history (`previousPackage=`), suffix collisions (`<pkg>.other`),
     conflicting active components, and unconfirmed WFF host dumpsys formats (`UNKNOWN` / `NOT_SELECTED`).
   - Checked before AND after Active capture, before AND after AOD capture, and at final Awake restoration (AG01-AUD-08).
7. Power and display state (`parse_power_and_display_state`, AG01-AUD-05):
   - Explicitly maps display states per Display ID across `dumpsys power` and `dumpsys display`.
   - Duplicate observations on the same Display ID are deduplicated per Display ID and NEVER counted as evidence
     for another Display ID.
   - If the target display (default Display ID `"0"`) cannot be determined, or any declared Display ID lacks a
     state observation, or states conflict across displays / power / display / global state / wakefulness,
     returns `status="UNKNOWN"`, `is_active=False`, `is_aod=False`.
8. PNG integrity (`validate_png_bytes`, AG01-AUD-06):
   - Enforces upper bounds on input byte size, resolution (`width`, `height`), and decompressed payload size.
   - Validates exact 8-byte signature, chunk bounds, CRC-32 of every chunk, strict chunk ordering (contiguous `IDAT`,
     single `IHDR`, valid `PLTE` placement, rejects unknown critical chunks and APNG chunks), non-interlaced only
     (explicitly rejects `interlace != 0`), `zlib.decompressobj()` stream completion (`eof`), zero `unused_data`
     and zero `unconsumed_tail`, exact scanline byte length, valid scanline filter bytes (`0..4`), `IEND`, and zero
     trailing bytes.
9. MP4 container & frame verification (`parse_and_validate_mp4_structure`, `verify_mp4_video_artifact`, AG01-AUD-07):
   - Parses ISO BMFF box framing (`ftyp`, `moov`, `mdat`, `trak` -> `mdia` -> `hdlr(vide)` + `minf` -> `stbl` ->
     `stsd`/`stsz`/`stco|co64`) to prove valid box hierarchy, video track presence, sample count >= 1, and in-bounds
     `mdat` sample payload.
   - Runs external frame decoder/probe (`ffprobe`) to verify actual decodable video frames (`nb_read_frames >= 1`).
   - When `ffprobe` is unavailable, NEVER reports PASS; returns `video_verification_status="NOT RUN"` and raises
     `RuntimeVerificationIncompleteError` in `execute_runtime_verification`.
10. Full-scope failure recovery & non-destructive evidence handling (`execute_runtime_verification`, AG01-AUD-09):
   - Recovery `try ... finally` wraps from the VERY FIRST device-state-mutating command (`KEYCODE_WAKEUP`,
     captures, `spawn_recorder()`, `KEYCODE_SLEEP`, etc.).
   - Handles `spawn_recorder()` failure and Active/Ambient capture failure with full Awake+ON + watchface recovery
     and remote file cleanup (`rm -f` + `test ! -e`) verification.
   - Writes new evidence exclusively (`open(..., "xb")`) and stages pulled MP4 via temporary file so existing
     evidence files are NEVER overwritten.
   - Never silently swallows recovery failures; raises `RecoveryFailureError` preserving primary and recovery errors.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
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

# PNG bounds & structural constraints (AG01-AUD-06)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_MAX_INPUT_BYTES = 16 * 1024 * 1024
PNG_MAX_WIDTH = 4096
PNG_MAX_HEIGHT = 4096
PNG_MAX_DECOMPRESSED_BYTES = 64 * 1024 * 1024
PNG_COLOR_CHANNELS = {
    0: (1, {1, 2, 4, 8, 16}),
    2: (3, {8, 16}),
    3: (1, {1, 2, 4, 8}),
    4: (2, {8, 16}),
    6: (4, {8, 16}),
}
PNG_DISALLOWED_ANIMATION_CHUNKS = {b"acTL", b"fcTL", b"fdAT"}
PNG_KNOWN_CRITICAL_CHUNKS = {b"IHDR", b"PLTE", b"IDAT", b"IEND"}

# MP4 bounds (AG01-AUD-07)
MP4_MIN_BYTES = 128
MP4_MAX_BYTES = 256 * 1024 * 1024
MP4_CONTAINER_BOXES = {b"moov", b"trak", b"mdia", b"minf", b"stbl", b"edts", b"dinf", b"udta"}


class UnsafeTargetError(RuntimeError):
    """Raised when a command attempts to touch a physical watch/phone, non-Wear AVD, or mismatched APK/device."""


class EvidenceOverwriteError(FileExistsError):
    """Raised when a runtime run would overwrite an already-existing evidence file (AG01-AUD-09)."""


class RuntimeVerificationIncompleteError(RuntimeError):
    """Raised when runtime state, dumpsys format, or video frame probe is UNKNOWN/NOT RUN and cannot PASS."""


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


DISPLAY_ID_PATTERNS = (
    re.compile(r"\b(?:Display Id|mDisplayId|displayId)\s*[:=]\s*(\d+)\b"),
    re.compile(r"\bLogical Display\s+(\d+)\b"),
    re.compile(r"\bDisplayPowerController\[(?:display=)?(\d+)\]"),
    re.compile(r"^\s*Display\s+(\d+)\s*:\s*$"),
    re.compile(r"DisplayDeviceInfo\{[^\n}]*?\bdisplayId\s+(\d+)\b"),
)
LOCAL_DISPLAY_STATE_PATTERNS = (
    re.compile(r"Display Power:\s*state=([A-Z_]+)\b"),
    re.compile(r"\bmScreenState=([A-Z_]+)\b"),
    re.compile(r"\bDisplay State:\s*([A-Z_]+)\b"),
    re.compile(r"\bmDisplayState=([A-Z_]+)\b"),
    re.compile(r"DisplayDeviceInfo\{[^\n}]*?\bstate\s+([A-Z_]+)\b"),
)
GLOBAL_DISPLAY_STATE_RE = re.compile(r"\bmGlobalDisplayState=([A-Z_]+)\b")
TOP_SECTION_BOUNDARY_RE = re.compile(
    r"^(?:"
    r"Logical Display\b.*|"
    r"Display Power Controller\b.*|"
    r"Display Manager\b.*|"
    r"Power Manager\b.*|"
    r"DisplayDeviceInfo\{.*|"
    r"Display\s+[^0-9\n].*:|"
    r"Wake Locks\b.*|"
    r"Suspend Blockers\b.*|"
    r"Wireless Charger Detector\b.*|"
    r"User\s+\d+\s*:.*"
    r")$"
)
GENERIC_SECTION_HEADER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_/ ()\-\[\]]+:\s*$")


def _extract_display_states_by_id(text, source_label):
    """Map display states explicitly to each Display ID without bleeding IDs across section boundaries (AG01-AUD-05 & R07).

    Rules:
    - Duplicate observations for the same Display ID are deduplicated into that Display ID's state set
      and NEVER counted as evidence for a different Display ID.
    - Inline self-contained records (such as `DisplayDeviceInfo{...}`) scope their Display ID strictly to that line
      and reset `current_display_id = None` immediately after the line.
    - Blank lines, separator lines (`---`, `===`), outdented lines (`indent < current_header_indent`),
      or new section headers at `indent <= current_header_indent` that lack a Display ID immediately reset
      `current_display_id = None` so a previous Display ID never bleeds into subsequent sections.
    """
    declared_ids = set()
    states_by_id = {}
    unscoped_states = set()
    global_states = set()
    ambiguous_lines = []
    current_display_id = None
    current_header_indent = None
    current_header_is_block = False

    for raw_line in (text or "").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("---") or stripped.startswith("==="):
            current_display_id = None
            current_header_indent = None
            current_header_is_block = False
            continue

        indent = len(raw_line) - len(raw_line.lstrip())
        is_inline_device_info = "DisplayDeviceInfo{" in stripped

        line_ids = []
        for pat in DISPLAY_ID_PATTERNS:
            for match in pat.finditer(raw_line):
                did = match.group(1)
                declared_ids.add(did)
                states_by_id.setdefault(did, set())
                line_ids.append(did)
        unique_line_ids = sorted(set(line_ids))

        for m_glob in GLOBAL_DISPLAY_STATE_RE.finditer(raw_line):
            global_states.add(m_glob.group(1))

        line_states = []
        for pat in LOCAL_DISPLAY_STATE_PATTERNS:
            for match in pat.finditer(raw_line):
                line_states.append(match.group(1))

        if len(unique_line_ids) > 1:
            current_display_id = None
            current_header_indent = None
            current_header_is_block = False
            if line_states:
                ambiguous_lines.append((unique_line_ids, line_states))
            continue

        if len(unique_line_ids) == 1:
            matched_id = unique_line_ids[0]
            if is_inline_device_info:
                if line_states:
                    states_by_id.setdefault(matched_id, set()).update(line_states)
                current_display_id = None
                current_header_indent = None
                current_header_is_block = False
                continue
            current_display_id = matched_id
            current_header_indent = indent
            current_header_is_block = stripped.endswith(":")
            if line_states:
                states_by_id.setdefault(current_display_id, set()).update(line_states)
            continue

        # No Display ID on this line: check if we crossed a section boundary before applying current_display_id
        if is_inline_device_info:
            current_display_id = None
            current_header_indent = None
            current_header_is_block = False
        elif current_display_id is not None:
            if not line_states and TOP_SECTION_BOUNDARY_RE.match(stripped):
                current_display_id = None
                current_header_indent = None
                current_header_is_block = False
            elif current_header_indent is not None and indent < current_header_indent:
                current_display_id = None
                current_header_indent = None
                current_header_is_block = False
            elif (
                current_header_indent is not None
                and indent <= current_header_indent
                and (
                    (current_header_is_block and indent == current_header_indent)
                    or (not line_states and GENERIC_SECTION_HEADER_RE.match(stripped))
                )
            ):
                current_display_id = None
                current_header_indent = None
                current_header_is_block = False

        if line_states:
            if current_display_id is not None:
                states_by_id.setdefault(current_display_id, set()).update(line_states)
            else:
                unscoped_states.update(line_states)

    return {
        "source": source_label,
        "declared_ids": declared_ids,
        "states_by_id": states_by_id,
        "unscoped_states": unscoped_states,
        "global_states": global_states,
        "ambiguous_lines": ambiguous_lines,
    }


def parse_power_and_display_state(dumpsys_power, dumpsys_display="", target_display_id="0"):
    """Strictly parse Awake vs Doze/AOD state with explicit per-Display-ID mapping (AG01-AUD-04 & AG01-AUD-05).

    Rules:
    - Explicitly maps display state observations to each Display ID across `dumpsys power` and `dumpsys display`.
    - Duplicate observations on a single Display ID (e.g. `Display Power: state=ON` and `mScreenState=ON` on Display 0)
      collapse into Display 0's set and NEVER masquerade as state evidence for Display 1.
    - If ANY declared Display ID has no state observation, or has conflicting states, or if multiple Display IDs
      disagree, or if the target display (`target_display_id`, default `"0"`) is absent/unconfirmed, returns
      `status="UNKNOWN"`, `is_active=False`, `is_aod=False`.
    - Conflicts between `dumpsys power`, `dumpsys display`, `mGlobalDisplayState`, `mWakefulness`, or incoherent
      wakefulness/display pairs (`Awake+DOZE`, `Dozing+ON`, `Awake+OFF`) ALWAYS return `status="UNKNOWN"`.
    """
    target_id = str(target_display_id)
    wake_matches = re.findall(r"\bmWakefulness=([A-Za-z_]+)\b", dumpsys_power or "")
    unique_wakes = sorted(set(wake_matches))

    power_parsed = _extract_display_states_by_id(dumpsys_power, "power")
    display_parsed = _extract_display_states_by_id(dumpsys_display, "display")

    declared_ids = sorted(power_parsed["declared_ids"] | display_parsed["declared_ids"], key=lambda x: int(x))
    states_by_id = {}
    for did in declared_ids:
        combined = set(power_parsed["states_by_id"].get(did, set())) | set(display_parsed["states_by_id"].get(did, set()))
        states_by_id[did] = sorted(combined)

    unscoped_states = sorted(power_parsed["unscoped_states"] | display_parsed["unscoped_states"])
    global_states = sorted(power_parsed["global_states"] | display_parsed["global_states"])
    ambiguous_lines = power_parsed["ambiguous_lines"] + display_parsed["ambiguous_lines"]

    all_observed_display_states = sorted(
        set(unscoped_states)
        | set(global_states)
        | {st for sts in states_by_id.values() for st in sts}
    )

    def _unknown(reason, wake_val="UNKNOWN", disp_val="UNKNOWN"):
        return {
            "status": "UNKNOWN",
            "wakefulness": wake_val,
            "display_state": disp_val,
            "target_display_id": target_id,
            "observed_wakefulness": unique_wakes,
            "observed_display_states": all_observed_display_states,
            "observed_display_ids": declared_ids,
            "display_states_by_id": states_by_id,
            "unscoped_display_states": unscoped_states,
            "global_display_states": global_states,
            "is_active": False,
            "is_aod": False,
            "reason": reason,
        }

    if len(unique_wakes) == 0:
        return _unknown("No mWakefulness field found in dumpsys power")
    if len(unique_wakes) > 1 or unique_wakes[0] not in VALID_WAKEFULNESS_STATES:
        return _unknown(
            f"Conflicting or invalid mWakefulness values observed: {unique_wakes}",
            wake_val="CONFLICT" if len(unique_wakes) > 1 else unique_wakes[0],
        )
    wakefulness = unique_wakes[0]

    if ambiguous_lines:
        return _unknown(
            f"Ambiguous display state line(s) referencing multiple Display IDs simultaneously: {ambiguous_lines}",
            wake_val=wakefulness,
            disp_val="AMBIGUOUS_DISPLAY_LINE",
        )

    # Global display state conflict / validity check
    if len(global_states) > 1:
        return _unknown(
            f"Conflicting mGlobalDisplayState values observed: {global_states}",
            wake_val=wakefulness,
            disp_val="CONFLICT",
        )
    if global_states and global_states[0] not in VALID_DISPLAY_STATES:
        return _unknown(
            f"Invalid mGlobalDisplayState value observed: {global_states[0]}",
            wake_val=wakefulness,
            disp_val=global_states[0],
        )

    if declared_ids:
        # If a single dump text declared explicit Display ID(s) AND also had unscoped local display states outside
        # any Display ID section (e.g. after a section boundary or an ID-less DisplayDeviceInfo), refuse to guess which
        # display that unscoped state belongs to (R07 Defect 5).
        for parsed_src in (power_parsed, display_parsed):
            if parsed_src["declared_ids"] and parsed_src["unscoped_states"]:
                return _unknown(
                    f"Dump '{parsed_src['source']}' contains both Display-ID-scoped sections ({sorted(parsed_src['declared_ids'])}) "
                    f"and unscoped display states ({sorted(parsed_src['unscoped_states'])}) across section boundaries",
                    wake_val=wakefulness,
                    disp_val="UNSCOPED_STATE_IN_SCOPED_DUMP",
                )
        # Every declared Display ID must have at least one explicit state observation (duplicate lines on another ID never count!)
        missing_ids = [did for did in declared_ids if not states_by_id[did]]
        if missing_ids:
            return _unknown(
                f"Display ID(s) {missing_ids} declared without explicit per-display state mapping (states_by_id={states_by_id})",
                wake_val=wakefulness,
                disp_val="INCOMPLETE_DISPLAY_MAPPING",
            )
        # No individual Display ID may report conflicting or invalid states
        for did, sts in states_by_id.items():
            if len(sts) > 1:
                return _unknown(
                    f"Conflicting display states observed for Display Id={did}: {sts}",
                    wake_val=wakefulness,
                    disp_val="CONFLICT",
                )
            if sts[0] not in VALID_DISPLAY_STATES:
                return _unknown(
                    f"Invalid display state '{sts[0]}' observed for Display Id={did}",
                    wake_val=wakefulness,
                    disp_val=sts[0],
                )
        # Target display must be explicitly present and mapped
        if target_id not in states_by_id:
            return _unknown(
                f"Target display Id={target_id} is missing from declared displays {declared_ids}; cannot confirm target display state",
                wake_val=wakefulness,
                disp_val="TARGET_DISPLAY_MISSING",
            )
        # Cross-display consistency: all declared displays must agree (no hidden multi-display contradiction)
        distinct_per_display = sorted({sts[0] for sts in states_by_id.values()})
        if len(distinct_per_display) > 1:
            return _unknown(
                f"Conflicting states across multiple displays: {states_by_id}",
                wake_val=wakefulness,
                disp_val="CONFLICT",
            )
        target_state = states_by_id[target_id][0]
        # Any unscoped or global state must agree with the target display state
        if unscoped_states and (len(unscoped_states) > 1 or unscoped_states[0] != target_state):
            return _unknown(
                f"Unscoped display state(s) {unscoped_states} conflict with target Display Id={target_id} state '{target_state}'",
                wake_val=wakefulness,
                disp_val="CONFLICT",
            )
        if global_states and global_states[0] != target_state:
            return _unknown(
                f"mGlobalDisplayState='{global_states[0]}' conflicts with target Display Id={target_id} state '{target_state}'",
                wake_val=wakefulness,
                disp_val="CONFLICT",
            )
        display_state = target_state
    else:
        # No Display ID headers in dumpsys output
        if target_id != "0":
            return _unknown(
                f"Cannot confirm non-default target Display Id={target_id} when dumpsys output omits Display IDs",
                wake_val=wakefulness,
                disp_val="TARGET_DISPLAY_MISSING",
            )
        combined_unscoped = sorted(set(unscoped_states) | set(global_states))
        if len(combined_unscoped) == 0:
            return _unknown(
                "No display state found in dumpsys power or dumpsys display",
                wake_val=wakefulness,
                disp_val="UNKNOWN",
            )
        if len(combined_unscoped) > 1 or combined_unscoped[0] not in VALID_DISPLAY_STATES:
            return _unknown(
                f"Conflicting or invalid display states observed across power/display: {combined_unscoped}",
                wake_val=wakefulness,
                disp_val="CONFLICT" if len(combined_unscoped) > 1 else combined_unscoped[0],
            )
        display_state = combined_unscoped[0]

    base_meta = {
        "wakefulness": wakefulness,
        "display_state": display_state,
        "target_display_id": target_id,
        "observed_wakefulness": unique_wakes,
        "observed_display_states": all_observed_display_states,
        "observed_display_ids": declared_ids,
        "display_states_by_id": states_by_id,
        "unscoped_display_states": unscoped_states,
        "global_display_states": global_states,
    }

    if wakefulness == "Awake" and display_state == "ON":
        return {**base_meta, "status": "ACTIVE", "is_active": True, "is_aod": False}
    if wakefulness in ("Dozing", "Asleep") and display_state in ("DOZE", "DOZE_SUSPEND"):
        return {**base_meta, "status": "AOD", "is_active": False, "is_aod": True}
    if wakefulness in ("Dozing", "Asleep") and display_state == "OFF":
        return {
            **base_meta,
            "status": "SCREEN_OFF",
            "is_active": False,
            "is_aod": False,
            "reason": f"Display is OFF while {wakefulness} (screen off, not AOD)",
        }

    return _unknown(
        f"Incoherent or transitional wakefulness/display combination: wakefulness={wakefulness}, display_state={display_state}",
        wake_val=wakefulness,
        disp_val=display_state,
    )


def verify_active_watchface_selected(dumpsys_wallpaper, expected_package):
    """Verify from `dumpsys wallpaper` that `expected_package` is the active current-user watch face (AG01-AUD-04 & R05)."""
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


def validate_png_bytes(
    data,
    min_width=1,
    min_height=1,
    max_input_bytes=PNG_MAX_INPUT_BYTES,
    max_width=PNG_MAX_WIDTH,
    max_height=PNG_MAX_HEIGHT,
    max_decompressed_bytes=PNG_MAX_DECOMPRESSED_BYTES,
):
    """Validate bounded PNG structure and integrity (ISO/IEC 15948, AG01-AUD-06) using Python stdlib only.

    Checks:
    1. Input byte size bounds (`33 <= len(data) <= max_input_bytes`) and exact 8-byte signature.
    2. Complete chunk framing without truncation or trailing bytes after `IEND`.
    3. CRC-32 checksum verification for EVERY chunk.
    4. First chunk is 13-byte `IHDR` (no duplicate `IHDR`), width/height within `[min, max]` bounds,
       valid color_type/bit_depth, compression=0, filter=0, and **interlace=0 ONLY** (explicitly rejects Adam7/unsupported interlace).
    5. Strict chunk ordering and structure:
       - Rejects non-contiguous `IDAT` chunks.
       - Rejects duplicate `PLTE`, `PLTE` after `IDAT`, `PLTE` on grayscale, or missing `PLTE` on indexed-color (`color_type=3`).
       - Rejects unknown critical chunks (`not (chunk_type[0] & 32)`) and APNG animation chunks (`acTL`, `fcTL`, `fdAT`).
    6. Enforces `max_decompressed_bytes` BEFORE inflating, decompresses with `zlib.decompressobj()` bounded to
       `expected_len + 1`, and strictly checks `inflater.eof`, empty `inflater.unused_data`, empty
       `inflater.unconsumed_tail`, exact scanline length, and valid filter byte (`0..4`) on every row.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise RuntimeError("PNG capture output is not bytes")
    raw = bytes(data)
    if len(raw) > max_input_bytes:
        raise RuntimeError(f"PNG input size {len(raw)} bytes exceeds upper limit {max_input_bytes} bytes")
    if len(raw) < 33 or raw[:8] != PNG_SIGNATURE:
        raise RuntimeError("Invalid PNG signature or truncated PNG header")

    offset = 8
    chunk_count = 0
    ihdr = None
    saw_plte = False
    idat_parts = []
    idat_closed = False
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
            if width > max_width or height > max_height:
                raise RuntimeError(f"PNG dimensions {width}x{height} exceed upper limit {max_width}x{max_height}")
            if color_type not in PNG_COLOR_CHANNELS:
                raise RuntimeError(f"Unsupported PNG color_type={color_type}")
            channels, allowed_depths = PNG_COLOR_CHANNELS[color_type]
            if bit_depth not in allowed_depths:
                raise RuntimeError(f"Invalid PNG bit_depth={bit_depth} for color_type={color_type}")
            if compression != 0 or filter_method != 0:
                raise RuntimeError(
                    f"Invalid PNG header flags: compression={compression}, filter={filter_method}"
                )
            if interlace != 0:
                raise RuntimeError(
                    f"Unsupported PNG interlace method={interlace} (only non-interlaced interlace=0 is supported)"
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
            if saw_plte:
                raise RuntimeError("Duplicate PLTE chunk found in PNG stream")
            if idat_parts:
                raise RuntimeError("Invalid PNG chunk order: PLTE chunk appeared after IDAT")
            if ihdr["color_type"] in (0, 4):
                raise RuntimeError(f"Invalid PNG chunk: PLTE is prohibited for grayscale color_type={ihdr['color_type']}")
            max_palette_bytes = 3 * min(256, 1 << ihdr["bit_depth"]) if ihdr["color_type"] == 3 else 768
            if length == 0 or length % 3 != 0 or length > max_palette_bytes:
                raise RuntimeError(f"Invalid PNG PLTE chunk length: {length} (max {max_palette_bytes})")
            saw_plte = True
        elif chunk_type == b"IDAT":
            if idat_closed:
                raise RuntimeError("Invalid PNG chunk order: non-contiguous IDAT chunks separated by another chunk")
            if ihdr["color_type"] == 3 and not saw_plte:
                raise RuntimeError("Indexed-color PNG (color_type=3) is missing required PLTE chunk before IDAT")
            idat_parts.append(chunk_data)
        elif chunk_type == b"IEND":
            if length != 0:
                raise RuntimeError(f"PNG IEND chunk must have 0 length, got {length}")
            saw_iend = True
        else:
            if chunk_type == b"tRNS" and idat_parts:
                raise RuntimeError("Invalid PNG chunk order: tRNS chunk appeared after IDAT")
            if chunk_type in PNG_DISALLOWED_ANIMATION_CHUNKS:
                raise RuntimeError(f"Unsupported APNG animation chunk {chunk_type.decode('ascii')} in static capture PNG")
            if chunk_type not in PNG_KNOWN_CRITICAL_CHUNKS and not (chunk_type[0] & 32):
                raise RuntimeError(f"Unsupported unknown critical PNG chunk {chunk_type.decode('ascii')}")
            if idat_parts:
                idat_closed = True

        offset = crc_end

    if ihdr is None:
        raise RuntimeError("PNG missing IHDR chunk")
    if not idat_parts:
        raise RuntimeError("PNG missing IDAT image data chunk")
    if not saw_iend:
        raise RuntimeError("PNG missing terminating IEND chunk")

    bits_per_pixel = ihdr["channels"] * ihdr["bit_depth"]
    row_bytes = (ihdr["width"] * bits_per_pixel + 7) // 8
    stride = 1 + row_bytes
    expected_decompressed_len = ihdr["height"] * stride
    if expected_decompressed_len > max_decompressed_bytes:
        raise RuntimeError(
            f"PNG decompressed payload size {expected_decompressed_len} bytes exceeds upper limit {max_decompressed_bytes} bytes"
        )

    idat_payload = b"".join(idat_parts)
    inflater = zlib.decompressobj()
    try:
        decompressed = inflater.decompress(idat_payload, expected_decompressed_len + 1)
    except zlib.error as exc:
        raise RuntimeError(f"Corrupt PNG IDAT zlib stream: {exc}") from exc

    if inflater.unconsumed_tail or len(decompressed) > expected_decompressed_len:
        raise RuntimeError(
            f"PNG IDAT zlib stream produced data beyond expected decompressed limit "
            f"(got {len(decompressed)} bytes, unconsumed={len(inflater.unconsumed_tail)})"
        )
    try:
        flushed = inflater.flush(expected_decompressed_len + 1 - len(decompressed))
    except zlib.error as exc:
        raise RuntimeError(f"Corrupt PNG IDAT zlib stream on flush: {exc}") from exc
    if flushed:
        decompressed += flushed

    if not inflater.eof:
        raise RuntimeError("Truncated/unterminated PNG IDAT zlib stream (inflater.eof is False)")
    if inflater.unused_data:
        raise RuntimeError(
            f"Trailing {len(inflater.unused_data)} unused byte(s) found after PNG IDAT zlib stream end"
        )
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
        "interlace": ihdr["interlace"],
        "chunk_count": chunk_count,
        "decompressed_bytes": len(decompressed),
        "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _iter_iso_bmff_boxes(raw, start, end):
    """Strictly parse ISO Base Media File Format (ISO/IEC 14496-12) boxes within [start, end)."""
    pos = start
    boxes = []
    while pos < end:
        if pos + 8 > end:
            raise RuntimeError(f"Truncated MP4 box header at offset {pos} (end={end})")
        size32, box_type = struct.unpack(">I4s", raw[pos:pos + 8])
        if not all(32 <= b <= 126 for b in box_type):
            raise RuntimeError(f"Invalid non-printable MP4 box type {box_type!r} at offset {pos}")
        header_len = 8
        if size32 == 1:
            if pos + 16 > end:
                raise RuntimeError(f"Truncated 64-bit MP4 box header for {box_type!r} at offset {pos}")
            box_size = struct.unpack(">Q", raw[pos + 8:pos + 16])[0]
            header_len = 16
        elif size32 == 0:
            box_size = end - pos
        else:
            box_size = size32
        if box_size < header_len:
            raise RuntimeError(f"Invalid MP4 box size {box_size} (< {header_len}) for {box_type!r} at offset {pos}")
        box_end = pos + box_size
        if box_end > end:
            raise RuntimeError(
                f"Truncated MP4 box {box_type.decode('ascii', errors='replace')}: declared end {box_end} > container end {end}"
            )
        boxes.append({
            "type": box_type,
            "start": pos,
            "payload_start": pos + header_len,
            "end": box_end,
            "size": box_size,
        })
        pos = box_end
    return boxes


def parse_and_validate_mp4_structure(data, min_size_bytes=MP4_MIN_BYTES, max_size_bytes=MP4_MAX_BYTES):
    """Validate MP4 ISO BMFF box framing, video track (`vide`), sample table (`stsd`/`stsz`/`stco|co64`), and `mdat` bounds (AG01-AUD-07)."""
    if not isinstance(data, (bytes, bytearray)):
        raise RuntimeError("MP4 recording data is not bytes")
    raw = bytes(data)
    if len(raw) < min_size_bytes:
        raise RuntimeError(f"Invalid or truncated MP4 recording: size={len(raw)} bytes (expected >= {min_size_bytes} bytes)")
    if len(raw) > max_size_bytes:
        raise RuntimeError(f"MP4 recording size {len(raw)} bytes exceeds upper limit {max_size_bytes} bytes")

    top_boxes = _iter_iso_bmff_boxes(raw, 0, len(raw))
    if not top_boxes or top_boxes[0]["type"] != b"ftyp":
        raise RuntimeError("Invalid MP4 file: first top-level box must be 'ftyp'")
    ftyp = top_boxes[0]
    if ftyp["end"] - ftyp["payload_start"] < 8:
        raise RuntimeError("Invalid MP4 'ftyp' box: payload shorter than 8 bytes")
    major_brand = raw[ftyp["payload_start"]:ftyp["payload_start"] + 4].decode("ascii", errors="replace")

    moov_boxes = [b for b in top_boxes if b["type"] == b"moov"]
    mdat_boxes = [b for b in top_boxes if b["type"] == b"mdat"]
    if len(moov_boxes) != 1:
        raise RuntimeError(f"Invalid MP4 structure: expected exactly 1 'moov' box, found {len(moov_boxes)}")
    if not mdat_boxes:
        raise RuntimeError("Invalid MP4 structure: missing 'mdat' media data box")

    mdat_ranges = [(b["payload_start"], b["end"]) for b in mdat_boxes]
    mdat_payload_bytes = sum(end - start for start, end in mdat_ranges)
    if mdat_payload_bytes <= 0:
        raise RuntimeError("Invalid MP4 structure: 'mdat' box contains 0 payload bytes")

    moov = moov_boxes[0]
    moov_children = _iter_iso_bmff_boxes(raw, moov["payload_start"], moov["end"])
    traks = [b for b in moov_children if b["type"] == b"trak"]
    if not traks:
        raise RuntimeError("Invalid MP4 structure: 'moov' contains no 'trak' boxes")

    video_tracks = []
    for trak in traks:
        trak_children = _iter_iso_bmff_boxes(raw, trak["payload_start"], trak["end"])
        mdias = [b for b in trak_children if b["type"] == b"mdia"]
        if len(mdias) != 1:
            continue
        mdia = mdias[0]
        mdia_children = _iter_iso_bmff_boxes(raw, mdia["payload_start"], mdia["end"])
        hdlrs = [b for b in mdia_children if b["type"] == b"hdlr"]
        if len(hdlrs) != 1:
            continue
        hdlr = hdlrs[0]
        if hdlr["end"] - hdlr["payload_start"] < 12:
            raise RuntimeError("Truncated MP4 'hdlr' box inside 'mdia'")
        handler_type = raw[hdlr["payload_start"] + 8:hdlr["payload_start"] + 12]
        if handler_type != b"vide":
            continue

        minfs = [b for b in mdia_children if b["type"] == b"minf"]
        if len(minfs) != 1:
            raise RuntimeError("Video 'trak/mdia' is missing 'minf' box")
        minf_children = _iter_iso_bmff_boxes(raw, minfs[0]["payload_start"], minfs[0]["end"])
        stbls = [b for b in minf_children if b["type"] == b"stbl"]
        if len(stbls) != 1:
            raise RuntimeError("Video 'minf' is missing 'stbl' sample table box")
        stbl_children = _iter_iso_bmff_boxes(raw, stbls[0]["payload_start"], stbls[0]["end"])

        # R07 Defect 3: Reject duplicate sample table boxes or mutually exclusive box pairs in stbl
        singular_stbl_types = {b"stsd", b"stsz", b"stz2", b"stsc", b"stco", b"co64", b"stts", b"ctts", b"stss"}
        stbl_by_type = {}
        for child in stbl_children:
            ctype = child["type"]
            if ctype in singular_stbl_types and ctype in stbl_by_type:
                raise RuntimeError(
                    f"Duplicate '{ctype.decode('ascii', errors='replace')}' sample table box inside video 'stbl'"
                )
            stbl_by_type[ctype] = child
        if b"stz2" in stbl_by_type:
            raise RuntimeError("Unsupported or conflicting 'stz2' compact sample size box in video 'stbl'")
        if b"stco" in stbl_by_type and b"co64" in stbl_by_type:
            raise RuntimeError("Conflicting 'stco' and 'co64' chunk offset boxes both present in video 'stbl'")

        # Validate stsd (sample description / codec)
        stsd = stbl_by_type.get(b"stsd")
        if stsd is None or (stsd["end"] - stsd["payload_start"]) < 16:
            raise RuntimeError("Video 'stbl' is missing valid 'stsd' sample description box")
        stsd_entry_count = struct.unpack(">I", raw[stsd["payload_start"] + 4:stsd["payload_start"] + 8])[0]
        if stsd_entry_count < 1:
            raise RuntimeError("Video 'stsd' declares 0 sample description entries")
        codec_boxes = _iter_iso_bmff_boxes(raw, stsd["payload_start"] + 8, stsd["end"])
        if len(codec_boxes) != stsd_entry_count:
            raise RuntimeError(
                f"Video 'stsd' entry_count ({stsd_entry_count}) does not match parsed codec entry boxes ({len(codec_boxes)})"
            )
        codec_fourcc = codec_boxes[0]["type"].decode("ascii", errors="replace")

        # Validate stsz (sample sizes & sample count >= 1)
        stsz = stbl_by_type.get(b"stsz")
        if stsz is None or (stsz["end"] - stsz["payload_start"]) < 12:
            raise RuntimeError("Video 'stbl' is missing valid 'stsz' sample size box")
        uniform_sample_size, sample_count = struct.unpack(">II", raw[stsz["payload_start"] + 4:stsz["payload_start"] + 12])
        if sample_count < 1:
            raise RuntimeError("Video track declares 0 samples in 'stsz'")
        if uniform_sample_size > 0:
            if (stsz["end"] - stsz["payload_start"]) != 12:
                raise RuntimeError("Video 'stsz' with non-zero uniform sample_size has unexpected trailing entry bytes")
            sample_sizes = [uniform_sample_size] * sample_count
        else:
            table_start = stsz["payload_start"] + 12
            table_end = table_start + (4 * sample_count)
            if table_end != stsz["end"]:
                raise RuntimeError(
                    f"Video 'stsz' sample size table length mismatch: expected end {table_end}, actual box end {stsz['end']}"
                )
            sample_sizes = list(struct.unpack(f">{sample_count}I", raw[table_start:table_end]))
            if any(sz == 0 for sz in sample_sizes):
                raise RuntimeError("Video 'stsz' contains 0-byte sample entry")
        total_sample_bytes = sum(sample_sizes)
        if total_sample_bytes <= 0 or total_sample_bytes > mdat_payload_bytes:
            raise RuntimeError(
                f"Video sample byte total ({total_sample_bytes}) is invalid relative to 'mdat' payload ({mdat_payload_bytes})"
            )

        # Validate stco / co64 chunk offsets
        stco = stbl_by_type.get(b"stco")
        co64 = stbl_by_type.get(b"co64")
        if stco is None and co64 is None:
            raise RuntimeError("Video 'stbl' is missing both 'stco' and 'co64' chunk offset boxes")
        chunk_offsets = []
        if stco is not None:
            if (stco["end"] - stco["payload_start"]) < 8:
                raise RuntimeError("Truncated 'stco' box")
            entry_cnt = struct.unpack(">I", raw[stco["payload_start"] + 4:stco["payload_start"] + 8])[0]
            if entry_cnt < 1 or (stco["payload_start"] + 8 + 4 * entry_cnt) != stco["end"]:
                raise RuntimeError("Invalid or mismatched 'stco' chunk offset table length")
            chunk_offsets.extend(struct.unpack(f">{entry_cnt}I", raw[stco["payload_start"] + 8:stco["end"]]))
        if co64 is not None:
            if (co64["end"] - co64["payload_start"]) < 8:
                raise RuntimeError("Truncated 'co64' box")
            entry_cnt = struct.unpack(">I", raw[co64["payload_start"] + 4:co64["payload_start"] + 8])[0]
            if entry_cnt < 1 or (co64["payload_start"] + 8 + 8 * entry_cnt) != co64["end"]:
                raise RuntimeError("Invalid or mismatched 'co64' chunk offset table length")
            chunk_offsets.extend(struct.unpack(f">{entry_cnt}Q", raw[co64["payload_start"] + 8:co64["end"]]))

        chunk_count = len(chunk_offsets)
        if sample_count < chunk_count:
            raise RuntimeError(
                f"Invalid MP4 sample-to-chunk count: sample_count ({sample_count}) < chunk_count ({chunk_count})"
            )

        # Validate stsc (Sample-To-Chunk correspondence) and determine exact sample count per chunk (R07 Defect 3)
        stsc = stbl_by_type.get(b"stsc")
        if stsc is not None:
            if (stsc["end"] - stsc["payload_start"]) < 8:
                raise RuntimeError("Truncated 'stsc' sample-to-chunk box")
            stsc_entry_count = struct.unpack(">I", raw[stsc["payload_start"] + 4:stsc["payload_start"] + 8])[0]
            expected_stsc_end = stsc["payload_start"] + 8 + (12 * stsc_entry_count)
            if stsc_entry_count < 1 or expected_stsc_end != stsc["end"]:
                raise RuntimeError("Invalid or truncated 'stsc' sample-to-chunk entry table")
            stsc_entries = []
            prev_first_chunk = 0
            for idx in range(stsc_entry_count):
                e_off = stsc["payload_start"] + 8 + (12 * idx)
                first_chunk, samples_per_chunk, sdi = struct.unpack(">III", raw[e_off:e_off + 12])
                if idx == 0 and first_chunk != 1:
                    raise RuntimeError(f"Invalid 'stsc': first entry must start at first_chunk=1, got {first_chunk}")
                if first_chunk <= prev_first_chunk or first_chunk > chunk_count:
                    raise RuntimeError(
                        f"Invalid 'stsc' first_chunk={first_chunk} (prev={prev_first_chunk}, chunk_count={chunk_count})"
                    )
                if samples_per_chunk < 1:
                    raise RuntimeError("Invalid 'stsc': samples_per_chunk must be >= 1")
                if sdi < 1 or sdi > stsd_entry_count:
                    raise RuntimeError(
                        f"Invalid 'stsc': sample_description_index={sdi} out of range 1..{stsd_entry_count}"
                    )
                stsc_entries.append((first_chunk, samples_per_chunk, sdi))
                prev_first_chunk = first_chunk

            samples_per_chunk_list = []
            for idx, (first_chunk, samples_per_chunk, _) in enumerate(stsc_entries):
                next_first = stsc_entries[idx + 1][0] if (idx + 1) < len(stsc_entries) else (chunk_count + 1)
                run_chunks = next_first - first_chunk
                samples_per_chunk_list.extend([samples_per_chunk] * run_chunks)

            mapped_sample_total = sum(samples_per_chunk_list)
            if mapped_sample_total != sample_count:
                raise RuntimeError(
                    f"MP4 'stsc' mapped sample count ({mapped_sample_total}) does not match 'stsz' sample_count ({sample_count})"
                )
        else:
            if chunk_count > 1:
                raise RuntimeError(
                    f"Video 'stbl' has {chunk_count} chunks in 'stco'/'co64' but is missing required 'stsc' sample-to-chunk box"
                )
            samples_per_chunk_list = [sample_count]

        # Verify every chunk's exact cumulative sample byte span fits inside a single mdat box without overlapping
        sample_cursor = 0
        chunk_spans = []
        for chunk_idx, (off, n_samples) in enumerate(zip(chunk_offsets, samples_per_chunk_list)):
            chunk_byte_size = sum(sample_sizes[sample_cursor:sample_cursor + n_samples])
            sample_cursor += n_samples
            chunk_end = off + chunk_byte_size
            if not any(m_start <= off and chunk_end <= m_end for m_start, m_end in mdat_ranges):
                raise RuntimeError(
                    f"Video chunk #{chunk_idx + 1} byte span [{off}, {chunk_end}) ({n_samples} samples, {chunk_byte_size} bytes) "
                    f"overflows 'mdat' payload bounds {mdat_ranges}"
                )
            chunk_spans.append((off, chunk_end, chunk_idx + 1))

        sorted_spans = sorted(chunk_spans, key=lambda item: item[0])
        for prev_span, curr_span in zip(sorted_spans, sorted_spans[1:]):
            if prev_span[1] > curr_span[0]:
                raise RuntimeError(
                    f"Overlapping video chunk byte spans in 'mdat': chunk #{prev_span[2]} [{prev_span[0]}, {prev_span[1]}) "
                    f"overlaps chunk #{curr_span[2]} [{curr_span[0]}, {curr_span[1]})"
                )

        video_tracks.append({
            "codec": codec_fourcc,
            "sample_count": sample_count,
            "total_sample_bytes": total_sample_bytes,
            "chunk_offset_count": len(chunk_offsets),
        })

    if not video_tracks:
        raise RuntimeError("Invalid MP4 structure: no video ('vide') track found inside 'moov'")

    return {
        "major_brand": major_brand,
        "top_level_boxes": [b["type"].decode("ascii", errors="replace") for b in top_boxes],
        "mdat_payload_bytes": mdat_payload_bytes,
        "video_track_count": len(video_tracks),
        "video_tracks": video_tracks,
        "sample_count": sum(t["sample_count"] for t in video_tracks),
        "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def validate_mp4_bytes(data, min_size_bytes=MP4_MIN_BYTES):
    """Validate MP4 box structure, video track, and sample table presence; returns verified byte length."""
    meta = parse_and_validate_mp4_structure(data, min_size_bytes=min_size_bytes)
    return meta["size_bytes"]


def verify_mp4_video_artifact(mp4_path, data=None, ffprobe_bin=None, probe_runner=None):
    """Verify MP4 container structure AND actual decodable video frames via `ffprobe` (AG01-AUD-07).

    - Structural MP4 box/track/sample errors ALWAYS raise `RuntimeError`.
    - If `ffprobe` (and custom `probe_runner`) is NOT installed/available, NEVER claims PASS; returns
      `status="NOT_RUN"`, `video_verification_status="NOT RUN"`, `frames_verified=False`.
    - When `ffprobe` runs, requires rc=0, at least one video stream with `width > 0`, `height > 0`,
      and `nb_read_frames >= 1` (actual decoded frames present).
    """
    path = Path(mp4_path)
    raw = bytes(data) if data is not None else path.read_bytes()
    container = parse_and_validate_mp4_structure(raw)

    if probe_runner is None:
        resolved_probe = str(ffprobe_bin) if ffprobe_bin else shutil.which("ffprobe")
        if not resolved_probe or not Path(resolved_probe).is_file():
            return {
                "status": "NOT_RUN",
                "video_verification_status": "NOT RUN",
                "frames_verified": False,
                "decoded_frame_count": None,
                "probe_tool": None,
                "reason": "ffprobe binary not found; actual video frame decode verification is NOT RUN",
                "container": container,
            }

        def _run_ffprobe(cmd, timeout=60):
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
            )

        runner_fn = _run_ffprobe
    else:
        resolved_probe = str(ffprobe_bin or "ffprobe")
        runner_fn = probe_runner

    cmd = [
        resolved_probe,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-count_frames",
        "-show_entries",
        "stream=codec_type,codec_name,width,height,nb_frames,nb_read_frames",
        "-of",
        "json",
        str(path),
    ]
    try:
        proc = runner_fn(cmd, timeout=60)
    except FileNotFoundError:
        return {
            "status": "NOT_RUN",
            "video_verification_status": "NOT RUN",
            "frames_verified": False,
            "decoded_frame_count": None,
            "probe_tool": None,
            "reason": f"ffprobe executable '{resolved_probe}' not found; actual video frame decode verification is NOT RUN",
            "container": container,
        }
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"ffprobe timed out after 60s while verifying {path}") from exc

    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed (rc={proc.returncode}) on {path}: {(proc.stderr or proc.stdout).strip()}")

    stderr_diag = (proc.stderr or "").strip()
    if stderr_diag:
        raise RuntimeError(
            f"ffprobe reported stream decoding error(s) on stderr for {path} (partial or corrupt video rejected): {stderr_diag}"
        )

    try:
        parsed = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON from ffprobe: {exc}") from exc

    if parsed.get("error"):
        raise RuntimeError(f"ffprobe reported error payload for {path}: {parsed.get('error')}")

    streams = parsed.get("streams") or []
    if not streams:
        raise RuntimeError(f"ffprobe found 0 video streams in {path}")
    vstream = streams[0]
    if vstream.get("codec_type") != "video":
        raise RuntimeError(
            f"ffprobe stream is missing or has non-video codec_type={vstream.get('codec_type')!r} (must be explicitly 'video')"
        )
    codec_name = (vstream.get("codec_name") or "").strip()
    if not codec_name or codec_name == "unknown":
        raise RuntimeError(f"ffprobe stream is missing valid codec_name (got {vstream.get('codec_name')!r})")

    width = int(vstream.get("width") or 0)
    height = int(vstream.get("height") or 0)
    raw_frames = vstream.get("nb_read_frames")
    try:
        decoded_frames = int(raw_frames)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"ffprobe did not report countable nb_read_frames (got {raw_frames!r})") from exc

    if width <= 0 or height <= 0:
        raise RuntimeError(f"ffprobe reported invalid video dimensions {width}x{height}")
    if decoded_frames < 1:
        raise RuntimeError(f"ffprobe decoded 0 video frames in {path}")

    expected_container_frames = container["video_tracks"][0]["sample_count"]
    raw_nb_frames = vstream.get("nb_frames")
    declared_nb_frames = None
    if raw_nb_frames not in (None, "", "N/A"):
        try:
            declared_nb_frames = int(raw_nb_frames)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"ffprobe reported invalid nb_frames={raw_nb_frames!r}") from exc
        if declared_nb_frames != expected_container_frames:
            raise RuntimeError(
                f"Video stream nb_frames ({declared_nb_frames}) does not match MP4 container sample_count ({expected_container_frames})"
            )

    if decoded_frames != expected_container_frames:
        raise RuntimeError(
            f"Partial video decoding detected in {path}: decoded {decoded_frames} frame(s), "
            f"but MP4 container declares {expected_container_frames} frame sample(s)"
        )

    return {
        "status": "VERIFIED",
        "video_verification_status": "PASS",
        "frames_verified": True,
        "decoded_frame_count": decoded_frames,
        "expected_frame_count": expected_container_frames,
        "codec_name": codec_name,
        "width": width,
        "height": height,
        "probe_tool": resolved_probe,
        "container": container,
    }


def _write_new_evidence_file(path, data):
    """Write a new evidence artifact exclusively without EVER overwriting an existing file (AG01-AUD-09)."""
    target = Path(path)
    if target.exists():
        raise EvidenceOverwriteError(f"Refusing to overwrite existing evidence file: {target}")
    try:
        with target.open("xb") as fh:
            fh.write(data)
    except FileExistsError as exc:
        raise EvidenceOverwriteError(f"Refusing to overwrite existing evidence file: {target}") from exc


def _promote_staged_evidence_file(staged_path, final_path):
    """Promote a validated temporary file to final_path without EVER overwriting an existing file (AG01-AUD-09)."""
    staged = Path(staged_path)
    final = Path(final_path)
    if final.exists():
        staged.unlink(missing_ok=True)
        raise EvidenceOverwriteError(f"Refusing to overwrite existing evidence file: {final}")
    try:
        os.link(staged, final)
    except FileExistsError as exc:
        staged.unlink(missing_ok=True)
        raise EvidenceOverwriteError(f"Refusing to overwrite existing evidence file: {final}") from exc
    except OSError:
        if final.exists():
            staged.unlink(missing_ok=True)
            raise EvidenceOverwriteError(f"Refusing to overwrite existing evidence file: {final}")
        shutil.move(str(staged), str(final))
    else:
        staged.unlink(missing_ok=True)


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
                "step": "0_precheck_local_apk_manifest_hash_and_existing_evidence",
                "commands": [
                    f"apkanalyzer manifest print \"{apk_str}\"",
                ],
                "pass_criteria": (
                    f"Existing evidence files absent in {out_dir} (no overwrite); APK exists, SHA-256 matches "
                    f"{expected_apk_sha256 or '<computed>'}, 0 .dex/0 .so, manifest package='{package_id}', "
                    f"WFF version='{wff_version}', minSdkVersion='{min_sdk}'"
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
                "step": "4_capture_active_state_with_before_after_checks",
                "commands": [
                    f"adb -s {safe_serial} shell input keyevent KEYCODE_WAKEUP",
                    f"adb -s {safe_serial} shell dumpsys wallpaper",
                    f"adb -s {safe_serial} shell dumpsys power",
                    f"adb -s {safe_serial} shell dumpsys display",
                    f"adb -s {safe_serial} exec-out screencap -p > {out_dir}/active_wff{wff_version}.png",
                    f"adb -s {safe_serial} shell dumpsys wallpaper",
                    f"adb -s {safe_serial} shell dumpsys power",
                    f"adb -s {safe_serial} shell dumpsys display",
                ],
                "pass_criteria": (
                    "Before & after capture: target Display Id=0 Awake+ON AND active watchface SELECTED; "
                    "bounded non-interlaced PNG CRC/IHDR/IDAT/zlib-EOF/IEND validated; no existing file overwritten"
                ),
            },
            {
                "step": "5_record_aod_transition_capture_ambient_restore_and_probe_mp4",
                "commands": [
                    f"adb -s {safe_serial} shell screenrecord --time-limit 8 {remote_video}  # background",
                    f"adb -s {safe_serial} shell input keyevent KEYCODE_SLEEP",
                    f"adb -s {safe_serial} shell dumpsys wallpaper",
                    f"adb -s {safe_serial} shell dumpsys power",
                    f"adb -s {safe_serial} shell dumpsys display",
                    f"adb -s {safe_serial} exec-out screencap -p > {out_dir}/ambient_wff{wff_version}.png",
                    f"adb -s {safe_serial} shell dumpsys wallpaper",
                    f"adb -s {safe_serial} shell dumpsys power",
                    f"adb -s {safe_serial} shell dumpsys display",
                    f"adb -s {safe_serial} shell input keyevent KEYCODE_WAKEUP",
                    f"adb -s {safe_serial} shell dumpsys wallpaper",
                    f"adb -s {safe_serial} shell dumpsys power",
                    f"adb -s {safe_serial} shell dumpsys display",
                    f"adb -s {safe_serial} pull {remote_video} {out_dir}/transition_wff{wff_version}.mp4",
                    f"ffprobe -v error -select_streams v:0 -count_frames -show_entries stream=codec_name,width,height,nb_read_frames -of json {out_dir}/transition_wff{wff_version}.mp4",
                    f"adb -s {safe_serial} shell rm -f {remote_video}",
                    f"adb -s {safe_serial} shell test ! -e {remote_video}",
                ],
                "pass_criteria": (
                    "All commands rc=0; active watchface & per-display state verified before/after AOD capture and at final Awake+ON restore; "
                    "MP4 ISO BMFF boxes/video-track/samples + ffprobe decoded frames >= 1 verified (NOT RUN if ffprobe absent); "
                    "full-scope finally recovery from first device mutation verified"
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


def _assert_watchface_selected(run_fn, safe_serial, package_id, stage_label):
    wallpaper = run_checked_adb(run_fn, ["shell", "dumpsys", "wallpaper"], timeout=30)
    selection = verify_active_watchface_selected(wallpaper.stdout, package_id)
    if selection["status"] == "UNKNOWN":
        raise RuntimeVerificationIncompleteError(
            f"[{stage_label}] Active watch face selection status is UNKNOWN on {safe_serial}: {selection.get('reason')}"
        )
    if not selection["selected"]:
        raise RuntimeError(
            f"[{stage_label}] Watch face '{package_id}' is NOT active on {safe_serial} "
            f"(status={selection['status']}, active_component='{selection.get('active_component')}')"
        )
    return selection


def _assert_screen_state(run_fn, safe_serial, expected_mode, stage_label, target_display_id="0"):
    state = parse_power_and_display_state(
        run_checked_adb(run_fn, ["shell", "dumpsys", "power"], timeout=30).stdout,
        run_checked_adb(run_fn, ["shell", "dumpsys", "display"], timeout=30).stdout,
        target_display_id=target_display_id,
    )
    if state["status"] == "UNKNOWN":
        raise RuntimeVerificationIncompleteError(
            f"[{stage_label}] Power/display state is UNKNOWN on {safe_serial}: {state}"
        )
    if expected_mode == "ACTIVE" and not state["is_active"]:
        raise RuntimeError(
            f"[{stage_label}] Expected Active (Awake+ON) on {safe_serial}, got {state['status']}: {state}"
        )
    if expected_mode == "AOD" and not state["is_aod"]:
        raise RuntimeError(
            f"[{stage_label}] Expected AOD (Dozing|Asleep + DOZE|DOZE_SUSPEND) on {safe_serial}, got {state['status']}: {state}"
        )
    return state


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
    target_display_id="0",
    runner=None,
    manifest_printer=None,
    recorder_factory=None,
    ffprobe_bin=None,
    probe_runner=None,
    sleep_fn=time.sleep,
):
    """Execute safe runtime verification against an ALREADY-RUNNING isolated Wear OS emulator (R06 hardened)."""
    safe_serial = validate_emulator_serial(serial)
    min_sdk = WFF_MIN_SDK[wff_version]
    target_api = expected_api_level if expected_api_level is not None else min_sdk
    target_avd = validate_dedicated_wear_avd_name(expected_avd_name or f"aura_wear{min_sdk}_round")

    # Step 0A: Refuse to overwrite any pre-existing evidence artifacts BEFORE touching device (AG01-AUD-09)
    out = Path(output_dir)
    active_png = out / f"active_wff{wff_version}.png"
    ambient_png = out / f"ambient_wff{wff_version}.png"
    local_video = out / f"transition_wff{wff_version}.mp4"
    staged_video = out / f"transition_wff{wff_version}.mp4.{os.getpid()}.tmp"
    for existing in (active_png, ambient_png, local_video):
        if existing.exists():
            raise EvidenceOverwriteError(
                f"Refusing to overwrite pre-existing evidence file '{existing}'; use a fresh output directory."
            )

    # Step 0B: Pre-check local APK hash, resource-only entries, and compiled AndroidManifest BEFORE touching emulator
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

    # Step 1: Read-only verification of running emulator AVD name, boot status, watch characteristics, and SDK level
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

    # Step 3: Initial active watch face verification
    selection_initial = _assert_watchface_selected(run_fn, safe_serial, package_id, "initial_selection")

    # Step 4 & Step 5: Wrap from the VERY FIRST device-state-mutating command in single try...finally (AG01-AUD-09)
    remote_video = f"/sdcard/ag01_wff{wff_version}_aod_transition.mp4"
    spawn_recorder = recorder_factory or (
        lambda: subprocess.Popen(
            [str(adb_bin), "-s", safe_serial, "shell", "screenrecord", "--time-limit", "8", remote_video],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    )

    out.mkdir(parents=True, exist_ok=True)
    recorder = None
    device_state_mutated = False
    recording_attempted = False

    checkpoints = {"initial_selection": selection_initial}
    power_active_before = None
    power_active_after = None
    power_aod_before = None
    power_aod_after = None
    power_restored = None
    selection_restored = None
    active_png_meta = None
    ambient_png_meta = None
    video_verification = None
    primary_error = None
    recovery_errors = []
    recovery_report = {
        "recovery_scope_entered": False,
        "recorder_spawned": False,
        "recorder_stopped": False,
        "staged_file_cleaned": False,
        "awake_restored": False,
        "watchface_restored": False,
        "remote_file_removed": False,
    }

    try:
        # Step 4: Wake display (first state mutation!), verify watchface + Active BEFORE and AFTER screencap (AG01-AUD-08)
        device_state_mutated = True
        recovery_report["recovery_scope_entered"] = True
        run_checked_adb(run_fn, ["shell", "input", "keyevent", "KEYCODE_WAKEUP"], timeout=15)
        checkpoints["active_before_selection"] = _assert_watchface_selected(run_fn, safe_serial, package_id, "active_before")
        power_active_before = _assert_screen_state(run_fn, safe_serial, "ACTIVE", "active_before", target_display_id)
        checkpoints["active_before_state"] = power_active_before

        cap_active = run_checked_adb(run_fn, ["exec-out", "screencap", "-p"], timeout=30, binary=True)
        active_png_meta = validate_png_bytes(cap_active.stdout)

        checkpoints["active_after_selection"] = _assert_watchface_selected(run_fn, safe_serial, package_id, "active_after")
        power_active_after = _assert_screen_state(run_fn, safe_serial, "ACTIVE", "active_after", target_display_id)
        checkpoints["active_after_state"] = power_active_after

        _write_new_evidence_file(active_png, cap_active.stdout)

        # Step 5: Start recorder (inside try/finally so spawn failure triggers recovery!), sleep -> AOD -> capture -> wake -> probe MP4
        recording_attempted = True
        recorder = spawn_recorder()
        recovery_report["recorder_spawned"] = True

        sleep_fn(1.0)
        run_checked_adb(run_fn, ["shell", "input", "keyevent", "KEYCODE_SLEEP"], timeout=15)
        sleep_fn(2.0)

        checkpoints["aod_before_selection"] = _assert_watchface_selected(run_fn, safe_serial, package_id, "aod_before")
        power_aod_before = _assert_screen_state(run_fn, safe_serial, "AOD", "aod_before", target_display_id)
        checkpoints["aod_before_state"] = power_aod_before

        cap_ambient = run_checked_adb(run_fn, ["exec-out", "screencap", "-p"], timeout=30, binary=True)
        ambient_png_meta = validate_png_bytes(cap_ambient.stdout)

        checkpoints["aod_after_selection"] = _assert_watchface_selected(run_fn, safe_serial, package_id, "aod_after")
        power_aod_after = _assert_screen_state(run_fn, safe_serial, "AOD", "aod_after", target_display_id)
        checkpoints["aod_after_state"] = power_aod_after

        _write_new_evidence_file(ambient_png, cap_ambient.stdout)

        sleep_fn(1.5)
        run_checked_adb(run_fn, ["shell", "input", "keyevent", "KEYCODE_WAKEUP"], timeout=15)
        sleep_fn(1.0)

        selection_restored = _assert_watchface_selected(run_fn, safe_serial, package_id, "final_restore")
        power_restored = _assert_screen_state(run_fn, safe_serial, "ACTIVE", "final_restore", target_display_id)
        checkpoints["final_restore_selection"] = selection_restored
        checkpoints["final_restore_state"] = power_restored

        try:
            rec_rc = recorder.wait(timeout=15)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"screenrecord did not exit within 15s timeout on {safe_serial}") from exc
        if rec_rc != 0:
            raise RuntimeError(f"screenrecord exited with non-zero returncode={rec_rc} on {safe_serial}")

        staged_video.unlink(missing_ok=True)
        run_checked_adb(run_fn, ["pull", remote_video, str(staged_video)], timeout=60)
        if not staged_video.is_file():
            raise RuntimeError(f"Pulled transition video file is missing at {staged_video}")

        try:
            video_verification = verify_mp4_video_artifact(
                staged_video,
                ffprobe_bin=ffprobe_bin,
                probe_runner=probe_runner,
            )
        except Exception:
            staged_video.unlink(missing_ok=True)
            raise

        _promote_staged_evidence_file(staged_video, local_video)

        if video_verification["status"] == "NOT_RUN":
            raise RuntimeVerificationIncompleteError(
                f"Video frame verification is NOT RUN ({video_verification['reason']}); "
                "refusing to mark runtime video verification as PASS."
            )
    except Exception as exc:
        primary_error = exc
    finally:
        # Step R1 (Independent): Verify recorder process is fully terminated and reaped (never blocked by staged unlink)
        if recorder is None:
            recovery_report["recorder_stopped"] = True
        else:
            try:
                if recorder.poll() is None:
                    try:
                        recorder.terminate()
                    except Exception as term_exc:
                        recovery_errors.append(f"recorder_terminate_call_failed: {term_exc}")
                    try:
                        recorder.wait(timeout=5)
                    except Exception:
                        try:
                            recorder.kill()
                        except Exception as kill_exc:
                            recovery_errors.append(f"recorder_kill_call_failed: {kill_exc}")
                        try:
                            recorder.wait(timeout=5)
                        except Exception as wait_exc:
                            recovery_errors.append(f"recorder_wait_after_kill_failed: {wait_exc}")
                else:
                    try:
                        recorder.wait(timeout=5)
                    except Exception as reap_exc:
                        recovery_errors.append(f"recorder_reap_wait_failed: {reap_exc}")
                if recorder.poll() is None:
                    recovery_errors.append("recorder_termination_failed: recorder process is still running after kill+wait")
                else:
                    recovery_report["recorder_stopped"] = True
            except Exception as rec_exc:
                recovery_errors.append(f"recorder_termination_failed: {rec_exc}")

        # Step R2 (Independent): Clean up local staged temporary video file without blocking any other recovery step
        try:
            staged_video.unlink(missing_ok=True)
            if staged_video.exists():
                recovery_errors.append(f"staged_cleanup_failed: staged file still exists at {staged_video}")
            else:
                recovery_report["staged_file_cleaned"] = True
        except Exception as stg_exc:
            recovery_errors.append(f"staged_cleanup_failed: {stg_exc}")

        # Step R3 & R4 (Independent): Verify final Awake+ON AND active watchface restoration whenever device state was mutated
        if device_state_mutated:
            already_restored_awake = power_restored is not None and bool(power_restored.get("is_active"))
            already_restored_wf = selection_restored is not None and bool(selection_restored.get("selected"))

            if already_restored_awake:
                recovery_report["awake_restored"] = True
            else:
                try:
                    run_checked_adb(run_fn, ["shell", "input", "keyevent", "KEYCODE_WAKEUP"], timeout=15)
                except Exception as wake_cmd_exc:
                    recovery_errors.append(f"awake_recovery_wakeup_failed: {wake_cmd_exc}")
                try:
                    sleep_fn(0.5)
                    recovered_state = parse_power_and_display_state(
                        run_checked_adb(run_fn, ["shell", "dumpsys", "power"], timeout=30).stdout,
                        run_checked_adb(run_fn, ["shell", "dumpsys", "display"], timeout=30).stdout,
                        target_display_id=target_display_id,
                    )
                    recovery_report["recovered_state"] = recovered_state
                    if recovered_state["is_active"]:
                        recovery_report["awake_restored"] = True
                    else:
                        recovery_errors.append(
                            f"awake_recovery_failed: emulator did not confirm Awake+ON after recovery wakeup ({recovered_state})"
                        )
                except Exception as wake_state_exc:
                    recovery_errors.append(f"awake_recovery_failed: {wake_state_exc}")

            if already_restored_wf:
                recovery_report["watchface_restored"] = True
            else:
                try:
                    recovered_wp = run_checked_adb(run_fn, ["shell", "dumpsys", "wallpaper"], timeout=30)
                    recovered_sel = verify_active_watchface_selected(recovered_wp.stdout, package_id)
                    recovery_report["recovered_selection"] = recovered_sel
                    if recovered_sel.get("selected"):
                        recovery_report["watchface_restored"] = True
                    else:
                        recovery_errors.append(
                            f"watchface_recovery_failed: active watchface not confirmed after recovery ({recovered_sel})"
                        )
                except Exception as wp_exc:
                    recovery_errors.append(f"watchface_recovery_failed: {wp_exc}")

        # Step R5 (Independent): Verify remote temporary MP4 deletion (`rm -f` and `test ! -e` checked independently)
        if recording_attempted:
            rm_ok = False
            absence_ok = False
            try:
                run_checked_adb(run_fn, ["shell", "rm", "-f", remote_video], timeout=15)
                rm_ok = True
            except Exception as rm_exc:
                recovery_errors.append(f"remote_cleanup_failed: {rm_exc}")
            try:
                run_checked_adb(run_fn, ["shell", "test", "!", "-e", remote_video], timeout=15)
                absence_ok = True
            except Exception as test_exc:
                recovery_errors.append(f"remote_cleanup_failed (remote_absence_check_failed): {test_exc}")
            if rm_ok and absence_ok:
                recovery_report["remote_file_removed"] = True
        else:
            recovery_report["remote_file_removed"] = True

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
        "target_display_id": str(target_display_id),
        "apk_verification": apk_meta,
        "selection": selection_initial,
        "checkpoints": checkpoints,
        "active_state": power_active_after,
        "aod_state": power_aod_after,
        "restored_active_state": power_restored,
        "restored_selection": selection_restored,
        "recovery_report": recovery_report,
        "active_png": str(active_png),
        "active_png_meta": active_png_meta,
        "active_png_sha256": active_png_meta["sha256"],
        "ambient_png": str(ambient_png),
        "ambient_png_meta": ambient_png_meta,
        "ambient_png_sha256": ambient_png_meta["sha256"],
        "transition_mp4": str(local_video),
        "transition_mp4_size_bytes": video_verification["container"]["size_bytes"],
        "transition_mp4_sha256": video_verification["container"]["sha256"],
        "video_verification": video_verification,
        "video_verification_status": video_verification["video_verification_status"],
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
    parser.add_argument("--ffprobe", type=Path, default=None)
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
        ffprobe_bin=args.ffprobe,
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
