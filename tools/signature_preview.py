"""Render a restricted Signature XML subset into synthetic host SVG evidence.

This is not a Wear OS renderer. Reject unsupported expressions and elements.
"""
import argparse
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET

from generate_bootstrap import ROOT, safe_path, check_outputs, rect
from generate_basic_face import OUTPUT as FACE_OUTPUT, generate as generate_face
from round_layout import DIAMETERS, inside_circle, project

PREFIX = "assets/generated/layouts/basic-preview"
BOOL_KEYS = {"WEATHER.IS_AVAILABLE", "WEATHER.IS_ERROR", "WEATHER.DAYS.0.IS_AVAILABLE"}
INT_KEYS = {"BATTERY_PERCENT", "STEP_COUNT", "STEP_GOAL", "WEATHER.TEMPERATURE",
            "WEATHER.TEMPERATURE_UNIT", "WEATHER.DAYS.0.CHANCE_OF_PRECIPITATION"}
STR_KEYS = {"MONTH_Z", "DAY_Z", "DAY_OF_WEEK_S", "WEATHER.CONDITION_NAME"}
TAGS = {"WatchFace", "Metadata", "Scene", "Group", "Variant", "PartText", "Text",
        "Font", "Template", "Parameter", "Condition", "Expressions", "Expression",
        "Compare", "Default", "DigitalClock", "TimeText"}


def scenario(name, locale, hour, minute, hour_format, ambient=False, weather="normal"):
    """Use only synthetic source values. Omit unavailable forecast values."""
    if locale not in ("en-US", "ko-KR") or hour_format not in (12, 24):
        raise ValueError("Unsupported synthetic locale or hour format")
    if type(hour) is not int or type(minute) is not int or not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError("Invalid synthetic time")
    sources = {"MONTH_Z": "12", "DAY_Z": "31",
               "DAY_OF_WEEK_S": "목" if locale == "ko-KR" else "Thu",
               "BATTERY_PERCENT": 85, "STEP_COUNT": 6420, "STEP_GOAL": 8000, "HEART_RATE": 72,
               "WEATHER.IS_AVAILABLE": weather not in ("missing", "error"),
               "WEATHER.IS_ERROR": weather in ("stale", "error")}
    if sources["WEATHER.IS_AVAILABLE"]:
        sources.update({"WEATHER.CONDITION_NAME": "흐림" if locale == "ko-KR" else "Partly cloudy",
                        "WEATHER.TEMPERATURE": -4 if locale == "ko-KR" else 25,
                        "WEATHER.TEMPERATURE_UNIT": 1 if locale == "ko-KR" else 2,
                        "WEATHER.DAYS.0.IS_AVAILABLE": weather != "no-forecast"})
        if sources["WEATHER.DAYS.0.IS_AVAILABLE"]:
            sources["WEATHER.DAYS.0.CHANCE_OF_PRECIPITATION"] = 30
    if weather in ("missing", "error"):
        sources["HEART_RATE"] = 0
    if weather == "missing":
        sources["STEP_COUNT"] = 0
        sources["BATTERY_PERCENT"] = 0
    if weather == "unknown-unit":
        sources["WEATHER.TEMPERATURE_UNIT"] = 0
    return {"name": name, "locale": locale, "hour": hour, "minute": minute,
            "hourFormat": hour_format, "ambient": ambient, "sources": sources}


def scenarios():
    return [
        scenario("en24-normal", "en-US", 23, 59, 24),
        scenario("ko12-midnight", "ko-KR", 0, 0, 12),
        scenario("ko12-noon", "ko-KR", 12, 0, 12),
        scenario("en24-missing", "en-US", 0, 1, 24, weather="missing"),
        scenario("en12-stale", "en-US", 13, 8, 12, weather="stale"),
        scenario("ko24-error", "ko-KR", 9, 59, 24, weather="error"),
        scenario("ko24-no-forecast", "ko-KR", 10, 8, 24, weather="no-forecast"),
        scenario("en24-unknown-unit", "en-US", 10, 8, 24, weather="unknown-unit"),
        scenario("en24-ambient", "en-US", 23, 59, 24, ambient=True),
        scenario("ko12-ambient", "ko-KR", 12, 0, 12, ambient=True),
    ]


def source(data, key):
    if key not in data:
        raise ValueError("Missing synthetic source: " + key)
    value = data[key]
    if key in BOOL_KEYS and type(value) is bool:
        return value
    if key in INT_KEYS and type(value) is int:
        return value
    if key in STR_KEYS and isinstance(value, str) and value.strip():
        return value
    if key == "HEART_RATE":
        if type(value) in (float, int) or (type(value) is str and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value)):
            result = float(value)
            if math.isfinite(result):
                return result
    raise ValueError("Unsupported source or type: " + key)


