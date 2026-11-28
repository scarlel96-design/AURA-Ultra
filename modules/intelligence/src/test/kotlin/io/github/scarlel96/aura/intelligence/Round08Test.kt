package io.github.scarlel96.aura.intelligence

import io.github.scarlel96.aura.domain.ObservationKind
import io.github.scarlel96.aura.domain.ObservationStatus
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNull
import kotlin.test.assertTrue

class Round08Test {
    @Test
    fun ceilingRaiseSurvivesSaturatedUnprotectAndOldSessionRelease() {
        val policy = openPolicy()
        val base = advanced(step(null, sample(battery = reading(80.0, "percent")), policy))
        val cleared = advanced(
            step(base.state, sample(moment = at(1), battery = reading(80.0, "percent")), policy, Long.MAX_VALUE),
        )
        val raised = advanced(
            step(
                base.state,
                sample(
                    moment = at(2),
                    battery = reading(10.0, "percent"),
                    motionReduction = true,
                    ambientDisplay = true,
                ),
                policy,
                Long.MAX_VALUE,
            ),
        )
        assertEquals(Long.MAX_VALUE, cleared.deliverySequence)
        assertEquals(Long.MAX_VALUE, raised.deliverySequence)
        assertFalse(raised.deliverySessionOpened)
        val consumer = ProtectionConsumer()
        consumer.push(cleared)
        consumer.push(raised)
        assertProtection(consumer, motion = true, ambient = true, graphics = true)
        consumer.push(cleared)
        assertProtection(consumer, motion = true, ambient = true, graphics = true)
        val opened = advanced(
            step(
                base.state,
                sample(
                    moment = at(3),
                    battery = reading(10.0, "percent"),
                    motionReduction = true,
                    ambientDisplay = true,
                ),
                policy,
                Long.MAX_VALUE,
                0L,
                true,
            ),
        )
        assertEquals(1L, opened.deliveryEpoch)
        assertEquals(1L, opened.deliverySequence)
        assertTrue(opened.deliverySessionOpened)
        val restarted = ProtectionConsumer()
        restarted.push(cleared)
        restarted.push(opened)
        restarted.push(cleared)
        assertProtection(restarted, motion = true, ambient = true, graphics = true)
        val release = advanced(
            step(
                opened.state,
                sample(moment = at(4), battery = reading(80.0, "percent")),
                policy,
                opened.deliverySequence,
                opened.deliveryEpoch,
                false,
            ),
        )
        assertEquals(opened.deliveryEpoch, release.deliveryEpoch)
        assertTrue(release.deliverySequence > opened.deliverySequence)
        assertFalse(release.deliverySessionOpened)
        restarted.push(release)
        assertProtection(restarted, motion = false, ambient = false, graphics = false)
        val stuck = advanced(
            step(release.state, sample(moment = at(5)), policy, Long.MAX_VALUE, Long.MAX_VALUE, true),
        )
        assertEquals(Long.MAX_VALUE, stuck.deliveryEpoch)
        assertEquals(Long.MAX_VALUE, stuck.deliverySequence)
        assertFalse(stuck.deliverySessionOpened)
        val forgedEpoch = release.copy(deliveryEpoch = 4L, deliverySessionOpened = false, deliverySequence = 1L)
        val forgedNegative = release.copy(deliverySequence = -1L)
        val guard = ProtectionConsumer()
        guard.push(opened)
        guard.push(forgedEpoch)
        guard.push(forgedNegative)
        assertProtection(guard, motion = true, ambient = true, graphics = true)
    }

