"""Reproduce F02 input isolation and checkout defects with disposable Git repositories."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from committed_build_inputs import clean_commit, copy_committed_inputs, git
import check_flavor_isolation as flavor


class F02InputsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.parent = Path(temp.name)
        self.source = self.parent / "source"
        self.source.mkdir()
        self.dest = self.parent / "output"
        self.dest.mkdir()
        git(self.source, "init", "-q")
        git(self.source, "config", "user.name", "AURA fixture")
        git(self.source, "config", "user.email", "fixture@example.invalid")
        git(self.source, "config", "commit.gpgsign", "false")
        git(self.source, "config", "core.autocrlf", "false")
        self.input = self.source / "tools/input.py"
        self.input.parent.mkdir()
        self.input.write_bytes(b"original\n")
        self.commit()

    def commit(self):
        git(self.source, "add", ".")
        git(self.source, "commit", "-qm", "fixture")
        return clean_commit(self.source)

    def copy(self):
        return copy_committed_inputs(self.source, self.dest,
                                     git(self.source, "rev-parse", "HEAD").decode().strip(),
                                     (), ("tools",))

    def link(self, path, target):
        try:
            path.symlink_to(target, target_is_directory=True)
        except OSError:
            if os.name != "nt":
                raise
            subprocess.run(["cmd", "/d", "/c", "mklink", "/J", str(path), str(target)],
                           check=True, capture_output=True)

    def test_normal_empty_destination(self):
        self.assertEqual(self.copy(), 1)
        self.assertEqual((self.dest / "tools/input.py").read_bytes(), b"original\n")

    def test_nonempty_destination_rejected_before_copy(self):
        marker = self.dest / "existing"
        marker.write_bytes(b"preserve")
        with self.assertRaises(ValueError):
            self.copy()
        self.assertEqual(list(self.dest.iterdir()), [marker])
        self.assertEqual(marker.read_bytes(), b"preserve")

    def test_parent_link_cannot_write_to_sibling(self):
        sibling = self.parent / "sibling"
        sibling.mkdir()
        self.link(self.dest / "tools", sibling)
        with self.assertRaises(ValueError):
            self.copy()
        self.assertEqual(list(sibling.iterdir()), [])

    def test_link_destination_rejected(self):
        self.dest.rmdir()
        sibling = self.parent / "sibling"
        sibling.mkdir()
        self.link(self.dest, sibling)
        with self.assertRaises(ValueError):
            self.copy()
        self.assertEqual(list(sibling.iterdir()), [])

    def test_assume_unchanged_rejected(self):
        git(self.source, "update-index", "--assume-unchanged", "tools/input.py")
        self.input.write_bytes(b"modified\n")
        with self.assertRaises(ValueError):
            clean_commit(self.source)

    def test_skip_worktree_rejected(self):
        git(self.source, "update-index", "--skip-worktree", "tools/input.py")
        self.input.write_bytes(b"modified\n")
        with self.assertRaises(ValueError):
            clean_commit(self.source)

    def test_clean_index_with_hidden_flags_rejected(self):
        for flag in ("assume-unchanged", "skip-worktree"):
            with self.subTest(flag=flag):
                git(self.source, "update-index", "--" + flag, "tools/input.py")
                try:
                    with self.assertRaises(ValueError):
                        clean_commit(self.source)
                finally:
                    git(self.source, "update-index", "--no-" + flag, "tools/input.py")

    def test_palette_checkout_is_exact_for_both_autocrlf_modes(self):
        name = "assets/generated/bootstrap/palette.svg"
        palette = self.source / name
        palette.parent.mkdir(parents=True)
        original = git(ROOT, "show", "HEAD:" + name)
        palette.write_bytes(original)
        (self.source / ".gitattributes").write_bytes(git(ROOT, "show", "HEAD:.gitattributes"))
        self.commit()
        for setting in ("false", "true"):
            with self.subTest(autocrlf=setting):
                git(self.source, "config", "core.autocrlf", setting)
                palette.unlink()
                git(self.source, "checkout", "--", name)
                self.assertEqual(palette.read_bytes(), original)

    def flavor_fixture(self):
        face = self.source / flavor.FACE
        face.parent.mkdir(parents=True)
        face.write_bytes(b"<WatchFace/>")
        (self.source / "apps/watchface/build.gradle.kts").write_bytes(b"fixture\n")
        (self.source / "gradlew").write_bytes(b"fixture\n")
        self.commit()
        cache = self.source / ".aura-tools"
        cache.mkdir()
        for name in ("wff-validator.jar", "memory-footprint.jar", "extra.jar"):
            (cache / name).write_bytes(b"fixture")
        return cache

    def test_flavor_uses_only_committed_inputs_and_named_cache(self):
        self.flavor_fixture()
        (self.source / "tools/untracked.py").write_bytes(b"untracked")
        class StopBeforeExecution(Exception):
            pass

        def inspect(snapshot, tool, *args, **kwargs):
            self.assertEqual(tool, "generate_bootstrap.py")
            self.assertEqual((snapshot / "tools/input.py").read_bytes(), b"original\n")
            self.assertFalse((snapshot / "tools/untracked.py").exists())
            self.assertEqual({p.name for p in (snapshot / ".aura-tools").iterdir()},
                             {"wff-validator.jar", "memory-footprint.jar"})
            raise StopBeforeExecution

        with patch.object(flavor, "ROOT", self.source), \
             patch.object(flavor, "FILES", ("gradlew",)), \
             patch.object(flavor, "DIRECTORIES", ("tools", "apps/watchface/src")), \
             patch.object(flavor, "run", side_effect=inspect):
            with self.assertRaises(StopBeforeExecution):
                flavor.main()

    def test_flavor_rejects_dirty_source_before_execution(self):
        self.flavor_fixture()
        self.input.write_bytes(b"modified\n")
        with patch.object(flavor, "ROOT", self.source), \
             patch.object(flavor, "FILES", ("gradlew",)), \
             patch.object(flavor, "DIRECTORIES", ("tools", "apps/watchface/src")), \
             patch.object(flavor, "run") as run:
            run.side_effect = AssertionError("Dirty source reached execution")
            with self.assertRaises(ValueError):
                flavor.main()
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
