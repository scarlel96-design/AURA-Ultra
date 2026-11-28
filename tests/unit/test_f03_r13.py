"""Test the bounded provenance evidence collector."""
import io
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import audit_provenance_priority as audit


class ProvenanceTests(unittest.TestCase):
    def row(self, raw, artifact="a-1.pom"):
        return {"coordinate": "g:a:1", "artifact": artifact, "sha256": [audit.sha(raw)],
                "trust": "UNREVIEWED"}

    def test_match_never_approves_signature(self):
        raw = b"<project><licenses><license><name>Example</name></license></licenses></project>"
        sig = b"-----BEGIN PGP SIGNATURE-----\nexample"
        with tempfile.TemporaryDirectory() as d:
            result = audit.collect(self.row(raw), Path(d),
                                   lambda url, limit: (sig if url.endswith(".asc") else raw, url))
            self.assertEqual(result["bytesStatus"], "MATCH")
            self.assertEqual(result["signatureStatus"], "PRESENT_UNVERIFIED")
            self.assertEqual(result["licenseStatus"], "DIRECT_DECLARATION")
            self.assertEqual(result["trust"], "UNREVIEWED")
            self.assertEqual((Path(d) / result["signatureFile"]).read_bytes(), sig)

    def test_mismatch_stops_before_signature(self):
        calls = []
        def reader(url, limit):
            calls.append(url)
            return b"changed", url
        with tempfile.TemporaryDirectory() as d:
            result = audit.collect(self.row(b"expected"), Path(d), reader)
            self.assertEqual(result["bytesStatus"], "MISMATCH")
            self.assertEqual(result["signatureStatus"], "NOT_CHECKED")
            self.assertEqual(len(calls), 1)

    def test_invalid_signature_is_not_approved(self):
        raw = b"<project/>"
        with tempfile.TemporaryDirectory() as d:
            result = audit.collect(self.row(raw), Path(d),
                                   lambda url, limit: (b"html" if url.endswith(".asc") else raw, url))
            self.assertEqual(result["signatureStatus"], "UNAVAILABLE_OR_INVALID")
            self.assertEqual(result["licenseStatus"], "NO_DIRECT_DECLARATION")
            self.assertEqual(list(Path(d).iterdir()), [])

    def test_jar_notices_are_bounded(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("META-INF/LICENSE", b"license")
            z.writestr("META-INF/NOTICE", b"notice")
            z.writestr("other/LICENSE", b"unrelated")
        self.assertEqual(len(audit.notices(buf.getvalue())), 2)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("META-INF/LICENSE", b"x" * (audit.MAX_NOTICE + 1))
        with self.assertRaises(ValueError):
            audit.notices(buf.getvalue())

    def test_conflicting_identity_rejected(self):
        rows = {}
        audit.merge_row(rows, ("g:a:1", "a-1.pom"), self.row(b"a"))
        with self.assertRaises(ValueError):
            audit.merge_row(rows, ("g:a:1", "a-1.pom"), self.row(b"b"))

    def test_archive_digest_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "bad.zip"
            path.write_bytes(b"not an archive")
            with self.assertRaises(ValueError):
                audit.archive(path, "0" * 64)


if __name__ == "__main__":
    unittest.main()