def expression(text, data):
    """Evaluate only expressions used by this candidate."""
    if not isinstance(text, str):
        raise ValueError("Missing expression")
    if text == "[HEART_RATE] > 0 && [HEART_RATE] <= 240":
        return 0 < source(data, "HEART_RATE") <= 240
    if text == "round([HEART_RATE])":
        return math.floor(source(data, "HEART_RATE") + 0.5)
    if text in ("[WEATHER.TEMPERATURE_UNIT] == 1", "[WEATHER.TEMPERATURE_UNIT] == 2"):
        return source(data, "WEATHER.TEMPERATURE_UNIT") == int(text[-1])
    match = re.fullmatch(r"\[([A-Z0-9_.]+)\]", text)
    if match:
        return source(data, match[1])
    raise ValueError("Unsupported preview expression: " + text)


def font_text(font, data):
    children = list(font)
    if not children:
        if not font.text:
            raise ValueError("Empty literal font")
        return font.text.strip()
    if len(children) != 1 or children[0].tag != "Template":
        raise ValueError("Unsupported Font content")
    t = children[0]
    fmt = (t.text or "").strip()
    if re.fullmatch(r"(?:[^%]|%s|%%)+", fmt) is None:
        raise ValueError("Unsupported template format")
    params = []
    for p in t:
        if p.tag != "Parameter" or set(p.attrib) != {"expression"} or len(p):
            raise ValueError("Unsupported template parameter")
        params.append(expression(p.get("expression"), data))
    if len(re.findall(r"%s|%%", fmt)) == 0 or len([x for x in re.findall(r"%s|%%", fmt) if x == "%s"]) != len(params):
        raise ValueError("Template arity mismatch")
    try:
        return fmt % tuple(params)
    except (TypeError, ValueError) as exc:
        raise ValueError("Template formatting failed") from exc


def selected(condition, data):
    children = list(condition)
    if len(children) < 3 or children[0].tag != "Expressions" or children[-1].tag != "Default":
        raise ValueError("Unsupported Condition structure")
    expressions = {}
    for e in children[0]:
        name = e.get("name")
        if e.tag != "Expression" or not name or name in expressions:
            raise ValueError("Invalid Condition expression name")
        expressions[name] = e.text
    comparisons = children[1:-1]
    names = [c.get("expression") for c in comparisons]
    if set(names) != set(expressions) or len(names) != len(expressions):
        raise ValueError("Unmatched Condition expressions")
    if any(c.tag != "Compare" or len(c) != 1 for c in comparisons) or len(children[-1]) != 1:
        raise ValueError("Expected single-child comparison and fallback")
    for c in comparisons:
        result = expression(expressions[c.get("expression")], data)
        if type(result) is not bool:
            raise ValueError("Condition did not return Boolean")
        if result:
            return c[0]
    return children[-1][0]


def alpha(element, ambient):
    value = int(element.get("alpha", "255"))
    variants = element.findall("Variant")
    if len(variants) > 1:
        raise ValueError("Unsupported preview Variant count")
    for v in variants:
        if set(v.attrib) != {"mode", "target", "value"} or v.get("mode") != "AMBIENT" or v.get("target") != "alpha":
            raise ValueError("Unsupported preview Variant")
        if ambient:
            value = int(v.get("value"))
    if value not in (0, 255):
        raise ValueError("Unsupported preview alpha")
    return value


def box_at(element, offset):
    x, y, w, h = [int(element.get(k)) for k in ("x", "y", "width", "height")]
    b = [x + offset[0], y + offset[1], w, h]
    rect(b, 450, element.tag)
    return b


def clock_text(sample):
    hour = sample["hour"]
    if sample["hourFormat"] == 12:
        hour = hour % 12 or 12
    elif sample["hourFormat"] != 24:
        raise ValueError("Unsupported synthetic clock mode")
    return f"{hour:02d}:{sample['minute']:02d}"


