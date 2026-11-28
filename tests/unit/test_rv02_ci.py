"""Test exact Intelligence identities and the pinned composite materializer."""
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import check_intelligence_results as evidence
import prepare_rv02_composite as composite


class InventoryTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def make(self, profile="rv02"):
        for path in self.root.glob("*.xml"):
            path.unlink()
        for suite, methods in evidence.expected_methods(profile).items():
            root = ET.Element("testsuite", name=suite, tests=str(len(methods)), failures="0", errors="0", skipped="0")
            for method in sorted(methods):
                ET.SubElement(root, "testcase", classname=suite, name=method)
            ET.ElementTree(root).write(self.root / f"TEST-{suite}.xml")

    def edit(self, fn):
        path = self.root / f"TEST-{evidence.PREFIX}ProtectedBoundaryTest.xml"
        tree = ET.parse(path)
        fn(tree.getroot())
        tree.write(path)

    def test_exact_inventories_and_cross_rejection(self):
        for profile, count, other in (("g01", 108, "rv02"), ("rv02", 124, "g01")):
            self.make(profile)
            self.assertEqual(count, evidence.verify(self.root, profile))
            with self.assertRaises(ValueError):
                evidence.verify(self.root, other)

    def test_missing_old_suite(self):
        self.make()
        (self.root / f"TEST-{evidence.PREFIX}Round05Test.xml").unlink()
        with self.assertRaises(ValueError):
            evidence.verify(self.root, "rv02")

    def test_same_count_wrong_method_or_class(self):
        for field in ("name", "classname"):
            self.make()
            self.edit(lambda root: root.find("testcase").set(field, "invented"))
            with self.assertRaises(ValueError):
                evidence.verify(self.root, "rv02")

    def test_duplicate_and_missing_method(self):
        for duplicate in (True, False):
            self.make()
            def edit(root):
                cases = root.findall("testcase")
                if duplicate:
                    cases[1].set("name", cases[0].get("name"))
                else:
                    root.remove(cases[0])
            self.edit(edit)
            with self.assertRaises(ValueError):
                evidence.verify(self.root, "rv02")

    def test_hidden_and_declared_nonpassing(self):
        for tag, counter in (("failure", "failures"), ("error", "errors"), ("skipped", "skipped"), ("testcase", "tests")):
            self.make()
            self.edit(lambda root: ET.SubElement(root.find("testcase"), tag))
            with self.assertRaises(ValueError):
                evidence.verify(self.root, "rv02")
            self.make()
            self.edit(lambda root: root.set(counter, "1"))
            with self.assertRaises(ValueError):
                evidence.verify(self.root, "rv02")

    def test_unknown_suite_and_wrong_filename(self):
        for extra in (True, False):
            self.make()
            path = self.root / f"TEST-{evidence.PREFIX}ProtectedBoundaryTest.xml"
            if extra:
                (self.root / "extra.xml").write_bytes(path.read_bytes())
            else:
                path.rename(self.root / "wrong.xml")
            with self.assertRaises(ValueError):
                evidence.verify(self.root, "rv02")

    def test_ci_exact_context(self):
        repo = "scarlel96-design/AURA-Ultra"
        branch = evidence.BRANCH
        for event in ("push", "workflow_dispatch"):
            self.assertEqual("rv02", evidence.ci_profile(event, "refs/heads/" + branch, "", "", repo))
        self.assertEqual("rv02", evidence.ci_profile("pull_request", "refs/pull/7/merge", branch, repo, repo))
        for args in (("push", "refs/heads/main", "", "", repo), ("push", "refs/heads/" + branch + "-other", "", "", repo),
                     ("push", "refs/tags/" + branch, "", "", repo), ("pull_request", "", branch, "other/fork", repo),
                     ("pull_request", "", branch, "", repo), ("unknown", "", branch, repo, repo)):
            with self.assertRaises(ValueError):
                evidence.ci_profile(*args)


class CompositeTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.run_git("init", "-q")
        self.run_git("config", "user.name", "Fixture")
        self.run_git("config", "user.email", "fixture@example.invalid")
        self.run_git("config", "core.autocrlf", "false")
        for module, count in (("domain", 26), ("intelligence", 1)):
            folder = self.repo / "modules" / module
            folder.mkdir(parents=True)
            for i in range(count):
                (folder / f"{i}.txt").write_bytes(f"{module}-{i}\n".encode())
        self.run_git("add", ".")
        self.run_git("commit", "-qm", "pinned fixture")
        self.pin = self.run_git("rev-parse", "HEAD").strip()
        self.tree = self.run_git("rev-parse", "HEAD:modules/domain").strip()
        (self.repo / "modules/domain/0.txt").write_bytes(b"wrong domain\n")
        self.run_git("commit", "-qam", "changed current Domain")

    def run_git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], text=True)

    def test_pinned_overlay_and_post_build_tamper(self):
        output = self.root / "scratch"
        with patch.object(composite, "DOMAIN_COMMIT", self.pin), patch.object(composite, "DOMAIN_TREE", self.tree):
            composite.materialize(self.repo, output)
            self.assertEqual(b"domain-0\n", (output / "modules/domain/0.txt").read_bytes())
            self.assertEqual(b"intelligence-0\n", (output / "modules/intelligence/0.txt").read_bytes())
            self.assertEqual(b"wrong domain\n", (self.repo / "modules/domain/0.txt").read_bytes())
            composite.materialize(self.repo, output, verify_only=True)
            with self.assertRaises(FileExistsError):
                composite.materialize(self.repo, output)
            (output / "modules/domain/0.txt").write_bytes(b"tampered")
            with self.assertRaises(ValueError):
                composite.materialize(self.repo, output, verify_only=True)

    def test_wrong_tree_and_missing_pin_fail(self):
        with patch.object(composite, "DOMAIN_COMMIT", self.pin), patch.object(composite, "DOMAIN_TREE", "0" * 40):
            with self.assertRaises(ValueError):
                composite.materialize(self.repo, self.root / "wrong")
        with patch.object(composite, "DOMAIN_COMMIT", "0" * 40):
            with self.assertRaises(subprocess.CalledProcessError):
                composite.materialize(self.repo, self.root / "missing")

    def test_unapproved_module(self):
        with self.assertRaises(ValueError):
            composite.module_files(self.repo, self.pin, "modules/other")
