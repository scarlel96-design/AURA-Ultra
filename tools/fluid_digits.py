"""Host-only M02 digit transition reference; not a WFF renderer."""
import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from fractions import Fraction

DURATION_MS = 220
SLOTS = (0, 1, 3, 4)
ONE_MINUTE = timedelta(minutes=1)


@dataclass(frozen=True)
class ClockSample:
    civil: datetime
    offset_minutes: int
    zone: str
    hour24: bool

    def __post_init__(self):
        if (type(self.civil) is not datetime or self.civil.tzinfo is not None or
                self.civil.second or self.civil.microsecond or self.civil.fold):
            raise ValueError("Expected naive civil minute")
        if type(self.offset_minutes) is not int or not -840 <= self.offset_minutes <= 840:
            raise ValueError("Invalid UTC offset")
        if type(self.zone) is not str or not self.zone or len(self.zone) > 128:
            raise ValueError("Invalid zone identity")
        if type(self.hour24) is not bool:
            raise ValueError("Invalid hour format")

    @property
    def text(self):
        hour = self.civil.hour if self.hour24 else (self.civil.hour % 12 or 12)
        return f"{hour:02d}:{self.civil.minute:02d}"

    @property
    def marker(self):
        return "" if self.hour24 else ("AM" if self.civil.hour < 12 else "PM")


@dataclass(frozen=True)
class Transition:
    previous: ClockSample
    current: ClockSample
    reason: str
    duration_ms: int
    changed: tuple


def plan(previous, current, *, profile=4, ambient=False, reduced=False,
         interrupted=False, resync=False):
    if type(previous) is not ClockSample or type(current) is not ClockSample:
        raise ValueError("Invalid clock sample")
    if type(profile) is not int or profile not in (2, 3, 4, 5):
        raise ValueError("Invalid profile")
    if any(type(v) is not bool for v in (ambient, reduced, interrupted, resync)):
        raise ValueError("Invalid transition flag")
    changed = tuple(i for i in SLOTS if previous.text[i] != current.text[i])
    if resync or interrupted:
        reason = "resync" if resync else "interrupted"
    elif previous.hour24 != current.hour24:
        reason = "format-change"
    elif (previous.zone, previous.offset_minutes) != (current.zone, current.offset_minutes):
        reason = "zone-change"
    elif previous == current:
        reason = "unchanged"
    elif current.civil - previous.civil != ONE_MINUTE:
        reason = "non-adjacent"
    elif ambient or reduced or profile < 4:
        reason = "static-policy"
    else:
        reason = "adjacent-minute"
    return Transition(previous, current, reason,
                      DURATION_MS if reason == "adjacent-minute" else 0, changed)


def phase(transition, elapsed_ms):
    if type(elapsed_ms) is not int or elapsed_ms < 0:
        raise ValueError("Invalid elapsed milliseconds")
    if transition.duration_ms == 0:
        return Fraction(1)
    x = Fraction(min(elapsed_ms, transition.duration_ms), transition.duration_ms)
    return x*x*(3-2*x)


def layer(symbol, offset, opacity):
    return {"symbol": symbol, "offset": offset, "alpha": opacity}


def digit_frame(transition, elapsed_ms):
    """Use normalized slot-height offsets. Clip each slot in the future renderer."""
    p = phase(transition, elapsed_ms)
    old, new = transition.previous, transition.current
    slots = {}
    for i in SLOTS:
        a,b = old.text[i], new.text[i]
        if a == b or p == 1:
            layers = [layer(b, Fraction(0), Fraction(1))]
        elif p == 0:
            layers = [layer(a, Fraction(0), Fraction(1))]
        else:
            layers = [layer(a, -p, 1-p), layer(b, 1-p, p)]
        slots[i] = layers
    anchor = old if p < Fraction(1,2) else new
    return {"slots": slots, "colon": ":", "semanticTime": new.text,
            "semanticDate": new.civil.date().isoformat(), "semanticMarker": new.marker,
            "visualDate": anchor.civil.date().isoformat(), "visualMarker": anchor.marker,
            "visualAnchor": anchor.text}