    @Test
    fun duplicateReverseNegativeAndSameTickStayOrdered() {
        val policy = openPolicy()
        val base = advanced(step(null, sample(battery = reading(80.0, "percent")), policy))
        assertEquals(1L, base.deliverySequence)
        assertEquals(0L, base.deliveryEpoch)
        assertFalse(base.deliverySessionOpened)
        val ambient = advanced(
            step(base.state, sample(moment = at(1), ambientDisplay = true), policy, base.deliverySequence),
        )
        val motion = advanced(
            step(
                ambient.state,
                sample(moment = at(1), ambientDisplay = true, motionReduction = true),
                policy,
                ambient.deliverySequence,
            ),
        )
        assertEquals(ambient.state.processedAt, motion.state.processedAt)
        assertTrue(motion.deliverySequence > ambient.deliverySequence)
        val lateRelease = advanced(
            step(motion.state, sample(moment = at(1)), policy, 0L),
        )
        val negative = advanced(
            step(motion.state, sample(moment = at(2), motionReduction = false), policy, Long.MIN_VALUE),
        )
        assertEquals(1L, negative.deliverySequence)
        assertTrue(negative.deliverySequence > 0L)
        val reversed = advanced(
            step(motion.state, sample(moment = at(2)), policy, 1L),
        )
        assertTrue(reversed.deliverySequence < motion.deliverySequence)
        val consumer = ProtectionConsumer()
        consumer.push(ambient)
        consumer.push(motion)
        consumer.push(motion)
        consumer.push(lateRelease)
        consumer.push(negative)
        consumer.push(reversed)
        assertProtection(consumer, motion = true, ambient = true, graphics = false)
    }

    @Test
    fun rejectedPolicyWithdrawsExpiredAndRevokedNumbers() {
        val policy = openPolicy()
        val bad = PolicyCandidates.documented().copy(powerEnterPercent = Double.NaN)
        val first = assertIs<StepResult.PolicyRejected>(
            step(null, sample(battery = reading(10.0, "percent"), ambientDisplay = true), bad),
        )
        assertNull(first.failSafe?.publishedBatteryPercent)
        assertFalse(first.failSafe?.graphicsPowerLimited == true)
        assertEquals(QualityCandidate.AOD, first.failSafe?.quality)
        assertNull(first.deliveredIntent())
        val published = advanced(
            step(
                null,
                sample(battery = reading(10.0, "percent", expiresAt = at(30)), ambientDisplay = true),
                policy,
            ),
        )
        val stillFresh = assertIs<StepResult.PolicyRejected>(
            step(published.state, sample(moment = at(29), battery = reading(4.0, "percent", expiresAt = at(90))), bad),
        )
        assertEquals(10.0, stillFresh.failSafe?.publishedBatteryPercent)
        assertTrue(stillFresh.issues.isNotEmpty())
        val expired = assertIs<StepResult.PolicyRejected>(
            step(published.state, sample(moment = at(30), battery = reading(4.0, "percent", expiresAt = at(90))), bad),
        )
        assertNull(expired.failSafe?.publishedBatteryPercent)
        assertNull(expired.state?.emission?.publishedBatteryPercent)
        assertTrue(expired.failSafe?.graphicsPowerLimited == true)
        assertEquals(QualityCandidate.AOD, expired.failSafe?.quality)
        assertNull(expired.deliveredIntent())
        val repeated = assertIs<StepResult.PolicyRejected>(
            step(expired.state, sample(moment = at(31), battery = reading(3.0, "percent")), bad),
        )
        assertNull(repeated.failSafe?.publishedBatteryPercent)
        assertTrue(repeated.issues.isNotEmpty())
        val restored = advanced(
            step(
                repeated.state,
                sample(
                    moment = at(32),
                    battery = reading(10.0, "percent", expiresAt = at(90), observedAt = at(32)),
                    motionReduction = true,
                    ambientDisplay = true,
                ),
                policy,
            ),
        )
        assertEquals(10.0, restored.intent.publishedBatteryPercent)
        assertEquals(QualityCandidate.AOD, restored.intent.quality)
        assertFalse(restored.intent.motionAllowed)
        assertTrue(restored.intent.graphicsPowerLimited)
        val fresh = advanced(
            step(null, sample(moment = at(100), battery = reading(80.0, "percent", expiresAt = at(200), observedAt = at(100))), policy),
        )
        val inverted = assertIs<StepResult.PolicyRejected>(
            step(
                fresh.state,
                sample(
                    moment = at(50),
                    battery = reading(null, "percent", status = ObservationStatus.DENIED, observedAt = at(50)),
                ),
                bad,
            ),
        )
        assertEquals(80.0, inverted.failSafe?.publishedBatteryPercent)
        for (status in listOf(ObservationStatus.DENIED, ObservationStatus.ERROR, ObservationStatus.UNAVAILABLE)) {
            val held = advanced(step(null, sample(battery = reading(80.0, "percent", expiresAt = at(90))), policy))
            val revoked = assertIs<StepResult.PolicyRejected>(
                step(
                    held.state,
                    sample(moment = at(2), battery = reading(null, "percent", status = status, observedAt = at(2))),
                    bad,
                ),
            )
            assertNull(revoked.failSafe?.publishedBatteryPercent)
            assertNull(revoked.state?.emission?.publishedBatteryPercent)
            val late = advanced(
                step(
                    revoked.state,
                    sample(moment = at(3), battery = reading(10.0, "percent", observedAt = at(1))),
                    policy,
                ),
            )
            assertNull(late.intent.publishedBatteryPercent)
        }
    }

