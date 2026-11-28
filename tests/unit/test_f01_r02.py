"""Negative regression fixtures for F01 R02."""
import contextlib
import hashlib
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_domain_results as domain
import verify_wff as wff


class DomainIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        for source in (ROOT / "docs/evidence/GB-01/junit-r02").glob("TEST-*.xml"):
            shutil.copyfile(source, self.directory / source.name)
        self.path = next(self.directory.glob("*PipelineTest.xml"))

    def mutate(self, edit):
        tree = ET.parse(self.path)
        edit(tree.getroot())
        tree.write(self.path)

    def test_original_evidence(self):
        self.assertEqual(81, domain.verify(self.directory))

    def test_wrong_class(self):
        self.mutate(lambda s: s.find("testcase").set("classname", "unrelated.Test"))
        with self.assertRaises(ValueError):
            domain.verify(self.directory)

    def test_missing_identity_with_equal_count(self):
        self.mutate(lambda s: s.find("testcase").set("name", "invented()"))
        with self.assertRaises(ValueError):
            domain.verify(self.directory)

    def test_nested_case(self):
        self.mutate(lambda s: ET.SubElement(ET.SubElement(s, "properties"), "testcase", name="hidden()"))
        with self.assertRaises(ValueError):
            domain.verify(self.directory)

    def test_nested_failure(self):
        self.mutate(lambda s: ET.SubElement(ET.SubElement(s.find("testcase"), "wrapper"), "failure"))
        with self.assertRaises(ValueError):
            domain.verify(self.directory)

    def test_suite_filename_mismatch(self):
        self.path.rename(self.directory / "TEST-unrelated.xml")
        with self.assertRaises(ValueError):
            domain.verify(self.directory)

    def test_unknown_suite(self):
        self.mutate(lambda s: s.set("name", "io.github.scarlel96.aura.domain.OtherTest"))
        with self.assertRaises(ValueError):
            domain.verify(self.directory)


class NegativeVerdictTests(unittest.TestCase):
    DIAGNOSTIC = "SEVERE: [Line 1:Column 13]: cvc-complex-type.4: Attribute 'width' must appear on element 'WatchFace'."

    def run_probe(self, code=0, diagnostic=DIAGNOSTIC, path_ok=True, version=2, duplicate=False, extra=""):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            (cache / "wff-validator.jar").write_bytes(b"fixture")
            face = cache / "watchface.xml"

            def run(jar, target, actual_version):
                if target == face:
                    return subprocess.CompletedProcess([], 0, f"INFO: PASSED : {face} is valid against watch face format version #2\n")
                target = target if path_ok else target.with_name("wrong.xml")
                verdict = f"INFO: FAILED : {target} is NOT valid against watch face format version #{version}"
                output = "\n".join([diagnostic, verdict, verdict if duplicate else "", extra])
                return subprocess.CompletedProcess([], code, output)

            with patch.object(wff, "CACHE", cache), \
                 patch.object(wff, "SHA256", hashlib.sha256(b"fixture").hexdigest()), \
                 patch.object(wff, "load_profiles", return_value=[{"name": "wff2", "version": 2, "enabled": True}]), \
                 patch.object(wff, "check_source_sets"), patch.object(wff, "face_source", return_value=face), \
                 patch.object(wff, "run_validator", side_effect=run), contextlib.redirect_stdout(io.StringIO()):
                wff.main()

    def test_valid_schema_rejection(self):
        self.run_probe()

    def test_nonzero_exit_with_failure_verdict(self):
        with self.assertRaises(SystemExit):
            self.run_probe(code=1)

    def test_missing_schema_diagnostic(self):
        with self.assertRaises(SystemExit):
            self.run_probe(diagnostic="SEVERE: File not found")

    def test_wrong_path(self):
        with self.assertRaises(SystemExit):
            self.run_probe(path_ok=False)

    def test_wrong_version(self):
        with self.assertRaises(SystemExit):
            self.run_probe(version=3)

    def test_duplicate_verdict(self):
        with self.assertRaises(SystemExit):
            self.run_probe(duplicate=True)

    def test_jvm_crash_alongside_verdict(self):
        with self.assertRaises(SystemExit):
            self.run_probe(extra='Exception in thread "main" java.lang.OutOfMemoryError')

    def test_contradictory_diagnostic(self):
        with self.assertRaises(SystemExit):
            self.run_probe(extra="SEVERE: File not found")


class DomainWorkflowTests(unittest.TestCase):
    def test_both_triggers_cover_verifier_tests_and_wrapper(self):
        text = (ROOT / ".github/workflows/domain-kotlin.yml").read_text()
        push = text.split("  push:\n", 1)[1].split("  pull_request:\n", 1)[0]
        pr = text.split("  pull_request:\n", 1)[1].split("  workflow_dispatch:", 1)[0]
        for section in (push, pr):
            for path in ("tools/check_domain_results.py", "tests/unit/test_domain_results.py", "tests/unit/test_f01_r02.py", "gradlew.bat"):
                with self.subTest(path=path, section=section[:20]):
                    self.assertIn(f"'{path}'", section)
