"""Test exact baseline selection and evidence reconciliation."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import audit_remaining_provenance as audit


class RemainingTests(unittest.TestCase):
    def row(self, name, sidecar="UNAVAILABLE"):
        return {"coordinate": "g:" + name + ":1", "artifact": name + "-1.jar",
                "sha256": "a" * 64, "sidecar": sidecar, "trust": "UNREVIEWED"}

    def evidence(self, row):
        return {"coordinate": row["coordinate"], "artifact": row["artifact"],
                "expectedSha256": row["sha256"][0], "actualSha256": row["sha256"][0],
                "bytesStatus": "MATCH", "trust": "UNREVIEWED"}

    def test_select_excludes_prior_and_sidecar(self):
        a, b, c = self.row("a"), self.row("b"), self.row("c", "MATCH")
        q = audit.row_from_ledger(a)
        self.assertEqual(audit.select([a, b, c], [q], [self.evidence(q)]),
                         [audit.row_from_ledger(b)])

    def test_candidate_only_prior_is_not_baseline(self):
        a, b = self.row("a"), audit.row_from_ledger(self.row("b"))
        self.assertEqual(audit.select([a], [b], [self.evidence(b)]), [audit.row_from_ledger(a)])

    def test_prior_mismatch_rejected(self):
        a = self.row("a")
        q = audit.row_from_ledger(a)
        r = self.evidence(q)
        r["actualSha256"] = "b" * 64
        with self.assertRaises(ValueError):
            audit.select([a], [q], [r])

    def test_duplicate_or_missing_rejected(self):
        a = self.row("a")
        q = audit.row_from_ledger(a)
        for ledger, prior in (([a, a], [self.evidence(q)]), ([a], [])):
            with self.assertRaises(ValueError):
                audit.select(ledger, [q], prior)

    def test_reconcile_keeps_adverse(self):
        q = audit.row_from_ledger(self.row("a"))
        r = self.evidence(q)
        r.update(bytesStatus="MISMATCH", actualSha256="b" * 64)
        self.assertEqual(audit.reconcile([q], [r])[audit.identity(q)]["bytesStatus"], "MISMATCH")

    def test_false_match_and_trust_rejected(self):
        q = audit.row_from_ledger(self.row("a"))
        for change in ({"actualSha256": "b" * 64}, {"trust": "APPROVED"}):
            r = self.evidence(q)
            r.update(change)
            with self.assertRaises(ValueError):
                audit.reconcile([q], [r])

    def test_reconcile_incomplete_rejected(self):
        q = audit.row_from_ledger(self.row("a"))
        with self.assertRaises(ValueError):
            audit.reconcile([q], [])


if __name__ == "__main__":
    unittest.main()
