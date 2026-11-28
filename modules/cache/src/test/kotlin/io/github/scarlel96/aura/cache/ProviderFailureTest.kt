package io.github.scarlel96.aura.cache

private fun complete(kind: RetryFailure, hint: Long? = null) = FailureAction.Complete(AttemptOutcome.Failure(kind, hint))

fun main() {
    val tests: List<Pair<String, () -> Unit>> = listOf(
        "absentAndZero" to { check(parseRetryDelaySeconds(null) == DelayHint.Absent); check(parseRetryDelaySeconds("0") == DelayHint.Millis(0)) },
        "secondsToMillis" to { check(parseRetryDelaySeconds("0012") == DelayHint.Millis(12000)) },
        "largestRepresentableSeconds" to { check(parseRetryDelaySeconds("9223372036854775") == DelayHint.Millis(9223372036854775000L)); check(parseRetryDelaySeconds("9223372036854776") == DelayHint.Invalid) },
        "boundedLength" to { check(parseRetryDelaySeconds("0".repeat(20)) == DelayHint.Invalid); check(parseRetryDelaySeconds("9".repeat(19)) == DelayHint.Invalid) },
        "rejectNonAsciiAndMalformed" to { for (s in listOf("", "-1", "+1", " 1", "1 ", "1.0", "1e2", "1,2", "１", "\n1", "Sat, 28 Nov 2026 12:00:00 GMT")) check(parseRetryDelaySeconds(s) == DelayHint.Invalid) },
        "offlineWaits" to { check(classifyProviderFailure(ProviderFailure.OFFLINE) == FailureAction.WaitForConnectivity) },
        "transientMappings" to { for (f in listOf(ProviderFailure.TIMEOUT, ProviderFailure.CONNECTION_LOST, ProviderFailure.SERVER_TEMPORARY)) check(classifyProviderFailure(f) == complete(RetryFailure.TRANSIENT_TRANSPORT)) },
        "rateLimitMapping" to { check(classifyProviderFailure(ProviderFailure.RATE_LIMITED, "5") == complete(RetryFailure.RATE_LIMITED, 5000)); check(classifyProviderFailure(ProviderFailure.RATE_LIMITED) == complete(RetryFailure.RATE_LIMITED)) },
        "invalidHintStopsRetry" to { for (f in listOf(ProviderFailure.TIMEOUT, ProviderFailure.RATE_LIMITED)) check(classifyProviderFailure(f, "-1") == complete(RetryFailure.INVALID_RESPONSE)) },
        "denialAndSecurityNeverRetry" to { check(classifyProviderFailure(ProviderFailure.AUTHORITY_DENIED, "1") == complete(RetryFailure.AUTHORITY_DENIED)); check(classifyProviderFailure(ProviderFailure.SECURITY_FAILURE, "1") == complete(RetryFailure.PERMANENT)) },
        "otherFailuresStop" to { check(classifyProviderFailure(ProviderFailure.INVALID_RESPONSE) == complete(RetryFailure.INVALID_RESPONSE)); check(classifyProviderFailure(ProviderFailure.PERMANENT) == complete(RetryFailure.PERMANENT)); check(classifyProviderFailure(ProviderFailure.UNKNOWN) == complete(RetryFailure.UNKNOWN)) },
        "hintPassedToEpisode" to {
            val e = RecoveryEpisode(RetryPolicy(10, 10000, 2), 20000)
            val token = (e.poll(0, true) as RecoveryPoll.Start).receipt
            val action = classifyProviderFailure(ProviderFailure.RATE_LIMITED, "5") as FailureAction.Complete
            check(e.complete(token, 0, action.outcome)); check(e.poll(4999, true) == RecoveryPoll.Wait(5000)); check(e.poll(5000, true) is RecoveryPoll.Start)
        },
        "largeHintNotShortened" to {
            val action = classifyProviderFailure(ProviderFailure.RATE_LIMITED, "10") as FailureAction.Complete
            val e = RecoveryEpisode(RetryPolicy(10, 100, 2), 20000)
            check(e.complete((e.poll(0, true) as RecoveryPoll.Start).receipt, 0, action.outcome)); check(e.poll(0, true) == RecoveryPoll.End(RecoveryEnd.RETRY_STOPPED, RetryStop.DELAY_LIMIT))
        },
    )
    check(tests.size == 13 && tests.map { it.first }.toSet().size == 13)
    for ((name, test) in tests) { test(); println("PASS $name") }
    println("PROVIDER_RESULT 13 PASS / 0 FAIL")
}
