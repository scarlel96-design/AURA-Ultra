"""Generate a resource-only Signature basic-face candidate from round layout tokens."""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET

from generate_bootstrap import ROOT, safe_path, check_outputs
from round_layout import SOURCE, parse

OUTPUT = "assets/generated/layouts/signature-basic.xml"


def node(parent, tag, **attrs):
    return ET.SubElement(parent, tag, {key: str(value) for key, value in attrs.items()})


def bounds(box):
    return dict(zip(("x", "y", "width", "height"), box))


def part(parent, box, size, color, text, expressions=(), name=None, weight=None):
    attrs = bounds(box)
    if name:
        attrs["name"] = name
    p = node(parent, "PartText", **attrs)
    attrs = {"family": "SYNC_TO_DEVICE", "size": size, "color": color}
    if weight:
        attrs["weight"] = weight
    font = node(node(p, "Text", align="CENTER"), "Font", **attrs)
    if expressions:
        template = node(font, "Template")
        template.text = text
        for expression in expressions:
            node(template, "Parameter", expression=expression)
    else:
        font.text = text
    return p


def condition(parent, cases, default):
    c = node(parent, "Condition")
    es = node(c, "Expressions")
    for name, expr, _ in cases:
        node(es, "Expression", name=name).text = expr
    for name, _, emit in cases:
        emit(node(c, "Compare", expression=name))
    default(node(c, "Default"))
    return c


def candidate(layout):
    r, fonts = layout["regions"], layout["fontSizes"]
    primary, muted, cyan, pink, warn = "#FFF3F7FA", "#FFA9BACB", "#FF79D4F2", "#FFF29AA8", "#FFFFA84D"
    root = ET.Element("WatchFace", {"width": "450", "height": "450"})
    node(root, "Metadata", key="CLOCK_TYPE", value="DIGITAL")
    node(root, "Metadata", key="PREVIEW_TIME", value="10:08:00")
    scene = node(root, "Scene", backgroundColor="#FF000000")
    active = node(scene, "Group", name="ActiveInformation", x=0, y=0, width=450, height=450)
    node(active, "Variant", mode="AMBIENT", target="alpha", value=0)
    part(active, r["brand"], fonts["brand"], cyan, "AURA ULTRA")
    part(active, r["battery"], fonts["battery"], cyan, "%s%%", ("[BATTERY_PERCENT]",))
    part(active, r["steps"], fonts["steps"], muted, "%s / %s", ("[STEP_COUNT]", "[STEP_GOAL]"))
    def split(name):
        x,y,w,h = r[name]
        return [x,y,w,18], [x,y+18,w,h-18]
    weather_title, weather_value = split("weather")
    heart_title, heart_value = split("heart")

    def weather_available(parent):
        g = node(parent, "Group", x=0, y=0, width=450, height=450)
        part(g, weather_title, 14, muted, "%s", ("[WEATHER.CONDITION_NAME]",))
        def unit(parent, error):
            prefix = "! " if error else ""
            color = warn if error else cyan
            condition(parent, [
                ("celsius", "[WEATHER.TEMPERATURE_UNIT] == 1",
                 lambda p: part(p, weather_value, fonts["weather"], color, prefix+"%s°C", ("[WEATHER.TEMPERATURE]",))),
                ("fahrenheit", "[WEATHER.TEMPERATURE_UNIT] == 2",
                 lambda p: part(p, weather_value, fonts["weather"], color, prefix+"%s°F", ("[WEATHER.TEMPERATURE]",))),
            ], lambda p: part(p, weather_value, fonts["weather"], warn, prefix+"--"))
        condition(g, [("refresh_error", "[WEATHER.IS_ERROR]", lambda p: unit(p, True))],
                  lambda p: unit(p, False))

    def weather_unavailable(parent):
        g = node(parent, "Group", x=0, y=0, width=450, height=450)
        part(g, weather_title, 14, muted, "WX")
        condition(g, [("load_error", "[WEATHER.IS_ERROR]", lambda p: part(p, weather_value, fonts["weather"], warn, "ERR"))],
                  lambda p: part(p, weather_value, fonts["weather"], muted, "--"))

    condition(active, [("weather_available", "[WEATHER.IS_AVAILABLE]", weather_available)], weather_unavailable)
    part(active, heart_title, 14, muted, "HR")
    condition(active, [("hr_present", "[HEART_RATE] > 0 && [HEART_RATE] <= 240",
                       lambda p: part(p, heart_value, fonts["heart"], pink, "%s bpm", ("round([HEART_RATE])",)))],
              lambda p: part(p, heart_value, fonts["heart"], muted, "-- bpm"))

    def rain_available(parent):
        condition(parent, [("today_available", "[WEATHER.DAYS.0.IS_AVAILABLE]", lambda p:
            condition(p, [("rain_refresh_error", "[WEATHER.IS_ERROR]", lambda q:
                part(q, r["rain"], fonts["rain"], warn, "P ! %s%%", ("[WEATHER.DAYS.0.CHANCE_OF_PRECIPITATION]",)))],
                lambda q: part(q, r["rain"], fonts["rain"], cyan, "P %s%%", ("[WEATHER.DAYS.0.CHANCE_OF_PRECIPITATION]",))))],
            lambda p: part(p, r["rain"], fonts["rain"], muted, "P --"))
    condition(active, [("rain_weather_available", "[WEATHER.IS_AVAILABLE]", rain_available)],
              lambda p: part(p, r["rain"], fonts["rain"], muted, "P --"))

    # Keep date independent of external data and before the dynamic clock.
    part(scene, r["date"], fonts["date"], muted, "%s.%s · %s", ("[MONTH_Z]", "[DAY_Z]", "[DAY_OF_WEEK_S]"), name="CoreDate")
    clock = node(scene, "DigitalClock", **bounds(r["time"]))
    _,_,w,h = r["time"]
    for alpha, ambient, weight, color in [(255,0,"NORMAL",primary),(0,255,"THIN","#FFB7C0C9")]:
        t = node(clock, "TimeText", x=0, y=0, width=w, height=h, format="hh:mm", hourFormat="SYNC_TO_DEVICE", align="CENTER", alpha=alpha)
        node(t, "Variant", mode="AMBIENT", target="alpha", value=ambient)
        node(t, "Font", family="SYNC_TO_DEVICE", size=fonts["time"], color=color, weight=weight)
    ET.indent(root, space="    ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)+b"\n"


def generate(root=ROOT):
    return {OUTPUT: candidate(parse(safe_path(root, SOURCE).read_bytes()))}


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
    for name, data in outputs.items():
        print("BASIC_FACE_RESULT " + json.dumps({"path": name, "sha256": hashlib.sha256(data).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
