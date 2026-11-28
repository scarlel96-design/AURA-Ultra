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
    EvidenceOverwriteError,
    PNG_SIGNATURE,
    RECOMMENDED_WEAR_AVD_PLANS,
    RecoveryFailureError,
    RuntimeVerificationIncompleteError,
    UnsafeTargetError,
    build_safe_runtime_verification_plan,
    build_safe_setup_commands,
    execute_runtime_verification,
    parse_and_validate_mp4_structure,
    parse_power_and_display_state,
    validate_dedicated_wear_avd_name,
    validate_emulator_serial,
    validate_mp4_bytes,
    validate_png_bytes,
    validate_wear_avd_record,
    validate_wear_device_properties,
    verify_active_watchface_selected,
    verify_local_apk_before_install,
    verify_mp4_video_artifact,
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


def _mp4_box(box_type, payload):
    return struct.pack(">I4s", 8 + len(payload), box_type) + payload


def _build_valid_mp4_bytes(handler=b"vide", sample_count=24, sample_size=64, codec=b"avc1", bad_offset=None, include_stsc=True):
    """Build a structurally valid ISO BMFF MP4 with ftyp + mdat + moov(trak/mdia/hdlr/minf/stbl[stsd+stsz+stsc+stco])."""
    ftyp = _mp4_box(b"ftyp", b"mp42" + struct.pack(">I", 0) + b"mp42isom")
    mdat_payload = b"\x00\x00\x00\x01\x65" + (b"\xAB" * max(128, sample_count * sample_size))
    mdat_header_offset = len(ftyp)
    mdat_payload_offset = mdat_header_offset + 8
    mdat = _mp4_box(b"mdat", mdat_payload)

    hdlr = _mp4_box(b"hdlr", b"\x00\x00\x00\x00" + b"\x00\x00\x00\x00" + handler + (b"\x00" * 12) + b"VideoHandler\x00")
    codec_entry = _mp4_box(codec, b"\x00" * 24)
    stsd = _mp4_box(b"stsd", b"\x00\x00\x00\x00" + struct.pack(">I", 1) + codec_entry)
    if sample_count > 0:
        stsz = _mp4_box(b"stsz", b"\x00\x00\x00\x00" + struct.pack(">II", sample_size, sample_count))
    else:
        stsz = _mp4_box(b"stsz", b"\x00\x00\x00\x00" + struct.pack(">II", 0, 0))
    stsc = (
        _mp4_box(b"stsc", b"\x00\x00\x00\x00" + struct.pack(">IIII", 1, 1, max(1, sample_count), 1))
        if include_stsc
        else b""
    )
    chunk_off = mdat_payload_offset if bad_offset is None else bad_offset
    stco = _mp4_box(b"stco", b"\x00\x00\x00\x00" + struct.pack(">II", 1, chunk_off))
    stbl = _mp4_box(b"stbl", stsd + stsz + stsc + stco)
    minf = _mp4_box(b"minf", stbl)
    mdia = _mp4_box(b"mdia", hdlr + minf)
    trak = _mp4_box(b"trak", mdia)
    moov = _mp4_box(b"moov", trak)
    return ftyp + mdat + moov


