"""Verify optical depth samples, fixed geometry and fail-closed policy."""
import copy
import hashlib
import json
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
from optical_depth import ROOT,SOURCE,LAYOUT,DIAMETERS,PROFILES,CASES,parse,state,generate,svg,verify_geometry
from round_layout import parse as parse_layout

NS="{http://www.w3.org/2000/svg}"


class OpticalDepthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t=parse((ROOT/SOURCE).read_bytes())
        cls.layout=parse_layout((ROOT/LAYOUT).read_bytes())
        cls.report,cls.frames=generate()

    def test_matrix(self):
        self.assertEqual(len(self.frames),176)
        self.assertEqual(self.report["sampleCount"],176)

    def test_depth_order(self):
        for p,scale in (("ULTRA",6),("BALANCED",3)):
            s=state(self.t,p,1000,-1000)["layers"]
            self.assertEqual(s["reflection"],[scale,-scale])
            self.assertLess(s["atmosphere"][0],s["material"][0])
            self.assertLess(s["material"][0],s["reflection"][0])

    def test_symmetry_and_bounds(self):
        for x in range(-1000,1001,25):
            a=state(self.t,"ULTRA",x,-x)["layers"]
            b=state(self.t,"ULTRA",-x,x)["layers"]
            for k,v in a.items():
                self.assertEqual(v,[-z for z in b[k]])
                self.assertLessEqual(max(map(abs,v)),self.t["depth"][k])

    def test_static_fallbacks(self):
        for p in PROFILES:
            for x,y,reduced in ((None,None,False),(1000,-1000,True)):
                s=state(self.t,p,x,y,reduced)
                self.assertNotEqual(s["mode"],"DYNAMIC")
                self.assertTrue(all(v==[0,0] for v in s["layers"].values()))
                if reduced:
                    self.assertNotIn("reflection",s["layers"])
        self.assertNotIn("reflection",state(self.t,"ECO",1000,1000)["layers"])

    def test_ambient_no_layers(self):
        for k,data in self.frames.items():
            if "/AOD/" in k:
                root=ET.fromstring(data)
                self.assertEqual([v.tag for v in root],[NS+"title"])
                self.assertEqual(self.report["samples"][k]["state"]["layers"],{})

    def test_fixed_geometry_and_clipping(self):
        for k,data in self.frames.items():
            d=int(k.split("/")[0])
            self.assertEqual(self.report["samples"][k]["regions"],
                             verify_geometry(self.t,self.layout,d)["regions"])
            root=ET.fromstring(data)
            for group in root.findall(NS+"g"):
                name=group.get("id")
                self.assertEqual(group.get("clip-path"),f"url(#clip-{name})")
                x,y,w,h=self.layout["regions"][name]
                for rect in group.findall(NS+"rect"):
                    a,b,c,e=[int(rect.get(q)) for q in ("x","y","width","height")]
                    self.assertTrue(x<=a and y<=b and a+c<=x+w and b+e<=y+h)
            self.assertFalse(root.findall(".//"+NS+"text"))
            self.assertEqual(hashlib.sha256(data).hexdigest(),self.report["samples"][k]["sha256"])

    def test_dynamic_reference_changes(self):
        for d in DIAMETERS:
            self.assertNotEqual(self.frames[f"{d}/ULTRA/0"],self.frames[f"{d}/ULTRA/8"])
            self.assertEqual(self.frames[f"{d}/ECO/0"],self.frames[f"{d}/ECO/8"])

    def test_reject_invalid_inputs(self):
        for args in (("ULTRA",1001,0),("ULTRA",True,0),("ULTRA",None,0),
                     ("unknown",0,0),("ULTRA",0,0,1)):
            with self.assertRaises(ValueError):
                state(self.t,*args)
        for edit in (lambda t:t["depth"].update(reflection=7),
                     lambda t:t["depth"].update(material=6),
                     lambda t:t["balancedDepth"].update(reflection=4),
                     lambda t:t["highlight"].update(peakOpacityMilli=181),
                     lambda t:t.update(panels=["time","heart"])):
            t=copy.deepcopy(self.t)
            edit(t)
            with self.assertRaises(ValueError):
                parse(json.dumps(t))

    def test_unsafe_geometry_rejected(self):
        t=copy.deepcopy(self.t)
        t["highlight"]["box"]=[150,10,80,12]
        for d in DIAMETERS:
            with self.assertRaisesRegex(ValueError,"Highlight leaves panel"):
                verify_geometry(t,self.layout,d)

    def test_independent_process(self):
        cmd=[sys.executable,str(ROOT/"tools/optical_depth.py")]
        p=subprocess.run(cmd+["--svg","480","ULTRA","8"],cwd=ROOT,capture_output=True,check=True,timeout=60)
        self.assertEqual(p.stdout,self.frames["480/ULTRA/8"])
        p=subprocess.run(cmd+["--check"],cwd=ROOT,capture_output=True,check=True,timeout=60)
        self.assertIn(b"OPTICAL_DEPTH_RESULT",p.stdout)
        self.assertEqual(self.report["runtimeVerification"],"NOT RUN")
        print(p.stdout.decode().strip())
