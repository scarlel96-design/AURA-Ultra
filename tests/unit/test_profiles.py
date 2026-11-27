"""Exercise profile validation and resource selection."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from profile_contract import validate_profiles, load_profiles, debug_tasks, face_source, check_source_sets, debug_apk


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.config = {"schemaVersion": 1, "logicalSize": 450, "profiles": copy.deepcopy(load_profiles())}
        self.profile = self.config["profiles"][0]

    def test_valid(self):
        self.assertEqual([2, 3, 4, 5], [p["version"] for p in validate_profiles(self.config)])

    def test_missing_profile(self):
        self.config["profiles"].pop()
        with self.assertRaises(ValueError):
            validate_profiles(self.config)

    def test_duplicate(self):
        self.config["profiles"].append(self.profile)
        with self.assertRaises(ValueError):
            validate_profiles(self.config)

    def test_wrong_api(self):
        self.profile["minSdk"] = 33
        with self.assertRaises(ValueError):
            validate_profiles(self.config)

    def test_wrong_name(self):
        self.profile["name"] = "../escape"
        with self.assertRaises(ValueError):
            validate_profiles(self.config)

    def test_disabled_baseline(self):
        self.profile.update(enabled=False, reason="test")
        with self.assertRaises(ValueError):
            validate_profiles(self.config)

    def test_non_boolean(self):
        self.profile["enabled"] = "true"
        with self.assertRaises(ValueError):
            validate_profiles(self.config)

    def test_build_tasks(self):
        profiles = [p for p in validate_profiles(self.config) if p["enabled"]]
        self.assertEqual([":apps:watchface:assembleWff2Debug", ":apps:watchface:assembleWff3Debug", ":apps:watchface:assembleWff4Debug"], debug_tasks(profiles))

    def test_overlay_and_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory)
            common = app / "src/main/res/raw/watchface.xml"
            common.parent.mkdir(parents=True)
            common.write_text("common")
            self.assertEqual(common, face_source(self.profile, app))
            override = app / "src/wff2/res/raw/watchface.xml"
            override.parent.mkdir(parents=True)
            override.write_text("override")
            self.assertEqual(override, face_source(self.profile, app))
            check_source_sets(self.config["profiles"], app)

    def test_untracked_override(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory)
            path = app / "src/debug/res/raw/watchface.xml"
            path.parent.mkdir(parents=True)
            path.touch()
            with self.assertRaises(ValueError):
                check_source_sets(self.config["profiles"], app)

    def test_missing_or_duplicate_apk(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory)
            with self.assertRaises(ValueError):
                debug_apk(self.profile, app)
            output = app / "build/outputs/apk/wff2/debug"
            output.mkdir(parents=True)
            (output / "one.apk").touch()
            self.assertEqual(output / "one.apk", debug_apk(self.profile, app))
            (output / "two.apk").touch()
            with self.assertRaises(ValueError):
                debug_apk(self.profile, app)
