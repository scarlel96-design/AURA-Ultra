"""Unit, schema, validator-strictness, emulator-inspection, and runtime-safety regression suite for AG-01 (R05)."""
import hashlib
import struct
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
import zlib
from pathlib import Path
from types import SimpleNamespace

AG01_DIR = Path(__file__).resolve().parent
ROOT = AG01_DIR.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(AG01_DIR))

from run_ag01_verification import (
    ABLATION_SPECS,
    ESTIMATED_WEAR_IMAGE_CANDIDATES,
    MEMORY_SHA256,
    NEGATIVE_SPECS,
    POC_SPECS,
    SEPARATED_NEGATIVE_SPECS,
    VALIDATOR_SHA256,
    determine_emulator_readiness,
    ensure_validator_jar,
    inspect_emulator_environment,
    parse_adb_devices,
    parse_avdmanager_avds,
    parse_avdmanager_devices,
    parse_sdkmanager_list,
    reconcile_wear_candidates,
    require_rejection,
    run_validator_utf8,
)
from verify_memory import get_jar as get_memory_jar
from verify_wff import require_pass
from wear_emulator_runtime import (
    PNG_SIGNATURE,
    RECOMMENDED_WEAR_AVD_PLANS,
    RecoveryFailureError,
    RuntimeVerificationIncompleteError,
    UnsafeTargetError,
    build_safe_runtime_verification_plan,
    build_safe_setup_commands,
    execute_runtime_verification,
    parse_power_and_display_state,
    validate_dedicated_wear_avd_name,
    validate_emulator_serial,
    validate_mp4_bytes,
    validate_png_bytes,
    validate_wear_avd_record,
    validate_wear_device_properties,
    verify_active_watchface_selected,
    verify_local_apk_before_install,
)

ALLOWED_INTERPOLATIONS = {"LINEAR", "EASE_IN", "EASE_OUT", "EASE_IN_OUT", "OVERSHOOT", "CUBIC_BEZIER"}
ALLOWED_ANGLE_DIRECTIONS = {"NONE", "CLOCKWISE", "COUNTER_CLOCKWISE"}
ALLOWED_REFERENCE_PARENTS = {
    "Scene", "Group", "PartDraw", "PartText", "PartImage", "PartAnimatedImage",
    "Arc", "Ellipse", "Line", "Rectangle", "RoundRectangle",
    "Fill", "Stroke", "WeightedStroke",
    "LinearGradient", "RadialGradient", "SweepGradient",
    "Font", "BitmapFont", "TextCircular", "InlineImage",
    "OutGlow", "Outline", "Shadow",
}
PROHIBITED_REFERENCE_PARENTS = {
    "DigitalClock", "TimeText", "AnalogClock", "HourHand", "MinuteHand", "SecondHand",
    "ComplicationSlot", "Complication",
}

EXPECTED_MAIN_VALIDATOR_SHA256 = "6ef308dbc306a9187b5b1f4997a662eb57e26ac3650cebbf2ab583cd38bb609e"
EXPECTED_MAIN_MEMORY_SHA256 = "1ec683365aee86627f0eb502b52fc71f71eff1872776edc5bc6ef7c7b37d28bc"

SAMPLE_SDKMANAGER_STDOUT = """Installed packages:
  Path                                                    | Version | Description                                | Location
  -------                                                 | ------- | -------                                    | -------
  platform-tools                                          | 36.0.2  | Android SDK Platform-Tools                 | platform-tools
  system-images;android-36.1;google_apis_playstore;x86_64 | 4       | Google Play Intel x86_64 Atom System Image | system-images\\android-36.1\\google_apis_playstore\\x86_64

Available Packages:
  Path                                            | Version | Description
  -------                                         | ------- | -------
  system-images;android-34;android-wear;x86_64    | 1       | Wear OS 5 Intel x86_64 Atom System Image
  system-images;android-36;android-wear-signed;x86_64 | 1   | Wear OS 6.0 Intel x86_64 Atom System Image (signed)
  system-images;android-37.0;android-wear-signed;x86_64 | 1 | Wear OS 7.0 Intel x86_64 Atom System Image (signed)
"""

SAMPLE_AVDMANAGER_DEVICES_STDOUT = """Available devices definitions:
id: 12 or "medium_phone"
    Name: Medium Phone
    OEM : Generic
---------
id: 59 or "wearos_large_round"
    Name: Wear OS Large Round
    OEM : Google
    Tag : android-wear
---------
id: 61 or "wearos_small_round"
    Name: Wear OS Small Round
    OEM : Google
    Tag : android-wear
"""

SAMPLE_AVDMANAGER_AVDS_PHONE_ONLY = """Available Android Virtual Devices:
    Name: Medium_Phone_API_36.1
  Device: medium_phone (Generic)
    Path: C:\\Users\\test\\.android\\avd\\Medium_Phone.avd
  Target: Google Play (Google Inc.)
          Based on: Android API 0 Tag/ABI: google_apis_playstore/x86_64
    Skin: 1080x2400
"""

SAMPLE_AVDMANAGER_AVDS_MIXED = SAMPLE_AVDMANAGER_AVDS_PHONE_ONLY + """---------
    Name: aura_wear36_round
  Device: wearos_large_round (Google)
    Path: C:\\Users\\test\\.android\\avd\\aura_wear36_round.avd
  Target: Wear OS 6.0 (Google Inc.)
          Based on: Android 16.0 Tag/ABI: android-wear-signed/x86_64
    Skin: 454x454
"""


def _png_chunk(chunk_type, chunk_data):
    crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
    return struct.pack(">I", len(chunk_data)) + chunk_type + chunk_data + struct.pack(">I", crc)


def _build_valid_png_bytes(width=4, height=4):
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    raw_scanlines = b"".join(b"\x00" + (b"\x10\x20\x30\xff" * width) for _ in range(height))
    idat_data = zlib.compress(raw_scanlines)
    return PNG_SIGNATURE + _png_chunk(b"IHDR", ihdr_data) + _png_chunk(b"IDAT", idat_data) + _png_chunk(b"IEND", b"")


def _build_synthetic_resource_only_apk(path, watchface_xml="<WatchFace width=\"450\" height=\"450\"><Scene/></WatchFace>", extra_entry=None):
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("AndroidManifest.xml", "<manifest/>")
        zf.writestr("resources.arsc", "arsc")
        zf.writestr("res/drawable-nodpi-v4/preview.png", _build_valid_png_bytes(4, 4))
        zf.writestr("res/xml/watch_face_info.xml", "<WatchFaceInfo/>")
        zf.writestr("res/raw/watchface.xml", watchface_xml.encode("utf-8"))
        if extra_entry:
            zf.writestr(extra_entry[0], extra_entry[1])


def _valid_manifest_xml(pkg="io.github.scarlel96.aura.watchface.wff4", min_sdk=36, wff_version=4, has_code="false"):
    return f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="{pkg}">
    <uses-sdk android:minSdkVersion="{min_sdk}" android:targetSdkVersion="37" />
    <application android:hasCode="{has_code}">
        <property android:name="com.google.wear.watchface.format.version" android:value="{wff_version}" />
    </application>
