"""Verify the active documentation byte gate and failure detection."""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import check_doc_budget as gate


class DocBudgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in gate.LIMITS:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"x")

    def test_exact_limit_and_one_byte_over(self):
        name = "docs/STATUS.md"
        path = self.root / name
        limit = gate.LIMITS[name]
        path.write_bytes(b"x" * limit)
        self.assertEqual(gate.check(self.root)[name]["bytes"], limit)
        path.write_bytes(b"x" * (limit + 1))
        with self.assertRaisesRegex(ValueError, name):
            gate.check(self.root)

    def test_utf8_bytes_not_characters(self):
        path = self.root / "docs/STATUS.md"
        path.write_text("가" * 3000, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "9000 bytes"):
            gate.check(self.root)

    def test_missing_empty_directory(self):
        path = self.root / "docs/STATUS.md"
        path.unlink()
        with self.assertRaises(ValueError):
            gate.check(self.root)
        path.touch()
        with self.assertRaises(ValueError):
            gate.check(self.root)
        path.unlink()
        path.mkdir()
        with self.assertRaises(ValueError):
            gate.check(self.root)

    def test_archive_and_evidence_exempt(self):
        for name in ("docs/archive/STATUS.md", "docs/evidence/REPORT.md"):
            path = self.root / name
            path.parent.mkdir(parents=True)
            path.write_bytes(b"x" * 100000)
        self.assertEqual(set(gate.check(self.root)), set(gate.LIMITS))

    def test_future_gpt_spec(self):
        path = self.root / "docs/operations/GPT-07.md"
        path.write_bytes(b"x" * 10240)
        self.assertEqual(gate.check(self.root)["docs/operations/GPT-07.md"]["bytes"], 10240)
        path.write_bytes(b"x" * 10241)
        with self.assertRaisesRegex(ValueError, "GPT-07.md"):
            gate.check(self.root)

    def test_exit_status(self):
        with patch.object(gate, "check", return_value={"ok": {"bytes": 1, "limit": 2}}):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(gate.main(), 0)
            self.assertIn("DOC_BUDGET_RESULT", output.getvalue())
        with patch.object(gate, "check", side_effect=ValueError("oversize")):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(gate.main(), 1)
            self.assertIn("FAIL: oversize", output.getvalue())

    def test_symlink_rejected(self):
        path = self.root / "docs/STATUS.md"
        path.unlink()
        try:
            path.symlink_to(self.root / "AGENTS.md")
        except OSError:
            # Windows may deny symlink creation. Use a non-regular file fixture.
            path.mkdir()
        with self.assertRaises(ValueError):
            gate.check(self.root)
