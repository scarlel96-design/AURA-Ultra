package io.github.scarlel96.aura.intelligence

import io.github.scarlel96.aura.domain.DomainParse
import io.github.scarlel96.aura.domain.Observation
import io.github.scarlel96.aura.domain.ObservationKind
import io.github.scarlel96.aura.domain.ObservationStatus
import io.github.scarlel96.aura.domain.SourceId
import java.time.Duration
import java.time.Instant

internal val origin: Instant = Instant.parse("2026-11-28T00:00:00Z")

internal val sensorSource: SourceId = when (val parsed = SourceId.parse("gb02.sensor")) {
    is DomainParse.Accepted -> parsed.value
    is DomainParse.Rejected -> error(parsed.code)
}

internal fun at(seconds: Long): Instant = origin.plusSeconds(seconds)

internal fun <T> reading(
    value: T?,
    unit: String,
    status: ObservationStatus = ObservationStatus.VALID,
    expiresAt: Instant? = origin.plusSeconds(3600),
    observedAt: Instant? = origin.minusSeconds(10),
    receivedAt: Instant = origin.minusSeconds(10),
): Observation<T> {
    return Observation(
        value,
        unit,
        sensorSource,
        observedAt,
        receivedAt,
        expiresAt,
        status,
        ObservationKind.OBSERVED,
    )
}

internal fun openPolicy(
    hold: Duration = Duration.ZERO,
    debounce: Duration = Duration.ZERO,
): PolicyCandidates {
    return PolicyCandidates.documented().copy(minimumHold = hold, debounce = debounce)
}

internal fun sample(
    moment: Instant = origin,
    battery: Observation<Double>? = null,
    charging: Observation<Boolean>? = null,
    precipitation: Observation<Double>? = null,
    alert: Observation<Boolean>? = null,
    activity: Observation<String>? = null,
    light: Observation<String>? = null,
    connectivity: Observation<String>? = null,
    userMode: Observation<String>? = null,
    motionReduction: Boolean = false,
    ambientDisplay: Boolean = false,
): IntelligenceSample {
    return IntelligenceSample(
        referenceTime = moment,
        batteryPercent = battery,
        charging = charging,
        precipitationProbability = precipitation,
        weatherAlert = alert,
        activity = activity,
        light = light,
        connectivity = connectivity,
        userMode = userMode,
        motionReduction = motionReduction,
        ambientDisplay = ambientDisplay,
    )
}
