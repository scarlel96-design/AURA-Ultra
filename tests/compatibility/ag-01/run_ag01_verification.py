"""AG-01 end-to-end verification runner for WFF 2-5 PoC XMLs, isolated APK builds, memory ablation evaluation, raw log preservation, and live Wear OS emulator environment inspection."""
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
from verify_wff import PASS, SHA256 as VALIDATOR_SHA256, require_pass
from wear_emulator_runtime import RECOMMENDED_WEAR_AVD_PLANS, build_safe_setup_commands

AG01_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = AG01_DIR / "fixtures"
VALIDATOR_JAR = ROOT / ".aura-tools" / "wff-validator.jar"

JAVA_UTF8_OPTS = "-Dfile.encoding=UTF-8 -Dsun.stdout.encoding=UTF-8 -Dsun.stderr.encoding=UTF-8"

# Strict WFF validator rejection patterns (AG01-AUD-02)
VALIDATOR_BANNER = re.compile(r"^INFO:\s*WFF Validation Application Version\s+\S+")
FAIL_VERDICT = re.compile(
    r"^INFO:\s*(?:❌\s*)?FAILED\s*:\s*(.+?) is NOT valid against watch face format version #(\d+)\s*$"
)
SCHEMA_SEVERE = re.compile(r"^SEVERE:\s*\[Line \d+:Column \d+\]:\s*(.+)$")

# Estimated Wear OS system image candidates (STRICTLY SEPARATED from live `sdkmanager --list` observations; AG01-AUD-01)
ESTIMATED_WEAR_IMAGE_CANDIDATES = [
    {
        "package_id": "system-images;android-36;android-wear-signed;x86_64",
        "target_wff_version": 4,
        "target_api_level": "36",
        "estimated_download_and_avd_gib": "~3.0 GiB (est.)",
        "priority": "P0 (Primary WFF 4)",
    },
    {
        "package_id": "system-images;android-37.0;android-wear-signed;x86_64",
        "target_wff_version": 5,
        "target_api_level": "37.0",
        "estimated_download_and_avd_gib": "~3.2 GiB (est.)",
        "priority": "P0 (Primary WFF 5)",
    },
    {
        "package_id": "system-images;android-36.1;android-wear-signed;x86_64",
        "target_wff_version": 4,
        "target_api_level": "36.1",
        "estimated_download_and_avd_gib": "~3.0 GiB (est.)",
        "priority": "P2 (Optional WFF 4 minor)",
    },
    {
        "package_id": "system-images;android-35-ext15;android-wear;x86_64",
        "target_wff_version": 3,
        "target_api_level": "35-ext15",
        "estimated_download_and_avd_gib": "~2.8 GiB (est.)",
        "priority": "P1 (Optional WFF 3 expansion)",
    },
    {
        "package_id": "system-images;android-34;android-wear;x86_64",
        "target_wff_version": 2,
        "target_api_level": "34",
        "estimated_download_and_avd_gib": "~2.6 GiB (est.)",
        "priority": "P1 (Optional WFF 2 expansion)",
    },
]

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
        "description": "Combined fixture preserved from R01/R02 (Variant duration > 1.0 and Reference under DigitalClock)",
    },
]

