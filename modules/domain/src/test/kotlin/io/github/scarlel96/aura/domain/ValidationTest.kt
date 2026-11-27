package io.github.scarlel96.aura.domain

import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertTrue

class ValidationTest {
    @Test
    fun actualZeroStaysAReading() {
        val observation = observation(value = 0, unit = "count", status = ObservationStatus.VALID)
        val report = validateObservation(observation)
        assertTrue(report.accepted)
        val classified = observation.classifiedValue()
        assertIs<ClassifiedValue.Reading<Int>>(classified)
        assertEquals(0, classified.value)
        assertEquals(ObservationStatus.VALID, classified.status)
    }

    @Test
    fun negativeZeroIsAnActualReadingAndIsNotCanonicalized() {
        val observation = observation(value = -0.0, unit = "1")
        assertTrue(validateObservation(observation).accepted)
        val classified = observation.classifiedValue()
        assertIs<ClassifiedValue.Reading<Double>>(classified)
        assertTrue(classified.value == 0.0)
        assertTrue(classified.value.toBits() != 0.0.toBits())
    }

    @Test
    fun missingValueIsUnavailableAndNotZero() {
        val observation = observation<Int>(
            value = null,
            unit = "",
            status = ObservationStatus.UNAVAILABLE,
        )
        assertTrue(validateObservation(observation).accepted)
        assertIs<ClassifiedValue.Unavailable>(observation.classifiedValue())
    }

    @Test
    fun deniedAndErrorWithoutValueStayDistinct() {
        val denied = observation<Int>(value = null, unit = "", status = ObservationStatus.DENIED)
        val failed = observation<Int>(value = null, unit = "", status = ObservationStatus.ERROR)
        assertTrue(validateObservation(denied).accepted)
        assertTrue(validateObservation(failed).accepted)
        assertIs<ClassifiedValue.Denied>(denied.classifiedValue())
        assertIs<ClassifiedValue.Failed>(failed.classifiedValue())
    }

    @Test
    fun staleZeroRemainsAStaleReading() {
        val observation = observation(value = 0, unit = "count", status = ObservationStatus.STALE)
        assertTrue(validateObservation(observation).accepted)
        val classified = observation.classifiedValue()
        assertIs<ClassifiedValue.Reading<Int>>(classified)
        assertEquals(0, classified.value)
        assertEquals(ObservationStatus.STALE, classified.status)
    }

    @Test
    fun textualZeroIsNotTreatedAsMissing() {
        val observation = observation(value = "0", unit = "text")
        assertTrue(validateObservation(observation).accepted)
        val classified = observation.classifiedValue()
        assertIs<ClassifiedValue.Reading<String>>(classified)
        assertEquals("0", classified.value)
    }

    @Test
    fun validOrStaleWithoutValueIsRejectedAndNotRewritten() {
        val valid = observation<Int>(value = null, unit = "count", status = ObservationStatus.VALID)
        val stale = observation<Int>(value = null, unit = "count", status = ObservationStatus.STALE)
        assertEquals(listOf(IssueCode.VALUE_REQUIRED), validateObservation(valid).codes())
        assertEquals(listOf(IssueCode.VALUE_REQUIRED), validateObservation(stale).codes())
        assertEquals(ObservationStatus.VALID, valid.status)
        assertEquals(null, valid.value)
        assertIs<ClassifiedValue.Inconsistent>(valid.classifiedValue())
    }

    @Test
    fun injectedErrorZeroIsNotAcceptedOrCoerced() {
        val observation = observation(value = 0, unit = "count", status = ObservationStatus.ERROR)
        val report = validateObservation(observation)
        assertFalse(report.accepted)
        assertEquals(listOf(IssueCode.VALUE_FORBIDDEN), report.codes())
        assertEquals(0, observation.value)
        assertEquals(ObservationStatus.ERROR, observation.status)
        assertIs<ClassifiedValue.Inconsistent>(observation.classifiedValue())
    }

