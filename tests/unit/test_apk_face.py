"""Reject absent or mismatched packaged WFF XML."""
import io
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from check_apk import inspect_face


class ApkFaceTests(unittest.TestCase):
    def inspect(self, content, expected):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            if content is not None:
                archive.writestr("res/raw/watchface.xml", content)
        with zipfile.ZipFile(buffer) as archive:
            return inspect_face(archive, expected)

    def test_matching_face(self):
        self.assertEqual([], self.inspect(b"<WatchFace/>", b"<WatchFace/>"))

    def test_missing_face(self):
        self.assertEqual(["Missing packaged face"], self.inspect(None, b"<WatchFace/>"))

    def test_wrong_face(self):
        self.assertEqual(["Packaged face differs from selected source"],
                         self.inspect(b"<WatchFace/>", b"<Other/>"))
