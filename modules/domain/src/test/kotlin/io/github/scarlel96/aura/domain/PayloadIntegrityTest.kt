package io.github.scarlel96.aura.domain

import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNull
import kotlin.test.assertSame

class PayloadIntegrityTest {
    private val origin = Instant.parse("2026-11-28T00:00:00Z")

    @Test
    fun mutableListDoesNotReplaceStoredScalarOrChangeDuplicateVerdict() {
        val key = acceptedKey()
        val stored = applyRevision(null, key, 1, sample<Any>(10.0, receivedAt = at(10), observedAt = at(10)))
        val items = mutableListOf("kept")
        val decision = applyRevision(null, key, 1, sample(items, unit = "token", receivedAt = at(20), observedAt = at(20)))
        assertEquals(RevisionOutcome.INVALID_OBSERVATION, decision.outcome)
        assertEquals(listOf(IssueCode.UNSUPPORTED_PAYLOAD), decision.issues.codes())
        assertNull(decision.cursor)
        val injected = applyRevision(
            stored.cursor,
            key,
            2,
            sample(items, unit = "token", receivedAt = at(21), observedAt = at(21)),
        )
        assertEquals(RevisionOutcome.INVALID_OBSERVATION, injected.outcome)
        assertEquals(listOf(IssueCode.UNSUPPORTED_PAYLOAD), injected.issues.codes())
        assertSame(stored.cursor, injected.cursor)
        items[0] = "changed"
        items += "more"
        val replay = applyRevision(stored.cursor, key, 1, sample(10.0, receivedAt = at(30), observedAt = at(10)))
        assertEquals(RevisionOutcome.DUPLICATE, replay.outcome)
        assertSame(stored.cursor, replay.cursor)
        assertEquals(10.0, replay.cursor?.observation?.value)
        val conflict = applyRevision(stored.cursor, key, 1, sample(11.0, receivedAt = at(31), observedAt = at(10)))
        assertEquals(RevisionOutcome.DUPLICATE_CONFLICT, conflict.outcome)
        assertSame(stored.cursor, conflict.cursor)
        assertEquals(10.0, conflict.cursor?.observation?.value)
    }

    @Test
    fun mapSetNestedArrayAndCustomPayloadsAreRejected() {
        val key = acceptedKey()
        val stored = applyRevision(null, key, 1, sample(1, receivedAt = at(10))).cursor
        val nested = mutableListOf(mutableListOf(1))
        val payloads: List<Any> = listOf(
            mutableMapOf("k" to 1),
            mutableSetOf("a"),
            nested,
            arrayOf("a"),
            intArrayOf(1),
            Box(1),
            listOf("fixed"),
        )
        payloads.forEach { payload ->
            val decision = applyRevision<Any>(null, key, 1, sample(payload, unit = "token", receivedAt = at(20)))
            assertEquals(RevisionOutcome.INVALID_OBSERVATION, decision.outcome, payload.javaClass.name)
            assertEquals(listOf(IssueCode.UNSUPPORTED_PAYLOAD), decision.issues.codes(), payload.javaClass.name)
            assertNull(decision.cursor)
        }
        nested[0][0] = 9
        assertEquals(1, stored?.observation?.value)
    }

    @Test
    fun cyclicCustomObjectIsRejectedWithoutBeingWalked() {
        val key = acceptedKey()
        val node = Node()
        node.next = node
        val decision = applyRevision(null, key, 1, sample(node, unit = "token"))
        assertEquals(RevisionOutcome.INVALID_OBSERVATION, decision.outcome)
        assertEquals(listOf(IssueCode.UNSUPPORTED_PAYLOAD), decision.issues.codes())
        assertNull(decision.cursor)
        node.label = "changed"
        assertNull(decision.cursor)
    }

    @Test
    fun classifiedValueDoesNotPublishAMutablePayload() {
        val items = mutableListOf(1)
        val classified = sample(items, unit = "count").classifiedValue()
        assertIs<ClassifiedValue.Inconsistent>(classified)
        items[0] = 9
        assertIs<ClassifiedValue.Inconsistent>(sample(items, unit = "count").classifiedValue())
        val derived = deriveStatus(sample(items, unit = "count"), at(30))
        assertIs<StatusDerivation.Rejected<MutableList<Int>>>(derived)
        assertEquals(listOf(IssueCode.UNSUPPORTED_PAYLOAD), derived.issues.codes())
        assertSame(derived.observation.value, items)

        val readingFailure = assertFailsWith<UnsupportedPayloadException> {
            ClassifiedValue.Reading(mutableListOf(1), ObservationStatus.VALID)
        }
        assertEquals(IssueCode.UNSUPPORTED_PAYLOAD.name, readingFailure.message)
        val reading = ClassifiedValue.Reading<Any>(4, ObservationStatus.VALID)
        assertFailsWith<UnsupportedPayloadException> {
            reading.copy(value = mutableListOf(1))
        }
        assertEquals(4, reading.value)

        val unchangedFailure = assertFailsWith<UnsupportedPayloadException> {
            StatusDerivation.Unchanged(sample(mutableListOf(1), unit = "count"), Freshness.FRESH)
        }
        assertEquals(IssueCode.UNSUPPORTED_PAYLOAD.name, unchangedFailure.message)
        val unchanged = StatusDerivation.Unchanged(sample<Any>(4), Freshness.FRESH)
        assertFailsWith<UnsupportedPayloadException> {
            unchanged.copy(observation = sample(mutableListOf(1), unit = "count"))
        }
        assertEquals(4, unchanged.observation.value)

        val degradedFailure = assertFailsWith<UnsupportedPayloadException> {
            StatusDerivation.DegradedToStale(sample(mutableListOf(1), unit = "count"), Freshness.EXPIRED)
        }
        assertEquals(IssueCode.UNSUPPORTED_PAYLOAD.name, degradedFailure.message)
        val degraded = StatusDerivation.DegradedToStale(sample<Any>(4, status = ObservationStatus.STALE), Freshness.EXPIRED)
        assertFailsWith<UnsupportedPayloadException> {
            degraded.copy(observation = sample(mutableListOf(1), unit = "count"))
        }
        assertEquals(4, degraded.observation.value)
    }

