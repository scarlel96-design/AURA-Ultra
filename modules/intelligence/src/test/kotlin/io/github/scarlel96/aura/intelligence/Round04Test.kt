package io.github.scarlel96.aura.intelligence

import io.github.scarlel96.aura.domain.ObservationStatus
import java.time.Duration
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

class Round04Test {
    private fun run(
        previous: MachineState?,
        sample: IntelligenceSample,
        policy: PolicyCandidates = openPolicy(),
    ): StepResult.Advanced {
        return assertIs(step(previous, sample, policy))
    }

    @Test
    fun freshLowBatteryLimitsDecorationWithoutChangingTheChargingAxis() {
        assertEquals(listOf(PowerAxis.NORMAL, PowerAxis.LOW, PowerAxis.CHARGING), PowerAxis.entries)
        val policy = PolicyCandidates.documented()
        val plugged = run(
            null,
            sample(battery = reading(90.0, "percent"), charging = reading(true, "flag")),
            policy,
        )
        val omitted = run(plugged.state, sample(moment = at(1), battery = reading(10.0, "percent")), policy)
        assertEquals(PowerAxis.CHARGING, omitted.state.power)
        assertEquals(FocusBand.POWER, omitted.state.focus)
        assertEquals(QualityCandidate.BALANCED, omitted.intent.quality)
        assertTrue(omitted.intent.motionAllowed)
        assertFalse(omitted.intent.particleEffectsAllowed)
        assertTrue(omitted.intent.graphicsPowerLimited)
        assertTrue(omitted.intent.weatherNumbersKept)
        assertEquals(10.0, omitted.intent.publishedBatteryPercent)
        assertTrue(omitted.intent.reasonCodes.contains(ReasonCode.POWER_LOW))
        assertTrue(omitted.intent.reasonCodes.contains(ReasonCode.POWER_CHARGING))
    }

    @Test
    fun lowPowerGraphicsDoNotWaitForDebounceOrHold() {
        val policy = PolicyCandidates.documented().copy(debounce = Duration.ofSeconds(30))
        val first = run(null, sample(battery = reading(80.0, "percent")), policy)
        val early = run(first.state, sample(moment = at(10), battery = reading(10.0, "percent")), policy)
        assertEquals(PowerAxis.NORMAL, early.state.power)
        assertEquals(PowerAxis.LOW, early.state.pending?.power)
        assertEquals(FocusBand.POWER, early.state.focus)
        assertFalse(early.intent.particleEffectsAllowed)
        assertTrue(early.intent.motionAllowed)
        assertEquals(QualityCandidate.BALANCED, early.intent.quality)
        assertEquals(10.0, early.intent.publishedBatteryPercent)
        assertTrue(early.intent.weatherNumbersKept)
        val committed = run(early.state, sample(moment = at(60), battery = reading(10.0, "percent")), policy)
        assertEquals(PowerAxis.LOW, committed.state.power)
        assertEquals(QualityCandidate.ECO, committed.intent.quality)
        assertFalse(committed.intent.motionAllowed)
        assertFalse(committed.intent.particleEffectsAllowed)
    }

    @Test
    fun ceilingProtectionIsDeliveredWhenRevisionStaysAtTheLimit() {
        val base = run(null, sample(battery = reading(80.0, "percent")))
        val maxed = base.state.copy(revision = Long.MAX_VALUE)
        val reduced = run(maxed, sample(moment = at(1), motionReduction = true))
        val delivered = assertNotNull(reduced.deliveredIntent())
        assertEquals(Long.MAX_VALUE, delivered.revision)
        assertEquals(maxed.revision, delivered.revision)
        assertFalse(delivered.motionAllowed)
        assertTrue(delivered.reasonCodes.contains(ReasonCode.MOTION_REDUCTION))
        assertEquals("BALANCED", delivered.toPresentationDraft().quality)
        assertTrue(
            delivered.toPresentationDraft().reasonCodes.orEmpty().contains(ReasonCode.MOTION_REDUCTION.name),
        )
        val low = run(maxed, sample(moment = at(1), battery = reading(10.0, "percent")))
        val lowIntent = assertNotNull(low.deliveredIntent())
        assertEquals(Long.MAX_VALUE, lowIntent.revision)
        assertEquals(PowerAxis.NORMAL, low.state.power)
        assertEquals(FocusBand.POWER, lowIntent.focus)
        assertFalse(lowIntent.particleEffectsAllowed)
        assertTrue(lowIntent.motionAllowed)
        assertEquals(80.0, lowIntent.publishedBatteryPercent)
        assertTrue(lowIntent.reasonCodes.contains(ReasonCode.REVISION_EXHAUSTED))
        val unchanged = assertIs<StepResult.LimitReached>(
            step(reduced.state, sample(moment = at(2), motionReduction = false), openPolicy()),
        )
        assertSame(reduced.state, unchanged.state)
        assertNull(unchanged.deliveredIntent())
    }

