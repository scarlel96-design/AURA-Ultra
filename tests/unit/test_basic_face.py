"""Test the basic display candidate independently of the Wear OS renderer."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from generate_basic_face import generate, OUTPUT
from generate_bootstrap import ROOT, FACE
from round_layout import parse, SOURCE


class BasicFaceTests(unittest.TestCase):
    def setUp(self):
        self.xml = generate()[OUTPUT]
        self.face = ET.fromstring(self.xml)
        self.scene = self.face.find("Scene")
        self.active = self.scene.find("Group")

    def test_deterministic(self):
        self.assertEqual(self.xml, generate()[OUTPUT])

    def test_product_unchanged(self):
        self.assertNotEqual(self.xml, (ROOT / FACE).read_bytes())

    def test_native_clock(self):
        times = self.scene.findall("DigitalClock/TimeText")
        self.assertEqual(len(times), 2)
        for t in times:
            self.assertEqual(t.get("hourFormat"), "SYNC_TO_DEVICE")
            self.assertEqual(t.get("format"), "hh:mm")
        self.assertEqual([t.get("alpha") for t in times], ["255", "0"])
        self.assertEqual([t.find("Variant").get("value") for t in times], ["0", "255"])

    def test_date_not_hidden_by_active_group(self):
        date = self.scene.find("PartText[@name='CoreDate']")
        self.assertIsNotNone(date)
        self.assertEqual([p.get("expression") for p in date.findall(".//Parameter")],
                         ["[MONTH_Z]", "[DAY_Z]", "[DAY_OF_WEEK_S]"])
        self.assertFalse(date.findall("Variant"))

    def test_active_only(self):
        self.assertEqual(self.active.find("Variant").attrib, {"mode":"AMBIENT","target":"alpha","value":"0"})

    def test_geometry_core(self):
        layout = parse((ROOT / SOURCE).read_bytes())
        for name, p in [("date", self.scene.find("PartText")), ("time", self.scene.find("DigitalClock"))]:
            self.assertEqual([int(p.get(k)) for k in ("x","y","width","height")], layout["regions"][name])

    def test_weather_guard(self):
        c = self.active.find("Condition")
        self.assertEqual(c.find("Expressions/Expression").text, "[WEATHER.IS_AVAILABLE]")
        self.assertIn("[WEATHER.CONDITION_NAME]", [p.get("expression") for p in c.findall("Compare//Parameter")])
        self.assertFalse(c.findall("Default//Parameter"))
        self.assertEqual({p.text for p in c.findall("Default//Font") if p.text}, {"WX","ERR","--"})

    def test_weather_units_and_error(self):
        c = self.active.find("Condition")
        texts = {t.text for t in c.findall("Compare//Template")}
        self.assertTrue({"%s°C", "%s°F", "! %s°C", "! %s°F"} <= texts)
        expr = {e.text for e in c.findall("Compare//Expression")}
        self.assertTrue({"[WEATHER.IS_ERROR]", "[WEATHER.TEMPERATURE_UNIT] == 1", "[WEATHER.TEMPERATURE_UNIT] == 2"} <= expr)

    def test_heart_zero_fallback(self):
        c = self.active.findall("Condition")[1]
        self.assertEqual(c.find("Expressions/Expression").text, "[HEART_RATE] > 0 && [HEART_RATE] <= 240")
        self.assertEqual(c.find("Default//Font").text, "-- bpm")

    def test_rain_forecast_guard(self):
        c = self.active.findall("Condition")[2]
        self.assertEqual(c.find("Expressions/Expression").text, "[WEATHER.IS_AVAILABLE]")
        self.assertIn("[WEATHER.DAYS.0.IS_AVAILABLE]", {e.text for e in c.findall("Compare//Expression")})
        self.assertEqual(c.find("Default//Font").text, "P --")
        self.assertFalse(c.findall("Default//Parameter"))

    def test_native_battery_steps(self):
        params = {p.get("expression") for p in self.active.findall(".//Parameter")}
        self.assertTrue({"[BATTERY_PERCENT]", "[STEP_COUNT]", "[STEP_GOAL]"} <= params)

    def test_group_names_required_and_unique(self):
        names = [g.get("name") for g in self.face.findall(".//Group")]
        self.assertEqual(set(names), {"ActiveInformation", "WeatherAvailable", "WeatherUnavailable"})
        self.assertEqual(len(names), len(set(names)))

    def test_ampm_guard_and_source(self):
        c = self.scene.find("Condition")
        self.assertEqual(c.find("Expressions/Expression").text, "![IS_24_HOUR_MODE]")
        self.assertIsNone(c.find("Default"))
        marker = c.find("Compare/PartText")
        self.assertEqual(marker.get("name"), "CoreAmPm")
        self.assertEqual(marker.find(".//Parameter").get("expression"), "[AMPM_STRING]")
        self.assertEqual([int(marker.get(k)) for k in ("x","y","width","height")], parse((ROOT / SOURCE).read_bytes())["regions"]["ampm"])
        self.assertFalse(marker.findall("Variant"))