def _ok_ffprobe_runner(frames=24):
    payload = (
        '{"streams":[{"codec_type":"video","codec_name":"h264","width":454,"height":454,"nb_read_frames":"'
        + str(frames)
        + '"}]}'
    )
    return lambda cmd, timeout=60: SimpleNamespace(returncode=0, stdout=payload, stderr="")


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
        with self.assertRaises(RuntimeError):
            validate_mp4_bytes(b"\x00\x00\x00\x18ftypmp42" + (b"\x00" * 2048))
        valid_mp4 = _build_valid_mp4_bytes()
        self.assertEqual(len(valid_mp4), validate_mp4_bytes(valid_mp4))

    def test_execute_runtime_verification_enforces_exit_codes_awake_restore_and_cleanup(self):
        """AG-01-R04 §2, R05 & R06: verify adb rc, timeout, recorder termination, Awake+watchface recovery, remote rm+absence check, PNG & MP4."""
        pkg = "io.github.scarlel96.aura.watchface.wff4"
        valid_png = _build_valid_png_bytes(4, 4)
        valid_mp4 = _build_valid_mp4_bytes()

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

            power_states = [
                "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n",
                "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n",
                "mWakefulness=Dozing\nDisplay Id=0\nDisplay Power: state=DOZE_SUSPEND\n",
                "mWakefulness=Dozing\nDisplay Id=0\nDisplay Power: state=DOZE_SUSPEND\n",
                "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n",
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

            # 1. Full happy path verifies PNG metadata, MP4 + ffprobe, Awake+watchface restore, rm -f AND `test ! -e`
            res = execute_runtime_verification(
                adb_bin=Path("adb"),
                serial="emulator-5554",
                apk_path=apk_path,
                package_id=pkg,
                wff_version=4,
                output_dir=tmp_path / "out_happy",
                expected_avd_name="aura_wear36_round",
                expected_api_level=36,
                expected_apk_sha256=apk_sha,
                runner=make_runner(),
                manifest_printer=lambda _: _valid_manifest_xml(pkg=pkg, min_sdk=36, wff_version=4),
                recorder_factory=lambda: FakeRecorder(rc=0),
                probe_runner=_ok_ffprobe_runner(24),
                sleep_fn=lambda _: None,
            )
            self.assertTrue(res["recovery_report"]["recorder_stopped"])
            self.assertTrue(res["recovery_report"]["awake_restored"])
            self.assertTrue(res["recovery_report"]["watchface_restored"])
            self.assertTrue(res["recovery_report"]["remote_file_removed"])
            self.assertEqual("PASS", res["video_verification_status"])
            self.assertEqual((4, 4), (res["active_png_meta"]["width"], res["active_png_meta"]["height"]))
            self.assertTrue(any("rm" in cmd and "-f" in cmd for cmd in commands_log))
            self.assertTrue(any("test" in cmd and "!" in cmd and "-e" in cmd for cmd in commands_log))

            # 2. Mid-run failure with clean recovery: recorder hung on terminate -> kill+wait succeeds,
            #    recovery WAKEUP + dumpsys confirms Awake+ON + watchface, rm -f + test ! -e succeeds -> raises original RuntimeError
            commands_log.clear()
            power_states[:] = [
                "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n",
                "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n",
                "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n",
            ]
            hang_rec = FakeRecorder(rc=None, hang_on_terminate=True)
            with self.assertRaises(RuntimeError) as ctx:
                execute_runtime_verification(
                    adb_bin=Path("adb"),
                    serial="emulator-5554",
                    apk_path=apk_path,
                    package_id=pkg,
                    wff_version=4,
                    output_dir=tmp_path / "out_hang",
                    expected_avd_name="aura_wear36_round",
                    runner=make_runner(
                        lambda args, _: SimpleNamespace(returncode=1, stdout="", stderr="input service dead")
                        if "KEYCODE_SLEEP" in args else None
                    ),
                    manifest_printer=lambda _: _valid_manifest_xml(pkg=pkg, min_sdk=36, wff_version=4),
                    recorder_factory=lambda: hang_rec,
                    probe_runner=_ok_ffprobe_runner(24),
                    sleep_fn=lambda _: None,
                )
            self.assertNotIsInstance(ctx.exception, RecoveryFailureError)
            self.assertTrue(hang_rec.terminated)
            self.assertTrue(hang_rec.killed)
            self.assertGreaterEqual(hang_rec.waits, 2)

            # 3. Failure recovery failure: remote rm -f fails with rc=1 AND recovery WAKEUP times out -> MUST raise RecoveryFailureError (never swallowed!)
            power_states[:] = [
                "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n",
                "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n",
                "mWakefulness=Dozing\nDisplay Id=0\nDisplay Power: state=DOZE\n",
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
                    output_dir=tmp_path / "out_rec_fail",
                    expected_avd_name="aura_wear36_round",
                    runner=make_runner(fail_recovery_override),
                    manifest_printer=lambda _: _valid_manifest_xml(pkg=pkg, min_sdk=36, wff_version=4),
                    recorder_factory=lambda: unkillable_rec,
                    probe_runner=_ok_ffprobe_runner(24),
                    sleep_fn=lambda _: None,
                )
            err_joined = " ".join(rec_ctx.exception.recovery_errors)
            self.assertIn("recorder_termination_failed", err_joined)
            self.assertIn("awake_recovery_failed", err_joined)
            self.assertIn("remote_cleanup_failed", err_joined)
            self.assertIsNotNone(rec_ctx.exception.primary_error)

            # 4. Failure recovery: remote `test ! -e` fails (file still exists after rm) -> MUST raise RecoveryFailureError
            power_states[:] = [
                "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n",
                "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n",
                "mWakefulness=Dozing\nDisplay Id=0\nDisplay Power: state=DOZE\n",
                "mWakefulness=Dozing\nDisplay Id=0\nDisplay Power: state=DOZE\n",
                "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n",
            ]
            with self.assertRaises(RecoveryFailureError) as rm_ctx:
                execute_runtime_verification(
                    adb_bin=Path("adb"),
                    serial="emulator-5554",
                    apk_path=apk_path,
                    package_id=pkg,
                    wff_version=4,
                    output_dir=tmp_path / "out_rm_fail",
                    expected_avd_name="aura_wear36_round",
                    runner=make_runner(
                        lambda args, _: SimpleNamespace(returncode=1, stdout="", stderr="file still exists")
                        if "test" in args and "-e" in args else None
                    ),
                    manifest_printer=lambda _: _valid_manifest_xml(pkg=pkg, min_sdk=36, wff_version=4),
                    recorder_factory=lambda: FakeRecorder(rc=0),
                    probe_runner=_ok_ffprobe_runner(24),
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
                    output_dir=tmp_path / "out_wp_unknown",
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
                    probe_runner=_ok_ffprobe_runner(24),
                    sleep_fn=lambda _: None,
                )

            # 6. Failure fixture: corrupt screencap PNG (4-byte header only) -> RuntimeError before saving
            power_states[:] = [
                "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n",
                "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n",
            ]
            with self.assertRaises(RuntimeError):
                execute_runtime_verification(
                    adb_bin=Path("adb"),
                    serial="emulator-5554",
                    apk_path=apk_path,
                    package_id=pkg,
                    wff_version=4,
                    output_dir=tmp_path / "out_bad_png",
                    expected_avd_name="aura_wear36_round",
                    runner=make_runner(
                        lambda args, _: SimpleNamespace(returncode=0, stdout=b"\x89PNG\x00\x00\x00", stderr=b"")
                        if "screencap" in args else None
                    ),
                    manifest_printer=lambda _: _valid_manifest_xml(pkg=pkg, min_sdk=36, wff_version=4),
                    recorder_factory=lambda: FakeRecorder(rc=0),
                    probe_runner=_ok_ffprobe_runner(24),
                    sleep_fn=lambda _: None,
                )

    def test_r06_aud05_per_display_id_mapping_dedup_and_target_display(self):
        """AG01-AUD-05: explicit Display ID mapping; duplicate observations never count for another display; unknown target display -> UNKNOWN."""
        # 1. Display Id=0 has 2 duplicate ON lines, Display Id=1 has NO state -> MUST be UNKNOWN (never inflated!)
        dup_obs = (
            "mWakefulness=Awake\n"
            "Display Id=0\n"
            "Display Power: state=ON\n"
            "mScreenState=ON\n"
            "Display Id=1\n"
        )
        r1 = parse_power_and_display_state(dup_obs)
        self.assertEqual("UNKNOWN", r1["status"])
        self.assertFalse(r1["is_active"])
        self.assertEqual(["ON"], r1["display_states_by_id"]["0"])
        self.assertEqual([], r1["display_states_by_id"]["1"])

        # 2. Only secondary Display Id=1 present, default target Display Id=0 missing -> MUST be UNKNOWN
        r2 = parse_power_and_display_state("mWakefulness=Awake\nDisplay Id=1\nDisplay Power: state=ON\n")
        self.assertEqual("UNKNOWN", r2["status"])
        self.assertEqual("TARGET_DISPLAY_MISSING", r2["display_state"])
        self.assertFalse(r2["is_active"])

        # 3. Both Display Id=0 and Display Id=1 explicitly mapped to ON -> ACTIVE
        both_on = (
            "mWakefulness=Awake\n"
            "Display Id=0\nDisplay Power: state=ON\n"
            "Display Id=1\nDisplay Power: state=ON\n"
        )
        r3 = parse_power_and_display_state(both_on)
        self.assertEqual("ACTIVE", r3["status"])
        self.assertTrue(r3["is_active"])
        self.assertEqual({"0": ["ON"], "1": ["ON"]}, r3["display_states_by_id"])

        # 4. Same Display Id=0 reports ON in power and DOZE in display -> CONFLICT -> UNKNOWN
        r4 = parse_power_and_display_state(
            "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n",
            "Display Id=0\nmScreenState=DOZE\n",
        )
        self.assertEqual("UNKNOWN", r4["status"])
        self.assertFalse(r4["is_active"])

        # 5. Non-default target_display_id="1" with unscoped dump (no Display IDs) -> TARGET_DISPLAY_MISSING -> UNKNOWN
        r5 = parse_power_and_display_state("mWakefulness=Awake\nDisplay Power: state=ON\n", target_display_id="1")
        self.assertEqual("UNKNOWN", r5["status"])
        self.assertEqual("TARGET_DISPLAY_MISSING", r5["display_state"])

    def test_r06_aud06_png_bounds_zlib_eof_interlace_and_chunk_order(self):
        """AG01-AUD-06: PNG input/resolution/decompressed bounds, zlib eof/unused_data, interlace rejection, and strict chunk ordering."""
        ihdr_4x4 = _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 6, 0, 0, 0))
        raw_4x4 = b"".join(b"\x00" + (b"\x10\x20\x30\xff" * 4) for _ in range(4))
        comp_4x4 = zlib.compress(raw_4x4)
        iend = _png_chunk(b"IEND", b"")

        # 1. Unsupported interlace=1 (Adam7) -> MUST FAIL
        ihdr_interlaced = _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 6, 0, 0, 1))
        with self.assertRaises(RuntimeError):
            validate_png_bytes(PNG_SIGNATURE + ihdr_interlaced + _png_chunk(b"IDAT", comp_4x4) + iend)

        # 2. Trailing unused bytes inside IDAT after valid zlib stream end -> MUST FAIL
        with self.assertRaises(RuntimeError):
            validate_png_bytes(PNG_SIGNATURE + ihdr_4x4 + _png_chunk(b"IDAT", comp_4x4 + b"EXTRA") + iend)

        # 3. Truncated/unterminated zlib stream (eof=False) -> MUST FAIL
        with self.assertRaises(RuntimeError):
            validate_png_bytes(PNG_SIGNATURE + ihdr_4x4 + _png_chunk(b"IDAT", comp_4x4[:-4]) + iend)

        # 4. Non-contiguous IDAT chunks separated by ancillary tEXt -> MUST FAIL
        mid = len(comp_4x4) // 2
        non_contig = (
            PNG_SIGNATURE
            + ihdr_4x4
            + _png_chunk(b"IDAT", comp_4x4[:mid])
            + _png_chunk(b"tEXt", b"Key\x00Val")
            + _png_chunk(b"IDAT", comp_4x4[mid:])
            + iend
        )
        with self.assertRaises(RuntimeError):
            validate_png_bytes(non_contig)

        # 5. PLTE after IDAT, duplicate PLTE, and PLTE on grayscale -> MUST FAIL
        with self.assertRaises(RuntimeError):
            validate_png_bytes(PNG_SIGNATURE + ihdr_4x4 + _png_chunk(b"IDAT", comp_4x4) + _png_chunk(b"PLTE", b"\x00\x00\x00") + iend)
        gray_ihdr = _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 0, 0, 0, 0))
        gray_idat = _png_chunk(b"IDAT", zlib.compress(b"".join(b"\x00" + b"\x00" * 4 for _ in range(4))))
        with self.assertRaises(RuntimeError):
            validate_png_bytes(PNG_SIGNATURE + gray_ihdr + _png_chunk(b"PLTE", b"\x00\x00\x00") + gray_idat + iend)

        # 6. Unknown critical chunk (uppercase first byte) and APNG acTL chunk -> MUST FAIL
        with self.assertRaises(RuntimeError):
            validate_png_bytes(PNG_SIGNATURE + ihdr_4x4 + _png_chunk(b"XyZz", b"abc") + _png_chunk(b"IDAT", comp_4x4) + iend)
        with self.assertRaises(RuntimeError):
            validate_png_bytes(PNG_SIGNATURE + ihdr_4x4 + _png_chunk(b"acTL", b"\x00\x00\x00\x02\x00\x00\x00\x00") + _png_chunk(b"IDAT", comp_4x4) + iend)

        # 7. Input size, resolution, and decompressed size upper bounds -> MUST FAIL
        good = _build_valid_png_bytes(8, 8)
        with self.assertRaises(RuntimeError):
            validate_png_bytes(good, max_input_bytes=len(good) - 1)
        with self.assertRaises(RuntimeError):
            validate_png_bytes(good, max_width=4, max_height=4)
        with self.assertRaises(RuntimeError):
            validate_png_bytes(good, max_decompressed_bytes=16)

    def test_r06_aud07_mp4_box_video_track_frames_and_missing_tool_not_run(self):
        """AG01-AUD-07: MP4 box/video-track/sample verification + ffprobe decoded frames; missing probe tool -> NOT RUN."""
        # 1. Structural rejections: fake zero-padded ftyp, audio-only track, 0 samples, out-of-bounds chunk offset
        with self.assertRaises(RuntimeError):
            parse_and_validate_mp4_structure(b"\x00\x00\x00\x18ftypmp42" + (b"\x00" * 2048))
        with self.assertRaises(RuntimeError):
            parse_and_validate_mp4_structure(_build_valid_mp4_bytes(handler=b"soun"))
        with self.assertRaises(RuntimeError):
            parse_and_validate_mp4_structure(_build_valid_mp4_bytes(sample_count=0))
        with self.assertRaises(RuntimeError):
            parse_and_validate_mp4_structure(_build_valid_mp4_bytes(bad_offset=999999))

        valid_mp4 = _build_valid_mp4_bytes(sample_count=18, sample_size=64)
        meta = parse_and_validate_mp4_structure(valid_mp4)
        self.assertEqual(1, meta["video_track_count"])
        self.assertEqual(18, meta["sample_count"])
        self.assertEqual("avc1", meta["video_tracks"][0]["codec"])

        with tempfile.TemporaryDirectory() as tmp:
            mp4_file = Path(tmp) / "clip.mp4"
            mp4_file.write_bytes(valid_mp4)

            # 2. Missing ffprobe binary -> explicit NOT RUN (never PASS!)
            missing_res = verify_mp4_video_artifact(mp4_file, ffprobe_bin=Path(tmp) / "no_such_ffprobe")
            self.assertEqual("NOT_RUN", missing_res["status"])
            self.assertEqual("NOT RUN", missing_res["video_verification_status"])
            self.assertFalse(missing_res["frames_verified"])

            # 3. ffprobe reports 0 decoded frames -> RuntimeError
            with self.assertRaises(RuntimeError):
                verify_mp4_video_artifact(mp4_file, probe_runner=_ok_ffprobe_runner(frames=0))

            # 4. ffprobe confirms 18 decoded frames -> VERIFIED / PASS
            ok_res = verify_mp4_video_artifact(mp4_file, probe_runner=_ok_ffprobe_runner(frames=18))
            self.assertEqual("VERIFIED", ok_res["status"])
            self.assertEqual("PASS", ok_res["video_verification_status"])
            self.assertTrue(ok_res["frames_verified"])
            self.assertEqual(18, ok_res["decoded_frame_count"])

            # 5. execute_runtime_verification with missing ffprobe MUST raise RuntimeVerificationIncompleteError (NOT RUN)
            pkg = "io.github.scarlel96.aura.watchface.wff4"
            apk_path = Path(tmp) / "wff4.apk"
            _build_synthetic_resource_only_apk(apk_path)
            valid_png = _build_valid_png_bytes(4, 4)
            p_seq = [
                "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n",
                "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n",
                "mWakefulness=Dozing\nDisplay Id=0\nDisplay Power: state=DOZE_SUSPEND\n",
                "mWakefulness=Dozing\nDisplay Id=0\nDisplay Power: state=DOZE_SUSPEND\n",
                "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n",
            ]
            p_idx = {"i": 0}

            def runner_ok(args, timeout=30, binary=False):
                s = " ".join(args)
                if "ro.boot.qemu.avd_name" in s: return SimpleNamespace(returncode=0, stdout="aura_wear36_round\n", stderr="")
                if "sys.boot_completed" in s: return SimpleNamespace(returncode=0, stdout="1\n", stderr="")
                if "ro.build.characteristics" in s: return SimpleNamespace(returncode=0, stdout="watch\n", stderr="")
                if "ro.build.version.sdk" in s: return SimpleNamespace(returncode=0, stdout="36\n", stderr="")
                if args[0] == "install": return SimpleNamespace(returncode=0, stdout="Success\n", stderr="")
                if "pm list packages" in s: return SimpleNamespace(returncode=0, stdout=f"package:{pkg}\n", stderr="")
                if "dumpsys wallpaper" in s: return SimpleNamespace(returncode=0, stdout=f"mCurrentUserId=0\n  WallpaperData 0 userId=0\n    mWallpaperComponent=ComponentInfo{{{pkg}/.WatchFace}}\n", stderr="")
                if "dumpsys power" in s:
                    out_s = p_seq[min(p_idx["i"], len(p_seq) - 1)]
                    p_idx["i"] += 1
                    return SimpleNamespace(returncode=0, stdout=out_s, stderr="")
                if "screencap" in s: return SimpleNamespace(returncode=0, stdout=valid_png, stderr=b"")
                if args[0] == "pull":
                    Path(args[2]).write_bytes(valid_mp4)
                    return SimpleNamespace(returncode=0, stdout="1 file pulled\n", stderr="")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            class DoneRec:
                def poll(self): return 0
                def wait(self, timeout=None): return 0
                def terminate(self): pass
                def kill(self): pass

            with self.assertRaises(RuntimeVerificationIncompleteError) as not_run_ctx:
                execute_runtime_verification(
                    adb_bin=Path("adb"),
                    serial="emulator-5554",
                    apk_path=apk_path,
                    package_id=pkg,
                    wff_version=4,
                    output_dir=Path(tmp) / "out_no_ffprobe",
                    expected_avd_name="aura_wear36_round",
                    runner=runner_ok,
                    manifest_printer=lambda _: _valid_manifest_xml(pkg=pkg, min_sdk=36, wff_version=4),
                    recorder_factory=lambda: DoneRec(),
                    ffprobe_bin=Path(tmp) / "no_such_ffprobe",
                    sleep_fn=lambda _: None,
                )
            self.assertIn("NOT RUN", str(not_run_ctx.exception))

    def test_r06_aud08_watchface_and_screen_consistency_before_after_captures_and_restore(self):
        """AG01-AUD-08: active watchface and screen state must be re-verified before/after Active & AOD captures and at final restore."""
        pkg = "io.github.scarlel96.aura.watchface.wff4"
        valid_png = _build_valid_png_bytes(4, 4)
        valid_mp4 = _build_valid_mp4_bytes(sample_count=12)
        good_wp = f"mCurrentUserId=0\n  WallpaperData 0 userId=0\n    mWallpaperComponent=ComponentInfo{{{pkg}/.WatchFace}}\n"
        drifted_wp = "mCurrentUserId=0\n  WallpaperData 0 userId=0\n    mWallpaperComponent=ComponentInfo{com.example.other/.Face}\n"

        class DoneRec:
            def poll(self): return 0
            def wait(self, timeout=None): return 0
            def terminate(self): pass
            def kill(self): pass

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            apk_path = tmp_path / "wff4.apk"
            _build_synthetic_resource_only_apk(apk_path)

            def run_scenario(out_name, wp_responses, power_responses):
                wp_idx = {"i": 0}
                pw_idx = {"i": 0}

                def runner(args, timeout=30, binary=False):
                    s = " ".join(args)
                    if "ro.boot.qemu.avd_name" in s: return SimpleNamespace(returncode=0, stdout="aura_wear36_round\n", stderr="")
                    if "sys.boot_completed" in s: return SimpleNamespace(returncode=0, stdout="1\n", stderr="")
                    if "ro.build.characteristics" in s: return SimpleNamespace(returncode=0, stdout="watch\n", stderr="")
                    if "ro.build.version.sdk" in s: return SimpleNamespace(returncode=0, stdout="36\n", stderr="")
                    if args[0] == "install": return SimpleNamespace(returncode=0, stdout="Success\n", stderr="")
                    if "pm list packages" in s: return SimpleNamespace(returncode=0, stdout=f"package:{pkg}\n", stderr="")
                    if "dumpsys wallpaper" in s:
                        out_s = wp_responses[min(wp_idx["i"], len(wp_responses) - 1)]
                        wp_idx["i"] += 1
                        return SimpleNamespace(returncode=0, stdout=out_s, stderr="")
                    if "dumpsys power" in s:
                        out_s = power_responses[min(pw_idx["i"], len(power_responses) - 1)]
                        pw_idx["i"] += 1
                        return SimpleNamespace(returncode=0, stdout=out_s, stderr="")
                    if "screencap" in s: return SimpleNamespace(returncode=0, stdout=valid_png, stderr=b"")
                    if args[0] == "pull":
                        Path(args[2]).write_bytes(valid_mp4)
                        return SimpleNamespace(returncode=0, stdout="1 file pulled\n", stderr="")
                    return SimpleNamespace(returncode=0, stdout="", stderr="")

                return execute_runtime_verification(
                    adb_bin=Path("adb"),
                    serial="emulator-5554",
                    apk_path=apk_path,
                    package_id=pkg,
                    wff_version=4,
                    output_dir=tmp_path / out_name,
                    expected_avd_name="aura_wear36_round",
                    runner=runner,
                    manifest_printer=lambda _: _valid_manifest_xml(pkg=pkg, min_sdk=36, wff_version=4),
                    recorder_factory=lambda: DoneRec(),
                    probe_runner=_ok_ffprobe_runner(12),
                    sleep_fn=lambda _: None,
                ), wp_idx["i"]

            on_s = "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n"
            aod_s = "mWakefulness=Dozing\nDisplay Id=0\nDisplay Power: state=DOZE_SUSPEND\n"

            # 1. Happy path checks dumpsys wallpaper at all 6 checkpoints (initial, active before/after, aod before/after, final restore)
            _, wp_count = run_scenario("ok", [good_wp] * 6, [on_s, on_s, aod_s, aod_s, on_s])
            self.assertEqual(6, wp_count)

            # 2. Watchface drifts right AFTER Active capture (3rd wallpaper query) -> MUST fail
            with self.assertRaises(RuntimeError) as ctx_drift_active:
                run_scenario("drift_active", [good_wp, good_wp, drifted_wp, good_wp], [on_s, on_s, on_s])
            self.assertIn("active_after", str(ctx_drift_active.exception))

            # 3. Screen state drops from ACTIVE to AOD right AFTER Active capture -> MUST fail
            with self.assertRaises(RuntimeError) as ctx_screen_drift:
                run_scenario("screen_drift", [good_wp] * 6, [on_s, aod_s, on_s])
            self.assertIn("active_after", str(ctx_screen_drift.exception))

            # 4. Watchface drifts right AFTER AOD capture (5th wallpaper query) -> MUST fail
            with self.assertRaises(RuntimeError) as ctx_drift_aod:
                run_scenario("drift_aod", [good_wp, good_wp, good_wp, good_wp, drifted_wp, good_wp], [on_s, on_s, aod_s, aod_s, on_s])
            self.assertIn("aod_after", str(ctx_drift_aod.exception))

            # 5. Watchface drifts at FINAL restore (6th wallpaper query) -> MUST fail (and recovery sees drift too)
            with self.assertRaises(RuntimeError):
                run_scenario("drift_final", [good_wp, good_wp, good_wp, good_wp, good_wp, drifted_wp], [on_s, on_s, aod_s, aod_s, on_s, on_s])

    def test_r06_aud09_early_recovery_spawn_failure_capture_failure_and_no_overwrite(self):
        """AG01-AUD-09: recovery starts at first device mutation, handles spawn/capture failure, and NEVER overwrites existing evidence."""
        pkg = "io.github.scarlel96.aura.watchface.wff4"
        valid_png = _build_valid_png_bytes(4, 4)
        on_s = "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n"
        good_wp = f"mCurrentUserId=0\n  WallpaperData 0 userId=0\n    mWallpaperComponent=ComponentInfo{{{pkg}/.WatchFace}}\n"

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            apk_path = tmp_path / "wff4.apk"
            _build_synthetic_resource_only_apk(apk_path)

            # 1. Existing evidence file MUST NOT be overwritten, and NO adb commands may run
            out_existing = tmp_path / "out_existing"
            out_existing.mkdir()
            existing_png = out_existing / "active_wff4.png"
            existing_png.write_bytes(b"ORIGINAL_EVIDENCE_BYTES")
            adb_called = []
            with self.assertRaises(EvidenceOverwriteError):
                execute_runtime_verification(
                    adb_bin=Path("adb"),
                    serial="emulator-5554",
                    apk_path=apk_path,
                    package_id=pkg,
                    wff_version=4,
                    output_dir=out_existing,
                    expected_avd_name="aura_wear36_round",
                    runner=lambda args, timeout=30, binary=False: adb_called.append(args),
                    manifest_printer=lambda _: _valid_manifest_xml(pkg=pkg, min_sdk=36, wff_version=4),
                    sleep_fn=lambda _: None,
                )
            self.assertEqual(b"ORIGINAL_EVIDENCE_BYTES", existing_png.read_bytes())
            self.assertEqual([], adb_called)

            # 2. Active capture failure (Step 4, before recorder even spawns) MUST trigger finally recovery (KEYCODE_WAKEUP + dumpsys check)
            cmds_cap = []

            def runner_cap_fail(args, timeout=30, binary=False):
                cmds_cap.append(" ".join(args))
                s = " ".join(args)
                if "ro.boot.qemu.avd_name" in s: return SimpleNamespace(returncode=0, stdout="aura_wear36_round\n", stderr="")
                if "sys.boot_completed" in s: return SimpleNamespace(returncode=0, stdout="1\n", stderr="")
                if "ro.build.characteristics" in s: return SimpleNamespace(returncode=0, stdout="watch\n", stderr="")
                if "ro.build.version.sdk" in s: return SimpleNamespace(returncode=0, stdout="36\n", stderr="")
                if args[0] == "install": return SimpleNamespace(returncode=0, stdout="Success\n", stderr="")
                if "pm list packages" in s: return SimpleNamespace(returncode=0, stdout=f"package:{pkg}\n", stderr="")
                if "dumpsys wallpaper" in s: return SimpleNamespace(returncode=0, stdout=good_wp, stderr="")
                if "dumpsys power" in s: return SimpleNamespace(returncode=0, stdout=on_s, stderr="")
                if "screencap" in s: return SimpleNamespace(returncode=1, stdout=b"", stderr=b"screencap crashed")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with self.assertRaises(RuntimeError) as cap_ctx:
                execute_runtime_verification(
                    adb_bin=Path("adb"),
                    serial="emulator-5554",
                    apk_path=apk_path,
                    package_id=pkg,
                    wff_version=4,
                    output_dir=tmp_path / "out_cap_fail",
                    expected_avd_name="aura_wear36_round",
                    runner=runner_cap_fail,
                    manifest_printer=lambda _: _valid_manifest_xml(pkg=pkg, min_sdk=36, wff_version=4),
                    sleep_fn=lambda _: None,
                )
            self.assertNotIsInstance(cap_ctx.exception, RecoveryFailureError)
            # Recovery ran a second KEYCODE_WAKEUP after Step 4 capture failed!
            self.assertEqual(2, sum(1 for c in cmds_cap if "KEYCODE_WAKEUP" in c))

            # 3. spawn_recorder() raises OSError -> MUST still run finally recovery (Awake+watchface + remote rm -f + test ! -e)
            cmds_spawn = []

            def runner_spawn_fail(args, timeout=30, binary=False):
                cmds_spawn.append(" ".join(args))
                s = " ".join(args)
                if "ro.boot.qemu.avd_name" in s: return SimpleNamespace(returncode=0, stdout="aura_wear36_round\n", stderr="")
                if "sys.boot_completed" in s: return SimpleNamespace(returncode=0, stdout="1\n", stderr="")
                if "ro.build.characteristics" in s: return SimpleNamespace(returncode=0, stdout="watch\n", stderr="")
                if "ro.build.version.sdk" in s: return SimpleNamespace(returncode=0, stdout="36\n", stderr="")
                if args[0] == "install": return SimpleNamespace(returncode=0, stdout="Success\n", stderr="")
                if "pm list packages" in s: return SimpleNamespace(returncode=0, stdout=f"package:{pkg}\n", stderr="")
                if "dumpsys wallpaper" in s: return SimpleNamespace(returncode=0, stdout=good_wp, stderr="")
                if "dumpsys power" in s: return SimpleNamespace(returncode=0, stdout=on_s, stderr="")
                if "screencap" in s: return SimpleNamespace(returncode=0, stdout=valid_png, stderr=b"")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            def broken_spawn():
                raise OSError("failed to spawn adb screenrecord")

            with self.assertRaises(OSError):
                execute_runtime_verification(
                    adb_bin=Path("adb"),
                    serial="emulator-5554",
                    apk_path=apk_path,
                    package_id=pkg,
                    wff_version=4,
                    output_dir=tmp_path / "out_spawn_fail",
                    expected_avd_name="aura_wear36_round",
                    runner=runner_spawn_fail,
                    manifest_printer=lambda _: _valid_manifest_xml(pkg=pkg, min_sdk=36, wff_version=4),
                    recorder_factory=broken_spawn,
                    sleep_fn=lambda _: None,
                )
            self.assertEqual(2, sum(1 for c in cmds_spawn if "KEYCODE_WAKEUP" in c))
            self.assertTrue(any("rm -f" in c for c in cmds_spawn))
            self.assertTrue(any("test ! -e" in c for c in cmds_spawn))

    def test_r07_staged_unlink_failure_never_blocks_recorder_awake_or_remote_cleanup(self):
        """AG-01-R07 §1: staged_video.unlink failure in finally must never block recorder termination, Awake recovery, or remote rm -f."""
        from unittest.mock import patch

        pkg = "io.github.scarlel96.aura.watchface.wff4"
        valid_png = _build_valid_png_bytes(4, 4)
        on_s = "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n"
        good_wp = f"mCurrentUserId=0\n  WallpaperData 0 userId=0\n    mWallpaperComponent=ComponentInfo{{{pkg}/.WatchFace}}\n"

        class TrackRecorder:
            def __init__(self):
                self.terminated = False
                self.waited = False

            def poll(self):
                return None if not self.terminated else 0

            def terminate(self):
                self.terminated = True

            def kill(self):
                self.terminated = True

            def wait(self, timeout=None):
                self.waited = True
                return 0

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            apk_path = tmp_path / "wff4.apk"
            _build_synthetic_resource_only_apk(apk_path)
            rec = TrackRecorder()
            cmds = []

            def runner(args, timeout=30, binary=False):
                cmds.append(" ".join(args))
                s = " ".join(args)
                if "ro.boot.qemu.avd_name" in s: return SimpleNamespace(returncode=0, stdout="aura_wear36_round\n", stderr="")
                if "sys.boot_completed" in s: return SimpleNamespace(returncode=0, stdout="1\n", stderr="")
                if "ro.build.characteristics" in s: return SimpleNamespace(returncode=0, stdout="watch\n", stderr="")
                if "ro.build.version.sdk" in s: return SimpleNamespace(returncode=0, stdout="36\n", stderr="")
                if args[0] == "install": return SimpleNamespace(returncode=0, stdout="Success\n", stderr="")
                if "pm list packages" in s: return SimpleNamespace(returncode=0, stdout=f"package:{pkg}\n", stderr="")
                if "dumpsys wallpaper" in s: return SimpleNamespace(returncode=0, stdout=good_wp, stderr="")
                if "dumpsys power" in s: return SimpleNamespace(returncode=0, stdout=on_s, stderr="")
                if "screencap" in s: return SimpleNamespace(returncode=0, stdout=valid_png, stderr=b"")
                if "KEYCODE_SLEEP" in s: return SimpleNamespace(returncode=1, stdout="", stderr="sleep failed")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            orig_unlink = Path.unlink

            def fail_tmp_unlink(path_obj, *a, **kw):
                if path_obj.name.endswith(".tmp"):
                    raise PermissionError("WinError 32: staged temp file locked")
                return orig_unlink(path_obj, *a, **kw)

            with patch.object(Path, "unlink", fail_tmp_unlink):
                with self.assertRaises(RecoveryFailureError) as ctx:
                    execute_runtime_verification(
                        adb_bin=Path("adb"),
                        serial="emulator-5554",
                        apk_path=apk_path,
                        package_id=pkg,
                        wff_version=4,
                        output_dir=tmp_path / "out_unlink_fail",
                        expected_avd_name="aura_wear36_round",
                        runner=runner,
                        manifest_printer=lambda _: _valid_manifest_xml(pkg=pkg, min_sdk=36, wff_version=4),
                        recorder_factory=lambda: rec,
                        sleep_fn=lambda _: None,
                    )

            # Recorder termination, Awake recovery wakeup, watchface recheck, and remote rm -f + test ! -e ALL ran!
            self.assertTrue(rec.terminated)
            self.assertTrue(rec.waited)
            self.assertTrue(ctx.exception.recovery_report["recorder_stopped"])
            self.assertTrue(ctx.exception.recovery_report["awake_restored"])
            self.assertTrue(ctx.exception.recovery_report["watchface_restored"])
            self.assertTrue(ctx.exception.recovery_report["remote_file_removed"])
            self.assertFalse(ctx.exception.recovery_report["staged_file_cleaned"])
            self.assertEqual(2, sum(1 for c in cmds if "KEYCODE_WAKEUP" in c))
            self.assertTrue(any("rm -f" in c for c in cmds))
            self.assertTrue(any("test ! -e" in c for c in cmds))
            self.assertIn("staged_cleanup_failed", " ".join(ctx.exception.recovery_errors))

    def test_r07_independent_recovery_steps_collect_all_errors_without_short_circuiting(self):
        """AG-01-R07 §2: every recovery step runs independently so one step's failure never short-circuits subsequent steps."""
        from unittest.mock import patch

        pkg = "io.github.scarlel96.aura.watchface.wff4"
        valid_png = _build_valid_png_bytes(4, 4)
        on_s = "mWakefulness=Awake\nDisplay Id=0\nDisplay Power: state=ON\n"
        good_wp = f"mCurrentUserId=0\n  WallpaperData 0 userId=0\n    mWallpaperComponent=ComponentInfo{{{pkg}/.WatchFace}}\n"

        class BrokenRecorder:
            def poll(self):
                return None

            def terminate(self):
                raise OSError("terminate syscall failed")

            def kill(self):
                raise OSError("kill syscall failed")

            def wait(self, timeout=None):
                raise subprocess.TimeoutExpired(cmd="screenrecord", timeout=timeout or 5)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            apk_path = tmp_path / "wff4.apk"
            _build_synthetic_resource_only_apk(apk_path)
            cmds = []
            sleep_seen = {"flag": False}

            def runner_all_fail(args, timeout=30, binary=False):
                cmds.append(" ".join(args))
                s = " ".join(args)
                if "ro.boot.qemu.avd_name" in s: return SimpleNamespace(returncode=0, stdout="aura_wear36_round\n", stderr="")
                if "sys.boot_completed" in s: return SimpleNamespace(returncode=0, stdout="1\n", stderr="")
                if "ro.build.characteristics" in s: return SimpleNamespace(returncode=0, stdout="watch\n", stderr="")
                if "ro.build.version.sdk" in s: return SimpleNamespace(returncode=0, stdout="36\n", stderr="")
                if args[0] == "install": return SimpleNamespace(returncode=0, stdout="Success\n", stderr="")
                if "pm list packages" in s: return SimpleNamespace(returncode=0, stdout=f"package:{pkg}\n", stderr="")
                if "KEYCODE_SLEEP" in s:
                    sleep_seen["flag"] = True
                    return SimpleNamespace(returncode=1, stdout="", stderr="sleep failed")
                if not sleep_seen["flag"]:
                    if "dumpsys wallpaper" in s: return SimpleNamespace(returncode=0, stdout=good_wp, stderr="")
                    if "dumpsys power" in s: return SimpleNamespace(returncode=0, stdout=on_s, stderr="")
                    if "screencap" in s: return SimpleNamespace(returncode=0, stdout=valid_png, stderr=b"")
                    return SimpleNamespace(returncode=0, stdout="", stderr="")
                # In recovery after KEYCODE_SLEEP failure, make every recovery sub-step fail independently
                if "KEYCODE_WAKEUP" in s:
                    return SimpleNamespace(returncode=1, stdout="", stderr="wakeup failed")
                if "dumpsys power" in s:
                    return SimpleNamespace(returncode=0, stdout="mWakefulness=Dozing\nDisplay Id=0\nDisplay Power: state=DOZE\n", stderr="")
                if "dumpsys wallpaper" in s:
                    return SimpleNamespace(returncode=0, stdout="mCurrentUserId=0\n  WallpaperData 0 userId=0\n    mWallpaperComponent=ComponentInfo{com.other/.Face}\n", stderr="")
                if "rm -f" in s:
                    return SimpleNamespace(returncode=1, stdout="", stderr="rm failed")
                if "test ! -e" in s:
                    return SimpleNamespace(returncode=1, stdout="", stderr="file still exists")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            orig_unlink = Path.unlink

            def fail_tmp_unlink(path_obj, *a, **kw):
                if path_obj.name.endswith(".tmp"):
                    raise PermissionError("staged unlink failed")
                return orig_unlink(path_obj, *a, **kw)

            with patch.object(Path, "unlink", fail_tmp_unlink):
                with self.assertRaises(RecoveryFailureError) as ctx:
                    execute_runtime_verification(
                        adb_bin=Path("adb"),
                        serial="emulator-5554",
                        apk_path=apk_path,
                        package_id=pkg,
                        wff_version=4,
                        output_dir=tmp_path / "out_all_rec_fail",
                        expected_avd_name="aura_wear36_round",
                        runner=runner_all_fail,
                        manifest_printer=lambda _: _valid_manifest_xml(pkg=pkg, min_sdk=36, wff_version=4),
                        recorder_factory=lambda: BrokenRecorder(),
                        sleep_fn=lambda _: None,
                    )

            joined = " | ".join(ctx.exception.recovery_errors)
            self.assertIn("recorder_terminate_call_failed", joined)
            self.assertIn("recorder_kill_call_failed", joined)
            self.assertIn("recorder_termination_failed", joined)
            self.assertIn("staged_cleanup_failed", joined)
            self.assertIn("awake_recovery_wakeup_failed", joined)
            self.assertIn("awake_recovery_failed", joined)
            self.assertIn("watchface_recovery_failed", joined)
            self.assertIn("remote_cleanup_failed", joined)
            self.assertIn("remote_absence_check_failed", joined)
            self.assertTrue(any("rm -f" in c for c in cmds))
            self.assertTrue(any("test ! -e" in c for c in cmds))

    def test_r07_mp4_duplicate_sample_tables_stsc_mismatch_and_chunk_span_overflow(self):
        """AG-01-R07 §3: reject duplicate sample tables, sample/chunk count mismatch, stsc mismatch, chunk overflow past mdat, and overlapping chunks."""
        ftyp = _mp4_box(b"ftyp", b"mp42\x00\x00\x00\x00mp42isom")
        mdat = _mp4_box(b"mdat", b"\x00" * 192)
        mdat_off = len(ftyp) + 8
        hdlr = _mp4_box(b"hdlr", b"\x00" * 8 + b"vide" + b"\x00" * 12 + b"Video\x00")
        stsd = _mp4_box(b"stsd", b"\x00" * 4 + struct.pack(">I", 1) + _mp4_box(b"avc1", b"\x00" * 24))

        def wrap_stbl(stbl_payload):
            return ftyp + mdat + _mp4_box(b"moov", _mp4_box(b"trak", _mp4_box(b"mdia", hdlr + _mp4_box(b"minf", _mp4_box(b"stbl", stbl_payload)))))

        stsz_bad = _mp4_box(b"stsz", b"\x00" * 4 + struct.pack(">II", 0, 0))
        stsz_2 = _mp4_box(b"stsz", b"\x00" * 4 + struct.pack(">II", 64, 2))
        stsz_3 = _mp4_box(b"stsz", b"\x00" * 4 + struct.pack(">II", 64, 3))
        stco_1 = _mp4_box(b"stco", b"\x00" * 4 + struct.pack(">II", 1, mdat_off))

        # 1. Duplicate stsz box -> MUST FAIL
        with self.assertRaises(RuntimeError):
            parse_and_validate_mp4_structure(wrap_stbl(stsd + stsz_bad + stsz_2 + stco_1))

        # 2. Both stco and co64 present simultaneously -> MUST FAIL
        co64_1 = _mp4_box(b"co64", b"\x00" * 4 + struct.pack(">IQ", 1, mdat_off))
        with self.assertRaises(RuntimeError):
            parse_and_validate_mp4_structure(wrap_stbl(stsd + stsz_2 + stco_1 + co64_1))

        # 3. Single chunk of 3x64B=192B starting 64B before mdat end (1st sample fits, 2nd & 3rd overflow past mdat) -> MUST FAIL
        stco_overflow = _mp4_box(b"stco", b"\x00" * 4 + struct.pack(">II", 1, mdat_off + 192 - 64))
        with self.assertRaises(RuntimeError):
            parse_and_validate_mp4_structure(wrap_stbl(stsd + stsz_3 + stco_overflow))

        # 4. More chunks (3 chunks) than total samples (2 samples) -> MUST FAIL
        stco_3 = _mp4_box(b"stco", b"\x00" * 4 + struct.pack(">IIII", 3, mdat_off, mdat_off + 64, mdat_off + 128))
        with self.assertRaises(RuntimeError):
            parse_and_validate_mp4_structure(wrap_stbl(stsd + stsz_2 + stco_3))

        # 5. Multiple chunks (2 chunks) missing required stsc box -> MUST FAIL
        stco_2 = _mp4_box(b"stco", b"\x00" * 4 + struct.pack(">III", 2, mdat_off, mdat_off + 64))
        with self.assertRaises(RuntimeError):
            parse_and_validate_mp4_structure(wrap_stbl(stsd + stsz_2 + stco_2))

        # 6. stsc mapped sample total (2 chunks * 2 samples = 4) != stsz sample_count (3) -> MUST FAIL
        stsc_2_each = _mp4_box(b"stsc", b"\x00" * 4 + struct.pack(">IIII", 1, 1, 2, 1))
        with self.assertRaises(RuntimeError):
            parse_and_validate_mp4_structure(wrap_stbl(stsd + stsz_3 + stsc_2_each + stco_2))

        # 7. Overlapping chunk byte spans in mdat (chunk 1 at [mdat_off, mdat_off+128), chunk 2 at [mdat_off+64, mdat_off+128)) -> MUST FAIL
        stsc_2_then_1 = _mp4_box(b"stsc", b"\x00" * 4 + struct.pack(">IIIIIII", 2, 1, 2, 1, 2, 1, 1))
        with self.assertRaises(RuntimeError):
            parse_and_validate_mp4_structure(wrap_stbl(stsd + stsz_3 + stsc_2_then_1 + stco_2))

        # 8. Valid multi-chunk MP4 (chunk 1 has 2 samples [0..128), chunk 2 has 1 sample [128..192)) -> PASS
        stco_2_valid = _mp4_box(b"stco", b"\x00" * 4 + struct.pack(">III", 2, mdat_off, mdat_off + 128))
        ok_multi = parse_and_validate_mp4_structure(wrap_stbl(stsd + stsz_3 + stsc_2_then_1 + stco_2_valid))
        self.assertEqual(3, ok_multi["sample_count"])

    def test_r07_ffprobe_missing_codec_type_stderr_decode_errors_and_partial_frame_rejection(self):
        """AG-01-R07 §4: reject missing codec_type, non-empty stderr decode errors, and partial frame decoding (decoded < container samples)."""
        with tempfile.TemporaryDirectory() as tmp:
            mp4_file = Path(tmp) / "clip24.mp4"
            mp4_file.write_bytes(_build_valid_mp4_bytes(sample_count=24, sample_size=64))

            # 1. Missing codec_type in ffprobe stream JSON -> MUST FAIL
            with self.assertRaises(RuntimeError):
                verify_mp4_video_artifact(
                    mp4_file,
                    probe_runner=lambda cmd, timeout=60: SimpleNamespace(
                        returncode=0,
                        stdout='{"streams":[{"codec_name":"h264","width":454,"height":454,"nb_read_frames":"24"}]}',
                        stderr="",
                    ),
                )

            # 2. Decode error diagnostic on stderr despite rc=0 and 24 frames -> MUST FAIL
            with self.assertRaises(RuntimeError):
                verify_mp4_video_artifact(
                    mp4_file,
                    probe_runner=lambda cmd, timeout=60: SimpleNamespace(
                        returncode=0,
                        stdout='{"streams":[{"codec_type":"video","codec_name":"h264","width":454,"height":454,"nb_read_frames":"24"}]}',
                        stderr="[h264 @ 0x1] error while decoding MB 4 8\n",
                    ),
                )

            # 3. Partial decoding: container has 24 samples, ffprobe decoded only 5 frames -> MUST FAIL
            with self.assertRaises(RuntimeError) as partial_ctx:
                verify_mp4_video_artifact(
                    mp4_file,
                    probe_runner=lambda cmd, timeout=60: SimpleNamespace(
                        returncode=0,
                        stdout='{"streams":[{"codec_type":"video","codec_name":"h264","width":454,"height":454,"nb_frames":"24","nb_read_frames":"5"}]}',
                        stderr="",
                    ),
                )
            self.assertIn("Partial video decoding", str(partial_ctx.exception))

            # 4. Header nb_frames (20) disagrees with container stsz sample_count (24) -> MUST FAIL
            with self.assertRaises(RuntimeError):
                verify_mp4_video_artifact(
                    mp4_file,
                    probe_runner=lambda cmd, timeout=60: SimpleNamespace(
                        returncode=0,
                        stdout='{"streams":[{"codec_type":"video","codec_name":"h264","width":454,"height":454,"nb_frames":"20","nb_read_frames":"24"}]}',
                        stderr="",
                    ),
                )

            # 5. Full decoding: all 24 frames decoded with 0 stderr errors and codec_type='video' -> VERIFIED
            ok = verify_mp4_video_artifact(
                mp4_file,
                probe_runner=lambda cmd, timeout=60: SimpleNamespace(
                    returncode=0,
                    stdout='{"streams":[{"codec_type":"video","codec_name":"h264","width":454,"height":454,"nb_frames":"24","nb_read_frames":"24"}]}',
                    stderr="",
                ),
            )
            self.assertEqual("VERIFIED", ok["status"])
            self.assertEqual(24, ok["decoded_frame_count"])
            self.assertEqual(24, ok["expected_frame_count"])

    def test_r07_display_parser_never_bleeds_previous_display_id_across_section_boundaries(self):
        """AG-01-R07 §5: display parser must reset current Display ID at blank lines, section headers, outdents, and inline DisplayDeviceInfo."""
        # 1. Logical Display 0 has no state; blank line + separate unscoped Display Power Controller has state=ON -> MUST be UNKNOWN
        bleed_blank = (
            "mWakefulness=Awake\n"
            "Logical Display 0:\n"
            "  mLayerStack=0\n"
            "\n"
            "Display Power Controller:\n"
            "  Display Power: state=ON\n"
        )
        r1 = parse_power_and_display_state(bleed_blank)
        self.assertEqual("UNKNOWN", r1["status"])
        self.assertFalse(r1["is_active"])
        self.assertEqual([], r1["display_states_by_id"]["0"])
        self.assertEqual(["ON"], r1["unscoped_display_states"])

        # 2. Same without blank line: sibling section header 'Display Power Controller:' resets Logical Display 0 scope -> UNKNOWN
        bleed_header = (
            "mWakefulness=Awake\n"
            "Logical Display 0:\n"
            "  mLayerStack=0\n"
            "Display Power Controller:\n"
            "  Display Power: state=ON\n"
        )
        r2 = parse_power_and_display_state(bleed_header)
        self.assertEqual("UNKNOWN", r2["status"])
        self.assertFalse(r2["is_active"])
        self.assertEqual([], r2["display_states_by_id"]["0"])

        # 3. Inline DisplayDeviceInfo with displayId 0 followed by inline DisplayDeviceInfo without displayId -> never attributed to 0 -> UNKNOWN
        inline_bleed = (
            "mWakefulness=Awake\n"
            "DisplayDeviceInfo{\"Built-in\": uniqueId=\"local:0\", displayId 0, state ON}\n"
            "DisplayDeviceInfo{\"HDMI\": uniqueId=\"local:1\", state DOZE}\n"
        )
        r3 = parse_power_and_display_state(inline_bleed)
        self.assertEqual("UNKNOWN", r3["status"])
        self.assertFalse(r3["is_active"])
        self.assertEqual(["ON"], r3["display_states_by_id"]["0"])
        self.assertEqual(["DOZE"], r3["unscoped_display_states"])

        # 4. Outdented state line after indented '  Display Id=0' block -> resets scope -> UNKNOWN
        outdent_bleed = (
            "mWakefulness=Awake\n"
            "  Display Id=0\n"
            "    mLayerStack=0\n"
            "Display Power: state=ON\n"
        )
        r4 = parse_power_and_display_state(outdent_bleed)
        self.assertEqual("UNKNOWN", r4["status"])
        self.assertFalse(r4["is_active"])
        self.assertEqual([], r4["display_states_by_id"]["0"])

        # 5 (G5 self-review): Indented sub-header inside 'Logical Display 0:' block preserves Display Id=0 scope -> ACTIVE
        nested_ok = (
            "mWakefulness=Awake\n"
            "Logical Display 0:\n"
            "  SubSection Details:\n"
            "    Display State: ON\n"
        )
        r5 = parse_power_and_display_state(nested_ok)
        self.assertEqual("ACTIVE", r5["status"])
        self.assertTrue(r5["is_active"])
        self.assertEqual(["ON"], r5["display_states_by_id"]["0"])


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
