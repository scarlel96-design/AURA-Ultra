package io.github.scarlel96.aura.intelligence

import io.github.scarlel96.aura.domain.Observation
import io.github.scarlel96.aura.domain.ObservationStatus
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNull
import kotlin.test.assertTrue

class Round08CloseoutTest {
    @Test
    fun lateRevocationDoesNotRestoreOlderBattery() {
        val policy = openPolicy()
        for (status in revocationStatuses) {
            val current = advanced(
                step(null, sample(moment = at(10), battery = battery(80.0, at(10))), policy),
            )
            val revoked = advanced(
                step(current.state, sample(moment = at(20), battery = revocation(status, at(20))), policy),
            )
            assertNull(revoked.intent.publishedBatteryPercent)
            assertEquals(at(20), revoked.state.observationMemory.battery?.observedAt)
            val late = advanced(
                step(
                    revoked.state,
                    sample(moment = at(22), battery = revocation(status, at(12)).copy(source = otherSource)),
                    policy,
                ),
            )
            assertNull(late.intent.publishedBatteryPercent)
            assertEquals(at(20), late.state.observationMemory.battery?.observedAt)
            assertTrue(late.state.observationMemory.battery?.revoked == true)
            val midpoint = advanced(
                step(late.state, sample(moment = at(23), battery = battery(10.0, at(15))), policy),
            )
            assertNull(midpoint.intent.publishedBatteryPercent)
            val restored = advanced(
                step(midpoint.state, sample(moment = at(24), battery = battery(40.0, at(24))), policy),
            )
            assertEquals(40.0, restored.intent.publishedBatteryPercent)
        }
    }

    @Test
    fun lateRevocationDoesNotRestoreOlderPrecipitation() {
        val policy = openPolicy()
        val current = advanced(
            step(
                null,
                sample(
                    moment = at(10),
                    battery = battery(80.0, at(10)),
                    precipitation = battery(20.0, at(10)),
                ),
                policy,
            ),
        )
        val revoked = advanced(
            step(
                current.state,
                sample(
                    moment = at(20),
                    battery = battery(80.0, at(10)),
                    precipitation = revocation(ObservationStatus.ERROR, at(20)),
                ),
                policy,
            ),
        )
        assertNull(revoked.intent.publishedPrecipitation)
        assertEquals(80.0, revoked.intent.publishedBatteryPercent)
        val late = advanced(
            step(
                revoked.state,
                sample(
                    moment = at(22),
                    battery = battery(80.0, at(10)),
                    precipitation = revocation(ObservationStatus.UNAVAILABLE, at(12)),
                ),
                policy,
            ),
        )
        assertEquals(at(20), late.state.observationMemory.precipitation?.observedAt)
        val midpoint = advanced(
            step(
                late.state,
                sample(
                    moment = at(23),
                    battery = battery(80.0, at(10)),
                    precipitation = battery(5.0, at(15)),
                ),
                policy,
            ),
        )
        assertNull(midpoint.intent.publishedPrecipitation)
        assertEquals(80.0, midpoint.intent.publishedBatteryPercent)
    }

