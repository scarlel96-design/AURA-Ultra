"""Experimental M01 object paths for host geometry only."""
import argparse
import hashlib
import json
from fractions import Fraction
from math import ceil

from generate_bootstrap import ROOT, exact_keys, integer, rect, safe_path
from round_layout import geometry, unique
from motion_contract import (SOURCE, LAYOUT, MAX, DIAMETERS, CORE, WINDOWS,
                             parse, parse_motion, frame, ease, position,
                             project_fraction)

OBJECTS = "design-system/motion/m01-object-path-draft.json"
FIELDS = {"schemaVersion", "translationEnd", "ambientTime", "ambientMarker",
          "ambientFont", "ringInnerRadius", "ringOuterStart", "ringOuterEnd",
          "ringStartDegrees", "ringStartSweep", "highlightStartDegrees",
          "highlightMaxSweep"}


def parse_objects(raw):
    data = json.loads(raw, object_pairs_hook=unique)
    exact_keys(data, FIELDS, "object path")
    integer(data["schemaVersion"], 1, 1, "schema")
    integer(data["translationEnd"], 1, WINDOWS["panel"][0], "translation end")
    rect(data["ambientTime"], 450, "ambient time")
    rect(data["ambientMarker"], 450, "ambient marker")
    integer(data["ambientFont"], 81, min(108, data["ambientTime"][3]), "font")
    x,y,w,h = data["ambientTime"]
    if 2*x+w != 450 or 2*y+h != 450:
        raise ValueError("Ambient time must be centered")
    integer(data["ringInnerRadius"], 1, 212, "inner radius")
    integer(data["ringOuterStart"], data["ringInnerRadius"]+1, 213, "start radius")
    integer(data["ringOuterEnd"], data["ringOuterStart"]+1, 213, "end radius")
    integer(data["ringStartDegrees"], -180, 0, "ring start")
    integer(data["ringStartSweep"], 1, 359, "start sweep")
    integer(data["highlightStartDegrees"], data["ringStartDegrees"],
            data["ringStartDegrees"]+data["ringStartSweep"]-1, "highlight start")
    integer(data["highlightMaxSweep"], 1,
            data["ringStartDegrees"]+data["ringStartSweep"]-data["highlightStartDegrees"],
            "highlight sweep")
    return data


def mix(a, b, p):
    return a+(b-a)*p


def blend(a, b, p):
    return [mix(x,y,p) for x,y in zip(a,b,strict=True)]


def scene(layout, motion, obj, tick, direction="wake", profile=4, reduced=False):
    p = position(tick, direction, profile, reduced)
    dynamic = profile >= 4 and not reduced
    states = frame(layout, motion, tick, direction, profile, reduced)
    regions = layout["regions"]
    font = Fraction(layout["fontSizes"]["time"])
    if dynamic:
        cut = obj["translationEnd"]
        move = ease(p, [0,cut])
        scale = ease(p, [cut,WINDOWS["time"][1]])
        a = obj["ambientTime"]
        target = regions["time"]
        # Translate the small object to the active center before expanding it.
        middle = [Fraction(2*target[0]+target[2]-a[2],2),
                  Fraction(2*target[1]+target[3]-a[3],2), a[2], a[3]]
        states["time"]["box"] = (blend(a,middle,move) if p <= cut
                                 else blend(middle,target,scale))
        states["ampm"]["box"] = blend(obj["ambientMarker"],regions["ampm"],move)
        font = mix(obj["ambientFont"],font,scale)
    ring_p = ease(p, motion["windows"]["ring"])
    shine_p = ease(p, motion["windows"]["highlight"]) if dynamic else Fraction(0)
    ring = {"inner": Fraction(obj["ringInnerRadius"]),
            "outer": mix(obj["ringOuterStart"],obj["ringOuterEnd"],ring_p),
            "start": Fraction(obj["ringStartDegrees"]),
            "sweep": mix(obj["ringStartSweep"],360,ring_p), "alpha": ring_p}
    highlight = {"inner": ring["inner"], "outer": ring["outer"],
                 "start": Fraction(obj["highlightStartDegrees"]),
                 "sweep": obj["highlightMaxSweep"]*shine_p,
                 "alpha": Fraction(3,5)*shine_p}
    return {"regions":states,"timeFont":font,"ring":ring,"highlight":highlight}