    @Test
    fun injectedDeniedAndUnavailableNumbersAreRejected() {
        val denied = observation(value = 0, unit = "count", status = ObservationStatus.DENIED)
        val missing = observation(value = 12, unit = "count", status = ObservationStatus.UNAVAILABLE)
        assertEquals(listOf(IssueCode.VALUE_FORBIDDEN), validateObservation(denied).codes())
        assertEquals(listOf(IssueCode.VALUE_FORBIDDEN), validateObservation(missing).codes())
        assertEquals(0, denied.value)
        assertEquals(12, missing.value)
    }

    @Test
    fun blankOrPaddedUnitIsRejectedWhenValueExists() {
        val blank = observation(value = 3, unit = " ")
        val padded = observation(value = 3, unit = " mm ")
        assertEquals(listOf(IssueCode.UNIT_BLANK), validateObservation(blank).codes())
        assertTrue(IssueCode.UNIT_PADDED in validateObservation(padded, ObservationConstraints(expectedUnit = "mm")).codes())
        assertTrue(IssueCode.UNIT_MISMATCH in validateObservation(padded, ObservationConstraints(expectedUnit = "mm")).codes())
    }

    @Test
    fun unitMatchIsExactAndDoesNotConvert() {
        val celsius = observation(value = 0.0, unit = "C")
        assertTrue(validateObservation(celsius, ObservationConstraints(expectedUnit = "C")).accepted)
        assertEquals(
            listOf(IssueCode.UNIT_MISMATCH),
            validateObservation(celsius, ObservationConstraints(expectedUnit = "°C")).codes(),
        )
        assertEquals(
            listOf(IssueCode.UNIT_MISMATCH),
            validateObservation(celsius, ObservationConstraints(expectedUnit = "c")).codes(),
        )
    }

    @Test
    fun absentValueSkipsExpectedUnit() {
        val missing = observation<Double>(value = null, unit = "", status = ObservationStatus.UNAVAILABLE)
        assertTrue(validateObservation(missing, ObservationConstraints(expectedUnit = "mm")).accepted)
    }

    @Test
    fun doubleRangeBoundaries() {
        val range = acceptedDoubleRange(0.0, 10.0)
        assertTrue(validateObservation(observation(0.0, "1"), ObservationConstraints(doubleRange = range)).accepted)
        assertTrue(validateObservation(observation(10.0, "1"), ObservationConstraints(doubleRange = range)).accepted)
        assertEquals(
            listOf(IssueCode.RANGE_BELOW),
            validateObservation(observation(-0.1, "1"), ObservationConstraints(doubleRange = range)).codes(),
        )
        assertEquals(
            listOf(IssueCode.RANGE_ABOVE),
            validateObservation(observation(10.1, "1"), ObservationConstraints(doubleRange = range)).codes(),
        )
    }

    @Test
    fun exclusiveDoubleBoundsRejectEndpoints() {
        val range = acceptedDoubleRange(0.0, 10.0, minimumInclusive = false, maximumInclusive = false)
        assertEquals(
            listOf(IssueCode.RANGE_BELOW),
            validateObservation(observation(0.0, "1"), ObservationConstraints(doubleRange = range)).codes(),
        )
        assertEquals(
            listOf(IssueCode.RANGE_ABOVE),
            validateObservation(observation(10.0, "1"), ObservationConstraints(doubleRange = range)).codes(),
        )
        assertTrue(validateObservation(observation(0.1, "1"), ObservationConstraints(doubleRange = range)).accepted)
    }

    @Test
    fun singlePointRangeAcceptsOnlyThatPoint() {
        val range = acceptedDoubleRange(0.0, 0.0)
        assertTrue(validateObservation(observation(0.0, "1"), ObservationConstraints(doubleRange = range)).accepted)
        assertTrue(validateObservation(observation(-0.0, "1"), ObservationConstraints(doubleRange = range)).accepted)
        assertEquals(
            listOf(IssueCode.RANGE_ABOVE),
            validateObservation(observation(0.1, "1"), ObservationConstraints(doubleRange = range)).codes(),
        )
    }