    @Test
    fun directCursorConstructionRejectsMutablePayload() {
        val key = acceptedKey()
        val failure = assertFailsWith<UnsupportedPayloadException> {
            RevisionCursor(key, 1, sample(mutableListOf(1), unit = "count"))
        }
        assertEquals(IssueCode.UNSUPPORTED_PAYLOAD.name, failure.message)
        val accepted = RevisionCursor(key, 1, sample<Any>(4.0))
        assertEquals(4.0, accepted.observation.value)
        assertFailsWith<UnsupportedPayloadException> {
            RevisionCursor(key, 2, sample(mutableMapOf("a" to 1), unit = "token"))
        }
        assertFailsWith<UnsupportedPayloadException> {
            accepted.copy(observation = sample(mutableListOf(1), unit = "count"))
        }
        assertEquals(4.0, accepted.observation.value)
    }

    @Test
    fun scalarZeroNullAndDeniedStayAccepted() {
        val key = acceptedKey()
        val zero = applyRevision(null, key, 1, sample(0.0, unit = "percent", receivedAt = at(10)))
        assertEquals(RevisionOutcome.ACCEPTED, zero.outcome)
        assertEquals(0.0, (zero.cursor?.observation?.classifiedValue() as ClassifiedValue.Reading).value)
        val text = applyRevision(null, key, 1, sample("0", unit = "token", receivedAt = at(11)))
        assertEquals(RevisionOutcome.ACCEPTED, text.outcome)
        assertEquals("0", text.cursor?.observation?.value)
        val blank = applyRevision(null, key, 1, sample("", unit = "token", receivedAt = at(14)))
        assertEquals(RevisionOutcome.ACCEPTED, blank.outcome)
        assertEquals("", blank.cursor?.observation?.value)
        val flag = applyRevision(null, key, 1, sample(false, unit = "flag", receivedAt = at(12)))
        assertEquals(RevisionOutcome.ACCEPTED, flag.outcome)
        assertEquals(false, flag.cursor?.observation?.value)
        val denied = applyRevision(
            null,
            key,
            1,
            sample(null, status = ObservationStatus.DENIED, receivedAt = at(20), observedAt = at(20)),
        )
        assertEquals(RevisionOutcome.ACCEPTED, denied.outcome)
        assertIs<ClassifiedValue.Denied>(denied.cursor?.observation?.classifiedValue())
        val unavailable = applyRevision(
            null,
            key,
            1,
            sample(null, status = ObservationStatus.UNAVAILABLE, receivedAt = at(21), observedAt = at(21)),
        )
        assertEquals(RevisionOutcome.ACCEPTED, unavailable.outcome)
        assertIs<ClassifiedValue.Unavailable>(unavailable.cursor?.observation?.classifiedValue())
        val failed = applyRevision(
            null,
            key,
            1,
            sample(null, status = ObservationStatus.ERROR, receivedAt = at(22), observedAt = at(22)),
        )
        assertEquals(RevisionOutcome.ACCEPTED, failed.outcome)
        assertIs<ClassifiedValue.Failed>(failed.cursor?.observation?.classifiedValue())
        val missing = applyRevision(null, key, 1, sample(null, receivedAt = at(23), observedAt = at(23)))
        assertEquals(RevisionOutcome.INVALID_OBSERVATION, missing.outcome)
        assertEquals(listOf(IssueCode.VALUE_REQUIRED), missing.issues.codes())
        assertNull(missing.cursor)
        val whole = applyRevision(null, key, 1, sample(0, unit = "count", receivedAt = at(13)))
        assertEquals(RevisionOutcome.ACCEPTED, whole.outcome)
        assertEquals(0, whole.cursor?.observation?.value)
        val scalars = listOf<Any>(0.toByte(), 0.toShort(), 0L, 0.0f, '0')
        scalars.forEach { value ->
            val accepted = applyRevision<Any>(null, key, 1, sample(value, unit = "scalar", receivedAt = at(15)))
            assertEquals(RevisionOutcome.ACCEPTED, accepted.outcome, value.javaClass.name)
            assertEquals(value, accepted.cursor?.observation?.value)
            assertIs<ClassifiedValue.Reading<Any>>(accepted.cursor?.observation?.classifiedValue())
        }
        val current = applyRevision(null, key, 1, sample<Any>(1.0, unit = "1", receivedAt = at(16))).cursor
        listOf<Any>(Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY, Float.NaN, Float.POSITIVE_INFINITY, Float.NEGATIVE_INFINITY).forEach { value ->
            val rejected = applyRevision(current, key, 2, sample(value, unit = "1", receivedAt = at(17)))
            assertEquals(RevisionOutcome.INVALID_OBSERVATION, rejected.outcome, value.toString())
            assertEquals(listOf(IssueCode.NON_FINITE), rejected.issues.codes(), value.toString())
            assertSame(current, rejected.cursor)
            assertIs<ClassifiedValue.Inconsistent>(sample(value, unit = "1").classifiedValue())
        }
    }

