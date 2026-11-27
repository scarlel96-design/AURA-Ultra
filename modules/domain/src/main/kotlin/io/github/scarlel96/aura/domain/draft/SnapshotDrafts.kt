package io.github.scarlel96.aura.domain.draft

import io.github.scarlel96.aura.domain.IssueCode
import io.github.scarlel96.aura.domain.Observation
import io.github.scarlel96.aura.domain.ObservationKind
import io.github.scarlel96.aura.domain.ValidationIssue
import io.github.scarlel96.aura.domain.ValidationReport
import io.github.scarlel96.aura.domain.issue
import io.github.scarlel96.aura.domain.validateObservation
import java.time.Instant

/**
 * DATA_INTELLIGENCE에 이름이 있는 필드만 담는 초안이다.
 * 생략 기호로 남은 필드는 추가하지 않는다. 예보를 계산하지 않는다.
 * [validFrom]과 [validTo]는 예보 유효 구간이다. [Observation.observedAt]과 같지 않다.
 */
data class WeatherSnapshotDraft(
    val locationId: String?,
    val issuedAt: Instant?,
    val validFrom: Instant?,
    val validTo: Instant?,
    val probability: Observation<Double>?,
    val observedRain: Observation<Double>?,
    val forecastRain: Observation<Double>?,
)

/**
 * 축의 토큰 목록과 dataQuality 집계 규칙은 미확정이다.
 * null은 없음이다. 빈 문자열과 앞뒤 공백은 거절한다.
 * 문자 "0"은 누락 표식으로 예약하지 않는다. 어휘가 없기 때문이다.
 */
data class ContextSnapshotDraft(
    val weather: WeatherSnapshotDraft?,
    val activity: String?,
    val power: String?,
    val timeOfDay: String?,
    val connectivity: String?,
    val userMode: String?,
    val dataQuality: String?,
)

/**
 * focus, paletteId, quality, reasonCodes의 어휘는 미확정이다.
 * [revision]이 null이면 아직 없는 것이고 0이 아니다. FSM을 실행하지 않는다.
 */
data class PresentationIntentDraft(
    val focus: String?,
    val paletteId: String?,
    val quality: String?,
    val motionAllowed: Boolean?,
    val reasonCodes: List<String>?,
    val revision: Long?,
)

fun validateWeatherSnapshotDraft(draft: WeatherSnapshotDraft): ValidationReport {
    val issues = mutableListOf<ValidationIssue>()
    rejectBlank(draft.locationId, IssueCode.LOCATION_ID_BLANK, "locationId", issues)
    val validFrom = draft.validFrom
    val validTo = draft.validTo
    if (validFrom != null && validTo != null) {
        when {
            validTo < validFrom ->
                issues += issue(IssueCode.VALIDITY_WINDOW_INVERTED, "예보 유효 종료가 시작보다 앞선다.", "validTo")
            validTo == validFrom ->
                issues += issue(IssueCode.VALIDITY_WINDOW_EMPTY, "예보 유효 구간의 길이가 0이다.", "validTo")
        }
    }
    draft.probability?.let { issues += validateObservation(it, subject = "probability").issues }
    draft.observedRain?.let {
        issues += validateObservation(it, subject = "observedRain").issues
        if (it.kind != ObservationKind.OBSERVED) {
            issues += issue(IssueCode.KIND_MISMATCH, "observedRain의 kind는 OBSERVED여야 한다.", "observedRain")
        }
    }
    draft.forecastRain?.let {
        issues += validateObservation(it, subject = "forecastRain").issues
        if (it.kind != ObservationKind.FORECAST) {
            issues += issue(IssueCode.KIND_MISMATCH, "forecastRain의 kind는 FORECAST여야 한다.", "forecastRain")
        }
    }
    return ValidationReport(issues)
}

fun validateContextSnapshotDraft(draft: ContextSnapshotDraft): ValidationReport {
    val issues = mutableListOf<ValidationIssue>()
    draft.weather?.let { issues += validateWeatherSnapshotDraft(it).issues }
    rejectBlank(draft.activity, IssueCode.TOKEN_BLANK, "activity", issues)
    rejectBlank(draft.power, IssueCode.TOKEN_BLANK, "power", issues)
    rejectBlank(draft.timeOfDay, IssueCode.TOKEN_BLANK, "timeOfDay", issues)
    rejectBlank(draft.connectivity, IssueCode.TOKEN_BLANK, "connectivity", issues)
    rejectBlank(draft.userMode, IssueCode.TOKEN_BLANK, "userMode", issues)
    rejectBlank(draft.dataQuality, IssueCode.TOKEN_BLANK, "dataQuality", issues)
    return ValidationReport(issues)
}

fun validatePresentationIntentDraft(draft: PresentationIntentDraft): ValidationReport {
    val issues = mutableListOf<ValidationIssue>()
    rejectBlank(draft.focus, IssueCode.TOKEN_BLANK, "focus", issues)
    rejectBlank(draft.paletteId, IssueCode.TOKEN_BLANK, "paletteId", issues)
    rejectBlank(draft.quality, IssueCode.TOKEN_BLANK, "quality", issues)
    draft.reasonCodes?.forEachIndexed { index, code ->
        rejectBlank(code, IssueCode.TOKEN_BLANK, "reasonCodes[$index]", issues)
    }
    return ValidationReport(issues)
}

private fun rejectBlank(
    value: String?,
    code: IssueCode,
    subject: String,
    issues: MutableList<ValidationIssue>,
) {
    if (value == null) {
        return
    }
    if (value.isBlank() || value != value.trim()) {
        issues += issue(code, "비어 있거나 공백으로 둘러싼 토큰은 값이 아니다.", subject)
    }
}
