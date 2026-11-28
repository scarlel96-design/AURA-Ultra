package io.github.scarlel96.aura.intelligence

import io.github.scarlel96.aura.domain.ObservationStatus
import java.time.Duration
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

class Round02Test {
    private fun run(
        previous: MachineState?,
        sample: IntelligenceSample,
        policy: PolicyCandidates = openPolicy(),
    ): StepResult.Advanced {
        return assertIs(step(previous, sample, policy))
    }

    @Test
    fun unchangedInputStillRejectsAnOlderSample() {
        val policy = openPolicy()
        val first = run(null, sample(battery = reading(50.0, "percent")), policy)
        val repeated = run(first.state, sample(moment = at(100), battery = reading(50.0, "percent")), policy)
        assertEquals(PowerAxis.NORMAL, repeated.state.power)
        assertEquals(first.state.committedAt, repeated.state.committedAt)
        assertEquals(at(100), repeated.state.processedAt)
        assertEquals(first.state.revision, repeated.state.revision)
        val older = run(
            repeated.state,
            sample(
                moment = at(50),
                battery = reading(10.0, "percent"),
                alert = reading(true, "flag"),
            ),
            policy,
        )
        assertEquals(PowerAxis.NORMAL, older.state.power)
        assertEquals(WeatherAxis.NORMAL, older.state.weather)
        assertEquals(first.state.committedAt, older.state.committedAt)
        assertEquals(at(100), older.state.processedAt)
        assertTrue(!older.state.processedAt.isBefore(older.state.committedAt))
        assertNull(older.intent.publishedBatteryPercent)
        assertNull(older.intent.publishedPrecipitation)
        assertTrue(older.intent.reasonCodes.contains(ReasonCode.CLOCK_INVERSION))
        assertFalse(older.intent.reasonCodes.contains(ReasonCode.URGENT))
        assertEquals(repeated.state.revision + 1, older.state.revision)
    }

    @Test
    fun equalProcessedTimeIsNotInversion() {
        val policy = openPolicy()
        val first = run(null, sample(battery = reading(50.0, "percent")), policy)
        val repeated = run(first.state, sample(moment = at(100), battery = reading(50.0, "percent")), policy)
        val sameInstant = run(
            repeated.state,
            sample(moment = at(100), light = reading("NIGHT", "token")),
            policy,
        )
        assertEquals(LightAxis.NIGHT, sameInstant.state.light)
        assertEquals(PowerAxis.NORMAL, sameInstant.state.power)
        assertEquals(at(100), sameInstant.state.processedAt)
        assertEquals(first.state.committedAt, sameInstant.state.committedAt)
        assertFalse(sameInstant.intent.reasonCodes.contains(ReasonCode.CLOCK_INVERSION))
    }

    @Test
    fun missingOrInvalidChargingDoesNotClearCharging() {
        val policy = PolicyCandidates.documented()
        val plugged = run(
            null,
            sample(battery = reading(90.0, "percent"), charging = reading(true, "flag")),
            policy,
        )
        assertEquals(PowerAxis.CHARGING, plugged.state.power)
        val omitted = run(
            plugged.state,
            sample(moment = at(1), battery = reading(10.0, "percent")),
            policy,
        )
        assertEquals(PowerAxis.CHARGING, omitted.state.power)
        assertEquals(10.0, omitted.intent.publishedBatteryPercent)
        // DATA_INTELLIGENCE requires a fresh low battery to limit decoration and particles.
        // The charging axis stays CHARGING. GB02-A28.
        assertEquals(FocusBand.POWER, omitted.state.focus)
        assertEquals(QualityCandidate.BALANCED, omitted.intent.quality)
        assertTrue(omitted.intent.motionAllowed)
        assertFalse(omitted.intent.particleEffectsAllowed)
        assertTrue(omitted.intent.reasonCodes.contains(ReasonCode.POWER_LOW))
        assertFalse(omitted.intent.reasonCodes.contains(ReasonCode.CHARGING_EXCEPTION))
        val unavailable = run(
            plugged.state,
            sample(
                moment = at(1),
                battery = reading(10.0, "percent"),
                charging = reading(null, "flag", status = ObservationStatus.UNAVAILABLE),
            ),
            policy,
        )
        assertEquals(PowerAxis.CHARGING, unavailable.state.power)
        assertEquals(10.0, unavailable.intent.publishedBatteryPercent)
        assertTrue(unavailable.intent.reasonCodes.contains(ReasonCode.UNAVAILABLE_IGNORED))
        assertTrue(unavailable.intent.motionAllowed)
        val wrongUnit = run(
            plugged.state,
            sample(
                moment = at(1),
                battery = reading(10.0, "percent"),
                charging = reading(false, "bool"),
            ),
            policy,
        )
        assertEquals(PowerAxis.CHARGING, wrongUnit.state.power)
        assertTrue(wrongUnit.intent.reasonCodes.contains(ReasonCode.UNIT_UNCHECKED))
        assertEquals(QualityCandidate.BALANCED, wrongUnit.intent.quality)
    }

