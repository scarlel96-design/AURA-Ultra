package io.github.scarlel96.aura.domain

import java.time.Instant
import kotlin.test.assertIs

fun acceptedSource(raw: String = "fixture.source"): SourceId {
    val parsed = SourceId.parse(raw)
    assertIs<DomainParse.Accepted<SourceId>>(parsed)
    return parsed.value
}

fun acceptedKey(source: SourceId = acceptedSource(), subject: String = "fixture.subject"): ObservationKey {
    val parsed = observationKey(source, subject)
    assertIs<DomainParse.Accepted<ObservationKey>>(parsed)
    return parsed.value
}

fun <T> observation(
    value: T?,
    unit: String = "fixture",
    source: SourceId = acceptedSource(),
    observedAt: Instant? = Instant.parse("2026-11-27T00:00:00Z"),
    receivedAt: Instant = Instant.parse("2026-11-27T00:00:01Z"),
    expiresAt: Instant? = Instant.parse("2026-11-27T01:00:00Z"),
    status: ObservationStatus = ObservationStatus.VALID,
    kind: ObservationKind = ObservationKind.OBSERVED,
): Observation<T> {
    return Observation(value, unit, source, observedAt, receivedAt, expiresAt, status, kind)
}

fun List<ValidationIssue>.codes(): List<IssueCode> = map { it.code }

fun ValidationReport.codes(): List<IssueCode> = issues.codes()

fun acceptedDoubleRange(
    minimum: Double? = null,
    maximum: Double? = null,
    minimumInclusive: Boolean = true,
    maximumInclusive: Boolean = true,
): NumericRange {
    val parsed = NumericRange.parse(minimum, maximum, minimumInclusive, maximumInclusive)
    assertIs<DomainParse.Accepted<NumericRange>>(parsed)
    return parsed.value
}

fun acceptedLongRange(
    minimum: Long? = null,
    maximum: Long? = null,
    minimumInclusive: Boolean = true,
    maximumInclusive: Boolean = true,
): LongBounds {
    val parsed = LongBounds.parse(minimum, maximum, minimumInclusive, maximumInclusive)
    assertIs<DomainParse.Accepted<LongBounds>>(parsed)
    return parsed.value
}
