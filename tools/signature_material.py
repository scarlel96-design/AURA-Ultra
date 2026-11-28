"""Generate a static Signature material face for isolated WFF builds."""
import hashlib
import json
import xml.etree.ElementTree as ET
from fractions import Fraction

import titanium_ring as ring
import liquid_crystal as glass
import material_foundation as material
import optical_depth as optical
import visual_quality as visual
from generate_bootstrap import ROOT, safe_path
from generate_basic_face import generate as basic, OUTPUT as BASIC, node, bounds
from round_layout import SOURCE as LAYOUT, parse as parse_layout

RESOURCE = "aura_signature_panel"
PNG_PATH = "res/drawable-nodpi-v4/" + RESOURCE + ".png"
SVG_NS = "{http://www.w3.org/2000/svg}"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def argb(color, opacity):
    if not color.startswith("#") or len(color)!=7 or not 0<=opacity<=1:
        raise ValueError("Invalid ring color or opacity")
    return f"#{round(255*opacity):02X}"+color[1:]


def build_ring(parent, t):
    # Translate the exact checked SVG centerlines to WFF drawing primitives.
    source = ET.fromstring(ring.svg(t,498,"BALANCED"))
    draw = node(parent,"PartDraw",name="PrecisionRing",x=0,y=0,width=450,height=450)
    stops = source.findall(".//"+SVG_NS+"stop")
    circles = source.findall(".//"+SVG_NS+"circle")
    lines = source.findall(".//"+SVG_NS+"line")
    if len(stops)!=5 or len(circles)!=4 or len(lines)!=60:
        raise ValueError("Unexpected ring topology")
    for c in circles:
        radius=Fraction(c.get("r"))
        diameter=ring.decimal(2*radius)
        ellipse=node(draw,"Ellipse",x=ring.decimal(225-radius),
                     y=ring.decimal(225-radius),width=diameter,height=diameter)
        opacity=Fraction(c.get("stroke-opacity"))
        stroke=node(ellipse,"Stroke",color="#FFFFFFFF",thickness=c.get("stroke-width"))
        node(stroke,"LinearGradient",startX=0,startY=0,endX=450,endY=450,
             colors=" ".join(argb(s.get("stop-color"),opacity) for s in stops),
             positions="0 0.25 0.5 0.75 1")
    for l in lines:
        line=node(draw,"Line",startX=l.get("x1"),startY=l.get("y1"),
                  endX=l.get("x2"),endY=l.get("y2"))
        node(line,"Stroke",color=argb(l.get("stroke"),1),
             thickness=l.get("stroke-width"),cap="BUTT")
    h=t["highlight"]
    # WFF zero is 12 o'clock; SVG zero is positive x.
    arc=node(draw,"Arc",centerX=225,centerY=225,width=2*h["radius"],height=2*h["radius"],
             startAngle=(h["startDegrees"]+90)%360,endAngle=(h["endDegrees"]+90)%360)
    node(arc,"Stroke",color=argb(h["color"],Fraction(h["opacityPermille"],1000)),
         thickness=ring.decimal(Fraction(h["widthMilli"],1000)),cap="BUTT")
    return draw


def canonical(element):
    """Compare structure and content, ignoring indentation-only whitespace."""
    def content(value):
        return value if value and value.strip() else ""
    return (element.tag, tuple(sorted(element.attrib.items())), content(element.text),
            content(element.tail), tuple(canonical(child) for child in element))


