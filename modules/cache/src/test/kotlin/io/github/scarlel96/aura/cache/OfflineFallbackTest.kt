package io.github.scarlel96.aura.cache

private fun choose(condition: CacheCondition, stale: Boolean = false, scope: CacheScope = CacheScope.UNPROTECTED, failure: ProviderFailure = ProviderFailure.OFFLINE) = chooseOfflineFallback(scope, failure, condition, stale)

fun main() {
    val tests: List<Pair<String, () -> Unit>> = listOf(
        "freshOfflineCandidate" to { check(choose(CacheCondition.FRESH) == CacheFallback(CacheChoice.FRESH_CANDIDATE, CacheReason.ELIGIBLE, ProviderFailure.OFFLINE)) },
        "staleExplicitOnly" to { check(choose(CacheCondition.STALE).reason == CacheReason.STALE_DISABLED); check(choose(CacheCondition.STALE, true).choice == CacheChoice.STALE_CANDIDATE) },
        "absentUnknownAndInvalidNotEligible" to { for ((c, r) in listOf(CacheCondition.ABSENT to CacheReason.ABSENT, CacheCondition.UNDECLARED to CacheReason.UNDECLARED, CacheCondition.INVALID to CacheReason.INVALID)) check(choose(c, true) == CacheFallback(CacheChoice.UNAVAILABLE, r, ProviderFailure.OFFLINE)) },
        "protectedAndUnknownNeverEligible" to { for (s in listOf(CacheScope.PROTECTED, CacheScope.UNKNOWN)) for (c in CacheCondition.entries) check(choose(c, true, s).reason == CacheReason.SCOPE_BLOCKED) },
        "denialAndSecurityBlockFresh" to { for (f in listOf(ProviderFailure.AUTHORITY_DENIED, ProviderFailure.SECURITY_FAILURE)) check(choose(CacheCondition.FRESH, true, failure = f).reason == CacheReason.FAILURE_BLOCKED) },
        "invalidPermanentUnknownBlockStale" to { for (f in listOf(ProviderFailure.INVALID_RESPONSE, ProviderFailure.PERMANENT, ProviderFailure.UNKNOWN)) check(choose(CacheCondition.STALE, true, failure = f).choice == CacheChoice.UNAVAILABLE) },
        "transientCausesPreserved" to { for (f in listOf(ProviderFailure.OFFLINE, ProviderFailure.TIMEOUT, ProviderFailure.CONNECTION_LOST, ProviderFailure.RATE_LIMITED, ProviderFailure.SERVER_TEMPORARY)) check(choose(CacheCondition.FRESH, failure = f) == CacheFallback(CacheChoice.FRESH_CANDIDATE, CacheReason.ELIGIBLE, f)) },
        "noImplicitRenewal" to { check(choose(CacheCondition.STALE, true).choice == CacheChoice.STALE_CANDIDATE); check(choose(CacheCondition.UNDECLARED, true).choice == CacheChoice.UNAVAILABLE) },
        "exhaustiveDecisionMatrix" to {
            var count = 0
            val allowed = setOf(ProviderFailure.OFFLINE, ProviderFailure.TIMEOUT, ProviderFailure.CONNECTION_LOST, ProviderFailure.RATE_LIMITED, ProviderFailure.SERVER_TEMPORARY)
            for (s in CacheScope.entries) for (f in ProviderFailure.entries) for (c in CacheCondition.entries) for (stale in listOf(false,true)) {
                val result = choose(c, stale, s, f)
                val expected = if (s == CacheScope.UNPROTECTED && f in allowed) when (c) {
                    CacheCondition.FRESH -> CacheChoice.FRESH_CANDIDATE
                    CacheCondition.STALE -> if (stale) CacheChoice.STALE_CANDIDATE else CacheChoice.UNAVAILABLE
                    else -> CacheChoice.UNAVAILABLE
                } else CacheChoice.UNAVAILABLE
                check(result.choice == expected && result.failure == f); count++
            }
            check(count == 300)
        },
    )
    check(tests.size == 9 && tests.map { it.first }.toSet().size == 9)
    for ((name, test) in tests) { test(); println("PASS $name") }
    println("CACHE_RESULT 9 PASS / 0 FAIL; matrix=300")
}