    @Test
    fun ceilingWithdrawsExpiredAndDeniedPublications() {
        val base = run(null, sample(battery = reading(40.0, "percent"), precipitation = reading(70.0, "percent")))
        val maxed = base.state.copy(revision = Long.MAX_VALUE)
        val expired = run(
            maxed,
            sample(moment = at(1), battery = reading(40.0, "percent", expiresAt = at(1))),
        )
        assertEquals(Long.MAX_VALUE, expired.state.revision)
        assertNull(expired.intent.publishedBatteryPercent)
        assertEquals(70.0, expired.intent.publishedPrecipitation)
        assertEquals(DataQuality.DEGRADED, expired.intent.dataQuality)
        assertTrue(expired.intent.reasonCodes.contains(ReasonCode.STALE_IGNORED))
        assertEquals(PowerAxis.NORMAL, expired.state.power)
        val denied = run(
            maxed,
            sample(
                moment = at(1),
                precipitation = reading(null, "percent", status = ObservationStatus.DENIED),
            ),
        )
        assertNull(denied.intent.publishedPrecipitation)
        assertEquals(40.0, denied.intent.publishedBatteryPercent)
        assertTrue(denied.intent.reasonCodes.contains(ReasonCode.DENIED_IGNORED))
        assertEquals(Long.MAX_VALUE, denied.intent.revision)
        assertNotNull(denied.deliveredIntent())
    }

    @Test
    fun anotherAxisDoesNotRestartDebounceOrHold() {
        val held = openPolicy(hold = Duration.ofSeconds(60), debounce = Duration.ZERO)
        val alert = run(null, sample(alert = reading(true, "flag")), held)
        val leaving = run(alert.state, sample(moment = at(1), alert = reading(false, "flag")), held)
        val plugged = run(
            leaving.state,
            sample(moment = at(10), alert = reading(false, "flag"), charging = reading(true, "flag")),
            held,
        )
        assertEquals(WeatherAxis.ALERT, plugged.state.weather)
        assertEquals(PowerAxis.CHARGING, plugged.state.power)
        val due = run(
            plugged.state,
            sample(moment = at(60), alert = reading(false, "flag"), charging = reading(true, "flag")),
            held,
        )
        assertEquals(WeatherAxis.NORMAL, due.state.weather)
        assertEquals(PowerAxis.CHARGING, due.state.power)
        val debounced = openPolicy(hold = Duration.ZERO, debounce = Duration.ofSeconds(30))
        var state = run(
            null,
            sample(battery = reading(80.0, "percent"), activity = reading("REST", "token")),
            debounced,
        ).state
        state = run(
            state,
            sample(moment = at(1), battery = reading(10.0, "percent"), activity = reading("REST", "token")),
            debounced,
        ).state
        assertEquals(PowerAxis.NORMAL, state.power)
        assertFalse(state.emission.particleEffectsAllowed)
        state = run(
            state,
            sample(moment = at(20), battery = reading(10.0, "percent"), activity = reading("EXERCISE", "token")),
            debounced,
        ).state
        assertEquals(PowerAxis.NORMAL, state.power)
        assertEquals(ActivityAxis.REST, state.activity)
        state = run(
            state,
            sample(moment = at(40), battery = reading(10.0, "percent"), activity = reading("ACTIVE", "token")),
            debounced,
        ).state
        assertEquals(PowerAxis.LOW, state.power)
        assertEquals(ActivityAxis.REST, state.activity)
        assertEquals(ActivityAxis.ACTIVE, state.pending?.activity)
    }
}
