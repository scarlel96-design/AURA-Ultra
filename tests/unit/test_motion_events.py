"""Test the event arbitration reference without a device or clock."""
import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
from motion_events import Sample,Goal,step,audit_matrix,DURATIONS,MIN_START_INTERVAL_MS


def baseline(**kwargs):
    return replace(Sample(0,charging=False,goal=Goal(1,100,99),
                          weather="CLEAR",gauge_permille=100),**kwargs)


class MotionEventTests(unittest.TestCase):
    def setUp(self):
        self.a = baseline()
        self.state = step(None,self.a).state

    def test_matrix(self):
        result = audit_matrix()
        self.assertEqual(result["cases"],2048)
        self.assertEqual(result["starts"],60)
        self.assertEqual(result["runtimeVerification"],"NOT RUN")
        print("MOTION_EVENT_RESULT "+json.dumps(result,sort_keys=True))

    def test_first_snapshot_never_animates(self):
        result = step(None,baseline(charging=True,goal=Goal(1,100,100)))
        self.assertIsNone(result.started)
        self.assertEqual(result.state.consumed_goal_day,1)

    def test_all_individual_events_and_durations(self):
        for kind,kwargs,duration in (
            ("M14",{"charging":True},750),("M13",{"goal":Goal(1,100,100)},950),
            ("M09",{"weather":"RAIN"},550),("M05",{"gauge_permille":101},350)):
            r = step(self.state,replace(self.a,tick_ms=1,**kwargs))
            self.assertEqual(r.started,kind)
            self.assertEqual(r.state.active.end_ms,1+duration)
            self.assertEqual(DURATIONS[kind],duration)

    def test_simultaneous_priority_and_no_replay(self):
        b = replace(self.a,tick_ms=1,charging=True,goal=Goal(1,100,100),
                    weather="RAIN",gauge_permille=200)
        r = step(self.state,b)
        self.assertEqual(r.started,"M14")
        self.assertEqual(r.dropped,("M13","M09","M05"))
        self.assertEqual(r.state.consumed_goal_day,1)
        r = step(r.state,replace(b,tick_ms=2000))
        self.assertIsNone(r.started)
        self.assertIsNone(r.state.active)

    def test_busy_drops_other_event_but_updates_data(self):
        b = replace(self.a,tick_ms=1,weather="RAIN")
        r = step(self.state,b)
        c = replace(b,tick_ms=2,charging=True)
        q = step(r.state,c)
        self.assertEqual(q.reason,"busy")
        self.assertEqual(q.dropped,("M14",))
        self.assertEqual(q.state.active.kind,"M09")
        self.assertTrue(q.state.sample.charging)

    def test_source_change_cancels_and_cooldown_prevents_restart(self):
        b = replace(self.a,tick_ms=1,gauge_permille=200)
        r = step(self.state,b)
        q = step(r.state,replace(b,tick_ms=2,gauge_permille=300))
        self.assertEqual(q.cancelled,"M05")
        self.assertIsNone(q.state.active)
        self.assertEqual(q.reason,"cooldown")
        self.assertEqual(q.state.sample.gauge_permille,300)

    def test_exact_cooldown_boundary(self):
        b = replace(self.a,tick_ms=1,gauge_permille=200)
        r = step(self.state,b)
        q = step(r.state,replace(b,tick_ms=MIN_START_INTERVAL_MS,gauge_permille=300))
        self.assertEqual(q.reason,"cooldown")
        t = step(q.state,replace(b,tick_ms=MIN_START_INTERVAL_MS+1,gauge_permille=400))
        self.assertEqual(t.started,"M05")

    def test_protection_cancels_active_without_replay(self):
        b = replace(self.a,tick_ms=1,charging=True)
        for flags in ({"ambient":True},{"reduced":True},{"core_busy":True},
                      {"quality":"ECO"},{"quality":"AOD"},{"profile":3}):
            r = step(self.state,b)
            q = step(r.state,replace(b,tick_ms=2,**flags))
            self.assertEqual(q.cancelled,"M14")
            self.assertIsNone(q.state.active)
            t = step(q.state,replace(b,tick_ms=2000,weather="RAIN"))
            self.assertEqual(t.reason,"policy-reentry")
            self.assertIsNone(t.started)
            self.assertEqual(t.dropped,("M09",))

    def test_missing_data_never_synthesizes_event(self):
        missing = replace(self.a,tick_ms=1,charging=None,weather=None,
                          goal=None,gauge_permille=None)
        r = step(self.state,missing)
        self.assertIsNone(r.started)
        restored = replace(self.a,tick_ms=2000,charging=True,weather="RAIN",
                           goal=Goal(1,100,100),gauge_permille=999)
        q = step(r.state,restored)
        self.assertIsNone(q.started)
        self.assertEqual(q.state.consumed_goal_day,1)
        self.assertEqual(q.state.sample,restored)

    def test_invalidated_active_source_cancels(self):
        b = replace(self.a,tick_ms=1,weather="RAIN")
        r = step(self.state,b)
        q = step(r.state,replace(b,tick_ms=2,weather=None))
        self.assertEqual(q.cancelled,"M09")
        self.assertIsNone(q.state.active)

    def test_goal_once_per_day_even_after_drop(self):
        r = step(self.state,replace(self.a,tick_ms=1,goal=Goal(1,100,100),reduced=True))
        self.assertEqual(r.state.consumed_goal_day,1)
        q = step(r.state,replace(self.a,tick_ms=2000,goal=Goal(1,100,90)))
        t = step(q.state,replace(self.a,tick_ms=4000,goal=Goal(1,100,110)))
        self.assertIsNone(t.started)
        u = step(t.state,replace(self.a,tick_ms=6000,goal=Goal(2,100,90)))
        v = step(u.state,replace(self.a,tick_ms=8000,goal=Goal(2,100,100)))
        self.assertEqual(v.started,"M13")

    def test_goal_target_change_and_day_rollback(self):
        r = step(self.state,replace(self.a,tick_ms=1,goal=Goal(1,90,99)))
        self.assertIsNone(r.started)
        q = step(r.state,replace(self.a,tick_ms=2000,goal=Goal(2,100,90)))
        t = step(q.state,replace(self.a,tick_ms=4000,goal=Goal(1,100,90)))
        u = step(t.state,replace(self.a,tick_ms=6000,goal=Goal(1,100,100)))
        self.assertEqual(u.state.latest_goal_day,2)
        self.assertIsNone(u.started)

    def test_duplicate_and_older_snapshot_keep_state(self):
        b = replace(self.a,tick_ms=10,reduced=True)
        r = step(self.state,b)
        for item,reason in ((b,"duplicate"),(replace(b,reduced=False),"non-increasing-tick"),
                            (replace(b,tick_ms=9,reduced=False),"non-increasing-tick")):
            q = step(r.state,item)
            self.assertIs(q.state,r.state)
            self.assertEqual(q.reason,reason)

    def test_goal_effect_remains_until_complete_while_steps_increase(self):
        b = replace(self.a,tick_ms=1,goal=Goal(1,100,100))
        r = step(self.state,b)
        q = step(r.state,replace(b,tick_ms=2,goal=Goal(1,100,101)))
        self.assertEqual(q.state.active.kind,"M13")
        t = step(q.state,replace(b,tick_ms=951,goal=Goal(1,100,102)))
        self.assertIsNone(t.state.active)

    def test_invalid_inputs(self):
        for kwargs in ({"tick_ms":-1},{"tick_ms":True},{"profile":True},
                       {"quality":"bad"},{"reduced":1},{"charging":0},{"weather":"unknown"},
                       {"gauge_permille":1001},{"gauge_permille":True},{"goal":{}}):
            with self.assertRaises(ValueError):
                baseline(**kwargs)
        for fields in ((0,100,0),(1,0,0),(1,100,-1),(True,100,0)):
            with self.assertRaises(ValueError):
                Goal(*fields)
