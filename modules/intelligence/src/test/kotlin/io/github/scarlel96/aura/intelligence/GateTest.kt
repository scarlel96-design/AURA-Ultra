package io.github.scarlel96.aura.intelligence

import io.github.scarlel96.aura.domain.ObservationStatus
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs

class GateTest {
    @Test
    fun absentIsNotZero() {
        assertIs<Channel.Absent>(gateDouble(null, origin, "percent", 0.0, 100.0))
        assertIs<Channel.Absent>(gateFlag(null, origin, "flag"))
        assertIs<Channel.Absent>(gateToken(null, origin, "token") { raw: String -> raw })
    }

    @Test
    fun scaleBoundsAreInclusiveAndAreNotConverted() {
        assertEquals(0.0, (gateDouble(reading(0.0, "percent"), origin, "percent", 0.0, 100.0) as Channel.Fresh).value)
        assertEquals(100.0, (gateDouble(reading(100.0, "percent"), origin, "percent", 0.0, 100.0) as Channel.Fresh).value)
        assertEquals(
            UnusableReason.OUTSIDE_CANDIDATE_SCALE,
            (gateDouble(reading(-0.1, "percent"), origin, "percent", 0.0, 100.0) as Channel.Unusable).reason,
        )
        assertEquals(
            UnusableReason.OUTSIDE_CANDIDATE_SCALE,
            (gateDouble(reading(100.1, "percent"), origin, "percent", 0.0, 100.0) as Channel.Unusable).reason,
        )
        assertEquals(
            UnusableReason.UNIT_UNCHECKED,
            (gateDouble(reading(0.15, "ratio"), origin, "percent", 0.0, 100.0) as Channel.Unusable).reason,
        )
    }

    @Test
    fun expiryBoundaryAndBadStatusStayUnusable() {
        assertIs<Channel.Fresh<Double>>(
            gateDouble(reading(10.0, "percent", expiresAt = origin.plusMillis(1)), origin, "percent", 0.0, 100.0),
        )
        assertEquals(
            UnusableReason.STALE,
            (gateDouble(reading(10.0, "percent", expiresAt = origin), origin, "percent", 0.0, 100.0) as Channel.Unusable).reason,
        )
        assertEquals(
            UnusableReason.STALE,
            (gateDouble(reading(10.0, "percent", status = ObservationStatus.STALE), origin, "percent", 0.0, 100.0) as Channel.Unusable).reason,
        )
        assertEquals(
            UnusableReason.UNDECLARED,
            (gateDouble(reading(10.0, "percent", expiresAt = null), origin, "percent", 0.0, 100.0) as Channel.Unusable).reason,
        )
        assertEquals(
            UnusableReason.DENIED,
            (gateDouble(reading(null, "percent", status = ObservationStatus.DENIED), origin, "percent", 0.0, 100.0) as Channel.Unusable).reason,
        )
        assertEquals(
            UnusableReason.ERROR,
            (gateFlag(reading(null, "flag", status = ObservationStatus.ERROR), origin, "flag") as Channel.Unusable).reason,
        )
        assertEquals(
            UnusableReason.UNAVAILABLE,
            (gateDouble(reading(null, "percent", status = ObservationStatus.UNAVAILABLE), origin, "percent", 0.0, 100.0) as Channel.Unusable).reason,
        )
        assertEquals(
            UnusableReason.REJECTED,
            (gateDouble(reading(Double.NaN, "percent"), origin, "percent", 0.0, 100.0) as Channel.Unusable).reason,
        )
        assertEquals(
            UnusableReason.REJECTED,
            (gateDouble(reading(null, "percent", status = ObservationStatus.VALID), origin, "percent", 0.0, 100.0) as Channel.Unusable).reason,
        )
    }

    @Test
    fun uncheckedTokenIsNotExercise() {
        val channel = gateToken(reading("commute", "token"), origin, "token") { raw: String ->
            if (raw == "EXERCISE") raw else null
        }
        assertEquals(UnusableReason.TOKEN_UNCHECKED, (channel as Channel.Unusable).reason)
    }
}
