"""Generate deterministic host-only M01 frame evidence."""
import argparse
import hashlib
import json
import sys
from fractions import Fraction

from generate_bootstrap import ROOT, safe_path
from motion_contract import (SOURCE, LAYOUT, MAX, WINDOWS, CORE, DIAMETERS,
                             parse_motion, parse, ease, frame, check_frame,
                             project_fraction)

# Include every window boundary and midpoint, plus the global midpoint.
SAMPLES = tuple(sorted({0, MAX//2, MAX} | {
    tick for start, end in WINDOWS.values()
    for tick in (start, (start+end)//2, end)}))


def rational(value):
    value = Fraction(value)
    return [value.numerator, value.denominator]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2)+"\n").encode("utf-8")


def frames(layout, motion, diameter):
    rows = []
    for tick in SAMPLES:
        states = frame(layout, motion, tick)
        reverse = frame(layout, motion, MAX-tick, "sleep")
        if states != reverse:
            raise ValueError("Storyboard reverse mismatch")
        check_frame(layout, states, diameter)
        objects = {}
        for name, state in sorted(states.items()):
            objects[name] = {
                "logicalBox": [rational(v) for v in state["box"]],
                "pixelBox": project_fraction(state["box"], diameter),
                "alpha": rational(state["alpha"]),
            }
        rows.append({"wakeTick": tick, "sleepTick": MAX-tick, "objects": objects,
                     "schedule": {name: rational(ease(tick, window))
                                  for name, window in sorted(motion["windows"].items())}})
    return rows


def opacity(pair):
    n, d = pair
    scaled = n*1000000//d
    return f"{scaled//1000000}.{scaled%1000000:06d}"


def storyboard(diameter, rows):
    """Draw rectangle bounds, not text glyphs, rings or actual rendering."""
    cell, label, columns = 184, 22, 5
    width = columns*cell
    height = ((len(rows)+columns-1)//columns)*(cell+label)+26
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<title>AURA M01 synthetic host geometry; runtime NOT RUN</title>',
           f'<rect width="{width}" height="{height}" fill="#090d13"/>',
           f'<text x="8" y="18" fill="#d6e4ef" font-size="12">M01 geometry only | {diameter} px | wake / reverse sleep</text>']
    for index, row in enumerate(rows):
        x = index%columns*cell
        y = index//columns*(cell+label)+26
        out.append(f'<svg x="{x+4}" y="{y}" width="{cell-8}" height="{cell-8}" viewBox="0 0 {diameter} {diameter}">')
        out.append(f'<circle cx="{diameter//2}" cy="{diameter//2}" r="{diameter//2-1}" fill="#030508" stroke="#526a80"/>')
        for name, state in row["objects"].items():
            if state["alpha"][0] == 0:
                continue
            a,b,w,h = state["pixelBox"]
            color = "#79D4F2" if name in CORE else "#A9BACB"
            out.append(f'<rect data-region="{name}" x="{a}" y="{b}" width="{w}" height="{h}" fill="none" stroke="{color}" stroke-width="2" opacity="{opacity(state["alpha"])}"/>')
        out.append("</svg>")
        out.append(f'<text x="{x+cell//2}" y="{y+cell+12}" text-anchor="middle" fill="#d6e4ef" font-size="11">{row["wakeTick"]}/{row["sleepTick"]}</text>')
    return ("\n".join(out)+"\n</svg>\n").encode("utf-8")


def generate(root=ROOT):
    motion_raw = safe_path(root, SOURCE).read_bytes()
    layout_raw = safe_path(root, LAYOUT).read_bytes()
    motion, layout = parse_motion(motion_raw), parse(layout_raw)
    screens = {str(d): frames(layout, motion, d) for d in DIAMETERS}
    svgs = {d: storyboard(d, screens[str(d)]) for d in DIAMETERS}
    report = {
        "schemaVersion": 1, "scope": "synthetic host geometry only",
        "runtimeVerification": "NOT RUN",
        "motionSha256": digest(motion_raw), "layoutSha256": digest(layout_raw),
        "progressMax": MAX, "samples": list(SAMPLES),
        "frameCount": len(SAMPLES)*len(DIAMETERS),
        "scheduleOnly": ["time", "ring", "highlight"],
        "screens": screens, "svgSha256": {str(d): digest(data) for d,data in svgs.items()},
    }
    return canonical(report), svgs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true")
    action.add_argument("--json", action="store_true")
    action.add_argument("--svg", type=int, choices=DIAMETERS)
    args = parser.parse_args()
    data, svgs = generate()
    if args.check:
        if (data, svgs) != generate():
            raise ValueError("Non-deterministic storyboard")
        report = json.loads(data)
        print("MOTION_STORYBOARD_RESULT " + json.dumps({
            "frames": report["frameCount"], "samples": report["samples"],
            "motionSha256": report["motionSha256"], "layoutSha256": report["layoutSha256"],
            "reportSha256": digest(data), "svgSha256": report["svgSha256"],
            "runtimeVerification": report["runtimeVerification"]}, sort_keys=True))
    else:
        sys.stdout.buffer.write(data if args.json else svgs[args.svg])


if __name__ == "__main__":
    main()
