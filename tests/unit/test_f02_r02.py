"""Exercise both basic candidate build entry points with disposable Git inputs."""
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_basic_face_build as basic
from committed_build_inputs import git


class BasicSnapshotTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.parent = Path(temp.name)
        self.root = self.parent / "source"
        self.root.mkdir()
        git(self.root, "init", "-q")
        for key, value in (("user.name", "AURA fixture"),
                           ("user.email", "fixture@example.invalid"),
                           ("commit.gpgsign", "false"), ("core.autocrlf", "false")):
            git(self.root, "config", key, value)
        self.original = b"<WatchFace/>"
        self.candidate = b"<WatchFace width='450'/>"
        for name, data in ((basic.FACE, self.original), ("gradlew", b"wrapper\n"),
                           ("tools/input.py", b"original\n"),
                           ("apps/watchface/build.gradle.kts", b"fixture\n")):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "fixture")
        self.source = git(self.root, "rev-parse", "HEAD").decode().strip()
        cache = self.root / ".aura-tools"
        cache.mkdir()
        for name in ("wff-validator.jar", "memory-footprint.jar", "extra.jar"):
            (cache / name).write_bytes(b"fixture")
        self.bundle = self.parent / "candidate.zip"
        self.profiles = [{"name": "wff" + str(n)} for n in range(2, 6)]

    def run_build(self, bundle=False, dirty_during=False, bad_generation=False):
        calls = []
        argv = ["check_basic_face_build.py"]
        if bundle:
            argv += ["--development-bundle", str(self.bundle)]

        def apk(profile, app):
            return app / (profile["name"] + ".apk")

        def run(snapshot, tool, *args):
            calls.append((tool, args))
            if tool == "generate_basic_face.py" and args == ("--write",):
                path = snapshot / basic.OUTPUT
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"bad" if bad_generation else self.candidate)
            elif tool == "verify_wff.py":
                self.assertEqual((snapshot / "tools/input.py").read_bytes(), b"original\n")
                self.assertFalse((snapshot / "tools/untracked.py").exists())
                self.assertEqual({p.name for p in (snapshot / ".aura-tools").iterdir()},
                                 {"wff-validator.jar", "memory-footprint.jar"})
                self.assertEqual((snapshot / basic.FACE).read_bytes(), self.candidate)
            elif tool == "build_profiles.py" and args == ("assemble",):
                for profile in self.profiles:
                    with zipfile.ZipFile(apk(profile, snapshot / "apps/watchface"), "w") as z:
                        z.writestr("res/raw/watchface.xml", self.candidate)
            elif tool == "build_profiles.py" and args == ("signatures",) and dirty_during:
                (self.root / "tools/input.py").write_bytes(b"changed during build\n")

        with patch.object(sys, "argv", argv), \
             patch.object(basic, "ROOT", self.root), \
             patch.object(basic, "FILES", ("gradlew",)), \
             patch.object(basic, "DIRECTORIES", ("tools", "apps/watchface/src")), \
             patch.object(basic, "generate", return_value={basic.OUTPUT: self.candidate}) as generate, \
             patch.object(basic, "check_outputs"), \
             patch.object(basic, "run", side_effect=run), \
             patch.object(basic, "enabled_profiles", return_value=self.profiles), \
             patch.object(basic, "debug_apk", side_effect=apk), \
             patch.object(basic, "build_bundle", return_value=(b"bundle", {"sourceCommit": self.source})) as build, \
             patch.object(basic, "verify_bundle", return_value={"sourceCommit": self.source}):
            basic.main()
            generate.assert_called_once()
            if bundle:
                build.assert_called_once()
                self.assertEqual(build.call_args.args[2], self.source)
            else:
                build.assert_not_called()
        return calls

    def test_nonbundle_uses_committed_inputs(self):
        (self.root / "tools/untracked.py").write_bytes(b"untracked")
        calls = self.run_build()
        self.assertEqual(calls[:2], [("generate_basic_face.py", ("--write",)),
                                     ("generate_basic_face.py", ("--check",))])
        self.assertFalse(self.bundle.exists())
        self.assertEqual((self.root / basic.FACE).read_bytes(), self.original)

    def test_bundle_uses_committed_inputs(self):
        (self.root / "tools/untracked.py").write_bytes(b"untracked")
        calls = self.run_build(bundle=True)
        self.assertEqual(calls[:2], [("generate_basic_face.py", ("--write",)),
                                     ("generate_basic_face.py", ("--check",))])
        self.assertEqual(self.bundle.read_bytes(), b"bundle")

    def test_dirty_source_rejected_in_both_modes(self):
        (self.root / "tools/input.py").write_bytes(b"modified\n")
        for bundle in (False, True):
            with self.subTest(bundle=bundle):
                with self.assertRaisesRegex(ValueError, "Tracked worktree"):
                    self.run_build(bundle=bundle)
                self.assertFalse(self.bundle.exists())

    def test_source_changed_during_build_rejected_in_both_modes(self):
        for bundle in (False, True):
            with self.subTest(bundle=bundle):
                try:
                    with self.assertRaises(ValueError):
                        self.run_build(bundle=bundle, dirty_during=True)
                    self.assertFalse(self.bundle.exists())
                finally:
                    git(self.root, "checkout", "--", "tools/input.py")

    def test_generation_mismatch_rejected_in_both_modes(self):
        for bundle in (False, True):
            with self.subTest(bundle=bundle):
                with self.assertRaisesRegex(ValueError, "Committed input reproduction mismatch"):
                    self.run_build(bundle=bundle, bad_generation=True)
                self.assertFalse(self.bundle.exists())


if __name__ == "__main__":
    unittest.main()
