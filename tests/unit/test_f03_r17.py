"""Exercise streaming bounds and route-specific digest checks."""
from email.message import Message
import io
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import audit_provenance_exceptions as audit


class Response(io.BytesIO):
    def __init__(self, raw, length=None, encoding=None):
        super().__init__(raw)
        self.headers = Message()
        if length is not None:
            self.headers["Content-Length"] = str(length)
        if encoding:
            self.headers["Content-Encoding"] = encoding


class ExceptionTests(unittest.TestCase):
    def test_exact_stream_and_retention(self):
        raw = b"abc"
        facts, body = audit.consume(Response(raw, 3), 3, True)
        self.assertEqual((facts["sha256"], facts["bytes"], body), (audit.sha(raw), 3, raw))
        self.assertEqual(audit.consume(Response(raw), 3)[1], b"")

    def test_limit_without_header(self):
        with self.assertRaisesRegex(ValueError, "exceeds bound"):
            audit.consume(Response(b"abcd"), 3)

    def test_invalid_response(self):
        for response in (Response(b"", 0), Response(b"abc", 4), Response(b"abc", 2),
                         Response(b"abc", "bad"), Response(b"abc", 3, "gzip")):
            with self.subTest(response=response):
                with self.assertRaises(ValueError):
                    audit.consume(response, 3)

    def test_deadline(self):
        with self.assertRaises(TimeoutError):
            audit.consume(Response(b"a"), 2, clock=iter([0, 121]).__next__)

    def test_duplicate_length(self):
        response = Response(b"a", 1)
        response.headers["Content-Length"] = "1"
        with self.assertRaises(ValueError):
            audit.consume(response, 2)

    def test_route_mismatch_retained_not_approved(self):
        raw = b"other"
        row = {"coordinate": "g:a:1", "artifact": "a-1.pom", "sha256": ["a" * 64], "trust": "UNREVIEWED"}
        with tempfile.TemporaryDirectory() as d:
            result = audit.attempt(row, audit.CENTRAL, 10, "a" * 64, Path(d), True,
                                   lambda url, limit, retain: ({"sha256": audit.sha(raw), "bytes": len(raw)}, raw))
            self.assertEqual(result["status"], "MISMATCH")
            self.assertEqual(result["trust"], "UNREVIEWED")
            self.assertEqual((Path(d) / (audit.sha(raw) + ".pom")).read_bytes(), raw)

    def test_error_reason_not_lost(self):
        row = {"coordinate": "g:a:1", "artifact": "a-1.jar", "sha256": ["a" * 64], "trust": "UNREVIEWED"}
        def reader(*args):
            raise ValueError("Stream exceeds bound")
        result = audit.attempt(row, audit.CENTRAL, 10, "a" * 64, Path("."), reader=reader)
        self.assertEqual((result["status"], result["reason"]), ("UNAVAILABLE", "Stream exceeds bound"))

    def test_redirect_host_only(self):
        with self.assertRaisesRegex(ValueError, "^Redirect refused; host=example.invalid$"):
            audit.ObservedRedirect().redirect_request(None, None, 302, "", {}, "https://example.invalid/a?secret=x")

    def test_alternate_only_on_unavailable(self):
        raw = b"artifact"
        row = {"coordinate": "g:a:1", "artifact": "a-1.jar", "sha256": [audit.sha(raw)], "trust": "UNREVIEWED"}
        calls = []
        def reader(url, limit, retain):
            calls.append(url)
            if url.startswith(audit.CENTRAL):
                raise ValueError("blocked")
            return {"sha256": audit.sha(raw), "bytes": len(raw)}, b""
        routes = audit.compiler_routes(row, Path("."), reader)
        self.assertEqual([x["status"] for x in routes], ["UNAVAILABLE", "MATCH"])
        self.assertEqual(len(calls), 2)
        routes = audit.compiler_routes(row, Path("."), lambda *a: ({"sha256": "0"*64, "bytes": 1}, b""))
        self.assertEqual([x["status"] for x in routes], ["MISMATCH"])


if __name__ == "__main__":
    unittest.main()
