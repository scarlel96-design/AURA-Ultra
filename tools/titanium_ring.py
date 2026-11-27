"""Generate a deterministic Titanium precision ring for host SVG evidence."""
import argparse
import hashlib
import json
import sys
from fractions import Fraction

from generate_bootstrap import ROOT, exact_keys, integer, safe_path
from round_layout import DIAMETERS, SOURCE as LAYOUT, parse as parse_layout, project_layout, unique
from motion_object_paths import OBJECTS, parse_objects
from material_foundation import SOURCE as MATERIAL, parse as parse_material

SOURCE = "design-system/materials/titanium-ring-draft.json"
PROFILES = {"ULTRA":["ring","ticks","highlight"],"BALANCED":["ring","ticks","highlight"],
            "ECO":["ring","ticks"],"AOD":[]}
# Fixed-point unit directions at 6-degree intervals, clockwise from 12 o'clock.
DIRECTIONS = (
    (0, -1000000),
    (104528, -994522),
    (207912, -978148),
    (309017, -951057),
    (406737, -913545),
    (500000, -866025),
    (587785, -809017),
    (669131, -743145),
    (743145, -669131),
    (809017, -587785),
    (866025, -500000),
    (913545, -406737),
    (951057, -309017),
    (978148, -207912),
    (994522, -104528),
    (1000000, 0),
    (994522, 104528),
    (978148, 207912),
    (951057, 309017),
    (913545, 406737),
    (866025, 500000),
    (809017, 587785),
    (743145, 669131),
    (669131, 743145),
    (587785, 809017),
    (500000, 866025),
    (406737, 913545),
    (309017, 951057),
    (207912, 978148),
    (104528, 994522),
    (0, 1000000),
    (-104528, 994522),
    (-207912, 978148),
    (-309017, 951057),
    (-406737, 913545),
    (-500000, 866025),
    (-587785, 809017),
    (-669131, 743145),
    (-743145, 669131),
    (-809017, 587785),
    (-866025, 500000),
    (-913545, 406737),
    (-951057, 309017),
    (-978148, 207912),
    (-994522, 104528),
    (-1000000, 0),
    (-994522, -104528),
    (-978148, -207912),
    (-951057, -309017),
    (-913545, -406737),
    (-866025, -500000),
    (-809017, -587785),
    (-743145, -669131),
    (-669131, -743145),
    (-587785, -809017),
    (-500000, -866025),
    (-406737, -913545),
    (-309017, -951057),
    (-207912, -978148),
    (-104528, -994522),
)
SCALE = 1000000
SHINE_START = (-707107,-707107)
SHINE_END = (-342020,-939693)


def color(value):
    if (type(value) is not str or len(value)!=7 or value[0]!="#"
            or any(c not in "0123456789ABCDEF" for c in value[1:])):
        raise ValueError("Invalid RGB color")


def parse(raw):
    t = json.loads(raw,object_pairs_hook=unique)
    exact_keys(t,{"schemaVersion","logicalSize","lighting","ring","ticks","highlight","profiles"},"ring")
    integer(t["schemaVersion"],1,1,"schema")
    integer(t["logicalSize"],450,450,"logical size")
    if t["lighting"] != {"origin":"upper-left","angleDegrees":45} or type(t["lighting"]["angleDegrees"]) is not int:
        raise ValueError("Invalid light")
    if t["profiles"]!=PROFILES:
        raise ValueError("Invalid ring profile policy")
    ring=t["ring"]
    exact_keys(ring,{"innerRadius","outerRadius","trackColors","machiningBands"},"ring bands")
    integer(ring["innerRadius"],200,211,"inner radius")
    integer(ring["outerRadius"],ring["innerRadius"]+1,213,"outer radius")
    integer(ring["machiningBands"],4,4,"machining bands")
    if type(ring["trackColors"]) is not list or len(ring["trackColors"])!=5:
        raise ValueError("Invalid ring gradient")
    for c in ring["trackColors"]:
        color(c)
    ticks=t["ticks"]
    exact_keys(ticks,{"count","majorEvery","innerMajor","innerMinor","outer",
                     "majorWidthMilli","minorWidthMilli","majorColor","minorColor"},"ticks")
    integer(ticks["count"],60,60,"tick count")
    integer(ticks["majorEvery"],5,5,"major interval")
    integer(ticks["innerMajor"],200,ring["innerRadius"]-3,"major inner")
    integer(ticks["innerMinor"],ticks["innerMajor"]+1,ring["innerRadius"]-2,"minor inner")
    integer(ticks["outer"],ticks["innerMinor"]+1,ring["innerRadius"]-1,"tick outer")
    integer(ticks["majorWidthMilli"],500,1200,"major width")
    integer(ticks["minorWidthMilli"],200,ticks["majorWidthMilli"]-1,"minor width")
    color(ticks["majorColor"])
    color(ticks["minorColor"])
    h=t["highlight"]
    exact_keys(h,{"startDegrees","endDegrees","radius","widthMilli","color","opacityPermille"},"highlight")
    integer(h["startDegrees"],-135,-135,"highlight start")
    integer(h["endDegrees"],-110,-110,"highlight end")
    integer(h["radius"],ring["innerRadius"]+1,ring["outerRadius"]-1,"highlight radius")
    integer(h["widthMilli"],200,1000,"highlight width")
    integer(h["opacityPermille"],1,600,"highlight opacity")
    color(h["color"])
    return t


