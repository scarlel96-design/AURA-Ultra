package io.github.scarlel96.aura.intelligence

import io.github.scarlel96.aura.domain.ObservationStatus
import io.github.scarlel96.aura.domain.draft.validatePresentationIntentDraft
import java.time.Duration
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNull
import kotlin.test.assertTrue

class MachineTest {
    private fun run(
        previous: MachineState?,
        sample: IntelligenceSample,
        policy: PolicyCandidates = openPolicy(),
    ): StepResult.Advanced {
        return assertIs(step(previous, sample, policy))
    }

    @Test
    fun firstStepStartsAtRevisionOneAndDoesNotInferActivity() {
        val advanced = run(null, sample())
        assertEquals(1L, advanced.state.revision)
        assertEquals(origin, advanced.state.committedAt)
        assertNull(advanced.state.pending)
        assertEquals(PowerAxis.NORMAL, advanced.state.power)
        assertEquals(WeatherAxis.NORMAL, advanced.state.weather)
        assertEquals(ActivityAxis.UNKNOWN, advanced.state.activity)
        assertEquals(LightAxis.DAY, advanced.state.light)
        assertEquals(ConnectivityAxis.ONLINE, advanced.state.connectivity)
        assertEquals(UserModeAxis.DEFAULT, advanced.state.userMode)
        assertEquals(FocusBand.DECORATIVE, advanced.state.focus)
        assertEquals(DataQuality.SETTINGS_ONLY, advanced.intent.dataQuality)
        assertEquals(QualityCandidate.BALANCED, advanced.intent.quality)
        assertTrue(advanced.intent.motionAllowed)
        assertEquals(advanced.intent.motionAllowed, advanced.intent.particleEffectsAllowed)
        assertTrue(advanced.intent.timeKept)
        assertTrue(advanced.intent.weatherNumbersKept)
        assertNull(advanced.intent.publishedBatteryPercent)
        assertNull(advanced.intent.publishedPrecipitation)
        assertEquals(listOf(ReasonCode.DECORATIVE), advanced.intent.reasonCodes)
        val draft = advanced.intent.toPresentationDraft()
        assertEquals(1L, draft.revision)
        assertEquals(true, draft.motionAllowed)
        assertNull(draft.paletteId)
        assertTrue(validatePresentationIntentDraft(draft).accepted)
    }

    @Test
    fun powerHysteresisUsesTheCandidateBand() {
        val policy = openPolicy()
        val entered = run(null, sample(battery = reading(15.0, "percent")), policy)
        assertEquals(PowerAxis.LOW, entered.state.power)
        assertEquals(15.0, entered.intent.publishedBatteryPercent)
        assertEquals(FocusBand.POWER, entered.state.focus)
        assertEquals(QualityCandidate.ECO, entered.intent.quality)
        assertFalse(entered.intent.motionAllowed)
        assertFalse(entered.intent.particleEffectsAllowed)
        assertTrue(entered.intent.timeKept)
        assertTrue(entered.intent.weatherNumbersKept)
        val inside = run(entered.state, sample(moment = at(1), battery = reading(19.0, "percent")), policy)
        assertEquals(PowerAxis.LOW, inside.state.power)
        val left = run(inside.state, sample(moment = at(2), battery = reading(20.0, "percent")), policy)
        assertEquals(PowerAxis.NORMAL, left.state.power)
        assertTrue(left.intent.motionAllowed)
        val stillNormal = run(left.state, sample(moment = at(3), battery = reading(19.0, "percent")), policy)
        assertEquals(PowerAxis.NORMAL, stillNormal.state.power)
        val floor = run(stillNormal.state, sample(moment = at(4), battery = reading(0.0, "percent")), policy)
        assertEquals(PowerAxis.LOW, floor.state.power)
        val ceiling = run(floor.state, sample(moment = at(5), battery = reading(100.0, "percent")), policy)
        assertEquals(PowerAxis.NORMAL, ceiling.state.power)
    }