# Separated single-fault negative fixtures added in R03 (AG01-AUD-02)
SEPARATED_NEGATIVE_SPECS = [
    {
        "id": "neg_wff4_variant_duration_out_of_range",
        "path": FIXTURES_DIR / "negative" / "neg_wff4_variant_duration_out_of_range.xml",
        "fail_versions": [2, 3, 4, 5],
        "pass_versions": [],
        "expected_error": "1.35",
        "description": "Single-fault fixture: Variant duration='1.35' violates maxInclusive '1.0E0' on WFF 4/5",
    },
    {
        "id": "neg_wff4_reference_invalid_parent",
        "path": FIXTURES_DIR / "negative" / "neg_wff4_reference_invalid_parent.xml",
        "fail_versions": [2, 3, 4, 5],
        "pass_versions": [],
        "expected_error": "Reference",
        "description": "Single-fault fixture: <Reference> directly under prohibited parent <DigitalClock> on WFF 4/5",
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


def require_rejection(returncode, output, face, version, expected_error=None):
    """Require an explicit WFF schema FAILED verdict for the exact requested XML file and WFF version.

    Tool execution errors (non-zero JVM exit code, missing banner, crash/timeout, wrong path, wrong version,
    or missing `[Line:Column]` SEVERE schema diagnostics) are strictly rejected as ValueError rather than
    misclassified as expected schema failures (AG01-AUD-02).
    """
    lines = output.splitlines()
    if returncode != 0:
        raise ValueError(
            f"Validator process exited abnormally with returncode={returncode} (tool crash/invocation error, not a clean schema rejection)"
        )
    if not any(VALIDATOR_BANNER.match(line) for line in lines):
        raise ValueError("Missing official WFF Validation Application banner in validator output")
    if any(PASS.fullmatch(line) for line in lines):
        raise ValueError("Fixture unexpectedly produced a PASSED verdict")

    fail_matches = [match for line in lines if (match := FAIL_VERDICT.fullmatch(line))]
    if len(fail_matches) != 1:
        raise ValueError(
            f"Expected exactly 1 explicit FAILED verdict line, found {len(fail_matches)}"
        )
    actual_path, actual_version = fail_matches[0].groups()
    if Path(actual_path).resolve() != Path(face).resolve():
        raise ValueError(
            f"FAILED verdict path mismatch: expected {Path(face).resolve()}, got {Path(actual_path).resolve()}"
        )
    if int(actual_version) != int(version):
        raise ValueError(
            f"FAILED verdict WFF version mismatch: expected #{version}, got #{actual_version}"
        )

    severe_messages = [match.group(1) for line in lines if (match := SCHEMA_SEVERE.match(line))]
    if not severe_messages:
        raise ValueError("Missing schema SEVERE [Line:Column] diagnostic line alongside FAILED verdict")
    if expected_error and not any(expected_error in msg for msg in severe_messages):
        raise ValueError(
            f"Expected schema error substring '{expected_error}' not found in SEVERE diagnostics: {severe_messages}"
        )
    return severe_messages


def verify_schemas(logs_dir=None, include_separated=True):
    jar = ensure_validator_jar()
    results = {"positive_matrix": [], "negative_matrix": [], "separated_negative_matrix": []}
    neg_groups = [("NEGATIVE MATRIX", NEGATIVE_SPECS, "negative_matrix")]
    if include_separated:
        neg_groups.append(("SEPARATED NEGATIVE MATRIX (R03)", SEPARATED_NEGATIVE_SPECS, "separated_negative_matrix"))

    total_cases = (len(POC_SPECS) + sum(len(g[1]) for g in neg_groups)) * 4
    log_lines = [
        "================================================================================",
        f"AG-01 OFFICIAL WFF VALIDATOR {total_cases}-CASE SCHEMA MATRIX RAW LOG (R03 STRICT REJECTION)",
        f"Validator JAR: .aura-tools/wff-validator.jar (SHA-256: {VALIDATOR_SHA256})",
        "Rejection rule: rc == 0, official banner present, 0 PASSED lines, exactly 1 explicit",
        "  FAILED line matching exact resolved XML path and WFF version, >=1 SEVERE [Line:Column]",
        "  schema diagnostic containing expected_error.",
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
                require_rejection(proc.returncode, proc.stdout, xml_path, version)
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
                f"--- [CASE {case_index:02d}/{total_cases}] POSITIVE MATRIX: {spec['id']} @ WFF#{version} ---",
                f"File: {rel_xml}",
                f"File SHA-256: {xml_sha256}",
                f"Command: java -jar .aura-tools/wff-validator.jar {version} {rel_xml}",
                f"Expected: {'VALID (PASS)' if should_pass else 'INVALID ON LOWER VERSION (EXPLICIT FAILED + SEVERE)'}",
                f"Exit Code: {proc.returncode}",
                f"Verdict: {verdict}",
                "Raw Output:",
                raw_clean,
                "",
            ])
            print(f"[SCHEMA] ({case_index:02d}/{total_cases}) {spec['id']} @ WFF#{version}: {verdict}")

    for label, specs, result_key in neg_groups:
        for spec in specs:
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
                    require_rejection(proc.returncode, proc.stdout, xml_path, version, expected_err)
                    verdict = "PASS_DETECTED_INVALID"
                elif version in spec["pass_versions"]:
                    require_pass(proc.returncode, proc.stdout, xml_path, version)
                    verdict = "PASS_VALID_ON_HIGHER_VERSION"
                else:
                    raise ValueError(f"Version {version} unclassified for {spec['id']}")
                raw_clean = proc.stdout.replace(str(xml_path.resolve()), rel_xml).replace(str(xml_path), rel_xml).strip()
                results[result_key].append({
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
                    f"--- [CASE {case_index:02d}/{total_cases}] {label}: {spec['id']} @ WFF#{version} ---",
                    f"File: {rel_xml}",
                    f"File SHA-256: {xml_sha256}",
                    f"Command: java -jar .aura-tools/wff-validator.jar {version} {rel_xml}",
                    f"Expected: {'EXPLICIT FAILED + SEVERE (' + (spec['expected_error'] if version == max(spec['fail_versions']) else 'schema violation') + ')' if version in spec['fail_versions'] else 'VALID ON HIGHER VERSION (PASS)'}",
                    f"Exit Code: {proc.returncode}",
                    f"Verdict: {verdict}",
                    "Raw Output:",
                    raw_clean,
                    "",
                ])
                print(f"[NEGATIVE] ({case_index:02d}/{total_cases}) {spec['id']} @ WFF#{version}: {verdict}")

    if logs_dir:
        logs_dir.mkdir(parents=True, exist_ok=True)
        out_name = f"schema-matrix-{total_cases}-r03.log"
        (logs_dir / out_name).write_text("\n".join(log_lines), encoding="utf-8")
        print(f"[LOG] Wrote {total_cases}-case strict schema matrix log to {logs_dir / out_name}")

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
        "================================================================================",
        f"[APK {index}/{total}] {res['poc_id']} (profile={res['profile']}, WFF#{res['wff_version']}, minSdk={res['min_sdk']})",
        "================================================================================",
        f"Source XML Path:          {rel_xml_path}",
        f"Source XML SHA-256:       {res['source_xml_sha256']}",
        f"Packaged XML SHA-256:     {res['packaged_xml_sha256']}",
        f"XML Byte-for-Byte Match:  {res['xml_exact_match']}",
        f"APK Filename:             {res['apk_name']}",
        f"APK Size (bytes):         {res['apk_size_bytes']}",
        f"APK SHA-256:              {res['apk_sha256']}",
        f"ZIP Entries ({len(res['zip_entries'])}):         {', '.join(res['zip_entries'])}",
        "Resource-Only Check:      PASS (0 .dex, 0 .so, 0 assets/)",
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
        "AG-01 CONTROLLED AOD MEMORY ABLATION STUDY (EVALUATOR MODEL SCOPE ONLY)",
        f"Memory Evaluator JAR: .aura-tools/memory-footprint.jar (SHA-256: {MEMORY_SHA256})",
        "Formula in AmbientMemoryFootprintCalculator.computeAmbientMemoryFootprint(450, 450):",
        "  maxAmbientBytes = (450 * 450 * numLayers * 4) + maximumResourceUsage",
        "  where 1 fullscreen RGBA8888 layer = 450 * 450 * 4 = 810,000 bytes,",
        "  and maximumResourceUsage (SYNC_TO_DEVICE -> Roboto fallback estimate) = 2,371,712 bytes.",
        "Scope note: Static evaluator asset estimation only; does NOT prove real device RAM/power/rendering.",
        "================================================================================",
        "",
    ]

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


