"""Test geometry, layers, vector topology and reproducibility."""
import copy
import hashlib
import json
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
from titanium_ring import (ROOT,SOURCE,LAYOUT,OBJECTS,MATERIAL,DIAMETERS,PROFILES,
                          DIRECTIONS,parse,generate,geometry,svg,point)
from round_layout import parse as parse_layout
from motion_object_paths import parse_objects
from material_foundation import parse as parse_material

NS="{http://www.w3.org/2000/svg}"


class TitaniumRingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t=parse((ROOT/SOURCE).read_bytes())
        cls.l=parse_layout((ROOT/LAYOUT).read_bytes())
        cls.o=parse_objects((ROOT/OBJECTS).read_bytes())
        cls.m=parse_material((ROOT/MATERIAL).read_bytes())
        cls.report,cls.outputs=generate()

    def test_matrix(self):
        self.assertEqual(self.report["assetCount"],16)
        self.assertEqual(self.report["regionChecks"],36)
        self.assertEqual(self.report["tickRegionChecks"],2160)
        self.assertEqual(self.report["shortenedMajorIndices"],[10,50])
        self.assertEqual(set(self.outputs),{(d,p) for d in DIAMETERS for p in PROFILES})
        self.assertEqual(self.report["runtimeVerification"],"NOT RUN")
        print("TITANIUM_RING_RESULT "+json.dumps(self.report,sort_keys=True))

    def test_svg_hashes_and_dimensions(self):
        for (d,p),data in self.outputs.items():
            root=ET.fromstring(data)
            self.assertEqual(root.attrib["width"],str(d))
            self.assertEqual(root.attrib["height"],str(d))
            self.assertEqual(root.attrib["viewBox"],"0 0 450 450")
            self.assertEqual(hashlib.sha256(data).hexdigest(),
                             self.report["screens"][str(d)]["profiles"][p]["sha256"])
            self.assertEqual(len(data),self.report["screens"][str(d)]["profiles"][p]["bytes"])

    def test_profile_layers(self):
        for (d,p),data in self.outputs.items():
            r=ET.fromstring(data)
            if p=="AOD":
                self.assertEqual([x.tag for x in r],[NS+"title"])
            else:
                self.assertEqual(len(r.findall(".//"+NS+"circle")),4)
                self.assertEqual(len(r.findall(".//"+NS+"line")),60)
                self.assertEqual(len(r.findall(".//"+NS+"path")),int(p!="ECO"))
            self.assertFalse(r.findall(".//"+NS+"image"))

    def test_tick_directions_and_major_count(self):
        self.assertEqual(len(set(DIRECTIONS)),60)
        r=ET.fromstring(self.outputs[(480,"ULTRA")])
        lines=r.findall(".//"+NS+"line")
        self.assertEqual(sum(x.attrib["stroke-width"]=="1.000000" for x in lines),12)
        self.assertEqual([x.attrib["id"] for x in lines],[f"tick-{i}" for i in range(60)])
        self.assertEqual(point(209,DIRECTIONS[0]),("225.000000","16.000000"))
        self.assertEqual(point(209,DIRECTIONS[15]),("434.000000","225.000000"))
        for x,y in DIRECTIONS:
            self.assertLess(abs(x*x+y*y-10**12),2000000)

    def test_serialized_tick_bounds(self):
        r=ET.fromstring(self.outputs[(498,"BALANCED")])
        for i,line in enumerate(r.findall(".//"+NS+"line")):
            v=line.attrib
            inner=207 if i in (10,50) or i%5 else 205
            for a,b,radius in (("x1","y1",inner),("x2","y2",209)):
                x,y=Fraction(v[a])-225,Fraction(v[b])-225
                self.assertLess(abs(x*x+y*y-radius*radius),Fraction(1,2))

    def test_ring_band_stroke_bounds(self):
        r=ET.fromstring(self.outputs[(432,"ULTRA")])
        bounds=[]
        for c in r.findall(".//"+NS+"circle"):
            radius=Fraction(c.attrib["r"])
            half=Fraction(c.attrib["stroke-width"])/2
            bounds.append((radius-half,radius+half))
        self.assertEqual(bounds[0][0],210)
        self.assertEqual(bounds[-1][1],212)
        self.assertTrue(all(a[1]==b[0] for a,b in zip(bounds,bounds[1:])))

    def test_geometry_all_screens(self):
        for d in DIAMETERS:
            self.assertEqual(geometry(self.t,self.l,self.o,self.m,d)["regionChecks"],9)

    def test_reject_layout_collision(self):
        l=copy.deepcopy(self.l)
        # The normal rectangle check permits this near-edge rectangle.
        l["regions"]["brand"]=[205,13,40,6]
        l["fontSizes"]["brand"]=5
        with self.assertRaises(ValueError):
            geometry(self.t,l,self.o,self.m,480)

    def test_reject_ring_motion_or_light_disagreement(self):
        o=copy.deepcopy(self.o)
        o["ringOuterEnd"]=213
        with self.assertRaisesRegex(ValueError,"M01 band mismatch"):
            geometry(self.t,self.l,o,self.m,480)
        m=copy.deepcopy(self.m)
        m["lighting"]["angleDegrees"]=30
        with self.assertRaisesRegex(ValueError,"Inconsistent shared light"):
            geometry(self.t,self.l,self.o,m,480)

    def test_reject_unsafe_stroke(self):
        t=copy.deepcopy(self.t)
        t["ticks"]["outer"]=210
        with self.assertRaisesRegex(ValueError,"Tick overlaps"):
            geometry(t,self.l,self.o,self.m,432)
        t=copy.deepcopy(self.t)
        t["highlight"]["widthMilli"]=4000
        with self.assertRaisesRegex(ValueError,"Highlight outside"):
            geometry(t,self.l,self.o,self.m,432)

    def test_reject_invalid_tokens(self):
        for edit in (lambda t:t["ring"].update(machiningBands=0),
                     lambda t:t["ticks"].update(count=True),
                     lambda t:t["highlight"].update(opacityPermille=601),
                     lambda t:t["ring"].update(trackColors=["#FFFFFF"]),
                     lambda t:t["profiles"].update(AOD=["ring"]),
                     lambda t:t["lighting"].update(angleDegrees=45.0)):
            t=copy.deepcopy(self.t)
            edit(t)
            with self.assertRaises(ValueError):
                parse(json.dumps(t))
        with self.assertRaises(ValueError):
            parse('{"schemaVersion":1,"schemaVersion":1}')
        with self.assertRaises(ValueError):
            svg(self.t,433,"ULTRA")

    def test_determinism_separate_process(self):
        self.assertEqual((self.report,self.outputs),generate())
        cmd=[sys.executable,str(ROOT/"tools/titanium_ring.py")]
        result=subprocess.run(cmd+["--manifest"],cwd=ROOT,capture_output=True,check=True,timeout=30)
        self.assertEqual(json.loads(result.stdout),self.report)
        result=subprocess.run(cmd+["--svg","498","ECO"],cwd=ROOT,capture_output=True,check=True,timeout=30)
        self.assertEqual(result.stdout,self.outputs[(498,"ECO")])

    def test_original_unshortened_ticks_rejected(self):
        t=copy.deepcopy(self.t)
        t["ticks"]["shortenedMajorIndices"]=[]
        for d in DIAMETERS:
            with self.assertRaisesRegex(ValueError,"Tick 10 intersects reserved information bounds: time"):
                geometry(t,self.l,self.o,self.m,d)
        t["ticks"]["shortenedMajorIndices"]=[10]
        for d in DIAMETERS:
            with self.assertRaisesRegex(ValueError,"Tick 50 intersects reserved information bounds: time"):
                geometry(t,self.l,self.o,self.m,d)

    def test_shortening_contract_rejects_invalid_indices(self):
        for indices in ([10,10],[50,10],[1],[60],[True],"10"):
            t=copy.deepcopy(self.t)
            t["ticks"]["shortenedMajorIndices"]=indices
            with self.assertRaises(ValueError):
                parse(json.dumps(t))

    def test_serialized_all_tick_clearances(self):
        # Independently check the actual serialized line endpoints, in pixels.
        from round_layout import project_layout
        for d in DIAMETERS:
            boxes=project_layout(self.l,d)["regions"]
            root=ET.fromstring(self.outputs[(d,"ULTRA")])
            scale=Fraction(d,450)
            for line in root.findall(".//"+NS+"line"):
                a=line.attrib
                x1,y1,x2,y2=(Fraction(a[k])*scale for k in ("x1","y1","x2","y2"))
                margin=Fraction(a["stroke-width"])*scale/2+1
                for name,(x,y,w,h) in boxes.items():
                    self.assertTrue(max(x1,x2)+margin<x or min(x1,x2)-margin>x+w
                                    or max(y1,y2)+margin<y or min(y1,y2)-margin>y+h,
                                    (d,a["id"],name))