    @Test
    fun precipitationHysteresisDoesNotTreatAlertAsPrecip() {
        val policy = openPolicy()
        val alert = run(null, sample(alert = reading(true, "flag")), policy)
        assertEquals(WeatherAxis.ALERT, alert.state.weather)
        assertEquals(FocusBand.CRITICAL, alert.state.focus)
        assertFalse(alert.intent.reasonCodes.contains(ReasonCode.URGENT))
        val between = run(
            alert.state,
            sample(moment = at(1), alert = reading(false, "flag"), precipitation = reading(60.0, "percent")),
            policy,
        )
        assertEquals(WeatherAxis.NORMAL, between.state.weather)
        assertEquals(60.0, between.intent.publishedPrecipitation)
        val atExit = run(between.state, sample(moment = at(2), precipitation = reading(50.0, "percent")), policy)
        assertEquals(WeatherAxis.NORMAL, atExit.state.weather)
        val entered = run(atExit.state, sample(moment = at(3), precipitation = reading(70.0, "percent")), policy)
        assertEquals(WeatherAxis.PRECIP, entered.state.weather)
        assertEquals(FocusBand.WEATHER, entered.state.focus)
        val held = run(entered.state, sample(moment = at(4), precipitation = reading(51.0, "percent")), policy)
        assertEquals(WeatherAxis.PRECIP, held.state.weather)
        val left = run(held.state, sample(moment = at(5), precipitation = reading(50.0, "percent")), policy)
        assertEquals(WeatherAxis.NORMAL, left.state.weather)
        val belowEnter = run(left.state, sample(moment = at(6), precipitation = reading(69.0, "percent")), policy)
        assertEquals(WeatherAxis.NORMAL, belowEnter.state.weather)
    }

    @Test
    fun priorityPrefersCriticalThenPowerThenExerciseThenWeatherThenContext() {
        val everything = run(
            null,
            sample(
                battery = reading(10.0, "percent"),
                precipitation = reading(90.0, "percent"),
                alert = reading(true, "flag"),
                activity = reading("EXERCISE", "token"),
                light = reading("NIGHT", "token"),
                connectivity = reading("OFFLINE", "token"),
                userMode = reading("WORK", "token"),
            ),
        )
        assertEquals(FocusBand.CRITICAL, everything.state.focus)
        assertTrue(everything.intent.reasonCodes.contains(ReasonCode.WEATHER_ALERT))
        assertTrue(everything.intent.reasonCodes.contains(ReasonCode.OFFLINE))
        assertFalse(everything.intent.motionAllowed)
        val power = run(
            null,
            sample(
                battery = reading(10.0, "percent"),
                precipitation = reading(90.0, "percent"),
                activity = reading("EXERCISE", "token"),
            ),
        )
        assertEquals(FocusBand.POWER, power.state.focus)
        val exercise = run(
            null,
            sample(
                battery = reading(80.0, "percent"),
                precipitation = reading(90.0, "percent"),
                activity = reading("EXERCISE", "token"),
                userMode = reading("SLEEP", "token"),
            ),
        )
        assertEquals(FocusBand.EXERCISE, exercise.state.focus)
        val weather = run(
            null,
            sample(
                precipitation = reading(90.0, "percent"),
                activity = reading("ACTIVE", "token"),
                light = reading("NIGHT", "token"),
                connectivity = reading("OFFLINE", "token"),
                userMode = reading("MANUAL", "token"),
            ),
        )
        assertEquals(FocusBand.WEATHER, weather.state.focus)
        assertEquals(FocusBand.CONTEXT, run(null, sample(light = reading("NIGHT", "token"))).state.focus)
        val offline = run(null, sample(connectivity = reading("OFFLINE", "token")))
        assertEquals(FocusBand.CONTEXT, offline.state.focus)
        assertTrue(offline.intent.reasonCodes.contains(ReasonCode.OFFLINE))
        assertEquals(FocusBand.CONTEXT, run(null, sample(activity = reading("ACTIVE", "token"))).state.focus)
        assertEquals(FocusBand.CONTEXT, run(null, sample(userMode = reading("SLEEP", "token"))).state.focus)
        assertEquals(FocusBand.DECORATIVE, run(null, sample(activity = reading("REST", "token"))).state.focus)
    }

