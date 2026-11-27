"""Compose host M01, M02 and event references without platform timers."""
import argparse
import json
from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from fluid_digits import ClockSample, Transition, plan, digit_frame, verify_frame
from motion_contract import MAX, DIAMETERS
from motion_object_paths import load, scene, validate_scene
from motion_events import Sample, State as EventState, Decision, step as event_step


@dataclass(frozen=True)
class Request:
    sample: Sample
    clock: ClockSample
    advance: int = 0
    resync: bool = False

    def __post_init__(self):
        if type(self.sample) is not Sample or type(self.clock) is not ClockSample:
            raise ValueError("Invalid input types")
        if type(self.advance) is not int or not 0 <= self.advance <= MAX:
            raise ValueError("Invalid normalized advance")
        if type(self.resync) is not bool:
            raise ValueError("Invalid resync flag")

    @property
    def target(self):
        return 0 if self.sample.ambient else MAX

    @property
    def static(self):
        s = self.sample
        return s.profile < 4 or s.reduced or s.quality == "ECO"


@dataclass(frozen=True)
class DigitRun:
    transition: Transition
    started_ms: int

    @property
    def end_ms(self):
        return self.started_ms + self.transition.duration_ms


@dataclass(frozen=True)
class State:
    request: Request
    progress: int
    digits: DigitRun | None
    events: EventState

    @property
    def moving(self):
        return self.progress != self.request.target


@dataclass(frozen=True)
class Result:
    state: State
    event: Decision | None
    reason: str


def stable_active(request, progress):
    return (progress == MAX and not request.sample.ambient
            and request.sample.allowed)


def advance(previous, request):
    """Keep absolute M01 progress at reversal; caller supplies subsequent deltas."""
    if type(request) is not Request:
        raise ValueError("Invalid request")
    if previous is None:
        if request.advance:
            raise ValueError("Baseline must not advance")
        event = event_step(None, request.sample)
        return Result(State(request,request.target,None,event.state),event,"baseline")
    if type(previous) is not State:
        raise ValueError("Invalid state")
    old = previous.request
    now = request.sample.tick_ms
    if now <= old.sample.tick_ms:
        return Result(previous,None,"duplicate" if request==old else "non-increasing-tick")
    changed_target = old.target != request.target
    changed_profile = old.sample.profile != request.sample.profile
    changed_static = old.static != request.static
    if changed_target and request.advance:
        raise ValueError("Direction change must not advance")
    if request.static or changed_profile or changed_static or request.resync:
        progress = request.target
    elif changed_target:
        progress = previous.progress
    elif request.target == MAX:
        progress = min(MAX,previous.progress+request.advance)
    else:
        progress = max(0,previous.progress-request.advance)
    moving = progress != request.target
    old_stable = stable_active(old,previous.progress)
    new_stable = stable_active(request,progress)
    clock_changed = old.clock != request.clock
    digits = previous.digits
    interrupted = digits is not None and now < digits.end_ms
    if digits and (not interrupted or clock_changed or not new_stable
                   or changed_profile or changed_static or request.resync):
        digits = None
    if (clock_changed and old_stable and new_stable and not changed_profile
            and not changed_static and not interrupted and not request.resync):
        transition = plan(old.clock,request.clock,profile=request.sample.profile)
        if transition.duration_ms:
            digits = DigitRun(transition,now)
    # Reserve this input for a clock change or resync even if it snaps.
    core_busy = (request.sample.core_busy or moving or digits is not None
                 or changed_target or changed_profile or changed_static
                 or clock_changed or request.resync)
    event = event_step(previous.events,replace(request.sample,core_busy=core_busy))
    return Result(State(request,progress,digits,event.state),event,"accepted")


def clock_frame(state):
    if state.digits:
        run = state.digits
        elapsed = state.request.sample.tick_ms-run.started_ms
        return digit_frame(run.transition,elapsed)
    clock = state.request.clock
    return digit_frame(plan(clock,clock),0)


def render(state, assets):
    layout,motion,objects = assets
    req = state.request
    if req.static:
        direction = "sleep" if req.target == 0 else "wake"
        geometry = scene(layout,motion,objects,MAX,direction,req.sample.profile,True)
    else:
        geometry = scene(layout,motion,objects,state.progress,"wake",req.sample.profile)
    return {"geometry":geometry,"clock":clock_frame(state),
            "effect":state.events.active.kind if state.events.active else None}


def verify(state, assets, value, diameter):
    req = state.request
    if not 0 <= state.progress <= MAX:
        raise ValueError("Invalid progress")
    if req.static and state.progress != req.target:
        raise ValueError("Static state not at target")
    if state.events.sample.tick_ms != req.sample.tick_ms:
        raise ValueError("Event snapshot out of sync")
    if state.digits and (state.moving or not stable_active(req,state.progress)):
        raise ValueError("Digit motion overlaps protected state")
    if state.events.active and (state.moving or state.digits or not req.sample.allowed
                                or state.events.sample.core_busy):
        raise ValueError("Decorative motion overlaps protected state")
    if value != render(state,assets):
        raise ValueError("Frame differs from coordinated state")
    validate_scene(assets[0],value["geometry"],diameter)
    if state.digits:
        run = state.digits
        if run.transition.current != req.clock:
            raise ValueError("Digit target is stale")
        verify_frame(run.transition,req.sample.tick_ms-run.started_ms,value["clock"])
    else:
        verify_frame(plan(req.clock,req.clock),0,value["clock"])


def audit_reentry(assets):
    clock = ClockSample(datetime(2026,1,1,10,8),0,"test",True)
    first = Request(Sample(0,ambient=True),clock)
    baseline = advance(None,first).state
    wake = advance(baseline,Request(Sample(1),clock)).state
    comparisons = geometry_checks = 0
    for p in range(MAX+1):
        mid = advance(wake,Request(Sample(2),clock,p)).state
        reverse = advance(mid,Request(Sample(3,ambient=True),clock)).state
        again = advance(reverse,Request(Sample(4),clock)).state
        initial = render(mid,assets)
        for state in (reverse,again):
            if state.progress != p or render(state,assets) != initial:
                raise ValueError("Reentry position discontinuity")
            comparisons += 1
        if p % 100 == 0:
            for d in DIAMETERS:
                verify(again,assets,initial,d)
                geometry_checks += 1
    return {"positions":MAX+1,"reentryComparisons":comparisons,
            "sampledGeometryChecks":geometry_checks,
            "scope":"host coordinated motion","runtimeVerification":"NOT RUN"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true",required=True)
    parser.parse_args()
    print("MOTION_COORDINATOR_RESULT "+json.dumps(audit_reentry(load()),sort_keys=True))


if __name__ == "__main__":
    main()
