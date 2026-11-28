package io.github.scarlel96.aura.domain

data class ObservationKey(
    val source: SourceId,
    val subject: String,
)

fun observationKey(source: SourceId, subject: String): DomainParse<ObservationKey> {
    return when (val token = parseToken(subject)) {
        is DomainParse.Rejected -> token
        is DomainParse.Accepted -> DomainParse.Accepted(ObservationKey(source, token.value))
    }
}

class UnsupportedPayloadException : IllegalArgumentException(IssueCode.UNSUPPORTED_PAYLOAD.name)

data class RevisionCursor<T>(
    val key: ObservationKey,
    val revision: Long,
    val observation: Observation<T>,
) {
    init {
        if (!isStableScalar(observation.value)) {
            throw UnsupportedPayloadException()
        }
    }
}

enum class RevisionOutcome {
    ACCEPTED,
    DUPLICATE,
    DUPLICATE_CONFLICT,
    SUPERSEDED_REJECTED,
    KEY_MISMATCH,
    INVALID_KEY,
    INVALID_OBSERVATION,
}

data class RevisionDecision<T>(
    val outcome: RevisionOutcome,
    val cursor: RevisionCursor<T>?,
    val receiveTimeInversion: Boolean,
    val issues: List<ValidationIssue>,
)

/**
 * 더 큰 revision만 반영한다. 같은 revision은 먼저 수락한 관측을 유지한다.
 * 페이로드가 같으면 DUPLICATE, 다르면 DUPLICATE_CONFLICT다. 수신 시각만 달라도 덮어쓰지 않는다.
 * revision이 더 큰데 수신 시각이 되돌아가면 수락하고 [RevisionDecision.receiveTimeInversion]을 남긴다.
 * 간격은 허용한다. 비교는 부호 있는 64비트 정수다.
 */
fun <T> applyRevision(
    current: RevisionCursor<T>?,
    key: ObservationKey,
    revision: Long,
    incoming: Observation<T>,
    constraints: ObservationConstraints<T> = ObservationConstraints(),
): RevisionDecision<T> {
    if (parseToken(key.subject) is DomainParse.Rejected) {
        return RevisionDecision(RevisionOutcome.INVALID_KEY, current, receiveTimeInversion = false, issues = emptyList())
    }
    if (current != null && current.key != key) {
        return RevisionDecision(RevisionOutcome.KEY_MISMATCH, current, receiveTimeInversion = false, issues = emptyList())
    }
    val issues = validateObservation(incoming, constraints).issues.toMutableList()
    if (incoming.source != key.source) {
        issues += issue(IssueCode.SOURCE_KEY_MISMATCH, "관측의 출처가 스트림 키와 다르다.", subject = null)
    }
    if (issues.isNotEmpty()) {
        return RevisionDecision(RevisionOutcome.INVALID_OBSERVATION, current, receiveTimeInversion = false, issues = issues)
    }
    if (current == null) {
        return RevisionDecision(
            outcome = RevisionOutcome.ACCEPTED,
            cursor = RevisionCursor(key, revision, incoming),
            receiveTimeInversion = false,
            issues = emptyList(),
        )
    }
    val inversion = incoming.receivedAt < current.observation.receivedAt
    return when {
        revision > current.revision -> RevisionDecision(
            outcome = RevisionOutcome.ACCEPTED,
            cursor = RevisionCursor(key, revision, incoming),
            receiveTimeInversion = inversion,
            issues = emptyList(),
        )
        revision == current.revision && samePayload(incoming, current.observation) -> RevisionDecision(
            outcome = RevisionOutcome.DUPLICATE,
            cursor = current,
            receiveTimeInversion = inversion,
            issues = emptyList(),
        )
        revision == current.revision -> RevisionDecision(
            outcome = RevisionOutcome.DUPLICATE_CONFLICT,
            cursor = current,
            receiveTimeInversion = inversion,
            issues = emptyList(),
        )
        else -> RevisionDecision(
            outcome = RevisionOutcome.SUPERSEDED_REJECTED,
            cursor = current,
            receiveTimeInversion = inversion,
            issues = emptyList(),
        )
    }
}