    @Test
    fun longRangeAcceptsIntExactlyAndRejectsDouble() {
        val range = acceptedLongRange(0, 10)
        assertTrue(validateObservation(observation(0, "count"), ObservationConstraints(longRange = range)).accepted)
        assertTrue(validateObservation(observation(10, "count"), ObservationConstraints(longRange = range)).accepted)
        assertEquals(
            listOf(IssueCode.RANGE_BELOW),
            validateObservation(observation(-1, "count"), ObservationConstraints(longRange = range)).codes(),
        )
        assertEquals(
            listOf(IssueCode.CONSTRAINT_TYPE_MISMATCH),
            validateObservation(observation(1.0, "count"), ObservationConstraints(longRange = range)).codes(),
        )
    }

    @Test
    fun exclusiveLongEndpointAndMaxValue() {
        val range = acceptedLongRange(0, Long.MAX_VALUE, minimumInclusive = false, maximumInclusive = true)
        assertEquals(
            listOf(IssueCode.RANGE_BELOW),
            validateObservation(observation(0L, "count"), ObservationConstraints(longRange = range)).codes(),
        )
        assertTrue(
            validateObservation(observation(Long.MAX_VALUE, "count"), ObservationConstraints(longRange = range)).accepted,
        )
    }

    @Test
    fun conflictingRangesAreRejectedBeforeComparison() {
        val constraints = ObservationConstraints<Int>(
            doubleRange = acceptedDoubleRange(0.0, 1.0),
            longRange = acceptedLongRange(0, 1),
        )
        assertEquals(listOf(IssueCode.CONSTRAINT_CONFLICT), validateObservation(observation(0, "count"), constraints).codes())
    }

    @Test
    fun nonFiniteFloatsAreRejectedWithoutBecomingZero() {
        listOf(Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY).forEach { value ->
            val observation = observation(value, "1")
            assertEquals(listOf(IssueCode.NON_FINITE), validateObservation(observation).codes())
            assertEquals(value, observation.value)
            assertIs<ClassifiedValue.Inconsistent>(observation.classifiedValue())
        }
        assertEquals(listOf(IssueCode.NON_FINITE), validateObservation(observation(Float.NaN, "1")).codes())
    }

    @Test
    fun malformedRangesAreRejected() {
        assertEquals(ParseCode.RANGE_EMPTY, (NumericRange.parse(null, null) as DomainParse.Rejected).code)
        assertEquals(ParseCode.RANGE_INVERTED, (NumericRange.parse(2.0, 1.0) as DomainParse.Rejected).code)
        assertEquals(ParseCode.RANGE_EMPTY, (NumericRange.parse(1.0, 1.0, minimumInclusive = false) as DomainParse.Rejected).code)
        assertEquals(ParseCode.NON_FINITE_BOUND, (NumericRange.parse(Double.NaN, 1.0) as DomainParse.Rejected).code)
        assertEquals(ParseCode.RANGE_INVERTED, (LongBounds.parse(2, 1) as DomainParse.Rejected).code)
        assertEquals(ParseCode.RANGE_EMPTY, (LongBounds.parse(null, null) as DomainParse.Rejected).code)
    }

    @Test
    fun expiryBeforeObservedAtIsStructural() {
        val observedAt = Instant.parse("2026-11-27T00:00:00Z")
        val broken = observation(
            value = 1,
            observedAt = observedAt,
            expiresAt = observedAt.minusNanos(1),
        )
        val touching = observation(value = 1, observedAt = observedAt, expiresAt = observedAt)
        assertEquals(listOf(IssueCode.EXPIRES_BEFORE_OBSERVED), validateObservation(broken).codes())
        assertTrue(validateObservation(touching).accepted)
    }

