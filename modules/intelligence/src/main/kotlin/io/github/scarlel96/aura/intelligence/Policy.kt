package io.github.scarlel96.aura.intelligence

import java.time.Duration

/** 공백, NUL, 제어문자가 섞인 단위 토큰은 합의된 단위가 아니다. */
internal fun String.isAbnormalUnitToken(): Boolean {
    return isEmpty() || any { it.isWhitespace() || it.isISOControl() }
}

/**
 * 문서에 적힌 후보 값이다. 제품이 승인한 상수가 아니다.
 * 호출자가 다른 값을 넣어 같은 규칙을 시험할 수 있다.
 */
data class PolicyCandidates(
    val powerEnterPercent: Double,
    val powerExitPercent: Double,
    val precipEnter: Double,
    val precipExit: Double,
    val percentUnit: String,
    val probabilityUnit: String,
    val tokenUnit: String,
    val flagUnit: String,
    val minimumHold: Duration,
    val debounce: Duration,
    val percentMinimum: Double,
    val percentMaximum: Double,
    val probabilityMinimum: Double,
    val probabilityMaximum: Double,
) {
    fun issues(): List<String> {
        val issues = mutableListOf<String>()
        if (!powerEnterPercent.isFinite() || !powerExitPercent.isFinite()) {
            issues += "power thresholds must be finite"
        } else if (powerEnterPercent >= powerExitPercent) {
            issues += "power enter must be below power exit"
        }
        if (!precipEnter.isFinite() || !precipExit.isFinite()) {
            issues += "precipitation thresholds must be finite"
        } else if (precipEnter <= precipExit) {
            issues += "precipitation enter must be above precipitation exit"
        }
        if (powerEnterPercent.isFinite() && powerExitPercent.isFinite() &&
            percentMinimum.isFinite() && percentMaximum.isFinite() &&
            percentMinimum <= percentMaximum &&
            (powerEnterPercent < percentMinimum || powerEnterPercent > percentMaximum ||
                powerExitPercent < percentMinimum || powerExitPercent > percentMaximum)
        ) {
            issues += "power thresholds must lie inside the percent scale"
        }
        if (precipEnter.isFinite() && precipExit.isFinite() &&
            probabilityMinimum.isFinite() && probabilityMaximum.isFinite() &&
            probabilityMinimum <= probabilityMaximum &&
            (precipEnter < probabilityMinimum || precipEnter > probabilityMaximum ||
                precipExit < probabilityMinimum || precipExit > probabilityMaximum)
        ) {
            issues += "precipitation thresholds must lie inside the probability scale"
        }
        if (minimumHold.isNegative || debounce.isNegative) {
            issues += "durations must not be negative"
        }
        if (!percentMinimum.isFinite() || !percentMaximum.isFinite() || percentMinimum > percentMaximum) {
            issues += "percent scale is not usable"
        }
        if (!probabilityMinimum.isFinite() || !probabilityMaximum.isFinite() || probabilityMinimum > probabilityMaximum) {
            issues += "probability scale is not usable"
        }
        if (
            percentUnit.isAbnormalUnitToken() ||
            probabilityUnit.isAbnormalUnitToken() ||
            tokenUnit.isAbnormalUnitToken() ||
            flagUnit.isAbnormalUnitToken()
        ) {
            issues += "unit tokens must not contain whitespace or control characters"
        }
        return issues
    }

    companion object {
        fun documented(): PolicyCandidates {
            return PolicyCandidates(
                powerEnterPercent = 15.0,
                powerExitPercent = 20.0,
                precipEnter = 70.0,
                precipExit = 50.0,
                percentUnit = "percent",
                probabilityUnit = "percent",
                tokenUnit = "token",
                flagUnit = "flag",
                minimumHold = Duration.ofSeconds(60),
                debounce = Duration.ZERO,
                percentMinimum = 0.0,
                percentMaximum = 100.0,
                probabilityMinimum = 0.0,
                probabilityMaximum = 100.0,
            )
        }
    }
}
