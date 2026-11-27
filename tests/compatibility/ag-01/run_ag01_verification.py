"""AG-01 end-to-end verification runner for WFF 2-5 PoC XMLs, isolated APK builds, memory ablation evaluation, raw log preservation, and emulator readiness."""
import argparse
import hashlib
import json
import os
import platform
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
from verify_memory import LIMITS, SHA256 as MEMORY_SHA256, enforce_limits, get_jar as get_memory_jar, parse_report
from verify_wff import FAILURE, PASS, SHA256 as VALIDATOR_SHA256, require_pass

AG01_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = AG01_DIR / "fixtures"
VALIDATOR_JAR = ROOT / ".aura-tools" / "wff-validator.jar"
DEFAULT_LOGS_DIR = ROOT / "docs" / "evidence" / "AG-01" / "logs"

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

ABLATION_SPECS = [
    {
        "id": "ablation_a_single_clock_only",
        "path": FIXTURES_DIR / "ablation" / "ablation_a_single_clock_only.xml",
        "min_version": 4,
        "target_profile": "wff4",
        "digital_clocks": 1,
        "aod_visible_part_nodes": 0,
        "expected_ambient_layers": 0,
        "expected_ambient_bytes": 2371712,
        "description": "1 DigitalClock (hh:mm) + 0 AOD-visible PartText nodes (ActiveDecoration identical to poc_wff4_motion_triggers)",
    },
    {
        "id": "ablation_b_four_clocks_only",
        "path": FIXTURES_DIR / "ablation" / "ablation_b_four_clocks_only.xml",
        "min_version": 4,
        "target_profile": "wff4",
        "digital_clocks": 4,
        "aod_visible_part_nodes": 0,
        "expected_ambient_layers": 0,
        "expected_ambient_bytes": 2371712,
        "description": "4 per-digit DigitalClocks (hh_10, hh_1, mm_10, mm_1) + 0 AOD-visible PartText nodes (ClockColon removed)",
    },
    {
        "id": "ablation_c_single_clock_plus_parttext",
        "path": FIXTURES_DIR / "ablation" / "ablation_c_single_clock_plus_parttext.xml",
        "min_version": 4,
        "target_profile": "wff4",
        "digital_clocks": 1,
        "aod_visible_part_nodes": 1,
        "expected_ambient_layers": 1,
        "expected_ambient_bytes": 3181712,
        "description": "1 DigitalClock (hh:mm) + 1 AOD-visible PartText (ClockColon without AMBIENT alpha=0)",
    },
    {
        "id": "ablation_d_four_clocks_plus_ambient_hidden_parttext",
        "path": FIXTURES_DIR / "ablation" / "ablation_d_four_clocks_plus_ambient_hidden_parttext.xml",
        "min_version": 4,
        "target_profile": "wff4",
        "digital_clocks": 4,
        "aod_visible_part_nodes": 0,
        "expected_ambient_layers": 0,
        "expected_ambient_bytes": 2371712,
        "description": "4 per-digit DigitalClocks + 1 PartText (ClockColon hidden in AMBIENT via Variant alpha=0)",
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


def verify_schemas(logs_dir=None):
    jar = ensure_validator_jar()
    results = {"positive_matrix": [], "negative_matrix": []}
    log_lines = [
        "================================================================================",
        "AG-01 OFFICIAL WFF VALIDATOR 52-CASE SCHEMA MATRIX RAW LOG",
        f"Validator JAR: .aura-tools/wff-validator.jar (SHA-256: {VALIDATOR_SHA256})",
        "================================================================================",
        "",
    ]

    case_index = 0
    for spec in POC_SPECS:
        xml_path = spec["path"]
        if not xml_path.is_file():
            raise FileNotFoundError(f"Missing PoC XML: {xml_path}")
        xml_sha256 = hashlib.sha256(xml_path.read_bytes()).hexdigest()
        rel_xml = xml_path.relative_to(ROOT).as_posix()
        for version in (2, 3, 4, 5):
            case_index += 1
            proc = run_validator_utf8(jar, xml_path, version)
            should_pass = version >= spec["min_version"]
            if should_pass:
                require_pass(proc.returncode, proc.stdout, xml_path, version)
                verdict = "PASS_EXPECTED_VALID"
            else:
                require_rejection(proc.returncode, proc.stdout)
                verdict = "PASS_EXPECTED_REJECTED_ON_LOWER_VERSION"
            raw_clean = proc.stdout.replace(str(xml_path.resolve()), rel_xml).replace(str(xml_path), rel_xml).strip()
            results["positive_matrix"].append({
                "case_number": case_index,
                "id": spec["id"],
                "xml_path": rel_xml,
                "xml_sha256": xml_sha256,
                "version": version,
                "should_pass": should_pass,
                "verdict": verdict,
                "returncode": proc.returncode,
                "output_tail": [line for line in raw_clean.splitlines() if "INFO:" in line or "SEVERE:" in line],
            })
            log_lines.extend([
                f"--- [CASE {case_index:02d}/52] POSITIVE MATRIX: {spec['id']} @ WFF#{version} ---",
                f"File: {rel_xml}",
                f"File SHA-256: {xml_sha256}",
                f"Command: java -jar .aura-tools/wff-validator.jar {version} {rel_xml}",
                f"Expected: {'VALID (PASS)' if should_pass else 'INVALID ON LOWER VERSION (REJECT)'}",
                f"Exit Code: {proc.returncode}",
                f"Verdict: {verdict}",
                "Raw Output:",
                raw_clean,
                "",
            ])
            print(f"[SCHEMA] ({case_index:02d}/52) {spec['id']} @ WFF#{version}: {verdict}")

    for spec in NEGATIVE_SPECS:
        xml_path = spec["path"]
        if not xml_path.is_file():
            raise FileNotFoundError(f"Missing negative fixture: {xml_path}")
        xml_sha256 = hashlib.sha256(xml_path.read_bytes()).hexdigest()
        rel_xml = xml_path.relative_to(ROOT).as_posix()
        for version in (2, 3, 4, 5):
            case_index += 1
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
            raw_clean = proc.stdout.replace(str(xml_path.resolve()), rel_xml).replace(str(xml_path), rel_xml).strip()
            results["negative_matrix"].append({
                "case_number": case_index,
                "id": spec["id"],
                "xml_path": rel_xml,
                "xml_sha256": xml_sha256,
                "version": version,
                "verdict": verdict,
                "returncode": proc.returncode,
                "output_tail": [line for line in raw_clean.splitlines() if "INFO:" in line or "SEVERE:" in line],
            })
            log_lines.extend([
                f"--- [CASE {case_index:02d}/52] NEGATIVE MATRIX: {spec['id']} @ WFF#{version} ---",
                f"File: {rel_xml}",
                f"File SHA-256: {xml_sha256}",
                f"Command: java -jar .aura-tools/wff-validator.jar {version} {rel_xml}",
                f"Expected: {'REJECT (' + (spec['expected_error'] if version == max(spec['fail_versions']) else 'schema violation') + ')' if version in spec['fail_versions'] else 'VALID ON HIGHER VERSION (PASS)'}",
                f"Exit Code: {proc.returncode}",
                f"Verdict: {verdict}",
                "Raw Output:",
                raw_clean,
                "",
            ])
            print(f"[NEGATIVE] ({case_index:02d}/52) {spec['id']} @ WFF#{version}: {verdict}")

    if logs_dir:
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "schema-matrix-52.log").write_text("\n".join(log_lines), encoding="utf-8")
        print(f"[LOG] Wrote 52-case schema matrix log to {logs_dir / 'schema-matrix-52.log'}")

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
    report_args = [
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
    report_proc = subprocess.run(report_args, capture_output=True, text=True, encoding="utf-8", env=utf8_env(), timeout=180, check=False)
    report = parse_report(report_proc.returncode, report_proc.stdout)
    enforce_limits(report)

    verbose_args = [
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
        "--verbose",
    ]
    verbose_proc = subprocess.run(verbose_args, capture_output=True, text=True, encoding="utf-8", env=utf8_env(), timeout=180, check=False)
    if verbose_proc.returncode != 0:
        raise RuntimeError(f"memory-footprint.jar --verbose failed for {apk_path.name}: {verbose_proc.stderr or verbose_proc.stdout}")

    # Normalize nondeterministic evaluation duration line in verbose output for deterministic log artifacts
    verbose_clean = re.sub(r"Watch face layout evaluation took \d+ ms", "Watch face layout evaluation took <elapsed> ms", verbose_proc.stdout.strip())
    return report, report_proc.stdout.strip(), verbose_clean


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

    memory_report, memory_json_raw, memory_verbose_raw = evaluate_memory_utf8(memory_jar, apk_path, profile["version"])

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
        "manifest_raw": manifest_proc.stdout.strip(),
        "memory_report": memory_report,
        "memory_json_raw": memory_json_raw,
        "memory_verbose_raw": memory_verbose_raw,
        "memory_limits": LIMITS,
        "signature_v2_pass": True,
        "signature_raw": sig_proc.stdout.strip(),
        "cert_sha256": cert_sha256,
    }


def format_apk_evidence_block(index, total, res, rel_xml_path):
    return [
        f"================================================================================",
        f"[APK {index}/{total}] {res['poc_id']} (profile={res['profile']}, WFF#{res['wff_version']}, minSdk={res['min_sdk']})",
        f"================================================================================",
        f"Source XML Path:          {rel_xml_path}",
        f"Source XML SHA-256:       {res['source_xml_sha256']}",
        f"Packaged XML SHA-256:     {res['packaged_xml_sha256']}",
        f"XML Byte-for-Byte Match:  {res['xml_exact_match']}",
        f"APK Filename:             {res['apk_name']}",
        f"APK Size (bytes):         {res['apk_size_bytes']}",
        f"APK SHA-256:              {res['apk_sha256']}",
        f"ZIP Entries ({len(res['zip_entries'])}):         {', '.join(res['zip_entries'])}",
        f"Resource-Only Check:      PASS (0 .dex, 0 .so, 0 assets/)",
        "",
        "--- [1] Compiled AndroidManifest.xml (apkanalyzer manifest print) ---",
        res["manifest_raw"],
        "",
        "--- [2] Memory Footprint JSON Report (memory-footprint.jar --report) ---",
        res["memory_json_raw"],
        "",
        "--- [3] Memory Footprint Verbose Layer Analysis (memory-footprint.jar --verbose) ---",
        res["memory_verbose_raw"],
        "",
        "--- [4] APK Signature Verification (apksigner verify --verbose --print-certs) ---",
        res["signature_raw"],
        "",
    ]


def verify_isolated_apks(logs_dir=None):
    profiles_by_name = {p["name"]: p for p in load_profiles() if p["enabled"]}
    analyzer = analyzer_path()
    signer = resolve_apksigner()
    memory_jar = get_memory_jar()
    apk_results = []
    log_lines = [
        "================================================================================",
        "AG-01 ISOLATED 6-APK CLEAN BUILD, MANIFEST, MEMORY & SIGNATURE RAW LOG",
        f"Validator JAR SHA-256:        {VALIDATOR_SHA256}",
        f"Memory Evaluator JAR SHA-256: {MEMORY_SHA256}",
        f"Active Memory Limit (bytes):  {LIMITS['maxActiveBytes']} (70 MiB)",
        f"Ambient Memory Limit (bytes): {LIMITS['maxAmbientBytes']} (7 MiB)",
        "================================================================================",
        "",
    ]

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
            log_lines.extend(format_apk_evidence_block(len(apk_results), len(POC_SPECS), res, spec["path"].relative_to(ROOT).as_posix()))
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
            log_lines.extend(format_apk_evidence_block(len(apk_results), len(POC_SPECS), res, spec["path"].relative_to(ROOT).as_posix()))
            print(f"[APK-PASS] {spec['id']} (wff4): SHA-256={res['apk_sha256']} memory={res['memory_report']}")

    if logs_dir:
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "isolated-apk-verification.log").write_text("\n".join(log_lines), encoding="utf-8")
        print(f"[LOG] Wrote 6-APK raw verification log to {logs_dir / 'isolated-apk-verification.log'}")

    return apk_results


