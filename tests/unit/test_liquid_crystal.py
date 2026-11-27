"""Verify Liquid Crystal host asset contracts and error detection."""
import copy
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
from liquid_crystal import ROOT,SOURCE,MATERIAL,MODES,PROFILES,DIAMETERS
from liquid_crystal import parse,render,generate,offset
from material_foundation import parse as parse_material
from test_material_foundation import decode


class LiquidCrystalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = parse((ROOT/SOURCE).read_bytes())
        cls.asset = parse_material((ROOT/MATERIAL).read_bytes())["assets"]["glass"]
        cls.report,cls.outputs = generate()

    def test_asset_matrix(self):
        self.assertEqual(self.report["assetCount"],8)
        self.assertEqual(set(self.outputs),{(d,m) for d in DIAMETERS for m in MODES})

    def test_png_decode_and_hash(self):
        for (d,m),data in self.outputs.items():
            w,h,rgba=decode(data)
            entry=self.report["screens"][str(d)]["assets"][m]
            self.assertEqual((w,h,len(rgba)),(entry["width"],entry["height"],entry["rgbaBytes"]))
            self.assertEqual(hashlib.sha256(data).hexdigest(),entry["sha256"])
            self.assertEqual(hashlib.sha256(rgba).hexdigest(),entry["rgbaSha256"])

    def test_pixel_channel_bound_and_mask(self):
        for data in self.outputs.values():
            w,h,rgba=decode(data)
            for i in range(0,len(rgba),4):
                self.assertLessEqual(max(rgba[i:i+3]),self.t["maxChannel"])
                if rgba[i+3]==0:
                    self.assertEqual(rgba[i:i+4],bytes(4))
            self.assertEqual(rgba[:4],bytes(4))
            self.assertTrue(any(0<a<255 for a in rgba[3::4]))

    def test_refraction_differs_from_static(self):
        for d in DIAMETERS:
            self.assertNotEqual(self.outputs[d,"REFRACTED"],self.outputs[d,"STATIC"])
            entries=self.report["screens"][str(d)]["assets"]
            self.assertEqual(entries["STATIC"]["maxShiftPixels"],0)
            self.assertGreater(entries["REFRACTED"]["maxShiftPixels"],0)
            self.assertLessEqual(entries["REFRACTED"]["maxShiftPixels"],4)

    def test_offset_is_symmetric_and_bounded(self):
        for n in (50,57,152,175):
            for i in range(n):
                self.assertEqual(offset(i,n,4),-offset(n-1-i,n,4))
                self.assertLessEqual(abs(offset(i,n,4)),4)
                self.assertEqual(offset(i,n,0),0)

    def test_panel_geometry_and_budget(self):
        for s in self.report["screens"].values():
            self.assertEqual(set(s["panels"]),{"weather","heart"})
            self.assertEqual(s["sharedRgbaBytes"]["AOD"],0)
            self.assertEqual(s["duplicateRgbaBytes"]["AOD"],0)
            for p,m in PROFILES.items():
                if m is not None:
                    self.assertLessEqual(s["sharedRgbaBytes"][p],100000)
                    self.assertEqual(s["duplicateRgbaBytes"][p]-s["sharedRgbaBytes"][p],
                                     s["assets"][m]["rgbaBytes"])

    def test_invalid_contract(self):
        for edit in (lambda t:t.update(displacementLogical=4),
                     lambda t:t.update(maxChannel=255),
                     lambda t:t["lighting"].update(angleDegrees=30),
                     lambda t:t.update(panelRegions=["time","heart"]),
                     lambda t:t["profiles"].update(AOD="STATIC"),
                     lambda t:t.update(schemaVersion=True)):
            t=copy.deepcopy(self.t)
            edit(t)
            with self.assertRaises(ValueError):
                parse(json.dumps(t))
        with self.assertRaises(ValueError):
            parse('{"schemaVersion":1,"schemaVersion":1}')

    def test_invalid_mode_and_resolution(self):
        for d,m in ((432,"AOD"),(433,"STATIC"),(432,"unknown")):
            with self.assertRaises(ValueError):
                render(self.t,self.asset,d,m)

    def test_independent_process_reproduction(self):
        command=[sys.executable,str(ROOT/"tools/liquid_crystal.py")]
        result=subprocess.run(command+["--manifest"],cwd=ROOT,capture_output=True,check=True,timeout=60)
        self.assertEqual(json.loads(result.stdout),self.report)
        result=subprocess.run(command+["--png","498","REFRACTED"],cwd=ROOT,capture_output=True,check=True,timeout=60)
        self.assertEqual(result.stdout,self.outputs[498,"REFRACTED"])

    def test_runtime_scope(self):
        self.assertEqual(self.report["runtimeVerification"],"NOT RUN")
        self.assertIn("not WFF resources",self.report["scope"])
        print("LIQUID_CRYSTAL_RESULT "+json.dumps(self.report,sort_keys=True))
