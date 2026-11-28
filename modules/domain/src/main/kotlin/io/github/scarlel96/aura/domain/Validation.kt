package io.github.scarlel96.aura.domain

enum class IssueCode {
    UNIT_BLANK,
    UNIT_PADDED,
    UNIT_CONTROL,
    UNIT_MISMATCH,
    VALUE_REQUIRED,
    VALUE_FORBIDDEN,
    EXPIRES_BEFORE_OBSERVED,
    NON_FINITE,
    RANGE_BELOW,
    RANGE_ABOVE,
    CONSTRAINT_TYPE_MISMATCH,
    CONSTRAINT_CONFLICT,
    FUTURE_OBSERVED_AT,
    FUTURE_RECEIVED_AT,
    REFERENCE_TIME_REQUIRED,
    SOURCE_KEY_MISMATCH,
    UNSUPPORTED_PAYLOAD,
    KIND_MISMATCH,
    LOCATION_ID_BLANK,
    VALIDITY_WINDOW_INVERTED,
    VALIDITY_WINDOW_EMPTY,
    TOKEN_BLANK,
}

data class ValidationIssue(
    val code: IssueCode,
    val message: String,
    val subject: String? = null,
)

data class ValidationReport(
    val issues: List<ValidationIssue>,
) {
    val accepted: Boolean get() = issues.isEmpty()
}

fun <T> validateObservation(
    observation: Observation<T>,
    constraints: ObservationConstraints<T> = ObservationConstraints(),
    subject: String? = null,
): ValidationReport {
    val issues = structuralIssues(observation, subject) + constraintIssues(observation, constraints, subject)
    return ValidationReport(issues)
}

private fun <T> structuralIssues(observation: Observation<T>, subject: String?): List<ValidationIssue> {
    val issues = mutableListOf<ValidationIssue>()
    val current = observation.value
    when (observation.status) {
        ObservationStatus.VALID, ObservationStatus.STALE -> {
            if (current == null) {
                issues += issue(IssueCode.VALUE_REQUIRED, "VALID와 STALE은 값이 필요하다. 누락은 UNAVAILABLE이다.", subject)
            }
        }
        ObservationStatus.UNAVAILABLE, ObservationStatus.DENIED, ObservationStatus.ERROR -> {
            if (current != null) {
                issues += issue(IssueCode.VALUE_FORBIDDEN, "UNAVAILABLE, DENIED, ERROR는 값을 가질 수 없다.", subject)
            }
        }
    }
    if (current != null) {
        when {
            observation.unit.isBlank() ->
                issues += issue(IssueCode.UNIT_BLANK, "값이 있으면 단위가 필요하다.", subject)
            else -> {
                if (observation.unit.any { it.isWhitespace() }) {
                    issues += issue(IssueCode.UNIT_PADDED, "단위에 공백을 포함하지 않는다.", subject)
                }
                if (observation.unit.any { it.isISOControl() && !it.isWhitespace() }) {
                    issues += issue(IssueCode.UNIT_CONTROL, "단위에 제어 문자를 포함하지 않는다.", subject)
                }
            }
        }
        if ((current is Double && !current.isFinite()) || (current is Float && !current.isFinite())) {
            issues += issue(IssueCode.NON_FINITE, "유한하지 않은 부동소수는 측정값이 아니다.", subject)
        }
        if (!isStableScalar(current)) {
            issues += issue(
                IssueCode.UNSUPPORTED_PAYLOAD,
                "지원하는 불변 스칼라가 아니면 승인 상태에 넣지 않는다.",
                subject,
            )
        }
    }
    val observedAt = observation.observedAt
    val expiresAt = observation.expiresAt
    if (observedAt != null && expiresAt != null && expiresAt < observedAt) {
        issues += issue(IssueCode.EXPIRES_BEFORE_OBSERVED, "만료 시각이 관측 시각보다 앞설 수 없다.", subject)
    }
    return issues
}

