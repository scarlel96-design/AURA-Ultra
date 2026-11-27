"""Compose host previews and measure cropped asset contrast and cost."""
import argparse
import base64
import hashlib
import json
import struct
import sys
import xml.etree.ElementTree as ET
import zlib

import liquid_crystal as glass
import optical_depth as optical
import titanium_ring as ring
import material_foundation as material
import signature_preview as preview
from generate_bootstrap import ROOT, safe_path
from generate_basic_face import generate as basic, OUTPUT as BASIC
from round_layout import DIAMETERS, SOURCE as LAYOUT, parse as parse_layout, project

NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
Q = "{" + NS + "}"
TILTS = {"neutral":(0,0), "negative":(-1000,-1000), "positive":(1000,1000)}
PROFILES = ("ULTRA","BALANCED","ECO","AOD")
PANEL_COLORS = ("#A9BACB","#79D4F2","#F29AA8","#FFA84D")
REFLECTION_CAP = 60
MIN_CONTRAST = 4.5


def luminance(rgb):
    def linear(v):
        s = v / 255
        return s / 12.92 if s <= 0.04045 else ((s+0.055)/1.055)**2.4
    return sum(w*linear(v) for w,v in zip((0.2126,0.7152,0.0722),rgb))


def rgb(hex_color):
    if not isinstance(hex_color,str) or len(hex_color)!=7 or hex_color[0]!="#":
        raise ValueError("Invalid foreground color")
    return tuple(int(hex_color[i:i+2],16) for i in (1,3,5))


def contrast(foreground, background_luminance):
    a = luminance(rgb(foreground))
    return (max(a,background_luminance)+0.05)/(min(a,background_luminance)+0.05)


def check_contrast(data, colors):
    if not data or len(data)%4 or not colors:
        raise ValueError("Missing RGBA pixels or foreground colors")
    if any(data[i]!=255 for i in range(3,len(data),4)):
        raise ValueError("Expected opaque composite")
    levels = {luminance(data[i:i+3]) for i in range(0,len(data),4)}
    values = {c:min(contrast(c,l) for l in levels) for c in colors}
    if any(v<MIN_CONTRAST for v in values.values()):
        raise ValueError("Draft contrast below 4.5:1")
    return {c:round(v,6) for c,v in values.items()}


