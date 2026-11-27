"""Test the round geometry contract and failure detection."""
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from round_layout import ROOT, SOURCE, DIAMETERS, parse, project, project_layout, inside_circle, separated, generate


class RoundLayoutTests(unittest.TestCase):
    def setUp(self):
        self.raw = (ROOT / SOURCE).read_bytes()
        self.layout = parse(self.raw)

    def reject(self, change):
        t = copy.deepcopy(self.layout)
        change(t)
        with self.assertRaises(ValueError):
            parse(json.dumps(t))

    def test_all_diameters(self):
        for size in DIAMETERS:
            with self.subTest(size=size):
                result = project_layout(self.layout, size)
                self.assertEqual(len(result["regions"]), 9)
                self.assertEqual(set(result["ambientRegions"]), {"time", "date", "ampm"})
                self.assertEqual(result["regions"]["time"], result["ambientRegions"]["time"])

    def test_projection_rounds_outward(self):
        self.assertEqual(project([1,1,1,1], 432), [0,0,2,2])

    def test_exact_circle_boundary(self):
        self.assertTrue(inside_circle([225,12,1,1], 450, 11))
        self.assertFalse(inside_circle([0,0,1,1], 450, 12))

    def test_gap_boundary(self):
        self.assertTrue(separated([0,0,10,10], [18,0,10,10], 8))
        self.assertFalse(separated([0,0,10,10], [17,0,10,10], 8))

    def test_missing_diameter(self):
        self.reject(lambda t: t["diameters"].pop())

    def test_duplicate_field(self):
        with self.assertRaises(ValueError):
            parse('{"schemaVersion":1,"schemaVersion":1}')

    def test_wrong_type(self):
        self.reject(lambda t: t.update(safeInset=True))

    def test_off_circle(self):
        self.reject(lambda t: t["regions"].update(brand=[0,0,160,24]))

    def test_collision(self):
        self.reject(lambda t: t["regions"].update(date=t["regions"]["battery"]))

    def test_no_time_ambient(self):
        self.reject(lambda t: t.update(ambient=["date"]))

    def test_wrong_font(self):
        self.reject(lambda t: t["fontSizes"].update(time=120))

    def test_missing_region(self):
        self.reject(lambda t: t["regions"].pop("heart"))

    def test_unverified_diameter(self):
        with self.assertRaises(ValueError):
            project_layout(self.layout, 500)

    def test_deterministic(self):
        self.assertEqual(generate(), generate())
        self.assertEqual(len(generate()), 5)

    def test_core_rectangles_unchanged(self):
        self.assertEqual(self.layout["regions"]["time"], [44,124,362,110])
        self.assertEqual(self.layout["regions"]["date"], [90,78,174,32])

    def test_ampm_region_is_required(self):
        self.reject(lambda t: t["regions"].pop("ampm"))
