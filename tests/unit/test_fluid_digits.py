"""Exercise M02 boundaries, fallback and invalid evidence."""
import copy
import json
import sys
import unittest
from datetime import datetime, timedelta
from fractions import Fraction
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
from fluid_digits import ClockSample,plan,digit_frame,verify_frame,audit_day,DURATION_MS


def sample(h,m,day=1,hour24=True,offset=540,zone="test"):
    return ClockSample(datetime(2026,1,day,h,m),offset,zone,hour24)


class FluidDigitsTests(unittest.TestCase):
    def test_full_day_both_formats(self):
        result = audit_day()
        self.assertEqual(result["transitions"],2880)
        self.assertEqual(result["frames"],8640)
        self.assertEqual(result["runtimeVerification"],"NOT RUN")
        print("FLUID_DIGITS_RESULT "+json.dumps(result,sort_keys=True))

    def test_single_digit_and_stable_colon(self):
        t = plan(sample(10,8),sample(10,9))
        self.assertEqual(t.changed,(4,))
        self.assertEqual(t.duration_ms,DURATION_MS)
        v = digit_frame(t,110)
        self.assertEqual(v["colon"],":")
        self.assertEqual(v["slots"][4],[
            {"symbol":"8","offset":Fraction(-1,2),"alpha":Fraction(1,2)},
            {"symbol":"9","offset":Fraction(1,2),"alpha":Fraction(1,2)}])
        for i in (0,1,3):
            self.assertEqual(v["slots"][i],[{"symbol":t.current.text[i],
                       "offset":Fraction(0),"alpha":Fraction(1)}])

    def test_hour_rollover(self):
        t = plan(sample(9,59),sample(10,0))
        self.assertEqual(t.changed,(0,1,3,4))
        self.assertEqual(digit_frame(t,0)["visualAnchor"],"09:59")
        self.assertEqual(digit_frame(t,220)["visualAnchor"],"10:00")

    def test_midnight_coherent_metadata(self):
        for fmt,old,new in ((True,"23:59","00:00"),(False,"11:59","12:00")):
            t = plan(sample(23,59,hour24=fmt),sample(0,0,day=2,hour24=fmt))
            self.assertEqual(t.duration_ms,220)
            a,b = digit_frame(t,109),digit_frame(t,110)
            self.assertEqual((a["visualAnchor"],b["visualAnchor"]),(old,new))
            self.assertEqual((a["visualDate"],b["visualDate"]),("2026-01-01","2026-01-02"))
            self.assertEqual(a["semanticDate"],"2026-01-02")
            self.assertEqual((a["visualMarker"],b["visualMarker"]),
                             ("","") if fmt else ("PM","AM"))

    def test_noon_marker(self):
        t = plan(sample(11,59,hour24=False),sample(12,0,hour24=False))
        self.assertEqual(digit_frame(t,109)["visualMarker"],"AM")
        self.assertEqual(digit_frame(t,110)["visualMarker"],"PM")

    def test_format_change_static(self):
        t = plan(sample(13,20),sample(13,20,hour24=False))
        self.assertEqual((t.reason,t.duration_ms),("format-change",0))
        self.assertEqual(digit_frame(t,0)["semanticTime"],"01:20")
        self.assertEqual(digit_frame(t,0)["visualMarker"],"PM")

    def test_skip_backward_duplicate(self):
        for old,new,reason in ((sample(10,8),sample(10,10),"non-adjacent"),
                              (sample(10,8),sample(10,7),"non-adjacent"),
                              (sample(10,8),sample(10,8),"unchanged")):
            t = plan(old,new)
            self.assertEqual((t.reason,t.duration_ms),(reason,0))
            self.assertEqual(digit_frame(t,0)["visualAnchor"],new.text)

    def test_zone_and_offset_change(self):
        for new in (sample(10,9,offset=480),sample(10,9,zone="other")):
            t = plan(sample(10,8),new)
            self.assertEqual((t.reason,t.duration_ms),("zone-change",0))

    def test_ambient_reduced_profiles_interruption(self):
        for kwargs in ({"profile":2},{"profile":3},{"ambient":True},{"reduced":True},
                       {"interrupted":True},{"resync":True}):
            t = plan(sample(10,8),sample(10,9),**kwargs)
            self.assertEqual(t.duration_ms,0)
            self.assertEqual(digit_frame(t,0)["visualAnchor"],"10:09")

    def test_completion_clamps(self):
        t = plan(sample(10,8),sample(10,9))
        self.assertEqual(digit_frame(t,220),digit_frame(t,1000000))

    def test_invalid_inputs(self):
        for kwargs in ({"profile":True},{"profile":6},{"ambient":1},{"reduced":None}):
            with self.assertRaises(ValueError):
                plan(sample(10,8),sample(10,9),**kwargs)
        with self.assertRaises(ValueError):
            ClockSample(datetime(2026,1,1,10,8,1),540,"test",True)
        with self.assertRaises(ValueError):
            sample(10,8,offset=True)
        with self.assertRaises(ValueError):
            sample(10,8,zone="")
        with self.assertRaises(ValueError):
            digit_frame(plan(sample(10,8),sample(10,9)),-1)

    def test_mutated_frame_rejected(self):
        t = plan(sample(10,8),sample(10,9))
        for mutate in (lambda v:v["slots"].pop(4),
                       lambda v:v["slots"][4][0].update(symbol="0"),
                       lambda v:v["slots"][4][0].update(alpha=Fraction(0)),
                       lambda v:v["slots"][4][1].update(offset=Fraction(2)),
                       lambda v:v.update(semanticTime="10:08"),
                       lambda v:v.update(visualMarker="PM"),
                       lambda v:v.update(colon=" ")):
            v = copy.deepcopy(digit_frame(t,110))
            mutate(v)
            with self.assertRaises(ValueError):
                verify_frame(t,110,v)

    def test_month_year_and_leap_rollover(self):
        for civil in (datetime(2024,2,29,23,59),datetime(2026,12,31,23,59)):
            a,b = (ClockSample(d,0,"test",True) for d in (civil,civil+timedelta(minutes=1)))
            t = plan(a,b)
            self.assertEqual(t.duration_ms,220)
            self.assertEqual(digit_frame(t,220)["semanticDate"],b.civil.date().isoformat())
