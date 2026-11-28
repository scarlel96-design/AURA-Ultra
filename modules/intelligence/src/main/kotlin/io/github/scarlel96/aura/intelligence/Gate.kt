package io.github.scarlel96.aura.intelligence

import io.github.scarlel96.aura.domain.ClassifiedValue
import io.github.scarlel96.aura.domain.Freshness
import io.github.scarlel96.aura.domain.IssueCode
import io.github.scarlel96.aura.domain.Observation
import io.github.scarlel96.aura.domain.ObservationConstraints
import io.github.scarlel96.aura.domain.ObservationStatus
import io.github.scarlel96.aura.domain.StatusDerivation
import io.github.scarlel96.aura.domain.classifiedValue
import io.github.scarlel96.aura.domain.deriveStatus
import io.github.scarlel96.aura.domain.validateObservation
import java.time.Instant

sealed class Channel<out T> {
    data object Absent : Channel<Nothing>()

    data class Unusable(
        val reason: UnusableReason,
        val freshness: Freshness? = null,
    ) : Channel<Nothing>()

    data class Fresh<T>(val value: T) : Channel<T>()
}

fun gateDouble(
    observation: Observation<Double>?,
    referenceTime: Instant,
    expectedUnit: String,
    minimum: Double,
    maximum: Double,
): Channel<Double> {
    if (!minimum.isFinite() || !maximum.isFinite() || minimum > maximum) {
        return Channel.Unusable(UnusableReason.REJECTED)
    }
    return gateReading(observation, referenceTime, expectedUnit) { value ->
        if (value < minimum || value > maximum) {
            Channel.Unusable(UnusableReason.OUTSIDE_CANDIDATE_SCALE)
        } else {
            Channel.Fresh(value)
        }
    }
}

fun gateFlag(
    observation: Observation<Boolean>?,
    referenceTime: Instant,
    expectedUnit: String,
): Channel<Boolean> {
    return gateReading(observation, referenceTime, expectedUnit) { Channel.Fresh(it) }
}

fun <T> gateToken(
    observation: Observation<String>?,
    referenceTime: Instant,
    expectedUnit: String,
    parse: (String) -> T?,
): Channel<T> {
    return gateReading(observation, referenceTime, expectedUnit) { token ->
        val parsed = parse(token)
        if (parsed == null) {
            Channel.Unusable(UnusableReason.TOKEN_UNCHECKED)
        } else {
            Channel.Fresh(parsed)
        }
    }
}

private fun <T, R> gateReading(
    observation: Observation<T>?,
    referenceTime: Instant,
    expectedUnit: String,
    accept: (T) -> Channel<R>,
): Channel<R> {
    if (observation == null) {
        return Channel.Absent
    }
    if (expectedUnit.isAbnormalUnitToken()) {
        return Channel.Unusable(UnusableReason.UNIT_UNCHECKED)
    }
    val derived = deriveStatus(observation, referenceTime)
    val freshness = when (derived) {
        is StatusDerivation.Rejected -> return Channel.Unusable(UnusableReason.REJECTED)
        is StatusDerivation.DegradedToStale ->
            return Channel.Unusable(UnusableReason.STALE, derived.freshness)
        is StatusDerivation.Unchanged -> derived.freshness
    }
    val current = derived.observation
    val reading = when (val classified = current.classifiedValue()) {
        is ClassifiedValue.Reading<T> -> classified
        ClassifiedValue.Unavailable -> return statusUnusable(UnusableReason.UNAVAILABLE, freshness)
        ClassifiedValue.Denied -> return statusUnusable(UnusableReason.DENIED, freshness)
        ClassifiedValue.Failed -> return statusUnusable(UnusableReason.ERROR, freshness)
        is ClassifiedValue.Inconsistent -> return Channel.Unusable(UnusableReason.INCONSISTENT)
    }
    when (freshness) {
        Freshness.UNDECLARED -> return Channel.Unusable(UnusableReason.UNDECLARED, freshness)
        Freshness.EXPIRED -> return Channel.Unusable(UnusableReason.STALE, freshness)
        Freshness.FRESH -> Unit
    }
    if (reading.status != ObservationStatus.VALID) {
        return Channel.Unusable(UnusableReason.STALE, freshness)
    }
    val constrained = validateObservation(
        current,
        ObservationConstraints(expectedUnit = expectedUnit),
    )
    if (!constrained.accepted) {
        val mismatch = constrained.issues.any { it.code == IssueCode.UNIT_MISMATCH }
        return Channel.Unusable(
            if (mismatch) UnusableReason.UNIT_UNCHECKED else UnusableReason.REJECTED,
        )
    }
    return accept(reading.value)
}

/** 권한·오류 사유는 TTL freshness와 따로 둔다. 신선한 TTL은 추가 사유가 아니다. */
private fun statusUnusable(reason: UnusableReason, freshness: Freshness): Channel<Nothing> {
    return Channel.Unusable(reason, freshness)
}