    @Test
    fun higherRevisionStillReplacesEarlierDenial() {
        val key = acceptedKey()
        val opened = applyRevision(null, key, 1, sample(10.0, observedAt = at(10), receivedAt = at(10)))
        val denied = applyRevision(
            opened.cursor,
            key,
            2,
            sample(null, status = ObservationStatus.DENIED, observedAt = at(20), receivedAt = at(20)),
        )
        assertEquals(RevisionOutcome.ACCEPTED, denied.outcome)
        val lateHigherRevision = applyRevision(
            denied.cursor,
            key,
            3,
            sample(33.0, observedAt = at(12), receivedAt = at(25)),
        )
        assertEquals(RevisionOutcome.ACCEPTED, lateHigherRevision.outcome)
        assertFalse(lateHigherRevision.receiveTimeInversion)
        assertEquals(33.0, lateHigherRevision.cursor?.observation?.value)
        assertEquals(at(12), lateHigherRevision.cursor?.observation?.observedAt)

        val other = acceptedKey(source = acceptedSource("other.source"), subject = "other.subject")
        val switched = applyRevision(
            lateHigherRevision.cursor,
            other,
            9,
            sample(1.0, source = other.source, receivedAt = at(26)),
        )
        assertEquals(RevisionOutcome.KEY_MISMATCH, switched.outcome)
        assertEquals(33.0, switched.cursor?.observation?.value)

        val sameInstant = applyRevision(
            lateHigherRevision.cursor,
            key,
            3,
            sample(33.0, observedAt = at(12), receivedAt = at(40)),
        )
        assertEquals(RevisionOutcome.DUPLICATE, sameInstant.outcome)

        val missingTime = applyRevision(
            lateHigherRevision.cursor,
            key,
            4,
            sample(40.0, observedAt = null, receivedAt = at(40)),
        )
        assertEquals(RevisionOutcome.ACCEPTED, missingTime.outcome)
        assertNull(missingTime.cursor?.observation?.observedAt)

        val future = applyRevision(
            missingTime.cursor,
            key,
            5,
            sample(50.0, observedAt = at(100), receivedAt = at(40)),
            ObservationConstraints(
                futureTimestamp = FutureTimestampPolicy.REJECT_AFTER_REFERENCE,
                referenceTime = at(40),
            ),
        )
        assertEquals(RevisionOutcome.INVALID_OBSERVATION, future.outcome)
        assertEquals(IssueCode.FUTURE_OBSERVED_AT, future.issues.first().code)
        assertEquals(40.0, future.cursor?.observation?.value)

        val restarted = applyRevision(null, key, 1, sample(7.0, observedAt = at(10), receivedAt = at(10)))
        assertEquals(RevisionOutcome.ACCEPTED, restarted.outcome)
        assertEquals(7.0, restarted.cursor?.observation?.value)
        val deniedAgain = applyRevision(
            restarted.cursor,
            key,
            2,
            sample(null, status = ObservationStatus.DENIED, observedAt = at(20), receivedAt = at(20)),
        )
        val recovered = applyRevision(
            deniedAgain.cursor,
            key,
            3,
            sample(80.0, observedAt = at(40), receivedAt = at(40)),
        )
        assertEquals(RevisionOutcome.ACCEPTED, recovered.outcome)
        assertEquals(80.0, recovered.cursor?.observation?.value)
        assertIs<ClassifiedValue.Reading<Double>>(recovered.cursor?.observation?.classifiedValue())
    }

    private fun at(seconds: Long): Instant = origin.plusSeconds(seconds)

    private fun <T> sample(
        value: T?,
        unit: String = "fixture",
        source: SourceId = acceptedSource(),
        observedAt: Instant? = at(1),
        receivedAt: Instant = at(1),
        status: ObservationStatus = ObservationStatus.VALID,
    ): Observation<T> {
        return observation(value, unit, source, observedAt, receivedAt, at(400), status)
    }

    private class Box(var value: Int)

    private class Node {
        var next: Node? = null
        var label: String = "cycle"
    }
}
