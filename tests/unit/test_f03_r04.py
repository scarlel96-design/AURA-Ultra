"""Check provisional repository checksum handling without network access."""
import sys
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import audit_published_checksums as audit


class PublishedChecksumTests(unittest.TestCase):
    def row(self):
        return {"coordinate": "example.lib:demo:1.0", "artifact": "demo-1.0.jar",
                "sha256": ["a" * 64], "trust": "UNREVIEWED"}

    def test_published_sha256_match(self):
        result = audit.corroborate(self.row(), lambda url, name: ("a" * 64, url))
        self.assertEqual(result["status"], "MATCH")
        self.assertEqual(result["trust"], "UNREVIEWED")

    def test_mismatch_not_overridden_by_fallback(self):
        calls = []
        def read(url, name):
            calls.append(url)
            return "b" * 64, url
        self.assertEqual(audit.corroborate(self.row(), read)["status"], "MISMATCH")
        self.assertEqual(len(calls), 1)

    def test_unavailable_not_pass(self):
        def read(url, name):
            raise urllib.error.HTTPError(url, 404, "missing", {}, None)
        result = audit.corroborate(self.row(), read)
        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertEqual(len(result["attempts"]), 3)

    def test_sidecar_valid_format(self):
        self.assertEqual(audit.parse_sidecar(b"A" * 64 + b"\n", "demo.jar"), "a" * 64)
        self.assertEqual(audit.parse_sidecar(b"a" * 64 + b" *demo.jar", "demo.jar"), "a" * 64)

    def test_sidecar_invalid_format(self):
        for raw in (b"a" * 40, b"a" * 64 + b" other.jar",
                    b"<html>" + b"a" * 64, b"a" * 64 + b"\n" + b"b" * 64):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                audit.parse_sidecar(raw, "demo.jar")

    def test_invalid_inventory_paths(self):
        for coordinate, artifact in (("../x:a:1", "a.jar"), ("a:b:..", "a.jar"),
                                     ("a:b:1", "../a.jar"), ("a:b:1", "a.jar?x=1")):
            row = dict(self.row(), coordinate=coordinate, artifact=artifact)
            with self.subTest(row=row), self.assertRaises(ValueError):
                audit.artifact_path(row)

    def test_ambiguous_hash_and_trust_rejected(self):
        for row in (dict(self.row(), sha256=["a" * 64, "b" * 64]),
                    dict(self.row(), trust="APPROVED"),
                    dict(self.row(), sha256=["a" * 40])):
            with self.subTest(row=row), self.assertRaises(ValueError):
                audit.artifact_path(row)

    def test_https_host_allowlist(self):
        self.assertTrue(audit.allowed_url("https://repo.maven.apache.org/maven2/x"))
        for url in ("http://repo.maven.apache.org/x", "https://repo.maven.apache.org.bad/x",
                    "https://user@repo.maven.apache.org/x", "https://127.0.0.1/x",
                    "https://repo.maven.apache.org:8080/x"):
            with self.subTest(url=url):
                self.assertFalse(audit.allowed_url(url))


if __name__ == "__main__":
    unittest.main()