</manifest>"""


class Ag01PoCStructureTests(unittest.TestCase):
    def test_official_tool_pins_match_latest_main(self):
        self.assertEqual(EXPECTED_MAIN_VALIDATOR_SHA256, VALIDATOR_SHA256)
        self.assertEqual(EXPECTED_MAIN_MEMORY_SHA256, MEMORY_SHA256)
        v_jar = ensure_validator_jar()
        m_jar = get_memory_jar()
        self.assertEqual(EXPECTED_MAIN_VALIDATOR_SHA256, hashlib.sha256(v_jar.read_bytes()).hexdigest())
        self.assertEqual(EXPECTED_MAIN_MEMORY_SHA256, hashlib.sha256(m_jar.read_bytes()).hexdigest())

    def test_all_poc_files_exist_and_respect_canvas_invariants(self):
        self.assertEqual(6, len(POC_SPECS))
        for spec in POC_SPECS:
            with self.subTest(poc=spec["id"]):
                self.assertTrue(spec["path"].is_file(), f"Missing {spec['path']}")
                root = ET.parse(spec["path"]).getroot()
                self.assertEqual("WatchFace", root.tag)
                self.assertEqual(("450", "450"), (root.get("width"), root.get("height")))
                scenes = root.findall("Scene")
                self.assertEqual(1, len(scenes))
                time_texts = root.findall(".//TimeText")
                self.assertGreaterEqual(len(time_texts), 1)
                for tt in time_texts:
                    self.assertEqual("SYNC_TO_DEVICE", tt.get("hourFormat"))
                ambient_zero = [
                    v for v in root.findall(".//Group/Variant")
                    if v.get("mode") == "AMBIENT" and v.get("target") == "alpha" and v.get("value") == "0"
                ]
                self.assertGreaterEqual(len(ambient_zero), 1)

    def test_single_clock_continuity_object_in_aod_pocs(self):
        for poc_id in ("poc_wff2_static_aod", "poc_wff3_part_blend_aod", "poc_wff4_continuity", "poc_wff4_reference_complication", "poc_wff5_blend_features"):
            spec = next(s for s in POC_SPECS if s["id"] == poc_id)
            with self.subTest(poc=poc_id):
                root = ET.parse(spec["path"]).getroot()
                clocks = root.findall(".//DigitalClock")
                self.assertEqual(1, len(clocks))
                time_texts = clocks[0].findall("TimeText")
                self.assertEqual(1, len(time_texts))
                targets = {v.get("target") for v in clocks[0].findall("Variant") if v.get("mode") == "AMBIENT"}
                self.assertTrue({"y", "scaleX", "scaleY"}.issubset(targets))

    def test_wff4_variant_transition_window_and_interpolations(self):
        spec = next(s for s in POC_SPECS if s["id"] == "poc_wff4_continuity")
        root = ET.parse(spec["path"]).getroot()
        seen_interpolations = set()
        seen_angle_directions = set()
        variants = root.findall(".//Variant")
        self.assertGreaterEqual(len(variants), 10)
        for v in variants:
            self.assertEqual("AMBIENT", v.get("mode"))
            duration = float(v.get("duration", "1.0"))
            start_offset = float(v.get("startOffset", "0.0"))
            self.assertGreaterEqual(duration, 0.0)
            self.assertLessEqual(duration, 1.0)
            self.assertGreaterEqual(start_offset, 0.0)
            self.assertLessEqual(start_offset, 1.0)
            self.assertLessEqual(round(start_offset + duration, 6), 1.0)
            interp = v.get("interpolation", "LINEAR")
            self.assertIn(interp, ALLOWED_INTERPOLATIONS)
            seen_interpolations.add(interp)
            if "controls" in v.attrib:
                parts = [float(x) for x in v.get("controls").split()]
                self.assertEqual(4, len(parts))
            if "angleDirection" in v.attrib:
                self.assertIn(v.get("angleDirection"), ALLOWED_ANGLE_DIRECTIONS)
                seen_angle_directions.add(v.get("angleDirection"))
        self.assertEqual(ALLOWED_INTERPOLATIONS, seen_interpolations)
        self.assertIn("CLOCKWISE", seen_angle_directions)

    def test_wff4_reference_unique_names_allowed_parents_and_multi_consumers(self):
        spec = next(s for s in POC_SPECS if s["id"] == "poc_wff4_reference_complication")
        xml_text = spec["path"].read_text(encoding="utf-8")
        root = ET.parse(spec["path"]).getroot()
        parent_map = {child: parent for parent in root.iter() for child in parent}
        references = root.findall(".//Reference")
        self.assertGreaterEqual(len(references), 5)
        names = []
        for ref in references:
            name = ref.get("name")
            source = ref.get("source")
            self.assertTrue(name and name.strip())
            self.assertTrue(source and source.strip())
            self.assertIsNotNone(ref.get("defaultValue"))
            parent = parent_map[ref]
            self.assertIn(parent.tag, ALLOWED_REFERENCE_PARENTS)
            self.assertNotIn(parent.tag, PROHIBITED_REFERENCE_PARENTS)
            for tr in parent.findall("Transform"):
                self.assertNotIn(f"[REFERENCE.{name}]", tr.get("value", ""))
            names.append(name)
        self.assertEqual(len(names), len(set(names)))
        for name in names:
            self.assertIn(f"[REFERENCE.{name}]", xml_text)
        self.assertIn("--", xml_text)

    def test_wff4_motion_triggers_gyro_and_per_digit_time_formats(self):
        spec = next(s for s in POC_SPECS if s["id"] == "poc_wff4_motion_triggers")
        root = ET.parse(spec["path"]).getroot()
        gyros = root.findall(".//Gyro")
        self.assertEqual(1, len(gyros))
        for attr in ("x", "y", "angle", "alpha"):
            self.assertIn("ACCELEROMETER_", gyros[0].get(attr, ""))
        formats = [tt.get("format") for tt in root.findall(".//TimeText")]
        self.assertEqual(["hh_10", "hh_1", "mm_10", "mm_1"], formats)
        animations = root.findall(".//Transform/Animation")
        self.assertGreaterEqual(len(animations), 4)

    def test_wff5_group_and_complication_slot_blend_modes(self):
        spec = next(s for s in POC_SPECS if s["id"] == "poc_wff5_blend_features")
        root = ET.parse(spec["path"]).getroot()
        blended_groups = [g for g in root.findall(".//Group") if g.get("blendMode")]
        self.assertGreaterEqual(len(blended_groups), 2)
        blended_slots = [c for c in root.findall(".//ComplicationSlot") if c.get("blendMode")]
        self.assertEqual(1, len(blended_slots))
        joined_strokes = [s for s in root.findall(".//Stroke") if s.get("join")]
        self.assertGreaterEqual(len(joined_strokes), 2)
        min_fonts = [f for f in root.findall(".//Font") if f.get("minSize")]
        self.assertGreaterEqual(len(min_fonts), 3)

    def test_controlled_ablation_fixtures_isolate_clock_count_and_aod_parttext(self):
        def canonical_tree(elem):
            return (
                elem.tag,
                sorted(elem.attrib.items()),
                (elem.text or "").strip(),
                [canonical_tree(c) for c in elem],
            )

        self.assertEqual(4, len(ABLATION_SPECS))
        baseline = ET.parse(next(s for s in POC_SPECS if s["id"] == "poc_wff4_motion_triggers")["path"]).getroot()
        baseline_active_tree = canonical_tree(baseline.find(".//Group[@name='ActiveDecoration']"))

        for spec in ABLATION_SPECS:
            with self.subTest(ablation=spec["id"]):
                self.assertTrue(spec["path"].is_file(), f"Missing {spec['path']}")
                root = ET.parse(spec["path"]).getroot()
                active_group = root.find(".//Group[@name='ActiveDecoration']")
                self.assertIsNotNone(active_group)
                self.assertEqual(baseline_active_tree, canonical_tree(active_group))

                fluid = root.find(".//Group[@name='FluidClockContainer']")
                self.assertIsNotNone(fluid)
                clocks = fluid.findall(".//DigitalClock")
                self.assertEqual(spec["digital_clocks"], len(clocks))

                aod_visible_parts = []
                for child in fluid.iter():
                    if child.tag.startswith("Part"):
                        hidden = any(
                            v.get("mode") == "AMBIENT" and v.get("target") == "alpha" and v.get("value") == "0"
                            for v in child.findall("Variant")
                        )
                        if not hidden:
                            aod_visible_parts.append(child)
                self.assertEqual(spec["aod_visible_part_nodes"], len(aod_visible_parts))

    def test_separated_single_fault_negative_fixtures_are_mutually_isolated(self):
        dur_spec = next(s for s in SEPARATED_NEGATIVE_SPECS if s["id"] == "neg_wff4_variant_duration_out_of_range")
        ref_spec = next(s for s in SEPARATED_NEGATIVE_SPECS if s["id"] == "neg_wff4_reference_invalid_parent")

        dur_root = ET.parse(dur_spec["path"]).getroot()
        self.assertEqual(0, len(dur_root.findall(".//Reference")))
        self.assertTrue(any(float(v.get("duration", "0")) > 1.0 for v in dur_root.findall(".//Variant")))

        ref_root = ET.parse(ref_spec["path"]).getroot()
        for v in ref_root.findall(".//Variant"):
            self.assertLessEqual(float(v.get("startOffset", "0")) + float(v.get("duration", "1")), 1.0)
        parent_map = {child: parent for parent in ref_root.iter() for child in parent}
        refs = ref_root.findall(".//Reference")
        self.assertEqual(1, len(refs))
        self.assertIn(parent_map[refs[0]].tag, PROHIBITED_REFERENCE_PARENTS)

    def test_detects_variant_window_overflow_and_invalid_reference_parent(self):
        neg7 = next(s for s in NEGATIVE_SPECS if s["id"] == "neg_wff4_invalid_variant_and_reference_parent")
        root = ET.parse(neg7["path"]).getroot()
        variants = root.findall(".//Variant")
        self.assertTrue(any(float(v.get("startOffset", "0")) + float(v.get("duration", "1")) > 1.0 for v in variants))
        parent_map = {child: parent for parent in root.iter() for child in parent}
        refs = root.findall(".//Reference")
        self.assertTrue(any(parent_map[r].tag in PROHIBITED_REFERENCE_PARENTS for r in refs))


class Ag01StrictValidatorRejectionTests(unittest.TestCase):
    """AG01-AUD-02 regression tests: tool errors, wrong paths/versions, and loose strings must never PASS rejection."""

    def setUp(self):
        self.face = POC_SPECS[0]["path"].resolve()
        self.other_face = POC_SPECS[1]["path"].resolve()
        self.banner = "INFO: WFF Validation Application Version 1.7.0. Maximum Supported Format Version #5"

    def test_valid_explicit_rejection_passes(self):
        output = "\n".join([
            self.banner,
            "SEVERE: [Line 9:Column 105]: cvc-complex-type.3.2.2: Attribute 'blendMode' is not allowed to appear in element 'PartDraw'.",
            f"INFO: ❌  FAILED : {self.face} is NOT valid against watch face format version #2",
        ])
        messages = require_rejection(0, output, self.face, 2, expected_error="blendMode")
        self.assertEqual(1, len(messages))

    def test_rejects_nonzero_tool_crash_even_if_error_substring_present(self):
        crash_output = "Error: Unable to access jarfile .aura-tools/wff-validator.jar (blendMode FAILED)"
        with self.assertRaises(ValueError):
            require_rejection(1, crash_output, self.face, 2, expected_error="blendMode")

    def test_rejects_missing_banner_or_passed_verdict(self):
        no_banner = "\n".join([
            "SEVERE: [Line 9:Column 10]: blendMode invalid",
            f"INFO: ❌  FAILED : {self.face} is NOT valid against watch face format version #2",
        ])
        with self.assertRaises(ValueError):
            require_rejection(0, no_banner, self.face, 2, expected_error="blendMode")

        passed = "\n".join([
            self.banner,
            f"INFO: ✅  PASSED : {self.face} is valid against watch face format version #2",
        ])
        with self.assertRaises(ValueError):
            require_rejection(0, passed, self.face, 2)

    def test_rejects_wrong_file_path_or_wrong_wff_version(self):
        wrong_path = "\n".join([
            self.banner,
            "SEVERE: [Line 9:Column 10]: Attribute 'blendMode' is not allowed",
            f"INFO: ❌  FAILED : {self.other_face} is NOT valid against watch face format version #2",
        ])
        with self.assertRaises(ValueError):
            require_rejection(0, wrong_path, self.face, 2, expected_error="blendMode")

        wrong_version = "\n".join([
            self.banner,
            "SEVERE: [Line 9:Column 10]: Attribute 'blendMode' is not allowed",
            f"INFO: ❌  FAILED : {self.face} is NOT valid against watch face format version #3",
        ])
        with self.assertRaises(ValueError):
            require_rejection(0, wrong_version, self.face, 2, expected_error="blendMode")

    def test_rejects_missing_severe_or_expected_error_outside_severe_line(self):
        no_severe = "\n".join([
            self.banner,
            f"INFO: ❌  FAILED : {self.face} is NOT valid against watch face format version #2",
        ])
        with self.assertRaises(ValueError):
            require_rejection(0, no_severe, self.face, 2)

        error_only_in_info = "\n".join([
            self.banner,
            "INFO: Note mentioning blendMode outside schema SEVERE diagnostic",
            "SEVERE: [Line 5:Column 2]: unrelated syntax error",
            f"INFO: ❌  FAILED : {self.face} is NOT valid against watch face format version #2",
        ])
        with self.assertRaises(ValueError):
            require_rejection(0, error_only_in_info, self.face, 2, expected_error="blendMode")


class Ag01EmulatorInspectionAndSafetyTests(unittest.TestCase):
    """AG01-AUD-01, AG01-AUD-04 & AG-01-R05 Runtime Safety regression tests."""

    def test_parsers_extract_live_sdk_devices_avds_and_separate_phone_from_wear(self):
        parsed_sdk = parse_sdkmanager_list(SAMPLE_SDKMANAGER_STDOUT)
        self.assertEqual(2, len(parsed_sdk["installed"]))
        self.assertEqual(3, len(parsed_sdk["available"]))

        reconciled = reconcile_wear_candidates(ESTIMATED_WEAR_IMAGE_CANDIDATES, parsed_sdk["installed"], parsed_sdk["available"])
        by_id = {c["package_id"]: c for c in reconciled}
        self.assertTrue(by_id["system-images;android-36;android-wear-signed;x86_64"]["observed_in_available_catalog"])
        self.assertFalse(by_id["system-images;android-36;android-wear-signed;x86_64"]["installed"])
        self.assertFalse(by_id["system-images;android-35-ext15;android-wear;x86_64"]["observed_in_available_catalog"])
        self.assertEqual("NOT_OBSERVED", by_id["system-images;android-35-ext15;android-wear;x86_64"]["observed_revision"])

        devices = parse_avdmanager_devices(SAMPLE_AVDMANAGER_DEVICES_STDOUT)
        self.assertEqual(3, len(devices))
        wear_devs = [d for d in devices if "android-wear" in d["tag"]]
        self.assertEqual(["wearos_large_round", "wearos_small_round"], [d["id"] for d in wear_devs])

        phone_only = parse_avdmanager_avds(SAMPLE_AVDMANAGER_AVDS_PHONE_ONLY)
        self.assertEqual(0, len(phone_only["wear_avds"]))
        self.assertEqual(["Medium_Phone_API_36.1"], [a["name"] for a in phone_only["non_wear_avds"]])

        mixed = parse_avdmanager_avds(SAMPLE_AVDMANAGER_AVDS_MIXED)
        self.assertEqual(["aura_wear36_round"], [a["name"] for a in mixed["wear_avds"]])
        self.assertEqual(["Medium_Phone_API_36.1"], [a["name"] for a in mixed["non_wear_avds"]])

        adb = parse_adb_devices("List of devices attached\nR5CX1234567 device model:SM_L705N\nemulator-5554 device product:sdk_gwear\n")
        self.assertEqual(["emulator-5554"], [d["serial"] for d in adb["emulators"]])
        self.assertEqual(["R5CX1234567"], [d["serial"] for d in adb["physical_devices"]])

    def test_missing_or_failed_or_empty_sdk_tools_return_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            info_missing = inspect_emulator_environment(sdk_root=Path(tmp))
            self.assertEqual("UNKNOWN", info_missing["status"])

        with tempfile.TemporaryDirectory() as tmp:
            sdk = Path(tmp)
            for rel in (
                "cmdline-tools/latest/bin/sdkmanager.bat",
                "cmdline-tools/latest/bin/sdkmanager",
                "cmdline-tools/latest/bin/avdmanager.bat",
                "cmdline-tools/latest/bin/avdmanager",
                "emulator/emulator.exe",
                "emulator/emulator",
                "platform-tools/adb.exe",
                "platform-tools/adb",
            ):
                p = sdk / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("stub", encoding="utf-8")

            def runner_sm_error(cmd, timeout=60):
                if "sdkmanager" in cmd[0]:
                    return {"command": cmd, "status": "ERROR", "returncode": 1, "stdout": "", "stderr": "network failed", "error": "exit 1"}
                return {"command": cmd, "status": "OK", "returncode": 0, "stdout": "List of devices attached\n", "stderr": "", "error": ""}

            res_err = inspect_emulator_environment(sdk_root=sdk, runner=runner_sm_error)
            self.assertEqual("UNKNOWN", res_err["status"])
            self.assertEqual([], res_err["observed_sdkmanager_available_wear_images"])

            def runner_avd_empty(cmd, timeout=60):
                if "sdkmanager" in cmd[0]:
                    return {"command": cmd, "status": "OK", "returncode": 0, "stdout": SAMPLE_SDKMANAGER_STDOUT, "stderr": "", "error": ""}
                if "avdmanager" in cmd[0]:
                    return {"command": cmd, "status": "OK", "returncode": 0, "stdout": "   \n", "stderr": "", "error": ""}
                return {"command": cmd, "status": "OK", "returncode": 0, "stdout": "List of devices attached\n", "stderr": "", "error": ""}

            res_empty = inspect_emulator_environment(sdk_root=sdk, runner=runner_avd_empty)
            self.assertEqual("UNKNOWN", res_empty["status"])

            def runner_phone_and_physical(cmd, timeout=60):
                if "sdkmanager" in cmd[0]:
                    return {"command": cmd, "status": "OK", "returncode": 0, "stdout": SAMPLE_SDKMANAGER_STDOUT, "stderr": "", "error": ""}
                if "avdmanager" in cmd[0] and "device" in cmd:
                    return {"command": cmd, "status": "OK", "returncode": 0, "stdout": SAMPLE_AVDMANAGER_DEVICES_STDOUT, "stderr": "", "error": ""}
                if "avdmanager" in cmd[0] and "avd" in cmd:
                    return {"command": cmd, "status": "OK", "returncode": 0, "stdout": SAMPLE_AVDMANAGER_AVDS_PHONE_ONLY, "stderr": "", "error": ""}
                if "emulator" in cmd[0]:
                    return {"command": cmd, "status": "OK", "returncode": 0, "stdout": "Medium_Phone_API_36.1\n", "stderr": "", "error": ""}
                if "adb" in cmd[0]:
                    return {"command": cmd, "status": "OK", "returncode": 0, "stdout": "List of devices attached\nR5CX9999999 device model:GalaxyWatch\n", "stderr": "", "error": ""}
                return {"command": cmd, "status": "OK", "returncode": 0, "stdout": "", "stderr": "", "error": ""}

            res_not_run = inspect_emulator_environment(sdk_root=sdk, runner=runner_phone_and_physical)
            self.assertEqual("NOT RUN", res_not_run["status"])
            self.assertEqual(0, len(res_not_run["observed_avds_wear"]))
            self.assertEqual(1, len(res_not_run["observed_avds_non_wear"]))
            self.assertEqual(1, len(res_not_run["adb_physical_devices_excluded"]))

    def test_installed_wear_image_alone_without_wear_avd_is_not_ready(self):
        ok_runs = {k: {"status": "OK", "returncode": 0, "error": ""} for k in ("sdkmanager", "avdmanager_devices", "avdmanager_avds", "emulator", "adb")}
        status_no_avd, _ = determine_emulator_readiness(
            tool_runs=ok_runs,
            installed_wear_images=[{"package_id": "system-images;android-36;android-wear-signed;x86_64"}],
            wear_avds=[],
            running_wear_emulators=[],
        )
        self.assertEqual("NOT RUN", status_no_avd)

        status_ready, _ = determine_emulator_readiness(
            tool_runs=ok_runs,
            installed_wear_images=[{"package_id": "system-images;android-36;android-wear-signed;x86_64"}],
            wear_avds=[{"name": "aura_wear36_round"}],
            running_wear_emulators=[],
        )
        self.assertEqual("READY", status_ready)

    def test_aud04_four_reproduced_false_positives_are_rejected(self):
        target_pkg = "io.github.scarlel96.aura.watchface.wff4"

        dump_inactive_ref = (
            "mCurrentUserId=0\n"
            "  WallpaperData 0 userId=0\n"
            "    mWallpaperComponent=ComponentInfo{com.example.default/.Face}\n"
            f"    previousPackage={target_pkg}\n"
        )
        res1 = verify_active_watchface_selected(dump_inactive_ref, target_pkg)
        self.assertFalse(res1["selected"])
        self.assertEqual("NOT_SELECTED", res1["status"])
        self.assertEqual("com.example.default", res1["active_package"])

        dump_suffix_collision = f"  mWallpaperComponent=ComponentInfo{{{target_pkg}.other/.Face}}\n"
        res2 = verify_active_watchface_selected(dump_suffix_collision, target_pkg)
        self.assertFalse(res2["selected"])
        self.assertEqual("NOT_SELECTED", res2["status"])
        self.assertEqual(f"{target_pkg}.other", res2["active_package"])

        state3 = parse_power_and_display_state("mWakefulness=Awake\n")
        self.assertEqual("UNKNOWN", state3["display_state"])
        self.assertEqual("UNKNOWN", state3["status"])
        self.assertFalse(state3["is_active"])
        self.assertFalse(state3["is_aod"])

        state4 = parse_power_and_display_state("mWakefulness=Dozing\nDisplay Power: state=OFF\n")
        self.assertEqual("OFF", state4["display_state"])
        self.assertEqual("SCREEN_OFF", state4["status"])
        self.assertFalse(state4["is_active"])
        self.assertFalse(state4["is_aod"])

        dump_unknown_host = "  mWallpaperComponent=ComponentInfo{com.google.wear.watchface.runtime/.DwfHostService}\n"
        res_host_unknown = verify_active_watchface_selected(dump_unknown_host, target_pkg)
        self.assertFalse(res_host_unknown["selected"])
        self.assertEqual("UNKNOWN", res_host_unknown["status"])

        dump_exact = f"  mWallpaperComponent=ComponentInfo{{{target_pkg}/.WatchFace}}\n"
        res_exact = verify_active_watchface_selected(dump_exact, target_pkg)
        self.assertTrue(res_exact["selected"])
        self.assertEqual("SELECTED", res_exact["status"])

        dump_host_bound = (
            "  mWallpaperComponent=ComponentInfo{com.google.wear.watchface.runtime/.DwfHostService}\n"
            f"  boundWatchFacePackage={target_pkg}\n"
        )
        res_host_bound = verify_active_watchface_selected(dump_host_bound, target_pkg)
        self.assertTrue(res_host_bound["selected"])
        self.assertEqual("SELECTED", res_host_bound["status"])

        awake_on = parse_power_and_display_state("mWakefulness=Awake\nDisplay Power: state=ON\n")
        self.assertEqual("ACTIVE", awake_on["status"])
        self.assertTrue(awake_on["is_active"])
        self.assertFalse(awake_on["is_aod"])

        doze_on = parse_power_and_display_state("mWakefulness=Dozing\nDisplay Power: state=DOZE_SUSPEND\n")
        self.assertEqual("AOD", doze_on["status"])
        self.assertFalse(doze_on["is_active"])
        self.assertTrue(doze_on["is_aod"])

    def test_r05_missing_current_user_binding_never_falls_back_to_other_user(self):
        """AG-01-R05: when current user has no wallpaper binding, NEVER fall back to another user's binding."""
        target_pkg = "io.github.scarlel96.aura.watchface.wff4"

        # Case 1: mCurrentUserId=0, but ONLY userId=10 has target_pkg -> MUST be UNKNOWN, selected=False
        dump_other_user_only = (
            "mCurrentUserId=0\n"
            "  WallpaperData 10 userId=10\n"
            f"    mWallpaperComponent=ComponentInfo{{{target_pkg}/.WatchFace}}\n"
        )
        res = verify_active_watchface_selected(dump_other_user_only, target_pkg)
        self.assertFalse(res["selected"])
        self.assertEqual("UNKNOWN", res["status"])

        # Case 2: User-scoped binding present WITHOUT mCurrentUserId -> MUST be UNKNOWN, selected=False
        dump_no_current_user = (
            "  WallpaperData 10 userId=10\n"
            f"    mWallpaperComponent=ComponentInfo{{{target_pkg}/.WatchFace}}\n"
        )
        res_no_cur = verify_active_watchface_selected(dump_no_current_user, target_pkg)
        self.assertFalse(res_no_cur["selected"])
        self.assertEqual("UNKNOWN", res_no_cur["status"])

        # Case 3: Conflicting mCurrentUserId values -> MUST be UNKNOWN, selected=False
        dump_conflict_user = (
            "mCurrentUserId=0\n"
            "mCurrentUserId=10\n"
            "  WallpaperData 0 userId=0\n"
            f"    mWallpaperComponent=ComponentInfo{{{target_pkg}/.WatchFace}}\n"
        )
        res_conflict = verify_active_watchface_selected(dump_conflict_user, target_pkg)
        self.assertFalse(res_conflict["selected"])
        self.assertEqual("UNKNOWN", res_conflict["status"])

        # Case 4: Both user 0 (other face) and user 10 (target face) with mCurrentUserId=0 -> MUST select user 0 (NOT_SELECTED)
        dump_multi_users = (
            "mCurrentUserId=0\n"
            "  WallpaperData 0 userId=0\n"
            "    mWallpaperComponent=ComponentInfo{com.example.other/.Face}\n"
            "  WallpaperData 10 userId=10\n"
            f"    mWallpaperComponent=ComponentInfo{{{target_pkg}/.WatchFace}}\n"
        )
        res_multi = verify_active_watchface_selected(dump_multi_users, target_pkg)
        self.assertFalse(res_multi["selected"])
        self.assertEqual("NOT_SELECTED", res_multi["status"])
        self.assertEqual("com.example.other", res_multi["active_package"])

        # Case 5 (G5 self-review): Mixed unscoped binding + user-scoped header -> MUST be UNKNOWN
        dump_mixed_scope = (
            "mCurrentUserId=0\n"
            f"  mWallpaperComponent=ComponentInfo{{{target_pkg}/.WatchFace}}\n"
            "  WallpaperData 10 userId=10\n"
            "    mWallpaperComponent=ComponentInfo{com.example.other/.Face}\n"
        )
        res_mixed = verify_active_watchface_selected(dump_mixed_scope, target_pkg)
        self.assertFalse(res_mixed["selected"])
        self.assertEqual("UNKNOWN", res_mixed["status"])

        # Case 6 (G5 self-review): Non-primary mCurrentUserId=10 with unscoped binding -> MUST be UNKNOWN
        dump_non_primary_unscoped = (
            "mCurrentUserId=10\n"
            f"  mWallpaperComponent=ComponentInfo{{{target_pkg}/.WatchFace}}\n"
        )
        res_non_primary = verify_active_watchface_selected(dump_non_primary_unscoped, target_pkg)
        self.assertFalse(res_non_primary["selected"])
        self.assertEqual("UNKNOWN", res_non_primary["status"])

    def test_r05_multi_display_and_conflicting_power_states_return_unknown(self):
        """AG-01-R05: conflicting power vs display, conflicting multi-display, conflicting wakefulness, or incoherent pairs -> UNKNOWN."""
        # 1. dumpsys power says ON while dumpsys display says OFF -> CONFLICT -> UNKNOWN
        c1 = parse_power_and_display_state(
            "mWakefulness=Awake\nDisplay Power: state=ON\n",
            "mScreenState=OFF\n",
        )
        self.assertEqual("UNKNOWN", c1["status"])
        self.assertFalse(c1["is_active"])
        self.assertFalse(c1["is_aod"])

        # 2. Multi-display dump with Display Id=0 ON and Display Id=1 DOZE -> CONFLICT -> UNKNOWN
        c2 = parse_power_and_display_state(
            "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\nDisplay Id=1\nDisplay Power: state=DOZE\n",
        )
        self.assertEqual("UNKNOWN", c2["status"])
        self.assertFalse(c2["is_active"])
        self.assertFalse(c2["is_aod"])

        # 3. Conflicting mWakefulness values (Awake and Dozing) -> UNKNOWN
        c3 = parse_power_and_display_state(
            "mWakefulness=Awake\nmWakefulness=Dozing\nDisplay Power: state=ON\n",
        )
        self.assertEqual("UNKNOWN", c3["status"])
        self.assertFalse(c3["is_active"])
        self.assertFalse(c3["is_aod"])

        # 4. Incoherent pair: Awake + DOZE -> UNKNOWN
        c4 = parse_power_and_display_state("mWakefulness=Awake\nDisplay Power: state=DOZE\n")
        self.assertEqual("UNKNOWN", c4["status"])
        self.assertFalse(c4["is_active"])
        self.assertFalse(c4["is_aod"])

        # 5. Incoherent pair: Dozing + ON -> UNKNOWN
        c5 = parse_power_and_display_state("mWakefulness=Dozing\nDisplay Power: state=ON\n")
        self.assertEqual("UNKNOWN", c5["status"])
        self.assertFalse(c5["is_active"])
        self.assertFalse(c5["is_aod"])

        # 6. Consistent power ON + display ON -> ACTIVE
        ok = parse_power_and_display_state(
            "mWakefulness=Awake\nDisplay Power: state=ON\n",
            "Display State: ON\nmScreenState=ON\nDisplayDeviceInfo{\"Built-in\": state ON}\n",
        )
        self.assertEqual("ACTIVE", ok["status"])
        self.assertTrue(ok["is_active"])

        # 7 (G5 self-review): Multiple Display Ids (0 and 1) with only 1 display state reported -> INCOMPLETE_MULTI_DISPLAY -> UNKNOWN
        c7 = parse_power_and_display_state(
            "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\nDisplay Id=1\n",
        )
        self.assertEqual("UNKNOWN", c7["status"])
        self.assertFalse(c7["is_active"])

        # 8 (G5 self-review): mGlobalDisplayState=DOZE conflicting with Display Power: state=ON -> UNKNOWN
        c8 = parse_power_and_display_state(
            "mWakefulness=Awake\nDisplay Power: state=ON\n",
            "mGlobalDisplayState=DOZE\n",
        )
        self.assertEqual("UNKNOWN", c8["status"])
        self.assertFalse(c8["is_active"])

    def test_r05_png_full_structure_and_integrity_validation(self):
        """AG-01-R05: validate_png_bytes must reject fake 4-byte headers, truncated chunks, CRC corruption, missing IEND, bad IDAT, and trailing garbage."""
        good_png = _build_valid_png_bytes(8, 8)
        meta = validate_png_bytes(good_png)
        self.assertEqual((8, 8), (meta["width"], meta["height"]))
        self.assertEqual(3, meta["chunk_count"])

        # 1. Fake 4-byte magic only (previously passed!) -> MUST FAIL
        with self.assertRaises(RuntimeError):
            validate_png_bytes(b"\x89PNG" + b"\x00" * 128)

        # 2. Truncated PNG missing IEND -> MUST FAIL
        with self.assertRaises(RuntimeError):
            validate_png_bytes(good_png[:-12])

        # 3. Corrupted CRC-32 in IHDR -> MUST FAIL
        bad_crc = bytearray(good_png)
        bad_crc[29] ^= 0xFF
        with self.assertRaises(RuntimeError):
            validate_png_bytes(bytes(bad_crc))

        # 4. Trailing garbage after IEND -> MUST FAIL
        with self.assertRaises(RuntimeError):
            validate_png_bytes(good_png + b"GARBAGE")

        # 5. Corrupt IDAT zlib stream (valid CRC on corrupt compressed payload) -> MUST FAIL
        ihdr = _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 6, 0, 0, 0))
        bad_idat = _png_chunk(b"IDAT", b"not-valid-zlib-stream")
        iend = _png_chunk(b"IEND", b"")
        with self.assertRaises(RuntimeError):
            validate_png_bytes(PNG_SIGNATURE + ihdr + bad_idat + iend)

        # 6. Valid zlib stream with truncated uncompressed scanline length -> MUST FAIL
        short_idat = _png_chunk(b"IDAT", zlib.compress(b"\x00\x01\x02"))
        with self.assertRaises(RuntimeError):
            validate_png_bytes(PNG_SIGNATURE + ihdr + short_idat + iend)

        # 7. Zero-dimension IHDR -> MUST FAIL
        zero_ihdr = _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 0, 4, 8, 6, 0, 0, 0))
        with self.assertRaises(RuntimeError):
            validate_png_bytes(PNG_SIGNATURE + zero_ihdr + _png_chunk(b"IDAT", zlib.compress(b"")) + iend)

        # 8 (G5 self-review): Invalid scanline filter byte (> 4) with exact decompressed length -> MUST FAIL
        bad_filter_scanlines = b"".join(b"\x09" + (b"\x10\x20\x30\xff" * 4) for _ in range(4))
        with self.assertRaises(RuntimeError):
            validate_png_bytes(PNG_SIGNATURE + ihdr + _png_chunk(b"IDAT", zlib.compress(bad_filter_scanlines)) + iend)

        # 9 (G5 self-review): Indexed-color (color_type=3) missing PLTE chunk before IDAT -> MUST FAIL
        idx_ihdr = _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 3, 0, 0, 0))
        idx_scanlines = b"".join(b"\x00" + (b"\x01" * 4) for _ in range(4))
        with self.assertRaises(RuntimeError):
            validate_png_bytes(PNG_SIGNATURE + idx_ihdr + _png_chunk(b"IDAT", zlib.compress(idx_scanlines)) + iend)

    def test_runtime_safety_guards_and_preinstall_apk_checks(self):
        with self.assertRaises(UnsafeTargetError):
            validate_emulator_serial("R5CX1234567")
        with self.assertRaises(UnsafeTargetError):
            validate_emulator_serial("")
        self.assertEqual("emulator-5554", validate_emulator_serial("emulator-5554"))

        with self.assertRaises(UnsafeTargetError):
            validate_dedicated_wear_avd_name("Medium_Phone_API_36.1")
        with self.assertRaises(UnsafeTargetError):
            validate_dedicated_wear_avd_name("unknown_custom_avd")
        with self.assertRaises(UnsafeTargetError):
            validate_dedicated_wear_avd_name("aura_wear36_round", expected_avd_name="aura_wear37_round")
        self.assertEqual("aura_wear36_round", validate_dedicated_wear_avd_name("aura_wear36_round", expected_avd_name="aura_wear36_round"))

        with self.assertRaises(UnsafeTargetError):
            validate_wear_avd_record({"name": "Medium_Phone_API_36.1", "device": "medium_phone (Generic)", "tag_abi": "google_apis_playstore/x86_64"})

        with self.assertRaises(UnsafeTargetError):
            validate_wear_device_properties("nosdcard,default", "36", 36)
        with self.assertRaises(UnsafeTargetError):
            validate_wear_device_properties("watch,nosdcard", "34", 36)
        with self.assertRaises(UnsafeTargetError):
            validate_wear_device_properties("watch,nosdcard", "37", 36, expected_api_level=36)
        self.assertEqual(36, validate_wear_device_properties("watch,nosdcard", "36", 36, expected_api_level=36))

        for plan in RECOMMENDED_WEAR_AVD_PLANS:
            for cmd in build_safe_setup_commands(plan):
                self.assertNotIn("--force", cmd)

        with tempfile.TemporaryDirectory() as tmp:
            apk_path = Path(tmp) / "test-wff4.apk"
            _build_synthetic_resource_only_apk(apk_path)
            true_sha = hashlib.sha256(apk_path.read_bytes()).hexdigest()

            meta = verify_local_apk_before_install(
                apk_path,
                "io.github.scarlel96.aura.watchface.wff4",
                4,
                expected_apk_sha256=true_sha,
                manifest_printer=lambda _: _valid_manifest_xml(),
            )
            self.assertEqual(true_sha, meta["apk_sha256"])

            with self.assertRaises(UnsafeTargetError):
                verify_local_apk_before_install(
                    apk_path,
                    "io.github.scarlel96.aura.watchface.wff4",
                    4,
                    expected_apk_sha256="0" * 64,
                    manifest_printer=lambda _: _valid_manifest_xml(),
                )

            with self.assertRaises(UnsafeTargetError):
                verify_local_apk_before_install(
                    apk_path,
                    "io.github.scarlel96.aura.watchface.wff4",
                    4,
                    manifest_printer=lambda _: _valid_manifest_xml(pkg="io.github.scarlel96.aura.watchface.wff5"),
                )

            with self.assertRaises(UnsafeTargetError):
                verify_local_apk_before_install(
                    apk_path,
                    "io.github.scarlel96.aura.watchface.wff4",
                    4,
                    manifest_printer=lambda _: _valid_manifest_xml(wff_version=3),
                )

            dex_apk = Path(tmp) / "bad-dex.apk"
            _build_synthetic_resource_only_apk(dex_apk, extra_entry=("classes.dex", b"dex"))
            with self.assertRaises(UnsafeTargetError):
                verify_local_apk_before_install(
                    dex_apk,
                    "io.github.scarlel96.aura.watchface.wff4",
                    4,
                    manifest_printer=lambda _: _valid_manifest_xml(),
                )

        with self.assertRaises(RuntimeError):
            validate_mp4_bytes(b"")
        with self.assertRaises(RuntimeError):
            validate_mp4_bytes(b"0" * 2048)
        valid_mp4 = b"\x00\x00\x00\x18ftypmp42" + (b"\x00" * 2048)
        self.assertEqual(len(valid_mp4), validate_mp4_bytes(valid_mp4))

    def test_execute_runtime_verification_enforces_exit_codes_awake_restore_and_cleanup(self):
        """AG-01-R04 §2 & AG-01-R05: verify adb rc, timeout, recorder termination, Awake recovery, remote rm+absence check, and PNG integrity."""
        pkg = "io.github.scarlel96.aura.watchface.wff4"
        valid_png = _build_valid_png_bytes(4, 4)
        valid_mp4 = b"\x00\x00\x00\x18ftypmp42" + (b"\x00" * 2048)

        class FakeRecorder:
            def __init__(self, rc=0, hang_on_terminate=False, unkillable=False):
                self.rc = rc
                self.hang_on_terminate = hang_on_terminate
                self.unkillable = unkillable
                self.terminated = False
                self.killed = False
                self.waits = 0

            def poll(self):
                if self.unkillable:
                    return None
                if self.killed or (self.terminated and not self.hang_on_terminate):
                    return 0
                return self.rc

            def wait(self, timeout=None):
                self.waits += 1
                if self.unkillable:
                    raise subprocess.TimeoutExpired(cmd="screenrecord", timeout=timeout or 5)
                if self.terminated and self.hang_on_terminate and not self.killed:
                    raise subprocess.TimeoutExpired(cmd="screenrecord", timeout=timeout or 5)
                return 0 if (self.terminated or self.killed) else self.rc

            def terminate(self):
                self.terminated = True

            def kill(self):
                self.killed = True

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            apk_path = tmp_path / "watchface-wff4-debug.apk"
            _build_synthetic_resource_only_apk(apk_path)
            apk_sha = hashlib.sha256(apk_path.read_bytes()).hexdigest()
            out_dir = tmp_path / "out"

            power_states = [
                "mWakefulness=Awake\nDisplay Power: state=ON\n",
                "mWakefulness=Dozing\nDisplay Power: state=DOZE_SUSPEND\n",
                "mWakefulness=Awake\nDisplay Power: state=ON\n",
            ]
            commands_log = []

            def make_runner(override_fn=None):
                state_idx = {"i": 0}

                def runner(args, timeout=30, binary=False):
                    commands_log.append(args)
                    if override_fn:
                        ov = override_fn(args, binary)
                        if ov is not None:
                            return ov
                    cmd_str = " ".join(args)
                    if "ro.boot.qemu.avd_name" in cmd_str:
                        return SimpleNamespace(returncode=0, stdout="aura_wear36_round\n", stderr="")
                    if "sys.boot_completed" in cmd_str:
                        return SimpleNamespace(returncode=0, stdout="1\n", stderr="")
                    if "ro.build.characteristics" in cmd_str:
                        return SimpleNamespace(returncode=0, stdout="watch,nosdcard\n", stderr="")
                    if "ro.build.version.sdk" in cmd_str:
                        return SimpleNamespace(returncode=0, stdout="36\n", stderr="")
                    if args[0] == "install":
                        return SimpleNamespace(returncode=0, stdout="Performing Streamed Install\nSuccess\n", stderr="")
                    if "pm list packages" in cmd_str:
                        return SimpleNamespace(returncode=0, stdout=f"package:{pkg}\n", stderr="")
                    if "dumpsys wallpaper" in cmd_str:
                        return SimpleNamespace(returncode=0, stdout=f"mCurrentUserId=0\n  WallpaperData 0 userId=0\n    mWallpaperComponent=ComponentInfo{{{pkg}/.WatchFace}}\n", stderr="")
                    if "dumpsys power" in cmd_str:
                        idx = min(state_idx["i"], len(power_states) - 1)
                        state_idx["i"] += 1
                        return SimpleNamespace(returncode=0, stdout=power_states[idx], stderr="")
                    if "dumpsys display" in cmd_str:
                        return SimpleNamespace(returncode=0, stdout="", stderr="")
                    if "screencap" in cmd_str:
                        return SimpleNamespace(returncode=0, stdout=valid_png, stderr=b"")
                    if args[0] == "pull":
                        Path(args[2]).write_bytes(valid_mp4)
                        return SimpleNamespace(returncode=0, stdout="1 file pulled\n", stderr="")
                    return SimpleNamespace(returncode=0, stdout="", stderr="")

                return runner

            # 1. Full happy path verifies PNG metadata, MP4, Awake restore, rm -f AND `test ! -e`
            res = execute_runtime_verification(
                adb_bin=Path("adb"),
                serial="emulator-5554",
                apk_path=apk_path,
                package_id=pkg,
                wff_version=4,
                output_dir=out_dir,
                expected_avd_name="aura_wear36_round",
                expected_api_level=36,
                expected_apk_sha256=apk_sha,
                runner=make_runner(),
                manifest_printer=lambda _: _valid_manifest_xml(pkg=pkg, min_sdk=36, wff_version=4),
                recorder_factory=lambda: FakeRecorder(rc=0),
                sleep_fn=lambda _: None,
            )
            self.assertTrue(res["recovery_report"]["recorder_stopped"])
            self.assertTrue(res["recovery_report"]["awake_restored"])
            self.assertTrue(res["recovery_report"]["remote_file_removed"])
            self.assertEqual((4, 4), (res["active_png_meta"]["width"], res["active_png_meta"]["height"]))
            self.assertTrue(any("rm" in cmd and "-f" in cmd for cmd in commands_log))
            self.assertTrue(any("test" in cmd and "!" in cmd and "-e" in cmd for cmd in commands_log))

            # 2. Mid-run failure with clean recovery: recorder hung on terminate -> kill+wait succeeds,
            #    recovery WAKEUP + dumpsys confirms Awake+ON, rm -f + test ! -e succeeds -> raises original RuntimeError
            commands_log.clear()
            power_states[:] = [
                "mWakefulness=Awake\nDisplay Power: state=ON\n",
                "mWakefulness=Awake\nDisplay Power: state=ON\n",
            ]
            hang_rec = FakeRecorder(rc=None, hang_on_terminate=True)
            with self.assertRaises(RuntimeError) as ctx:
                execute_runtime_verification(
                    adb_bin=Path("adb"),
                    serial="emulator-5554",
                    apk_path=apk_path,
                    package_id=pkg,
                    wff_version=4,
                    output_dir=out_dir,
                    expected_avd_name="aura_wear36_round",
                    runner=make_runner(
                        lambda args, _: SimpleNamespace(returncode=1, stdout="", stderr="input service dead")
                        if "KEYCODE_SLEEP" in args else None
                    ),
                    manifest_printer=lambda _: _valid_manifest_xml(pkg=pkg, min_sdk=36, wff_version=4),
                    recorder_factory=lambda: hang_rec,
                    sleep_fn=lambda _: None,
                )
            self.assertNotIsInstance(ctx.exception, RecoveryFailureError)
            self.assertTrue(hang_rec.terminated)
            self.assertTrue(hang_rec.killed)
            self.assertGreaterEqual(hang_rec.waits, 2)

            # 3. Failure recovery failure: remote rm -f fails with rc=1 AND recovery WAKEUP times out -> MUST raise RecoveryFailureError (never swallowed!)
            power_states[:] = [
                "mWakefulness=Awake\nDisplay Power: state=ON\n",
                "mWakefulness=Dozing\nDisplay Power: state=DOZE\n",
                "mWakefulness=Dozing\nDisplay Power: state=DOZE\n",
            ]

            def fail_recovery_override(args, _):
                if "KEYCODE_SLEEP" in args:
                    return SimpleNamespace(returncode=1, stdout="", stderr="sleep failed")
                if "rm" in args:
                    return SimpleNamespace(returncode=1, stdout="", stderr="permission denied")
                if "KEYCODE_WAKEUP" in args and sum(1 for c in commands_log if "KEYCODE_WAKEUP" in c) >= 2:
                    raise subprocess.TimeoutExpired(cmd="adb wakeup", timeout=15)
                return None

            unkillable_rec = FakeRecorder(rc=None, unkillable=True)
            commands_log.clear()
            with self.assertRaises(RecoveryFailureError) as rec_ctx:
                execute_runtime_verification(
                    adb_bin=Path("adb"),
                    serial="emulator-5554",
                    apk_path=apk_path,
                    package_id=pkg,
                    wff_version=4,
                    output_dir=out_dir,
                    expected_avd_name="aura_wear36_round",
                    runner=make_runner(fail_recovery_override),
                    manifest_printer=lambda _: _valid_manifest_xml(pkg=pkg, min_sdk=36, wff_version=4),
                    recorder_factory=lambda: unkillable_rec,
                    sleep_fn=lambda _: None,
                )
            err_joined = " ".join(rec_ctx.exception.recovery_errors)
            self.assertIn("recorder_termination_failed", err_joined)
            self.assertIn("awake_recovery_failed", err_joined)
            self.assertIn("remote_cleanup_failed", err_joined)
            self.assertIsNotNone(rec_ctx.exception.primary_error)

            # 4. Failure recovery: remote `test ! -e` fails (file still exists after rm) -> MUST raise RecoveryFailureError
            power_states[:] = [
                "mWakefulness=Awake\nDisplay Power: state=ON\n",
                "mWakefulness=Dozing\nDisplay Power: state=DOZE\n",
                "mWakefulness=Awake\nDisplay Power: state=ON\n",
            ]
            with self.assertRaises(RecoveryFailureError) as rm_ctx:
                execute_runtime_verification(
                    adb_bin=Path("adb"),
                    serial="emulator-5554",
                    apk_path=apk_path,
                    package_id=pkg,
                    wff_version=4,
                    output_dir=out_dir,
                    expected_avd_name="aura_wear36_round",
                    runner=make_runner(
                        lambda args, _: SimpleNamespace(returncode=1, stdout="", stderr="file still exists")
                        if "test" in args and "-e" in args else None
                    ),
                    manifest_printer=lambda _: _valid_manifest_xml(pkg=pkg, min_sdk=36, wff_version=4),
                    recorder_factory=lambda: FakeRecorder(rc=0),
                    sleep_fn=lambda _: None,
                )
            self.assertIn("remote_cleanup_failed", " ".join(rm_ctx.exception.recovery_errors))

            # 5. Failure fixture: UNKNOWN wallpaper binding (missing current user binding) -> RuntimeVerificationIncompleteError
            with self.assertRaises(RuntimeVerificationIncompleteError):
                execute_runtime_verification(
                    adb_bin=Path("adb"),
                    serial="emulator-5554",
                    apk_path=apk_path,
                    package_id=pkg,
                    wff_version=4,
                    output_dir=out_dir,
                    expected_avd_name="aura_wear36_round",
                    runner=make_runner(
                        lambda args, _: SimpleNamespace(
                            returncode=0,
                            stdout=f"mCurrentUserId=0\n  WallpaperData 10 userId=10\n    mWallpaperComponent=ComponentInfo{{{pkg}/.WatchFace}}\n",
                            stderr="",
                        ) if "wallpaper" in args else None
                    ),
                    manifest_printer=lambda _: _valid_manifest_xml(pkg=pkg, min_sdk=36, wff_version=4),
                    recorder_factory=lambda: FakeRecorder(rc=0),
                    sleep_fn=lambda _: None,
                )

            # 6. Failure fixture: corrupt screencap PNG (4-byte header only) -> RuntimeError before saving
            with self.assertRaises(RuntimeError):
                execute_runtime_verification(
                    adb_bin=Path("adb"),
                    serial="emulator-5554",
                    apk_path=apk_path,
                    package_id=pkg,
                    wff_version=4,
                    output_dir=out_dir,
                    expected_avd_name="aura_wear36_round",
                    runner=make_runner(
                        lambda args, _: SimpleNamespace(returncode=0, stdout=b"\x89PNG\x00\x00\x00", stderr=b"")
                        if "screencap" in args else None
                    ),
                    manifest_printer=lambda _: _valid_manifest_xml(pkg=pkg, min_sdk=36, wff_version=4),
                    recorder_factory=lambda: FakeRecorder(rc=0),
                    sleep_fn=lambda _: None,
                )