def collect(xml, sample):
    root = ET.fromstring(xml)
    if root.tag != "WatchFace" or root.attrib != {"width": "450", "height": "450"}:
        raise ValueError("Unsupported preview canvas")
    if any(e.tag not in TAGS for e in root.iter()):
        raise ValueError("Unsupported preview element")
    scenes = root.findall("Scene")
    if len(scenes) != 1 or scenes[0].get("backgroundColor") != "#FF000000":
        raise ValueError("Unsupported preview scene")
    items = []
    data = sample["sources"]
    ambient = sample["ambient"]

    def emit(element, font, box, text, role):
        size = int(font.get("size"))
        color = font.get("color", "")
        weight = font.get("weight", "NORMAL")
        if (not 0 < size <= box[3] or font.get("family") != "SYNC_TO_DEVICE"
                or not re.fullmatch(r"#FF[0-9A-F]{6}", color) or weight not in ("NORMAL", "THIN")):
            raise ValueError("Unsupported preview font")
        if not inside_circle(box, 450, 12):
            raise ValueError("Visible text outside round safe area")
        items.append({"role": role, "text": text, "box": box, "fontSize": size,
                      "color": "#" + color[3:], "weight": weight})

    def walk(e, offset=(0, 0)):
        if e.tag == "Variant":
            return
        if e.tag == "Condition":
            walk(selected(e, data), offset)
            return
        if e.tag in ("Group", "DigitalClock"):
            box = box_at(e, offset)
            if alpha(e, ambient) == 0:
                return
            for c in e:
                walk(c, tuple(box[:2]))
            return
        if e.tag == "PartText":
            if alpha(e, ambient) == 0:
                return
            txt = e.find("Text")
            if txt is None or txt.attrib != {"align": "CENTER"} or len(txt) != 1 or txt[0].tag != "Font":
                raise ValueError("Unsupported PartText")
            emit(e, txt[0], box_at(e, offset), font_text(txt[0], data), e.get("name", "info"))
            return
        if e.tag == "TimeText":
            if alpha(e, ambient) == 0:
                return
            if e.get("format") != "hh:mm" or e.get("hourFormat") != "SYNC_TO_DEVICE" or e.get("align") != "CENTER":
                raise ValueError("Unsupported TimeText")
            fonts = e.findall("Font")
            if len(fonts) != 1:
                raise ValueError("Expected one TimeText Font")
            emit(e, fonts[0], box_at(e, offset), clock_text(sample), "time")
            return
        raise ValueError("Unsupported preview branch: " + e.tag)

    for e in scenes[0]:
        walk(e)
    roles = [i["role"] for i in items]
    if roles.count("CoreDate") != 1 or roles.count("time") != 1:
        raise ValueError("Missing or duplicate core time/date")
    if ambient and len(items) != 2:
        raise ValueError("Unexpected ambient data")
    return items


def render(items, sample, diameter):
    """Render logical rectangles; no actual glyph or display measurement."""
    if diameter not in DIAMETERS:
        raise ValueError("Unsupported screen")
    root = ET.Element("svg", {"xmlns": "http://www.w3.org/2000/svg", "width": str(diameter),
                             "height": str(diameter), "viewBox": f"0 0 {diameter} {diameter}"})
    ET.SubElement(root, "title").text = "AURA synthetic host preview — not a runtime screenshot"
    ET.SubElement(root, "desc").text = sample["name"] + "; synthetic data; system font approximation"
    ET.SubElement(root, "circle", {"cx": str(diameter//2), "cy": str(diameter//2), "r": str(diameter//2), "fill": "#000000"})
    for i in items:
        x, y, w, h = project(i["box"], diameter)
        if not inside_circle([x,y,w,h], diameter, (12*diameter+449)//450):
            raise ValueError("Projected text rectangle outside safe area")
        ET.SubElement(root, "text", {"x": str(x+w/2), "y": str(y+h/2),
            "text-anchor": "middle", "dominant-baseline": "central", "font-family": "sans-serif",
            "font-size": str(i["fontSize"]*diameter//450), "font-weight": "200" if i["weight"] == "THIN" else "400",
            "fill": i["color"], "data-role": i["role"]}).text = i["text"]
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8") + b"\n"


def generate(root=ROOT):
    xml = generate_face(root)[FACE_OUTPUT]
    outputs = {}
    records = []
    for s in scenarios():
        items = collect(xml, s)
        for d in DIAMETERS:
            path = f"{PREFIX}-{s['name']}-{d}.svg"
            data = render(items, s, d)
            outputs[path] = data
            records.append({"scenario": s["name"], "locale": s["locale"], "hourFormat": s["hourFormat"],
                            "ambient": s["ambient"], "diameter": d,
                            "expectedAmPm": ("AM" if s["hour"] < 12 else "PM") if s["hourFormat"] == 12 else None,
                            "amPmRendered": False, "items": items, "path": path,
                            "sha256": hashlib.sha256(data).hexdigest()})
    report = {"schemaVersion": 1, "scope": "synthetic host subset, not Wear OS rendering or glyph measurement",
              "sourceXmlSha256": hashlib.sha256(xml).hexdigest(), "previews": records}
    outputs[f"{PREFIX}-manifest.json"] = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)+"\n").encode("utf-8")
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
    for name, data in sorted(outputs.items()):
        print(f"PREVIEW_RESULT {name} {hashlib.sha256(data).hexdigest()}")
    print("PASS: 40 synthetic Signature previews and manifest")


if __name__ == "__main__":
    main()
