"""Validate logical round layouts and generate host-only geometry evidence."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

from generate_bootstrap import ROOT, exact_keys, integer, rect, safe_path, check_outputs

SOURCE = "design-system/layouts/signature-draft.json"
OUTPUT = "assets/generated/layouts/signature-draft"
DIAMETERS = (432, 438, 480, 498)
REGIONS = {"brand", "date", "battery", "time", "weather", "heart", "steps", "rain"}


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate layout field: " + key)
        result[key] = value
    return result


def inside_circle(box, size, inset):
    x, y, w, h = box
    radius2 = size - 2 * inset
    return all((2*cx-size)**2 + (2*cy-size)**2 <= radius2**2
               for cx in (x, x+w) for cy in (y, y+h))


def separated(a, b, gap):
    x, y, w, h = a
    u, v, p, q = b
    return x+w+gap <= u or u+p+gap <= x or y+h+gap <= v or v+q+gap <= y


def ceiling(n, d):
    return (n+d-1)//d


def project(box, diameter, logical=450):
    """Round outer edges outward so the test covers the entire region."""
    x, y, w, h = box
    left, top = x*diameter//logical, y*diameter//logical
    right = ceiling((x+w)*diameter, logical)
    bottom = ceiling((y+h)*diameter, logical)
    return [left, top, right-left, bottom-top]


def geometry(regions, size, inset, gap):
    for name, box in regions.items():
        rect(box, size, name)
        if not inside_circle(box, size, inset):
            raise ValueError(f"{size}: outside round safe area: {name}")
    for a, b in itertools.combinations(sorted(regions), 2):
        if not separated(regions[a], regions[b], gap):
            raise ValueError(f"{size}: insufficient gap: {a}/{b}")


def parse(raw):
    t = json.loads(raw, object_pairs_hook=unique)
    exact_keys(t, {"schemaVersion", "logicalSize", "safeInset", "minGap",
                   "diameters", "regions", "fontSizes", "ambient"}, "layout")
    integer(t["schemaVersion"], 1, 1, "schemaVersion")
    integer(t["logicalSize"], 450, 450, "logicalSize")
    integer(t["safeInset"], 12, 18, "safeInset")
    integer(t["minGap"], 8, 20, "minGap")
    if not isinstance(t["diameters"], list) or any(type(x) is not int for x in t["diameters"]) or tuple(t["diameters"]) != DIAMETERS:
        raise ValueError("Missing or unsupported screen diameter")
    exact_keys(t["regions"], REGIONS, "regions")
    exact_keys(t["fontSizes"], REGIONS, "fontSizes")
    if t["ambient"] != ["date", "time"]:
        raise ValueError("Draft ambient contract requires date and time")
    geometry(t["regions"], 450, t["safeInset"], t["minGap"])
    for name, font in t["fontSizes"].items():
        integer(font, 1, t["regions"][name][3], name + " font size")
    integer(t["fontSizes"]["time"], 81, 108, "primary time font")
    return t


def project_layout(t, size):
    if type(size) is not int or size not in DIAMETERS:
        raise ValueError("Unsupported screen diameter")
    boxes = {name: project(box, size) for name, box in sorted(t["regions"].items())}
    inset = ceiling(t["safeInset"]*size, 450)
    # Outward edge rounding can reduce the original gap by two pixels.
    gap = max(1, t["minGap"]*size//450 - 2)
    geometry(boxes, size, inset, gap)
    fonts = {name: t["fontSizes"][name]*size//450 for name in sorted(boxes)}
    if any(not 1 <= fonts[name] <= boxes[name][3] for name in boxes):
        raise ValueError("Projected font size outside region")
    return {"diameter": size, "inset": inset, "minimumGap": gap,
            "regions": boxes, "fontSizes": fonts,
            "ambientRegions": {name: boxes[name] for name in t["ambient"]}}


def svg(layout):
    size = layout["diameter"]
    inset = layout["inset"]
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">',
        '<title>AURA Signature draft geometry — not a runtime screenshot</title>',
        f'<circle cx="{size//2}" cy="{size//2}" r="{size//2}" fill="#030508"/>',
        f'<circle cx="{size//2}" cy="{size//2}" r="{size//2-inset}" fill="none" stroke="#526A80" stroke-dasharray="4 4"/>',
    ]
    for name, (x,y,w,h) in layout["regions"].items():
        color = "#79D4F2" if name in layout["ambientRegions"] else "#A9BACB"
        lines.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="none" stroke="{color}"/>')
        lines.append(f'<text x="{x+w//2}" y="{y+h//2}" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="10" fill="{color}">{name}</text>')
    return ("\n".join(lines) + "\n</svg>\n").encode("utf-8")


def generate(root=ROOT):
    raw = safe_path(root, SOURCE).read_bytes()
    t = parse(raw)
    layouts = [project_layout(t, size) for size in DIAMETERS]
    outputs = {f"{OUTPUT}-{x['diameter']}.svg": svg(x) for x in layouts}
    report = {"schemaVersion": 1, "sourceSha256": hashlib.sha256(raw).hexdigest(),
              "scope": "geometry-only; runtime, glyph fit and lit pixels not tested",
              "screens": layouts,
              "svgSha256": {p: hashlib.sha256(data).hexdigest() for p, data in sorted(outputs.items())}}
    outputs[f"{OUTPUT}-geometry.json"] = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)+"\n").encode("utf-8")
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = generate()
    if args.write:
        for name, data in outputs.items():
            path = safe_path(ROOT, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    check_outputs(ROOT, outputs)
    if outputs != generate():
        raise ValueError("Non-deterministic geometry output")
    for name, data in sorted(outputs.items()):
        print(f"LAYOUT_RESULT {name} {hashlib.sha256(data).hexdigest()}")
    print("PASS: four round geometry projections and deterministic wireframes")


if __name__ == "__main__":
    main()
