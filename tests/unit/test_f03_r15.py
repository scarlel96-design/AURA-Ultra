"""Check exact alternative evidence and fail-closed boundaries."""
import base64
import hashlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import audit_alternative_provenance as audit


class AlternativeTests(unittest.TestCase):
    def test_checksum_identity(self):
        self.assertEqual(audit.checksum512(b"a" * 128, "a.jar"), "a" * 128)
        self.assertEqual(audit.checksum512(b"a" * 128 + b" *a.jar", "a.jar"), "a" * 128)
        for raw in (b"a" * 127, b"a" * 128 + b" other.jar", b"html"):
            with self.assertRaises(ValueError):
                audit.checksum512(raw, "a.jar")

    def test_central_is_corroboration_only(self):
        raw = b"artifact"
        row = {"coordinate": "g:a:1", "artifact": "a-1.jar", "sha256": [audit.sha(raw)], "trust": "UNREVIEWED"}
        def reader(url, limit):
            return (hashlib.sha512(raw).hexdigest().encode() if url.endswith(".sha512") else raw), url
        result = audit.central512(row, reader)
        self.assertEqual(result["status"], "SAME_REPOSITORY_MATCH")
        self.assertEqual(result["trust"], "UNREVIEWED")
        row["sha256"] = ["0" * 64]
        self.assertEqual(audit.central512(row, reader)["status"], "MISMATCH")

    def test_members_do_not_match_by_substring(self):
        b = io.BytesIO()
        with zipfile.ZipFile(b, "w") as z:
            z.writestr("lib/a.jar", b"a")
            z.writestr("lib/not-a.jar", b"b")
        self.assertEqual(audit.member_hashes(b.getvalue(), ["a.jar", "missing.jar"]),
                         {"a.jar": [{"path": "lib/a.jar", "sha256": audit.sha(b"a")}], "missing.jar": []})

    def test_distribution_digest_failure(self):
        with tempfile.TemporaryDirectory() as d:
            result = audit.distribution(audit.APACHE, [], Path(d), "a" * 128,
                                        lambda url, limit: b"a" * 128 if url.endswith(".sha512") else b"bad")
            self.assertEqual(result["status"], "MISMATCH")
            self.assertEqual(list(Path(d).iterdir()), [])

    def test_google_binding_requires_exact_group_and_key(self):
        xml = ('<verification-metadata xmlns="https://schema.gradle.org/dependency-verification">'
               '<configuration><trusted-keys><trusted-key id="' + audit.GUAVA_FPR +
               '"><trusting group="com.google.guava"/></trusted-key></trusted-keys></configuration>'
               '</verification-metadata>').encode()
        self.assertEqual(audit.guava_binding(base64.b64encode(xml)), "GOOGLE_CONSUMER_KEY_BINDING")
        self.assertEqual(audit.guava_binding(base64.b64encode(xml.replace(b"com.google.guava", b"other"))), "NOT_FOUND")

    def test_jose_key_only_in_gpg_plugin(self):
        xml = ('<project xmlns="http://maven.apache.org/POM/4.0.0"><build><plugins><plugin>'
               '<artifactId>maven-gpg-plugin</artifactId><configuration><keyname>' + audit.JOSE_FPR +
               '</keyname></configuration></plugin></plugins></build></project>').encode()
        self.assertEqual(audit.jose_binding(xml), "RELEASE_SOURCE_KEYNAME_MATCH")
        self.assertEqual(audit.jose_binding(xml.replace(b"maven-gpg-plugin", b"other")), "NOT_FOUND")

    def test_dtd_rejected(self):
        with self.assertRaises(ValueError):
            audit.xml_root(b'<!DOCTYPE p><p/>')


if __name__ == "__main__":
    unittest.main()
