package io.github.scarlel96.aura.domain

import java.time.Instant

enum class Freshness {
    FRESH,
    EXPIRED,
    UNDECLARED,
}

/**
 * 만료 경계. [EXPIRED_AT_OR_AFTER]에서는 referenceTime < expiresAt 일 때만 신선하다.
 * referenceTime == expiresAt 은 만료다. 제품 상수로 승인된 값은 아니다.
 */
enum class ExpiryBoundary {
    EXPIRED_AT_OR_AFTER,
}

fun freshnessOf(
    expiresAt: Instant?,
    referenceTime: Instant,
    boundary: ExpiryBoundary = ExpiryBoundary.EXPIRED_AT_OR_AFTER,
): Freshness {
    if (expiresAt == null) {
        return Freshness.UNDECLARED
    }
    return when (boundary) {
        ExpiryBoundary.EXPIRED_AT_OR_AFTER ->
            if (referenceTime < expiresAt) Freshness.FRESH else Freshness.EXPIRED
    }
}

sealed class StatusDerivation<T> {
    abstract val observation: Observation<T>

    data class Unchanged<T>(
        override val observation: Observation<T>,
        val freshness: Freshness,
    ) : StatusDerivation<T>() {
        init {
            requireStablePayload(observation.value)
        }
    }

    data class DegradedToStale<T>(
        override val observation: Observation<T>,
        val freshness: Freshness,
    ) : StatusDerivation<T>() {
        init {
            requireStablePayload(observation.value)
        }
    }

    data class Rejected<T>(
        override val observation: Observation<T>,
        val issues: List<ValidationIssue>,
    ) : StatusDerivation<T>()
}

/**
 * 호출자가 [referenceTime]을 전달한다. 시스템 시계를 읽지 않는다.
 * VALID가 만료됐을 때만 STALE 사본을 만든다. STALE, ERROR, DENIED, UNAVAILABLE은 올리지 않는다.
 * 입력은 바꾸지 않는다. 오류 상태를 정상 값으로 바꾸지 않는다.
 */
fun <T> deriveStatus(
    observation: Observation<T>,
    referenceTime: Instant,
    boundary: ExpiryBoundary = ExpiryBoundary.EXPIRED_AT_OR_AFTER,
): StatusDerivation<T> {
    val report = validateObservation(observation)
    if (!report.accepted) {
        return StatusDerivation.Rejected(observation, report.issues)
    }
    val freshness = freshnessOf(observation.expiresAt, referenceTime, boundary)
    if (observation.status == ObservationStatus.VALID && freshness == Freshness.EXPIRED) {
        return StatusDerivation.DegradedToStale(
            observation.copy(status = ObservationStatus.STALE),
            freshness,
        )
    }
    return StatusDerivation.Unchanged(observation, freshness)
}
