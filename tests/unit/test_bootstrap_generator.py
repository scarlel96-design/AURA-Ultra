"""Test deterministic generation and rejected input/output defects."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from generate_bootstrap import (ROOT, TOKENS, TEMPLATE, PREVIEW, FACE, PACKAGED_PREVIEW,
                                PALETTE, parse_tokens, render_face, generate, check_outputs,
                                safe_path)


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.tokens = parse_tokens((ROOT / TOKENS).read_bytes())
        self.template = (ROOT / TEMPLATE).read_text(encoding="utf-8")

    def reject(self, change):
        t = copy.deepcopy(self.tokens)
        change(t)
        with self.assertRaises(ValueError):
            parse_tokens(json.dumps(t))

    def test_deterministic(self):
        self.assertEqual(generate(), generate())

    def test_checked_in_outputs(self):
        outputs, manifest = generate()
        check_outputs(ROOT, outputs)
        self.assertEqual({FACE, PACKAGED_PREVIEW, PALETTE}, set(manifest["outputs"]))

    def test_missing_key(self):
        self.reject(lambda t: t["colors"].pop("primary"))

    def test_unknown_key(self):
        self.reject(lambda t: t.update(extra=1))

    def test_duplicate(self):
        with self.assertRaises(ValueError):
            parse_tokens('{"schemaVersion":1,"schemaVersion":1}')

    def test_bad_color(self):
        self.reject(lambda t: t["colors"].update(primary="#ZZ000000"))

    def test_alpha_color(self):
        self.reject(lambda t: t["colors"].update(primary="#00123456"))

    def test_wrong_canvas(self):
        self.reject(lambda t: t.update(size=451))

    def test_non_integer(self):
        self.reject(lambda t: t["typography"].update(time=True))

    def test_outside_canvas(self):
        self.reject(lambda t: t["layout"].update(date=[449,90,270,35]))

    def test_outside_circle(self):
        self.reject(lambda t: t["layout"].update(date=[0,0,50,20]))

    def test_zero_size(self):
        self.reject(lambda t: t["layout"].update(date=[90,90,0,35]))

    def test_font_too_large(self):
        self.reject(lambda t: t["typography"].update(date=36))

    def test_ring_inset(self):
        self.reject(lambda t: t["decoration"].update(outerRing=[1,1,448,448]))

    def test_panel_radius(self):
        self.reject(lambda t: t["decoration"].update(panelRadius=22))

    def test_unknown_binding(self):
        with self.assertRaises(ValueError):
            render_face(self.template.replace("{{size}}", "{{unknown}}", 1), self.tokens)

    def test_unused_binding(self):
        with self.assertRaises(ValueError):
            render_face(self.template.replace("{{typography.brand}}", "15"), self.tokens)

    def test_token_change(self):
        t = copy.deepcopy(self.tokens)
        t["colors"]["accent"] = "#FFFFFFFF"
        self.assertNotEqual(render_face(self.template, t), render_face(self.template, self.tokens))

    def test_missing_output(self):
        with tempfile.TemporaryDirectory() as d, self.assertRaises(ValueError):
            check_outputs(Path(d), {FACE: b"test"})

    def test_stale_output(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = root / FACE
            path.parent.mkdir(parents=True)
            path.write_bytes(b"old")
            with self.assertRaises(ValueError):
                check_outputs(root, {FACE: b"new"})

    def test_path_traversal(self):
        with self.assertRaises(ValueError):
            safe_path(ROOT, "../outside")

    def test_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "real").mkdir()
            (root / "link").symlink_to(root / "real", target_is_directory=True)
            with self.assertRaises(ValueError):
                safe_path(root, "link/file")
