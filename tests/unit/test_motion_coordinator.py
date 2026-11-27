"""Test core motion priority, reentry and static fallback."""
import copy
import json
import sys
import unittest
from dataclasses import replace
from datetime import datetime,timedelta
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
from fluid_digits import ClockSample
from motion_events import Sample
from motion_coordinator import Request,advance,render,verify,audit_reentry,load


class MotionCoordinatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets = load()

    def setUp(self):
        self.clock = ClockSample(datetime(2026,1,1,10,8),0,"test",True)
        self.next_clock = replace(self.clock,civil=self.clock.civil+timedelta(minutes=1))
        self.initial = Sample(0,charging=False,weather="CLEAR",gauge_permille=100)
        self.base = advance(None,Request(self.initial,self.clock)).state

    def request(self,tick,clock=None,delta=0,resync=False,**kwargs):
        return Request(replace(self.initial,tick_ms=tick,**kwargs),
                       self.clock if clock is None else clock,delta,resync)

    def test_all_reentry_positions(self):
        r = audit_reentry(self.assets)
        self.assertEqual(r["positions"],1001)
        self.assertEqual(r["reentryComparisons"],2002)
        self.assertEqual(r["sampledGeometryChecks"],44)
        self.assertEqual(r["runtimeVerification"],"NOT RUN")
        print("MOTION_COORDINATOR_RESULT "+json.dumps(r,sort_keys=True))

    def test_sleep_reverse_and_finish(self):
        a = advance(self.base,self.request(1,ambient=True)).state
        b = advance(a,self.request(2,ambient=True,delta=400)).state
        self.assertEqual(b.progress,600)
        c = advance(b,self.request(3)).state
        self.assertEqual(render(b,self.assets),render(c,self.assets))
        d = advance(c,self.request(4,delta=1000)).state
        self.assertEqual(d.progress,1000)
        self.assertFalse(d.moving)

    def test_digit_blocks_decoration_and_updates_data(self):
        r = advance(self.base,self.request(1,self.next_clock,charging=True))
        self.assertIsNotNone(r.state.digits)
        self.assertIsNone(r.state.events.active)
        self.assertEqual(r.event.dropped,("M14",))
        self.assertTrue(r.state.events.sample.charging)
        self.assertEqual(render(r.state,self.assets)["clock"]["semanticTime"],"10:09")

    def test_digit_cancelled_by_sleep(self):
        a = advance(self.base,self.request(1,self.next_clock)).state
        r = advance(a,self.request(2,self.next_clock,ambient=True))
        self.assertIsNone(r.state.digits)
        self.assertIsNone(r.state.events.active)
        self.assertEqual(render(r.state,self.assets)["clock"]["visualAnchor"],"10:09")

    def test_clock_change_mid_m01_snaps_and_no_replay(self):
        a = advance(self.base,self.request(1,ambient=True)).state
        b = advance(a,self.request(2,self.next_clock,delta=400,ambient=True)).state
        c = advance(b,self.request(3,self.next_clock,weather="RAIN")).state
        d = advance(c,self.request(4,self.next_clock,delta=1000,weather="RAIN")).state
        self.assertIsNone(d.digits)
        self.assertIsNone(d.events.active)
        self.assertEqual(render(d,self.assets)["clock"]["visualAnchor"],"10:09")

    def test_existing_effect_cancelled_by_digit(self):
        a = advance(self.base,self.request(1,charging=True)).state
        self.assertEqual(a.events.active.kind,"M14")
        r = advance(a,self.request(2,self.next_clock,charging=True))
        self.assertEqual(r.event.cancelled,"M14")
        self.assertIsNotNone(r.state.digits)
        self.assertIsNone(r.state.events.active)

    def test_existing_effect_cancelled_by_m01(self):
        a = advance(self.base,self.request(1,weather="RAIN")).state
        r = advance(a,self.request(2,ambient=True,weather="RAIN"))
        self.assertEqual(r.event.cancelled,"M09")
        self.assertTrue(r.state.moving)

    def test_exact_digit_end_and_no_event_replay(self):
        a = advance(self.base,self.request(1,self.next_clock,charging=True)).state
        b = advance(a,self.request(220,self.next_clock,charging=True)).state
        self.assertIsNotNone(b.digits)
        c = advance(b,self.request(221,self.next_clock,charging=True)).state
        self.assertIsNone(c.digits)
        self.assertIsNone(c.events.active)
        self.assertEqual(render(c,self.assets)["clock"]["visualAnchor"],"10:09")

    def test_rapid_second_clock_change_snaps(self):
        a = advance(self.base,self.request(1,self.next_clock)).state
        next2 = replace(self.next_clock,civil=self.next_clock.civil+timedelta(minutes=1))
        b = advance(a,self.request(2,next2)).state
        self.assertIsNone(b.digits)
        self.assertEqual(render(b,self.assets)["clock"]["visualAnchor"],"10:10")

    def test_protection_and_static_geometry(self):
        a = advance(self.base,self.request(1,ambient=True)).state
        b = advance(a,self.request(2,ambient=True,delta=400)).state
        for flags in ({"reduced":True},{"quality":"ECO"},{"profile":3}):
            c = advance(b,self.request(3,ambient=True,**flags)).state
            self.assertEqual(c.progress,0)
            self.assertFalse(c.moving)
            self.assertIsNone(c.digits)
            self.assertIsNone(c.events.active)
            verify(c,self.assets,render(c,self.assets),480)

    def test_out_of_order_rejects_policy_and_clock_change(self):
        a = advance(self.base,self.request(10,reduced=True)).state
        for tick in (9,10):
            r = advance(a,self.request(tick,self.next_clock))
            self.assertIs(r.state,a)
            self.assertIsNone(r.event)
            self.assertEqual(r.reason,"non-increasing-tick")

    def test_resync_and_external_core_busy(self):
        for flags in ({"resync":True},{"core_busy":True}):
            r = advance(self.base,self.request(1,self.next_clock,weather="RAIN",**flags))
            self.assertIsNone(r.state.digits)
            self.assertIsNone(r.state.events.active)
            self.assertEqual(render(r.state,self.assets)["clock"]["visualAnchor"],"10:09")

    def test_invalid_delta_and_direction_change(self):
        for delta in (-1,1001,True):
            with self.assertRaises(ValueError):
                self.request(1,delta=delta)
        with self.assertRaises(ValueError):
            advance(None,self.request(1,delta=1))
        with self.assertRaisesRegex(ValueError,"Direction change"):
            advance(self.base,self.request(1,delta=1,ambient=True))

    def test_mutated_frame_rejected(self):
        value = render(self.base,self.assets)
        for mutate in (lambda v:v["clock"].update(semanticTime="00:00"),
                       lambda v:v["geometry"]["regions"]["time"].update(alpha=0),
                       lambda v:v.update(effect="M14")):
            v = copy.deepcopy(value)
            mutate(v)
            with self.assertRaises(ValueError):
                verify(self.base,self.assets,v,432)
