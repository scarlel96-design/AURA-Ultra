"""Unit, schema, validator-strictness, emulator-inspection, and runtime-safety regression suite for AG-01."""
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

AG01_DIR = Path(__file__).resolve().parent
ROOT = AG01_DIR.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(AG01_DIR))

from run_ag01_verification import (
    ABLATION_SPECS,
    ESTIMATED_WEAR_IMAGE_CANDIDATES,
    NEGATIVE_SPECS,
    POC_SPECS,
    SEPARATED_NEGATIVE_SPECS,
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
from verify_wff import require_pass
from wear_emulator_runtime import (
    RECOMMENDED_WEAR_AVD_PLANS,
    UnsafeTargetError,
    build_safe_runtime_verification_plan,
    build_safe_setup_commands,
    parse_power_and_display_state,
    validate_emulator_serial,
    validate_wear_avd_record,
    validate_wear_device_properties,
    verify_active_watchface_selected,
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


class Ag01PoCStructureTests(unittest.TestCase):
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
        """AG01-AUD-02: ensure duration-range and Reference-parent fixtures each carry only their own fault."""
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
    """AG01-AUD-01 & Runtime Safety regression tests (tool missing/error/empty, phone vs Wear AVD, physical ADB exclusion)."""

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
            # No tools exist inside tmp -> MISSING -> UNKNOWN
            info_missing = inspect_emulator_environment(sdk_root=Path(tmp))
            self.assertEqual("UNKNOWN", info_missing["status"])

        # Prepare fake tool binaries so inspect_emulator_environment invokes mocked runner
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

            # Case 1: sdkmanager returns nonzero error -> UNKNOWN
            def runner_sm_error(cmd, timeout=60):
                if "sdkmanager" in cmd[0]:
                    return {"command": cmd, "status": "ERROR", "returncode": 1, "stdout": "", "stderr": "network failed", "error": "exit 1"}
                return {"command": cmd, "status": "OK", "returncode": 0, "stdout": "List of devices attached\n", "stderr": "", "error": ""}

            res_err = inspect_emulator_environment(sdk_root=sdk, runner=runner_sm_error)
            self.assertEqual("UNKNOWN", res_err["status"])
            self.assertEqual([], res_err["observed_sdkmanager_available_wear_images"])

            # Case 2: avdmanager returns empty output -> UNKNOWN
            def runner_avd_empty(cmd, timeout=60):
                if "sdkmanager" in cmd[0]:
                    return {"command": cmd, "status": "OK", "returncode": 0, "stdout": SAMPLE_SDKMANAGER_STDOUT, "stderr": "", "error": ""}
                if "avdmanager" in cmd[0]:
                    return {"command": cmd, "status": "OK", "returncode": 0, "stdout": "   \n", "stderr": "", "error": ""}
                return {"command": cmd, "status": "OK", "returncode": 0, "stdout": "List of devices attached\n", "stderr": "", "error": ""}

            res_empty = inspect_emulator_environment(sdk_root=sdk, runner=runner_avd_empty)
            self.assertEqual("UNKNOWN", res_empty["status"])

            # Case 3: Phone AVD + physical watch connected via ADB -> MUST stay NOT RUN (never READY!)
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

    def test_runtime_safety_guards_block_physical_devices_phone_avds_and_force_overwrite(self):
        with self.assertRaises(UnsafeTargetError):
            validate_emulator_serial("R5CX1234567")
        with self.assertRaises(UnsafeTargetError):
            validate_emulator_serial("")
        self.assertEqual("emulator-5554", validate_emulator_serial("emulator-5554"))

        with self.assertRaises(UnsafeTargetError):
            validate_wear_avd_record({"name": "Medium_Phone_API_36.1", "device": "medium_phone (Generic)", "tag_abi": "google_apis_playstore/x86_64"})
        self.assertEqual(
            "aura_wear36_round",
            validate_wear_avd_record({"name": "aura_wear36_round", "device": "wearos_large_round (Google)", "tag_abi": "android-wear-signed/x86_64"}),
        )

        with self.assertRaises(UnsafeTargetError):
            validate_wear_device_properties("nosdcard,default", "36", 36)
        with self.assertRaises(UnsafeTargetError):
            validate_wear_device_properties("watch,nosdcard", "34", 36)
        self.assertEqual(36, validate_wear_device_properties("watch,nosdcard", "36", 36))

        for plan in RECOMMENDED_WEAR_AVD_PLANS:
            cmds = build_safe_setup_commands(plan)
            for cmd in cmds:
                self.assertNotIn("--force", cmd, "AVD creation commands must never include --force")

        runtime_plan = build_safe_runtime_verification_plan(
            "emulator-5554", "watchface-wff4-debug.apk", "io.github.scarlel96.aura.watchface.wff4", 4, "docs/evidence/AG-01/runtime-wff4"
        )
        for step in runtime_plan["steps"]:
            for cmd in step["commands"]:
                if cmd.startswith("adb "):
                    self.assertIn("-s emulator-5554", cmd)

        awake = parse_power_and_display_state("mWakefulness=Awake\nDisplay Power: state=ON\n")
        self.assertTrue(awake["is_active"])
        self.assertFalse(awake["is_aod"])

        doze = parse_power_and_display_state("mWakefulness=Dozing\nDisplay Power: state=DOZE_SUSPEND\n")
        self.assertFalse(doze["is_active"])
        self.assertTrue(doze["is_aod"])

        sel_ok = verify_active_watchface_selected("mWallpaperComponent=ComponentInfo{io.github.scarlel96.aura.watchface.wff4/.WatchFace}", "io.github.scarlel96.aura.watchface.wff4")
        self.assertTrue(sel_ok["selected"])
        sel_miss = verify_active_watchface_selected("mWallpaperComponent=ComponentInfo{com.google.android.wearable.watchface/.Default}", "io.github.scarlel96.aura.watchface.wff4")
        self.assertFalse(sel_miss["selected"])


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