    @Test
    fun chargingIsNotLowPowerAndBypassesHold() {
        val resting = run(
            null,
            sample(
                battery = reading(10.0, "percent"),
                charging = reading(true, "flag"),
                activity = reading("REST", "token"),
            ),
        )
        assertEquals(PowerAxis.CHARGING, resting.state.power)
        assertEquals(10.0, resting.intent.publishedBatteryPercent)
        assertEquals(FocusBand.DECORATIVE, resting.state.focus)
        assertEquals(QualityCandidate.BALANCED, resting.intent.quality)
        assertTrue(resting.intent.motionAllowed)
        assertTrue(resting.intent.reasonCodes.contains(ReasonCode.POWER_CHARGING))
        val exercise = run(
            null,
            sample(charging = reading(true, "flag"), activity = reading("EXERCISE", "token")),
        )
        assertEquals(FocusBand.EXERCISE, exercise.state.focus)
        val policy = PolicyCandidates.documented()
        val normal = run(null, sample(battery = reading(80.0, "percent")), policy)
        val plugged = run(
            normal.state,
            sample(moment = at(1), battery = reading(80.0, "percent"), charging = reading(true, "flag")),
            policy,
        )
        assertEquals(PowerAxis.CHARGING, plugged.state.power)
        assertTrue(plugged.intent.reasonCodes.contains(ReasonCode.CHARGING_EXCEPTION))
        val unplugged = run(
            plugged.state,
            sample(moment = at(2), battery = reading(80.0, "percent"), charging = reading(false, "flag")),
            policy,
        )
        assertEquals(PowerAxis.NORMAL, unplugged.state.power)
        assertTrue(unplugged.intent.reasonCodes.contains(ReasonCode.CHARGING_EXCEPTION))
        val unpluggedWithoutPercent = run(
            plugged.state,
            sample(moment = at(2), charging = reading(false, "flag")),
            policy,
        )
        assertEquals(PowerAxis.NORMAL, unpluggedWithoutPercent.state.power)
        assertNull(unpluggedWithoutPercent.intent.publishedBatteryPercent)
    }

    @Test
    fun documentedHoldAndSeparateDebounceKeepThePreviousSensorAxis() {
        val held = PolicyCandidates.documented()
        val first = run(null, sample(battery = reading(80.0, "percent")), held)
        val early = run(first.state, sample(moment = at(59), battery = reading(10.0, "percent")), held)
        assertEquals(PowerAxis.NORMAL, early.state.power)
        assertEquals(first.state.committedAt, early.state.committedAt)
        assertEquals(PowerAxis.LOW, early.state.pending?.power)
        assertTrue(early.intent.reasonCodes.contains(ReasonCode.MINIMUM_HOLD))
        assertFalse(early.intent.reasonCodes.contains(ReasonCode.DEBOUNCE))
        assertEquals(2L, early.state.revision)
        assertEquals(early.state.revision, early.intent.revision)
        val due = run(early.state, sample(moment = at(60), battery = reading(10.0, "percent")), held)
        assertEquals(PowerAxis.LOW, due.state.power)
        assertEquals(3L, due.state.revision)
        assertNull(due.state.pending)
        val leaving = run(null, sample(alert = reading(true, "flag")), held)
        val stillAlert = run(leaving.state, sample(moment = at(1), alert = reading(false, "flag")), held)
        assertEquals(WeatherAxis.ALERT, stillAlert.state.weather)
        assertTrue(stillAlert.intent.reasonCodes.contains(ReasonCode.MINIMUM_HOLD))
        val cleared = run(stillAlert.state, sample(moment = at(60), alert = reading(false, "flag")), held)
        assertEquals(WeatherAxis.NORMAL, cleared.state.weather)
        val debounced = openPolicy(hold = Duration.ZERO, debounce = Duration.ofSeconds(5))
        val baseline = run(null, sample(battery = reading(80.0, "percent")), debounced)
        val waiting = run(baseline.state, sample(battery = reading(10.0, "percent")), debounced)
        assertEquals(PowerAxis.NORMAL, waiting.state.power)
        assertEquals(origin, waiting.state.pending?.since)
        val notYet = run(waiting.state, sample(moment = at(4), battery = reading(10.0, "percent")), debounced)
        assertEquals(PowerAxis.NORMAL, notYet.state.power)
        assertEquals(origin, notYet.state.pending?.since)
        val committed = run(notYet.state, sample(moment = at(5), battery = reading(10.0, "percent")), debounced)
        assertEquals(PowerAxis.LOW, committed.state.power)
        val both = held.copy(debounce = Duration.ofSeconds(30))
        val started = run(null, sample(battery = reading(80.0, "percent")), both)
        val blocked = run(started.state, sample(moment = at(10), battery = reading(10.0, "percent")), both)
        assertTrue(blocked.intent.reasonCodes.contains(ReasonCode.DEBOUNCE))
        assertTrue(blocked.intent.reasonCodes.contains(ReasonCode.MINIMUM_HOLD))
    }

