package io.github.scarlel96.aura.intelligence

import io.github.scarlel96.aura.domain.DomainParse
import io.github.scarlel96.aura.domain.ObservationKind
import io.github.scarlel96.aura.domain.SourceId
import java.time.Duration
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

class Round07Test {
    @Test
    fun olderObservationDoesNotReplaceNewerBattery() {
        val policy = openPolicy()
        val newer = advanced(step(null, sample(moment = at(20), battery = reading(80.0, "percent", observedAt = at(20))), policy))
        val lateOld = advanced(
            step(newer.state, sample(moment = at(30), battery = reading(10.0, "percent", observedAt = at(5))), policy),
        )
        assertEquals(80.0, lateOld.intent.publishedBatteryPercent)
        assertEquals(PowerAxis.NORMAL, lateOld.state.power)
        assertFalse(lateOld.intent.graphicsPowerLimited)
        assertTrue(lateOld.intent.reasonCodes.contains(ReasonCode.SUPERSEDED_OBSERVATION))
    }

    @Test
    fun sameObservationTimeWithoutRevisionFollowsCallOrder() {
        val policy = openPolicy()
        val first = advanced(step(null, sample(battery = reading(80.0, "percent")), policy))
        val second = advanced(step(first.state, sample(moment = at(1), battery = reading(50.0, "percent")), policy))
        assertEquals(50.0, second.intent.publishedBatteryPercent)
        assertFalse(second.intent.reasonCodes.contains(ReasonCode.OBSERVATION_CONFLICT))
    }

    @Test
    fun equalRevisionConflictKeepsTheFirstBattery() {
        val policy = openPolicy()
        val first = advanced(
            step(
                null,
                sample(moment = at(1), battery = reading(80.0, "percent", observedAt = at(1)), batteryRevision = 4L),
                policy,
            ),
        )
        val conflict = advanced(
            step(
                first.state,
                sample(moment = at(2), battery = reading(10.0, "percent", observedAt = at(2)), batteryRevision = 4L),
                policy,
            ),
        )
        assertEquals(80.0, conflict.intent.publishedBatteryPercent)
        assertTrue(conflict.intent.reasonCodes.contains(ReasonCode.OBSERVATION_CONFLICT))
        val duplicate = advanced(
            step(
                conflict.state,
                sample(moment = at(3), battery = reading(80.0, "percent", observedAt = at(3)), batteryRevision = 4L),
                policy,
            ),
        )
        assertEquals(80.0, duplicate.intent.publishedBatteryPercent)
        assertTrue(duplicate.intent.reasonCodes.contains(ReasonCode.DUPLICATE_OBSERVATION))
        val higher = advanced(
            step(
                duplicate.state,
                sample(moment = at(4), battery = reading(40.0, "percent", observedAt = at(1)), batteryRevision = 5L),
                policy,
            ),
        )
        assertEquals(40.0, higher.intent.publishedBatteryPercent)
    }

    @Test
    fun deniedBatteryIsNotRedisplayedByAnOlderSample() {
        val policy = openPolicy()
        val fresh = advanced(
            step(null, sample(moment = at(10), battery = reading(80.0, "percent", observedAt = at(10))), policy),
        )
        val denied = advanced(
            step(
                fresh.state,
                sample(
                    moment = at(11),
                    battery = reading(null, "percent", status = io.github.scarlel96.aura.domain.ObservationStatus.DENIED, observedAt = at(11)),
                ),
                policy,
            ),
        )
        assertNull(denied.intent.publishedBatteryPercent)
        val late = advanced(
            step(denied.state, sample(moment = at(12), battery = reading(10.0, "percent", observedAt = at(1))), policy),
        )
        assertNull(late.intent.publishedBatteryPercent)
        assertTrue(late.intent.reasonCodes.contains(ReasonCode.SUPERSEDED_OBSERVATION))
    }

    @Test
    fun newerSourceCanReplaceAnOlderSource() {
        val policy = openPolicy()
        val first = advanced(
            step(null, sample(moment = at(5), battery = reading(80.0, "percent", observedAt = at(5))), policy),
        )
        assertEquals(80.0, first.intent.publishedBatteryPercent)
        val other = reading(55.0, "percent", observedAt = at(8)).copy(source = otherSource)
        val switched = advanced(step(first.state, sample(moment = at(9), battery = other), policy))
        assertEquals(55.0, switched.intent.publishedBatteryPercent)
        val staleOther = reading(10.0, "percent", observedAt = at(2)).copy(source = otherSource)
        val rejected = advanced(step(switched.state, sample(moment = at(10), battery = staleOther), policy))
        assertEquals(55.0, rejected.intent.publishedBatteryPercent)
    }

