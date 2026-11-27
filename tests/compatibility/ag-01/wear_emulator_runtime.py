"""Safe Wear OS emulator runtime verification helper for AG-01 (no auto-downloads, strict Wear-only isolation).

Safety invariants enforced by this module:
1. Never downloads SDK packages or creates AVDs automatically.
2. Never uses `--force` in recommended `avdmanager create avd` commands so existing AVDs are never overwritten.
3. Refuses to target physical devices (non-`emulator-*` serials) or non-Wear AVDs (e.g. phone/tablet AVDs).
4. Requires explicit `-s <emulator-serial>` on every `adb` command.
5. Verifies `ro.build.characteristics` contains `watch` and `ro.build.version.sdk >= required_min_sdk`.
6. Verifies watch face package installation, active watch face selection (`dumpsys wallpaper` / watch face service),
   Active (`Awake`) vs AOD (`Dozing` / `DOZE`) power/display state transitions, screenshots, and transition video capture.
"""
import argparse
import re
import subprocess
import time
from pathlib import Path

WFF_MIN_SDK = {
    2: 34,
    3: 35,
    4: 36,
    5: 37,
}

# Candidate Wear OS system image definitions (verified against sdkmanager --list before use; never auto-installed)
RECOMMENDED_WEAR_AVD_PLANS = [
    {
        "stage": 1,
        "wff_version": 4,
        "min_sdk": 36,
        "avd_name": "aura_wear36_round",
        "package_id": "system-images;android-36;android-wear-signed;x86_64",
        "device_profile": "wearos_large_round",
        "priority": "P0 (Primary WFF 4: Variant continuity, Reference, Gyro)",
    },
    {
        "stage": 2,
        "wff_version": 5,
        "min_sdk": 37,
        "avd_name": "aura_wear37_round",
        "package_id": "system-images;android-37.0;android-wear-signed;x86_64",
        "device_profile": "wearos_large_round",
        "priority": "P0 (Primary WFF 5: Group/ComplicationSlot blendMode)",
    },
    {
        "stage": 3,
        "wff_version": 3,
        "min_sdk": 35,
        "avd_name": "aura_wear35_round",
        "package_id": "system-images;android-35-ext15;android-wear;x86_64",
        "device_profile": "wearos_large_round",
        "priority": "P1 (Optional expansion: WFF 3 Part blendMode static AOD)",
    },
    {
        "stage": 4,
        "wff_version": 2,
        "min_sdk": 34,
        "avd_name": "aura_wear34_round",
        "package_id": "system-images;android-34;android-wear;x86_64",
        "device_profile": "wearos_large_round",
        "priority": "P1 (Optional expansion: WFF 2 baseline static AOD)",
    },
]


class UnsafeTargetError(RuntimeError):
    """Raised when a command attempts to touch a physical watch/phone or a non-Wear AVD."""


def validate_emulator_serial(serial):
    """Allow only Android emulator serials (emulator-<port>); hard-reject physical devices or blank serials."""
    if not serial or not re.fullmatch(r"emulator-\d+", serial.strip()):
        raise UnsafeTargetError(
            f"Refusing target serial '{serial}': only isolated Android emulators ('emulator-<port>') are allowed; "
            "physical watches/phones and implicit adb targeting without -s are prohibited."
        )
    return serial.strip()


def validate_wear_avd_record(avd_record):
    """Ensure the selected AVD metadata explicitly proves it is a Wear OS AVD and not a phone/tablet AVD."""
    name = (avd_record or {}).get("name", "")
    tag_abi = ((avd_record or {}).get("tag_abi") or "").lower()
    device = ((avd_record or {}).get("device") or "").lower()
    if "android-wear" not in tag_abi and "wearos" not in device:
        raise UnsafeTargetError(
            f"Refusing AVD '{name}': metadata (device='{avd_record.get('device')}', tag_abi='{avd_record.get('tag_abi')}') "
            "does not identify a Wear OS AVD. Existing phone/tablet AVDs must not be modified or targeted."
        )
    return name


def validate_wear_device_properties(characteristics, sdk_int_raw, required_min_sdk):
    """Verify running emulator reports `watch` hardware characteristics and meets WFF minSdk."""
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
    return sdk_int


def parse_power_and_display_state(dumpsys_power, dumpsys_display=""):
    """Parse Awake vs Doze/AOD state from `dumpsys power` and `dumpsys display` outputs."""
    wake_match = re.search(r"mWakefulness=([A-Za-z_]+)", dumpsys_power or "")
    wakefulness = wake_match.group(1) if wake_match else "UNKNOWN"

    display_match = re.search(r"Display Power:\s*state=([A-Z_]+)", dumpsys_power or "")
    if not display_match:
        display_match = re.search(r"mScreenState=([A-Z_]+)", dumpsys_display or "")
    if not display_match:
        display_match = re.search(r"state=([A-Z_]+)", dumpsys_display or "")
    display_state = display_match.group(1) if display_match else "UNKNOWN"

    is_active = wakefulness == "Awake" and display_state in ("ON", "UNKNOWN")
    is_aod = wakefulness == "Dozing" or display_state in ("DOZE", "DOZE_SUSPEND")
    return {
        "wakefulness": wakefulness,
        "display_state": display_state,
        "is_active": is_active,
        "is_aod": is_aod,
    }


