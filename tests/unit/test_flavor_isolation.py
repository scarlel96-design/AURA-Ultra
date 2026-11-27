"""Test flavor fixture generation and the exact negative-verdict contract."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from check_flavor_isolation import ROOT, FACE, make_override, require_mismatch


class FlavorIsolationTests(unittest.TestCase):
    def test_deterministic_override(self):
        first = make_override(ROOT)
        self.assertEqual(first, make_override(ROOT))
        self.assertNotEqual(first, (ROOT / FACE).read_bytes())

    def good_failure(self):
        return "\n".join(["PASS: wff2 resource-only package", "PASS: wff3 resource-only package",
                          "PASS: wff5 resource-only package",
                          "FAIL: wff4: Packaged face differs from selected source"])

    def test_exact_negative(self):
        require_mismatch(self.good_failure())

    def test_wrong_profile(self):
        with self.assertRaises(ValueError):
            require_mismatch(self.good_failure().replace("FAIL: wff4", "FAIL: wff3"))

    def test_missing_unaffected_profile(self):
        with self.assertRaises(ValueError):
            require_mismatch(self.good_failure().replace("PASS: wff5 resource-only package", ""))

    def test_unrelated_failure(self):
        with self.assertRaises(ValueError):
            require_mismatch(self.good_failure() + "\nFAIL: unrelated error")

    def test_no_failure(self):
        with self.assertRaises(ValueError):
            require_mismatch("PASS: inspected all 4 enabled APKs")