def blend(bg,fg,alpha,denominator):
    return tuple((a*(denominator-alpha)+b*alpha+denominator//2)//denominator
                 for a,b in zip(bg,fg))


def panel(g,m,o,d,profile,tilt):
    if profile not in PROFILES or profile=="AOD" or tilt not in TILTS:
        raise ValueError("Unsupported panel state")
    mode = glass.PROFILES[profile]
    w,h,rgba,_ = glass.render(g,m["assets"]["glass"],d,mode)
    s = optical.state(o,profile,*TILTS[tilt])
    shift = s["layers"].get("reflection")
    out = bytearray()
    box = None
    if shift is not None:
        x,y,bw,bh = o["highlight"]["box"]
        box = project([x+shift[0],y+shift[1],bw,bh],d)
        a,b,c,e = box
        if not (0<=a and 0<=b and a+c<=w and b+e<=h):
            raise ValueError("Reflection outside cropped panel")
    for y in range(h):
        for x in range(w):
            i = (y*w+x)*4
            bg = blend((0,0,0),rgba[i:i+3],rgba[i+3],255)
            if box:
                a,b,c,e = box
                if a<=x<a+c and b<=y<b+e:
                    # A local envelope avoids a hard rectangular light edge.
                    edge = min(x-a+1,a+c-x,y-b+1,b+e-y,4)
                    opacity = min(REFLECTION_CAP,o["highlight"]["peakOpacityMilli"])*edge//4
                    opacity = opacity*rgba[i+3]//255
                    bg = blend(bg,(208,233,249),opacity,1000)
            out.extend((*bg,255))
    data = bytes(out)
    return w,h,data,check_contrast(data,PANEL_COLORS)


def compressed_png(w,h,data):
    if not (1<=w<=200 and 1<=h<=80) or len(data)!=w*h*4:
        raise ValueError("Invalid cropped pixel data")
    stride = w*4
    raw = b"".join(b"\x00"+data[i:i+stride] for i in range(0,len(data),stride))
    payload = zlib.compress(raw,9)
    if zlib.decompress(payload)!=raw:
        raise ValueError("Compression read-back mismatch")
    return (material.PNG_SIGNATURE+material.chunk(b"IHDR",struct.pack(">IIBBBBB",w,h,8,6,0,0,0))
            +material.chunk(b"IDAT",payload)+material.chunk(b"IEND",b""))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def generate(root=ROOT):
    g = glass.parse(safe_path(root,glass.SOURCE).read_bytes())
    m = material.parse(safe_path(root,material.SOURCE).read_bytes())
    o = optical.parse(safe_path(root,optical.SOURCE).read_bytes())
    l = parse_layout(safe_path(root,LAYOUT).read_bytes())
    if not g["lighting"]==m["lighting"]==o["lighting"]:
        raise ValueError("Composition light mismatch")
    _,ring_svg = ring.generate(root)
    xml = basic(root)[BASIC]
    frames,assets,records = {},{},{}
    for d in DIAMETERS:
        optical.verify_geometry(o,l,d)
        for p in PROFILES[:-1]:
            for tilt in TILTS:
                w,h,data,ratios = panel(g,m,o,d,p,tilt)
                png = compressed_png(w,h,data)
                original = material.png(w,h,data)
                if len(png)>len(original) or 2*len(data)>100000:
                    raise ValueError("Draft panel asset budget exceeded")
                key = f"{d}/{p}/{tilt}"
                assets[key] = png
                records[key] = {"width":w,"height":h,"rgbaBytes":len(data),
                                "duplicateRgbaBytes":2*len(data),"storedBytes":len(original),
                                "compressedBytes":len(png),"sha256":digest(png),
                                "rgbaSha256":digest(data),"contrast":ratios}
        active_sample = next(s for s in preview.scenarios() if not s["ambient"])
        for sample in preview.scenarios():
            profiles = ("AOD",) if sample["ambient"] else (*PROFILES[:-1],"HIGH_CONTRAST")
            for p in profiles:
                tilts = tuple(TILTS) if sample["name"]==active_sample["name"] and p in PROFILES[:2] else ("neutral",)
                for tilt in tilts:
                    items = preview.collect(xml,sample)
                    if p=="HIGH_CONTRAST":
                        items = [{**i,"color":"#FFFFFF"} for i in items]
                    tree = ET.fromstring(preview.render(items,sample,d))
                    tree.find(Q+"title").text = "AURA host material composition; not a runtime screenshot"
                    if p not in ("AOD","HIGH_CONTRAST"):
                        # Preserve the source ring viewBox and pixel dimensions.
                        ring_tree = ET.fromstring(ring_svg[d,p])
                        tree.insert(3,ring_tree)
                        key = f"{d}/{p}/{tilt}"
                        entry = records[key]
                        uri = "data:image/png;base64,"+base64.b64encode(assets[key]).decode("ascii")
                        for n in g["panelRegions"]:
                            x,y,w,h = project(l["regions"][n],d)
                            aw,ah = entry["width"],entry["height"]
                            if not (0<=w-aw<=1 and 0<=h-ah<=1):
                                raise ValueError("Panel projection mismatch")
                            image = ET.Element(Q+"image",{"id":"material-"+n,"x":str(x),
                                "y":str(y),"width":str(aw),"height":str(ah),"href":uri})
                            tree.insert(4,image)
                        # Check every actual preview foreground against its panel or black.
                        for item in items:
                            x,y,w,h = item["box"]
                            inside = any(px<=x and py<=y and x+w<=px+pw and y+h<=py+ph
                                for px,py,pw,ph in (l["regions"][n] for n in g["panelRegions"]))
                            if inside and item["color"] not in entry["contrast"]:
                                raise ValueError("Unverified panel foreground")
                            if not inside and contrast(item["color"],0)<MIN_CONTRAST:
                                raise ValueError("Insufficient contrast on black")
                    else:
                        if any(contrast(i["color"],0)<MIN_CONTRAST for i in items):
                            raise ValueError("Insufficient contrast on black")
                    key = f"{d}/{p}/{sample['name']}/{tilt}"
                    frames[key] = ET.tostring(tree,encoding="utf-8")+b"\n"
    report = {"schemaVersion":1,"previewCount":len(frames),"assetCount":len(assets),
              "assets":records,"previewHashes":{k:digest(v) for k,v in frames.items()},
              "sourceXmlSha256":digest(xml),"reflectionOpacityMilliCap":REFLECTION_CAP,
              "minimumContrast":MIN_CONTRAST,"ambientMaterialBytes":0,
              "scope":"host opaque panel composites; contrast of ideal foreground colors only; no glyph, WFF, ring raster, or device memory measurement",
              "runtimeVerification":"NOT RUN"}
    return report,frames,assets


def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--check",action="store_true")
    g.add_argument("--manifest",action="store_true")
    g.add_argument("--svg",nargs=4)
    args=p.parse_args()
    report,frames,assets=generate()
    if args.check:
        if (report,frames,assets)!=generate():
            raise ValueError("Non-deterministic composition")
        print("VISUAL_QUALITY_RESULT "+json.dumps(report,sort_keys=True))
    elif args.manifest:
        print(json.dumps(report,sort_keys=True,indent=2))
    else:
        key="/".join(args.svg)
        if key not in frames:
            p.error("Unsupported preview")
        sys.stdout.buffer.write(frames[key])


if __name__=="__main__":
    main()
