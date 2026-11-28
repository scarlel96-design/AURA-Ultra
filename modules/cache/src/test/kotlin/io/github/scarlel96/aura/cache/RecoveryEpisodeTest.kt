package io.github.scarlel96.aura.cache

import java.util.Random

private fun episode(retries: Int = 2, deadline: Long = 1000) = RecoveryEpisode(RetryPolicy(10, 100, retries), deadline)
private fun RecoveryEpisode.start(t: Long = 0) = (poll(t, true) as RecoveryPoll.Start).receipt
private val failure = AttemptOutcome.Failure(RetryFailure.TRANSIENT_TRANSPORT)
private val success = AttemptOutcome.Success
private fun ended(r: RecoveryEnd, stop: RetryStop? = null) = RecoveryPoll.End(r, stop)
private fun stop(r: RetryStop) = ended(RecoveryEnd.RETRY_STOPPED, r)

fun main() {
    val tests: List<Pair<String, () -> Unit>> = listOf(
        "initialPauseThenStart" to {
            val e = episode(); check(e.poll(0, false) == RecoveryPoll.Paused); e.start(1)
        },
        "singleActiveAttempt" to {
            val e = episode(); e.start(); check(e.poll(0, true) == RecoveryPoll.InFlight)
            check(e.poll(1, false) == RecoveryPoll.InFlight)
        },
        "successIsTerminal" to {
            val e = episode(); check(e.complete(e.start(), 1, success)); check(e.poll(2, true) == ended(RecoveryEnd.SUCCEEDED))
            check(e.cancel() == ended(RecoveryEnd.SUCCEEDED))
        },
        "noEarlyRetry" to {
            val e = episode(); check(e.complete(e.start(), 1, failure)); check(e.poll(10, true) == RecoveryPoll.Wait(11)); e.start(11)
        },
        "retryBudgetIsCumulative" to {
            val e = episode(); check(e.complete(e.start(), 0, failure)); check(e.complete(e.start(10), 10, failure))
            check(e.complete(e.start(30), 30, failure)); check(e.poll(31, true) == stop(RetryStop.RETRY_BUDGET))
        },
        "zeroRetriesStillAllowsInitialAttempt" to {
            val e = episode(0); check(e.complete(e.start(), 0, failure)); check(e.poll(1, true) == stop(RetryStop.RETRY_BUDGET))
        },
        "foreignReceiptIgnored" to {
            val a = episode(); val b = episode(); val t = a.start(); val other = b.start()
            check(!a.complete(other, 1000, success)); check(a.poll(1, true) == RecoveryPoll.InFlight); check(a.complete(t, 1, success))
        },
        "constructedReceiptIgnored" to {
            val e = episode(); e.start(); check(!e.complete(AttemptReceipt(), 0, success)); check(e.poll(0, true) == RecoveryPoll.InFlight)
        },
        "duplicateCompletionCannotChangeDue" to {
            val e = episode(); val t = e.start(); check(e.complete(t, 1, failure)); check(!e.complete(t, 9, success))
            check(e.poll(2, true) == RecoveryPoll.Wait(11))
        },
        "oldCompletionCannotConsumeNewAttempt" to {
            val e = episode(); val t = e.start(); check(e.complete(t, 0, failure)); val next = e.start(10)
            check(!e.complete(t, 1001, success)); check(e.poll(10, true) == RecoveryPoll.InFlight); check(e.complete(next, 10, success))
        },
        "pauseDoesNotResetBackoff" to {
            val e = episode(); check(e.complete(e.start(), 0, failure)); check(e.poll(4, false) == RecoveryPoll.Paused)
            check(e.poll(5, true) == RecoveryPoll.Wait(10)); check(e.poll(10, false) == RecoveryPoll.Paused); e.start(11)
        },
        "serverDelayIsPreservedAcrossPause" to {
            val e = episode(); check(e.complete(e.start(), 0, AttemptOutcome.Failure(RetryFailure.RATE_LIMITED, 80)))
            check(e.poll(60, false) == RecoveryPoll.Paused); check(e.poll(79, true) == RecoveryPoll.Wait(80)); e.start(80)
        },
        "permanentAndDeniedStop" to {
            for (kind in listOf(RetryFailure.PERMANENT, RetryFailure.AUTHORITY_DENIED, RetryFailure.INVALID_RESPONSE, RetryFailure.UNKNOWN)) {
                val e = episode(); check(e.complete(e.start(), 0, AttemptOutcome.Failure(kind))); check(e.poll(1, true) == stop(RetryStop.NOT_RETRYABLE))
            }
        },
        "invalidHintsFailClosed" to {
            val e = episode(); check(e.complete(e.start(), 0, AttemptOutcome.Failure(RetryFailure.RATE_LIMITED, -1))); check(e.poll(0, true) == stop(RetryStop.INVALID_INPUT))
            val f = episode(); check(f.complete(f.start(), 0, AttemptOutcome.Failure(RetryFailure.RATE_LIMITED, 101))); check(f.poll(0, true) == stop(RetryStop.DELAY_LIMIT))
        },
        "deadlineBeforeInitialAndDuringPause" to {
            val e = episode(deadline = 10); check(e.poll(10, true) == ended(RecoveryEnd.DEADLINE))
            val f = episode(deadline = 10); check(f.poll(9, false) == RecoveryPoll.Paused); check(f.poll(10, false) == ended(RecoveryEnd.DEADLINE))
        },
        "deadlineWhileInFlight" to {
            val e = episode(deadline = 10); val t = e.start(); check(e.poll(10, true) == ended(RecoveryEnd.DEADLINE)); check(!e.complete(t, 10, success))
            val f = episode(deadline = 10); check(f.complete(f.start(), 10, success)); check(f.poll(10, true) == ended(RecoveryEnd.DEADLINE))
        },
        "retryCannotReachDeadline" to {
            val e = episode(deadline = 10); check(e.complete(e.start(), 0, failure)); check(e.poll(0, true) == stop(RetryStop.DEADLINE))
        },
        "rollbackAndNegativeTicksAreTerminal" to {
            val e = episode(); e.start(10); check(e.poll(9, true) == ended(RecoveryEnd.CLOCK_INVALID)); check(e.poll(11, true) == ended(RecoveryEnd.CLOCK_INVALID))
            val f = episode(); check(f.complete(f.start(10), 9, success)); check(f.poll(11, true) == ended(RecoveryEnd.CLOCK_INVALID))
            check(episode().poll(-1, true) == ended(RecoveryEnd.CLOCK_INVALID))
        },
        "cancelBeforeAndDuringAttempt" to {
            val e = episode(); check(e.cancel() == ended(RecoveryEnd.CANCELLED)); check(e.poll(0, true) == ended(RecoveryEnd.CANCELLED))
            val f = episode(); val t = f.start(); f.cancel(); check(!f.complete(t, 1, success)); check(f.poll(2, true) == ended(RecoveryEnd.CANCELLED))
        },
        "cancelWhileWaiting" to {
            val e = episode(); check(e.complete(e.start(), 0, failure)); e.cancel(); check(e.poll(50, true) == ended(RecoveryEnd.CANCELLED))
        },
        "nearLongLimitFailsClosed" to {
            val e = episode(deadline = Long.MAX_VALUE); check(e.complete(e.start(Long.MAX_VALUE - 5), Long.MAX_VALUE - 5, failure)); check(e.poll(Long.MAX_VALUE - 1, true) == stop(RetryStop.TICK_OVERFLOW))
        },
        "seededFiniteEpisodes" to {
            val rng = Random(20261128L)
            repeat(10000) {
                val budget = rng.nextInt(8); val e = episode(budget, 10000); var t = 0L; var attempts = 0
                while (true) {
                    when (val p = e.poll(t, true)) {
                        is RecoveryPoll.Start -> { attempts++; check(e.poll(t, true) == RecoveryPoll.InFlight); check(e.complete(p.receipt, t, failure)); check(!e.complete(p.receipt, t, success)) }
                        is RecoveryPoll.Wait -> { check(p.dueTickMillis > t); t = p.dueTickMillis }
                        is RecoveryPoll.End -> { check(p == stop(RetryStop.RETRY_BUDGET)); break }
                        else -> error("Unexpected poll")
                    }
                }
                check(attempts == budget + 1)
            }
        },
    )
    check(tests.size == 22 && tests.map { it.first }.toSet().size == 22)
    for ((name, test) in tests) { test(); println("PASS $name") }
    println("RECOVERY_RESULT 22 PASS / 0 FAIL; seed=20261128 episodes=10000")
}