    @Test
    fun urgentAlertBypassesHoldAndCommitsTheCurrentDesiredSensors() {
        val policy = PolicyCandidates.documented()
        val quiet = run(null, sample(battery = reading(80.0, "percent"), precipitation = reading(10.0, "percent")), policy)
        val urgent = run(
            quiet.state,
            sample(moment = at(1), battery = reading(10.0, "percent"), alert = reading(true, "flag")),
            policy,
        )
        assertEquals(WeatherAxis.ALERT, urgent.state.weather)
        assertEquals(PowerAxis.LOW, urgent.state.power)
        assertEquals(FocusBand.CRITICAL, urgent.state.focus)
        assertEquals(at(1), urgent.state.committedAt)
        assertTrue(urgent.intent.reasonCodes.contains(ReasonCode.URGENT))
        assertEquals(10.0, urgent.intent.publishedBatteryPercent)
        assertTrue(urgent.intent.weatherNumbersKept)
        assertTrue(urgent.intent.timeKept)
        val staleBattery = run(
            quiet.state,
            sample(
                moment = at(1),
                battery = reading(1.0, "percent", status = ObservationStatus.STALE),
                alert = reading(true, "flag"),
            ),
            policy,
        )
        assertEquals(WeatherAxis.ALERT, staleBattery.state.weather)
        assertEquals(PowerAxis.NORMAL, staleBattery.state.power)
        assertNull(staleBattery.intent.publishedBatteryPercent)
    }

    @Test
    fun immediateAxesDoNotResetTheSensorHold() {
        val policy = PolicyCandidates.documented()
        val first = run(null, sample(battery = reading(80.0, "percent")), policy)
        val night = run(
            first.state,
            sample(moment = at(10), battery = reading(10.0, "percent"), light = reading("NIGHT", "token")),
            policy,
        )
        assertEquals(PowerAxis.NORMAL, night.state.power)
        assertEquals(LightAxis.NIGHT, night.state.light)
        assertEquals(FocusBand.CONTEXT, night.state.focus)
        assertEquals(first.state.committedAt, night.state.committedAt)
        assertEquals(2L, night.state.revision)
        val still = run(
            night.state,
            sample(moment = at(59), battery = reading(10.0, "percent"), light = reading("NIGHT", "token")),
            policy,
        )
        assertEquals(PowerAxis.NORMAL, still.state.power)
        assertEquals(2L, still.state.revision)
        val committed = run(
            still.state,
            sample(moment = at(60), battery = reading(10.0, "percent"), light = reading("NIGHT", "token")),
            policy,
        )
        assertEquals(PowerAxis.LOW, committed.state.power)
        assertEquals(FocusBand.POWER, committed.state.focus)
        assertEquals(3L, committed.state.revision)
    }

    @Test
    fun repeatedSamplesAndReturningDesiredDoNotBumpRevision() {
        val policy = openPolicy(debounce = Duration.ofSeconds(10))
        var state: MachineState? = null
        for (second in 0L until 10L) {
            val advanced = run(
                state,
                sample(moment = at(second), battery = reading(50.0, "percent"), activity = reading("REST", "token")),
                policy,
            )
            state = advanced.state
        }
        assertEquals(1L, state?.revision)
        val pending = run(state, sample(moment = at(10), activity = reading("ACTIVE", "token")), policy)
        assertEquals(ActivityAxis.REST, pending.state.activity)
        assertEquals(at(10), pending.state.pending?.since)
        val shifted = run(pending.state, sample(moment = at(12), activity = reading("EXERCISE", "token")), policy)
        assertEquals(ActivityAxis.REST, shifted.state.activity)
        assertEquals(ActivityAxis.EXERCISE, shifted.state.pending?.activity)
        assertEquals(at(12), shifted.state.pending?.since)
        val cancelled = run(shifted.state, sample(moment = at(13), activity = reading("REST", "token")), policy)
        assertEquals(ActivityAxis.REST, cancelled.state.activity)
        assertNull(cancelled.state.pending)
        assertEquals(pending.state.revision + 1, cancelled.state.revision)
    }