def validate_scene(layout, value, diameter):
    if type(diameter) is not int or diameter not in DIAMETERS:
        raise ValueError("Unsupported diameter")
    exact_keys(value, {"regions","timeFont","ring","highlight"}, "scene")
    states = value["regions"]
    exact_keys(states, set(layout["regions"]), "regions")
    visible = {}
    for name,state in states.items():
        exact_keys(state, {"box","alpha"}, name)
        alpha = state["alpha"]
        if type(alpha) not in (int,Fraction) or not 0 <= alpha <= 1:
            raise ValueError("Invalid region alpha")
        box = state["box"]
        if (not isinstance(box,list) or len(box)!=4 or
                any(type(v) not in (int,Fraction) for v in box)):
            raise ValueError("Invalid region rectangle")
        if box[2] <= 0 or box[3] <= 0:
            raise ValueError("Collapsed region")
        if name in CORE and alpha != 1:
            raise ValueError("Hidden core region")
        if name not in ("time","ampm"):
            x,y,w,h = box
            u,v,a,b = layout["regions"][name]
            if x<u or y<v or x+w>u+a or y+h>v+b:
                raise ValueError("Region outside reserved bounds")
        if name == "date" and box != layout["regions"][name]:
            raise ValueError("Date moved")
        if alpha > 0:
            visible[name] = project_fraction(box,diameter)
    font = value["timeFont"]
    if type(font) not in (int,Fraction) or not 81 <= font <= min(108,states["time"]["box"][3]):
        raise ValueError("Invalid time font geometry")
    inset = ceil(Fraction(layout["safeInset"]*diameter,450))
    gap = max(1,layout["minGap"]*diameter//450-2)
    geometry(visible,diameter,inset,gap)
    scale = Fraction(diameter,450)
    center = Fraction(diameter,2)
    ring, shine = value["ring"], value["highlight"]
    for arc in (ring,shine):
        exact_keys(arc, {"inner","outer","start","sweep","alpha"}, "arc")
        if any(type(v) not in (int,Fraction) for v in arc.values()):
            raise ValueError("Invalid arc number")
        if not (0 < arc["inner"] < arc["outer"] and
                arc["outer"]*scale <= center-inset and
                -180 <= arc["start"] <= 180 and 0 <= arc["sweep"] <= 360 and
                0 <= arc["alpha"] <= 1):
            raise ValueError("Arc outside bounds")
        if arc["alpha"]>0 and arc["sweep"]==0:
            raise ValueError("Visible arc has zero sweep")
    if shine["alpha"]>0:
        if (ring["alpha"]==0 or shine["inner"]<ring["inner"] or
                shine["outer"]>ring["outer"] or shine["start"]<ring["start"] or
                shine["start"]+shine["sweep"]>ring["start"]+ring["sweep"]):
            raise ValueError("Highlight outside ring")
    # Check the whole annulus conservatively, not just the visible sector.
    if ring["alpha"]>0:
        limit = (ring["inner"]*scale)**2
        for x,y,w,h in visible.values():
            if any((u-center)**2+(v-center)**2 >= limit
                   for u in (x,x+w) for v in (y,y+h)):
                raise ValueError("Ring intersects information bounds")


def audit_objects(layout,motion,obj):
    for tick in range(MAX+1):
        value = scene(layout,motion,obj,tick)
        if value != scene(layout,motion,obj,MAX-tick,"sleep"):
            raise ValueError("Object reverse mismatch")
        for d in DIAMETERS:
            validate_scene(layout,value,d)
    return {"geometryChecks":(MAX+1)*len(DIAMETERS),"reverseChecks":MAX+1,
            "scope":"experimental host object paths","runtimeVerification":"NOT RUN"}


def load(root=ROOT):
    return (parse(safe_path(root,LAYOUT).read_bytes()),
            parse_motion(safe_path(root,SOURCE).read_bytes()),
            parse_objects(safe_path(root,OBJECTS).read_bytes()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true",required=True)
    parser.parse_args()
    result = audit_objects(*load())
    result["objectSha256"] = hashlib.sha256(safe_path(ROOT,OBJECTS).read_bytes()).hexdigest()
    print("MOTION_OBJECT_RESULT "+json.dumps(result,sort_keys=True))


if __name__ == "__main__":
    main()
