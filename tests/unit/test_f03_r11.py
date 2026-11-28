"""Check the candidate pilot's input and graph validation."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import audit_upstream_candidate as audit


class UpstreamCandidateTests(unittest.TestCase):
    def test_version_anchor(self):
        self.assertEqual(audit.replace_once("old", "old", "new"), "new")
        for text in ("none", "old old"):
            with self.assertRaises(ValueError):
                audit.replace_once(text, "old", "new")

    def parts(self):
        return [{"project": p, "rows": [{"project": p, "scope": "buildscript",
                 "configuration": "classpath", "modules": ["g:a:1"], "error": None,
                 "unresolved": []}]} for p in sorted(audit.PROJECTS)]

    def test_graph_rejects_missing_duplicate_and_unresolved(self):
        self.assertEqual(len(audit.graph_index(self.parts())), 3)
        for parts in (self.parts()[:-1], self.parts() + self.parts()[:1]):
            with self.assertRaises(ValueError):
                audit.graph_index(parts)
        for field, value in (("unresolved", ["g:b:1"]), ("error", "failed"),
                             ("modules", ["g:a:1", "g:a:1"]), ("project", ":wrong")):
            parts = self.parts()
            parts[0]["rows"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                audit.graph_index(parts)

    def test_incomplete_osv_is_unknown(self):
        self.assertEqual(audit.scan(["g:a:1"], lambda q: {})["g:a:1"]["status"], "UNKNOWN")
        self.assertEqual(audit.scan(["g:a:1"], lambda q: {"results": [{}]})["g:a:1"]["status"],
                         "NO_KNOWN_MATCH")


if __name__ == "__main__":
    unittest.main()
