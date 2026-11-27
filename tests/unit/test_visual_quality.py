"""Check material composition, contrast rejection and lossless compression."""
import base64
import hashlib
import json
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import visual_quality as v
from test_material_foundation import decode


class VisualQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report,cls.frames,cls.assets=v.generate()

    def test_matrix(self):
        self.assertEqual(len(self.assets),36)
        self.assertEqual(self.report["assetCount"],36)
        samples=v.preview.scenarios()
        expected=4*sum(1 if s["ambient"] else 4 for s in samples)+16
        self.assertEqual(len(self.frames),expected)
        self.assertEqual(self.report["previewCount"],expected)

    def test_lossless_and_budget(self):
        for k,png in self.assets.items():
            w,h,data=decode(png)
            r=self.report["assets"][k]
            self.assertEqual((w,h,len(data)),(r["width"],r["height"],r["rgbaBytes"]))
            self.assertEqual(hashlib.sha256(data).hexdigest(),r["rgbaSha256"])
            self.assertEqual(hashlib.sha256(png).hexdigest(),r["sha256"])
            self.assertLessEqual(len(png),r["storedBytes"])
            self.assertEqual(r["duplicateRgbaBytes"],2*len(data))
            self.assertLessEqual(2*len(data),100000)

    def test_contrast_recomputed(self):
        for k,png in self.assets.items():
            _,_,rgba=decode(png)
            self.assertEqual(v.check_contrast(rgba,v.PANEL_COLORS),self.report["assets"][k]["contrast"])

    def test_contrast_negative(self):
        for data,colors in ((bytes([170,186,203,255]),["#A9BACB"]),
                            (bytes([0,0,0,0]),["#FFFFFF"]),(b"",["#FFFFFF"]),
                            (bytes([0,0,0,255]),[])):
            with self.assertRaises(ValueError):
                v.check_contrast(data,colors)

    def test_tilt_and_eco(self):
        for d in v.DIAMETERS:
            for p in ("ULTRA","BALANCED"):
                self.assertNotEqual(self.assets[f"{d}/{p}/negative"],self.assets[f"{d}/{p}/positive"])
            self.assertEqual(self.assets[f"{d}/ECO/negative"],self.assets[f"{d}/ECO/positive"])

    def test_embedded_assets_and_text(self):
        xml=v.basic()[v.BASIC]
        samples={s["name"]:s for s in v.preview.scenarios()}
        for k,svg in self.frames.items():
            d,p,name,tilt=k.split("/")
            root=ET.fromstring(svg)
            images=root.findall(v.Q+"image")
            plain=p in ("AOD","HIGH_CONTRAST")
            self.assertEqual(len(images),0 if plain else 2)
            self.assertEqual(len(root.findall(v.Q+"svg")),0 if plain else 1)
            for img in images:
                self.assertEqual(base64.b64decode(img.get("href").split(",",1)[1]),
                                 self.assets[f"{d}/{p}/{tilt}"])
            items=v.preview.collect(xml,samples[name])
            self.assertEqual([x.text for x in root.findall(v.Q+"text")],[i["text"] for i in items])
            old=ET.fromstring(v.preview.render(items,samples[name],int(d)))
            for a,b in zip(root.findall(v.Q+"text"),old.findall(v.Q+"text")):
                self.assertEqual({k:x for k,x in a.attrib.items() if k!="fill"},
                                 {k:x for k,x in b.attrib.items() if k!="fill"})
                self.assertEqual(a.get("fill"),"#FFFFFF" if p=="HIGH_CONTRAST" else b.get("fill"))
            self.assertEqual(hashlib.sha256(svg).hexdigest(),self.report["previewHashes"][k])

    def test_ambient_and_scope(self):
        self.assertEqual(self.report["ambientMaterialBytes"],0)
        self.assertEqual(self.report["runtimeVerification"],"NOT RUN")
        self.assertIn("no glyph",self.report["scope"])

    def test_independent_process(self):
        cmd=[sys.executable,str(v.ROOT/"tools/visual_quality.py"),"--manifest"]
        result=subprocess.run(cmd,cwd=v.ROOT,capture_output=True,check=True,timeout=120)
        self.assertEqual(json.loads(result.stdout),self.report)
        print("VISUAL_QUALITY_RESULT "+json.dumps(self.report,sort_keys=True))