class Ag01OfficialValidatorMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jar = ensure_validator_jar()

    def test_positive_pocs_across_all_wff_versions(self):
        """Verify all 6 PoCs pass on their supported WFF versions and explicitly fail on lower WFF versions (24 subtests)."""
        for spec in POC_SPECS:
            for version in (2, 3, 4, 5):
                with self.subTest(poc=spec["id"], wff_version=version):
                    proc = run_validator_utf8(self.jar, spec["path"], version)
                    if version >= spec["min_version"]:
                        require_pass(proc.returncode, proc.stdout, spec["path"], version)
                    else:
                        require_rejection(proc.returncode, proc.stdout, spec["path"], version)

    def test_negative_fixtures_across_all_wff_versions(self):
        """Verify all 7 baseline negative fixtures explicitly fail on invalid versions and pass only where valid (28 subtests)."""
        for spec in NEGATIVE_SPECS:
            for version in (2, 3, 4, 5):
                with self.subTest(fixture=spec["id"], wff_version=version):
                    proc = run_validator_utf8(self.jar, spec["path"], version)
                    if version in spec["fail_versions"]:
                        expected_err = spec["expected_error"] if version == max(spec["fail_versions"]) else None
                        require_rejection(proc.returncode, proc.stdout, spec["path"], version, expected_err)
                    else:
                        require_pass(proc.returncode, proc.stdout, spec["path"], version)

    def test_separated_negative_fixtures_across_all_wff_versions(self):
        """AG01-AUD-02: verify separated single-fault duration and Reference-parent fixtures explicitly fail (8 subtests)."""
        for spec in SEPARATED_NEGATIVE_SPECS:
            for version in (2, 3, 4, 5):
                with self.subTest(fixture=spec["id"], wff_version=version):
                    proc = run_validator_utf8(self.jar, spec["path"], version)
                    expected_err = spec["expected_error"] if version == max(spec["fail_versions"]) else None
                    require_rejection(proc.returncode, proc.stdout, spec["path"], version, expected_err)

    def test_ablation_fixtures_valid_on_wff4_and_wff5(self):
        """Verify all 4 controlled ablation fixtures pass WFF 4 and WFF 5 validation (8 subtests)."""
        for spec in ABLATION_SPECS:
            for version in (4, 5):
                with self.subTest(ablation=spec["id"], wff_version=version):
                    proc = run_validator_utf8(self.jar, spec["path"], version)
                    require_pass(proc.returncode, proc.stdout, spec["path"], version)


if __name__ == "__main__":
    unittest.main()