private fun <T> constraintIssues(
    observation: Observation<T>,
    constraints: ObservationConstraints<T>,
    subject: String?,
): List<ValidationIssue> {
    val issues = mutableListOf<ValidationIssue>()
    val expectedUnit = constraints.expectedUnit
    if (observation.value != null && expectedUnit != null && observation.unit != expectedUnit) {
        issues += issue(IssueCode.UNIT_MISMATCH, "단위가 기대한 토큰과 다르다. 단위 환산은 하지 않는다.", subject)
    }
    if (constraints.doubleRange != null && constraints.longRange != null) {
        issues += issue(IssueCode.CONSTRAINT_CONFLICT, "부동소수 범위와 정수 범위를 동시에 적용하지 않는다.", subject)
    } else {
        val current = observation.value
        if (current != null) {
            issues += rangeIssues(current, constraints, subject)
        }
    }
    when (constraints.futureTimestamp) {
        FutureTimestampPolicy.UNCHECKED -> Unit
        FutureTimestampPolicy.REJECT_AFTER_REFERENCE -> {
            val referenceTime = constraints.referenceTime
            if (referenceTime == null) {
                issues += issue(IssueCode.REFERENCE_TIME_REQUIRED, "미래 시각 정책에는 호출자가 기준 시각을 전달해야 한다.", subject)
            } else {
                val observedAt = observation.observedAt
                if (observedAt != null && observedAt > referenceTime) {
                    issues += issue(IssueCode.FUTURE_OBSERVED_AT, "관측 시각이 기준 시각보다 미래다.", subject)
                }
                if (observation.receivedAt > referenceTime) {
                    issues += issue(IssueCode.FUTURE_RECEIVED_AT, "수신 시각이 기준 시각보다 미래다.", subject)
                }
            }
        }
    }
    return issues
}

private fun rangeIssues(value: Any, constraints: ObservationConstraints<*>, subject: String?): List<ValidationIssue> {
    val doubleRange = constraints.doubleRange
    if (doubleRange != null) {
        val numeric = when (value) {
            is Double -> value
            is Float -> value.toDouble()
            else -> return listOf(issue(IssueCode.CONSTRAINT_TYPE_MISMATCH, "이 값 형식에는 부동소수 범위를 적용하지 않는다.", subject))
        }
        if (!numeric.isFinite()) {
            return emptyList()
        }
        return doubleViolation(numeric, doubleRange, subject)
    }
    val longRange = constraints.longRange
    if (longRange != null) {
        val numeric = when (value) {
            is Byte -> value.toLong()
            is Short -> value.toLong()
            is Int -> value.toLong()
            is Long -> value
            else -> return listOf(issue(IssueCode.CONSTRAINT_TYPE_MISMATCH, "이 값 형식에는 정수 범위를 적용하지 않는다.", subject))
        }
        return longViolation(numeric, longRange, subject)
    }
    return emptyList()
}

private fun doubleViolation(value: Double, range: NumericRange, subject: String?): List<ValidationIssue> {
    val minimum = range.minimum
    if (minimum != null) {
        val below = if (range.minimumInclusive) value < minimum else value <= minimum
        if (below) {
            return listOf(issue(IssueCode.RANGE_BELOW, "값이 하한보다 작다.", subject))
        }
    }
    val maximum = range.maximum
    if (maximum != null) {
        val above = if (range.maximumInclusive) value > maximum else value >= maximum
        if (above) {
            return listOf(issue(IssueCode.RANGE_ABOVE, "값이 상한보다 크다.", subject))
        }
    }
    return emptyList()
}

private fun longViolation(value: Long, range: LongBounds, subject: String?): List<ValidationIssue> {
    val minimum = range.minimum
    if (minimum != null) {
        val below = if (range.minimumInclusive) value < minimum else value <= minimum
        if (below) {
            return listOf(issue(IssueCode.RANGE_BELOW, "값이 하한보다 작다.", subject))
        }
    }
    val maximum = range.maximum
    if (maximum != null) {
        val above = if (range.maximumInclusive) value > maximum else value >= maximum
        if (above) {
            return listOf(issue(IssueCode.RANGE_ABOVE, "값이 상한보다 크다.", subject))
        }
    }
    return emptyList()
}

internal fun issue(code: IssueCode, message: String, subject: String?): ValidationIssue {
    return ValidationIssue(code, message, subject)
}
