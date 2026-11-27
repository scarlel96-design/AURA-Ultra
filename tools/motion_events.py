"""Host-only event motion arbitration; no runtime or sensor access."""
import argparse
import json
from dataclasses import dataclass, replace

# Draft durations within MOTION_SPEC targets, ordered by priority.
DURATIONS = {"M14": 750, "M13": 950, "M09": 550, "M05": 350}
PRIORITY = tuple(DURATIONS)
MIN_START_INTERVAL_MS = 1500
WEATHER = ("CLEAR", "CLOUDY", "RAIN", "SNOW", "FOG", "THUNDER")


@dataclass(frozen=True)
class Goal:
    day: int
    target: int
    steps: int

    def __post_init__(self):
        if any(type(v) is not int for v in (self.day, self.target, self.steps)):
            raise ValueError("Invalid goal field type")
        if not 1 <= self.day <= 3652059 or self.target <= 0 or self.steps < 0:
            raise ValueError("Invalid goal field range")

    @property
    def met(self):
        return self.steps >= self.target


@dataclass(frozen=True)
class Sample:
    tick_ms: int
    profile: int = 4
    quality: str = "BALANCED"
    ambient: bool = False
    reduced: bool = False
    core_busy: bool = False
    charging: bool | None = None
    goal: Goal | None = None
    weather: str | None = None
    gauge_permille: int | None = None

    def __post_init__(self):
        if type(self.tick_ms) is not int or self.tick_ms < 0:
            raise ValueError("Invalid monotonic tick")
        if type(self.profile) is not int or self.profile not in (2,3,4,5):
            raise ValueError("Invalid profile")
        if self.quality not in ("ULTRA","BALANCED","ECO","AOD"):
            raise ValueError("Invalid quality")
        if any(type(v) is not bool for v in (self.ambient,self.reduced,self.core_busy)):
            raise ValueError("Invalid policy flag")
        if self.charging is not None and type(self.charging) is not bool:
            raise ValueError("Invalid charging flag")
        if self.goal is not None and type(self.goal) is not Goal:
            raise ValueError("Invalid goal")
        if self.weather is not None and self.weather not in WEATHER:
            raise ValueError("Invalid synthetic weather token")
        if self.gauge_permille is not None and (
                type(self.gauge_permille) is not int or not 0 <= self.gauge_permille <= 1000):
            raise ValueError("Invalid gauge value")

    @property
    def allowed(self):
        return (self.profile >= 4 and self.quality in ("ULTRA","BALANCED")
                and not self.ambient and not self.reduced and not self.core_busy)


@dataclass(frozen=True)
class Effect:
    kind: str
    started_ms: int

    @property
    def end_ms(self):
        return self.started_ms + DURATIONS[self.kind]


@dataclass(frozen=True)
class State:
    sample: Sample
    active: Effect | None
    last_start_ms: int | None
    latest_goal_day: int
    consumed_goal_day: int


@dataclass(frozen=True)
class Decision:
    state: State
    started: str | None
    cancelled: str | None
    dropped: tuple
    reason: str


def goal_crossed(old, new, latest_day, consumed_day):
    return (old is not None and new is not None
            and old.day == new.day and old.target == new.target
            and new.day >= latest_day and new.day > consumed_day
            and not old.met and new.met)


def changed_known(old, new):
    return old is not None and new is not None and old != new


def candidates(old, new, state):
    flags = {
        "M14": changed_known(old.charging,new.charging),
        "M13": goal_crossed(old.goal,new.goal,state.latest_goal_day,state.consumed_goal_day),
        "M09": changed_known(old.weather,new.weather),
        "M05": changed_known(old.gauge_permille,new.gauge_permille),
    }
    return tuple(k for k in PRIORITY if flags[k])


def target_current(kind, old, new, latest_day):
    if kind == "M13":
        a,b = old.goal,new.goal
        return (a is not None and b is not None and b.day >= latest_day
                and a.day == b.day and a.target == b.target and b.met)
    field = {"M14":"charging","M09":"weather","M05":"gauge_permille"}[kind]
    a,b = getattr(old,field),getattr(new,field)
    return a is not None and a == b


def step(previous, current):
    """Apply a serialized snapshot. Never queue or replay decorative events."""
    if type(current) is not Sample:
        raise ValueError("Invalid sample")
    if previous is None:
        day = current.goal.day if current.goal else 0
        consumed = day if current.goal and current.goal.met else 0
        return Decision(State(current,None,None,day,consumed),None,None,(),"baseline")
    if type(previous) is not State:
        raise ValueError("Invalid state")
    old = previous.sample
    if current.tick_ms <= old.tick_ms:
        reason = "duplicate" if current == old else "non-increasing-tick"
        return Decision(previous,None,None,(),reason)
    offered = candidates(old,current,previous)
    latest_day = max(previous.latest_goal_day,current.goal.day if current.goal else 0)
    consumed = previous.consumed_goal_day
    # Mark observed achievement even if policy suppresses its animation.
    if current.goal and current.goal.met and current.goal.day >= previous.latest_goal_day:
        consumed = max(consumed,current.goal.day)
    active = previous.active
    cancelled = None
    if active and current.tick_ms >= active.end_ms:
        active = None
    if active and (not current.allowed or old.profile != current.profile
                   or not target_current(active.kind,old,current,latest_day)):
        cancelled = active.kind
        active = None
    started = None
    last_start = previous.last_start_ms
    if not current.allowed:
        reason = "policy-blocked"
    elif not old.allowed or old.profile != current.profile:
        reason = "policy-reentry"
    elif not offered:
        reason = "no-event"
    elif active:
        reason = "busy"
    elif last_start is not None and current.tick_ms-last_start < MIN_START_INTERVAL_MS:
        reason = "cooldown"
    else:
        started = offered[0]
        active = Effect(started,current.tick_ms)
        last_start = current.tick_ms
        reason = "started"
    dropped = tuple(k for k in offered if k != started)
    return Decision(State(current,active,last_start,latest_day,consumed),
                    started,cancelled,dropped,reason)


def audit_matrix():
    checked = starts = 0
    for profile in (2,3,4,5):
        for quality in ("ULTRA","BALANCED","ECO","AOD"):
            for ambient in (False,True):
                for reduced in (False,True):
                    for core in (False,True):
                        before = Sample(0,profile,quality,ambient,reduced,core,
                                        False,Goal(1,100,99),"CLEAR",100)
                        for mask in range(16):
                            after = replace(before,tick_ms=1,
                                            charging=bool(mask & 1),
                                            goal=Goal(1,100,100 if mask & 2 else 99),
                                            weather="RAIN" if mask & 4 else "CLEAR",
                                            gauge_permille=200 if mask & 8 else 100)
                            result = step(step(None,before).state,after)
                            expected = next((k for bit,k in enumerate(PRIORITY)
                                             if mask & (1 << bit)),None)
                            if not after.allowed:
                                expected = None
                            if result.started != expected or result.state.sample != after:
                                raise ValueError("Arbitration matrix mismatch")
                            if bool(result.state.active) != bool(expected):
                                raise ValueError("Active effect mismatch")
                            checked += 1
                            starts += bool(expected)
    return {"cases":checked,"starts":starts,"scope":"host event arbitration",
            "runtimeVerification":"NOT RUN"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true",required=True)
    parser.parse_args()
    print("MOTION_EVENT_RESULT "+json.dumps(audit_matrix(),sort_keys=True))


if __name__ == "__main__":
    main()