    @Test
    fun freshChargingFalseUsesHysteresisAndDoesNotInventZero() {
        val policy = PolicyCandidates.documented()
        val plugged = run(null, sample(charging = reading(true, "flag")), policy)
        val toNormal = run(
            plugged.state,
            sample(moment = at(1), battery = reading(80.0, "percent"), charging = reading(false, "flag")),
            policy,
        )
        assertEquals(PowerAxis.NORMAL, toNormal.state.power)
        assertTrue(toNormal.intent.reasonCodes.contains(ReasonCode.CHARGING_EXCEPTION))
        val absentBattery = run(
            plugged.state,
            sample(moment = at(1), charging = reading(false, "flag")),
            policy,
        )
        assertEquals(PowerAxis.NORMAL, absentBattery.state.power)
        assertNull(absentBattery.intent.publishedBatteryPercent)
        val low = run(
            plugged.state,
            sample(moment = at(1), battery = reading(10.0, "percent"), charging = reading(false, "flag")),
            policy,
        )
        assertEquals(PowerAxis.LOW, low.state.power)
        assertEquals(FocusBand.POWER, low.state.focus)
        assertEquals(QualityCandidate.ECO, low.intent.quality)
        assertFalse(low.intent.motionAllowed)
        assertEquals(at(1), low.state.committedAt)
        assertTrue(low.intent.reasonCodes.contains(ReasonCode.CHARGING_EXCEPTION))
        val enterEdge = run(
            plugged.state,
            sample(moment = at(1), battery = reading(15.0, "percent"), charging = reading(false, "flag")),
            policy,
        )
        assertEquals(PowerAxis.LOW, enterEdge.state.power)
        val insideBand = run(
            plugged.state,
            sample(moment = at(1), battery = reading(19.0, "percent"), charging = reading(false, "flag")),
            policy,
        )
        assertEquals(PowerAxis.NORMAL, insideBand.state.power)
        val exitEdge = run(
            plugged.state,
            sample(moment = at(1), battery = reading(20.0, "percent"), charging = reading(false, "flag")),
            policy,
        )
        assertEquals(PowerAxis.NORMAL, exitEdge.state.power)
    }

    @Test
    fun olderSampleCannotClearChargingOrRaiseAlert() {
        val policy = openPolicy()
        val plugged = run(
            null,
            sample(battery = reading(90.0, "percent"), charging = reading(true, "flag")),
            policy,
        )
        val later = run(
            plugged.state,
            sample(moment = at(100), battery = reading(90.0, "percent"), charging = reading(true, "flag")),
            policy,
        )
        assertEquals(origin, later.state.committedAt)
        assertEquals(at(100), later.state.processedAt)
        val older = run(
            later.state,
            sample(moment = at(50), battery = reading(90.0, "percent"), alert = reading(true, "flag")),
            policy,
        )
        assertEquals(PowerAxis.CHARGING, older.state.power)
        assertEquals(WeatherAxis.NORMAL, older.state.weather)
        assertEquals(at(100), older.state.processedAt)
        assertNull(older.intent.publishedBatteryPercent)
        assertTrue(older.intent.reasonCodes.contains(ReasonCode.CLOCK_INVERSION))
    }

