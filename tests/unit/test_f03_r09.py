"""Fail-closed regression checks for the audit evidence tool."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import audit_dependency_review as audit


class DependencyReviewTests(unittest.TestCase):
    def test_osv_empty_result_and_match(self):
        result = audit.osv_query(["g:a:1", "g:b:2"], lambda q: {"results": [{}, {"vulns": [{"id": "TEST-1"}]}]})
        self.assertEqual(result["g:a:1"]["status"], "NO_KNOWN_MATCH")
        self.assertEqual(result["g:b:2"]["ids"], ["TEST-1"])

    def test_osv_missing_results_rejected(self):
        for response in ({}, {"results": []}, {"results": [{"error": "bad"}]}):
            with self.subTest(response=response), self.assertRaises(ValueError):
                audit.osv_query(["g:a:1"], lambda q: response)

    def test_osv_pagination(self):
        def request(q):
            return {"results": [{"vulns": [{"id": "TEST-2"}]}]} if q[0].get("page_token") else {
                "results": [{"vulns": [{"id": "TEST-1"}], "next_page_token": "next"}]}
        self.assertEqual(audit.osv_query(["g:a:1"], request)["g:a:1"]["ids"], ["TEST-1", "TEST-2"])
        with self.assertRaises(ValueError):
            audit.osv_query(["g:a:1"], lambda q: {"results": [{"next_page_token": "loop"}]})

    def test_pom_exact_hash_and_direct_declarations(self):
        raw = b'<project xmlns="http://maven.apache.org/POM/4.0.0"><licenses><license><name>Example</name></license></licenses></project>'
        c = {"artifacts": {"a-1.pom": audit.digest(raw)}}
        self.assertEqual(audit.license_evidence("g:a:1", c, lambda u: (raw, u))["status"], "DECLARED")
        self.assertEqual(audit.license_evidence("g:a:1", c, lambda u: (raw+b" ", u))["status"], "HASH_MISMATCH")
        self.assertEqual(audit.license_evidence("g:a:1", {"artifacts": {} })["status"], "NO_PINNED_POM")

    def test_pom_unknown_not_guessed(self):
        self.assertEqual(audit.parse_pom(b"<project><parent><licenses><license><name>Other</name></license></licenses></parent></project>"), [])
        self.assertEqual(audit.parse_pom(b"<project><licenses><license><name>${license}</name></license></licenses></project>"), [])
        with self.assertRaises(ValueError):
            audit.parse_pom(b"<!DOCTYPE project><project/>")

    def test_merge_conflict_and_sbom(self):
        a = {"coordinate": "g:a:1", "artifact": "a-1.jar", "sha256": ["a"*64]}
        c = audit.merge({"android": ([a], {"g:a:1"}), "domain": ([a], set())})
        self.assertEqual(len(audit.sbom(c)["components"]), 1)
        self.assertNotIn("dependencies", audit.sbom(c))
        with self.assertRaises(ValueError):
            audit.merge({"android": ([a], set()), "domain": ([dict(a, sha256=["b"*64])], set())})


if __name__ == "__main__":
    unittest.main()