    @Test
    fun futureTimestampsStayUncheckedUnlessCallerSelectsPolicy() {
        val reference = Instant.parse("2026-11-27T00:00:00Z")
        val future = observation(
            value = 1,
            observedAt = reference.plusSeconds(1),
            receivedAt = reference.plusSeconds(2),
        )
        assertTrue(validateObservation(future).accepted)
        val rejected = validateObservation(
            future,
            ObservationConstraints(
                futureTimestamp = FutureTimestampPolicy.REJECT_AFTER_REFERENCE,
                referenceTime = reference,
            ),
        )
        assertEquals(listOf(IssueCode.FUTURE_OBSERVED_AT, IssueCode.FUTURE_RECEIVED_AT), rejected.codes())
        val missingReference = validateObservation(
            future,
            ObservationConstraints(futureTimestamp = FutureTimestampPolicy.REJECT_AFTER_REFERENCE),
        )
        assertEquals(listOf(IssueCode.REFERENCE_TIME_REQUIRED), missingReference.codes())
    }

    @Test
    fun equalReferenceTimeIsNotFuture() {
        val reference = Instant.parse("2026-11-27T00:00:00Z")
        val observation = observation(value = 1, observedAt = reference, receivedAt = reference)
        val report = validateObservation(
            observation,
            ObservationConstraints(
                futureTimestamp = FutureTimestampPolicy.REJECT_AFTER_REFERENCE,
                referenceTime = reference,
            ),
        )
        assertTrue(report.accepted)
    }

    @Test
    fun plainUnitTokensStayAccepted() {
        val millimeters = observation(value = 1, unit = "mm")
        val celsius = observation(value = 21.5, unit = "°C")
        val ratio = observation(value = 1, unit = "m/s")
        assertTrue(validateObservation(millimeters, ObservationConstraints(expectedUnit = "mm")).accepted)
        assertTrue(validateObservation(celsius, ObservationConstraints(expectedUnit = "°C")).accepted)
        assertTrue(validateObservation(ratio).accepted)
    }

    @Test
    fun internalWhitespaceInUnitIsRejectedEvenWhenExpectedMatches() {
        val spaced = observation(value = 3, unit = "mm Hg")
        val report = validateObservation(spaced, ObservationConstraints(expectedUnit = "mm Hg"))
        assertEquals(listOf(IssueCode.UNIT_PADDED), report.codes())
        assertEquals("mm Hg", spaced.unit)
        assertEquals(3, spaced.value)
    }

    @Test
    fun nonWhitespaceControlCharacterInUnitIsRejected() {
        val embedded = observation(value = 3, unit = "mm\u0000")
        val onlyControl = observation(value = 3, unit = "\u0000")
        val leading = observation(value = 3, unit = "\u0007mm")
        assertEquals(
            listOf(IssueCode.UNIT_CONTROL),
            validateObservation(embedded, ObservationConstraints(expectedUnit = "mm\u0000")).codes(),
        )
        assertEquals(listOf(IssueCode.UNIT_CONTROL), validateObservation(onlyControl).codes())
        assertEquals(listOf(IssueCode.UNIT_CONTROL), validateObservation(leading).codes())
        assertEquals("mm\u0000", embedded.unit)
    }

    @Test
    fun internalWhitespaceThatIsAlsoAControlCharacterIsRejected() {
        val observation = observation(value = 3, unit = "mm\u000BHg")
        assertEquals(listOf(IssueCode.UNIT_PADDED), validateObservation(observation).codes())
    }

    @Test
    fun absentValueStillSkipsUnitCharacterChecks() {
        val missing = observation<Int>(value = null, unit = "\u0000", status = ObservationStatus.UNAVAILABLE)
        assertTrue(validateObservation(missing).accepted)
    }

