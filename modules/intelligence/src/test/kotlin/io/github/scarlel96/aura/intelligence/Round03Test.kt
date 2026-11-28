package io.github.scarlel96.aura.intelligence

import io.github.scarlel96.aura.domain.ObservationStatus
import java.time.Duration
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNull
import kotlin.test.assertTrue

class Round03Test {
    private fun run(
        previous: MachineState?,
        sample: IntelligenceSample,
        policy: PolicyCandidates = openPolicy(),
    ): StepResult.Advanced {
        return assertIs(step(previous, sample, policy))
    }

    @Test
    fun olderSampleCannotClearLatestAodAndMotionReduction() {
        val protected = run(
            null,
            sample(ambientDisplay = true, motionReduction = true, battery = reading(80.0, "percent")),
        )
        val latest = run(
            protected.state,
            sample(moment = at(100), ambientDisplay = true, motionReduction = true, battery = reading(80.0, "percent")),
        )
        val older = run(
            latest.state,
            sample(moment = at(50), ambientDisplay = false, motionReduction = false, battery = reading(10.0, "percent")),
        )
        assertEquals(QualityCandidate.AOD, older.intent.quality)
        assertFalse(older.intent.motionAllowed)
        assertFalse(older.intent.particleEffectsAllowed)
        assertTrue(older.intent.reasonCodes.contains(ReasonCode.AOD))
        assertTrue(older.intent.reasonCodes.contains(ReasonCode.MOTION_REDUCTION))
        assertTrue(older.intent.reasonCodes.contains(ReasonCode.CLOCK_INVERSION))
        assertEquals(PowerAxis.NORMAL, older.state.power)
        assertNull(older.intent.publishedBatteryPercent)
        assertEquals(at(100), older.state.processedAt)
        assertEquals(true, older.state.settings.ambientDisplay)
        assertEquals(true, older.state.settings.motionReduction)
    }

    @Test
    fun sameInstantReplacesSettingsBecauseItIsNotAnOlderObservation() {
        val enabled = run(
            null,
            sample(moment = at(10), ambientDisplay = true, motionReduction = true),
        )
        val replaced = run(
            enabled.state,
            sample(moment = at(10), ambientDisplay = false, motionReduction = false, light = reading("NIGHT", "token")),
        )
        assertEquals(QualityCandidate.BALANCED, replaced.intent.quality)
        assertTrue(replaced.intent.motionAllowed)
        assertEquals(LightAxis.NIGHT, replaced.state.light)
        assertFalse(replaced.intent.reasonCodes.contains(ReasonCode.CLOCK_INVERSION))
        assertEquals(false, replaced.state.settings.ambientDisplay)
        assertEquals(false, replaced.state.settings.motionReduction)
    }

    @Test
    fun urgentAlertDoesNotBypassAnUnrelatedActivityDebounce() {
        val policy = openPolicy(hold = Duration.ZERO, debounce = Duration.ofSeconds(30))
        val resting = run(null, sample(activity = reading("REST", "token")), policy)
        val waiting = run(resting.state, sample(moment = at(1), activity = reading("EXERCISE", "token")), policy)
        assertEquals(ActivityAxis.REST, waiting.state.activity)
        val urgent = run(
            waiting.state,
            sample(moment = at(2), activity = reading("EXERCISE", "token"), alert = reading(true, "flag")),
            policy,
        )
        assertEquals(WeatherAxis.ALERT, urgent.state.weather)
        assertEquals(ActivityAxis.REST, urgent.state.activity)
        assertEquals(ActivityAxis.EXERCISE, urgent.state.pending?.activity)
        assertTrue(urgent.intent.reasonCodes.contains(ReasonCode.URGENT))
        assertTrue(urgent.intent.reasonCodes.contains(ReasonCode.DEBOUNCE))
    }

