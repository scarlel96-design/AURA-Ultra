"""F01 R01 regressions for the four audited validation gaps."""
import dataclasses
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import signature_material as material
import fluid_digits as digits
import check_foundation as foundation
import check_apk
import profile_contract as profiles


class F01SignatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.xml, cls.png, cls.report = material.generate()
        cls.original = material.basic()[material.BASIC]
        cls.layout = material.parse_layout((ROOT / material.LAYOUT).read_bytes())

    def test_normal_artifact_preserved(self):
        material.check_face(self.xml, self.original, self.layout)
        self.assertEqual(material.digest(self.xml), "fe355897238beecc2e19ad9602fe0f82d0e3a75447644a118bbf63a4320c71de")
        self.assertEqual(material.digest(self.png), "0ca25941c01f013440698b81252025b7cb6e349e440a61325f7ba3d754da5d8c")

    def reject(self, edit):
        root = ET.fromstring(self.xml)
        edit(root)
        with self.assertRaises(ValueError):
            material.check_face(ET.tostring(root), self.original, self.layout)

    def test_duplicate_ticks(self):
        def edit(root):
            lines = root.findall(".//PartDraw/Line")
            for line in lines[1:]:
                line.attrib = dict(lines[0].attrib)
        self.reject(edit)

    def test_hidden_ring(self):
        self.reject(lambda r: r.find(".//PartDraw").set("alpha", "0"))

    def test_center_intrusion(self):
        self.reject(lambda r: r.find(".//PartDraw/Line").attrib.update(
            startX="225", startY="225", endX="226", endY="226"))

    def test_arc_angle(self):
        self.reject(lambda r: r.find(".//PartDraw/Arc").set("startAngle", "0"))

    def test_gradient_color(self):
        self.reject(lambda r: r.find(".//LinearGradient").set("colors", "#FF000000 #FF000000 #FF000000 #FF000000 #FF000000"))

    def test_template_tail(self):
        def edit(root):
            template = root.find(".//Template")
            self.assertIsNotNone(template)
            self.assertGreater(len(template), 0)
            template[0].tail = "WRONG"
        self.reject(edit)

    def test_unexpected_draw_child(self):
        self.reject(lambda r: ET.SubElement(r.find(".//PartDraw"), "Variant",
                                             mode="AMBIENT", target="alpha", value="1"))

    def test_indentation_is_not_content(self):
        root = ET.fromstring(self.xml)
        ET.indent(root, space="  ")
        material.check_face(ET.tostring(root), self.original, self.layout)


class F01FluidTests(unittest.TestCase):
    def setUp(self):
        self.old = digits.ClockSample(datetime(2026, 1, 1, 10, 8), 0, "audit", True)
        self.new = digits.ClockSample(datetime(2026, 1, 1, 10, 9), 0, "audit", True)
        self.valid = digits.plan(self.old, self.new)

    def test_forged_metadata(self):
        forged = dataclasses.replace(self.valid, duration_ms=5000, changed=(), reason="forged")
        with self.assertRaises(ValueError):
            digits.verify_frame(forged, 100, digits.digit_frame(forged, 100))

    def test_each_invalid_field(self):
        for kwargs in ({"duration_ms": 5000}, {"duration_ms": True},
                       {"changed": ()}, {"changed": (True,)},
                       {"reason": "forged"}, {"reason": "zone-change"},
                       {"reason": "static-policy"}):
            with self.subTest(kwargs=kwargs):
                forged = dataclasses.replace(self.valid, **kwargs)
                with self.assertRaises(ValueError):
                    digits.verify_frame(forged, 100, digits.digit_frame(forged, 100))

    def test_valid_policies(self):
        for kwargs in ({}, {"ambient": True}, {"profile": 2}, {"reduced": True},
                       {"resync": True}, {"interrupted": True}):
            transition = digits.plan(self.old, self.new, **kwargs)
            digits.verify_frame(transition, 100, digits.digit_frame(transition, 100))


class F01ManifestTests(unittest.TestCase):
    def test_source_and_compiled_reject(self):
        import shutil
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            app = root / "apps/watchface"
            shutil.copytree(ROOT / "apps/watchface/src", app / "src")
            shutil.copy2(ROOT / "apps/watchface/build.gradle.kts", app)
            shutil.copytree(ROOT / "design-system", root / "design-system")
            path = app / "src/main/AndroidManifest.xml"
            original = path.read_text(encoding="utf-8")
            with patch.multiple(foundation, ROOT=root, APP=app, RES=app / "src/main/res",
                  load_profiles=lambda: profiles.load_profiles(ROOT),
                  face_source=lambda p: profiles.face_source(p, app),
                  check_source_sets=lambda p: profiles.check_source_sets(p, app)):
                foundation.check()
                for tag, xml in (
                    ("receiver", '<receiver android:name=".Audit" android:exported="false"/>'),
                    ("provider", '<provider android:name=".Audit" android:authorities="audit.test"/>'),
                    ("activity-alias", '<activity-alias android:name=".Audit" android:targetActivity=".Other"/>'),
                    ("duplicate-property", '<property android:name="com.google.wear.watchface.format.version" android:value="5"/>'),
                ):
                    with self.subTest(tag=tag):
                        modified = original.replace("</application>", xml + "</application>")
                        path.write_text(modified, encoding="utf-8")
                        with self.assertRaises(ValueError):
                            foundation.check()
                        compiled = modified.replace("<manifest ", '<manifest package="io.github.scarlel96.aura.watchface.wff4" ').replace(
                            "<application ", '<uses-sdk android:minSdkVersion="36"/><application ').replace(
                            "$" + "{wffVersion}", "4")
                        self.assertTrue(check_apk.inspect_manifest(compiled, {"name": "wff4", "version": 4, "minSdk": 36}))
                modified = original.replace("<application ", '<uses-permission-sdk-23 android:name="android.permission.INTERNET"/><application ')
                path.write_text(modified, encoding="utf-8")
                with self.assertRaises(ValueError):
                    foundation.check()
                compiled = modified.replace("<manifest ", '<manifest package="io.github.scarlel96.aura.watchface.wff4" ').replace(
                    "<application ", '<uses-sdk android:minSdkVersion="36"/><application ').replace("$" + "{wffVersion}", "4")
                self.assertTrue(check_apk.inspect_manifest(compiled, {"name": "wff4", "version": 4, "minSdk": 36}))


class F01ProfileTests(unittest.TestCase):
    def test_duplicate_keys(self):
        import re
        original = (ROOT / "compatibility/profiles.json").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "compatibility/profiles.json"
            path.parent.mkdir()
            for key, value in (("schemaVersion", "1"), ("version", "2")):
                changed = re.sub(r'"' + key + r'"\s*:\s*' + value,
                                 '"' + key + '": 999, "' + key + '": ' + value, original, count=1)
                self.assertNotEqual(original, changed)
                path.write_text(changed, encoding="utf-8")
                with self.subTest(key=key), self.assertRaises(ValueError):
                    profiles.load_profiles(root)
            path.write_text(original, encoding="utf-8")
            self.assertEqual([2, 3, 4, 5], [p["version"] for p in profiles.load_profiles(root)])
