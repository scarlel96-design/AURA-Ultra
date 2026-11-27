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

    def test_aod_quality_overrides_inconsistent_ambient_flag(self):
        for profile in (2,3,4,5):
            for ambient in (False,True):
                for reduced in (False,True):
                    request = self.request(1,quality="AOD",profile=profile,
                                           ambient=ambient,reduced=reduced)
                    state = advance(None,request).state
                    self.assertEqual(state.progress,0)
                    self.assertFalse(state.moving)
                    self.assertTrue(request.static)
                    value = render(state,self.assets)
                    self.assertEqual({n for n,r in value["geometry"]["regions"].items()
                                      if r["alpha"]>0},{"time","date","ampm"})
                    self.assertEqual(value["geometry"]["ring"]["alpha"],0)
                    self.assertEqual(value["geometry"]["highlight"]["alpha"],0)
                    self.assertIsNone(value["effect"])
                    for d in (432,438,480,498):
                        verify(state,self.assets,value,d)

    def test_aod_quality_cancels_effect_and_ignores_pending_delta(self):
        a = advance(self.base,self.request(1,charging=True)).state
        r = advance(a,self.request(2,self.next_clock,delta=200,quality="AOD",charging=True))
        self.assertEqual(r.state.progress,0)
        self.assertEqual(r.event.cancelled,"M14")
        self.assertIsNone(r.state.digits)
        self.assertEqual(render(r.state,self.assets)["clock"]["visualAnchor"],"10:09")
        b = advance(r.state,self.request(3,self.next_clock,charging=True,weather="RAIN"))
        self.assertEqual(b.state.progress,1000)
        self.assertIsNone(b.state.events.active)
        self.assertIsNone(b.state.digits)

    def test_aod_quality_interrupts_digits(self):
        a = advance(self.base,self.request(1,self.next_clock)).state
        self.assertIsNotNone(a.digits)
        b = advance(a,self.request(2,self.next_clock,quality="AOD")).state
        self.assertEqual(b.progress,0)
        self.assertIsNone(b.digits)
        self.assertEqual(render(b,self.assets)["clock"]["visualAnchor"],"10:09")

    def test_protection_precedes_direction_delta(self):
        a = advance(self.base,self.request(1,ambient=True)).state
        b = advance(a,self.request(2,ambient=True,delta=400)).state
        for kwargs in ({"reduced":True},{"profile":3},{"quality":"ECO"},{"resync":True}):
            c = advance(b,self.request(3,delta=100,**kwargs)).state
            self.assertEqual(c.progress,1000)
            self.assertIsNone(c.digits)
            self.assertIsNone(c.events.active)

    def test_forged_event_snapshot_and_guard_rejected(self):
        a = advance(self.base,self.request(1,ambient=True)).state
        for sample in (replace(a.events.sample,weather="RAIN"),
                       replace(a.events.sample,core_busy=False)):
            invalid = replace(a,events=replace(a.events,sample=sample))
            with self.assertRaises(ValueError):
                verify(invalid,self.assets,render(invalid,self.assets),432)

    def test_expired_runs_and_noninteger_progress_rejected(self):
        a = advance(self.base,self.request(1,charging=True)).state
        b = replace(a,events=replace(a.events,active=replace(a.events.active,started_ms=-1000)))
        with self.assertRaisesRegex(ValueError,"Effect outside lifetime"):
            verify(b,self.assets,render(b,self.assets),432)
        c = advance(self.base,self.request(1,self.next_clock)).state
        d = replace(c,digits=replace(c.digits,started_ms=-1000))
        with self.assertRaisesRegex(ValueError,"Digit run outside lifetime"):
            verify(d,self.assets,render(d,self.assets),432)
        with self.assertRaisesRegex(ValueError,"Invalid progress"):
            verify(replace(self.base,progress=True),self.assets,render(self.base,self.assets),432)