def verify_active_watchface_selected(dumpsys_wallpaper, expected_package):
    """Verify from `dumpsys wallpaper` that the target WFF package is actually selected as the active watch face."""
    if not expected_package:
        raise ValueError("expected_package must be non-empty")
    text = dumpsys_wallpaper or ""
    # In Wear OS WFF, the declarative watch face host service binds the target resource-only package or records
    # the active watchface package/component in wallpaper/watchface dumpsys output.
    pkg_pattern = re.compile(rf"\b{re.escape(expected_package)}\b")
    matches = [line.strip() for line in text.splitlines() if pkg_pattern.search(line)]
    return {
        "selected": len(matches) > 0,
        "expected_package": expected_package,
        "matched_lines": matches[:10],
    }


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


def build_safe_runtime_verification_plan(serial, apk_path, package_id, wff_version, output_dir):
    """Generate an explicit `-s <serial>` step-by-step runtime verification command sequence."""
    safe_serial = validate_emulator_serial(serial)
    min_sdk = WFF_MIN_SDK[wff_version]
    out_dir = Path(output_dir).as_posix()
    apk_str = Path(apk_path).as_posix()
    remote_video = f"/sdcard/ag01_wff{wff_version}_aod_transition.mp4"
    return {
        "serial": safe_serial,
        "package_id": package_id,
        "wff_version": wff_version,
        "required_min_sdk": min_sdk,
        "steps": [
            {
                "step": "1_verify_wear_emulator_props",
                "commands": [
                    f"adb -s {safe_serial} wait-for-device",
                    f"adb -s {safe_serial} shell getprop sys.boot_completed",
                    f"adb -s {safe_serial} shell getprop ro.build.characteristics",
                    f"adb -s {safe_serial} shell getprop ro.build.version.sdk",
                ],
                "pass_criteria": f"boot_completed=1, characteristics contains 'watch', sdk >= {min_sdk}",
            },
            {
                "step": "2_install_isolated_apk",
                "commands": [
                    f"adb -s {safe_serial} install -r \"{apk_str}\"",
                    f"adb -s {safe_serial} shell pm list packages {package_id}",
                ],
                "pass_criteria": f"package:{package_id} present on {safe_serial}",
            },
            {
                "step": "3_select_and_confirm_watchface",
                "commands": [
                    f"adb -s {safe_serial} shell dumpsys package {package_id}",
                    f"adb -s {safe_serial} shell am start -a android.intent.action.MAIN -c android.intent.category.HOME",
                    f"# Select '{package_id}' in the Wear OS Watch Face Picker on {safe_serial} (do NOT assume install auto-activates a WFF face)",
                    f"adb -s {safe_serial} shell dumpsys wallpaper",
                ],
                "pass_criteria": f"dumpsys wallpaper output explicitly contains '{package_id}' as the active bound watch face before any screenshot or video capture",
            },
            {
                "step": "4_capture_active_state",
                "commands": [
                    f"adb -s {safe_serial} shell input keyevent KEYCODE_WAKEUP",
                    f"adb -s {safe_serial} shell dumpsys power",
                    f"adb -s {safe_serial} exec-out screencap -p > {out_dir}/active_wff{wff_version}.png",
                ],
                "pass_criteria": "mWakefulness=Awake and Display state=ON before active PNG capture",
            },
            {
                "step": "5_record_aod_transition_and_capture_ambient",
                "commands": [
                    f"adb -s {safe_serial} shell screenrecord --time-limit 8 {remote_video}  # background",
                    f"adb -s {safe_serial} shell input keyevent KEYCODE_SLEEP",
                    f"adb -s {safe_serial} shell dumpsys power",
                    f"adb -s {safe_serial} shell dumpsys display",
                    f"adb -s {safe_serial} exec-out screencap -p > {out_dir}/ambient_wff{wff_version}.png",
                    f"adb -s {safe_serial} shell input keyevent KEYCODE_WAKEUP",
                    f"adb -s {safe_serial} pull {remote_video} {out_dir}/transition_wff{wff_version}.mp4",
                    f"adb -s {safe_serial} shell rm -f {remote_video}",
                ],
                "pass_criteria": "mWakefulness=Dozing or Display state=DOZE/DOZE_SUSPEND confirmed before ambient PNG; MP4 video covers Active->AOD->Active transition",
            },
        ],
    }


