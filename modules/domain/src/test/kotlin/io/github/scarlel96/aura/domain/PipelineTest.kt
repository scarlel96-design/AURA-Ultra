package io.github.scarlel96.aura.domain

import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertTrue

class PipelineTest {
    @Test
    fun zeroReadingExpiresWithoutBecomingMissing() {
        val source = acceptedSource("fixture.power")
        val key = acceptedKey(source, "battery.percent")
        val observedAt = Instant.parse("2026-11-27T00:00:00Z")
        val receivedAt = observedAt.plusSeconds(2)
        val expiresAt = observedAt.plusSeconds(60)
        val reading = observation(
            value = 0,
            unit = "percent",
            source = source,
            observedAt = observedAt,
            receivedAt = receivedAt,
            expiresAt = expiresAt,
            kind = ObservationKind.OBSERVED,
        )
        val accepted = applyRevision(null, key, 11, reading, ObservationConstraints(expectedUnit = "percent"))
        assertEquals(RevisionOutcome.ACCEPTED, accepted.outcome)
        val stored = accepted.cursor ?: error("cursor")
        val late = deriveStatus(stored.observation, expiresAt)
        assertIs<StatusDerivation.DegradedToStale<Int>>(late)
        val classified = late.observation.classifiedValue()
        assertIs<ClassifiedValue.Reading<Int>>(classified)
        assertEquals(0, classified.value)
        assertEquals(ObservationStatus.STALE, classified.status)
    }

    @Test
    fun deniedStreamRejectsALaterZeroForgery() {
        val source = acceptedSource("fixture.health")
        val key = acceptedKey(source, "heart.rate")
        val denied = observation<Int>(
            value = null,
            unit = "",
            source = source,
            status = ObservationStatus.DENIED,
            kind = ObservationKind.OBSERVED,
        )
        val current = applyRevision(null, key, 2, denied).cursor
        val forged = observation(value = 0, unit = "bpm", source = source, status = ObservationStatus.VALID)
        val decision = applyRevision(current, key, 2, forged)
        assertEquals(RevisionOutcome.DUPLICATE_CONFLICT, decision.outcome)
        assertIs<ClassifiedValue.Denied>(decision.cursor?.observation?.classifiedValue())
        val older = applyRevision(current, key, 1, forged)
        assertEquals(RevisionOutcome.SUPERSEDED_REJECTED, older.outcome)
        assertIs<ClassifiedValue.Denied>(older.cursor?.observation?.classifiedValue())
    }

    @Test
    fun corruptUnitDoesNotReplaceStoredReading() {
        val source = acceptedSource("fixture.weather")
        val key = acceptedKey(source, "rain.mm")
        val reference = Instant.parse("2026-11-27T00:10:00Z")
        val stored = observation(
            value = 0,
            unit = "mm",
            source = source,
            expiresAt = reference.plusSeconds(60),
        )
        val current = applyRevision(null, key, 4, stored, ObservationConstraints(expectedUnit = "mm"))
        assertEquals(RevisionOutcome.ACCEPTED, current.outcome)
        listOf("mm Hg", "mm\u0000").forEach { unit ->
            val bad = observation(value = 9, unit = unit, source = source)
            val decision = applyRevision(
                current.cursor,
                key,
                5,
                bad,
                ObservationConstraints(expectedUnit = unit),
            )
            assertEquals(RevisionOutcome.INVALID_OBSERVATION, decision.outcome)
            assertEquals(0, decision.cursor?.observation?.value)
            assertEquals(ObservationStatus.VALID, decision.cursor?.observation?.status)
            val derived = deriveStatus(bad, reference)
            assertIs<StatusDerivation.Rejected<Int>>(derived)
            assertEquals(9, bad.value)
            assertEquals(ObservationStatus.VALID, bad.status)
        }
    }

