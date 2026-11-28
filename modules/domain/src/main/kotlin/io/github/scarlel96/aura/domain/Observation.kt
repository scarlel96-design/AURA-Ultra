package io.github.scarlel96.aura.domain

import java.time.Instant

enum class ObservationStatus {
    VALID,
    STALE,
    UNAVAILABLE,
    DENIED,
    ERROR,
}

enum class ObservationKind {
    OBSERVED,
    FORECAST,
    ESTIMATED,
    SYSTEM,
}

data class Observation<T>(
    val value: T?,
    val unit: String,
    val source: SourceId,
    val observedAt: Instant?,
    val receivedAt: Instant,
    val expiresAt: Instant?,
    val status: ObservationStatus,
    val kind: ObservationKind,
)

sealed class ClassifiedValue<out T> {
    data class Reading<T>(val value: T, val status: ObservationStatus) : ClassifiedValue<T>()
    data object Unavailable : ClassifiedValue<Nothing>()
    data object Denied : ClassifiedValue<Nothing>()
    data object Failed : ClassifiedValue<Nothing>()
    data class Inconsistent(val status: ObservationStatus, val valuePresent: Boolean) : ClassifiedValue<Nothing>()
}

/**
 * TTL은 적용하지 않는다. 누락·거부·오류를 0으로 바꾸지 않는다.
 * 상태와 값이 어긋나거나 유한하지 않은 부동소수면 [ClassifiedValue.Inconsistent]다.
 */
fun <T> Observation<T>.classifiedValue(): ClassifiedValue<T> {
    val current = value
    if (!isStableScalar(current)) {
        return ClassifiedValue.Inconsistent(status, valuePresent = true)
    }
    if ((current is Double && !current.isFinite()) || (current is Float && !current.isFinite())) {
        return ClassifiedValue.Inconsistent(status, valuePresent = true)
    }
    return when (status) {
        ObservationStatus.VALID, ObservationStatus.STALE ->
            if (current != null) {
                ClassifiedValue.Reading(current, status)
            } else {
                ClassifiedValue.Inconsistent(status, valuePresent = false)
            }
        ObservationStatus.UNAVAILABLE ->
            if (current == null) {
                ClassifiedValue.Unavailable
            } else {
                ClassifiedValue.Inconsistent(status, valuePresent = true)
            }
        ObservationStatus.DENIED ->
            if (current == null) {
                ClassifiedValue.Denied
            } else {
                ClassifiedValue.Inconsistent(status, valuePresent = true)
            }
        ObservationStatus.ERROR ->
            if (current == null) {
                ClassifiedValue.Failed
            } else {
                ClassifiedValue.Inconsistent(status, valuePresent = true)
            }
    }
}

/**
 * 승인 상태에 남길 수 있는 값. null과 JVM 불변 스칼라만 해당한다.
 * 읽기 전용 컬렉션 인터페이스도 포함하지 않는다.
 */
internal fun isStableScalar(value: Any?): Boolean {
    return when (value) {
        null -> true
        is Boolean, is Byte, is Short, is Int, is Long, is Float, is Double, is Char, is String -> true
        else -> false
    }
}

/** 중복 비교용 페이로드. 수신 시각은 로컬 수신 시각이라 제외한다. */
fun <T> samePayload(left: Observation<T>, right: Observation<T>): Boolean {
    return left.value == right.value &&
        left.unit == right.unit &&
        left.source == right.source &&
        left.observedAt == right.observedAt &&
        left.expiresAt == right.expiresAt &&
        left.status == right.status &&
        left.kind == right.kind
}
