"""Generate synthetic optical depth references without sensor or WFF access."""
import argparse
import hashlib
import json
import sys

from generate_bootstrap import ROOT, exact_keys, integer, safe_path
from round_layout import DIAMETERS, unique, project_layout, project, inside_circle, SOURCE as LAYOUT
from round_layout import parse as parse_layout
from material_foundation import SOURCE as MATERIAL, parse as parse_material

SOURCE = "design-system/materials/optical-depth-draft.json"
PROFILES = ("ULTRA","BALANCED","ECO","AOD")
LAYERS = ("atmosphere","material","reflection")
SAMPLES = tuple((x,y) for x in (-1000,0,1000) for y in (-1000,0,1000))
CASES = tuple((str(i),x,y,False) for i,(x,y) in enumerate(SAMPLES)) + (
    ("missing",None,None,False),("reduced",1000,-1000,True))


def parse(raw):
    t = json.loads(raw,object_pairs_hook=unique)
    exact_keys(t,{"schemaVersion","logicalSize","lighting","panels","depth",
                  "balancedDepth","highlight","profiles"},"optical depth")
    integer(t["schemaVersion"],1,1,"schema")
    integer(t["logicalSize"],450,450,"size")
    if t["lighting"] != {"origin":"upper-left","angleDegrees":45}:
        raise ValueError("Invalid optical lighting")
    integer(t["lighting"]["angleDegrees"],45,45,"light angle")
    if t["panels"] != ["weather","heart"] or t["profiles"] != list(PROFILES):
        raise ValueError("Invalid panel or profile policy")
    for key,maximum in (("depth",6),("balancedDepth",3)):
        exact_keys(t[key],set(LAYERS),key)
        for layer in LAYERS:
            integer(t[key][layer],1,maximum,layer)
        if not t[key]["atmosphere"] < t[key]["material"] < t[key]["reflection"]:
            raise ValueError("Invalid depth order")
    if any(t["balancedDepth"][k]>=t["depth"][k] for k in LAYERS):
        raise ValueError("Invalid Balanced depth")
    exact_keys(t["highlight"],{"box","peakOpacityMilli"},"highlight")
    if t["highlight"]["box"] != [18,10,80,12]:
        raise ValueError("Invalid highlight box")
    for v in t["highlight"]["box"]:
        integer(v,0,450,"highlight geometry")
    integer(t["highlight"]["peakOpacityMilli"],1,180,"highlight opacity")
    return t