# ---------------------------------------------------------------------------
# Live Android SDK / AVD / ADB query & parsing helpers (AG01-AUD-01)
# ---------------------------------------------------------------------------

def _default_tool_runner(cmd, timeout=60):
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return {
            "command": cmd,
            "status": "OK" if proc.returncode == 0 else "ERROR",
            "returncode": proc.returncode,
            "stdout": proc.stdout or "",
            "stderr": proc.stderr or "",
            "error": "" if proc.returncode == 0 else f"Non-zero exit code {proc.returncode}",
        }
    except FileNotFoundError as exc:
        return {
            "command": cmd,
            "status": "MISSING",
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "error": f"Executable not found: {exc}",
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": cmd,
            "status": "TIMEOUT",
            "returncode": None,
            "stdout": (exc.stdout or "") if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "") if isinstance(exc.stderr, str) else "",
            "error": f"Command timed out after {timeout}s",
        }


def resolve_cmdline_tool(sdk_root, name):
    suffix = ".bat" if os.name == "nt" else ""
    candidates = [
        sdk_root / "cmdline-tools" / "latest" / "bin" / f"{name}{suffix}",
        sdk_root / "tools" / "bin" / f"{name}{suffix}",
    ]
    cmdline_dir = sdk_root / "cmdline-tools"
    if cmdline_dir.is_dir():
        for child in sorted(cmdline_dir.iterdir(), reverse=True):
            candidates.append(child / "bin" / f"{name}{suffix}")
    for path in candidates:
        if path.is_file():
            return path
    found = shutil.which(name)
    return Path(found) if found else None