def geometry(t,layout,objects,material,diameter):
    """Bound strokes and rounded coordinate error without raster assumptions."""
    projected=project_layout(layout,diameter)
    r=t["ring"]
    k=t["ticks"]
    h=t["highlight"]
    if t["lighting"]!=material["lighting"]:
        raise ValueError("Inconsistent shared light")
    if (r["innerRadius"]!=objects["ringInnerRadius"] or
            r["outerRadius"]!=objects["ringOuterEnd"] or
            h["startDegrees"]!=objects["highlightStartDegrees"] or
            h["endDegrees"]-h["startDegrees"]!=objects["highlightMaxSweep"]):
        raise ValueError("M01 band mismatch")
    # Fixed-point endpoint and decimal serialization error: <= 0.001 logical unit.
    eps=Fraction(1,1000)
    tick_half=Fraction(k["majorWidthMilli"],2000)
    tick_outer=k["outer"]+tick_half+eps
    inner=k["innerMajor"]-tick_half-eps
    shine_half=Fraction(h["widthMilli"],2000)+eps
    if tick_outer>=r["innerRadius"]:
        raise ValueError("Tick overlaps material band")
    if h["radius"]-shine_half<r["innerRadius"] or h["radius"]+shine_half>r["outerRadius"]:
        raise ValueError("Highlight outside material band")
    scale=Fraction(diameter,450)
    center=Fraction(diameter,2)
    outer=Fraction(r["outerRadius"])*scale
    if outer>center-projected["inset"]:
        raise ValueError("Ring outside round safe area")
    limit=(inner*scale-1)**2
    if inner*scale<=1:
        raise ValueError("Invalid ring clearance")
    for x,y,w,h in projected["regions"].values():
        if any((u-center)**2+(v-center)**2>=limit for u in (x,x+w) for v in (y,y+h)):
            raise ValueError("Ring intersects reserved information bounds")
    return {"diameter":diameter,"regionChecks":len(projected["regions"]),
            "innerBoundMilli":int(inner*1000),"outerRadius":r["outerRadius"],
            "clearancePixels":1}


def decimal(value):
    """Serialize rational coordinates with six decimal places."""
    v=round(Fraction(value)*SCALE)
    sign="-" if v<0 else ""
    a,b=divmod(abs(v),SCALE)
    return sign+str(a)+"."+f"{b:06d}"


def point(radius,direction):
    return tuple(decimal(225+Fraction(radius)*v/SCALE) for v in direction)