def signed_scale(value, amplitude):
    return (1 if value>=0 else -1)*(abs(value)*amplitude//1000)


def state(t,profile,x,y,reduced=False):
    if profile not in PROFILES or type(reduced) is not bool:
        raise ValueError("Invalid optical state")
    if (x is None)!=(y is None):
        raise ValueError("Incomplete tilt")
    if x is not None:
        integer(x,-1000,1000,"tilt x")
        integer(y,-1000,1000,"tilt y")
    if profile=="AOD":
        return {"mode":"OFF","layers":{}}
    dynamic = profile in ("ULTRA","BALANCED") and x is not None and not reduced
    depth = t["depth"] if profile=="ULTRA" else t["balancedDepth"]
    shifts = {k:[signed_scale(x,depth[k]),signed_scale(y,depth[k])]
              if dynamic else [0,0] for k in LAYERS}
    if profile=="ECO" or reduced:
        del shifts["reflection"]
    return {"mode":"DYNAMIC" if dynamic else "STATIC","layers":shifts}


def verify_geometry(t,layout,diameter):
    p = project_layout(layout,diameter)
    # Check all extrema. Intermediate offsets stay inside these bounds.
    for name in t["panels"]:
        x,y,w,h = layout["regions"][name]
        a,b,c,d = t["highlight"]["box"]
        m = t["depth"]["reflection"]
        envelope = [x+a-m,y+b-m,c+2*m,d+2*m]
        outer = project(envelope,diameter)
        px,py,pw,ph = p["regions"][name]
        ox,oy,ow,oh = outer
        if not (px<=ox and py<=oy and ox+ow<=px+pw and oy+oh<=py+ph):
            raise ValueError("Highlight leaves panel")
        if not inside_circle(outer,diameter,p["inset"]):
            raise ValueError("Highlight leaves safe area")
    return p


def svg(t,layout,diameter,profile,x,y,reduced=False):
    p = verify_geometry(t,layout,diameter)
    s = state(t,profile,x,y,reduced)
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{diameter}" height="{diameter}" viewBox="0 0 450 450">',
             '<title>Synthetic optical depth; not a runtime screenshot</title>']
    layers = s["layers"]
    for name in t["panels"]:
        if not layers:
            continue
        px,py,w,h = layout["regions"][name]
        ax,ay = layers["atmosphere"]
        mx,my = layers["material"]
        lines += [f'<defs><clipPath id="clip-{name}"><rect x="{px}" y="{py}" width="{w}" height="{h}" rx="12"/></clipPath>',
                  f'<linearGradient id="atmosphere-{name}" gradientUnits="userSpaceOnUse" x1="{px+ax}" y1="{py+ay}" x2="{px+w+ax}" y2="{py+h+ay}"><stop stop-color="#243748"/><stop offset="1" stop-color="#091018"/></linearGradient>',
                  f'<linearGradient id="material-{name}" gradientUnits="userSpaceOnUse" x1="{px+mx}" y1="{py+my}" x2="{px+w+mx}" y2="{py+h+my}"><stop stop-color="#637a8c" stop-opacity=".25"/><stop offset="1" stop-color="#182432" stop-opacity=".05"/></linearGradient></defs>',
                  f'<g id="{name}" clip-path="url(#clip-{name})">',
                  f'<rect x="{px}" y="{py}" width="{w}" height="{h}" fill="url(#atmosphere-{name})"/>',
                  f'<rect x="{px}" y="{py}" width="{w}" height="{h}" fill="url(#material-{name})"/>']
        if "reflection" in layers:
            rx,ry = layers["reflection"]
            a,b,c,d = t["highlight"]["box"]
            opacity = t["highlight"]["peakOpacityMilli"]
            lines.append(f'<rect id="reflection-{name}" x="{px+a+rx}" y="{py+b+ry}" width="{c}" height="{d}" rx="6" fill="#D0E9F9" opacity="{opacity/1000:.3f}"/>')
        lines.append('</g>')
    lines.append('</svg>')
    return ("\n".join(lines)+"\n").encode("utf-8"),s,p


def generate(root=ROOT):
    raw = {k:safe_path(root,k).read_bytes() for k in (SOURCE,LAYOUT,MATERIAL)}
    t = parse(raw[SOURCE])
    layout = parse_layout(raw[LAYOUT])
    mat = parse_material(raw[MATERIAL])
    if t["lighting"] != mat["lighting"] or any(
        layout["regions"][n][2:]!=mat["assets"]["glass"]["size"] or n in layout["ambient"]
        for n in t["panels"]):
        raise ValueError("Optical material/layout mismatch")
    frames, records = {}, {}
    for d in DIAMETERS:
        for profile in PROFILES:
            for name,x,y,reduced in CASES:
                data,s,p = svg(t,layout,d,profile,x,y,reduced)
                key = f"{d}/{profile}/{name}"
                frames[key] = data
                records[key] = {"state":s,"regions":p["regions"],
                                "sha256":hashlib.sha256(data).hexdigest()}
    return {"schemaVersion":1,"sampleCount":len(frames),
            "sourceSha256":{k:hashlib.sha256(v).hexdigest() for k,v in raw.items()},
            "samples":records,"scope":"host SVG; no sensor, WFF renderer or power measurement",
            "runtimeVerification":"NOT RUN"},frames


def main():
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--check",action="store_true")
    g.add_argument("--manifest",action="store_true")
    g.add_argument("--svg",nargs=3,metavar=("DIAMETER","PROFILE","CASE"))
    args = p.parse_args()
    report,frames = generate()
    if args.check:
        if (report,frames)!=generate():
            raise ValueError("Non-deterministic optical reference")
        print("OPTICAL_DEPTH_RESULT "+json.dumps({"sampleCount":report["sampleCount"],
              "manifestSha256":hashlib.sha256(json.dumps(report,sort_keys=True).encode()).hexdigest(),
              "runtimeVerification":"NOT RUN"},sort_keys=True))
    elif args.manifest:
        print(json.dumps(report,sort_keys=True))
    else:
        key = "/".join(args.svg)
        if key not in frames:
            p.error("Unsupported sample")
        sys.stdout.buffer.write(frames[key])


if __name__=="__main__":
    main()