    @Test
    fun badObservationsAreNotPromotedAndDoNotBecomeZero() {
        val policy = openPolicy()
        val cases = listOf(
            sample(battery = reading(5.0, "percent", status = ObservationStatus.STALE)) to ReasonCode.STALE_IGNORED,
            sample(moment = at(100), battery = reading(5.0, "percent", expiresAt = at(100))) to ReasonCode.STALE_IGNORED,
            sample(battery = reading(5.0, "percent", expiresAt = null)) to ReasonCode.UNDECLARED_IGNORED,
            sample(battery = reading(null, "percent", status = ObservationStatus.DENIED)) to ReasonCode.DENIED_IGNORED,
            sample(battery = reading(null, "percent", status = ObservationStatus.UNAVAILABLE)) to ReasonCode.UNAVAILABLE_IGNORED,
            sample(battery = reading(Double.NaN, "percent")) to ReasonCode.REJECTED_IGNORED,
            sample(battery = reading(null, "percent", status = ObservationStatus.VALID)) to ReasonCode.REJECTED_IGNORED,
            sample(battery = reading(101.0, "percent")) to ReasonCode.OUTSIDE_CANDIDATE_SCALE,
            sample(battery = reading(10.0, "ratio")) to ReasonCode.UNIT_UNCHECKED,
        )
        cases.forEach { (input, reason) ->
            val advanced = run(null, input, policy)
            assertEquals(PowerAxis.NORMAL, advanced.state.power, reason.name)
            assertNull(advanced.intent.publishedBatteryPercent, reason.name)
            assertTrue(advanced.intent.reasonCodes.contains(reason), reason.name)
            assertEquals(DataQuality.DEGRADED, advanced.intent.dataQuality)
            assertTrue(advanced.intent.weatherNumbersKept)
            assertTrue(advanced.intent.timeKept)
        }
        val error = run(null, sample(activity = reading(null, "token", status = ObservationStatus.ERROR)), policy)
        assertEquals(ActivityAxis.UNKNOWN, error.state.activity)
        assertTrue(error.intent.reasonCodes.contains(ReasonCode.ERROR_IGNORED))
        val disguised = run(null, sample(activity = reading("EXERCISE", "token", status = ObservationStatus.ERROR)), policy)
        assertEquals(ActivityAxis.UNKNOWN, disguised.state.activity)
        assertTrue(disguised.intent.reasonCodes.contains(ReasonCode.REJECTED_IGNORED))
        val commute = run(null, sample(activity = reading("commute", "token")), policy)
        assertEquals(ActivityAxis.UNKNOWN, commute.state.activity)
        assertEquals(UserModeAxis.DEFAULT, commute.state.userMode)
        assertTrue(commute.intent.reasonCodes.contains(ReasonCode.TOKEN_UNCHECKED))
        val lower = run(null, sample(activity = reading("exercise", "token")), policy)
        assertEquals(ActivityAxis.UNKNOWN, lower.state.activity)
        val padded = run(null, sample(activity = reading(" EXERCISE", "token")), policy)
        assertEquals(ActivityAxis.UNKNOWN, padded.state.activity)
        val workLabel = run(null, sample(activity = reading("WORK", "token")), policy)
        assertEquals(ActivityAxis.UNKNOWN, workLabel.state.activity)
        assertEquals(UserModeAxis.DEFAULT, workLabel.state.userMode)
        val collapsed = run(
            null,
            sample(
                battery = reading(10.0, "percent", status = ObservationStatus.STALE),
                precipitation = reading(90.0, "percent", status = ObservationStatus.STALE),
            ),
            policy,
        )
        assertEquals(1, collapsed.intent.reasonCodes.count { it == ReasonCode.STALE_IGNORED })
        assertNull(collapsed.intent.publishedPrecipitation)
        assertEquals(WeatherAxis.UNKNOWN, collapsed.state.weather)
    }