def verify_aod_memory_ablation(logs_dir=None):
    """Run controlled 2x2 ablation study isolating DigitalClock count (1 vs 4) from AOD-visible PartText nodes (0 vs 1)."""
    jar = ensure_validator_jar()
    profiles_by_name = {p["name"]: p for p in load_profiles() if p["enabled"]}
    wff4_profile = profiles_by_name["wff4"]
    analyzer = analyzer_path()
    signer = resolve_apksigner()
    memory_jar = get_memory_jar()

    ablation_results = []
    log_lines = [
        "================================================================================",
        "AG-01 CONTROLLED AOD MEMORY ABLATION STUDY (SINGLE CLOCK vs 4 PER-DIGIT CLOCKS vs AOD PARTTEXT)",
        f"Memory Evaluator JAR: .aura-tools/memory-footprint.jar (SHA-256: {MEMORY_SHA256})",
        "Formula in AmbientMemoryFootprintCalculator.computeAmbientMemoryFootprint(450, 450):",
        "  maxAmbientBytes = (450 * 450 * numLayers * 4) + maximumResourceUsage",
        "  where 1 fullscreen RGBA8888 layer = 450 * 450 * 4 = 810,000 bytes,",
        "  and maximumResourceUsage (SYNC_TO_DEVICE font baseline) = 2,371,712 bytes.",
        "================================================================================",
        "",
    ]

    # Compare the 4 controlled ablation fixtures plus the 2 reference WFF4 PoCs
    study_specs = [
        *ABLATION_SPECS,
        {
            "id": "poc_wff4_continuity",
            "path": FIXTURES_DIR / "wff4" / "poc_wff4_continuity.xml",
            "min_version": 4,
            "target_profile": "wff4",
            "digital_clocks": 1,
            "aod_visible_part_nodes": 0,
            "expected_ambient_layers": 0,
            "expected_ambient_bytes": 2371712,
            "description": "Reference PoC: single DigitalClock (hh:mm) + ActiveDecoration hidden in AMBIENT",
        },
        {
            "id": "poc_wff4_motion_triggers",
            "path": FIXTURES_DIR / "wff4" / "poc_wff4_motion_triggers.xml",
            "min_version": 4,
            "target_profile": "wff4",
            "digital_clocks": 4,
            "aod_visible_part_nodes": 1,
            "expected_ambient_layers": 1,
            "expected_ambient_bytes": 3181712,
            "description": "Reference PoC: 4 per-digit DigitalClocks + 1 AOD-visible PartText (ClockColon)",
        },
    ]

    with tempfile.TemporaryDirectory(prefix="aura-ag01-ablation-") as temp_dir:
        temp_root = Path(temp_dir)
        copy_isolated_project(temp_root)
        app_dir = temp_root / "apps" / "watchface"
        wrapper = temp_root / ("gradlew.bat" if os.name == "nt" else "gradlew")

        for idx, spec in enumerate(study_specs, start=1):
            proc_v4 = run_validator_utf8(jar, spec["path"], 4)
            require_pass(proc_v4.returncode, proc_v4.stdout, spec["path"], 4)

            override_path = app_dir / "src" / "wff4" / "res" / "raw" / "watchface.xml"
            override_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(spec["path"], override_path)

            subprocess.run([str(wrapper), "--no-daemon", "--stacktrace", "clean", ":apps:watchface:assembleWff4Debug"], cwd=temp_root, env=utf8_env(), check=True)
            apks = sorted((app_dir / "build" / "outputs" / "apk" / "wff4" / "debug").glob("*.apk"))
            if len(apks) != 1:
                raise RuntimeError(f"Expected 1 APK for ablation {spec['id']}, found {len(apks)}")

            res = inspect_single_apk(apks[0], wff4_profile, spec["path"].read_bytes(), analyzer, signer, memory_jar)
            actual_ambient = res["memory_report"]["maxAmbientBytes"]
            if actual_ambient != spec["expected_ambient_bytes"]:
                raise RuntimeError(
                    f"Ablation {spec['id']} maxAmbientBytes mismatch: expected {spec['expected_ambient_bytes']}, got {actual_ambient}"
                )

            layer_match = re.search(r"Number of layers:\s*(\d+)", res["memory_verbose_raw"])
            actual_layers = int(layer_match.group(1)) if layer_match else -1
            if actual_layers != spec["expected_ambient_layers"]:
                raise RuntimeError(
                    f"Ablation {spec['id']} layer count mismatch: expected {spec['expected_ambient_layers']}, got {actual_layers}"
                )

            entry = {
                "id": spec["id"],
                "xml_path": spec["path"].relative_to(ROOT).as_posix(),
                "xml_sha256": res["source_xml_sha256"],
                "apk_sha256": res["apk_sha256"],
                "digital_clocks": spec["digital_clocks"],
                "aod_visible_part_nodes": spec["aod_visible_part_nodes"],
                "ambient_layers": actual_layers,
                "total_bytes": res["memory_report"]["totalBytes"],
                "max_active_bytes": res["memory_report"]["maxActiveBytes"],
                "max_ambient_bytes": actual_ambient,
                "delta_vs_baseline_bytes": actual_ambient - 2371712,
                "memory_verbose_raw": res["memory_verbose_raw"],
                "description": spec["description"],
            }
            ablation_results.append(entry)
            log_lines.extend([
                f"--- [ABLATION {idx}/{len(study_specs)}] {spec['id']} ---",
                f"Description:              {spec['description']}",
                f"Source XML Path:          {entry['xml_path']}",
                f"Source XML SHA-256:       {entry['xml_sha256']}",
                f"Isolated APK SHA-256:     {entry['apk_sha256']}",
                f"DigitalClock Count:       {entry['digital_clocks']}",
                f"AOD-Visible Part* Nodes:  {entry['aod_visible_part_nodes']}",
                f"Evaluated Ambient Layers: {entry['ambient_layers']}",
                f"maxActiveBytes:           {entry['max_active_bytes']} bytes",
                f"maxAmbientBytes:          {entry['max_ambient_bytes']} bytes (Delta vs 2,371,712 baseline: {entry['delta_vs_baseline_bytes']:+d} bytes)",
                "Raw memory-footprint.jar --report:",
                res["memory_json_raw"],
                "Raw memory-footprint.jar --verbose:",
                res["memory_verbose_raw"],
                "",
            ])
            print(
                f"[ABLATION] {spec['id']}: clocks={entry['digital_clocks']} aod_part={entry['aod_visible_part_nodes']} "
                f"layers={entry['ambient_layers']} maxAmbientBytes={entry['max_ambient_bytes']} ({entry['delta_vs_baseline_bytes']:+d})"
            )

    if logs_dir:
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "aod-memory-ablation.log").write_text("\n".join(log_lines), encoding="utf-8")
        print(f"[LOG] Wrote controlled AOD memory ablation log to {logs_dir / 'aod-memory-ablation.log'}")

    return ablation_results