    @Test
    fun denialThenMidpointAndOtherStreamsDoNotRepublish() {
        val policy = openPolicy()
        val newer = advanced(
            step(null, sample(moment = at(10), battery = reading(80.0, "percent", observedAt = at(10))), policy),
        )
        val denied = advanced(
            step(
                newer.state,
                sample(
                    moment = at(20),
                    battery = reading(null, "percent", status = ObservationStatus.DENIED, observedAt = at(20)),
                ),
                policy,
            ),
        )
        assertNull(denied.intent.publishedBatteryPercent)
        val midpoint = advanced(
            step(denied.state, sample(moment = at(21), battery = reading(10.0, "percent", observedAt = at(15))), policy),
        )
        assertNull(midpoint.intent.publishedBatteryPercent)
        assertTrue(midpoint.intent.reasonCodes.contains(ReasonCode.SUPERSEDED_OBSERVATION))
        val reopened = advanced(
            step(midpoint.state, sample(moment = at(22), battery = reading(40.0, "percent", observedAt = at(22))), policy),
        )
        assertEquals(40.0, reopened.intent.publishedBatteryPercent)
        val first = advanced(
            step(null, sample(moment = at(10), battery = reading(80.0, "percent", observedAt = at(10))), policy),
        )
        val other = reading(55.0, "percent", observedAt = at(18)).copy(source = otherSource)
        val switched = advanced(step(first.state, sample(moment = at(19), battery = other), policy))
        assertEquals(55.0, switched.intent.publishedBatteryPercent)
        val back = reading(10.0, "percent", observedAt = at(12))
        val rejected = advanced(step(switched.state, sample(moment = at(20), battery = back), policy))
        assertEquals(55.0, rejected.intent.publishedBatteryPercent)
        assertTrue(rejected.intent.reasonCodes.contains(ReasonCode.SUPERSEDED_OBSERVATION))
        val paired = advanced(
            step(
                null,
                sample(
                    moment = at(10),
                    battery = reading(80.0, "percent", observedAt = at(10)),
                    precipitation = reading(20.0, "percent", observedAt = at(10)),
                ),
                policy,
            ),
        )
        val precipDenied = advanced(
            step(
                paired.state,
                sample(
                    moment = at(20),
                    battery = reading(80.0, "percent", observedAt = at(10)),
                    precipitation = reading(null, "percent", status = ObservationStatus.ERROR, observedAt = at(20)),
                ),
                policy,
            ),
        )
        assertNull(precipDenied.intent.publishedPrecipitation)
        assertEquals(80.0, precipDenied.intent.publishedBatteryPercent)
        val batteryMid = advanced(
            step(
                precipDenied.state,
                sample(moment = at(21), battery = reading(70.0, "percent", observedAt = at(15))),
                policy,
            ),
        )
        assertEquals(70.0, batteryMid.intent.publishedBatteryPercent)
        val precipMid = advanced(
            step(
                batteryMid.state,
                sample(
                    moment = at(22),
                    battery = reading(70.0, "percent", observedAt = at(15)),
                    precipitation = reading(5.0, "percent", observedAt = at(15)),
                ),
                policy,
            ),
        )
        assertNull(precipMid.intent.publishedPrecipitation)
        assertEquals(70.0, precipMid.intent.publishedBatteryPercent)
    }

