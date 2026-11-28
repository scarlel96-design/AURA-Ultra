package io.github.scarlel96.aura.cache

/** Candidate settings. The adapter supplies values; no production defaults are implied. */
data class RetryPolicy(
    val baseDelayMillis: Long,
    val maxDelayMillis: Long,
    val maxRetries: Int,
) {
    init {
        require(baseDelayMillis > 0)
        require(maxDelayMillis >= baseDelayMillis)
        require(maxRetries >= 0)
    }
}

/** Classify failures outside the planner. Do not infer permission from a retry decision. */
enum class RetryFailure {
    TRANSIENT_TRANSPORT, RATE_LIMITED, PERMANENT, INVALID_RESPONSE, AUTHORITY_DENIED, UNKNOWN,
}

enum class RetryStop {
    INVALID_INPUT, DISABLED, NOT_RETRYABLE, RETRY_BUDGET, DELAY_LIMIT, DEADLINE, TICK_OVERFLOW,
}

sealed interface RetryDecision {
    data class RetryAt(val tickMillis: Long, val delayMillis: Long, val retryNumber: Int) : RetryDecision
    data class Stop(val reason: RetryStop) : RetryDecision
}

/**
 * Calculate a candidate retry time in one monotonic clock session.
 * Count the first failed attempt as failure 1. The caller owns the counter.
 * Treat deadlineExclusive as the first prohibited start tick.
 * Pass a nonnegative relative server delay, not an HTTP date.
 * This function does not schedule requests, authorize data, or retain results.
 */
fun planRetry(
    policy: RetryPolicy,
    failure: RetryFailure,
    consecutiveFailures: Int,
    nowTickMillis: Long,
    deadlineExclusive: Long,
    retryAfterMillis: Long? = null,
    jitterMillis: Long = 0,
    automaticRetryEnabled: Boolean = true,
): RetryDecision {
    if (consecutiveFailures <= 0 || nowTickMillis < 0 || deadlineExclusive < 0 ||
        (retryAfterMillis != null && retryAfterMillis < 0) || jitterMillis < 0
    ) return RetryDecision.Stop(RetryStop.INVALID_INPUT)
    if (!automaticRetryEnabled) return RetryDecision.Stop(RetryStop.DISABLED)
    if (failure != RetryFailure.TRANSIENT_TRANSPORT && failure != RetryFailure.RATE_LIMITED) {
        return RetryDecision.Stop(RetryStop.NOT_RETRYABLE)
    }
    if (consecutiveFailures > policy.maxRetries) return RetryDecision.Stop(RetryStop.RETRY_BUDGET)
    if (nowTickMillis >= deadlineExclusive) return RetryDecision.Stop(RetryStop.DEADLINE)
    if (retryAfterMillis != null && retryAfterMillis > policy.maxDelayMillis) {
        return RetryDecision.Stop(RetryStop.DELAY_LIMIT)
    }

    var delay = policy.baseDelayMillis
    var remaining = consecutiveFailures - 1
    while (remaining > 0 && delay < policy.maxDelayMillis) {
        delay = if (delay > policy.maxDelayMillis / 2) policy.maxDelayMillis else delay * 2
        remaining--
    }
    // Saturate before addition. Never shorten the server's requested delay.
    delay += minOf(jitterMillis, policy.maxDelayMillis - delay)
    delay = maxOf(delay, retryAfterMillis ?: 0)
    if (delay > Long.MAX_VALUE - nowTickMillis) return RetryDecision.Stop(RetryStop.TICK_OVERFLOW)
    val tick = nowTickMillis + delay
    if (tick >= deadlineExclusive) return RetryDecision.Stop(RetryStop.DEADLINE)
    return RetryDecision.RetryAt(tick, delay, consecutiveFailures)
}
