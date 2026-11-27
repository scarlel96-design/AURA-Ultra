"""Verify that the Kotlin CI evidence checker rejects incomplete test results."""
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from check_domain_results import BASELINE, verify


class DomainEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name, count in BASELINE.items():
            suite = ET.Element("testsuite", name="io.github.scarlel96.aura.domain." + name,
                               tests=str(count), failures="0", errors="0", skipped="0")
            for i in range(count):
                ET.SubElement(suite, "testcase", classname=suite.get("name"), name=f"test{i}")
            ET.ElementTree(suite).write(self.root / f"TEST-{name}.xml")

    def modify(self, edit):
        path = self.root / "TEST-PipelineTest.xml"
        tree = ET.parse(path)
        edit(tree.getroot())
        tree.write(path)

    def test_baseline(self):
        self.assertEqual(81, verify(self.root))

    def test_missing_suite(self):
        (self.root / "TEST-PipelineTest.xml").unlink()
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
        self.modify(lambda suite: suite.findall("testcase")[1].set("name", "test0"))
        with self.assertRaises(ValueError):
            verify(self.root)