    @Test
    fun thresholdsOutsideTheConfiguredScaleAreRejected() {
        val narrowPercent = PolicyCandidates.documented().copy(percentMaximum = 1.0)
        assertTrue(narrowPercent.issues().any { it == "power thresholds must lie inside the percent scale" })
        val rejectedPower = assertIs<StepResult.PolicyRejected>(
            step(null, sample(battery = reading(10.0, "percent")), narrowPercent),
        )
        assertEquals(narrowPercent.issues(), rejectedPower.issues)
        val widePrecip = PolicyCandidates.documented().copy(precipEnter = 150.0, precipExit = 40.0)
        assertTrue(widePrecip.issues().any { it == "precipitation thresholds must lie inside the probability scale" })
        val below = PolicyCandidates.documented().copy(powerEnterPercent = -1.0)
        assertTrue(below.issues().any { it == "power thresholds must lie inside the percent scale" })
        val nonFinite = PolicyCandidates.documented().copy(powerEnterPercent = Double.NaN)
        assertTrue(nonFinite.issues().any { it.contains("finite") })
        assertTrue(nonFinite.issues().none { it.contains("inside") })
        assertEquals(emptyList(), PolicyCandidates.documented().issues())
    }

    @Test
    fun scaleEdgesRemainAccepted() {
        val edges = PolicyCandidates.documented().copy(
            minimumHold = Duration.ZERO,
            powerEnterPercent = 0.0,
            powerExitPercent = 100.0,
            precipEnter = 100.0,
            precipExit = 0.0,
        )
        assertEquals(emptyList(), edges.issues())
        val advanced = run(
            null,
            sample(battery = reading(0.0, "percent"), precipitation = reading(100.0, "percent")),
            edges,
        )
        assertEquals(PowerAxis.LOW, advanced.state.power)
        assertEquals(WeatherAxis.PRECIP, advanced.state.weather)
        assertEquals(0.0, advanced.intent.publishedBatteryPercent)
        assertEquals(100.0, advanced.intent.publishedPrecipitation)
    }

    @Test
    fun extremeInstantAndDurationDoNotEscapeStep() {
        val near = Instant.MAX.minusSeconds(30)
        val later = Instant.MAX.minusSeconds(10)
        val policy = PolicyCandidates.documented()
        val first = run(
            null,
            sample(moment = near, battery = freshPercent(80.0, near)),
            policy,
        )
        val held = run(
            first.state,
            sample(moment = later, battery = freshPercent(10.0, later)),
            policy,
        )
        assertEquals(PowerAxis.NORMAL, held.state.power)
        assertEquals(PowerAxis.LOW, held.state.pending?.power)
        assertEquals(near, held.state.committedAt)
        assertEquals(later, held.state.processedAt)
        assertTrue(held.intent.reasonCodes.contains(ReasonCode.MINIMUM_HOLD))
        val unchanged = run(
            held.state,
            sample(moment = later, battery = freshPercent(80.0, later)),
            policy,
        )
        assertEquals(PowerAxis.NORMAL, unchanged.state.power)
        assertEquals(later, unchanged.state.processedAt)
        val huge = openPolicy(hold = Duration.ofSeconds(Long.MAX_VALUE))
        assertEquals(emptyList(), huge.issues())
        val baseline = run(null, sample(battery = reading(80.0, "percent")), huge)
        val blocked = run(baseline.state, sample(moment = at(1), battery = reading(10.0, "percent")), huge)
        assertEquals(PowerAxis.NORMAL, blocked.state.power)
        assertEquals(PowerAxis.LOW, blocked.state.pending?.power)
        assertTrue(blocked.intent.reasonCodes.contains(ReasonCode.MINIMUM_HOLD))
        val charging = run(
            baseline.state,
            sample(moment = at(1), charging = reading(true, "flag")),
            huge,
        )
        assertEquals(PowerAxis.CHARGING, charging.state.power)
        assertTrue(charging.intent.reasonCodes.contains(ReasonCode.CHARGING_EXCEPTION))
        val inverted = run(
            baseline.state,
            sample(moment = Instant.MIN, battery = reading(1.0, "percent")),
            huge,
        )
        assertEquals(PowerAxis.NORMAL, inverted.state.power)
        assertEquals(baseline.state.processedAt, inverted.state.processedAt)
        assertTrue(inverted.intent.reasonCodes.contains(ReasonCode.CLOCK_INVERSION))
    }

