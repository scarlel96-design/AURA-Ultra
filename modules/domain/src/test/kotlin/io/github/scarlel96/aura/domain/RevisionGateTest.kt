package io.github.scarlel96.aura.domain

import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertSame
import kotlin.test.assertTrue

class RevisionGateTest {
    private val key = acceptedKey()
    private val baseReceived = Instant.parse("2026-11-27T00:00:01Z")

    private fun sample(value: Int, receivedAt: Instant = baseReceived): Observation<Int> {
        return observation(value = value, source = key.source, receivedAt = receivedAt)
    }

    @Test
    fun firstValidRevisionIsAccepted() {
        val decision = applyRevision(null, key, 0, sample(3))
        assertEquals(RevisionOutcome.ACCEPTED, decision.outcome)
        assertEquals(0, decision.cursor?.revision)
        assertEquals(3, decision.cursor?.observation?.value)
        assertFalse(decision.receiveTimeInversion)
    }

    @Test
    fun higherRevisionReplacesAndGapIsAllowed() {
        val first = applyRevision(null, key, 5, sample(1))
        val second = applyRevision(first.cursor, key, 7, sample(2, baseReceived.plusSeconds(1)))
        assertEquals(RevisionOutcome.ACCEPTED, second.outcome)
        assertEquals(7, second.cursor?.revision)
        assertEquals(2, second.cursor?.observation?.value)
        higherRevisionStillReplacesAnEarlierDenial()
    }

    @Test
    fun olderRevisionDoesNotReplaceCurrent() {
        val current = applyRevision(null, key, 4, sample(9)).cursor
        val older = sample(1, baseReceived.plusSeconds(5))
        val decision = applyRevision(current, key, 2, older)
        assertEquals(RevisionOutcome.SUPERSEDED_REJECTED, decision.outcome)
        assertSame(current, decision.cursor)
        assertEquals(9, decision.cursor?.observation?.value)
        assertEquals(4, decision.cursor?.revision)
    }

    @Test
    fun outOfOrderSequenceKeepsTheNewestRevision() {
        var cursor = applyRevision(null, key, 3, sample(30)).cursor
        val rejectedOne = applyRevision(cursor, key, 1, sample(10, baseReceived.plusSeconds(1)))
        cursor = rejectedOne.cursor
        val rejectedTwo = applyRevision(cursor, key, 2, sample(20, baseReceived.plusSeconds(2)))
        cursor = rejectedTwo.cursor
        val duplicate = applyRevision(cursor, key, 3, sample(30, baseReceived.plusSeconds(3)))
        cursor = duplicate.cursor
        val next = applyRevision(cursor, key, 4, sample(40, baseReceived.plusSeconds(4)))
        assertEquals(RevisionOutcome.SUPERSEDED_REJECTED, rejectedOne.outcome)
        assertEquals(RevisionOutcome.SUPERSEDED_REJECTED, rejectedTwo.outcome)
        assertEquals(RevisionOutcome.DUPLICATE, duplicate.outcome)
        assertEquals(RevisionOutcome.ACCEPTED, next.outcome)
        assertEquals(4, next.cursor?.revision)
        assertEquals(40, next.cursor?.observation?.value)
    }

    @Test
    fun equalRevisionWithOnlyReceiveTimeChangedIsDuplicate() {
        val current = applyRevision(null, key, 8, sample(5)).cursor
        val replay = applyRevision(current, key, 8, sample(5, baseReceived.plusSeconds(9)))
        assertEquals(RevisionOutcome.DUPLICATE, replay.outcome)
        assertSame(current, replay.cursor)
        assertEquals(baseReceived, replay.cursor?.observation?.receivedAt)
    }

    @Test
    fun equalRevisionWithDifferentPayloadDoesNotOverwrite() {
        val current = applyRevision(null, key, 8, sample(5)).cursor
        val conflict = applyRevision(current, key, 8, sample(6, baseReceived.plusSeconds(1)))
        assertEquals(RevisionOutcome.DUPLICATE_CONFLICT, conflict.outcome)
        assertSame(current, conflict.cursor)
        assertEquals(5, conflict.cursor?.observation?.value)
    }

    @Test
    fun newerRevisionWithEarlierReceiveTimeIsAcceptedAndFlagged() {
        val current = applyRevision(null, key, 1, sample(1, baseReceived.plusSeconds(10))).cursor
        val decision = applyRevision(current, key, 2, sample(2, baseReceived))
        assertEquals(RevisionOutcome.ACCEPTED, decision.outcome)
        assertTrue(decision.receiveTimeInversion)
        assertEquals(2, decision.cursor?.revision)
        assertEquals(2, decision.cursor?.observation?.value)
        assertEquals(baseReceived, decision.cursor?.observation?.receivedAt)
    }