def _run_adb(adb_bin, serial, adb_args, timeout=30):
    safe_serial = validate_emulator_serial(serial)
    return subprocess.run(
        [str(adb_bin), "-s", safe_serial, *adb_args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def execute_runtime_verification(adb_bin, serial, apk_path, package_id, wff_version, output_dir, runner=None):
    """Execute safe runtime verification against an ALREADY-RUNNING isolated Wear OS emulator."""
    safe_serial = validate_emulator_serial(serial)
    min_sdk = WFF_MIN_SDK[wff_version]
    run_fn = runner or (lambda args, timeout=30: _run_adb(adb_bin, safe_serial, args, timeout=timeout))

    boot = run_fn(["shell", "getprop", "sys.boot_completed"])
    if boot.returncode != 0 or boot.stdout.strip() != "1":
        raise RuntimeError(f"Emulator {safe_serial} is not booted (rc={boot.returncode}, out='{boot.stdout.strip()}')")

    chars = run_fn(["shell", "getprop", "ro.build.characteristics"])
    sdk_raw = run_fn(["shell", "getprop", "ro.build.version.sdk"])
    sdk_int = validate_wear_device_properties(chars.stdout.strip(), sdk_raw.stdout.strip(), min_sdk)

    install = run_fn(["install", "-r", str(apk_path)], timeout=120)
    if install.returncode != 0 or "Success" not in install.stdout:
        raise RuntimeError(f"APK install failed on {safe_serial}: {install.stdout} {install.stderr}")

    pm = run_fn(["shell", "pm", "list", "packages", package_id])
    if f"package:{package_id}" not in pm.stdout:
        raise RuntimeError(f"Installed package {package_id} not found on {safe_serial}: {pm.stdout}")

    wallpaper = run_fn(["shell", "dumpsys", "wallpaper"])
    selection = verify_active_watchface_selected(wallpaper.stdout, package_id)
    if not selection["selected"]:
        raise RuntimeError(
            f"Watch face {package_id} is installed on {safe_serial} but NOT selected as active watch face in dumpsys wallpaper. "
            "Select it via Wear OS Watch Face Picker before capturing screenshots/video."
        )

    run_fn(["shell", "input", "keyevent", "KEYCODE_WAKEUP"])
    power_active = parse_power_and_display_state(run_fn(["shell", "dumpsys", "power"]).stdout)
    if not power_active["is_active"]:
        raise RuntimeError(f"Emulator {safe_serial} did not enter Awake state: {power_active}")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    active_png = out / f"active_wff{wff_version}.png"
    cap_active = subprocess.run([str(adb_bin), "-s", safe_serial, "exec-out", "screencap", "-p"], capture_output=True, timeout=30, check=False)
    if cap_active.returncode != 0 or not cap_active.stdout.startswith(b"\x89PNG"):
        raise RuntimeError(f"Failed to capture active PNG on {safe_serial}")
    active_png.write_bytes(cap_active.stdout)

    remote_video = f"/sdcard/ag01_wff{wff_version}_aod_transition.mp4"
    recorder = subprocess.Popen([str(adb_bin), "-s", safe_serial, "shell", "screenrecord", "--time-limit", "8", remote_video])
    try:
        time.sleep(1.0)
        run_fn(["shell", "input", "keyevent", "KEYCODE_SLEEP"])
        time.sleep(2.0)
        power_aod = parse_power_and_display_state(
            run_fn(["shell", "dumpsys", "power"]).stdout,
            run_fn(["shell", "dumpsys", "display"]).stdout,
        )
        if not power_aod["is_aod"]:
            raise RuntimeError(f"Emulator {safe_serial} did not enter AOD/Doze state: {power_aod}")
        ambient_png = out / f"ambient_wff{wff_version}.png"
        cap_ambient = subprocess.run([str(adb_bin), "-s", safe_serial, "exec-out", "screencap", "-p"], capture_output=True, timeout=30, check=False)
        if cap_ambient.returncode != 0 or not cap_ambient.stdout.startswith(b"\x89PNG"):
            raise RuntimeError(f"Failed to capture ambient PNG on {safe_serial}")
        ambient_png.write_bytes(cap_ambient.stdout)
        time.sleep(1.5)
        run_fn(["shell", "input", "keyevent", "KEYCODE_WAKEUP"])
    finally:
        recorder.wait(timeout=15)

    local_video = out / f"transition_wff{wff_version}.mp4"
    pull = run_fn(["pull", remote_video, str(local_video)], timeout=60)
    run_fn(["shell", "rm", "-f", remote_video])
    if pull.returncode != 0 or not local_video.is_file():
        raise RuntimeError(f"Failed to pull AOD transition video from {safe_serial}: {pull.stdout} {pull.stderr}")

    return {
        "serial": safe_serial,
        "sdk_int": sdk_int,
        "package_id": package_id,
        "selection": selection,
        "active_state": power_active,
        "aod_state": power_aod,
        "active_png": str(active_png),
        "ambient_png": str(ambient_png),
        "transition_mp4": str(local_video),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-only", action="store_true", help="Print safe runtime verification plan without touching any device")
    parser.add_argument("--serial", required=True, help="Explicit Android emulator serial (must match emulator-<port>)")
    parser.add_argument("--apk", type=Path, required=True)
    parser.add_argument("--package-id", required=True)
    parser.add_argument("--wff-version", type=int, choices=(2, 3, 4, 5), required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--adb", type=Path, default=Path("adb"))
    args = parser.parse_args()

    plan = build_safe_runtime_verification_plan(args.serial, args.apk, args.package_id, args.wff_version, args.out_dir)
    if args.plan_only:
        import json
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return

    res = execute_runtime_verification(args.adb, args.serial, args.apk, args.package_id, args.wff_version, args.out_dir)
    import json
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