    @Test
    fun futureObservedValueIsRejectedWithoutAProductSkew() {
        val future = gateDouble(reading(70.0, "percent", observedAt = at(20)), at(1), "percent", 0.0, 100.0)
        assertEquals(UnusableReason.FUTURE_OBSERVATION, assertIs<Channel.Unusable>(future).reason)
        val sameInstant = gateDouble(reading(70.0, "percent", observedAt = at(1)), at(1), "percent", 0.0, 100.0)
        assertEquals(70.0, assertIs<Channel.Fresh<Double>>(sameInstant).value)
        val forecast = reading(70.0, "percent", observedAt = at(20)).copy(kind = ObservationKind.FORECAST)
        assertEquals(70.0, assertIs<Channel.Fresh<Double>>(gateDouble(forecast, at(1), "percent", 0.0, 100.0)).value)
        val policy = openPolicy()
        val current = advanced(
            step(null, sample(moment = at(1), battery = reading(80.0, "percent", observedAt = at(1))), policy),
        )
        val rejected = advanced(
            step(current.state, sample(moment = at(2), battery = reading(10.0, "percent", observedAt = at(30))), policy),
        )
        assertEquals(80.0, rejected.intent.publishedBatteryPercent)
        assertTrue(rejected.intent.reasonCodes.contains(ReasonCode.FUTURE_OBSERVATION))
        assertFalse(rejected.intent.graphicsPowerLimited)
    }

    @Test
    fun forecastDoesNotReplaceAnAcceptedObservation() {
        val policy = openPolicy()
        val observed = advanced(
            step(null, sample(moment = at(2), precipitation = reading(20.0, "percent", observedAt = at(2))), policy),
        )
        val forecast = reading(90.0, "percent", observedAt = at(40)).copy(kind = ObservationKind.FORECAST)
        val kept = advanced(step(observed.state, sample(moment = at(3), precipitation = forecast), policy))
        assertEquals(20.0, kept.intent.publishedPrecipitation)
        assertTrue(kept.intent.reasonCodes.contains(ReasonCode.FORECAST_SEPARATE))
    }

    @Test
    fun ceilingDropsOmittedBatteryAfterStoredTtlAndResyncCanReplaceIt() {
        val policy = openPolicy()
        val published = advanced(step(null, sample(battery = reading(80.0, "percent", expiresAt = at(30))), policy))
        val maxed = published.state.copy(revision = Long.MAX_VALUE)
        val stillFresh = assertIs<StepResult.LimitReached>(step(maxed, sample(moment = at(29)), policy))
        assertSame(maxed, stillFresh.state)
        assertEquals(80.0, stillFresh.state.emission.publishedBatteryPercent)
        val expired = advanced(step(maxed, sample(moment = at(30)), policy))
        assertNull(expired.intent.publishedBatteryPercent)
        assertEquals(Long.MAX_VALUE, expired.intent.revision)
        val ignored = advanced(step(expired.state, sample(moment = at(31), battery = reading(10.0, "percent", expiresAt = at(90))), policy))
        assertNull(ignored.intent.publishedBatteryPercent)
        val resynced = advanced(
            step(
                ignored.state,
                sample(moment = at(32), battery = reading(40.0, "percent", expiresAt = at(90)), resync = true),
                policy,
            ),
        )
        assertEquals(40.0, resynced.intent.publishedBatteryPercent)
        assertEquals(Long.MAX_VALUE, resynced.intent.revision)
    }

    @Test
    fun chargingAndLowWaitKeepGraphicsInsideTheCandidateBand() {
        val policy = openPolicy()
        val charging = advanced(
            step(null, sample(battery = reading(10.0, "percent"), charging = reading(true, "flag")), policy),
        )
        val raised = advanced(
            step(
                charging.state,
                sample(moment = at(1), battery = reading(17.0, "percent"), charging = reading(true, "flag")),
                policy,
            ),
        )
        assertEquals(PowerAxis.CHARGING, raised.state.power)
        assertTrue(raised.intent.graphicsPowerLimited)
        val released = advanced(
            step(
                raised.state,
                sample(moment = at(2), battery = reading(20.0, "percent"), charging = reading(true, "flag")),
                policy,
            ),
        )
        assertFalse(released.intent.graphicsPowerLimited)
        val debounced = openPolicy(hold = Duration.ofSeconds(60), debounce = Duration.ofSeconds(30))
        val baseline = advanced(step(null, sample(battery = reading(50.0, "percent")), debounced))
        val waiting = advanced(step(baseline.state, sample(moment = at(10), battery = reading(10.0, "percent")), debounced))
        assertEquals(PowerAxis.NORMAL, waiting.state.power)
        assertEquals(PowerAxis.LOW, waiting.state.pending?.power)
        assertTrue(waiting.intent.graphicsPowerLimited)
        val inside = advanced(step(waiting.state, sample(moment = at(12), battery = reading(17.0, "percent")), debounced))
        assertEquals(PowerAxis.NORMAL, inside.state.power)
        assertTrue(inside.intent.graphicsPowerLimited)
        assertNull(inside.state.pending)
    }

