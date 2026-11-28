package io.github.scarlel96.aura.cache

/** Supply a classified failure from the adapter. Do not infer authority from a transport code. */
enum class ProviderFailure {
    OFFLINE, TIMEOUT, CONNECTION_LOST, RATE_LIMITED, SERVER_TEMPORARY,
    AUTHORITY_DENIED, INVALID_RESPONSE, SECURITY_FAILURE, PERMANENT, UNKNOWN,
}

sealed interface FailureAction {
    data object WaitForConnectivity : FailureAction
    data class Complete(val outcome: AttemptOutcome.Failure) : FailureAction
}

sealed interface DelayHint {
    data object Absent : DelayHint
    data class Millis(val value: Long) : DelayHint
    data object Invalid : DelayHint
}

/**
 * Parse a bounded decimal delta in seconds. Require ASCII digits.
 * The adapter removes HTTP field whitespace and rejects duplicate headers.
 * Do not parse HTTP dates here. Treat unsupported or malformed hints as invalid.
 */
fun parseRetryDelaySeconds(raw: String?): DelayHint {
    if (raw == null) return DelayHint.Absent
    if (raw.length !in 1..19) return DelayHint.Invalid
    var seconds = 0L
    val cap = Long.MAX_VALUE / 1000
    for (ch in raw) {
        if (ch !in '0'..'9') return DelayHint.Invalid
        val digit = ch - '0'
        if (seconds > (cap - digit) / 10) return DelayHint.Invalid
        seconds = seconds * 10 + digit
    }
    return DelayHint.Millis(seconds * 1000)
}

/**
 * Map a classified failure to a recovery action. Preserve denial and security failure.
 * A connectivity wait does not reset an active episode. The adapter owns cancellation.
 * Only retryable failures accept a delay hint. Never ignore an invalid hint for a retry.
 */
fun classifyProviderFailure(failure: ProviderFailure, retryAfterSeconds: String? = null): FailureAction {
    if (failure == ProviderFailure.OFFLINE) return FailureAction.WaitForConnectivity
    val kind = when (failure) {
        ProviderFailure.TIMEOUT, ProviderFailure.CONNECTION_LOST, ProviderFailure.SERVER_TEMPORARY -> RetryFailure.TRANSIENT_TRANSPORT
        ProviderFailure.RATE_LIMITED -> RetryFailure.RATE_LIMITED
        ProviderFailure.AUTHORITY_DENIED -> RetryFailure.AUTHORITY_DENIED
        ProviderFailure.INVALID_RESPONSE -> RetryFailure.INVALID_RESPONSE
        ProviderFailure.SECURITY_FAILURE, ProviderFailure.PERMANENT -> RetryFailure.PERMANENT
        else -> RetryFailure.UNKNOWN
    }
    if (kind != RetryFailure.TRANSIENT_TRANSPORT && kind != RetryFailure.RATE_LIMITED) {
        return FailureAction.Complete(AttemptOutcome.Failure(kind))
    }
    val hint = when (val parsed = parseRetryDelaySeconds(retryAfterSeconds)) {
        DelayHint.Absent -> null
        is DelayHint.Millis -> parsed.value
        DelayHint.Invalid -> return FailureAction.Complete(AttemptOutcome.Failure(RetryFailure.INVALID_RESPONSE))
    }
    return FailureAction.Complete(AttemptOutcome.Failure(kind, hint))
}