    @Test
    fun lateRevocationDoesNotRestoreOlderAxes() {
        val policy = openPolicy()
        val current = advanced(
            step(
                null,
                sample(
                    moment = at(10),
                    battery = battery(80.0, at(10)),
                    charging = reading(true, "flag", observedAt = at(10)),
                    alert = reading(true, "flag", observedAt = at(10)),
                    activity = reading("EXERCISE", "token", observedAt = at(10)),
                    light = reading("NIGHT", "token", observedAt = at(10)),
                    connectivity = reading("OFFLINE", "token", observedAt = at(10)),
                    userMode = reading("WORK", "token", observedAt = at(10)),
                ),
                policy,
            ),
        )
        assertEquals(PowerAxis.CHARGING, current.state.power)
        assertEquals(WeatherAxis.ALERT, current.state.weather)
        assertEquals(ActivityAxis.EXERCISE, current.state.activity)
        assertEquals(LightAxis.NIGHT, current.state.light)
        assertEquals(ConnectivityAxis.OFFLINE, current.state.connectivity)
        assertEquals(UserModeAxis.WORK, current.state.userMode)
        val revoked = advanced(
            step(
                current.state,
                sample(
                    moment = at(20),
                    battery = battery(80.0, at(10)),
                    charging = reading(null, "flag", status = ObservationStatus.DENIED, observedAt = at(20)),
                    alert = reading(null, "flag", status = ObservationStatus.ERROR, observedAt = at(20)),
                    activity = reading(null, "token", status = ObservationStatus.UNAVAILABLE, observedAt = at(20)),
                    light = reading(null, "token", status = ObservationStatus.DENIED, observedAt = at(20)),
                    connectivity = reading(null, "token", status = ObservationStatus.ERROR, observedAt = at(20)),
                    userMode = reading(null, "token", status = ObservationStatus.UNAVAILABLE, observedAt = at(20)),
                ),
                policy,
            ),
        )
        val late = advanced(
            step(
                revoked.state,
                sample(
                    moment = at(22),
                    battery = battery(80.0, at(10)),
                    charging = reading(null, "flag", status = ObservationStatus.DENIED, observedAt = at(12)),
                    alert = reading(null, "flag", status = ObservationStatus.ERROR, observedAt = at(12)),
                    activity = reading(null, "token", status = ObservationStatus.UNAVAILABLE, observedAt = at(12)),
                    light = reading(null, "token", status = ObservationStatus.DENIED, observedAt = at(12)),
                    connectivity = reading(null, "token", status = ObservationStatus.ERROR, observedAt = at(12)),
                    userMode = reading(null, "token", status = ObservationStatus.UNAVAILABLE, observedAt = at(12)),
                ),
                policy,
            ),
        )
        assertEquals(at(20), late.state.observationMemory.charging?.observedAt)
        assertEquals(at(20), late.state.observationMemory.alert?.observedAt)
        assertEquals(at(20), late.state.observationMemory.activity?.observedAt)
        assertEquals(at(20), late.state.observationMemory.light?.observedAt)
        assertEquals(at(20), late.state.observationMemory.connectivity?.observedAt)
        assertEquals(at(20), late.state.observationMemory.userMode?.observedAt)
        val midpoint = advanced(
            step(
                late.state,
                sample(
                    moment = at(23),
                    battery = battery(80.0, at(10)),
                    charging = reading(false, "flag", observedAt = at(15)),
                    alert = reading(true, "flag", observedAt = at(15)),
                    activity = reading("REST", "token", observedAt = at(15)),
                    light = reading("DAY", "token", observedAt = at(15)),
                    connectivity = reading("ONLINE", "token", observedAt = at(15)),
                    userMode = reading("DEFAULT", "token", observedAt = at(15)),
                ),
                policy,
            ),
        )
        assertEquals(PowerAxis.CHARGING, midpoint.state.power)
        assertEquals(WeatherAxis.UNKNOWN, midpoint.state.weather)
        assertEquals(ActivityAxis.UNKNOWN, midpoint.state.activity)
        assertEquals(LightAxis.NIGHT, midpoint.state.light)
        assertEquals(ConnectivityAxis.OFFLINE, midpoint.state.connectivity)
        assertEquals(UserModeAxis.WORK, midpoint.state.userMode)
        val later = advanced(
            step(
                midpoint.state,
                sample(
                    moment = at(24),
                    battery = battery(80.0, at(10)),
                    charging = reading(false, "flag", observedAt = at(24)),
                    light = reading("DAY", "token", observedAt = at(24)),
                    connectivity = reading("ONLINE", "token", observedAt = at(24)),
                    userMode = reading("SLEEP", "token", observedAt = at(24)),
                ),
                policy,
            ),
        )
        assertEquals(PowerAxis.NORMAL, later.state.power)
        assertEquals(LightAxis.DAY, later.state.light)
        assertEquals(ConnectivityAxis.ONLINE, later.state.connectivity)
        assertEquals(UserModeAxis.SLEEP, later.state.userMode)
    }

