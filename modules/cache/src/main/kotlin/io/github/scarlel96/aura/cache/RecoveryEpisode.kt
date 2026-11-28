package io.github.scarlel96.aura.cache

/** Identity only. Constructing a different receipt cannot complete an active attempt. */
class AttemptReceipt internal constructor()

enum class RecoveryEnd { SUCCEEDED, CANCELLED, DEADLINE, CLOCK_INVALID, RETRY_STOPPED }

sealed interface RecoveryPoll {
    data class Start(val receipt: AttemptReceipt) : RecoveryPoll
    data class Wait(val dueTickMillis: Long) : RecoveryPoll
    data object Paused : RecoveryPoll
    data object InFlight : RecoveryPoll
    data class End(val reason: RecoveryEnd, val retryStop: RetryStop? = null) : RecoveryPoll
}

sealed interface AttemptOutcome {
    data object Success : AttemptOutcome
    data class Failure(
        val kind: RetryFailure,
        val retryAfterMillis: Long? = null,
        val jitterMillis: Long = 0,
    ) : AttemptOutcome
}

/**
 * Track one finite recovery episode. Serialize all calls in the adapter.
 * Use ticks from one monotonic clock session. Do not persist this object.
 * A Start is a scheduling decision, not authority to access or publish data.
 * The adapter must recheck permission and readiness before actual dispatch.
 * Cancel on session loss. Cancel transport separately; late results are ignored here.
 */
class RecoveryEpisode(private val policy: RetryPolicy, private val deadlineExclusive: Long) {
    init { require(deadlineExclusive > 0) }

    private var lastTick = 0L
    private var due = 0L
    private var failures = 0L
    private var active: AttemptReceipt? = null
    private var terminal: RecoveryPoll.End? = null

    fun poll(nowTickMillis: Long, ready: Boolean): RecoveryPoll {
        terminal?.let { return it }
        checkTime(nowTickMillis)?.let { return it }
        if (active != null) return RecoveryPoll.InFlight
        if (!ready) return RecoveryPoll.Paused
        if (nowTickMillis < due) return RecoveryPoll.Wait(due)
        val receipt = AttemptReceipt()
        active = receipt
        return RecoveryPoll.Start(receipt)
    }

    /** Consume only the active receipt. Ignore duplicate and foreign completions. */
    fun complete(receipt: AttemptReceipt, nowTickMillis: Long, outcome: AttemptOutcome): Boolean {
        if (terminal != null || active !== receipt) return false
        active = null
        if (checkTime(nowTickMillis) != null) return true
        when (outcome) {
            AttemptOutcome.Success -> end(RecoveryEnd.SUCCEEDED)
            is AttemptOutcome.Failure -> {
                failures++
                val decision = if (failures > Int.MAX_VALUE.toLong()) {
                    RetryDecision.Stop(RetryStop.RETRY_BUDGET)
                } else {
                    planRetry(policy, outcome.kind, failures.toInt(), nowTickMillis,
                        deadlineExclusive, outcome.retryAfterMillis, outcome.jitterMillis)
                }
                when (decision) {
                    is RetryDecision.RetryAt -> due = decision.tickMillis
                    is RetryDecision.Stop -> end(RecoveryEnd.RETRY_STOPPED, decision.reason)
                }
            }
        }
        return true
    }

    /** Make cancellation terminal. Do not replace a previous terminal result. */
    fun cancel(): RecoveryPoll.End = terminal ?: end(RecoveryEnd.CANCELLED)

    private fun checkTime(now: Long): RecoveryPoll.End? {
        if (now < lastTick) return end(RecoveryEnd.CLOCK_INVALID)
        lastTick = now
        if (now >= deadlineExclusive) return end(RecoveryEnd.DEADLINE)
        return null
    }

    private fun end(reason: RecoveryEnd, stop: RetryStop? = null): RecoveryPoll.End {
        val result = RecoveryPoll.End(reason, stop)
        active = null
        terminal = result
        return result
    }
}
