"""Test the restricted preview subset and synthetic display branches."""
import copy
import json
import sys
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from generate_basic_face import generate as face, OUTPUT
from signature_preview import collect, generate, scenarios, expression, clock_text, PREFIX, render, font_text


class SignaturePreviewTests(unittest.TestCase):
    def setUp(self):
        self.xml = face()[OUTPUT]
        self.samples = {s["name"]: s for s in scenarios()}

    def texts(self, name):
        return [x["text"] for x in collect(self.xml, self.samples[name])]

    def test_all_screens_and_manifest(self):
        output = generate()
        self.assertEqual(len(output), 41)
        report = json.loads(output[f"{PREFIX}-manifest.json"])
        self.assertEqual(len(report["previews"]), 40)
        for record in report["previews"]:
            self.assertEqual(ET.fromstring(output[record["path"]]).get("width"), str(record["diameter"]))

    def test_deterministic(self):
        self.assertEqual(generate(), generate())

    def test_english_fahrenheit(self):
        self.assertIn("25°F", self.texts("en24-normal"))
        self.assertIn("Partly cloudy", self.texts("en24-normal"))

    def test_korean_celsius(self):
        self.assertIn("-4°C", self.texts("ko12-midnight"))
        self.assertIn("흐림", self.texts("ko12-midnight"))
        self.assertIn("12.31 · 목", self.texts("ko12-midnight"))

    def test_twelve_hour_midnight_and_noon(self):
        self.assertEqual(clock_text(self.samples["ko12-midnight"]), "12:00")
        self.assertEqual(clock_text(self.samples["ko12-noon"]), "12:00")
        self.assertEqual(clock_text(self.samples["en12-stale"]), "01:08")

    def test_twenty_four_hour(self):
        self.assertIn("23:59", self.texts("en24-normal"))
        self.assertIn("00:01", self.texts("en24-missing"))

    def test_missing_weather_and_zero_battery_steps(self):
        t = self.texts("en24-missing")
        for v in ("--", "-- bpm", "P --", "0%", "0 / 8000"):
            self.assertIn(v, t)
        self.assertNotIn("0°C", t)

    def test_weather_error(self):
        self.assertIn("ERR", self.texts("ko24-error"))

    def test_weather_stale(self):
        self.assertIn("! 25°F", self.texts("en12-stale"))
        self.assertIn("P ! 30%", self.texts("en12-stale"))

    def test_unknown_temperature_unit(self):
        self.assertIn("--", self.texts("en24-unknown-unit"))
        self.assertNotIn("25°F", self.texts("en24-unknown-unit"))

    def test_no_forecast(self):
        self.assertIn("P --", self.texts("ko24-no-forecast"))

    def test_aod_preserves_only_date_time(self):
        for name in ("en24-ambient", "ko12-ambient"):
            items = collect(self.xml, self.samples[name])
            expected = ["CoreDate", "CoreAmPm", "time"] if name == "ko12-ambient" else ["CoreDate", "time"]
            self.assertEqual([i["role"] for i in items], expected)
            self.assertEqual(items[-1]["weight"], "THIN")

    def test_missing_available_source_rejected(self):
        s = copy.deepcopy(self.samples["en24-normal"])
        del s["sources"]["WEATHER.TEMPERATURE"]
        with self.assertRaises(ValueError):
            collect(self.xml, s)

    def test_invalid_boolean_rejected(self):
        s = copy.deepcopy(self.samples["en24-normal"])
        s["sources"]["WEATHER.IS_AVAILABLE"] = 1
        with self.assertRaises(ValueError):
            collect(self.xml, s)

    def test_unknown_expression_rejected(self):
        with self.assertRaises(ValueError):
            expression("1+2", {})

    def test_unknown_element_rejected(self):
        with self.assertRaises(ValueError):
            collect(self.xml.replace(b"</Scene>", b"<PartImage /></Scene>"), self.samples["en24-normal"])

    def test_string_heart_value(self):
        s = copy.deepcopy(self.samples["en24-normal"])
        s["sources"]["HEART_RATE"] = "72.4"
        self.assertIn("72 bpm", [i["text"] for i in collect(self.xml, s)])

    def test_unsupported_diameter(self):
        with self.assertRaises(ValueError):
            render(collect(self.xml, self.samples["en24-normal"]), self.samples["en24-normal"], 500)

    def test_literal_percent_template(self):
        font = ET.fromstring('<Font><Template>%s%%<Parameter expression="[BATTERY_PERCENT]" /></Template></Font>')
        self.assertEqual(font_text(font, {"BATTERY_PERCENT": 0}), "0%")

    def test_invalid_percent_template(self):
        for fmt in ("%s%", "%d", "%s%%%", "%s%s"):
            with self.subTest(fmt=fmt):
                font = ET.fromstring(f'<Font><Template>{fmt}<Parameter expression="[BATTERY_PERCENT]" /></Template></Font>')
                with self.assertRaises(ValueError):
                    font_text(font, {"BATTERY_PERCENT": 85})

    def test_ampm_active_and_ambient(self):
        for name, expected in (("ko12-midnight", "AM"), ("ko12-noon", "PM"), ("en12-stale", "PM"), ("ko12-ambient", "PM")):
            with self.subTest(name=name):
                markers = [i["text"] for i in collect(self.xml, self.samples[name]) if i["role"] == "CoreAmPm"]
                self.assertEqual(markers, [expected])

    def test_24_hour_no_ampm(self):
        for name, sample in self.samples.items():
            if sample["hourFormat"] == 24:
                self.assertFalse(any(i["role"] == "CoreAmPm" for i in collect(self.xml, sample)), name)

    def test_24_hour_does_not_read_ampm(self):
        s = copy.deepcopy(self.samples["en24-normal"])
        del s["sources"]["AMPM_STRING"]
        self.assertIn("23:59", [i["text"] for i in collect(self.xml, s)])

    def test_12_hour_missing_ampm_rejected(self):
        s = copy.deepcopy(self.samples["ko12-midnight"])
        del s["sources"]["AMPM_STRING"]
        with self.assertRaises(ValueError):
            collect(self.xml, s)

    def test_wrong_hour_mode_rejected(self):
        s = copy.deepcopy(self.samples["ko12-noon"])
        s["sources"]["IS_24_HOUR_MODE"] = True
        with self.assertRaises(ValueError):
            collect(self.xml, s)

    def test_invalid_ampm_rejected(self):
        s = copy.deepcopy(self.samples["ko12-noon"])
        s["sources"]["AMPM_STRING"] = "AM"
        with self.assertRaises(ValueError):
            collect(self.xml, s)
        s["sources"]["AMPM_STRING"] = "UNKNOWN"
        with self.assertRaises(ValueError):
            collect(self.xml, s)
