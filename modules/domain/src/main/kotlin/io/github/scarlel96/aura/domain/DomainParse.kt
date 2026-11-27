package io.github.scarlel96.aura.domain

enum class ParseCode {
    BLANK,
    PADDED,
    CONTROL_CHARACTER,
    RANGE_EMPTY,
    RANGE_INVERTED,
    NON_FINITE_BOUND,
}

sealed class DomainParse<out T> {
    data class Accepted<T>(val value: T) : DomainParse<T>()
    data class Rejected(val code: ParseCode) : DomainParse<Nothing>()
}

fun parseToken(raw: String): DomainParse<String> {
    if (raw.isBlank()) {
        return DomainParse.Rejected(ParseCode.BLANK)
    }
    if (raw != raw.trim()) {
        return DomainParse.Rejected(ParseCode.PADDED)
    }
    if (raw.any { it.isISOControl() }) {
        return DomainParse.Rejected(ParseCode.CONTROL_CHARACTER)
    }
    return DomainParse.Accepted(raw)
}
