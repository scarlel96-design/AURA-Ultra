"""Reproduce bootstrap WFF resources and a non-runtime palette asset."""
import argparse
import hashlib
import json
import re
import struct
import sys
import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKENS = "design-system/tokens/bootstrap.json"
TEMPLATE = "design-system/templates/bootstrap.xml.tmpl"
PREVIEW = "assets/source/bootstrap/preview.png"
FACE = "apps/watchface/src/main/res/raw/watchface.xml"
PACKAGED_PREVIEW = "apps/watchface/src/main/res/drawable-nodpi/preview.png"
PALETTE = "assets/generated/bootstrap/palette.svg"
COLORS = {"background", "primary", "secondary", "ring", "accent", "panel", "ambient", "innerRing"}
LABELS = {"time", "date", "battery", "steps", "brand"}
DECORATION = {"outerRing", "innerRing", "batteryPanel", "outerStroke", "innerStroke", "panelStroke", "panelRadius"}
BINDING = re.compile(r"\{\{([A-Za-z0-9_.]+)\}\}")


def exact_keys(value, keys, name):
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("Unexpected fields: " + name)


def integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError("Invalid integer: " + name)


def rect(value, size, name):
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError("Invalid rectangle: " + name)
    x, y, w, h = value
    for v in (x, y):
        integer(v, 0, size, name)
    for v in (w, h):
        integer(v, 1, size, name)
    if x + w > size or y + h > size:
        raise ValueError("Rectangle outside canvas: " + name)
    return x, y, w, h