    @Test
    fun omittedChannelsKeepStateAndUnusableSettingsDoNotWipeIt() {
        val policy = openPolicy()
        val low = run(
            null,
            sample(
                battery = reading(10.0, "percent"),
                precipitation = reading(80.0, "percent"),
                light = reading("NIGHT", "token"),
                userMode = reading("WORK", "token"),
            ),
            policy,
        )
        val omitted = run(low.state, sample(moment = at(1)), policy)
        assertEquals(PowerAxis.LOW, omitted.state.power)
        assertEquals(WeatherAxis.PRECIP, omitted.state.weather)
        assertEquals(LightAxis.NIGHT, omitted.state.light)
        assertEquals(UserModeAxis.WORK, omitted.state.userMode)
        assertNull(omitted.intent.publishedBatteryPercent)
        assertNull(omitted.intent.publishedPrecipitation)
        assertEquals(DataQuality.SETTINGS_ONLY, omitted.intent.dataQuality)
        val brokenMode = run(low.state, sample(moment = at(1), userMode = reading("home", "token")), policy)
        assertEquals(UserModeAxis.WORK, brokenMode.state.userMode)
        val brokenLight = run(low.state, sample(moment = at(1), light = reading("DUSK", "token")), policy)
        assertEquals(LightAxis.NIGHT, brokenLight.state.light)
        val brokenCharge = run(
            run(null, sample(charging = reading(true, "flag")), policy).state,
            sample(moment = at(1), charging = reading(null, "flag", status = ObservationStatus.UNAVAILABLE)),
            policy,
        )
        assertEquals(PowerAxis.CHARGING, brokenCharge.state.power)
        val mismatchedCharge = run(
            null,
            sample(battery = reading(10.0, "percent"), charging = reading(true, "bool")),
            policy,
        )
        assertEquals(PowerAxis.LOW, mismatchedCharge.state.power)
        assertTrue(mismatchedCharge.intent.reasonCodes.contains(ReasonCode.UNIT_UNCHECKED))
    }

    @Test
    fun lowPowerKeepsFreshWeatherNumbersWhileRemovingParticles() {
        val advanced = run(
            null,
            sample(
                battery = reading(10.0, "percent"),
                precipitation = reading(80.0, "percent"),
                connectivity = reading("OFFLINE", "token"),
            ),
        )
        assertEquals(FocusBand.POWER, advanced.state.focus)
        assertEquals(80.0, advanced.intent.publishedPrecipitation)
        assertEquals(10.0, advanced.intent.publishedBatteryPercent)
        assertTrue(advanced.intent.weatherNumbersKept)
        assertTrue(advanced.intent.timeKept)
        assertFalse(advanced.intent.motionAllowed)
        assertFalse(advanced.intent.particleEffectsAllowed)
        assertEquals(QualityCandidate.ECO, advanced.intent.quality)
        val ambient = run(null, sample(ambientDisplay = true, battery = reading(10.0, "percent"), precipitation = reading(80.0, "percent")))
        assertEquals(QualityCandidate.AOD, ambient.intent.quality)
        assertFalse(ambient.intent.motionAllowed)
        assertTrue(ambient.intent.reasonCodes.contains(ReasonCode.AOD))
        assertEquals(80.0, ambient.intent.publishedPrecipitation)
        assertTrue(ambient.intent.timeKept)
        val reduced = run(null, sample(motionReduction = true, battery = reading(90.0, "percent")))
        assertEquals(QualityCandidate.BALANCED, reduced.intent.quality)
        assertFalse(reduced.intent.motionAllowed)
        assertFalse(reduced.intent.particleEffectsAllowed)
        assertTrue(reduced.intent.reasonCodes.contains(ReasonCode.MOTION_REDUCTION))
    }

    @Test
    fun clockInversionPublishesNoNumbersAndKeepsTheMachineState() {
        val first = run(null, sample(battery = reading(80.0, "percent"), precipitation = reading(10.0, "percent")))
        val invertedSample = sample(
            moment = origin.minusSeconds(1),
            battery = reading(5.0, "percent"),
            precipitation = reading(99.0, "percent"),
            alert = reading(true, "flag"),
            motionReduction = true,
        )
        val before = invertedSample.batteryPercent
        val inverted = run(first.state, invertedSample)
        assertEquals(first.state.power, inverted.state.power)
        assertEquals(first.state.weather, inverted.state.weather)
        assertEquals(first.state.activity, inverted.state.activity)
        assertEquals(first.state.focus, inverted.state.focus)
        assertEquals(first.state.committedAt, inverted.state.committedAt)
        assertEquals(first.state.pending, inverted.state.pending)
        assertEquals(first.state.revision + 1, inverted.state.revision)
        assertEquals(inverted.state.revision, inverted.intent.revision)
        val repeated = run(inverted.state, invertedSample)
        assertEquals(inverted.state.revision, repeated.state.revision)
        assertNull(inverted.intent.publishedBatteryPercent)
        assertNull(inverted.intent.publishedPrecipitation)
        assertEquals(DataQuality.DEGRADED, inverted.intent.dataQuality)
        assertTrue(inverted.intent.reasonCodes.contains(ReasonCode.CLOCK_INVERSION))
        assertFalse(inverted.intent.reasonCodes.contains(ReasonCode.URGENT))
        assertFalse(inverted.intent.motionAllowed)
        assertTrue(inverted.intent.timeKept)
        assertTrue(inverted.intent.weatherNumbersKept)
        assertEquals(before, invertedSample.batteryPercent)
        val sameInstant = run(first.state, sample(light = reading("NIGHT", "token")))
        assertEquals(LightAxis.NIGHT, sameInstant.state.light)
        assertFalse(sameInstant.intent.reasonCodes.contains(ReasonCode.CLOCK_INVERSION))
    }

