"""AG-01 end-to-end verification runner for WFF 2-5 PoC XMLs, isolated APK builds, memory evaluation, and emulator readiness."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from check_apk import analyzer_path, inspect_entries, inspect_face, inspect_manifest
from profile_contract import load_profiles
from verify_memory import LIMITS, enforce_limits, get_jar as get_memory_jar, parse_report
from verify_wff import FAILURE, PASS, SHA256 as VALIDATOR_SHA256, require_pass

AG01_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = AG01_DIR / "fixtures"
VALIDATOR_JAR = ROOT / ".aura-tools" / "wff-validator.jar"

JAVA_UTF8_OPTS = "-Dfile.encoding=UTF-8 -Dsun.stdout.encoding=UTF-8 -Dsun.stderr.encoding=UTF-8"

POC_SPECS = [
    {
        "id": "poc_wff2_static_aod",
        "path": FIXTURES_DIR / "wff2" / "poc_wff2_static_aod.xml",
        "min_version": 2,
        "target_profile": "wff2",
        "description": "WFF 2 static AOD fallback on single DigitalClock/TimeText with weather missing-data fallback",
    },
    {
        "id": "poc_wff3_part_blend_aod",
        "path": FIXTURES_DIR / "wff3" / "poc_wff3_part_blend_aod.xml",
        "min_version": 3,
        "target_profile": "wff3",
        "description": "WFF 3 static AOD fallback with PartDraw/PartText blendMode (SCREEN, SRC_OVER)",
    },
    {
        "id": "poc_wff4_continuity",
        "path": FIXTURES_DIR / "wff4" / "poc_wff4_continuity.xml",
        "min_version": 4,
        "target_profile": "wff4",
        "description": "WFF 4 staged AOD transition continuity (duration, startOffset, all 6 interpolations, single clock object)",
    },
    {
        "id": "poc_wff4_reference_complication",
        "path": FIXTURES_DIR / "wff4" / "poc_wff4_reference_complication.xml",
        "min_version": 4,
        "target_profile": "wff4",
        "description": "WFF 4 Reference single-source publication and synthetic Complication multi-element control",
    },
    {
        "id": "poc_wff4_motion_triggers",
        "path": FIXTURES_DIR / "wff4" / "poc_wff4_motion_triggers.xml",
        "min_version": 4,
        "target_profile": "wff4",
        "description": "WFF 4 Gyro parallax/reflection, per-digit TimeText container motion, and state Transform Animations",
    },
    {
        "id": "poc_wff5_blend_features",
        "path": FIXTURES_DIR / "wff5" / "poc_wff5_blend_features.xml",
        "min_version": 5,
        "target_profile": "wff5",
        "description": "WFF 5 Group and ComplicationSlot blendMode with Stroke join, Font minSize, Text lineSpacing/verticalAlign",
    },
]

NEGATIVE_SPECS = [
    {
        "id": "neg_wff3_part_blend_in_wff2",
        "path": FIXTURES_DIR / "negative" / "neg_wff3_part_blend_in_wff2.xml",
        "fail_versions": [2],
        "pass_versions": [3, 4, 5],
        "expected_error": "blendMode",
        "description": "Detect WFF 3 PartDraw blendMode leaked into WFF 2",
    },
    {
        "id": "neg_wff4_variant_transition_in_wff3",
        "path": FIXTURES_DIR / "negative" / "neg_wff4_variant_transition_in_wff3.xml",
        "fail_versions": [2, 3],
        "pass_versions": [4, 5],
        "expected_error": "Variant",
        "description": "Detect WFF 4 Variant transition attributes (duration/startOffset/interpolation) leaked into WFF 2/3",
    },
    {
        "id": "neg_wff4_reference_in_wff3",
        "path": FIXTURES_DIR / "negative" / "neg_wff4_reference_in_wff3.xml",
        "fail_versions": [2, 3],
        "pass_versions": [4, 5],
        "expected_error": "Reference",
        "description": "Detect WFF 4 Reference element leaked into WFF 2/3",
    },
    {
        "id": "neg_wff5_group_blend_in_wff4",
        "path": FIXTURES_DIR / "negative" / "neg_wff5_group_blend_in_wff4.xml",
        "fail_versions": [2, 3, 4],
        "pass_versions": [5],
        "expected_error": "blendMode",
        "description": "Detect WFF 5 Group blendMode leaked into WFF 2/3/4",
    },
    {
        "id": "neg_wff5_complicationslot_blend_in_wff4",
        "path": FIXTURES_DIR / "negative" / "neg_wff5_complicationslot_blend_in_wff4.xml",
        "fail_versions": [2, 3, 4],
        "pass_versions": [5],
        "expected_error": "blendMode",
        "description": "Detect WFF 5 ComplicationSlot blendMode leaked into WFF 2/3/4",
    },
    {
        "id": "neg_wff5_stroke_join_font_minsize_in_wff4",
        "path": FIXTURES_DIR / "negative" / "neg_wff5_stroke_join_font_minsize_in_wff4.xml",
        "fail_versions": [2, 3, 4],
        "pass_versions": [5],
        "expected_error": "join",
        "description": "Detect WFF 5 Stroke join and Font minSize leaked into WFF 2/3/4",
    },
    {
        "id": "neg_wff4_invalid_variant_and_reference_parent",
        "path": FIXTURES_DIR / "negative" / "neg_wff4_invalid_variant_and_reference_parent.xml",
        "fail_versions": [2, 3, 4, 5],
        "pass_versions": [],
        "expected_error": "1.35",
        "description": "Detect out-of-range Variant duration (>1.0) and illegal Reference under DigitalClock in all versions",
    },
]


def utf8_env():
    env = dict(os.environ)
    existing = env.get("JAVA_TOOL_OPTIONS", "").strip()
    if "-Dfile.encoding=UTF-8" not in existing:
        env["JAVA_TOOL_OPTIONS"] = f"{existing} {JAVA_UTF8_OPTS}".strip()
    return env


def ensure_validator_jar():
    if not VALIDATOR_JAR.is_file():
        raise RuntimeError(f"Missing official WFF validator JAR at {VALIDATOR_JAR}; run tools/verify_wff.py first.")
    digest = hashlib.sha256(VALIDATOR_JAR.read_bytes()).hexdigest()
    if digest != VALIDATOR_SHA256:
        raise RuntimeError(f"Validator SHA-256 mismatch: expected {VALIDATOR_SHA256}, got {digest}")
    return VALIDATOR_JAR


def run_validator_utf8(jar, face_path, version):
    return subprocess.run(
        ["java", "-Dfile.encoding=UTF-8", "-Dsun.stdout.encoding=UTF-8", "-Dsun.stderr.encoding=UTF-8", "-jar", str(jar), str(version), str(face_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        env=utf8_env(),
        timeout=120,
        check=False,
    )


def require_rejection(returncode, output, expected_error=None):
    if any(PASS.fullmatch(line) for line in output.splitlines()):
        raise ValueError("Fixture unexpectedly produced a PASSED verdict")
    if returncode == 0 and not FAILURE.search(output):
        raise ValueError("Inconclusive validator rejection: returncode 0 without FAILURE/SEVERE")
    if expected_error and expected_error not in output:
        raise ValueError(f"Expected error substring '{expected_error}' not found in validator output: {output.strip()}")


def verify_schemas():
    jar = ensure_validator_jar()
    results = {"positive_matrix": [], "negative_matrix": []}

    for spec in POC_SPECS:
        xml_path = spec["path"]
        if not xml_path.is_file():
            raise FileNotFoundError(f"Missing PoC XML: {xml_path}")
        xml_sha256 = hashlib.sha256(xml_path.read_bytes()).hexdigest()
        for version in (2, 3, 4, 5):
            proc = run_validator_utf8(jar, xml_path, version)
            should_pass = version >= spec["min_version"]
            if should_pass:
                require_pass(proc.returncode, proc.stdout, xml_path, version)
                verdict = "PASS_EXPECTED_VALID"
            else:
                require_rejection(proc.returncode, proc.stdout)
                verdict = "PASS_EXPECTED_REJECTED_ON_LOWER_VERSION"
            results["positive_matrix"].append({
                "id": spec["id"],
                "xml_sha256": xml_sha256,
                "version": version,
                "should_pass": should_pass,
                "verdict": verdict,
                "returncode": proc.returncode,
                "output_tail": [line for line in proc.stdout.splitlines() if "INFO:" in line or "SEVERE:" in line],
            })
            print(f"[SCHEMA] {spec['id']} @ WFF#{version}: {verdict}")

    for spec in NEGATIVE_SPECS:
        xml_path = spec["path"]
        if not xml_path.is_file():
            raise FileNotFoundError(f"Missing negative fixture: {xml_path}")
        xml_sha256 = hashlib.sha256(xml_path.read_bytes()).hexdigest()
        for version in (2, 3, 4, 5):
            proc = run_validator_utf8(jar, xml_path, version)
            if version in spec["fail_versions"]:
                expected_err = spec["expected_error"] if version == max(spec["fail_versions"]) else None
                require_rejection(proc.returncode, proc.stdout, expected_err)
                verdict = "PASS_DETECTED_INVALID"
            elif version in spec["pass_versions"]:
                require_pass(proc.returncode, proc.stdout, xml_path, version)
                verdict = "PASS_VALID_ON_HIGHER_VERSION"
            else:
                raise ValueError(f"Version {version} unclassified for {spec['id']}")
            results["negative_matrix"].append({
                "id": spec["id"],
                "xml_sha256": xml_sha256,
                "version": version,
                "verdict": verdict,
                "returncode": proc.returncode,
                "output_tail": [line for line in proc.stdout.splitlines() if "INFO:" in line or "SEVERE:" in line],
            })
            print(f"[NEGATIVE] {spec['id']} @ WFF#{version}: {verdict}")

    return results


def copy_isolated_project(temp_root):
    """Copy minimal watchface Gradle project to an isolated temporary directory without modifying the main repository."""
    for rel in ("settings.gradle.kts", "build.gradle.kts", "gradle.properties", "gradlew", "gradlew.bat"):
        src = ROOT / rel
        if src.is_file():
            shutil.copy2(src, temp_root / rel)
    shutil.copytree(ROOT / "gradle", temp_root / "gradle")
    shutil.copytree(ROOT / "compatibility", temp_root / "compatibility")
    shutil.copytree(ROOT / "apps" / "watchface" / "src", temp_root / "apps" / "watchface" / "src")
    shutil.copy2(ROOT / "apps" / "watchface" / "build.gradle.kts", temp_root / "apps" / "watchface" / "build.gradle.kts")


def resolve_apksigner():
    sdk = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not sdk:
        raise RuntimeError("ANDROID_HOME or ANDROID_SDK_ROOT is not configured")
    signer = Path(sdk) / "build-tools" / "36.0.0" / ("apksigner.bat" if os.name == "nt" else "apksigner")
    if not signer.is_file():
        raise RuntimeError(f"apksigner not found at {signer}")
    return signer


def evaluate_memory_utf8(memory_jar, apk_path, version):
    args = [
        "java",
        "-Dfile.encoding=UTF-8",
        "-Dsun.stdout.encoding=UTF-8",
        "-Dsun.stderr.encoding=UTF-8",
        "-jar",
        str(memory_jar),
        "--watch-face",
        str(apk_path),
        "--schema-version",
        str(version),
        "--apply-v1-offload-limitations",
        "--report",
    ]
    proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", env=utf8_env(), timeout=180, check=False)
    report = parse_report(proc.returncode, proc.stdout)
    enforce_limits(report)
    return report


def inspect_single_apk(apk_path, profile, expected_xml_bytes, analyzer, signer, memory_jar):
    apk_bytes = apk_path.read_bytes()
    apk_sha256 = hashlib.sha256(apk_bytes).hexdigest()
    expected_xml_sha256 = hashlib.sha256(expected_xml_bytes).hexdigest()

    with zipfile.ZipFile(apk_path) as archive:
        entries = sorted(archive.namelist())
        errors = inspect_entries(entries)
        errors.extend(inspect_face(archive, expected_xml_bytes))
        corrupt = archive.testzip()
        if corrupt:
            errors.append("Corrupt ZIP entry: " + corrupt)
        packaged_xml_sha256 = hashlib.sha256(archive.read("res/raw/watchface.xml")).hexdigest()

    if errors:
        raise RuntimeError(f"APK entry/face verification failed for {profile['name']}: {errors}")

    manifest_proc = subprocess.run(
        [analyzer, "manifest", "print", str(apk_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=utf8_env(),
        timeout=60,
        check=False,
    )
    if manifest_proc.returncode != 0:
        raise RuntimeError(f"apkanalyzer failed for {profile['name']}: {manifest_proc.stderr.strip()}")
    manifest_errors = inspect_manifest(manifest_proc.stdout, profile)
    if manifest_errors:
        raise RuntimeError(f"Compiled manifest errors for {profile['name']}: {manifest_errors}")

    memory_report = evaluate_memory_utf8(memory_jar, apk_path, profile["version"])

    sig_proc = subprocess.run(
        [str(signer), "verify", "--verbose", "--print-certs", str(apk_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=utf8_env(),
        timeout=60,
        check=False,
    )
    if sig_proc.returncode != 0:
        raise RuntimeError(f"apksigner failed for {profile['name']}: {sig_proc.stderr.strip()}")
    if "Verifies" not in sig_proc.stdout or "Verified using v2 scheme (APK Signature Scheme v2): true" not in sig_proc.stdout:
        raise RuntimeError(f"Unexpected signature verification output for {profile['name']}: {sig_proc.stdout}")

    cert_match = re.search(r"Signer #1 certificate SHA-256 digest:\s*([0-9a-fA-F]+)", sig_proc.stdout)
    cert_sha256 = cert_match.group(1) if cert_match else "unknown"

    return {
        "profile": profile["name"],
        "wff_version": profile["version"],
        "min_sdk": profile["minSdk"],
        "apk_name": apk_path.name,
        "apk_size_bytes": len(apk_bytes),
        "apk_sha256": apk_sha256,
        "source_xml_sha256": expected_xml_sha256,
        "packaged_xml_sha256": packaged_xml_sha256,
        "xml_exact_match": expected_xml_sha256 == packaged_xml_sha256,
        "zip_entries": entries,
        "resource_only_pass": True,
        "manifest_pass": True,
        "memory_report": memory_report,
        "memory_limits": LIMITS,
        "signature_v2_pass": True,
        "cert_sha256": cert_sha256,
    }


def verify_isolated_apks():
    profiles_by_name = {p["name"]: p for p in load_profiles() if p["enabled"]}
    analyzer = analyzer_path()
    signer = resolve_apksigner()
    memory_jar = get_memory_jar()
    apk_results = []

    with tempfile.TemporaryDirectory(prefix="aura-ag01-isolated-") as temp_dir:
        temp_root = Path(temp_dir)
        copy_isolated_project(temp_root)
        app_dir = temp_root / "apps" / "watchface"
        wrapper = temp_root / ("gradlew.bat" if os.name == "nt" else "gradlew")

        # Round 1: Build primary 4-profile matrix (wff2, wff3, wff4 continuity, wff5 blend)
        round1_map = {
            "wff2": next(s for s in POC_SPECS if s["id"] == "poc_wff2_static_aod"),
            "wff3": next(s for s in POC_SPECS if s["id"] == "poc_wff3_part_blend_aod"),
            "wff4": next(s for s in POC_SPECS if s["id"] == "poc_wff4_continuity"),
            "wff5": next(s for s in POC_SPECS if s["id"] == "poc_wff5_blend_features"),
        }
        for pname, spec in round1_map.items():
            override_path = app_dir / "src" / pname / "res" / "raw" / "watchface.xml"
            override_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(spec["path"], override_path)

        tasks_r1 = ["clean", ":apps:watchface:assembleWff2Debug", ":apps:watchface:assembleWff3Debug", ":apps:watchface:assembleWff4Debug", ":apps:watchface:assembleWff5Debug"]
        print(f"[APK-BUILD] Round 1 isolated clean build in {temp_root}: {' '.join(tasks_r1)}", flush=True)
        subprocess.run([str(wrapper), "--no-daemon", "--stacktrace", *tasks_r1], cwd=temp_root, env=utf8_env(), check=True)

        for pname, spec in round1_map.items():
            profile = profiles_by_name[pname]
            apks = sorted((app_dir / "build" / "outputs" / "apk" / pname / "debug").glob("*.apk"))
            if len(apks) != 1:
                raise RuntimeError(f"Expected 1 APK for {pname}, found {len(apks)}")
            res = inspect_single_apk(apks[0], profile, spec["path"].read_bytes(), analyzer, signer, memory_jar)
            res["poc_id"] = spec["id"]
            apk_results.append(res)
            print(f"[APK-PASS] {spec['id']} ({pname}): SHA-256={res['apk_sha256']} memory={res['memory_report']}")

        # Round 2 & 3: Build remaining WFF 4 PoCs (poc_wff4_reference_complication and poc_wff4_motion_triggers)
        for extra_id in ("poc_wff4_reference_complication", "poc_wff4_motion_triggers"):
            spec = next(s for s in POC_SPECS if s["id"] == extra_id)
            override_path = app_dir / "src" / "wff4" / "res" / "raw" / "watchface.xml"
            shutil.copy2(spec["path"], override_path)
            tasks_extra = ["clean", ":apps:watchface:assembleWff4Debug"]
            print(f"[APK-BUILD] Isolated clean build for {extra_id}: {' '.join(tasks_extra)}", flush=True)
            subprocess.run([str(wrapper), "--no-daemon", "--stacktrace", *tasks_extra], cwd=temp_root, env=utf8_env(), check=True)
            profile = profiles_by_name["wff4"]
            apks = sorted((app_dir / "build" / "outputs" / "apk" / "wff4" / "debug").glob("*.apk"))
            if len(apks) != 1:
                raise RuntimeError(f"Expected 1 APK for wff4 ({extra_id}), found {len(apks)}")
            res = inspect_single_apk(apks[0], profile, spec["path"].read_bytes(), analyzer, signer, memory_jar)
            res["poc_id"] = spec["id"]
            apk_results.append(res)
            print(f"[APK-PASS] {spec['id']} (wff4): SHA-256={res['apk_sha256']} memory={res['memory_report']}")

    return apk_results


def inspect_emulator_environment():
    sdk = Path(os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT") or "")
    sys_images_dir = sdk / "system-images" if sdk.is_dir() else None
    installed_images = []
    wear_images = []
    if sys_images_dir and sys_images_dir.is_dir():
        for prop in sorted(sys_images_dir.rglob("source.properties")):
            rel = str(prop.parent.relative_to(sdk))
            installed_images.append(rel)
            if "wear" in rel.lower():
                wear_images.append(rel)

    emulator_bin = sdk / "emulator" / ("emulator.exe" if os.name == "nt" else "emulator")
    avds = []
    if emulator_bin.is_file():
        proc = subprocess.run([str(emulator_bin), "-list-avds"], capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            avds = [line.strip() for line in proc.stdout.splitlines() if line.strip()]

    adb_bin = sdk / "platform-tools" / ("adb.exe" if os.name == "nt" else "adb")
    connected_devices = []
    adb_note = ""
    if adb_bin.is_file():
        proc = subprocess.run([str(adb_bin), "devices", "-l"], capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            for line in proc.stdout.splitlines()[1:]:
                if line.strip():
                    connected_devices.append(line.strip())
        else:
            adb_note = proc.stderr.strip()

    status = "NOT RUN" if (not wear_images and not connected_devices) else "READY"
    return {
        "status": status,
        "sdk_root": str(sdk),
        "installed_system_images": installed_images,
        "installed_wear_system_images": wear_images,
        "configured_avds": avds,
        "connected_adb_devices": connected_devices,
        "adb_note": adb_note,
        "reason": "No isolated Wear OS system image (android-wear) or Wear OS AVD is installed locally, and downloading new SDK/emulator images without user approval is prohibited by AG-01.",
        "reproduction_commands": [
            "sdkmanager \"system-images;android-36;android-wear;x86_64\" \"system-images;android-37.0;android-wear;x86_64\"",
            "avdmanager create avd -n aura_wear36_round -k \"system-images;android-36;android-wear;x86_64\" -d wearos_large_round",
            "emulator -avd aura_wear36_round -no-snapshot -no-boot-anim",
            "adb wait-for-device",
            "adb install -r watchface-wff4-debug.apk",
            "adb shell cmd overlay list",
            "adb exec-out screencap -p > active_wff4.png",
            "adb shell input keyevent KEYCODE_SLEEP",
            "adb exec-out screencap -p > ambient_wff4.png",
            "adb shell input keyevent KEYCODE_WAKEUP",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("all", "schema", "apk", "emulator"), default="all")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    summary = {}
    if args.mode in ("all", "schema"):
        summary["schema"] = verify_schemas()
    if args.mode in ("all", "apk"):
        summary["isolated_apks"] = verify_isolated_apks()
    if args.mode in ("all", "emulator"):
        summary["emulator"] = inspect_emulator_environment()
        print(f"[EMULATOR] status={summary['emulator']['status']} wear_images={summary['emulator']['installed_wear_system_images']} avds={summary['emulator']['configured_avds']}")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[REPORT] Wrote verification JSON to {args.json_out}")


if __name__ == "__main__":
    main()