    @Test
    fun missingAndFutureRevocationTimesKeepALaterValueReachable() {
        val policy = openPolicy()
        val current = advanced(
            step(null, sample(moment = at(10), battery = battery(80.0, at(10))), policy),
        )
        val revoked = advanced(
            step(
                current.state,
                sample(moment = at(20), battery = revocation(ObservationStatus.DENIED, at(20))),
                policy,
            ),
        )
        val missingTime = advanced(
            step(
                revoked.state,
                sample(
                    moment = at(22),
                    battery = revocation(ObservationStatus.ERROR, at(20)).copy(observedAt = null),
                ),
                policy,
            ),
        )
        assertTrue(!missingTime.state.observationMemory.battery?.observedAt!!.isBefore(at(20)))
        val duringGap = advanced(
            step(missingTime.state, sample(moment = at(23), battery = battery(10.0, at(15))), policy),
        )
        assertNull(duringGap.intent.publishedBatteryPercent)
        val futureStamp = advanced(
            step(
                duringGap.state,
                sample(moment = at(24), battery = revocation(ObservationStatus.UNAVAILABLE, at(100))),
                policy,
            ),
        )
        assertTrue(!futureStamp.state.observationMemory.battery?.observedAt!!.isAfter(at(24)))
        val later = advanced(
            step(futureStamp.state, sample(moment = at(25), battery = battery(40.0, at(25))), policy),
        )
        assertEquals(40.0, later.intent.publishedBatteryPercent)
    }

    @Test
    fun higherRevisionCanStillPassAnOlderTimeAfterRevocation() {
        val policy = openPolicy()
        val current = advanced(
            step(
                null,
                sample(moment = at(10), battery = battery(80.0, at(10)), batteryRevision = 2L),
                policy,
            ),
        )
        val revoked = advanced(
            step(
                current.state,
                sample(
                    moment = at(20),
                    battery = revocation(ObservationStatus.DENIED, at(20)),
                    batteryRevision = 3L,
                ),
                policy,
            ),
        )
        val lower = advanced(
            step(
                revoked.state,
                sample(moment = at(21), battery = battery(11.0, at(21)), batteryRevision = 1L),
                policy,
            ),
        )
        assertNull(lower.intent.publishedBatteryPercent)
        val olderHigher = advanced(
            step(
                lower.state,
                sample(moment = at(22), battery = battery(33.0, at(12)), batteryRevision = 4L),
                policy,
            ),
        )
        assertEquals(33.0, olderHigher.intent.publishedBatteryPercent)
    }

    @Test
    fun olderReleaseDoesNotClearProtectionRaisedByARejectedPolicy() {
        val policy = openPolicy()
        val bad = PolicyCandidates.documented().copy(powerEnterPercent = Double.NaN)
        val current = advanced(
            step(
                null,
                sample(moment = at(10), battery = battery(10.0, at(10), expiresAt = at(400))),
                policy,
            ),
        )
        assertTrue(current.intent.graphicsPowerLimited)
        val raised = assertIs<StepResult.PolicyRejected>(
            step(
                current.state,
                sample(moment = at(30), motionReduction = true, ambientDisplay = true),
                bad,
            ),
        )
        assertEquals(at(10), raised.state?.processedAt)
        assertEquals(QualityCandidate.AOD, raised.failSafe?.quality)
        assertFalse(raised.failSafe?.motionAllowed == true)
        assertTrue(raised.failSafe?.graphicsPowerLimited == true)
        val late = advanced(
            step(
                raised.state,
                sample(
                    moment = at(20),
                    battery = battery(10.0, at(10), expiresAt = at(400)),
                    motionReduction = false,
                    ambientDisplay = false,
                ),
                policy,
            ),
        )
        assertEquals(QualityCandidate.AOD, late.intent.quality)
        assertFalse(late.intent.motionAllowed)
        assertTrue(late.intent.graphicsPowerLimited)
        assertEquals(10.0, late.intent.publishedBatteryPercent)
        val cleared = advanced(
            step(
                late.state,
                sample(
                    moment = at(40),
                    battery = battery(80.0, at(40), expiresAt = at(400)),
                    motionReduction = false,
                    ambientDisplay = false,
                ),
                policy,
            ),
        )
        assertEquals(QualityCandidate.BALANCED, cleared.intent.quality)
        assertTrue(cleared.intent.motionAllowed)
        assertFalse(cleared.intent.graphicsPowerLimited)
        assertEquals(80.0, cleared.intent.publishedBatteryPercent)
    }