    @Test
    fun chargingExceptionDoesNotBypassUnrelatedWeatherOrActivity() {
        val held = PolicyCandidates.documented()
        val alert = run(null, sample(alert = reading(true, "flag")), held)
        val early = run(
            alert.state,
            sample(moment = at(1), alert = reading(false, "flag"), charging = reading(true, "flag")),
            held,
        )
        assertEquals(PowerAxis.CHARGING, early.state.power)
        assertEquals(WeatherAxis.ALERT, early.state.weather)
        assertEquals(WeatherAxis.NORMAL, early.state.pending?.weather)
        assertTrue(early.intent.reasonCodes.contains(ReasonCode.CHARGING_EXCEPTION))
        assertTrue(early.intent.reasonCodes.contains(ReasonCode.MINIMUM_HOLD))
        val debounced = openPolicy(hold = Duration.ZERO, debounce = Duration.ofSeconds(20))
        val resting = run(null, sample(activity = reading("REST", "token")), debounced)
        val waiting = run(resting.state, sample(moment = at(1), activity = reading("EXERCISE", "token")), debounced)
        val plugged = run(
            waiting.state,
            sample(moment = at(2), activity = reading("EXERCISE", "token"), charging = reading(true, "flag")),
            debounced,
        )
        assertEquals(PowerAxis.CHARGING, plugged.state.power)
        assertEquals(ActivityAxis.REST, plugged.state.activity)
        assertEquals(ActivityAxis.EXERCISE, plugged.state.pending?.activity)
        assertTrue(plugged.intent.reasonCodes.contains(ReasonCode.CHARGING_EXCEPTION))
        assertTrue(plugged.intent.reasonCodes.contains(ReasonCode.DEBOUNCE))
    }

    @Test
    fun missingChargingAndLowBatteryDoNotAddAPowerAxis() {
        assertEquals(listOf(PowerAxis.NORMAL, PowerAxis.LOW, PowerAxis.CHARGING), PowerAxis.entries)
        val policy = PolicyCandidates.documented()
        val plugged = run(
            null,
            sample(battery = reading(90.0, "percent"), charging = reading(true, "flag")),
            policy,
        )
        val omitted = run(plugged.state, sample(moment = at(1), battery = reading(10.0, "percent")), policy)
        assertEquals(PowerAxis.CHARGING, omitted.state.power)
        assertEquals(QualityCandidate.BALANCED, omitted.intent.quality)
        // DATA_INTELLIGENCE: fresh low battery limits decoration and particles without a new axis.
        assertEquals(FocusBand.POWER, omitted.state.focus)
        assertTrue(omitted.intent.motionAllowed)
        assertFalse(omitted.intent.particleEffectsAllowed)
        assertTrue(omitted.intent.reasonCodes.contains(ReasonCode.POWER_LOW))
        assertTrue(omitted.intent.reasonCodes.contains(ReasonCode.POWER_CHARGING))
        assertEquals(10.0, omitted.intent.publishedBatteryPercent)
    }

    @Test
    fun revisionCeilingAppliesProtectionWithoutWrapping() {
        val base = run(null, sample(battery = reading(50.0, "percent")))
        val maxed = base.state.copy(revision = Long.MAX_VALUE)
        val reduced = run(maxed, sample(moment = at(1), motionReduction = true))
        assertEquals(Long.MAX_VALUE, reduced.state.revision)
        assertFalse(reduced.intent.motionAllowed)
        assertTrue(reduced.intent.reasonCodes.contains(ReasonCode.MOTION_REDUCTION))
        assertEquals(PowerAxis.NORMAL, reduced.state.power)
        assertEquals(at(1), reduced.state.processedAt)
        val ambient = run(maxed, sample(moment = at(1), ambientDisplay = true))
        assertEquals(QualityCandidate.AOD, ambient.intent.quality)
        assertFalse(ambient.intent.motionAllowed)
        assertEquals(Long.MAX_VALUE, ambient.state.revision)
        assertTrue(ambient.intent.reasonCodes.contains(ReasonCode.AOD))
        val mixed = run(
            maxed,
            sample(moment = at(2), light = reading("NIGHT", "token"), motionReduction = true),
        )
        assertEquals(LightAxis.DAY, mixed.state.light)
        assertFalse(mixed.intent.motionAllowed)
        assertEquals(Long.MAX_VALUE, mixed.state.revision)
        assertTrue(mixed.intent.reasonCodes.contains(ReasonCode.MOTION_REDUCTION))
        assertTrue(mixed.intent.reasonCodes.contains(ReasonCode.REVISION_EXHAUSTED))
        val clearing = assertIs<StepResult.LimitReached>(
            step(reduced.state, sample(moment = at(3), motionReduction = false), openPolicy()),
        )
        assertEquals(ReasonCode.REVISION_EXHAUSTED, clearing.reason)
        assertEquals(at(3), clearing.state.processedAt)
        assertEquals(Long.MAX_VALUE, clearing.state.revision)
        assertFalse(clearing.state.emission.motionAllowed)
    }

