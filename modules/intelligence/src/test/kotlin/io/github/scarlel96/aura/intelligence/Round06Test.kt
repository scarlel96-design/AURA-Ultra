package io.github.scarlel96.aura.intelligence

import io.github.scarlel96.aura.domain.Freshness
import io.github.scarlel96.aura.domain.ObservationStatus
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNull
import kotlin.test.assertTrue

/**
 * AUD-R02-01, AUD-R02-05, AUD-R02-08.
 * 수정 전에는 권한 사유가 TTL에 덮이고, 비정상 단위와 NaN 경계가 통과한다.
 */
class Round06Test {
    @Test
    fun permissionStatusStaysDistinctFromTtl() {
        val cases = listOf(
            ObservationStatus.DENIED to UnusableReason.DENIED,
            ObservationStatus.ERROR to UnusableReason.ERROR,
            ObservationStatus.UNAVAILABLE to UnusableReason.UNAVAILABLE,
        )
        val windows = listOf(
            null to Freshness.UNDECLARED,
            origin to Freshness.EXPIRED,
            origin.plusSeconds(60) to Freshness.FRESH,
        )
        for ((status, reason) in cases) {
            for ((expiresAt, freshness) in windows) {
                val observation = reading<Double>(
                    null,
                    "percent",
                    status = status,
                    expiresAt = expiresAt,
                )
                val channel = assertIs<Channel.Unusable>(
                    gateDouble(observation, origin, "percent", 0.0, 100.0),
                    "$status $freshness",
                )
                assertEquals(reason, channel.reason, "$status $freshness")
                assertEquals(freshness, channel.freshness, "$status $freshness")
                val stepped = assertIs<StepResult.Advanced>(
                    step(null, sample(battery = observation), openPolicy()),
                )
                val codes = stepped.intent.reasonCodes
                assertTrue(codes.contains(reason.toReasonCode()), "$status $freshness $codes")
                assertNull(stepped.intent.publishedBatteryPercent, "$status $freshness")
                when (freshness) {
                    Freshness.UNDECLARED -> assertTrue(codes.contains(ReasonCode.UNDECLARED_IGNORED), codes.toString())
                    Freshness.EXPIRED -> assertTrue(codes.contains(ReasonCode.STALE_IGNORED), codes.toString())
                    Freshness.FRESH -> {
                        assertFalse(codes.contains(ReasonCode.UNDECLARED_IGNORED), codes.toString())
                        assertFalse(codes.contains(ReasonCode.STALE_IGNORED), codes.toString())
                    }
                }
            }
        }
    }

    @Test
    fun abnormalUnitTokensAreRejected() {
        val tokens = listOf(" percent", "percent ", "per cent", "percent\u0000", "per\u0000cent", "percent\n", "\u0007flag")
        for (token in tokens) {
            val policy = PolicyCandidates.documented().copy(percentUnit = token)
            assertTrue(policy.issues().any { it.contains("unit tokens") }, token)
            val rejected = assertIs<StepResult.PolicyRejected>(
                step(null, sample(battery = reading(0.0, token)), policy),
                token,
            )
            assertNull(rejected.deliveredIntent())
        }
        assertEquals(emptyList(), PolicyCandidates.documented().issues())
        val zero = assertIs<Channel.Fresh<Double>>(gateDouble(reading(0.0, "percent"), origin, "percent", 0.0, 100.0))
        assertEquals(0.0, zero.value)
    }

    @Test
    fun nonFiniteAndInvertedBoundsAreRejected() {
        val sample = reading(999.0, "percent")
        val nanBounds = assertIs<Channel.Unusable>(gateDouble(sample, origin, "percent", Double.NaN, Double.NaN))
        assertEquals(UnusableReason.REJECTED, nanBounds.reason)
        val infiniteBounds = assertIs<Channel.Unusable>(
            gateDouble(sample, origin, "percent", Double.NEGATIVE_INFINITY, Double.POSITIVE_INFINITY),
        )
        assertEquals(UnusableReason.REJECTED, infiniteBounds.reason)
        val inverted = assertIs<Channel.Unusable>(gateDouble(reading(50.0, "percent"), origin, "percent", 100.0, 0.0))
        assertEquals(UnusableReason.REJECTED, inverted.reason)
        assertEquals(0.0, (gateDouble(reading(0.0, "percent"), origin, "percent", 0.0, 100.0) as Channel.Fresh).value)
        assertEquals(100.0, (gateDouble(reading(100.0, "percent"), origin, "percent", 0.0, 100.0) as Channel.Fresh).value)
        assertEquals(
            UnusableReason.REJECTED,
            (gateDouble(reading(Double.NaN, "percent"), origin, "percent", 0.0, 100.0) as Channel.Unusable).reason,
        )
        assertEquals(
            UnusableReason.REJECTED,
            (gateDouble(reading(Double.POSITIVE_INFINITY, "percent"), origin, "percent", 0.0, 100.0) as Channel.Unusable).reason,
        )
    }
}
