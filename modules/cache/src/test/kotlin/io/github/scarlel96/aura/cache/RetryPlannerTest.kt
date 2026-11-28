package io.github.scarlel96.aura.cache

import java.math.BigInteger
import java.util.Random

private val policy = RetryPolicy(100, 1000, 8)
private fun plan(
    n: Int = 1,
    now: Long = 0,
    deadline: Long = 10000,
    hint: Long? = null,
    jitter: Long = 0,
    enabled: Boolean = true,
    failure: RetryFailure = RetryFailure.TRANSIENT_TRANSPORT,
    p: RetryPolicy = policy,
) = planRetry(p, failure, n, now, deadline, hint, jitter, enabled)

private fun stop(reason: RetryStop) = RetryDecision.Stop(reason)
private fun at(tick: Long, delay: Long, number: Int = 1) = RetryDecision.RetryAt(tick, delay, number)
private fun invalidPolicy(block: () -> Unit) {
    try {
        block()
    } catch (_: IllegalArgumentException) {
        return
    }
    error("Invalid policy accepted")
}

fun main() {
    val tests: List<Pair<String, () -> Unit>> = listOf(
        "policyRejectsZeroNegativeAndInverted" to {
            invalidPolicy { RetryPolicy(0, 1, 1) }
            invalidPolicy { RetryPolicy(-1, 1, 1) }
            invalidPolicy { RetryPolicy(10, 9, 1) }
            invalidPolicy { RetryPolicy(1, 1, -1) }
        },
        "firstFailureUsesBaseDelay" to { check(plan(now = 7) == at(107, 100)) },
        "exponentialGrowthCaps" to {
            listOf(100L, 200, 400, 800, 1000, 1000, 1000, 1000).forEachIndexed { i, d ->
                check(plan(n = i + 1) == at(d, d, i + 1))
            }
        },
        "lastRetryAndExhaustion" to {
            check(plan(n = 8) == at(1000, 1000, 8))
            check(plan(n = 9) == stop(RetryStop.RETRY_BUDGET))
        },
        "zeroBudgetDisablesRetries" to { check(plan(p = RetryPolicy(1, 1, 0)) == stop(RetryStop.RETRY_BUDGET)) },
        "invalidFailureCount" to {
            for (n in listOf(0, -1, Int.MIN_VALUE)) check(plan(n = n) == stop(RetryStop.INVALID_INPUT))
        },
        "invalidTicks" to {
            check(plan(now = -1) == stop(RetryStop.INVALID_INPUT))
            check(plan(deadline = -1) == stop(RetryStop.INVALID_INPUT))
        },
        "negativeHintAndJitterRejected" to {
            check(plan(hint = -1) == stop(RetryStop.INVALID_INPUT))
            check(plan(jitter = -1) == stop(RetryStop.INVALID_INPUT))
        },
        "disabledDoesNotRetry" to { check(plan(enabled = false) == stop(RetryStop.DISABLED)) },
        "nonTransientFailuresNeverRetry" to {
            for (f in listOf(RetryFailure.PERMANENT, RetryFailure.INVALID_RESPONSE, RetryFailure.AUTHORITY_DENIED, RetryFailure.UNKNOWN)) {
                check(plan(failure = f) == stop(RetryStop.NOT_RETRYABLE))
            }
        },
        "rateLimitedWithoutHintUsesBackoff" to { check(plan(failure = RetryFailure.RATE_LIMITED) == at(100, 100)) },
        "serverHintIsFloor" to {
            check(plan(hint = 700) == at(700, 700))
            check(plan(hint = 1) == at(100, 100))
            check(plan(hint = 0) == at(100, 100))
        },
        "serverHintAboveCapStops" to {
            check(plan(hint = 1000) == at(1000, 1000))
            check(plan(hint = 1001) == stop(RetryStop.DELAY_LIMIT))
            check(plan(hint = Long.MAX_VALUE) == stop(RetryStop.DELAY_LIMIT))
        },
        "boundedJitter" to {
            check(plan(jitter = 25) == at(125, 125))
            check(plan(jitter = Long.MAX_VALUE) == at(1000, 1000))
            check(plan(jitter = 25, hint = 200) == at(200, 200))
        },
        "deadlineIsExclusive" to {
            check(plan(now = 1, deadline = 102) == at(101, 100))
            check(plan(now = 1, deadline = 101) == stop(RetryStop.DEADLINE))
            check(plan(now = 2, deadline = 1) == stop(RetryStop.DEADLINE))
            check(plan(now = 1, deadline = 1) == stop(RetryStop.DEADLINE))
        },
        "serverHintCannotCrossDeadline" to { check(plan(hint = 500, deadline = 500) == stop(RetryStop.DEADLINE)) },
        "tickAdditionCannotWrap" to {
            check(plan(now = Long.MAX_VALUE - 50, deadline = Long.MAX_VALUE) == stop(RetryStop.TICK_OVERFLOW))
            check(plan(now = Long.MAX_VALUE - 101, deadline = Long.MAX_VALUE) == at(Long.MAX_VALUE - 1, 100))
            check(plan(now = Long.MAX_VALUE - 100, deadline = Long.MAX_VALUE) == stop(RetryStop.DEADLINE))
        },
        "hugeFailureCountIsBounded" to {
            val p = RetryPolicy(1, Long.MAX_VALUE - 1, Int.MAX_VALUE)
            check(plan(n = Int.MAX_VALUE, deadline = Long.MAX_VALUE, p = p) == at(Long.MAX_VALUE - 1, Long.MAX_VALUE - 1, Int.MAX_VALUE))
        },
        "doublingAndJitterNeverOverflow" to {
            val p = RetryPolicy(Long.MAX_VALUE / 2 + 1, Long.MAX_VALUE, 2)
            check(plan(n = 2, deadline = Long.MAX_VALUE, p = p) == stop(RetryStop.DEADLINE))
            check(plan(jitter = Long.MAX_VALUE, deadline = Long.MAX_VALUE, p = p) == stop(RetryStop.DEADLINE))
        },
        "deterministicAndNoStoredState" to {
            val first = plan(n = 4, hint = 900)
            plan(n = 8, enabled = false)
            check(first == plan(n = 4, hint = 900))
            check(plan() == at(100, 100))
        },
        "seededArithmeticAgainstBigInteger" to {
            val rng = Random(20261128L)
            repeat(50000) {
                val base = 1 + (rng.nextLong() ushr 1) % 1000000
                val cap = base + (rng.nextLong() ushr 1) % (Long.MAX_VALUE - base)
                val n = 1 + rng.nextInt(90)
                val now = (rng.nextLong() ushr 1) % Long.MAX_VALUE
                val jitter = rng.nextLong() ushr 1
                val hint = (rng.nextLong() ushr 1) % cap
                val max = BigInteger.valueOf(cap)
                val expectedDelay = BigInteger.valueOf(base).shiftLeft(n - 1).min(max)
                    .add(BigInteger.valueOf(jitter)).min(max).max(BigInteger.valueOf(hint))
                val due = expectedDelay.add(BigInteger.valueOf(now))
                val ceiling = BigInteger.valueOf(Long.MAX_VALUE)
                val expected = when {
                    due > ceiling -> stop(RetryStop.TICK_OVERFLOW)
                    due == ceiling -> stop(RetryStop.DEADLINE)
                    else -> at(due.longValueExact(), expectedDelay.longValueExact(), n)
                }
                check(plan(n, now, Long.MAX_VALUE, hint, jitter, p = RetryPolicy(base, cap, 90)) == expected)
            }
        },
    )
    check(tests.size == 21 && tests.map { it.first }.toSet().size == 21)
    for ((name, test) in tests) {
        test()
        println("PASS $name")
    }
    println("RETRY_RESULT 21 PASS / 0 FAIL; seed=20261128 arithmeticCases=50000")
}
