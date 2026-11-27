"""Exercise the experimental centered-time and annulus paths."""
import copy
import json
import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
from motion_object_paths import (load,scene,validate_scene,audit_objects,parse_objects,
                                 DIAMETERS)


class MotionObjectPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layout,cls.motion,cls.obj = load()

    def sample(self,tick,direction="wake",profile=4,reduced=False):
        return scene(self.layout,self.motion,self.obj,tick,direction,profile,reduced)

    def test_all_positions(self):
        result = audit_objects(self.layout,self.motion,self.obj)
        self.assertEqual(result["geometryChecks"],4004)
        self.assertEqual(result["reverseChecks"],1001)
        self.assertEqual(result["runtimeVerification"],"NOT RUN")
        print("MOTION_OBJECT_RESULT "+json.dumps(result,sort_keys=True))

    def test_time_center_then_scale(self):
        a,b,c = (self.sample(t) for t in (0,250,850))
        self.assertEqual(a["regions"]["time"]["box"],[85,183,280,84])
        self.assertEqual(b["regions"]["time"]["box"],[85,137,280,84])
        self.assertEqual(c["regions"]["time"]["box"],self.layout["regions"]["time"])
        self.assertEqual([x["timeFont"] for x in (a,b,c)],[81,81,96])
        self.assertEqual(b["regions"]["ampm"]["box"],self.layout["regions"]["ampm"])

    def test_ring_expands(self):
        a,b,c = (self.sample(t)["ring"] for t in (100,550,1000))
        self.assertEqual([x["outer"] for x in (a,b,c)],[211,Fraction(423,2),212])
        self.assertEqual([x["sweep"] for x in (a,b,c)],[60,210,360])
        self.assertEqual([x["alpha"] for x in (a,b,c)],[0,Fraction(1,2),1])

    def test_highlight_formation(self):
        a,b,c = (self.sample(t)["highlight"] for t in (150,475,800))
        self.assertEqual([x["alpha"] for x in (a,b,c)],[0,Fraction(3,10),Fraction(3,5)])
        self.assertEqual([x["sweep"] for x in (a,b,c)],[0,Fraction(25,2),25])

    def test_static_and_reduced(self):
        for profile,reduced in ((2,False),(3,False),(4,True),(5,True)):
            for direction in ("wake","sleep"):
                v = self.sample(500,direction,profile,reduced)
                self.assertEqual(v["regions"]["time"]["box"],self.layout["regions"]["time"])
                self.assertEqual(v["highlight"]["alpha"],0)
                self.assertEqual(v,self.sample(0,direction,profile,reduced))
                for d in DIAMETERS:
                    validate_scene(self.layout,v,d)

    def test_ambient_core_only(self):
        a = self.sample(0)
        self.assertEqual({n for n,s in a["regions"].items() if s["alpha"]>0},
                         {"time","date","ampm"})
        self.assertEqual(a["ring"]["alpha"],0)
        self.assertEqual(a["highlight"]["alpha"],0)

    def test_core_hidden_rejected(self):
        a = self.sample(500)
        a["regions"]["time"]["alpha"] = 0
        with self.assertRaisesRegex(ValueError,"Hidden core"):
            validate_scene(self.layout,a,432)

    def test_collision_rejected(self):
        a = self.sample(500)
        a["regions"]["ampm"]["box"] = list(a["regions"]["time"]["box"])
        with self.assertRaisesRegex(ValueError,"insufficient gap"):
            validate_scene(self.layout,a,480)

    def test_ring_outside_rejected(self):
        a = self.sample(1000)
        a["ring"]["outer"] = 225
        with self.assertRaisesRegex(ValueError,"Arc outside"):
            validate_scene(self.layout,a,498)

    def test_ring_overlap_rejected(self):
        a = self.sample(1000)
        a["ring"]["inner"] = 100
        with self.assertRaisesRegex(ValueError,"Ring intersects"):
            validate_scene(self.layout,a,498)

    def test_highlight_outside_rejected(self):
        a = self.sample(500)
        a["highlight"]["start"] = -180
        with self.assertRaisesRegex(ValueError,"Highlight outside"):
            validate_scene(self.layout,a,438)

    def test_bad_contract_rejected(self):
        for key,value in (("translationEnd",251),("ambientTime",[1,1,280,84]),
                          ("ambientFont",109),("ringOuterEnd",214),("highlightMaxSweep",46),
                          ("schemaVersion",True)):
            x = copy.deepcopy(self.obj)
            x[key] = value
            with self.assertRaises(ValueError):
                parse_objects(json.dumps(x))

    def test_font_bounds_rejected(self):
        a = self.sample(0)
        a["timeFont"] = 96
        with self.assertRaisesRegex(ValueError,"font"):
            validate_scene(self.layout,a,432)