def svg(t,diameter,profile):
    if type(diameter) is not int or diameter not in DIAMETERS or profile not in PROFILES:
        raise ValueError("Unsupported ring output")
    lines=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{diameter}" height="{diameter}" viewBox="0 0 450 450">',
           '<title>AURA Titanium precision ring — host-only decorative material</title>']
    if profile!="AOD":
        r=t["ring"]
        k=t["ticks"]
        h=t["highlight"]
        lines+=['<defs><linearGradient id="metal" x1="0%" y1="0%" x2="100%" y2="100%">']
        for i,c in enumerate(r["trackColors"]):
            lines.append(f'<stop offset="{i*25}%" stop-color="{c}"/>')
        lines+=['</linearGradient></defs>','<g id="ring" fill="none">']
        band=Fraction(r["outerRadius"]-r["innerRadius"],r["machiningBands"])
        for i in range(r["machiningBands"]):
            radius=r["innerRadius"]+band*(i+Fraction(1,2))
            opacity=("0.66","0.95","0.58","0.86")[i]
            lines.append(f'<circle cx="225" cy="225" r="{decimal(radius)}" stroke="url(#metal)" stroke-width="{decimal(band)}" stroke-opacity="{opacity}"/>')
        lines+=['</g>','<g id="ticks" fill="none" stroke-linecap="butt">']
        for i,direction in enumerate(DIRECTIONS):
            major=i%k["majorEvery"]==0
            start=point(k["innerMajor"] if major else k["innerMinor"],direction)
            end=point(k["outer"],direction)
            width=k["majorWidthMilli"] if major else k["minorWidthMilli"]
            shade=k["majorColor"] if major else k["minorColor"]
            lines.append(f'<line id="tick-{i}" x1="{start[0]}" y1="{start[1]}" x2="{end[0]}" y2="{end[1]}" stroke="{shade}" stroke-width="{decimal(Fraction(width,1000))}"/>')
        lines.append('</g>')
        if "highlight" in PROFILES[profile]:
            a=point(h["radius"],SHINE_START)
            b=point(h["radius"],SHINE_END)
            lines.append(f'<path id="highlight" d="M {a[0]} {a[1]} A {h["radius"]} {h["radius"]} 0 0 1 {b[0]} {b[1]}" fill="none" stroke="{h["color"]}" stroke-linecap="butt" stroke-width="{decimal(Fraction(h["widthMilli"],1000))}" stroke-opacity="{decimal(Fraction(h["opacityPermille"],1000))}"/>')
    lines.append('</svg>')
    return ("\n".join(lines)+"\n").encode()


def generate(root=ROOT):
    raw={p:safe_path(root,p).read_bytes() for p in (SOURCE,LAYOUT,OBJECTS,MATERIAL)}
    t=parse(raw[SOURCE])
    l=parse_layout(raw[LAYOUT])
    o=parse_objects(raw[OBJECTS])
    m=parse_material(raw[MATERIAL])
    screens={}
    outputs={}
    for d in DIAMETERS:
        g=geometry(t,l,o,m,d)
        profiles={}
        for profile,layers in PROFILES.items():
            data=svg(t,d,profile)
            outputs[(d,profile)]=data
            profiles[profile]={"layers":layers,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}
        screens[str(d)]={"geometry":g,"profiles":profiles,
                         "hypotheticalFullBitmapRgbaBytes":d*d*4}
    return {"schemaVersion":1,"sourceSha256":{p:hashlib.sha256(v).hexdigest() for p,v in raw.items()},
            "assetCount":len(outputs),"regionChecks":sum(x["geometry"]["regionChecks"] for x in screens.values()),
            "tickCount":60,"majorTicks":12,"screens":screens,
            "scope":"host vector reference; no data gauge, raster or WFF resource",
            "runtimeVerification":"NOT RUN"},outputs


def main():
    p=argparse.ArgumentParser(description=__doc__)
    a=p.add_mutually_exclusive_group(required=True)
    a.add_argument("--check",action="store_true")
    a.add_argument("--manifest",action="store_true")
    a.add_argument("--svg",nargs=2,metavar=("DIAMETER","PROFILE"))
    args=p.parse_args()
    report,outputs=generate()
    if args.check:
        if (report,outputs)!=generate():
            raise ValueError("Non-deterministic ring output")
        print("TITANIUM_RING_RESULT "+json.dumps(report,sort_keys=True,separators=(",",":")))
    elif args.manifest:
        print(json.dumps(report,sort_keys=True,indent=2))
    else:
        d,profile=args.svg
        key=(int(d),profile)
        if key not in outputs:
            p.error("Unsupported ring output")
        sys.stdout.buffer.write(outputs[key])


if __name__=="__main__":
    main()
