"""Regression tests for WFF verdicts and APK inspection."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from verify_wff import require_pass
from check_apk import inspect_entries, inspect_manifest

FACE = Path("watchface.xml").resolve()
HEADER = "INFO: WFF Validation Application Version 1.7.0. Maximum Supported Format Version #5"
VALID = f"INFO: ✅  PASSED : {FACE} is valid against watch face format version #2"
PROFILE = {"name": "wff2", "version": 2, "minSdk": 34}
MANIFEST = """<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="io.github.scarlel96.aura.watchface.wff2">
    <uses-sdk android:minSdkVersion="34"/>
    <uses-feature android:name="android.hardware.type.watch" android:required="true"/>
    <application android:hasCode="false">
        <property android:name="com.google.wear.watchface.format.version" android:value="2"/>
    </application>
</manifest>"""


class ValidatorTests(unittest.TestCase):
    def test_explicit_success(self):
        require_pass(0, HEADER + "\n" + VALID, FACE, 2)

    def test_header_only(self):
        with self.assertRaises(ValueError):
            require_pass(0, HEADER, FACE, 2)

    def test_empty_output(self):
        with self.assertRaises(ValueError):
            require_pass(0, "", FACE, 2)

    def test_nonzero_exit(self):
        with self.assertRaises(ValueError):
            require_pass(1, VALID, FACE, 2)

    def test_explicit_failure(self):
        with self.assertRaises(ValueError):
            require_pass(0, VALID + "\nERROR: FAILED", FACE, 2)

    def test_wrong_version(self):
        with self.assertRaises(ValueError):
            require_pass(0, VALID, FACE, 3)

    def test_wrong_path(self):
        with self.assertRaises(ValueError):
            require_pass(0, VALID, FACE.parent / "other.xml", 2)

    def test_duplicate_verdict(self):
        with self.assertRaises(ValueError):
            require_pass(0, VALID + "\n" + VALID, FACE, 2)


class ApkTests(unittest.TestCase):
    def test_resource_only(self):
        self.assertEqual([], inspect_entries(["AndroidManifest.xml", "resources.arsc", "res/raw/watchface.xml"]))

    def test_dex_native_and_jar(self):
        entries = ["AndroidManifest.xml", "resources.arsc", "classes.dex", "classes2.dex", "lib/a/libx.so", "assets/a.jar"]
        errors = inspect_entries(entries)
        for name in entries[2:]:
            self.assertTrue(any(name in error for error in errors))

    def test_missing_and_duplicate(self):
        errors = inspect_entries(["AndroidManifest.xml", "AndroidManifest.xml"])
        self.assertTrue(any("Missing" in e for e in errors))
        self.assertTrue(any("Duplicate" in e for e in errors))

    def test_invalid_path(self):
        self.assertTrue(any("Invalid" in e for e in inspect_entries(["../x"])))

    def test_valid_manifest(self):
        self.assertEqual([], inspect_manifest(MANIFEST, PROFILE))

    def test_wrong_package(self):
        self.assertTrue(any("package" in e for e in inspect_manifest(MANIFEST.replace(".wff2", ".wff3"), PROFILE)))

    def test_wrong_sdk(self):
        self.assertTrue(any("minSdk" in e for e in inspect_manifest(MANIFEST.replace('"34"', '"33"'), PROFILE)))

    def test_wrong_version(self):
        self.assertTrue(any("WFF version" in e for e in inspect_manifest(MANIFEST.replace('android:value="2"', 'android:value="3"'), PROFILE)))

    def test_has_code(self):
        self.assertTrue(any("hasCode" in e for e in inspect_manifest(MANIFEST.replace('hasCode="false"', 'hasCode="true"'), PROFILE)))

    def test_component(self):
        self.assertTrue(any("component" in e for e in inspect_manifest(MANIFEST.replace("</application>", '<service android:name=".Bad"/></application>'), PROFILE)))

    def test_permission(self):
        self.assertTrue(any("permission" in e for e in inspect_manifest(MANIFEST.replace("<uses-sdk", '<uses-permission android:name="android.permission.INTERNET"/><uses-sdk'), PROFILE)))


if __name__ == "__main__":
    unittest.main()
