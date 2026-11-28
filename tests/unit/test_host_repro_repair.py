"""Test exact CRLF recovery and fail-closed static material publication."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import generate_bootstrap as bootstrap
import check_material_baseline as baseline


class HostRepairTests(unittest.TestCase):
    def fixture(self, root):
        outputs = {bootstrap.FACE: b"<face/>\n", bootstrap.PACKAGED_PREVIEW: b"png",
                   bootstrap.PALETTE: b"<svg>\n</svg>\n"}
        for name, data in outputs.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return outputs

    def test_repair_only_exact_crlf(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            outputs = self.fixture(root)
            path = root / bootstrap.PALETTE
            path.write_bytes(outputs[bootstrap.PALETTE].replace(b"\n", b"\r\n"))
            with self.assertRaisesRegex(ValueError, "CRLF-only"):
                bootstrap.check_outputs(root, outputs)
            self.assertTrue(bootstrap.repair_palette_crlf(root, outputs))
            bootstrap.check_outputs(root, outputs)
            self.assertFalse(bootstrap.repair_palette_crlf(root, outputs))

    def test_refuse_other_changes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            outputs = self.fixture(root)
            path = root / bootstrap.PALETTE
            changed = b"<other>\r\n"
            path.write_bytes(changed)
            with self.assertRaises(ValueError):
                bootstrap.repair_palette_crlf(root, outputs)
            self.assertEqual(path.read_bytes(), changed)

    def test_no_write_when_other_output_stale(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            outputs = self.fixture(root)
            path = root / bootstrap.PALETTE
            changed = outputs[bootstrap.PALETTE].replace(b"\n", b"\r\n")
            path.write_bytes(changed)
            (root / bootstrap.FACE).write_bytes(b"stale")
            with self.assertRaises(ValueError):
                bootstrap.repair_palette_crlf(root, outputs)
            self.assertEqual(path.read_bytes(), changed)

    def test_material_drift_rejected(self):
        xml, png = b"xml", b"png"
        with patch.multiple(baseline, XML_SHA=baseline.digest(xml),
                            PNG_SHA=baseline.digest(png), RGBA_SHA="pixels"):
            report = {"panelRgbaSha256": "pixels"}
            self.assertEqual(baseline.require_canonical_material(xml, png, report)["status"], "CANONICAL")
            for x, p, r, status in ((b"other", png, report, "XML_CHANGED"),
                                    (xml, b"other", report, "PNG_ENCODING_CHANGED"),
                                    (xml, png, {}, "PIXELS_CHANGED")):
                with self.subTest(status=status):
                    with self.assertRaisesRegex(ValueError, status):
                        baseline.require_canonical_material(x, p, r)


if __name__ == "__main__":
    unittest.main()