    @Test
    fun negativeRevisionsCompareNumerically() {
        val current = applyRevision(null, key, -1, sample(1)).cursor
        val older = applyRevision(current, key, -5, sample(0))
        val newer = applyRevision(current, key, 0, sample(2, baseReceived.plusSeconds(1)))
        assertEquals(RevisionOutcome.SUPERSEDED_REJECTED, older.outcome)
        assertEquals(RevisionOutcome.ACCEPTED, newer.outcome)
        assertEquals(0, newer.cursor?.revision)
    }

    @Test
    fun maxLongRevisionDuplicateAndPredecessor() {
        val current = applyRevision(null, key, Long.MAX_VALUE, sample(1)).cursor
        val duplicate = applyRevision(current, key, Long.MAX_VALUE, sample(1, baseReceived.plusSeconds(1)))
        val predecessor = applyRevision(current, key, Long.MAX_VALUE - 1, sample(2))
        assertEquals(RevisionOutcome.DUPLICATE, duplicate.outcome)
        assertEquals(RevisionOutcome.SUPERSEDED_REJECTED, predecessor.outcome)
        assertEquals(Long.MAX_VALUE, duplicate.cursor?.revision)
    }

    @Test
    fun invalidIncomingDoesNotCreateOrReplaceCursor() {
        val invalid = observation(value = 0, unit = "count", source = key.source, status = ObservationStatus.ERROR)
        val first = applyRevision(null, key, 1, invalid)
        assertEquals(RevisionOutcome.INVALID_OBSERVATION, first.outcome)
        assertEquals(null, first.cursor)
        assertEquals(listOf(IssueCode.VALUE_FORBIDDEN), first.issues.codes())

        val current = applyRevision(null, key, 2, sample(4)).cursor
        val rejected = applyRevision(current, key, 3, invalid)
        assertEquals(RevisionOutcome.INVALID_OBSERVATION, rejected.outcome)
        assertSame(current, rejected.cursor)
        assertEquals(4, rejected.cursor?.observation?.value)
        mutablePayloadsStayOutOfTheCursor()
    }