    @Test
    fun forecastAndOlderAxesDoNotRewriteState() {
        val policy = openPolicy()
        val charging = advanced(
            step(null, sample(moment = at(20), charging = reading(true, "flag", observedAt = at(20))), policy),
        )
        val lateOff = advanced(
            step(charging.state, sample(moment = at(30), charging = reading(false, "flag", observedAt = at(15))), policy),
        )
        assertEquals(PowerAxis.CHARGING, lateOff.state.power)
        assertTrue(lateOff.intent.reasonCodes.contains(ReasonCode.SUPERSEDED_OBSERVATION))
        val deniedCharge = advanced(
            step(
                charging.state,
                sample(
                    moment = at(21),
                    charging = reading(null, "flag", status = ObservationStatus.DENIED, observedAt = at(21)),
                ),
                policy,
            ),
        )
        assertEquals(PowerAxis.CHARGING, deniedCharge.state.power)
        val olderAfterDenial = advanced(
            step(deniedCharge.state, sample(moment = at(22), charging = reading(false, "flag", observedAt = at(16))), policy),
        )
        assertEquals(PowerAxis.CHARGING, olderAfterDenial.state.power)
        val axes = advanced(
            step(
                null,
                sample(
                    moment = at(20),
                    alert = reading(true, "flag", observedAt = at(20)),
                    activity = reading("EXERCISE", "token", observedAt = at(20)),
                    light = reading("NIGHT", "token", observedAt = at(20)),
                    connectivity = reading("OFFLINE", "token", observedAt = at(20)),
                    userMode = reading("WORK", "token", observedAt = at(20)),
                ),
                policy,
            ),
        )
        val staleAxes = advanced(
            step(
                axes.state,
                sample(
                    moment = at(30),
                    alert = reading(false, "flag", observedAt = at(15)),
                    activity = reading("REST", "token", observedAt = at(15)),
                    light = reading("DAY", "token", observedAt = at(15)),
                    connectivity = reading("ONLINE", "token", observedAt = at(15)),
                    userMode = reading("DEFAULT", "token", observedAt = at(15)),
                ),
                policy,
            ),
        )
        assertEquals(WeatherAxis.ALERT, staleAxes.state.weather)
        assertEquals(ActivityAxis.EXERCISE, staleAxes.state.activity)
        assertEquals(LightAxis.NIGHT, staleAxes.state.light)
        assertEquals(ConnectivityAxis.OFFLINE, staleAxes.state.connectivity)
        assertEquals(UserModeAxis.WORK, staleAxes.state.userMode)
        val forecastCharge = reading(true, "flag", observedAt = at(5)).copy(kind = ObservationKind.FORECAST)
        val forecasted = advanced(step(null, sample(moment = at(6), charging = forecastCharge), policy))
        assertEquals(PowerAxis.NORMAL, forecasted.state.power)
        assertTrue(forecasted.intent.reasonCodes.contains(ReasonCode.FORECAST_SEPARATE))
        val forecastBattery = reading(10.0, "percent", observedAt = at(5)).copy(kind = ObservationKind.FORECAST)
        val lowForecast = advanced(step(null, sample(moment = at(6), battery = forecastBattery), policy))
        assertNull(lowForecast.intent.publishedBatteryPercent)
        assertFalse(lowForecast.intent.graphicsPowerLimited)
        assertEquals(PowerAxis.NORMAL, lowForecast.state.power)
        val forecastPrecip = reading(90.0, "percent", observedAt = at(5)).copy(kind = ObservationKind.FORECAST)
        val precip = advanced(step(null, sample(moment = at(6), precipitation = forecastPrecip), policy))
        assertEquals(90.0, precip.intent.publishedPrecipitation)
        assertEquals(WeatherAxis.NORMAL, precip.state.weather)
        val forecastAxes = advanced(
            step(
                axes.state,
                sample(
                    moment = at(31),
                    alert = reading(false, "flag", observedAt = at(40)).copy(kind = ObservationKind.FORECAST),
                    activity = reading("REST", "token", observedAt = at(40)).copy(kind = ObservationKind.FORECAST),
                ),
                policy,
            ),
        )
        assertEquals(WeatherAxis.ALERT, forecastAxes.state.weather)
        assertEquals(ActivityAxis.EXERCISE, forecastAxes.state.activity)
    }