def check_face(face, original, layout, *, ring_tokens=None):
    root=ET.fromstring(face)
    scene=root.find("Scene")
    if scene is None or not len(scene):
        raise ValueError("Missing Scene or material layer")
    groups=scene.findall("Group")
    selected=[g for g in groups if g.get("name")=="SignatureMaterials"]
    if len(selected)!=1 or scene[0] is not selected[0]:
        raise ValueError("Missing material layer before information")
    group=selected[0]
    if group.attrib!={"name":"SignatureMaterials","x":"0","y":"0","width":"450","height":"450"}:
        raise ValueError("Invalid material group")
    if len(group.findall("Variant"))!=1 or group[0].attrib!={"mode":"AMBIENT","target":"alpha","value":"0"}:
        raise ValueError("Missing ambient suppression")
    if [e.tag for e in group]!=["Variant","PartDraw","PartImage","PartImage"]:
        raise ValueError("Unexpected material layer")
    draw=group[1]
    if len(draw.findall("Ellipse"))!=4 or len(draw.findall("Line"))!=60 or len(draw.findall("Arc"))!=1:
        raise ValueError("Missing ring geometry")
    # Reconstruct the full ring from the approved token source, not the candidate XML.
    if ring_tokens is None:
        ring_tokens = ring.parse(safe_path(ROOT, ring.SOURCE).read_bytes())
    expected = build_ring(ET.Element("Group"), ring_tokens)
    if canonical(draw) != canonical(expected):
        raise ValueError("Ring attributes, geometry or paint differ from tokens")
    for e,name in zip(group.findall("PartImage"),("weather","heart")):
        if e.attrib!={**{k:str(v) for k,v in bounds(layout["regions"][name]).items()},
                      "name":"Glass_"+name} or len(e)!=1 or e[0].tag!="Image" or e[0].attrib!={"resource":RESOURCE}:
            raise ValueError("Wrong panel reference or bounds")
    # Check the entire material subtree, including any unexpected content.
    expected_group = ET.Element("Group", dict(group.attrib))
    node(expected_group, "Variant", mode="AMBIENT", target="alpha", value=0)
    expected_group.append(expected)
    for name in ("weather", "heart"):
        part = node(expected_group, "PartImage", **bounds(layout["regions"][name]), name="Glass_"+name)
        node(part, "Image", resource=RESOURCE)
    if canonical(group) != canonical(expected_group):
        raise ValueError("Unexpected material attributes or content")
    scene.remove(group)
    # Preserve text and tails, including Template mixed content.
    if canonical(root)!=canonical(ET.fromstring(original)):
        raise ValueError("Original information contract changed")


def generate(root=ROOT):
    raw={p:safe_path(root,p).read_bytes() for p in (ring.SOURCE,glass.SOURCE,material.SOURCE,optical.SOURCE,LAYOUT)}
    t=ring.parse(raw[ring.SOURCE])
    g=glass.parse(raw[glass.SOURCE])
    m=material.parse(raw[material.SOURCE])
    o=optical.parse(raw[optical.SOURCE])
    l=parse_layout(raw[LAYOUT])
    # Run the checked host generators before translating geometry.
    ring.generate(root)
    optical.verify_geometry(o,l,498)
    if not t["lighting"]==g["lighting"]==m["lighting"]==o["lighting"]:
        raise ValueError("Material light mismatch")
    w,h,rgba,ratios=visual.panel(g,m,o,498,"BALANCED","neutral")
    if 2*len(rgba)>100000:
        raise ValueError("Panel duplication budget exceeded")
    png=visual.compressed_png(w,h,rgba)
    original=basic(root)[BASIC]
    face=ET.fromstring(original)
    scene=face.find("Scene")
    group=ET.Element("Group",{"name":"SignatureMaterials","x":"0","y":"0","width":"450","height":"450"})
    node(group,"Variant",mode="AMBIENT",target="alpha",value=0)
    build_ring(group,t)
    for name in g["panelRegions"]:
        part=node(group,"PartImage",**bounds(l["regions"][name]),name="Glass_"+name)
        node(part,"Image",resource=RESOURCE)
    scene.insert(0,group)
    ET.indent(face,space="    ")
    xml=ET.tostring(face,encoding="utf-8",xml_declaration=True)+b"\n"
    check_face(xml,original,l,ring_tokens=t)
    report={"schemaVersion":1,"scope":"static Balanced material candidate; not runtime verified",
            "xmlSha256":digest(xml),"basicXmlSha256":digest(original),
            "panelSha256":digest(png),"panelRgbaSha256":digest(rgba),
            "panelDimensions":[w,h],"panelRgbaBytes":len(rgba),
            "duplicatePanelRgbaBytes":2*len(rgba),"panelContrast":ratios,
            "sourceSha256":{p:digest(v) for p,v in raw.items()},
            "ringTicks":60,"ambientDecoration":"hidden by Group Variant",
            "preview":"bootstrap placeholder; not candidate rendering",
            "runtimeVerification":"NOT RUN"}
    return xml,png,report


def inspect_material_apk(archive,face,png):
    names=archive.namelist()
    if len(names)!=len(set(names)):
        raise ValueError("Duplicate APK entry")
    if archive.read("res/raw/watchface.xml")!=face:
        raise ValueError("Candidate XML mismatch")
    if archive.read(PNG_PATH)!=png:
        raise ValueError("Candidate PNG bytes mismatch")
    if archive.testzip() is not None:
        raise ValueError("Corrupt candidate APK")


if __name__=="__main__":
    xml,png,report=generate()
    print("SIGNATURE_MATERIAL_RESULT "+json.dumps(report,sort_keys=True))
