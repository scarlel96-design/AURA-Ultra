package io.github.scarlel96.aura.domain

import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs

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
}