    @Test
    fun olderSampleDoesNotRepublishANumberWithdrawnByARejectedPolicy() {
        val policy = openPolicy()
        val bad = PolicyCandidates.documented().copy(powerEnterPercent = Double.NaN)
        val current = advanced(
            step(
                null,
                sample(moment = at(10), battery = battery(80.0, at(10), expiresAt = at(25))),
                policy,
            ),
        )
        val withdrawn = assertIs<StepResult.PolicyRejected>(
            step(current.state, sample(moment = at(30), battery = battery(4.0, at(30), expiresAt = at(90))), bad),
        )
        assertEquals(at(10), withdrawn.state?.processedAt)
        assertNull(withdrawn.failSafe?.publishedBatteryPercent)
        val late = advanced(
            step(withdrawn.state, sample(moment = at(20), battery = battery(70.0, at(18), expiresAt = at(90))), policy),
        )
        assertNull(late.intent.publishedBatteryPercent)
        val restored = advanced(
            step(late.state, sample(moment = at(40), battery = battery(60.0, at(40), expiresAt = at(90))), policy),
        )
        assertEquals(60.0, restored.intent.publishedBatteryPercent)
    }

    @Test
    fun ceilingNoOpDoesNotLetAnEarlierResyncBypassClockOrder() {
        val policy = openPolicy()
        val current = advanced(
            step(
                null,
                sample(
                    moment = at(10),
                    battery = battery(10.0, at(10), expiresAt = at(200)),
                    precipitation = battery(20.0, at(10), expiresAt = at(200)),
                    motionReduction = true,
                    ambientDisplay = true,
                ),
                policy,
            ),
        )
        val maxed = current.state.copy(revision = Long.MAX_VALUE)
        val noop = assertIs<StepResult.LimitReached>(
            step(maxed, sample(moment = at(100), motionReduction = true, ambientDisplay = true), policy),
        )
        assertEquals(at(100), noop.state.processedAt)
        assertEquals(10.0, noop.state.emission.publishedBatteryPercent)
        assertEquals(20.0, noop.state.emission.publishedPrecipitation)
        assertEquals(Long.MAX_VALUE, noop.state.revision)
        assertFalse(noop.state.emission.motionAllowed)
        assertEquals(QualityCandidate.AOD, noop.state.emission.quality)
        assertTrue(noop.state.emission.graphicsPowerLimited)
        val early = held(
            step(
                noop.state,
                sample(
                    moment = at(50),
                    battery = battery(80.0, at(50), expiresAt = at(90)),
                    precipitation = battery(90.0, at(50), expiresAt = at(90)),
                    motionReduction = false,
                    ambientDisplay = false,
                    resync = true,
                ),
                policy,
            ),
        )
        assertEquals(at(100), early.processedAt)
        assertEquals(10.0, early.emission.publishedBatteryPercent)
        assertEquals(20.0, early.emission.publishedPrecipitation)
        assertFalse(early.emission.motionAllowed)
        assertEquals(QualityCandidate.AOD, early.emission.quality)
        assertTrue(early.emission.graphicsPowerLimited)
        assertEquals(Long.MAX_VALUE, early.revision)
        val resynced = advanced(
            step(
                early,
                sample(
                    moment = at(120),
                    battery = battery(80.0, at(120), expiresAt = at(400)),
                    precipitation = battery(30.0, at(120), expiresAt = at(400)),
                    motionReduction = true,
                    ambientDisplay = true,
                    resync = true,
                ),
                policy,
            ),
        )
        assertEquals(80.0, resynced.intent.publishedBatteryPercent)
        assertEquals(30.0, resynced.intent.publishedPrecipitation)
        assertTrue(resynced.intent.graphicsPowerLimited)
        assertEquals(QualityCandidate.AOD, resynced.intent.quality)
        assertEquals(Long.MAX_VALUE, resynced.state.revision)
        val expired = advanced(
            step(
                noop.state,
                sample(moment = at(200), motionReduction = true, ambientDisplay = true),
                policy,
            ),
        )
        assertNull(expired.intent.publishedBatteryPercent)
        assertNull(expired.intent.publishedPrecipitation)
        assertTrue(expired.intent.graphicsPowerLimited)
        assertEquals(QualityCandidate.AOD, expired.intent.quality)
        val denied = advanced(
            step(
                maxed,
                sample(
                    moment = at(130),
                    battery = revocation(ObservationStatus.DENIED, at(130)),
                    precipitation = revocation(ObservationStatus.ERROR, at(130)),
                    motionReduction = true,
                    ambientDisplay = true,
                ),
                policy,
            ),
        )
        assertNull(denied.intent.publishedBatteryPercent)
        assertNull(denied.intent.publishedPrecipitation)
        assertTrue(denied.intent.graphicsPowerLimited)
        assertFalse(denied.intent.motionAllowed)
    }