    @Test
    fun badPolicyKeepsProtectionWithoutPretendingThePolicyIsValid() {
        val policy = openPolicy()
        val protectedState = advanced(
            step(null, sample(battery = reading(10.0, "percent"), motionReduction = true, ambientDisplay = true), policy),
        )
        val bad = PolicyCandidates.documented().copy(powerEnterPercent = Double.NaN)
        val rejected = assertIs<StepResult.PolicyRejected>(
            step(protectedState.state, sample(moment = at(1), motionReduction = true, ambientDisplay = true), bad),
        )
        assertTrue(rejected.issues.isNotEmpty())
        assertNull(rejected.deliveredIntent())
        val safe = assertNotNullIntent(rejected.failSafe)
        assertTrue(safe.graphicsPowerLimited)
        assertFalse(safe.motionAllowed)
        assertEquals(QualityCandidate.AOD, safe.quality)
        assertTrue(safe.reasonCodes.contains(ReasonCode.POLICY_REJECTED))
        assertEquals(10.0, safe.publishedBatteryPercent)
        val first = assertIs<StepResult.PolicyRejected>(step(null, sample(ambientDisplay = true), bad))
        assertEquals(0L, first.failSafe?.revision)
        assertEquals(QualityCandidate.AOD, first.failSafe?.quality)
        assertNull(first.deliveredIntent())
    }

    @Test
    fun deliverySequenceKeepsLateReleaseFromClearingNewerProtection() {
        val policy = openPolicy()
        val base = advanced(step(null, sample(battery = reading(80.0, "percent")), policy))
        val raised = advanced(
            step(base.state, sample(moment = at(1), motionReduction = true), policy, base.deliverySequence),
        )
        val sameRevision = advanced(
            step(raised.state, sample(moment = at(1), motionReduction = true), policy, raised.deliverySequence),
        )
        assertEquals(raised.state.revision, sameRevision.state.revision)
        assertTrue(sameRevision.deliverySequence > raised.deliverySequence)
        val lateRelease = advanced(
            step(raised.state, sample(moment = at(1), motionReduction = false), policy, 0L),
        )
        assertTrue(lateRelease.deliverySequence < raised.deliverySequence)
        assertTrue(lateRelease.intent.motionAllowed)
        val explicitRelease = advanced(
            step(raised.state, sample(moment = at(2), motionReduction = false), policy, sameRevision.deliverySequence),
        )
        assertTrue(explicitRelease.deliverySequence > sameRevision.deliverySequence)
        val ceiling = raised.state.copy(revision = Long.MAX_VALUE)
        val stalled = assertIs<StepResult.LimitReached>(
            step(ceiling, sample(moment = at(2)), policy, explicitRelease.deliverySequence),
        )
        assertSame(ceiling, stalled.state)
        assertTrue(stalled.deliverySequence > explicitRelease.deliverySequence)
        assertNull(stalled.deliveredIntent())
        val consumer = ProtectionConsumer()
        consumer.push(raised)
        consumer.push(lateRelease)
        consumer.push(sameRevision)
        assertTrue(consumer.motionReduction)
        consumer.push(stalled)
        assertTrue(consumer.motionReduction)
        val restarted = ProtectionConsumer()
        restarted.push(lateRelease)
        assertFalse(restarted.motionReduction)
        restarted.push(raised)
        assertTrue(restarted.motionReduction)
        val cleared = ProtectionConsumer()
        cleared.push(raised)
        cleared.push(explicitRelease)
        assertFalse(cleared.motionReduction)
        val saturated = advanced(
            step(base.state, sample(moment = at(3), motionReduction = true), policy, Long.MAX_VALUE),
        )
        val saturatedRelease = advanced(
            step(saturated.state, sample(moment = at(4), motionReduction = false), policy, Long.MAX_VALUE),
        )
        assertEquals(Long.MAX_VALUE, saturated.deliverySequence)
        assertEquals(Long.MAX_VALUE, saturatedRelease.deliverySequence)
        val held = ProtectionConsumer()
        held.push(saturated)
        held.push(saturatedRelease)
        assertTrue(held.motionReduction)
    }

    private fun advanced(result: StepResult): StepResult.Advanced {
        return assertIs<StepResult.Advanced>(result)
    }
}

internal class ProtectionConsumer {
    private var appliedSequence = 0L
    var motionReduction = false

    fun push(result: StepResult) {
        val sequence = result.deliverySequence
        if (sequence <= appliedSequence) {
            return
        }
        appliedSequence = sequence
        val intent = result.deliveredIntent() ?: (result as? StepResult.PolicyRejected)?.failSafe ?: return
        if (intent.reasonCodes.contains(ReasonCode.MOTION_REDUCTION) && !intent.motionAllowed) {
            motionReduction = true
        } else if (intent.motionAllowed) {
            motionReduction = false
        }
    }
}

private val otherSource: SourceId = when (val parsed = SourceId.parse("gb02.other")) {
    is DomainParse.Accepted -> parsed.value
    is DomainParse.Rejected -> error(parsed.code)
}

private fun assertNotNullIntent(intent: IntelligenceIntent?): IntelligenceIntent {
    return assertIs<IntelligenceIntent>(intent)
}