def verify_transition(transition):
    """Check metadata against clock samples and the supported policy reasons."""
    if type(transition) is not Transition:
        raise ValueError("Invalid transition")
    baseline = plan(transition.previous, transition.current)
    if (type(transition.changed) is not tuple or
            any(type(i) is not int for i in transition.changed) or
            transition.changed != baseline.changed):
        raise ValueError("Incorrect changed digit slots")
    if type(transition.reason) is not str or type(transition.duration_ms) is not int:
        raise ValueError("Invalid transition metadata")
    if transition.reason in ("resync", "interrupted"):
        expected = plan(transition.previous, transition.current, **{transition.reason: True})
    elif transition.reason == "static-policy":
        expected = plan(transition.previous, transition.current, ambient=True)
    else:
        expected = baseline
    if transition != expected:
        raise ValueError("Transition reason or duration differs from plan")


def verify_frame(transition, elapsed_ms, value):
    """Reject wrong metadata, symbols, geometry and semantics."""
    verify_transition(transition)
    old,new = transition.previous,transition.current
    p = phase(transition,elapsed_ms)
    anchor = old if p < Fraction(1,2) else new
    expected = {"colon":":","semanticTime":new.text,"semanticDate":new.civil.date().isoformat(),
                "semanticMarker":new.marker,"visualDate":anchor.civil.date().isoformat(),
                "visualMarker":anchor.marker,"visualAnchor":anchor.text}
    if type(value) is not dict or set(value) != set(expected) | {"slots"}:
        raise ValueError("Invalid frame fields")
    if any(value[k] != v for k,v in expected.items()):
        raise ValueError("Incorrect clock semantics")
    slots = value["slots"]
    if type(slots) is not dict or any(type(i) is not int for i in slots) or set(slots) != set(SLOTS):
        raise ValueError("Invalid digit slots")
    for i, layers in slots.items():
        a,b = old.text[i],new.text[i]
        if type(layers) is not list or not 1 <= len(layers) <= 2:
            raise ValueError("Invalid layer count")
        for item in layers:
            if type(item) is not dict or set(item) != {"symbol","offset","alpha"}:
                raise ValueError("Invalid layer fields")
            if (type(item["offset"]) is not Fraction or type(item["alpha"]) is not Fraction or
                    not -1 <= item["offset"] <= 1 or not 0 < item["alpha"] <= 1):
                raise ValueError("Unsafe layer geometry")
        if sum(v["alpha"] for v in layers) != 1:
            raise ValueError("Unbalanced slot alpha")
        if a == b or p == 1:
            ok = len(layers)==1 and layers[0] == layer(b,Fraction(0),Fraction(1))
        elif p == 0:
            ok = len(layers)==1 and layers[0] == layer(a,Fraction(0),Fraction(1))
        else:
            ok = (len(layers)==2 and layers[0]["symbol"]==a and layers[1]["symbol"]==b
                  and layers[0]["offset"]==-p and layers[1]["offset"]==1-p
                  and layers[0]["alpha"]==1-p and layers[1]["alpha"]==p)
        if not ok:
            raise ValueError("Incorrect digit layers")


def audit_day():
    """Exercise every adjacent local minute in both display formats."""
    transitions = frames = 0
    start = datetime(2026,1,1)
    for hour24 in (False,True):
        for i in range(1440):
            a = start + timedelta(minutes=i)
            b = a + ONE_MINUTE
            old,new = (ClockSample(t,540,"fixed-test-zone",hour24) for t in (a,b))
            t = plan(old,new)
            if t.duration_ms != DURATION_MS or not t.changed:
                raise ValueError("Missing adjacent-minute transition")
            for elapsed in (0,110,220):
                verify_frame(t,elapsed,digit_frame(t,elapsed))
                frames += 1
            transitions += 1
    return {"transitions":transitions,"frames":frames,
            "scope":"host digit-slot reference","runtimeVerification":"NOT RUN"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true",required=True)
    parser.parse_args()
    print("FLUID_DIGITS_RESULT "+json.dumps(audit_day(),sort_keys=True))


if __name__ == "__main__":
    main()