def parse_sdkmanager_list(stdout):
    """Parse live `sdkmanager --list` output into Installed and Available package tables."""
    installed = []
    available = []
    section = None
    for raw_line in (stdout or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lower = line.lower()
        if lower.startswith("installed packages:"):
            section = "installed"
            continue
        if lower.startswith("available packages:"):
            section = "available"
            continue
        if lower.startswith("available updates:"):
            section = "updates"
            continue
        if "|" not in line or line.startswith("Path") or line.startswith("---"):
            continue
        cols = [col.strip() for col in line.split("|")]
        if len(cols) < 3:
            continue
        entry = {
            "package_id": cols[0],
            "version": cols[1],
            "description": cols[2],
            "location": cols[3] if len(cols) >= 4 else "",
        }
        if section == "installed":
            installed.append(entry)
        elif section == "available":
            available.append(entry)
    return {"installed": installed, "available": available}


def parse_avdmanager_devices(stdout):
    """Parse live `avdmanager list device` output into structured device profile records."""
    devices = []
    current = None
    for raw_line in (stdout or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("Available devices"):
            continue
        if line.startswith("---------"):
            if current:
                devices.append(current)
                current = None
            continue
        id_match = re.match(r'^id:\s*(\d+)\s+or\s+"([^"]+)"', line)
        if id_match:
            if current:
                devices.append(current)
            current = {
                "numeric_id": int(id_match.group(1)),
                "id": id_match.group(2),
                "name": "",
                "oem": "",
                "tag": "",
            }
            continue
        if current is None:
            continue
        if line.startswith("Name:"):
            current["name"] = line.split(":", 1)[1].strip()
        elif line.startswith("OEM"):
            current["oem"] = line.split(":", 1)[1].strip()
        elif line.startswith("Tag"):
            current["tag"] = line.split(":", 1)[1].strip()
    if current:
        devices.append(current)
    return devices


def parse_avdmanager_avds(stdout):
    """Parse live `avdmanager list avd` output and separate Wear OS AVDs from phone/tablet AVDs."""
    avds = []
    current = None
    for raw_line in (stdout or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("Available Android Virtual Devices:"):
            continue
        if line.startswith("The following Android Virtual Devices could not be loaded"):
            break
        if line.startswith("---------"):
            if current:
                avds.append(current)
                current = None
            continue
        if line.startswith("Name:"):
            if current:
                avds.append(current)
            current = {
                "name": line.split(":", 1)[1].strip(),
                "device": "",
                "path": "",
                "target": "",
                "tag_abi": "",
                "skin": "",
            }
            continue
        if current is None:
            continue
        if line.startswith("Device:"):
            current["device"] = line.split(":", 1)[1].strip()
        elif line.startswith("Path:"):
            current["path"] = line.split(":", 1)[1].strip()
        elif line.startswith("Target:"):
            current["target"] = line.split(":", 1)[1].strip()
        elif "Tag/ABI:" in line:
            current["tag_abi"] = line.split("Tag/ABI:", 1)[1].strip()
        elif line.startswith("Skin:"):
            current["skin"] = line.split(":", 1)[1].strip()
    if current:
        avds.append(current)

    wear_avds = []
    non_wear_avds = []
    unknown_avds = []
    for avd in avds:
        tag_abi = avd["tag_abi"].lower()
        device = avd["device"].lower()
        if "android-wear" in tag_abi or "wearos" in device:
            avd["classification"] = "wear_os"
            wear_avds.append(avd)
        elif tag_abi or device:
            avd["classification"] = "non_wear"
            non_wear_avds.append(avd)
        else:
            avd["classification"] = "unknown"
            unknown_avds.append(avd)
    return {
        "all": avds,
        "wear_avds": wear_avds,
        "non_wear_avds": non_wear_avds,
        "unknown_avds": unknown_avds,
    }


def parse_adb_devices(stdout):
    """Parse `adb devices -l` and strictly separate emulator serials from physical devices."""
    emulators = []
    physical_devices = []
    for raw_line in (stdout or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("List of devices") or line.startswith("* daemon"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        serial, state = parts[0], parts[1]
        record = {"serial": serial, "state": state, "raw": line}
        if re.fullmatch(r"emulator-\d+", serial):
            emulators.append(record)
        else:
            physical_devices.append(record)
    return {"emulators": emulators, "physical_devices": physical_devices}


def reconcile_wear_candidates(candidates, observed_installed, observed_available):
    """Compare static candidate estimates against live `sdkmanager --list` observations."""
    installed_by_id = {pkg["package_id"]: pkg for pkg in observed_installed}
    available_by_id = {pkg["package_id"]: pkg for pkg in observed_available}
    reconciled = []
    for cand in candidates:
        pid = cand["package_id"]
        inst = installed_by_id.get(pid)
        avail = available_by_id.get(pid)
        reconciled.append({
            **cand,
            "installed": inst is not None,
            "observed_in_available_catalog": avail is not None,
            "observed_revision": (inst or avail or {}).get("version", "NOT_OBSERVED"),
            "observed_description": (inst or avail or {}).get("description", "NOT_OBSERVED"),
        })
    return reconciled


def determine_emulator_readiness(
    tool_runs,
    installed_wear_images,
    wear_avds,
    running_wear_emulators,
):
    """Determine strict Wear OS emulator readiness: READY, NOT RUN, or UNKNOWN.

    - Any missing/failed/timed-out/empty critical SDK/AVD/ADB query -> UNKNOWN (unless a verified running Wear emulator exists).
    - Physical ADB devices or non-Wear phone AVDs NEVER promote status to READY.
    - Installed Wear images alone WITHOUT a Wear OS AVD (or vice versa) stay NOT RUN.
    - Only a verified running Wear emulator OR (installed Wear image + configured Wear AVD + emulator & adb tools OK) yields READY.
    """
    if running_wear_emulators:
        return "READY", f"Verified running Wear OS emulator(s): {[e['serial'] for e in running_wear_emulators]}"

    critical_issues = []
    for tool_name in ("sdkmanager", "avdmanager_devices", "avdmanager_avds", "emulator", "adb"):
        run = tool_runs.get(tool_name, {})
        st = run.get("status")
        if st in ("MISSING", "ERROR", "TIMEOUT", "EMPTY"):
            critical_issues.append(f"{tool_name}={st} ({run.get('error', '')})")
    if critical_issues:
        return "UNKNOWN", "Cannot establish Wear OS emulator readiness due to tool failures: " + "; ".join(critical_issues)

    if installed_wear_images and wear_avds:
        return "READY", f"Wear OS system image(s) and Wear OS AVD(s) ({[a['name'] for a in wear_avds]}) are installed locally."

    reasons = []
    if not installed_wear_images:
        reasons.append("no Wear OS system image (android-wear / android-wear-signed) is installed locally")
    if not wear_avds:
        reasons.append("no Wear OS AVD is configured (non-Wear phone AVDs and physical devices are excluded)")
    reasons.append("downloading new SDK system images or creating AVDs without explicit user approval is prohibited")
    return "NOT RUN", "; ".join(reasons)


def inspect_emulator_environment(logs_dir=None, sdk_root=None, runner=None):
    """Inspect local Android SDK, live sdkmanager/avdmanager catalogs, AVDs, and ADB devices without mutating state."""
    run_fn = runner or _default_tool_runner
    sdk = Path(sdk_root) if sdk_root is not None else Path(os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT") or "")

    sdkmanager_bin = resolve_cmdline_tool(sdk, "sdkmanager") if sdk.is_dir() else None
    avdmanager_bin = resolve_cmdline_tool(sdk, "avdmanager") if sdk.is_dir() else None
    emulator_bin = sdk / "emulator" / ("emulator.exe" if os.name == "nt" else "emulator")
    adb_bin = sdk / "platform-tools" / ("adb.exe" if os.name == "nt" else "adb")

    tool_runs = {}

    # 1. Live `sdkmanager --list` (read-only query; never downloads packages)
    if sdkmanager_bin and sdkmanager_bin.is_file():
        sm_run = run_fn([str(sdkmanager_bin), "--list"], timeout=90)
        if sm_run["status"] == "OK" and not sm_run["stdout"].strip():
            sm_run["status"] = "EMPTY"
            sm_run["error"] = "sdkmanager --list returned empty stdout"
    else:
        sm_run = {"command": ["sdkmanager", "--list"], "status": "MISSING", "returncode": None, "stdout": "", "stderr": "", "error": "sdkmanager binary not found"}
    tool_runs["sdkmanager"] = sm_run

    parsed_sdk = parse_sdkmanager_list(sm_run["stdout"]) if sm_run["status"] == "OK" else {"installed": [], "available": []}
    if sm_run["status"] == "OK" and not parsed_sdk["installed"] and not parsed_sdk["available"]:
        sm_run["status"] = "EMPTY"
        sm_run["error"] = "sdkmanager --list stdout contained no parseable Installed or Available package rows"

    observed_installed_wear = [
        pkg for pkg in parsed_sdk["installed"]
        if "android-wear" in pkg["package_id"].lower()
    ]
    observed_available_wear = [
        pkg for pkg in parsed_sdk["available"]
        if "android-wear" in pkg["package_id"].lower()
    ]
    reconciled_candidates = reconcile_wear_candidates(
        ESTIMATED_WEAR_IMAGE_CANDIDATES,
        parsed_sdk["installed"],
        parsed_sdk["available"],
    )

    # 2. Live `avdmanager list device`
    if avdmanager_bin and avdmanager_bin.is_file():
        dev_run = run_fn([str(avdmanager_bin), "list", "device"], timeout=60)
        if dev_run["status"] == "OK" and not dev_run["stdout"].strip():
            dev_run["status"] = "EMPTY"
            dev_run["error"] = "avdmanager list device returned empty stdout"
    else:
        dev_run = {"command": ["avdmanager", "list", "device"], "status": "MISSING", "returncode": None, "stdout": "", "stderr": "", "error": "avdmanager binary not found"}
    tool_runs["avdmanager_devices"] = dev_run

    all_devices = parse_avdmanager_devices(dev_run["stdout"]) if dev_run["status"] == "OK" else []
    if dev_run["status"] == "OK" and not all_devices:
        dev_run["status"] = "EMPTY"
        dev_run["error"] = "avdmanager list device stdout contained no parseable device definitions"
    observed_wear_device_profiles = [
        d for d in all_devices
        if "android-wear" in d["tag"].lower() or "wearos" in d["id"].lower()
    ]

    # 3. Live `avdmanager list avd` (separates Wear AVDs from phone/tablet AVDs)
    if avdmanager_bin and avdmanager_bin.is_file():
        avd_run = run_fn([str(avdmanager_bin), "list", "avd"], timeout=60)
        if avd_run["status"] == "OK" and not avd_run["stdout"].strip():
            avd_run["status"] = "EMPTY"
            avd_run["error"] = "avdmanager list avd returned empty stdout"
    else:
        avd_run = {"command": ["avdmanager", "list", "avd"], "status": "MISSING", "returncode": None, "stdout": "", "stderr": "", "error": "avdmanager binary not found"}
    tool_runs["avdmanager_avds"] = avd_run
    parsed_avds = parse_avdmanager_avds(avd_run["stdout"]) if avd_run["status"] == "OK" else {"all": [], "wear_avds": [], "non_wear_avds": [], "unknown_avds": []}

    # 4. Live `emulator -list-avds`
    if emulator_bin.is_file():
        emu_run = run_fn([str(emulator_bin), "-list-avds"], timeout=30)
    else:
        emu_run = {"command": ["emulator", "-list-avds"], "status": "MISSING", "returncode": None, "stdout": "", "stderr": "", "error": f"emulator binary not found at {emulator_bin}"}
    tool_runs["emulator"] = emu_run
    emulator_listed_avds = [line.strip() for line in emu_run["stdout"].splitlines() if line.strip()] if emu_run["status"] == "OK" else []

    # 5. Live `adb devices -l` + Wear emulator verification (never counts physical devices as Wear emulators)
    if adb_bin.is_file():
        adb_run = run_fn([str(adb_bin), "devices", "-l"], timeout=30)
    else:
        adb_run = {"command": ["adb", "devices", "-l"], "status": "MISSING", "returncode": None, "stdout": "", "stderr": "", "error": f"adb binary not found at {adb_bin}"}
    tool_runs["adb"] = adb_run
    parsed_adb = parse_adb_devices(adb_run["stdout"]) if adb_run["status"] == "OK" else {"emulators": [], "physical_devices": []}

    running_wear_emulators = []
    running_non_wear_emulators = []
    for emu in parsed_adb["emulators"]:
        if emu["state"] != "device":
            continue
        char_run = run_fn([str(adb_bin), "-s", emu["serial"], "shell", "getprop", "ro.build.characteristics"], timeout=15)
        chars = char_run["stdout"].strip() if char_run["status"] == "OK" else ""
        emu_entry = {**emu, "characteristics": chars}
        if "watch" in {c.strip().lower() for c in chars.split(",") if c.strip()}:
            running_wear_emulators.append(emu_entry)
        else:
            running_non_wear_emulators.append(emu_entry)

    # Also inspect local filesystem system-images directory for independent cross-check
    fs_installed_images = []
    fs_installed_wear_images = []
    sys_images_dir = sdk / "system-images" if sdk.is_dir() else None
    if sys_images_dir and sys_images_dir.is_dir():
        for prop in sorted(sys_images_dir.rglob("source.properties")):
            rel = str(prop.parent.relative_to(sdk))
            fs_installed_images.append(rel)
            if "wear" in rel.lower():
                fs_installed_wear_images.append(rel)

    status, reason = determine_emulator_readiness(
        tool_runs=tool_runs,
        installed_wear_images=observed_installed_wear,
        wear_avds=parsed_avds["wear_avds"],
        running_wear_emulators=running_wear_emulators,
    )

    disk_free_gib = round(shutil.disk_usage(sdk if sdk.is_dir() else ROOT).free / (1024 ** 3), 2)

    safe_setup_commands = []
    for plan in RECOMMENDED_WEAR_AVD_PLANS[:2]:
        safe_setup_commands.extend(build_safe_setup_commands(plan))

    info = {
        "status": status,
        "reason": reason,
        "sdk_root": str(sdk),
        "disk_free_gib": disk_free_gib,
        "tool_runs": {
            k: {"status": v["status"], "returncode": v["returncode"], "error": v["error"]}
            for k, v in tool_runs.items()
        },
        "filesystem_installed_system_images": fs_installed_images,
        "filesystem_installed_wear_images": fs_installed_wear_images,
        "observed_sdkmanager_installed_packages_count": len(parsed_sdk["installed"]),
        "observed_sdkmanager_installed_wear_images": observed_installed_wear,
        "observed_sdkmanager_available_wear_images": observed_available_wear,
        "estimated_candidates_reconciled_with_live_catalog": reconciled_candidates,
        "observed_avdmanager_wear_device_profiles": observed_wear_device_profiles,
        "observed_avds_wear": parsed_avds["wear_avds"],
        "observed_avds_non_wear": parsed_avds["non_wear_avds"],
        "observed_avds_unknown": parsed_avds["unknown_avds"],
        "emulator_list_avds_raw": emulator_listed_avds,
        "adb_running_wear_emulators": running_wear_emulators,
        "adb_running_non_wear_emulators": running_non_wear_emulators,
        "adb_physical_devices_excluded": parsed_adb["physical_devices"],
        "safe_setup_commands_after_approval": safe_setup_commands,
    }

    if logs_dir:
        logs_dir.mkdir(parents=True, exist_ok=True)
        # Preserve separate verbatim tool output logs
        for filename, key, title in (
            ("sdkmanager-list.raw.log", "sdkmanager", "LIVE sdkmanager --list RAW OUTPUT"),
            ("avdmanager-list-device.raw.log", "avdmanager_devices", "LIVE avdmanager list device RAW OUTPUT"),
            ("avdmanager-list-avd.raw.log", "avdmanager_avds", "LIVE avdmanager list avd RAW OUTPUT"),
        ):
            tr = tool_runs[key]
            raw_doc = [
                "================================================================================",
                title,
                f"Command:     {' '.join(tr['command'])}",
                f"Tool Status: {tr['status']}",
                f"Exit Code:   {tr['returncode']}",
                f"Error Note:  {tr['error']}",
                "================================================================================",
                "--- STDOUT ---",
                tr["stdout"].rstrip(),
                "",
                "--- STDERR ---",
                tr["stderr"].rstrip(),
                "",
            ]
            (logs_dir / filename).write_text("\n".join(raw_doc), encoding="utf-8")

        java_proc = subprocess.run(["java", "-version"], capture_output=True, text=True, encoding="utf-8", check=False)
        java_ver = (java_proc.stderr or java_proc.stdout).strip()
        summary_lines = [
            "================================================================================",
            "AG-01 R03 LIVE ENVIRONMENT, TOOL HASHES & WEAR OS EMULATOR READINESS LOG",
            "================================================================================",
            f"OS Platform:                         {platform.platform()} ({platform.machine()})",
            f"Python Version:                      {sys.version.splitlines()[0]}",
            "Java Version:",
            java_ver,
            f"WFF Validator JAR:                   .aura-tools/wff-validator.jar (v1.7.0, SHA-256: {VALIDATOR_SHA256})",
            f"Memory Evaluator JAR:                .aura-tools/memory-footprint.jar (v1.5.1, SHA-256: {MEMORY_SHA256})",
            f"Android SDK Root:                    {info['sdk_root']}",
            f"Available Free Disk Space:           {info['disk_free_gib']} GiB",
            f"Wear Emulator Readiness Status:      {info['status']}",
            f"Readiness Reason:                    {info['reason']}",
            "",
            "--- Live Tool Execution Status ---",
            *[
                f"  * {name}: status={meta['status']}, rc={meta['returncode']}, error='{meta['error']}'"
                for name, meta in info["tool_runs"].items()
            ],
            "",
            "--- Live Observed Installed Wear OS Images (sdkmanager --list) ---",
            *(
                [f"  * {p['package_id']} | rev {p['version']} | {p['description']}" for p in observed_installed_wear]
                or ["  (none)"]
            ),
            "",
            "--- Live Observed Available Wear OS Images (sdkmanager --list, verbatim parsed rows) ---",
            *(
                [f"  * {p['package_id']} | rev {p['version']} | {p['description']}" for p in observed_available_wear]
                or ["  (none observed or sdkmanager failed)"]
            ),
            "",
            "--- Estimated Candidates Reconciled Against Live Catalog (Candidate != Live Fact) ---",
            *[
                f"  * {c['package_id']} | WFF#{c['target_wff_version']} | {c['priority']} | est={c['estimated_download_and_avd_gib']} | "
                f"installed={c['installed']} | in_live_catalog={c['observed_in_available_catalog']} | live_rev={c['observed_revision']}"
                for c in reconciled_candidates
            ],
            "",
            "--- Live Observed Wear OS AVD Device Profiles (avdmanager list device) ---",
            *(
                [f"  * {d['id']} (numeric_id={d['numeric_id']}, Name={d['name']}, OEM={d['oem']}, Tag={d['tag']})" for d in observed_wear_device_profiles]
                or ["  (none observed or avdmanager failed)"]
            ),
            "",
            "--- Live Configured AVDs Separated by Type (avdmanager list avd) ---",
            f"  * Wear OS AVDs ({len(parsed_avds['wear_avds'])}): {[a['name'] for a in parsed_avds['wear_avds']]}",
            f"  * Non-Wear Phone/Tablet AVDs ({len(parsed_avds['non_wear_avds'])}): "
            f"{[(a['name'], a['device'], a['tag_abi']) for a in parsed_avds['non_wear_avds']]}",
            f"  * Unknown AVDs ({len(parsed_avds['unknown_avds'])}): {[a['name'] for a in parsed_avds['unknown_avds']]}",
            "",
            "--- Live ADB Devices Separated by Type (adb devices -l) ---",
            f"  * Running Verified Wear Emulators ({len(running_wear_emulators)}): {running_wear_emulators}",
            f"  * Running Non-Wear Emulators ({len(running_non_wear_emulators)}): {running_non_wear_emulators}",
            f"  * Physical Devices (EXCLUDED FROM AUTOMATION) ({len(parsed_adb['physical_devices'])}): {parsed_adb['physical_devices']}",
            "",
            "--- Safe Setup Commands (ONLY AFTER EXPLICIT USER APPROVAL; NO --force) ---",
            *[f"  {cmd}" for cmd in safe_setup_commands],
            "",
        ]
        (logs_dir / "emulator-readiness-r03.log").write_text("\n".join(summary_lines), encoding="utf-8")
        print(f"[LOG] Wrote live R03 emulator readiness & raw SDK/AVD logs to {logs_dir}")

    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("all", "schema", "apk", "ablation", "emulator"), default="all")
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--logs-dir", type=Path, default=None, help="Directory to write raw verification logs (e.g. docs/evidence/AG-01/logs-r03)")
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
        print(
            f"[EMULATOR] status={summary['emulator']['status']} "
            f"wear_images={len(summary['emulator']['observed_sdkmanager_installed_wear_images'])} "
            f"wear_avds={[a['name'] for a in summary['emulator']['observed_avds_wear']]} "
            f"non_wear_avds={[a['name'] for a in summary['emulator']['observed_avds_non_wear']]}"
        )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[REPORT] Wrote verification JSON to {args.json_out}")


if __name__ == "__main__":
    main()