    @Test
    fun ceilingResyncDoesNotBypassValidation() {
        val policy = openPolicy()
        val published = advanced(
            step(
                null,
                sample(
                    moment = at(10),
                    battery = reading(80.0, "percent", expiresAt = at(30), observedAt = at(10)),
                    precipitation = reading(20.0, "percent", expiresAt = at(30), observedAt = at(10)),
                ),
                policy,
            ),
        )
        val maxed = published.state.copy(revision = Long.MAX_VALUE)
        val forecast = reading(7.0, "percent", expiresAt = at(90), observedAt = at(40)).copy(kind = ObservationKind.FORECAST)
        val extended = heldState(step(maxed, sample(moment = at(20), battery = forecast, resync = true), policy))
        assertEquals(80.0, extended.emission.publishedBatteryPercent)
        val due = publishedNumber(step(extended, sample(moment = at(30)), policy))
        assertNull(due)
        val again = published.state.copy(revision = Long.MAX_VALUE)
        val superseded = heldState(
            step(
                again,
                sample(
                    moment = at(20),
                    battery = reading(10.0, "percent", expiresAt = at(90), observedAt = at(1)),
                    resync = true,
                ),
                policy,
            ),
        )
        assertEquals(80.0, superseded.emission.publishedBatteryPercent)
        assertNull(publishedNumber(step(superseded, sample(moment = at(30)), policy)))
        val denied = publishedNumber(
            step(
                again,
                sample(
                    moment = at(20),
                    battery = reading(null, "percent", status = ObservationStatus.DENIED, observedAt = at(20)),
                    resync = true,
                ),
                policy,
            ),
        )
        assertNull(denied)
        val omitted = heldState(step(again, sample(moment = at(20), resync = true), policy))
        assertEquals(80.0, omitted.emission.publishedBatteryPercent)
        assertEquals(20.0, omitted.emission.publishedPrecipitation)
        val future = heldState(
            step(
                again,
                sample(
                    moment = at(20),
                    battery = reading(1.0, "percent", expiresAt = at(90), observedAt = at(50)),
                    resync = true,
                ),
                policy,
            ),
        )
        assertEquals(80.0, future.emission.publishedBatteryPercent)
        val both = publishedNumber(step(again, sample(moment = at(30)), policy))
        assertNull(both)
        val bothState = heldState(step(again, sample(moment = at(30)), policy))
        assertNull(bothState.emission.publishedPrecipitation)
        val reversed = heldState(
            step(
                again,
                sample(moment = at(5), battery = reading(1.0, "percent", expiresAt = at(9)), resync = true),
                policy,
            ),
        )
        assertEquals(80.0, reversed.emission.publishedBatteryPercent)
        assertEquals(at(10), reversed.processedAt)
    }

    private fun assertProtection(consumer: ProtectionConsumer, motion: Boolean, ambient: Boolean, graphics: Boolean) {
        assertEquals(motion, consumer.motionReduction)
        assertEquals(ambient, consumer.ambientDisplay)
        assertEquals(graphics, consumer.graphicsPowerLimited)
    }

    private fun advanced(result: StepResult): StepResult.Advanced = assertIs(result)

    private fun heldState(result: StepResult): MachineState {
        return when (result) {
            is StepResult.Advanced -> result.state
            is StepResult.LimitReached -> result.state
            is StepResult.PolicyRejected -> error("policy")
        }
    }

    private fun publishedNumber(result: StepResult): Double? {
        return when (result) {
            is StepResult.Advanced -> result.intent.publishedBatteryPercent
            is StepResult.LimitReached -> result.state.emission.publishedBatteryPercent
            is StepResult.PolicyRejected -> error("policy")
        }
    }
}
