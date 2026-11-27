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

    data class Unusable(val reason: UnusableReason) : Channel<Nothing>()

    data class Fresh<T>(val value: T) : Channel<T>()
}

fun gateDouble(
    observation: Observation<Double>?,
    referenceTime: Instant,
    expectedUnit: String,
    minimum: Double,
    maximum: Double,
): Channel<Double> {
    val gated = gateReading(observation, referenceTime, expectedUnit) { value ->
        if (value < minimum || value > maximum) {
            Channel.Unusable(UnusableReason.OUTSIDE_CANDIDATE_SCALE)
        } else {
            Channel.Fresh(value)
        }
    }
    return gated
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
    val derived = deriveStatus(observation, referenceTime)
    when (derived) {
        is StatusDerivation.Rejected -> return Channel.Unusable(UnusableReason.REJECTED)
        is StatusDerivation.DegradedToStale -> return Channel.Unusable(UnusableReason.STALE)
        is StatusDerivation.Unchanged -> {
            when (derived.freshness) {
                Freshness.UNDECLARED -> return Channel.Unusable(UnusableReason.UNDECLARED)
                Freshness.EXPIRED -> return Channel.Unusable(UnusableReason.STALE)
                Freshness.FRESH -> Unit
            }
        }
    }
    val current = derived.observation
    val classified = current.classifiedValue()
    val reading = when (classified) {
        is ClassifiedValue.Reading<T> -> classified
        ClassifiedValue.Unavailable -> return Channel.Unusable(UnusableReason.UNAVAILABLE)
        ClassifiedValue.Denied -> return Channel.Unusable(UnusableReason.DENIED)
        ClassifiedValue.Failed -> return Channel.Unusable(UnusableReason.ERROR)
        is ClassifiedValue.Inconsistent -> return Channel.Unusable(UnusableReason.INCONSISTENT)
    }
    if (reading.status != ObservationStatus.VALID) {
        return Channel.Unusable(UnusableReason.STALE)
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
