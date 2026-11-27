"""Generate cropped Liquid Crystal host references, not WFF resources."""
import argparse
import hashlib
import json
import sys

from generate_bootstrap import ROOT, exact_keys, integer, safe_path
from round_layout import DIAMETERS, unique, ceiling, project_layout, SOURCE as LAYOUT
from round_layout import parse as parse_layout
from material_foundation import SOURCE as MATERIAL, parse as parse_material
from material_foundation import dimensions, coverage, png

SOURCE = "design-system/materials/liquid-crystal-draft.json"
MODES = ("REFRACTED", "STATIC")
PROFILES = {"ULTRA":"REFRACTED", "BALANCED":"REFRACTED", "ECO":"STATIC", "AOD":None}


def parse(raw):
    t = json.loads(raw, object_pairs_hook=unique)
    exact_keys(t, {"schemaVersion","logicalSize","lighting","panelRegions",
                   "displacementLogical","maxChannel","profiles"}, "liquid crystal")
    integer(t["schemaVersion"],1,1,"schema")
    integer(t["logicalSize"],450,450,"size")
    exact_keys(t["lighting"],{"origin","angleDegrees"},"light")
    if t["lighting"]["origin"] != "upper-left":
        raise ValueError("Invalid light origin")
    integer(t["lighting"]["angleDegrees"],45,45,"light angle")
    if t["panelRegions"] != ["weather","heart"] or t["profiles"] != PROFILES:
        raise ValueError("Invalid panel/profile contract")
    integer(t["displacementLogical"],1,3,"displacement")
    integer(t["maxChannel"],48,68,"channel limit")
    return t


def offset(position, length, limit):
    """Bound a symmetric displacement near the lens edge."""
    signed = 2*position+1-length
    magnitude = abs(signed)
    delta = limit*magnitude*magnitude//(length*length)
    return delta if signed >= 0 else -delta


def sample(x,y,w,h):
    # Synthetic background only. Do not sample text or real screen content.
    x = max(0,min(w-1,x))
    y = max(0,min(h-1,y))
    diagonal = 24*(x+y)//max(1,w+h-2)
    band = 9 if (3*x+2*y) % 23 < 5 else 0
    return (5+diagonal//3+band, 9+diagonal//2+band, 16+diagonal+band)


def render(t, asset, diameter, mode):
    if mode not in MODES:
        raise ValueError("Unsupported lens mode")
    w,h,r = dimensions(asset,diameter)
    limit = ceiling(t["displacementLogical"]*diameter,450) if mode=="REFRACTED" else 0
    out = bytearray()
    max_shift = 0
    for y in range(h):
        for x in range(w):
            cover = coverage(x,y,w,h,r)
            if not cover:
                out.extend((0,0,0,0))
                continue
            dx,dy = offset(x,w,limit),offset(y,h,limit)
            max_shift = max(max_shift,abs(dx),abs(dy))
            bg = sample(x+dx,y+dy,w,h)
            light = 255-(127*x//max(1,w-1)+128*y//max(1,h-1))
            rim = min(x,y,w-1-x,h-1-y)
            spec = (20 if rim==0 else 8 if rim==1 else 0)*light//255
            reflection = asset["reflection"]*light//510
            color = [min(t["maxChannel"],(2*a+b)//3+reflection+spec)
                     for a,b in zip(asset["base"],bg)]
            alpha = (255*cover+8)//16
            out.extend((*color,alpha))
    return w,h,bytes(out),max_shift


def generate(root=ROOT):
    raw = {p:safe_path(root,p).read_bytes() for p in (SOURCE,MATERIAL,LAYOUT)}
    t = parse(raw[SOURCE])
    material = parse_material(raw[MATERIAL])
    layout = parse_layout(raw[LAYOUT])
    if t["lighting"] != material["lighting"]:
        raise ValueError("Material light mismatch")
    asset = material["assets"]["glass"]
    for name in t["panelRegions"]:
        if layout["regions"][name][2:] != asset["size"] or name in layout["ambient"]:
            raise ValueError("Glass placement contract mismatch")
    outputs, screens = {}, {}
    for d in DIAMETERS:
        projected = project_layout(layout,d)
        boxes = {n:projected["regions"][n] for n in t["panelRegions"]}
        items = {}
        for mode in MODES:
            w,h,rgba,shift = render(t,asset,d,mode)
            for box in boxes.values():
                if not (0 <= box[2]-w <= 1 and 0 <= box[3]-h <= 1):
                    raise ValueError("Projected glass scale mismatch")
            data = png(w,h,rgba)
            outputs[(d,mode)] = data
            items[mode] = {"width":w,"height":h,"rgbaBytes":len(rgba),
                           "sha256":hashlib.sha256(data).hexdigest(),
                           "rgbaSha256":hashlib.sha256(rgba).hexdigest(),
                           "maxShiftPixels":shift,"pngBytes":len(data)}
        shared, duplicate = {}, {}
        for profile,mode in PROFILES.items():
            if mode is None:
                shared[profile] = duplicate[profile] = 0
                continue
            other = sum(dimensions(material["assets"][k],d)[0]*
                        dimensions(material["assets"][k],d)[1]*4
                        for k in material["profiles"][profile] if k!="glass")
            shared[profile] = other+items[mode]["rgbaBytes"]
            duplicate[profile] = shared[profile]+items[mode]["rgbaBytes"]
            if shared[profile]>100000:
                raise ValueError("Draft shared asset budget exceeded")
        screens[str(d)] = {"panels":boxes,"assets":items,
                           "sharedRgbaBytes":shared,"duplicateRgbaBytes":duplicate}
    return {"schemaVersion":1,"assetCount":len(outputs),"screens":screens,
            "sourceSha256":{p:hashlib.sha256(v).hexdigest() for p,v in raw.items()},
            "scope":"synthetic cropped glass reference; not WFF resources",
            "runtimeVerification":"NOT RUN"},outputs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--check",action="store_true")
    g.add_argument("--manifest",action="store_true")
    g.add_argument("--png",nargs=2,metavar=("DIAMETER","MODE"))
    args = p.parse_args()
    report,outputs = generate()
    if args.check:
        if (report,outputs)!=generate():
            raise ValueError("Non-deterministic glass output")
        print("LIQUID_CRYSTAL_RESULT "+json.dumps(report,sort_keys=True))
    elif args.manifest:
        print(json.dumps(report,sort_keys=True,indent=2))
    else:
        try:
            key = (int(args.png[0]),args.png[1])
            data = outputs[key]
        except (ValueError,KeyError):
            p.error("Unsupported glass asset")
        sys.stdout.buffer.write(data)


if __name__=="__main__":
    main()
