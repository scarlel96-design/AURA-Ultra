package io.github.scarlel96.aura.domain

import java.time.Instant
import java.time.ZoneId
import java.time.ZoneOffset
import java.time.ZonedDateTime
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertSame

class FreshnessTest {
    private val expiry = Instant.parse("2026-11-27T01:00:00Z")

    @Test
    fun boundaryIsExpiredAtOrAfter() {
        assertEquals(Freshness.FRESH, freshnessOf(expiry, expiry.minusNanos(1)))
        assertEquals(Freshness.EXPIRED, freshnessOf(expiry, expiry))
        assertEquals(Freshness.EXPIRED, freshnessOf(expiry, expiry.plusNanos(1)))
        assertEquals(Freshness.UNDECLARED, freshnessOf(null, expiry))
    }

    @Test
    fun instantMaxBoundary() {
        assertEquals(Freshness.FRESH, freshnessOf(Instant.MAX, Instant.MAX.minusNanos(1)))
        assertEquals(Freshness.EXPIRED, freshnessOf(Instant.MAX, Instant.MAX))
    }

    @Test
    fun sameInstantFromDifferentZonesHasOneFreshness() {
        val seoul = ZonedDateTime.of(2026, 11, 27, 9, 0, 0, 0, ZoneId.of("Asia/Seoul")).toInstant()
        val utc = ZonedDateTime.of(2026, 11, 27, 0, 0, 0, 0, ZoneOffset.UTC).toInstant()
        assertEquals(utc, seoul)
        val observation = observation(value = 1, expiresAt = seoul.plusSeconds(60))
        val derived = deriveStatus(observation, utc.plusSeconds(30))
        assertIs<StatusDerivation.Unchanged<Int>>(derived)
        assertEquals(Freshness.FRESH, derived.freshness)
    }

    @Test
    fun callerReferenceTimeDecidesFreshnessWithoutAClock() {
        val observation = observation(value = 4, expiresAt = expiry)
        val early = deriveStatus(observation, expiry.minusSeconds(1))
        val late = deriveStatus(observation, expiry)
        assertIs<StatusDerivation.Unchanged<Int>>(early)
        assertIs<StatusDerivation.DegradedToStale<Int>>(late)
        assertEquals(ObservationStatus.VALID, observation.status)
    }

    @Test
    fun expiredValidBecomesStaleCopyAndKeepsPayload() {
        val original = observation(
            value = 0,
            unit = "mm",
            observedAt = Instant.parse("2026-11-27T00:00:00Z"),
            receivedAt = Instant.parse("2026-11-27T00:00:02Z"),
            expiresAt = expiry,
            kind = ObservationKind.FORECAST,
        )
        val derived = deriveStatus(original, expiry)
        assertIs<StatusDerivation.DegradedToStale<Int>>(derived)
        assertEquals(ObservationStatus.VALID, original.status)
        assertEquals(ObservationStatus.STALE, derived.observation.status)
        assertEquals(0, derived.observation.value)
        assertEquals(original.unit, derived.observation.unit)
        assertEquals(original.source, derived.observation.source)
        assertEquals(original.observedAt, derived.observation.observedAt)
        assertEquals(original.receivedAt, derived.observation.receivedAt)
        assertEquals(original.expiresAt, derived.observation.expiresAt)
        assertEquals(ObservationKind.FORECAST, derived.observation.kind)
    }

    @Test
    fun undeclaredExpiryDoesNotBecomeStaleOrImmortalClaim() {
        val observation = observation(value = 1, expiresAt = null, status = ObservationStatus.VALID)
        val derived = deriveStatus(observation, expiry)
        assertIs<StatusDerivation.Unchanged<Int>>(derived)
        assertSame(observation, derived.observation)
        assertEquals(Freshness.UNDECLARED, derived.freshness)
        assertEquals(ObservationStatus.VALID, derived.observation.status)
    }

    @Test
    fun staleIsNotPromotedWhenStillInsideWindow() {
        val observation = observation(value = 2, status = ObservationStatus.STALE, expiresAt = expiry)
        val derived = deriveStatus(observation, expiry.minusSeconds(10))
        assertIs<StatusDerivation.Unchanged<Int>>(derived)
        assertSame(observation, derived.observation)
        assertEquals(Freshness.FRESH, derived.freshness)
        assertEquals(ObservationStatus.STALE, derived.observation.status)
    }

    @Test
    fun errorDeniedAndUnavailableAreNotRewrittenWhenExpired() {
        val error = observation<Int>(value = null, unit = "", status = ObservationStatus.ERROR, expiresAt = expiry)
        val denied = observation<Int>(value = null, unit = "", status = ObservationStatus.DENIED, expiresAt = expiry)
        val missing = observation<Int>(value = null, unit = "", status = ObservationStatus.UNAVAILABLE, expiresAt = expiry)
        listOf(error, denied, missing).forEach { observation ->
            val derived = deriveStatus(observation, expiry.plusSeconds(5))
            assertIs<StatusDerivation.Unchanged<Int>>(derived)
            assertSame(observation, derived.observation)
            assertEquals(Freshness.EXPIRED, derived.freshness)
        }
        assertEquals(ObservationStatus.ERROR, error.status)
        assertEquals(ObservationStatus.DENIED, denied.status)
        assertEquals(ObservationStatus.UNAVAILABLE, missing.status)
    }

    @Test
    fun freshDeniedDoesNotBecomeValid() {
        val denied = observation<Int>(value = null, unit = "", status = ObservationStatus.DENIED, expiresAt = expiry)
        val derived = deriveStatus(denied, expiry.minusSeconds(1))
        assertIs<StatusDerivation.Unchanged<Int>>(derived)
        assertEquals(Freshness.FRESH, derived.freshness)
        assertEquals(ObservationStatus.DENIED, derived.observation.status)
        assertIs<ClassifiedValue.Denied>(derived.observation.classifiedValue())
    }

    @Test
    fun structurallyInvalidInputIsNotDegraded() {
        val broken = observation(value = 5, unit = "count", status = ObservationStatus.ERROR, expiresAt = expiry)
        val derived = deriveStatus(broken, expiry.plusSeconds(1))
        assertIs<StatusDerivation.Rejected<Int>>(derived)
        assertSame(broken, derived.observation)
        assertEquals(listOf(IssueCode.VALUE_FORBIDDEN), derived.issues.codes())
        assertEquals(5, broken.value)
        assertEquals(ObservationStatus.ERROR, broken.status)
        val items = mutableListOf(1)
        val classified = observation(items, unit = "count").classifiedValue()
        assertIs<ClassifiedValue.Inconsistent>(classified)
        items[0] = 9
        assertIs<ClassifiedValue.Inconsistent>(observation(items, unit = "count").classifiedValue())
        val mutableDerived = deriveStatus(observation(items, unit = "count"), expiry)
        assertIs<StatusDerivation.Rejected<MutableList<Int>>>(mutableDerived)
        assertEquals(listOf(IssueCode.UNSUPPORTED_PAYLOAD), mutableDerived.issues.codes())
    }

    @Test
    fun lateArrivalBeforeObservedExpiryRemainsValid() {
        val observedAt = Instant.parse("2026-11-27T00:00:00Z")
        val receivedAt = Instant.parse("2026-11-27T00:30:00Z")
        val observation = observation(
            value = 1,
            observedAt = observedAt,
            receivedAt = receivedAt,
            expiresAt = expiry,
        )
        val derived = deriveStatus(observation, receivedAt)
        assertIs<StatusDerivation.Unchanged<Int>>(derived)
        assertEquals(Freshness.FRESH, derived.freshness)
    }
}
