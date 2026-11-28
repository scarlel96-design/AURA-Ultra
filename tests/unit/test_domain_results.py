"""Verify that the Kotlin CI evidence checker rejects incomplete test results."""
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from check_domain_results import BASELINE_METHODS, D01_METHODS, D01_BRANCH, ci_profile, verify


class DomainEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name, methods in BASELINE_METHODS.items():
            count = len(methods)
            suite = ET.Element("testsuite", name="io.github.scarlel96.aura.domain." + name,
                               tests=str(count), failures="0", errors="0", skipped="0")
            for method in sorted(methods):
                ET.SubElement(suite, "testcase", classname=suite.get("name"), name=method)
            ET.ElementTree(suite).write(self.root / f"TEST-{suite.get('name')}.xml")

    def modify(self, edit):
        path = self.root / "TEST-io.github.scarlel96.aura.domain.PipelineTest.xml"
        tree = ET.parse(path)
        edit(tree.getroot())
        tree.write(path)

    def test_baseline(self):
        self.assertEqual(81, verify(self.root))

    def test_missing_suite(self):
        (self.root / "TEST-io.github.scarlel96.aura.domain.PipelineTest.xml").unlink()
        with self.assertRaises(ValueError):
            verify(self.root)

    def test_wrong_count(self):
        self.modify(lambda suite: suite.set("tests", "0"))
        with self.assertRaises(ValueError):
            verify(self.root)

    def test_failure(self):
        self.modify(lambda suite: suite.set("failures", "1"))
        with self.assertRaises(ValueError):
            verify(self.root)

    def test_hidden_skip(self):
        self.modify(lambda suite: ET.SubElement(suite.find("testcase"), "skipped"))
        with self.assertRaises(ValueError):
            verify(self.root)

    def test_duplicate_case(self):
        self.modify(lambda suite: suite.findall("testcase")[1].set("name", suite.findall("testcase")[0].get("name")))
        with self.assertRaises(ValueError):
            verify(self.root)

class D01InventoryTests(unittest.TestCase):
    setUp = DomainEvidenceTests.setUp
    def add_d01(self):
        name = "io.github.scarlel96.aura.domain.PayloadIntegrityTest"
        methods = D01_METHODS["PayloadIntegrityTest"]
        suite = ET.Element("testsuite", name=name, tests=str(len(methods)),
                           failures="0", errors="0", skipped="0")
        for method in sorted(methods):
            ET.SubElement(suite, "testcase", classname=name, name=method)
        self.d01_path = self.root / f"TEST-{name}.xml"
        ET.ElementTree(suite).write(self.d01_path)

    def edit_d01(self, edit):
        tree = ET.parse(self.d01_path)
        edit(tree.getroot())
        tree.write(self.d01_path)

    def test_explicit_inventory_accepts_all_88(self):
        self.add_d01()
        self.assertEqual(88, verify(self.root, "d01"))
        with self.assertRaisesRegex(ValueError, "Unknown or duplicate suite"):
            verify(self.root)

    def test_candidate_cannot_fall_back_to_81(self):
        with self.assertRaisesRegex(ValueError, "Missing baseline suites"):
            verify(self.root, "d01")

    def test_candidate_requires_every_original_suite(self):
        self.add_d01()
        (self.root / "TEST-io.github.scarlel96.aura.domain.PipelineTest.xml").unlink()
        with self.assertRaises(ValueError):
            verify(self.root, "d01")

    def test_candidate_rejects_unknown_method_same_count(self):
        self.add_d01()
        self.edit_d01(lambda s: s.find("testcase").set("name", "invented()"))
        with self.assertRaises(ValueError):
            verify(self.root, "d01")

    def test_candidate_rejects_duplicate_method(self):
        self.add_d01()
        self.edit_d01(lambda s: s.findall("testcase")[1].set("name", s.find("testcase").get("name")))
        with self.assertRaises(ValueError):
            verify(self.root, "d01")

    def test_candidate_rejects_hidden_nonpassing(self):
        self.add_d01()
        for tag in ("failure", "error", "skipped"):
            with self.subTest(tag=tag):
                self.add_d01()
                self.edit_d01(lambda s: ET.SubElement(s.find("testcase"), tag))
                with self.assertRaises(ValueError):
                    verify(self.root, "d01")

    def test_candidate_rejects_extra_suite(self):
        self.add_d01()
        extra = self.root / "TEST-extra.xml"
        extra.write_bytes(self.d01_path.read_bytes())
        with self.assertRaises(ValueError):
            verify(self.root, "d01")

    def test_unknown_profile_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown test inventory"):
            verify(self.root, "auto")

    def test_branch_selection_is_exact(self):
        repo = "scarlel96-design/AURA-Ultra"
        for event in ("push", "workflow_dispatch"):
            self.assertEqual("d01", ci_profile(event, "refs/heads/" + D01_BRANCH, "", "", repo))
            self.assertEqual("baseline", ci_profile(event, "refs/heads/main", "", "", repo))
            self.assertEqual("baseline", ci_profile(event, "refs/heads/" + D01_BRANCH + "-other", "", "", repo))
        self.assertEqual("d01", ci_profile("pull_request", "refs/pull/5/merge", D01_BRANCH, repo, repo))
        self.assertEqual("baseline", ci_profile("pull_request", "refs/pull/6/merge", D01_BRANCH, "other/fork", repo))
        with self.assertRaises(ValueError):
            ci_profile("pull_request", "refs/pull/5/merge", "", "", repo)
        with self.assertRaises(ValueError):
            ci_profile("unknown", "refs/heads/" + D01_BRANCH, "", "", repo)
