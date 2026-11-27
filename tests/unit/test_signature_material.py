"""Check the static WFF material candidate and APK payload rejection."""
import io
import json
import sys
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import signature_material as s
from test_material_foundation import decode


class SignatureMaterialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.xml,cls.png,cls.report=s.generate()
        cls.basic=s.basic()[s.BASIC]
        cls.layout=s.parse_layout((s.ROOT/s.LAYOUT).read_bytes())

    def test_reproducible(self):
        self.assertEqual(s.generate(),(self.xml,self.png,self.report))

    def test_png_contrast_and_budget(self):
        w,h,data=decode(self.png)
        self.assertEqual([w,h],self.report["panelDimensions"])
        self.assertEqual(s.digest(data),self.report["panelRgbaSha256"])
        self.assertEqual(s.visual.check_contrast(data,s.visual.PANEL_COLORS),self.report["panelContrast"])
        self.assertLessEqual(2*len(data),100000)

    def test_geometry_and_ambient(self):
        s.check_face(self.xml,self.basic,self.layout)
        root=ET.fromstring(self.xml)
        self.assertEqual(len(root.findall(".//Line")),60)
        self.assertEqual(len(root.findall(".//PartImage")),2)
        self.assertEqual(len(root.findall(".//TimeText")),2)

    def test_reject_missing_ambient(self):
        root=ET.fromstring(self.xml)
        group=root.find("Scene/Group")
        group.remove(group[0])
        with self.assertRaises(ValueError):
            s.check_face(ET.tostring(root),self.basic,self.layout)

    def test_reject_wrong_reference(self):
        root=ET.fromstring(self.xml)
        root.find(".//PartImage/Image").set("resource","other")
        with self.assertRaises(ValueError):
            s.check_face(ET.tostring(root),self.basic,self.layout)

    def test_reject_changed_information(self):
        root=ET.fromstring(self.xml)
        root.find(".//TimeText").set("hourFormat","HOUR_FORMAT_24")
        with self.assertRaises(ValueError):
            s.check_face(ET.tostring(root),self.basic,self.layout)

    def test_apk_payload(self):
        def archive(xml,png):
            stream=io.BytesIO()
            with zipfile.ZipFile(stream,"w") as z:
                z.writestr("res/raw/watchface.xml",xml)
                z.writestr(s.PNG_PATH,png)
            return zipfile.ZipFile(stream)
        with archive(self.xml,self.png) as z:
            s.inspect_material_apk(z,self.xml,self.png)
        for xml,png in ((self.basic,self.png),(self.xml,b"wrong")):
            with archive(xml,png) as z, self.assertRaises(ValueError):
                s.inspect_material_apk(z,self.xml,self.png)

    def test_scope(self):
        self.assertEqual(self.report["runtimeVerification"],"NOT RUN")
        print("SIGNATURE_MATERIAL_RESULT "+json.dumps(self.report,sort_keys=True))