    private fun mutablePayloadsStayOutOfTheCursor() {
        val items = mutableListOf("kept")
        val decision = applyRevision(
            null,
            key,
            1,
            observation(items, unit = "token", source = key.source),
        )
        assertEquals(RevisionOutcome.INVALID_OBSERVATION, decision.outcome)
        assertEquals(listOf(IssueCode.UNSUPPORTED_PAYLOAD), decision.issues.codes())
        assertEquals(null, decision.cursor)
        items[0] = "changed"
        items += "more"
        val stored = applyRevision(null, key, 1, sample(10))
        val replay = applyRevision(stored.cursor, key, 1, sample(10, baseReceived.plusSeconds(3)))
        assertEquals(RevisionOutcome.DUPLICATE, replay.outcome)
        assertEquals(10, replay.cursor?.observation?.value)

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
            val rejected = applyRevision<Any>(
                null,
                key,
                1,
                observation(payload, unit = "token", source = key.source),
            )
            assertEquals(RevisionOutcome.INVALID_OBSERVATION, rejected.outcome, payload.javaClass.name)
            assertEquals(listOf(IssueCode.UNSUPPORTED_PAYLOAD), rejected.issues.codes())
            assertEquals(null, rejected.cursor)
        }
        nested[0][0] = 9
        assertEquals(10, stored.cursor?.observation?.value)
        val node = Node()
        node.next = node
        val cyclic = applyRevision(null, key, 1, observation(node, unit = "token", source = key.source))
        assertEquals(RevisionOutcome.INVALID_OBSERVATION, cyclic.outcome)
        assertEquals(null, cyclic.cursor)
        val failure = assertFailsWith<UnsupportedPayloadException> {
            RevisionCursor(key, 1, observation(mutableListOf(1), unit = "count", source = key.source))
        }
        assertEquals(IssueCode.UNSUPPORTED_PAYLOAD.name, failure.message)
    }

    private fun higherRevisionStillReplacesAnEarlierDenial() {
        val origin = Instant.parse("2026-11-28T00:00:00Z")
        fun at(seconds: Long): Instant = origin.plusSeconds(seconds)
        val opened = applyRevision(
            null,
            key,
            1,
            observation(10.0, source = key.source, observedAt = at(10), receivedAt = at(10), expiresAt = at(400)),
        )
        val denied = applyRevision(
            opened.cursor,
            key,
            2,
            observation(
                null,
                source = key.source,
                status = ObservationStatus.DENIED,
                observedAt = at(20),
                receivedAt = at(20),
                expiresAt = at(400),
            ),
        )
        assertEquals(RevisionOutcome.ACCEPTED, denied.outcome)
        val late = applyRevision(
            denied.cursor,
            key,
            3,
            observation(33.0, source = key.source, observedAt = at(12), receivedAt = at(25), expiresAt = at(400)),
        )
        assertEquals(RevisionOutcome.ACCEPTED, late.outcome)
        assertFalse(late.receiveTimeInversion)
        assertEquals(33.0, late.cursor?.observation?.value)
        val other = acceptedKey(source = acceptedSource("other.source"), subject = "other.subject")
        val switched = applyRevision(
            late.cursor,
            other,
            9,
            observation(1.0, source = other.source, receivedAt = at(26), expiresAt = at(400)),
        )
        assertEquals(RevisionOutcome.KEY_MISMATCH, switched.outcome)
        assertEquals(33.0, switched.cursor?.observation?.value)
        val duplicate = applyRevision(
            late.cursor,
            key,
            3,
            observation(33.0, source = key.source, observedAt = at(12), receivedAt = at(40), expiresAt = at(400)),
        )
        assertEquals(RevisionOutcome.DUPLICATE, duplicate.outcome)
        val missingTime = applyRevision(
            late.cursor,
            key,
            4,
            observation(40.0, source = key.source, observedAt = null, receivedAt = at(40), expiresAt = at(400)),
        )
        assertEquals(RevisionOutcome.ACCEPTED, missingTime.outcome)
        assertEquals(null, missingTime.cursor?.observation?.observedAt)
        val future = applyRevision(
            missingTime.cursor,
            key,
            5,
            observation(50.0, source = key.source, observedAt = at(100), receivedAt = at(40), expiresAt = at(400)),
            ObservationConstraints(
                futureTimestamp = FutureTimestampPolicy.REJECT_AFTER_REFERENCE,
                referenceTime = at(40),
            ),
        )
        assertEquals(RevisionOutcome.INVALID_OBSERVATION, future.outcome)
        assertEquals(IssueCode.FUTURE_OBSERVED_AT, future.issues.first().code)
        val restarted = applyRevision(
            null,
            key,
            1,
            observation(7.0, source = key.source, observedAt = at(10), receivedAt = at(10), expiresAt = at(400)),
        )
        val deniedAgain = applyRevision(
            restarted.cursor,
            key,
            2,
            observation(
                null,
                source = key.source,
                status = ObservationStatus.DENIED,
                observedAt = at(20),
                receivedAt = at(20),
                expiresAt = at(400),
            ),
        )
        val recovered = applyRevision(
            deniedAgain.cursor,
            key,
            3,
            observation(80.0, source = key.source, observedAt = at(40), receivedAt = at(40), expiresAt = at(400)),
        )
        assertEquals(RevisionOutcome.ACCEPTED, recovered.outcome)
        assertEquals(80.0, recovered.cursor?.observation?.value)
    }

    private class Box(var value: Int)

    private class Node {
        var next: Node? = null
    }

    @Test
    fun wrongUnitDoesNotPassTheGate() {
        val current = applyRevision(null, key, 1, sample(1)).cursor
        val incoming = observation(value = 2, unit = "mm", source = key.source)
        val decision = applyRevision(
            current,
            key,
            2,
            incoming,
            ObservationConstraints(expectedUnit = "fixture"),
        )
        assertEquals(RevisionOutcome.INVALID_OBSERVATION, decision.outcome)
        assertEquals(listOf(IssueCode.UNIT_MISMATCH), decision.issues.codes())
        assertSame(current, decision.cursor)
    }

    @Test
    fun keyMismatchKeepsTheCurrentStream() {
        val current = applyRevision(null, key, 1, sample(1)).cursor
        val other = acceptedKey(subject = "other.subject")
        val decision = applyRevision(current, other, 9, observation(value = 9, source = other.source))
        assertEquals(RevisionOutcome.KEY_MISMATCH, decision.outcome)
        assertSame(current, decision.cursor)
        assertEquals(1, decision.cursor?.observation?.value)
    }

    @Test
    fun sourceInsideObservationMustMatchKey() {
        val foreign = observation(value = 1, source = acceptedSource("other.source"))
        val decision = applyRevision(null, key, 1, foreign)
        assertEquals(RevisionOutcome.INVALID_OBSERVATION, decision.outcome)
        assertEquals(listOf(IssueCode.SOURCE_KEY_MISMATCH), decision.issues.codes())
        assertEquals(null, decision.cursor)
    }

    @Test
    fun negativeZeroIsNotTreatedAsTheSamePayload() {
        val positive = observation(value = 0.0, unit = "1", source = key.source)
        val negative = positive.copy(value = -0.0)
        val current = applyRevision(null, key, 1, positive).cursor
        val decision = applyRevision(current, key, 1, negative)
        assertEquals(RevisionOutcome.DUPLICATE_CONFLICT, decision.outcome)
        assertSame(current, decision.cursor)
        assertTrue(decision.cursor?.observation?.value?.toBits() == 0.0.toBits())
    }

    @Test
    fun blankSubjectKeyIsRejected() {
        val broken = ObservationKey(key.source, " ")
        val decision = applyRevision(null, broken, 1, sample(1))
        assertEquals(RevisionOutcome.INVALID_KEY, decision.outcome)
        assertEquals(null, decision.cursor)
    }
}