def parse_tokens(raw):
    def unique(pairs):
        result = {}
        for k, v in pairs:
            if k in result:
                raise ValueError("Duplicate token: " + k)
            result[k] = v
        return result
    t = json.loads(raw, object_pairs_hook=unique)
    exact_keys(t, {"schemaVersion", "size", "colors", "layout", "typography", "decoration", "safeInset"}, "root")
    integer(t["schemaVersion"], 1, 1, "schemaVersion")
    integer(t["size"], 450, 450, "size")
    size = t["size"]
    integer(t["safeInset"], 12, 18, "safeInset")
    exact_keys(t["colors"], COLORS, "colors")
    for name, color in t["colors"].items():
        if not isinstance(color, str) or not re.fullmatch(r"#FF[0-9A-F]{6}", color):
            raise ValueError("Invalid opaque ARGB color: " + name)
    exact_keys(t["layout"], LABELS, "layout")
    exact_keys(t["typography"], LABELS, "typography")
    radius = size // 2 - t["safeInset"]
    for name, value in t["layout"].items():
        x, y, w, h = rect(value, size, name)
        if any((cx-size//2)**2 + (cy-size//2)**2 > radius**2
               for cx in (x, x+w) for cy in (y, y+h)):
            raise ValueError("Label outside circle: " + name)
        integer(t["typography"][name], 1, h, name + " font size")
    exact_keys(t["decoration"], DECORATION, "decoration")
    d = t["decoration"]
    for name in ("outerRing", "innerRing", "batteryPanel"):
        rect(d[name], size, name)
    for name in ("outerStroke", "innerStroke", "panelStroke"):
        integer(d[name], 1, 8, name)
    for name, stroke in (("outerRing", "outerStroke"), ("innerRing", "innerStroke")):
        x, y, w, h = d[name]
        if w != h or 2*x+w != size or 2*y+h != size or 2*x-d[stroke] < 2*t["safeInset"]:
            raise ValueError("Ring outside safe area: " + name)
    x, y, w, h = d["batteryPanel"]
    integer(d["panelRadius"], 1, min(w,h)//2, "panelRadius")
    if any((cx-size//2)**2+(cy-size//2)**2 > radius**2
           for cx in (x,x+w) for cy in (y,y+h)):
        raise ValueError("Panel outside circle")
    return t


def render_face(template, tokens):
    values = {"size": tokens["size"]}
    for group in ("colors", "layout", "typography", "decoration"):
        for name, value in tokens[group].items():
            key = group + "." + name
            if isinstance(value, list):
                values.update({f"{key}.{i}": v for i, v in enumerate(value)})
            else:
                values[key] = value
    used = set()
    def substitute(match):
        key = match[1]
        if key not in values:
            raise ValueError("Unknown binding: " + key)
        used.add(key)
        return str(values[key])
    xml = BINDING.sub(substitute, template)
    if "{{" in xml or "}}" in xml or used != set(values):
        raise ValueError("Unresolved or unused template binding")
    root = ET.fromstring(xml)
    if root.tag != "WatchFace" or root.get("width") != str(tokens["size"]) or root.get("height") != str(tokens["size"]):
        raise ValueError("Invalid generated face")
    return xml.encode("utf-8")


def palette(tokens):
    colors = tokens["colors"]
    height = len(colors) * 32
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="256" height="{height}" viewBox="0 0 256 {height}">',
        '  <title>AURA bootstrap palette reference</title>',
        f'  <rect width="256" height="{height}" fill="#000000"/>',
    ]
    for i, name in enumerate(sorted(colors)):
        color = colors[name]
        lines += [
            f'  <rect x="8" y="{i*32+4}" width="56" height="24" fill="#{color[3:]}"/>',
            f'  <text x="76" y="{i*32+20}" fill="#FFFFFF" font-size="12">{name} {color}</text>',
        ]
    return ("\n".join(lines) + "\n</svg>\n").encode("utf-8")


def safe_path(root, name):
    # Use fixed paths. Reject symlinks rather than following them.
    path = root
    for part in name.split("/"):
        if part in ("", ".", ".."):
            raise ValueError("Unsafe path")
        path = path / part
        if path.is_symlink():
            raise ValueError("Symlink not allowed: " + name)
    return path


def generate(root=ROOT):
    inputs = {p: safe_path(root, p).read_bytes() for p in (TOKENS, TEMPLATE, PREVIEW)}
    t = parse_tokens(inputs[TOKENS])
    preview = inputs[PREVIEW]
    if len(preview) < 33 or preview[:8] != b"\x89PNG\r\n\x1a\n" or preview[12:16] != b"IHDR" or struct.unpack(">II", preview[16:24]) != (450,450):
        raise ValueError("Invalid bootstrap preview header")
    outputs = {FACE: render_face(inputs[TEMPLATE].decode("utf-8"), t),
               PACKAGED_PREVIEW: preview, PALETTE: palette(t)}
    digest = lambda files: {p: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
                            for p, data in sorted(files.items())}
    manifest = {"schemaVersion": 1, "inputs": digest(inputs), "outputs": digest(outputs)}
    return outputs, manifest


def check_outputs(root, outputs):
    for name, data in outputs.items():
        path = safe_path(root, name)
        actual = path.read_bytes() if path.is_file() else None
        if actual != data:
            suffix = ""
            if name == PALETTE and actual is not None and actual.replace(b"\r\n", b"\n") == data:
                suffix = " (CRLF-only mismatch; use --repair-palette-crlf)"
            raise ValueError("Missing or stale generated file: " + name + suffix)


def repair_palette_crlf(root, outputs):
    """Restore only an exact CRLF conversion; reject other changes."""
    if set(outputs) != {FACE, PACKAGED_PREVIEW, PALETTE}:
        raise ValueError("Unexpected bootstrap output inventory")
    for name in (FACE, PACKAGED_PREVIEW):
        check_outputs(root, {name: outputs[name]})
    path = safe_path(root, PALETTE)
    old = path.read_bytes()
    expected = outputs[PALETTE]
    if old == expected:
        return False
    if b"\r\n" not in old or old.replace(b"\r\n", b"\n") != expected:
        raise ValueError("Palette differs beyond CRLF conversion")
    # Use a sibling temporary file. Preserve mode and reject intervening changes.
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            tmp = Path(stream.name)
            stream.write(expected)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(tmp, path.stat().st_mode)
        if safe_path(root, PALETTE).read_bytes() != old:
            raise ValueError("Palette changed before repair")
        os.replace(tmp, path)
        tmp = None
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
    check_outputs(root, outputs)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true")
    action.add_argument("--write", action="store_true")
    action.add_argument("--repair-palette-crlf", action="store_true")
    args = parser.parse_args()
    try:
        outputs, manifest = generate()
        if args.write:
            for name, data in outputs.items():
                path = safe_path(ROOT, name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        if args.repair_palette_crlf:
            repair_palette_crlf(ROOT, outputs)
        check_outputs(ROOT, outputs)
        # Check two independent executions of the generation logic.
        if generate() != (outputs, manifest):
            raise ValueError("Non-deterministic generation")
        print(json.dumps(manifest, sort_keys=True, indent=2))
        print("PASS: deterministic bootstrap generation and byte equality")
    except (OSError, ValueError, ET.ParseError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