    @Test
    fun protectionArrivingBeforeTheSessionOpenerDoesNotClearAndMustBeResent() {
        val policy = openPolicy()
        val base = advanced(
            step(
                null,
                sample(battery = battery(10.0, at(0)), motionReduction = true, ambientDisplay = true),
                policy,
            ),
        )
        val opener = advanced(
            step(
                base.state,
                sample(moment = at(2), battery = battery(10.0, at(2)), ambientDisplay = true),
                policy,
                Long.MAX_VALUE,
                0L,
                true,
            ),
        )
        assertTrue(opener.deliverySessionOpened)
        assertEquals(1L, opener.deliveryEpoch)
        val follow = advanced(
            step(
                opener.state,
                sample(
                    moment = at(3),
                    battery = battery(10.0, at(3)),
                    motionReduction = true,
                    ambientDisplay = true,
                ),
                policy,
                opener.deliverySequence,
                opener.deliveryEpoch,
                false,
            ),
        )
        assertFalse(follow.deliverySessionOpened)
        assertTrue(follow.deliverySequence > opener.deliverySequence)
        val oldRelease = advanced(
            step(base.state, sample(moment = at(4), battery = battery(80.0, at(4))), policy, 1L, 0L, false),
        )
        val consumer = ProtectionConsumer()
        consumer.push(base)
        consumer.push(follow)
        assertProtection(consumer, motion = true, ambient = true, graphics = true)
        consumer.push(opener)
        assertProtection(consumer, motion = false, ambient = true, graphics = true)
        consumer.push(follow)
        assertProtection(consumer, motion = true, ambient = true, graphics = true)
        consumer.push(oldRelease)
        assertProtection(consumer, motion = true, ambient = true, graphics = true)
        val saturated = advanced(
            step(follow.state, sample(moment = at(5)), policy, Long.MAX_VALUE, Long.MAX_VALUE, true),
        )
        assertEquals(Long.MAX_VALUE, saturated.deliveryEpoch)
        assertFalse(saturated.deliverySessionOpened)
        consumer.push(saturated)
        assertProtection(consumer, motion = true, ambient = true, graphics = true)
    }

    private fun battery(value: Double, observedAt: java.time.Instant, expiresAt: java.time.Instant = at(3600)) =
        reading(value, "percent", expiresAt = expiresAt, observedAt = observedAt)

    private fun revocation(status: ObservationStatus, observedAt: java.time.Instant): Observation<Double> =
        reading(null, "percent", status = status, observedAt = observedAt)

    private fun advanced(result: StepResult): StepResult.Advanced = assertIs(result)

    private fun held(result: StepResult): MachineState {
        return when (result) {
            is StepResult.Advanced -> result.state
            is StepResult.LimitReached -> result.state
            is StepResult.PolicyRejected -> error("policy")
        }
    }

    private fun assertProtection(consumer: ProtectionConsumer, motion: Boolean, ambient: Boolean, graphics: Boolean) {
        assertEquals(motion, consumer.motionReduction)
        assertEquals(ambient, consumer.ambientDisplay)
        assertEquals(graphics, consumer.graphicsPowerLimited)
    }

    private val revocationStatuses = listOf(
        ObservationStatus.DENIED,
        ObservationStatus.ERROR,
        ObservationStatus.UNAVAILABLE,
    )
}
