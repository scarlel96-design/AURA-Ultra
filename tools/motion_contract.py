"""Host-only M01 geometry model; never a Wear OS renderer."""
import argparse
import hashlib
import json
from fractions import Fraction
from math import ceil, floor

from generate_bootstrap import ROOT, exact_keys, integer, safe_path
from round_layout import SOURCE as LAYOUT, DIAMETERS, geometry, parse, unique

SOURCE = "design-system/motion/m01-draft.json"
MAX = 1000
WINDOWS = {"time": [0, 850], "ring": [100, 1000], "highlight": [150, 800],
           "panel": [250, 900], "secondary": [450, 1000]}
CORE = ("date", "time", "ampm")
PANELS = ("weather", "heart")
SECONDARY = ("brand", "battery", "steps", "rain")


def parse_motion(raw):
    value = json.loads(raw, object_pairs_hook=unique)
    exact_keys(value, {"schemaVersion", "progressMax", "windows",
                       "panelInset", "secondaryInset"}, "motion")
    integer(value["schemaVersion"], 1, 1, "schemaVersion")
    integer(value["progressMax"], MAX, MAX, "progressMax")
    exact_keys(value["windows"], set(WINDOWS), "windows")
    for name, pair in value["windows"].items():
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError("Invalid window: " + name)
        integer(pair[0], 0, MAX-1, name)
        integer(pair[1], pair[0]+1, MAX, name)
        if pair != WINDOWS[name]:
            raise ValueError("Window differs from M01 specification: " + name)
    integer(value["panelInset"], 1, 12, "panelInset")
    integer(value["secondaryInset"], 1, 6, "secondaryInset")
    return value


def ease(tick, window):
    """Exact rational smoothstep for a host reference, not WFF easing."""
    integer(tick, 0, MAX, "progress")
    start, end = window
    x = Fraction(max(0, min(end-start, tick-start)), end-start)
    return x*x*(3-2*x)


def inset_box(box, inset):
    x, y, w, h = box
    if w <= 2*inset or h <= 2*inset:
        raise ValueError("Motion inset collapses rectangle")
    return [x+inset, y+inset, w-2*inset, h-2*inset]


def project_fraction(box, diameter):
    x, y, w, h = box
    k = Fraction(diameter, 450)
    left, top = floor(x*k), floor(y*k)
    right, bottom = ceil((x+w)*k), ceil((y+h)*k)
    return [left, top, right-left, bottom-top]


def position(tick, direction, profile, reduced):
    integer(tick, 0, MAX, "progress")
    integer(profile, 2, 5, "WFF profile")
    if direction not in ("wake", "sleep") or type(reduced) is not bool:
        raise ValueError("Invalid motion mode")
    if profile < 4 or reduced:
        return MAX if direction == "wake" else 0
    return tick if direction == "wake" else MAX-tick


def frame(layout, motion, tick, direction="wake", profile=4, reduced=False):
    p = position(tick, direction, profile, reduced)
    states = {}
    for name in CORE + PANELS + SECONDARY:
        box = layout["regions"][name]
        if name in CORE:
            alpha = Fraction(1)
            bounds = list(box)
        else:
            group = "panel" if name in PANELS else "secondary"
            alpha = ease(p, motion["windows"][group])
            inset = motion[group+"Inset"] * (1-alpha)
            bounds = inset_box(box, inset)
        states[name] = {"box": bounds, "alpha": alpha}
    return states


def check_frame(layout, states, diameter):
    if type(diameter) is not int or diameter not in DIAMETERS:
        raise ValueError("Unsupported diameter")
    exact_keys(states, set(CORE+PANELS+SECONDARY), "frame")
    visible = {}
    for name, state in states.items():
        alpha, box = state["alpha"], state["box"]
        if not 0 <= alpha <= 1:
            raise ValueError("Alpha outside range")
        x,y,w,h = box
        u,v,p,q = layout["regions"][name]
        if w <= 0 or h <= 0 or x < u or y < v or x+w > u+p or y+h > v+q:
            raise ValueError("Motion leaves reserved rectangle: " + name)
        if name in CORE and (alpha != 1 or box != layout["regions"][name]):
            raise ValueError("Core region changed: " + name)
        if alpha > 0:
            visible[name] = project_fraction(box, diameter)
    inset = ceil(Fraction(layout["safeInset"]*diameter,450))
    gap = max(1, layout["minGap"]*diameter//450-2)
    geometry(visible, diameter, inset, gap)


def audit(layout, motion):
    """Check 1001 normalized positions in both directions by exact reversal."""
    for tick in range(MAX+1):
        states = frame(layout, motion, tick)
        if states != frame(layout, motion, MAX-tick, "sleep"):
            raise ValueError("Reverse path mismatch")
        for diameter in DIAMETERS:
            check_frame(layout, states, diameter)
    return {"positions": MAX+1, "diameters": list(DIAMETERS),
            "geometryChecks": (MAX+1)*len(DIAMETERS),
            "reverseChecks": MAX+1, "scope": "synthetic host geometry only",
            "runtimeVerification": "NOT RUN"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    raw = safe_path(ROOT, SOURCE).read_bytes()
    layout_raw = safe_path(ROOT, LAYOUT).read_bytes()
    result = audit(parse(layout_raw), parse_motion(raw))
    result["motionSha256"] = hashlib.sha256(raw).hexdigest()
    result["layoutSha256"] = hashlib.sha256(layout_raw).hexdigest()
    print("MOTION_RESULT " + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