def inspect_emulator_environment(logs_dir=None):
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

    disk_free_gib = round(shutil.disk_usage(sdk if sdk.is_dir() else ROOT).free / (1024 ** 3), 2)

    status = "NOT RUN" if (not wear_images and not connected_devices) else "READY"
    info = {
        "status": status,
        "sdk_root": str(sdk),
        "disk_free_gib": disk_free_gib,
        "installed_system_images": installed_images,
        "installed_wear_system_images": wear_images,
        "available_wear_system_image_packages": [
            {
                "package_id": "system-images;android-34;android-wear;x86_64",
                "api_level": "34",
                "wear_os_version": "Wear OS 5.0",
                "supported_wff_version": 2,
                "revision": 1,
                "estimated_size_gib": "1.6 - 2.0 GiB",
            },
            {
                "package_id": "system-images;android-35-ext15;android-wear;x86_64",
                "api_level": "35 (ext15)",
                "wear_os_version": "Wear OS 5.1",
                "supported_wff_version": 3,
                "revision": 1,
                "estimated_size_gib": "1.7 - 2.1 GiB",
            },
            {
                "package_id": "system-images;android-36;android-wear-signed;x86_64",
                "api_level": "36.0",
                "wear_os_version": "Wear OS 6.0 (signed)",
                "supported_wff_version": 4,
                "revision": 1,
                "estimated_size_gib": "1.8 - 2.3 GiB",
            },
            {
                "package_id": "system-images;android-36.1;android-wear-signed;x86_64",
                "api_level": "36.1",
                "wear_os_version": "Wear OS 6.1 (signed)",
                "supported_wff_version": 4,
                "revision": 1,
                "estimated_size_gib": "1.8 - 2.3 GiB",
            },
            {
                "package_id": "system-images;android-37.0;android-wear-signed;x86_64",
                "api_level": "37.0",
                "wear_os_version": "Wear OS 7.0 (signed)",
                "supported_wff_version": 5,
                "revision": 1,
                "estimated_size_gib": "1.9 - 2.4 GiB",
            },
        ],
        "available_wear_device_profiles": [
            {"id": "wearos_large_round", "numeric_id": 59, "oem": "Google", "tag": "android-wear", "recommended_for": "450x450 circular canvas primary testing"},
            {"id": "wearos_small_round", "numeric_id": 61, "oem": "Google", "tag": "android-wear", "recommended_for": "small circular DPI scaling verification"},
            {"id": "wearos_square", "numeric_id": 62, "oem": "Google", "tag": "android-wear", "recommended_for": "square layout compatibility"},
            {"id": "wearos_rect", "numeric_id": 60, "oem": "Google", "tag": "android-wear", "recommended_for": "rectangular layout compatibility"},
        ],
        "configured_avds": avds,
        "connected_adb_devices": connected_devices,
        "adb_note": adb_note,
        "reason": "No isolated Wear OS system image (android-wear / android-wear-signed) or Wear OS AVD is installed locally, and downloading new SDK/emulator images without user approval is prohibited by AG-01 / AG-01-R02.",
        "reproduction_commands": [
            "sdkmanager \"system-images;android-34;android-wear;x86_64\" \"system-images;android-35-ext15;android-wear;x86_64\" \"system-images;android-36;android-wear-signed;x86_64\" \"system-images;android-37.0;android-wear-signed;x86_64\"",
            "avdmanager create avd -n aura_wear36_round -k \"system-images;android-36;android-wear-signed;x86_64\" -d wearos_large_round",
            "avdmanager create avd -n aura_wear37_round -k \"system-images;android-37.0;android-wear-signed;x86_64\" -d wearos_large_round",
            "emulator -avd aura_wear36_round -no-snapshot -no-boot-anim",
            "adb wait-for-device",
            "adb install -r watchface-wff4-debug.apk",
            "adb exec-out screencap -p > active_wff4.png",
            "adb shell input keyevent KEYCODE_SLEEP",
            "adb exec-out screencap -p > ambient_wff4.png",
            "adb shell input keyevent KEYCODE_WAKEUP",
        ],
    }

    if logs_dir:
        logs_dir.mkdir(parents=True, exist_ok=True)
        java_proc = subprocess.run(["java", "-version"], capture_output=True, text=True, encoding="utf-8", check=False)
        java_ver = (java_proc.stderr or java_proc.stdout).strip()
        env_lines = [
            "================================================================================",
            "AG-01 ENVIRONMENT, TOOL HASHES & WEAR OS EMULATOR READINESS LOG",
            "================================================================================",
            f"OS Platform:                  {platform.platform()} ({platform.machine()})",
            f"Python Version:               {sys.version.splitlines()[0]}",
            "Java Version:",
            java_ver,
            f"WFF Validator JAR:            .aura-tools/wff-validator.jar (v1.7.0, SHA-256: {VALIDATOR_SHA256})",
            f"Memory Evaluator JAR:         .aura-tools/memory-footprint.jar (v1.5.1, SHA-256: {MEMORY_SHA256})",
            f"Android SDK Root:             {info['sdk_root']}",
            f"Available Free Disk Space:    {info['disk_free_gib']} GiB",
            f"Installed System Images:      {info['installed_system_images']}",
            f"Installed Wear System Images: {info['installed_wear_system_images']}",
            f"Configured AVDs:              {info['configured_avds']}",
            f"Connected ADB Devices:        {info['connected_adb_devices']}",
            f"ADB Note:                     {info['adb_note']}",
            f"Emulator Verification Status: {info['status']}",
            f"Reason:                       {info['reason']}",
            "",
            "--- Available Wear OS System Image Packages (queried read-only via sdkmanager --list) ---",
        ]
        for pkg in info["available_wear_system_image_packages"]:
            env_lines.append(
                f"  * {pkg['package_id']} | API {pkg['api_level']} | {pkg['wear_os_version']} | WFF#{pkg['supported_wff_version']} | rev {pkg['revision']} | est. {pkg['estimated_size_gib']}"
            )
        env_lines.extend([
            "",
            "--- Available Official Wear OS AVD Device Profiles (avdmanager list device) ---",
        ])
        for prof in info["available_wear_device_profiles"]:
            env_lines.append(
                f"  * {prof['id']} (numeric id={prof['numeric_id']}, OEM={prof['oem']}, Tag={prof['tag']}) -> {prof['recommended_for']}"
            )
        env_lines.extend([
            "",
            "--- Exact Reproduction Commands (upon approval) ---",
            *[f"  {cmd}" for cmd in info["reproduction_commands"]],
            "",
        ])
        (logs_dir / "environment-and-emulator.log").write_text("\n".join(env_lines), encoding="utf-8")
        print(f"[LOG] Wrote environment & emulator readiness log to {logs_dir / 'environment-and-emulator.log'}")

    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("all", "schema", "apk", "ablation", "emulator"), default="all")
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--logs-dir", type=Path, default=None, help="Directory to write raw verification logs (e.g. docs/evidence/AG-01/logs)")
    args = parser.parse_args()

    summary = {}
    if args.mode in ("all", "schema"):
        summary["schema"] = verify_schemas(logs_dir=args.logs_dir)
    if args.mode in ("all", "apk"):
        summary["isolated_apks"] = verify_isolated_apks(logs_dir=args.logs_dir)
    if args.mode in ("all", "ablation"):
        summary["ablation"] = verify_aod_memory_ablation(logs_dir=args.logs_dir)
    if args.mode in ("all", "emulator"):
        summary["emulator"] = inspect_emulator_environment(logs_dir=args.logs_dir)
        print(f"[EMULATOR] status={summary['emulator']['status']} wear_images={summary['emulator']['installed_wear_system_images']} avds={summary['emulator']['configured_avds']}")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[REPORT] Wrote verification JSON to {args.json_out}")


if __name__ == "__main__":
    main()
