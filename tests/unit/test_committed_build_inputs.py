"""Exercise committed input isolation with real temporary Git repositories."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
from committed_build_inputs import clean_commit, copy_committed_inputs, git


class CommittedInputsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/"source"
        self.root.mkdir()
        self.dest = Path(self.tmp.name)/"output"
        self.dest.mkdir()
        git(self.root,"init","-q")
        git(self.root,"config","user.name","AURA test")
        git(self.root,"config","user.email","test@example.invalid")
        git(self.root,"config","commit.gpgsign","false")
        (self.root/"tools").mkdir()
        (self.root/"gradlew").write_bytes(b"#!/bin/sh\n")
        (self.root/"tools"/"input.py").write_bytes(b"original\n")
        (self.root/".gitignore").write_text("ignored.py\n",encoding="utf-8")
        git(self.root,"add",".")
        git(self.root,"update-index","--chmod=+x","gradlew")
        git(self.root,"commit","-qm","fixture")
        self.commit = clean_commit(self.root)

    def copy(self, files=("gradlew",), directories=("tools",)):
        return copy_committed_inputs(self.root,self.dest,self.commit,files,directories)

    def test_only_committed_inputs(self):
        (self.root/"tools"/"extra.py").write_bytes(b"untracked")
        (self.root/"tools"/"ignored.py").write_bytes(b"ignored")
        self.assertEqual(clean_commit(self.root),self.commit)
        self.assertEqual(self.copy(),2)
        self.assertEqual((self.dest/"tools"/"input.py").read_bytes(),b"original\n")
        self.assertFalse((self.dest/"tools"/"extra.py").exists())
        self.assertFalse((self.dest/"tools"/"ignored.py").exists())
        if os.name != "nt":
            self.assertTrue(os.access(self.dest/"gradlew",os.X_OK))

    def test_dirty_tracked_input_rejected(self):
        (self.root/"tools"/"input.py").write_bytes(b"modified")
        with self.assertRaisesRegex(ValueError,"Tracked worktree"):
            clean_commit(self.root)
        self.copy()
        self.assertEqual((self.dest/"tools"/"input.py").read_bytes(),b"original\n")

    def test_missing_required_input(self):
        with self.assertRaisesRegex(ValueError,"Incomplete"):
            self.copy(files=("gradlew","missing"))
        self.assertEqual(list(self.dest.iterdir()),[])

    def test_missing_required_directory(self):
        with self.assertRaisesRegex(ValueError,"Incomplete"):
            self.copy(directories=("tools","missing"))

    def test_nonregular_git_entry(self):
        oid=git(self.root,"rev-parse","HEAD:tools/input.py").decode().strip()
        git(self.root,"update-index","--add","--cacheinfo","120000,"+oid+",tools/link")
        git(self.root,"commit","-qm","symlink fixture")
        self.commit=git(self.root,"rev-parse","HEAD").decode().strip()
        with self.assertRaisesRegex(ValueError,"Non-regular"):
            self.copy()
        self.assertEqual(list(self.dest.iterdir()),[])

    def test_pinned_commit_after_head_changes(self):
        (self.root/"tools"/"input.py").write_bytes(b"new")
        git(self.root,"add","tools/input.py")
        git(self.root,"commit","-qm","new input")
        self.assertNotEqual(clean_commit(self.root),self.commit)
        self.copy()
        self.assertEqual((self.dest/"tools"/"input.py").read_bytes(),b"original\n")

    def test_invalid_commit(self):
        with self.assertRaisesRegex(ValueError,"Invalid source commit"):
            copy_committed_inputs(self.root,self.dest,"HEAD",("gradlew",),("tools",))