    @Test
    fun exclusiveAdjacentLongRangeIsEmpty() {
        assertEquals(
            ParseCode.RANGE_EMPTY,
            (LongBounds.parse(5, 6, minimumInclusive = false, maximumInclusive = false) as DomainParse.Rejected).code,
        )
        assertEquals(
            ParseCode.RANGE_EMPTY,
            (LongBounds.parse(Long.MAX_VALUE - 1, Long.MAX_VALUE, minimumInclusive = false, maximumInclusive = false) as DomainParse.Rejected).code,
        )
        assertEquals(
            ParseCode.RANGE_EMPTY,
            (LongBounds.parse(Long.MIN_VALUE, Long.MIN_VALUE + 1, minimumInclusive = false, maximumInclusive = false) as DomainParse.Rejected).code,
        )
    }

    @Test
    fun exclusiveExtremeWithNoRepresentableLongIsEmpty() {
        assertEquals(
            ParseCode.RANGE_EMPTY,
            (LongBounds.parse(Long.MAX_VALUE, null, minimumInclusive = false, maximumInclusive = true) as DomainParse.Rejected).code,
        )
        assertEquals(
            ParseCode.RANGE_EMPTY,
            (LongBounds.parse(null, Long.MIN_VALUE, minimumInclusive = true, maximumInclusive = false) as DomainParse.Rejected).code,
        )
        assertEquals(
            ParseCode.RANGE_EMPTY,
            (LongBounds.parse(Long.MAX_VALUE, Long.MAX_VALUE, minimumInclusive = false, maximumInclusive = true) as DomainParse.Rejected).code,
        )
        assertEquals(
            ParseCode.RANGE_EMPTY,
            (LongBounds.parse(Long.MIN_VALUE, Long.MIN_VALUE, minimumInclusive = true, maximumInclusive = false) as DomainParse.Rejected).code,
        )
    }

    @Test
    fun exclusiveNeighborAndExtremeInclusivePointsStayValid() {
        val aboveZero = acceptedLongRange(0, null, minimumInclusive = false)
        assertEquals(
            listOf(IssueCode.RANGE_BELOW),
            validateObservation(observation(0L, "count"), ObservationConstraints(longRange = aboveZero)).codes(),
        )
        assertTrue(validateObservation(observation(1L, "count"), ObservationConstraints(longRange = aboveZero)).accepted)

        val belowTen = acceptedLongRange(null, 10, maximumInclusive = false)
        assertTrue(validateObservation(observation(9L, "count"), ObservationConstraints(longRange = belowTen)).accepted)
        assertEquals(
            listOf(IssueCode.RANGE_ABOVE),
            validateObservation(observation(10L, "count"), ObservationConstraints(longRange = belowTen)).codes(),
        )

        val onlyMin = acceptedLongRange(Long.MIN_VALUE, Long.MIN_VALUE)
        assertTrue(validateObservation(observation(Long.MIN_VALUE, "count"), ObservationConstraints(longRange = onlyMin)).accepted)
        val onlyMax = acceptedLongRange(Long.MAX_VALUE, Long.MAX_VALUE)
        assertTrue(validateObservation(observation(Long.MAX_VALUE, "count"), ObservationConstraints(longRange = onlyMax)).accepted)

        val openGap = acceptedLongRange(5, 7, minimumInclusive = false, maximumInclusive = false)
        assertTrue(validateObservation(observation(6L, "count"), ObservationConstraints(longRange = openGap)).accepted)
        assertEquals(
            listOf(IssueCode.RANGE_BELOW),
            validateObservation(observation(5L, "count"), ObservationConstraints(longRange = openGap)).codes(),
        )
        assertEquals(
            listOf(IssueCode.RANGE_ABOVE),
            validateObservation(observation(7L, "count"), ObservationConstraints(longRange = openGap)).codes(),
        )
    }

    @Test
    fun allKindsRemainUnchangedByValidation() {
        ObservationKind.entries.forEach { kind ->
            val observation = observation(value = 1, kind = kind)
            assertTrue(validateObservation(observation).accepted)
            assertEquals(kind, observation.kind)
        }
    }
}