    @Test
    fun freshAlertSurvivesABadPrecipitationSample() {
        val advanced = run(
            null,
            sample(alert = reading(true, "flag"), precipitation = reading(Double.POSITIVE_INFINITY, "percent")),
        )
        assertEquals(WeatherAxis.ALERT, advanced.state.weather)
        assertEquals(FocusBand.CRITICAL, advanced.state.focus)
        assertNull(advanced.intent.publishedPrecipitation)
        assertTrue(advanced.intent.reasonCodes.contains(ReasonCode.REJECTED_IGNORED))
        val wrongUnit = run(null, sample(alert = reading(true, "ratio")))
        assertEquals(WeatherAxis.UNKNOWN, wrongUnit.state.weather)
        assertTrue(wrongUnit.intent.reasonCodes.contains(ReasonCode.UNIT_UNCHECKED))
    }

    @Test
    fun callerScaleIsNotTheDocumentedPercentScale() {
        val narrow = PolicyCandidates.documented().copy(
            minimumHold = Duration.ZERO,
            percentMaximum = 1.0,
            powerEnterPercent = 0.15,
            powerExitPercent = 0.20,
        )
        val outside = run(null, sample(battery = reading(15.0, "percent")), narrow)
        assertNull(outside.intent.publishedBatteryPercent)
        assertEquals(PowerAxis.NORMAL, outside.state.power)
        val inside = run(null, sample(battery = reading(0.10, "percent")), narrow)
        assertEquals(0.10, inside.intent.publishedBatteryPercent)
        assertEquals(PowerAxis.LOW, inside.state.power)
        assertEquals(100.0, PolicyCandidates.documented().percentMaximum)
    }

    @Test
    fun suppliedFreshChannelsStayFreshAndObservationsAreUnchanged() {
        val battery = reading(40.0, "percent")
        val snapshot = battery.copy()
        val advanced = run(null, sample(battery = battery))
        assertEquals(DataQuality.FRESH, advanced.intent.dataQuality)
        assertEquals(snapshot, battery)
        val mixed = run(
            null,
            sample(
                battery = reading(40.0, "percent"),
                activity = reading(null, "token", status = ObservationStatus.DENIED),
            ),
        )
        assertEquals(DataQuality.DEGRADED, mixed.intent.dataQuality)
        assertEquals(40.0, mixed.intent.publishedBatteryPercent)
    }

    @Test
    fun presentationChangesBumpRevisionWhenAxesStay() {
        val fresh = run(null, sample(battery = reading(40.0, "percent")))
        val stale = run(
            fresh.state,
            sample(moment = at(1), battery = reading(40.0, "percent", status = ObservationStatus.STALE)),
        )
        assertEquals(PowerAxis.NORMAL, stale.state.power)
        assertNull(stale.intent.publishedBatteryPercent)
        assertEquals(fresh.state.revision + 1, stale.state.revision)
        assertEquals(stale.state.revision, stale.intent.revision)
        val reduced = run(stale.state, sample(moment = at(2), battery = reading(40.0, "percent"), motionReduction = true))
        assertEquals(PowerAxis.NORMAL, reduced.state.power)
        assertFalse(reduced.intent.motionAllowed)
        assertEquals(stale.state.revision + 1, reduced.state.revision)
        val same = run(reduced.state, sample(moment = at(3), battery = reading(40.0, "percent"), motionReduction = true))
        assertEquals(reduced.state.revision, same.state.revision)
        assertEquals(same.state.emission, same.intent.emission())
    }
}
