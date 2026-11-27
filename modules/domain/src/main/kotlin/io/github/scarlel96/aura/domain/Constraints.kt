package io.github.scarlel96.aura.domain

import java.time.Instant

enum class FutureTimestampPolicy {
    UNCHECKED,
    REJECT_AFTER_REFERENCE,
}

data class ObservationConstraints<T>(
    val expectedUnit: String? = null,
    val doubleRange: NumericRange? = null,
    val longRange: LongBounds? = null,
    val futureTimestamp: FutureTimestampPolicy = FutureTimestampPolicy.UNCHECKED,
    val referenceTime: Instant? = null,
)

@ConsistentCopyVisibility
data class NumericRange private constructor(
    val minimum: Double?,
    val maximum: Double?,
    val minimumInclusive: Boolean,
    val maximumInclusive: Boolean,
) {
    companion object {
        fun parse(
            minimum: Double?,
            maximum: Double?,
            minimumInclusive: Boolean = true,
            maximumInclusive: Boolean = true,
        ): DomainParse<NumericRange> {
            return parseBounds(minimum, maximum, minimumInclusive, maximumInclusive) { low, high, lowInclusive, highInclusive ->
                NumericRange(low, high, lowInclusive, highInclusive)
            }
        }
    }
}

@ConsistentCopyVisibility
data class LongBounds private constructor(
    val minimum: Long?,
    val maximum: Long?,
    val minimumInclusive: Boolean,
    val maximumInclusive: Boolean,
) {
    companion object {
        fun parse(
            minimum: Long?,
            maximum: Long?,
            minimumInclusive: Boolean = true,
            maximumInclusive: Boolean = true,
        ): DomainParse<LongBounds> {
            if (minimum == null && maximum == null) {
                return DomainParse.Rejected(ParseCode.RANGE_EMPTY)
            }
            if (minimum != null && maximum != null && minimum > maximum) {
                return DomainParse.Rejected(ParseCode.RANGE_INVERTED)
            }
            if (longSpanEmpty(minimum, maximum, minimumInclusive, maximumInclusive)) {
                return DomainParse.Rejected(ParseCode.RANGE_EMPTY)
            }
            return DomainParse.Accepted(LongBounds(minimum, maximum, minimumInclusive, maximumInclusive))
        }
    }
}

private fun longSpanEmpty(
    minimum: Long?,
    maximum: Long?,
    minimumInclusive: Boolean,
    maximumInclusive: Boolean,
): Boolean {
    val lower = when {
        minimum == null -> null
        minimumInclusive -> minimum
        minimum == Long.MAX_VALUE -> return true
        else -> minimum + 1
    }
    val upper = when {
        maximum == null -> null
        maximumInclusive -> maximum
        maximum == Long.MIN_VALUE -> return true
        else -> maximum - 1
    }
    return lower != null && upper != null && lower > upper
}

private fun <T> parseBounds(
    minimum: Double?,
    maximum: Double?,
    minimumInclusive: Boolean,
    maximumInclusive: Boolean,
    build: (Double?, Double?, Boolean, Boolean) -> T,
): DomainParse<T> {
    if (minimum == null && maximum == null) {
        return DomainParse.Rejected(ParseCode.RANGE_EMPTY)
    }
    if ((minimum != null && !minimum.isFinite()) || (maximum != null && !maximum.isFinite())) {
        return DomainParse.Rejected(ParseCode.NON_FINITE_BOUND)
    }
    if (minimum != null && maximum != null) {
        if (minimum > maximum) {
            return DomainParse.Rejected(ParseCode.RANGE_INVERTED)
        }
        if (minimum == maximum && (!minimumInclusive || !maximumInclusive)) {
            return DomainParse.Rejected(ParseCode.RANGE_EMPTY)
        }
    }
    return DomainParse.Accepted(build(minimum, maximum, minimumInclusive, maximumInclusive))
}
