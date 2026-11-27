"""Generate cropped procedural material assets for host evidence only."""
import argparse
import hashlib
import json
import struct
import sys
import zlib

from generate_bootstrap import ROOT, exact_keys, integer, safe_path
from round_layout import DIAMETERS, unique, ceiling

SOURCE = "design-system/materials/signature-material-draft.json"
KINDS = ("titanium", "glass", "highlight")
PROFILES = {"ULTRA": list(KINDS), "BALANCED": list(KINDS),
            "ECO": ["titanium", "glass"], "AOD": []}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def rgb(value, name):
    if type(value) is not list or len(value) != 3:
        raise ValueError("Invalid RGB: " + name)
    for v in value:
        integer(v, 0, 255, name)


def parse(raw):
    data = json.loads(raw, object_pairs_hook=unique)
    exact_keys(data, {"schemaVersion","logicalSize","lighting","seed","assets","profiles"}, "material")
    integer(data["schemaVersion"],1,1,"schema")
    integer(data["logicalSize"],450,450,"logical size")
    integer(data["seed"],0,65535,"seed")
    exact_keys(data["lighting"],{"origin","angleDegrees"},"light")
    if data["lighting"]["origin"] != "upper-left":
        raise ValueError("Invalid light origin")
    # R01 renderer implements only this direction.
    integer(data["lighting"]["angleDegrees"],45,45,"light angle")
    if data["profiles"] != PROFILES:
        raise ValueError("Invalid material profile policy")
    exact_keys(data["assets"],set(KINDS),"assets")
    for name, asset in data["assets"].items():
        extra = {"titanium":{"grain","light"},"glass":{"edge","reflection"},
                 "highlight":{"peakAlpha"}}[name]
        exact_keys(asset,{"size","radius","base"} | extra,name)
        size = asset["size"]
        if type(size) is not list or len(size)!=2:
            raise ValueError("Invalid asset size")
        integer(size[0],8,180,name+" width")
        integer(size[1],8,64,name+" height")
        integer(asset["radius"],1,min(size)//2,name+" radius")
        rgb(asset["base"],name)
        if name=="titanium":
            integer(asset["grain"],1,24,"grain")
            integer(asset["light"],1,48,"light")
        elif name=="glass":
            rgb(asset["edge"],"edge")
            integer(asset["reflection"],1,40,"reflection")
            if max(asset["base"])>48 or max(asset["edge"])>180:
                raise ValueError("Glass colors outside draft bounds")
        else:
            integer(asset["peakAlpha"],1,160,"highlight alpha")
    return data


def clamp(value):
    return max(0,min(255,value))


def noise(seed,x,y):
    # Fixed 32-bit integer hash. No random or floating-point state.
    n = (seed ^ (x*374761393) ^ (y*668265263)) & 0xffffffff
    n = ((n ^ (n >> 13))*1274126177) & 0xffffffff
    return (n ^ (n >> 16)) & 255


def dimensions(asset, diameter):
    if type(diameter) is not int or diameter not in DIAMETERS:
        raise ValueError("Unsupported diameter")
    w,h = (ceiling(v*diameter,450) for v in asset["size"])
    radius = min(w//2,h//2,ceiling(asset["radius"]*diameter,450))
    return w,h,radius


def inside(x,y,w,h,r):
    # Coordinates are in eighth-pixel units. Corners use a circle.
    u = max(r-x,0,x-(w-r))
    v = max(r-y,0,y-(h-r))
    return u*u+v*v <= r*r


def coverage(x,y,w,h,r):
    return sum(inside(8*x+a,8*y+b,8*w,8*h,8*r)
               for a in (1,3,5,7) for b in (1,3,5,7))


def pixels(kind,asset,diameter,seed):
    w,h,r = dimensions(asset,diameter)
    out = bytearray()
    for y in range(h):
        for x in range(w):
            cover = coverage(x,y,w,h,r)
            if not cover:
                out.extend((0,0,0,0))
                continue
            light = 255-(127*x//max(1,w-1)+128*y//max(1,h-1))
            if kind=="titanium":
                grain = (noise(seed,0,y)-128)*asset["grain"]//128
                fine = (noise(seed,x,y)-128)*asset["grain"]//512
                bevel = 12 if y<2 else -12 if y>=h-2 else 0
                delta = (light-128)*asset["light"]//128 + grain + fine + bevel
                color = [clamp(v+delta) for v in asset["base"]]
                alpha = 255
            elif kind=="glass":
                # Simulate reflection and a dark lens; no live refraction.
                border = min(x,y,w-1-x,h-1-y)
                blend = 192 if border==0 else 96 if border==1 else 0
                reflection = light*asset["reflection"]//255
                color = [clamp((a*(255-blend)+b*blend)//255+reflection)
                         for a,b in zip(asset["base"],asset["edge"])]
                alpha = 255
            elif kind=="highlight":
                # Local optical streak with a bounded alpha envelope.
                ax = min(2*x+1,2*w-2*x-1)*255//w
                ay = min(2*y+1,2*h-2*y-1)*255//h
                alpha = asset["peakAlpha"]*ax*ay//(255*255)
                color = asset["base"]
            else:
                raise ValueError("Unknown asset kind")
            alpha = (alpha*cover+8)//16
            out.extend((*color,alpha) if alpha else (0,0,0,0))
    return w,h,bytes(out)


def chunk(kind,data):
    return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data))


def png(w,h,data):
    if type(w) is not int or type(h) is not int or not 1<=w<=200 or not 1<=h<=80:
        raise ValueError("Invalid cropped PNG dimensions")
    if type(data) is not bytes or len(data)!=w*h*4:
        raise ValueError("Invalid RGBA length")
    stride = w*4
    raw = b"".join(b"\x00"+data[i:i+stride] for i in range(0,len(data),stride))
    # Stored DEFLATE prioritizes reproducibility; optimize later.
    return PNG_SIGNATURE+chunk(b"IHDR",struct.pack(">IIBBBBB",w,h,8,6,0,0,0))+chunk(b"IDAT",zlib.compress(raw,0))+chunk(b"IEND",b"")


def generate(root=ROOT):
    raw = safe_path(root,SOURCE).read_bytes()
    config = parse(raw)
    outputs = {}
    screens = {}
    for d in DIAMETERS:
        items = {}
        for kind in KINDS:
            w,h,rgba = pixels(kind,config["assets"][kind],d,config["seed"])
            data = png(w,h,rgba)
            outputs[(d,kind)] = data
            items[kind] = {"width":w,"height":h,"rgbaBytes":len(rgba),
                           "pngBytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),
                           "rgbaSha256":hashlib.sha256(rgba).hexdigest()}
        budgets = {profile:sum(items[k]["rgbaBytes"] for k in names)
                   for profile,names in config["profiles"].items()}
        if budgets["ULTRA"]>100000 or budgets["AOD"]!=0:
            raise ValueError("Draft material allocation exceeds budget")
        screens[str(d)] = {"assets":items,"rgbaBytesByProfile":budgets}
    return {"schemaVersion":1,"sourceSha256":hashlib.sha256(raw).hexdigest(),
            "assetCount":len(outputs),"screens":screens,
            "scope":"cropped host material swatches; not WFF resources",
            "runtimeVerification":"NOT RUN"},outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check",action="store_true")
    action.add_argument("--manifest",action="store_true")
    action.add_argument("--png",nargs=2,metavar=("DIAMETER","KIND"))
    args = parser.parse_args()
    report,outputs = generate()
    if args.check:
        if (report,outputs)!=generate():
            raise ValueError("Non-deterministic materials")
        print("MATERIAL_RESULT "+json.dumps(report,sort_keys=True,separators=(",",":")))
    elif args.manifest:
        print(json.dumps(report,sort_keys=True,indent=2))
    else:
        d,kind = args.png
        key = (int(d),kind)
        if key not in outputs:
            parser.error("Unsupported asset")
        sys.stdout.buffer.write(outputs[key])


if __name__=="__main__":
    main()
