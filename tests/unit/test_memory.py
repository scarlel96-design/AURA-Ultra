"""Check strict memory report parsing and budget enforcement."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from verify_memory import parse_report, enforce_limits, MIB


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.valid = {"totalBytes": 100 * MIB, "maxActiveBytes": 70 * MIB, "maxAmbientBytes": 7 * MIB}

    def test_exact_budget(self):
        enforce_limits(parse_report(0, json.dumps(self.valid)))

    def test_zero_assets(self):
        enforce_limits(parse_report(0, json.dumps(dict.fromkeys(self.valid, 0))))

    def test_active_over(self):
        with self.assertRaises(ValueError):
            enforce_limits(dict(self.valid, maxActiveBytes=70 * MIB + 1))

    def test_ambient_over(self):
        with self.assertRaises(ValueError):
            enforce_limits(dict(self.valid, maxAmbientBytes=7 * MIB + 1))

    def test_nonzero_exit(self):
        with self.assertRaises(ValueError):
            parse_report(1, json.dumps(self.valid))

    def test_bad_reports(self):
        for bad in ("", "{}", "[]", '{"error":"bad"}', '{"totalBytes":0,"totalBytes":1,"maxActiveBytes":0,"maxAmbientBytes":0}'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse_report(0, bad)

    def test_invalid_bytes(self):
        for value in (-1, True, 1.0, "1", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_report(0, json.dumps(dict(self.valid, maxActiveBytes=value)))
