package io.github.scarlel96.aura.domain

import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNull

class PayloadIntegrityTest {
    private val origin = Instant.parse("2026-11-28T00:00:00Z")

    @Test
    fun mutableListDoesNotReplaceStoredScalarOrChangeDuplicateVerdict() {
        val key = acceptedKey()
        val stored = applyRevision(null, key, 1, sample(10.0, receivedAt = at(10), observedAt = at(10)))
        val items = mutableListOf("kept")
        val decision = applyRevision(null, key, 1, sample(items, unit = "token", receivedAt = at(20), observedAt = at(20)))
        assertEquals(RevisionOutcome.INVALID_OBSERVATION, decision.outcome)
        assertEquals(listOf(IssueCode.UNSUPPORTED_PAYLOAD), decision.issues.codes())
        assertNull(decision.cursor)
        items[0] = "changed"
        items += "more"
        val replay = applyRevision(stored.cursor, key, 1, sample(10.0, receivedAt = at(30), observedAt = at(10)))
        assertEquals(RevisionOutcome.DUPLICATE, replay.outcome)
        assertEquals(10.0, replay.cursor?.observation?.value)
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
    }

    @Test
    fun directCursorConstructionRejectsMutablePayload() {
        val key = acceptedKey()
        val failure = assertFailsWith<UnsupportedPayloadException> {
            RevisionCursor(key, 1, sample(mutableListOf(1), unit = "count"))
        }
        assertEquals(IssueCode.UNSUPPORTED_PAYLOAD.name, failure.message)
        val accepted = RevisionCursor(key, 1, sample(4.0))
        assertEquals(4.0, accepted.observation.value)
        assertFailsWith<UnsupportedPayloadException> {
            RevisionCursor(key, 2, sample(mutableMapOf("a" to 1), unit = "token"))
        }
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
        val flag = applyRevision(null, key, 1, sample(false, unit = "flag", receivedAt = at(12)))
        assertEquals(RevisionOutcome.ACCEPTED, flag.outcome)
        val denied = applyRevision(
            null,
            key,
            1,
            sample(null, status = ObservationStatus.DENIED, receivedAt = at(20), observedAt = at(20)),
        )
        assertEquals(RevisionOutcome.ACCEPTED, denied.outcome)
        assertIs<ClassifiedValue.Denied>(denied.cursor?.observation?.classifiedValue())
        val whole = applyRevision(null, key, 1, sample(0, unit = "count", receivedAt = at(13)))
        assertEquals(RevisionOutcome.ACCEPTED, whole.outcome)
        assertEquals(0, whole.cursor?.observation?.value)
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