    @Test
    fun revisionDoesNotWrapAndStopsAtTheLimit() {
        val policy = openPolicy()
        val base = run(null, sample(battery = reading(50.0, "percent")), policy)
        val maxed = base.state.copy(revision = Long.MAX_VALUE)
        val same = run(maxed, sample(moment = at(5), battery = reading(50.0, "percent")), policy)
        assertEquals(Long.MAX_VALUE, same.state.revision)
        assertEquals(at(5), same.state.processedAt)
        assertEquals(maxed.committedAt, same.state.committedAt)
        assertEquals(PowerAxis.NORMAL, same.state.power)
        assertTrue(same.state.revision > 0L)
        val blocked = assertIs<StepResult.LimitReached>(
            step(maxed, sample(moment = at(1), light = reading("NIGHT", "token")), policy),
        )
        assertEquals(ReasonCode.REVISION_EXHAUSTED, blocked.reason)
        assertEquals(at(1), blocked.state.processedAt)
        assertEquals(50.0, blocked.state.emission.publishedBatteryPercent)
        assertEquals(LightAxis.DAY, blocked.state.light)
        assertEquals(Long.MAX_VALUE, blocked.state.revision)
        val almost = base.state.copy(revision = Long.MAX_VALUE - 1L)
        val night = run(almost, sample(moment = at(1), light = reading("NIGHT", "token")), policy)
        assertEquals(Long.MAX_VALUE, night.state.revision)
        assertEquals(LightAxis.NIGHT, night.state.light)
        assertTrue(night.state.revision > 0L)
        val exhaustedInversion = assertIs<StepResult.LimitReached>(
            step(maxed, sample(moment = origin.minusSeconds(1), battery = reading(1.0, "percent")), policy),
        )
        assertEquals(ReasonCode.REVISION_EXHAUSTED, exhaustedInversion.reason)
        assertSame(maxed, exhaustedInversion.state)
        assertEquals(origin, exhaustedInversion.state.processedAt)
    }

    @Test
    fun hysteresisDebounceUrgentAndLowPowerInteract() {
        val policy = PolicyCandidates.documented().copy(debounce = Duration.ofSeconds(30))
        val baseline = run(null, sample(battery = reading(50.0, "percent")), policy)
        val pendingLow = run(baseline.state, sample(moment = at(10), battery = reading(10.0, "percent")), policy)
        assertEquals(PowerAxis.NORMAL, pendingLow.state.power)
        assertEquals(PowerAxis.LOW, pendingLow.state.pending?.power)
        assertTrue(pendingLow.intent.reasonCodes.contains(ReasonCode.DEBOUNCE))
        assertTrue(pendingLow.intent.reasonCodes.contains(ReasonCode.MINIMUM_HOLD))
        val cancelled = run(pendingLow.state, sample(moment = at(12), battery = reading(18.0, "percent")), policy)
        assertEquals(PowerAxis.NORMAL, cancelled.state.power)
        assertNull(cancelled.state.pending)
        assertEquals(18.0, cancelled.intent.publishedBatteryPercent)
        assertFalse(cancelled.intent.reasonCodes.contains(ReasonCode.DEBOUNCE))
        val quiet = run(null, sample(battery = reading(80.0, "percent")), policy)
        val urgent = run(
            quiet.state,
            sample(
                moment = at(1),
                battery = reading(10.0, "percent"),
                precipitation = reading(80.0, "percent"),
                alert = reading(true, "flag"),
                connectivity = reading("OFFLINE", "token"),
            ),
            policy,
        )
        assertEquals(WeatherAxis.ALERT, urgent.state.weather)
        assertEquals(PowerAxis.LOW, urgent.state.power)
        assertEquals(FocusBand.CRITICAL, urgent.state.focus)
        assertEquals(80.0, urgent.intent.publishedPrecipitation)
        assertEquals(10.0, urgent.intent.publishedBatteryPercent)
        assertFalse(urgent.intent.particleEffectsAllowed)
        assertFalse(urgent.intent.motionAllowed)
        assertTrue(urgent.intent.timeKept)
        assertTrue(urgent.intent.weatherNumbersKept)
        assertEquals(QualityCandidate.ECO, urgent.intent.quality)
        assertTrue(urgent.intent.reasonCodes.contains(ReasonCode.URGENT))
        assertTrue(urgent.intent.reasonCodes.contains(ReasonCode.OFFLINE))
        assertEquals(at(1), urgent.state.committedAt)
        assertNull(urgent.state.pending)
        val held = run(
            urgent.state,
            sample(
                moment = at(2),
                battery = reading(80.0, "percent"),
                precipitation = reading(10.0, "percent"),
                alert = reading(false, "flag"),
                connectivity = reading("ONLINE", "token"),
            ),
            policy,
        )
        assertEquals(PowerAxis.LOW, held.state.power)
        assertEquals(WeatherAxis.ALERT, held.state.weather)
        assertEquals(ConnectivityAxis.ONLINE, held.state.connectivity)
        assertEquals(urgent.state.committedAt, held.state.committedAt)
        assertTrue(held.intent.reasonCodes.contains(ReasonCode.MINIMUM_HOLD))
        assertTrue(held.intent.reasonCodes.contains(ReasonCode.DEBOUNCE))
        val released = run(
            held.state,
            sample(
                moment = at(61),
                battery = reading(80.0, "percent"),
                precipitation = reading(10.0, "percent"),
                alert = reading(false, "flag"),
                connectivity = reading("ONLINE", "token"),
            ),
            policy,
        )
        assertEquals(PowerAxis.NORMAL, released.state.power)
        assertEquals(WeatherAxis.NORMAL, released.state.weather)
        assertEquals(FocusBand.DECORATIVE, released.state.focus)
        assertEquals(QualityCandidate.BALANCED, released.intent.quality)
        assertTrue(released.intent.motionAllowed)
        assertNull(released.state.pending)
    }

