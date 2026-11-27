"""Test the M01 host reference and its failure detection."""
import copy
import json
import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/"tools"))
from motion_contract import (ROOT, SOURCE, LAYOUT, MAX, CORE, WINDOWS,
                             parse_motion, parse, ease, frame, audit, check_frame,
                             position, inset_box)


class MotionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (ROOT/SOURCE).read_bytes()
        cls.motion = parse_motion(cls.raw)
        cls.layout = parse((ROOT/LAYOUT).read_bytes())

    def test_all_positions_and_diameters(self):
        result = audit(self.layout, self.motion)
        self.assertEqual(result["geometryChecks"], 4004)
        self.assertEqual(result["reverseChecks"], 1001)
        self.assertEqual(result["runtimeVerification"], "NOT RUN")

    def test_exact_window_endpoints(self):
        for start,end in WINDOWS.values():
            self.assertEqual(ease(start,[start,end]),0)
            self.assertEqual(ease(end,[start,end]),1)
            self.assertEqual(ease((start+end)//2,[start,end]),Fraction(1,2))

    def test_monotonic_no_overshoot(self):
        for window in WINDOWS.values():
            values = [ease(i,window) for i in range(MAX+1)]
            self.assertEqual(values,sorted(values))
            self.assertTrue(all(0 <= x <= 1 for x in values))

    def test_core_preserved(self):
        for t in (0,250,500,999,1000):
            result = frame(self.layout,self.motion,t)
            for name in CORE:
                self.assertEqual(result[name]["box"],self.layout["regions"][name])
                self.assertEqual(result[name]["alpha"],1)

    def test_panel_expansion_not_only_fade(self):
        a = frame(self.layout,self.motion,0)["weather"]
        b = frame(self.layout,self.motion,1000)["weather"]
        self.assertLess(a["box"][2],b["box"][2])
        self.assertEqual(b["box"],self.layout["regions"]["weather"])
        self.assertEqual((a["alpha"],b["alpha"]),(0,1))

    def test_reentry_exact_position(self):
        for t in (1,250,449,500,900,999):
            self.assertEqual(frame(self.layout,self.motion,t),
                             frame(self.layout,self.motion,MAX-t,"sleep"))

    def test_static_fallback_and_reduced(self):
        for profile in (2,3,4,5):
            for reduced in (False,True):
                if profile >= 4 and not reduced:
                    continue
                for direction, p in (("wake",1000),("sleep",0)):
                    self.assertEqual(frame(self.layout,self.motion,500,direction,profile,reduced),
                                     frame(self.layout,self.motion,p))

    def test_invalid_progress_and_profile(self):
        for tick in (-1,1001,True,0.5):
            with self.assertRaises(ValueError):
                position(tick,"wake",4,False)
        for profile in (1,6,True):
            with self.assertRaises(ValueError):
                position(0,"wake",profile,False)
        with self.assertRaises(ValueError):
            position(0,"bad",4,False)

    def test_invalid_contract(self):
        for field,value in (("schemaVersion",True),("progressMax",999),("panelInset",0)):
            data = copy.deepcopy(self.motion)
            data[field] = value
            with self.assertRaises(ValueError):
                parse_motion(json.dumps(data))
        with self.assertRaises(ValueError):
            parse_motion(self.raw.replace(b'"schemaVersion": 1',b'"schemaVersion": 1, "schemaVersion": 1'))

    def test_changed_window_rejected(self):
        data = copy.deepcopy(self.motion)
        data["windows"]["time"] = [0,900]
        with self.assertRaises(ValueError):
            parse_motion(json.dumps(data))

    def test_core_hiding_rejected(self):
        states = frame(self.layout,self.motion,500)
        states["time"]["alpha"] = 0
        with self.assertRaisesRegex(ValueError,"Core region"):
            check_frame(self.layout,states,432)

    def test_outside_reserved_region_rejected(self):
        states = frame(self.layout,self.motion,500)
        states["weather"]["box"][0] -= 100
        with self.assertRaisesRegex(ValueError,"reserved rectangle"):
            check_frame(self.layout,states,480)

    def test_alpha_and_collapsed_box_rejected(self):
        states = frame(self.layout,self.motion,500)
        states["weather"]["alpha"] = Fraction(2)
        with self.assertRaisesRegex(ValueError,"Alpha"):
            check_frame(self.layout,states,498)
        with self.assertRaisesRegex(ValueError,"collapses"):
            inset_box([1,1,4,4],2)