    @Test
    fun deniedErrorAndStaleAreNotPresentedAsFreshValidReadings() {
        val source = acceptedSource("fixture.health")
        val key = acceptedKey(source, "heart.rate")
        val expiry = Instant.parse("2026-11-27T01:00:00Z")
        val inside = expiry.minusSeconds(10)
        val denied = observation<Int>(
            value = null,
            unit = "",
            source = source,
            status = ObservationStatus.DENIED,
            expiresAt = expiry,
        )
        val deniedDecision = applyRevision(null, key, 1, denied)
        assertEquals(RevisionOutcome.ACCEPTED, deniedDecision.outcome)
        val deniedDerived = deriveStatus(deniedDecision.cursor?.observation ?: error("cursor"), inside)
        assertIs<StatusDerivation.Unchanged<Int>>(deniedDerived)
        assertEquals(Freshness.FRESH, deniedDerived.freshness)
        assertEquals(ObservationStatus.DENIED, deniedDerived.observation.status)
        assertIs<ClassifiedValue.Denied>(deniedDerived.observation.classifiedValue())

        val error = observation<Int>(
            value = null,
            unit = "",
            source = source,
            status = ObservationStatus.ERROR,
            expiresAt = expiry,
        )
        val errorDecision = applyRevision(deniedDecision.cursor, key, 2, error)
        assertEquals(RevisionOutcome.ACCEPTED, errorDecision.outcome)
        val errorDerived = deriveStatus(errorDecision.cursor?.observation ?: error("cursor"), expiry.plusSeconds(1))
        assertIs<StatusDerivation.Unchanged<Int>>(errorDerived)
        assertEquals(Freshness.EXPIRED, errorDerived.freshness)
        assertEquals(ObservationStatus.ERROR, errorDerived.observation.status)
        assertIs<ClassifiedValue.Failed>(errorDerived.observation.classifiedValue())

        val stale = observation(
            value = 0,
            unit = "bpm",
            source = source,
            status = ObservationStatus.STALE,
            expiresAt = expiry,
        )
        val staleDecision = applyRevision(errorDecision.cursor, key, 3, stale)
        assertEquals(RevisionOutcome.ACCEPTED, staleDecision.outcome)
        val staleDerived = deriveStatus(staleDecision.cursor?.observation ?: error("cursor"), inside)
        assertIs<StatusDerivation.Unchanged<Int>>(staleDerived)
        assertEquals(Freshness.FRESH, staleDerived.freshness)
        assertEquals(ObservationStatus.STALE, staleDerived.observation.status)
        val staleClassed = staleDerived.observation.classifiedValue()
        assertIs<ClassifiedValue.Reading<Int>>(staleClassed)
        assertEquals(ObservationStatus.STALE, staleClassed.status)
        assertEquals(0, staleClassed.value)

        val forged = observation(value = 0, unit = "bpm", source = source, status = ObservationStatus.ERROR)
        val rejected = applyRevision(staleDecision.cursor, key, 4, forged)
        assertEquals(RevisionOutcome.INVALID_OBSERVATION, rejected.outcome)
        assertEquals(ObservationStatus.STALE, rejected.cursor?.observation?.status)
        assertEquals(0, rejected.cursor?.observation?.value)
        assertIs<ClassifiedValue.Reading<Int>>(rejected.cursor?.observation?.classifiedValue())
    }

    @Test
    fun undeclaredTtlStaysDistinctFromFresh() {
        val source = acceptedSource("fixture.power")
        val key = acceptedKey(source, "battery.percent")
        val reference = Instant.parse("2026-11-27T00:00:00Z")
        val reading = observation(value = 0, unit = "percent", source = source, expiresAt = null)
        val decision = applyRevision(null, key, 1, reading, ObservationConstraints(expectedUnit = "percent"))
        assertEquals(RevisionOutcome.ACCEPTED, decision.outcome)
        val derived = deriveStatus(decision.cursor?.observation ?: error("cursor"), reference)
        assertIs<StatusDerivation.Unchanged<Int>>(derived)
        assertEquals(Freshness.UNDECLARED, derived.freshness)
        assertEquals(ObservationStatus.VALID, derived.observation.status)
        val classified = derived.observation.classifiedValue()
        assertIs<ClassifiedValue.Reading<Int>>(classified)
        assertEquals(0, classified.value)
        assertTrue(derived.freshness == Freshness.UNDECLARED)
    }
}
