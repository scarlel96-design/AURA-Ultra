"""Unit and schema regression suite for AG-01 WFF 2-5 PoC fixtures and verification tooling."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

AG01_DIR = Path(__file__).resolve().parent
ROOT = AG01_DIR.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(AG01_DIR))

from run_ag01_verification import (
    NEGATIVE_SPECS,
    POC_SPECS,
    ensure_validator_jar,
    require_rejection,
    run_validator_utf8,
)
from verify_wff import require_pass

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
                # Verify active decoration suppression in AMBIENT mode
                ambient_zero = [
                    v for v in root.findall(".//Group/Variant")
                    if v.get("mode") == "AMBIENT" and v.get("target") == "alpha" and v.get("value") == "0"
                ]
                self.assertGreaterEqual(len(ambient_zero), 1)

    def test_single_clock_continuity_object_in_aod_pocs(self):
        """Ensure AOD transition PoCs transform a single DigitalClock/TimeText object rather than crossfading duplicate clocks."""
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
        """Verify startOffset + duration <= 1.0 (so startOffset is never ignored) and all 6 official interpolations are covered."""
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
            self.assertLessEqual(round(start_offset + duration, 6), 1.0,
                                 f"startOffset ({start_offset}) + duration ({duration}) > 1.0 causes WFF4 parser to ignore startOffset")
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
        """Verify <Reference> elements obey WFF4 parent rules, unique naming, non-circularity, and drive multiple elements."""
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
            # Ensure no self-circular reference on the same element's transforms
            for tr in parent.findall("Transform"):
                self.assertNotIn(f"[REFERENCE.{name}]", tr.get("value", ""))
            names.append(name)
        self.assertEqual(len(names), len(set(names)), "Reference names must be unique within document")
        for name in names:
            self.assertIn(f"[REFERENCE.{name}]", xml_text, f"Published Reference {name} is never consumed")
        # Ensure missing data fallback uses '--' rather than '0'
        self.assertIn("--", xml_text)

    def test_wff4_motion_triggers_gyro_and_per_digit_time_formats(self):
        """Verify Gyro uses only sensorSourceType and TimeText uses official per-digit formats (hh_10, hh_1, mm_10, mm_1)."""
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
        """Verify WFF 5 PoC exercises Group blendMode, ComplicationSlot blendMode, Stroke join, Font minSize, Text lineSpacing."""
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

    def test_rejection_helper_detects_unexpected_pass_and_inconclusive_output(self):
        """G2 verification: ensure require_rejection catches false passes and missing error strings."""
        face = POC_SPECS[0]["path"].resolve()
        pass_line = f"INFO: ✅  PASSED : {face} is valid against watch face format version #2"
        with self.assertRaises(ValueError):
            require_rejection(0, pass_line)
        with self.assertRaises(ValueError):
            require_rejection(0, "INFO: WFF Validation Application Version 1.7.0")
        with self.assertRaises(ValueError):
            require_rejection(1, "SEVERE: unrelated error", expected_error="blendMode")
        require_rejection(1, "SEVERE: Attribute 'blendMode' is not allowed", expected_error="blendMode")

    def test_detects_variant_window_overflow_and_invalid_reference_parent(self):
        """G2/G5 review regression: verify negative fixture 7 violates both startOffset+duration<=1.0 and Reference parent constraints."""
        neg7 = next(s for s in NEGATIVE_SPECS if s["id"] == "neg_wff4_invalid_variant_and_reference_parent")
        root = ET.parse(neg7["path"]).getroot()
        variants = root.findall(".//Variant")
        self.assertTrue(any(float(v.get("startOffset", "0")) + float(v.get("duration", "1")) > 1.0 for v in variants))
        parent_map = {child: parent for parent in root.iter() for child in parent}
        refs = root.findall(".//Reference")
        self.assertTrue(any(parent_map[r].tag in PROHIBITED_REFERENCE_PARENTS for r in refs))



class Ag01OfficialValidatorMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jar = ensure_validator_jar()

    def test_positive_pocs_across_all_wff_versions(self):
        """Verify all 6 PoCs pass on their supported WFF versions and fail when leaked into lower WFF versions."""
        for spec in POC_SPECS:
            for version in (2, 3, 4, 5):
                with self.subTest(poc=spec["id"], wff_version=version):
                    proc = run_validator_utf8(self.jar, spec["path"], version)
                    if version >= spec["min_version"]:
                        require_pass(proc.returncode, proc.stdout, spec["path"], version)
                    else:
                        require_rejection(proc.returncode, proc.stdout)

    def test_negative_fixtures_across_all_wff_versions(self):
        """Verify all 7 negative fixtures are rejected on lower/invalid versions and accepted only where valid."""
        for spec in NEGATIVE_SPECS:
            for version in (2, 3, 4, 5):
                with self.subTest(fixture=spec["id"], wff_version=version):
                    proc = run_validator_utf8(self.jar, spec["path"], version)
                    if version in spec["fail_versions"]:
                        expected_err = spec["expected_error"] if version == max(spec["fail_versions"]) else None
                        require_rejection(proc.returncode, proc.stdout, expected_err)
                    else:
                        require_pass(proc.returncode, proc.stdout, spec["path"], version)


if __name__ == "__main__":
    unittest.main()