    @Test
    fun missingExpiryDenialInversionAndRapidRepeatsStayDistinct() {
        val policy = openPolicy(hold = Duration.ofSeconds(60), debounce = Duration.ofSeconds(10))
        var state = run(
            null,
            sample(
                battery = reading(80.0, "percent"),
                charging = reading(true, "flag"),
                activity = reading("REST", "token"),
                ambientDisplay = true,
                motionReduction = true,
            ),
            policy,
        ).state
        for (second in 1L..5L) {
            val repeated = run(
                state,
                sample(
                    moment = at(second),
                    battery = reading(80.0, "percent"),
                    charging = reading(true, "flag"),
                    activity = reading("REST", "token"),
                    ambientDisplay = true,
                    motionReduction = true,
                ),
                policy,
            )
            assertEquals(1L, repeated.state.revision)
            assertEquals(PowerAxis.CHARGING, repeated.state.power)
            assertEquals(QualityCandidate.AOD, repeated.intent.quality)
            assertFalse(repeated.intent.motionAllowed)
            state = repeated.state
        }
        assertEquals(at(5), state.processedAt)
        val degraded = run(
            state,
            sample(
                moment = at(6),
                battery = reading(5.0, "percent", status = ObservationStatus.STALE),
                activity = reading(null, "token", status = ObservationStatus.DENIED),
                ambientDisplay = true,
                motionReduction = true,
            ),
            policy,
        )
        assertEquals(PowerAxis.CHARGING, degraded.state.power)
        assertEquals(ActivityAxis.REST, degraded.state.activity)
        assertEquals(ActivityAxis.UNKNOWN, degraded.state.pending?.activity)
        assertNull(degraded.intent.publishedBatteryPercent)
        assertEquals(DataQuality.DEGRADED, degraded.intent.dataQuality)
        assertEquals(QualityCandidate.AOD, degraded.intent.quality)
        assertTrue(degraded.intent.reasonCodes.contains(ReasonCode.STALE_IGNORED))
        assertTrue(degraded.intent.reasonCodes.contains(ReasonCode.DENIED_IGNORED))
        assertTrue(degraded.intent.reasonCodes.contains(ReasonCode.DEBOUNCE))
        val older = run(
            degraded.state,
            sample(
                moment = at(3),
                battery = reading(1.0, "percent", expiresAt = at(3)),
                charging = reading(false, "flag"),
                alert = reading(true, "flag"),
                activity = reading(null, "token", status = ObservationStatus.DENIED),
                ambientDisplay = false,
                motionReduction = false,
            ),
            policy,
        )
        assertEquals(PowerAxis.CHARGING, older.state.power)
        assertEquals(WeatherAxis.NORMAL, older.state.weather)
        assertEquals(ActivityAxis.REST, older.state.activity)
        assertEquals(QualityCandidate.AOD, older.intent.quality)
        assertFalse(older.intent.motionAllowed)
        assertNull(older.intent.publishedBatteryPercent)
        assertTrue(older.intent.reasonCodes.contains(ReasonCode.CLOCK_INVERSION))
        assertFalse(older.intent.reasonCodes.contains(ReasonCode.URGENT))
        assertEquals(at(6), older.state.processedAt)
        val sameInstant = run(
            older.state,
            sample(
                moment = at(6),
                battery = reading(40.0, "percent"),
                ambientDisplay = true,
                motionReduction = true,
            ),
            policy,
        )
        assertEquals(40.0, sameInstant.intent.publishedBatteryPercent)
        assertEquals(QualityCandidate.AOD, sameInstant.intent.quality)
        assertFalse(sameInstant.intent.reasonCodes.contains(ReasonCode.CLOCK_INVERSION))
        assertEquals(PowerAxis.CHARGING, sameInstant.state.power)
    }
}