    @Test
    fun staleReadingDuringUrgentDoesNotLeaveLowOrPublishANumber() {
        val policy = PolicyCandidates.documented().copy(debounce = Duration.ofSeconds(30))
        val low = run(null, sample(battery = reading(10.0, "percent")), policy)
        val urgent = run(
            low.state,
            sample(
                moment = at(1),
                battery = reading(90.0, "percent", status = ObservationStatus.STALE),
                alert = reading(true, "flag"),
            ),
            policy,
        )
        assertEquals(PowerAxis.LOW, urgent.state.power)
        assertEquals(WeatherAxis.ALERT, urgent.state.weather)
        assertEquals(FocusBand.CRITICAL, urgent.state.focus)
        assertNull(urgent.intent.publishedBatteryPercent)
        assertTrue(urgent.intent.reasonCodes.contains(ReasonCode.STALE_IGNORED))
        assertTrue(urgent.intent.reasonCodes.contains(ReasonCode.URGENT))
        assertEquals(QualityCandidate.ECO, urgent.intent.quality)
        assertFalse(urgent.intent.motionAllowed)
        assertTrue(urgent.intent.timeKept)
        assertTrue(urgent.intent.weatherNumbersKept)
        assertEquals(DataQuality.DEGRADED, urgent.intent.dataQuality)
    }

    @Test
    fun inBandBatteryWithDeniedActivityStaysNormalAndDegraded() {
        val advanced = run(
            null,
            sample(
                battery = reading(19.0, "percent"),
                activity = reading(null, "token", status = ObservationStatus.DENIED),
            ),
        )
        assertEquals(PowerAxis.NORMAL, advanced.state.power)
        assertEquals(ActivityAxis.UNKNOWN, advanced.state.activity)
        assertEquals(FocusBand.DECORATIVE, advanced.state.focus)
        assertEquals(DataQuality.DEGRADED, advanced.intent.dataQuality)
        assertEquals(19.0, advanced.intent.publishedBatteryPercent)
        assertTrue(advanced.intent.reasonCodes.contains(ReasonCode.DENIED_IGNORED))
        assertFalse(advanced.intent.reasonCodes.contains(ReasonCode.POWER_LOW))
        assertEquals(QualityCandidate.BALANCED, advanced.intent.quality)
    }

    private fun freshPercent(percent: Double, moment: Instant) = reading(
        percent,
        "percent",
        expiresAt = Instant.MAX,
        observedAt = moment,
        receivedAt = moment,
    )
}
