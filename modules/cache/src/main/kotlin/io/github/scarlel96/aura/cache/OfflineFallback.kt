package io.github.scarlel96.aura.cache

/** Use only the adapter's current validated classification. Do not recalculate TTL here. */
enum class CacheCondition { ABSENT, FRESH, STALE, UNDECLARED, INVALID }
enum class CacheScope { UNPROTECTED, PROTECTED, UNKNOWN }
enum class CacheChoice { FRESH_CANDIDATE, STALE_CANDIDATE, UNAVAILABLE }
enum class CacheReason { ELIGIBLE, SCOPE_BLOCKED, FAILURE_BLOCKED, ABSENT, STALE_DISABLED, UNDECLARED, INVALID }

data class CacheFallback(val choice: CacheChoice, val reason: CacheReason, val failure: ProviderFailure)

/**
 * Inspect metadata only. Return no payload or permission to read a cache.
 * The adapter must verify source, stream, provenance and freshness at final use.
 * This candidate excludes protected or unknown scope. Do not wire it to location or health data.
 * Keep stale eligibility explicit. Do not renew TTL or hide the original failure.
 */
fun chooseOfflineFallback(
    scope: CacheScope,
    failure: ProviderFailure,
    condition: CacheCondition,
    allowStale: Boolean,
): CacheFallback {
    fun unavailable(reason: CacheReason) = CacheFallback(CacheChoice.UNAVAILABLE, reason, failure)
    if (scope != CacheScope.UNPROTECTED) return unavailable(CacheReason.SCOPE_BLOCKED)
    if (failure != ProviderFailure.OFFLINE && failure != ProviderFailure.TIMEOUT &&
        failure != ProviderFailure.CONNECTION_LOST && failure != ProviderFailure.RATE_LIMITED &&
        failure != ProviderFailure.SERVER_TEMPORARY) return unavailable(CacheReason.FAILURE_BLOCKED)
    return when (condition) {
        CacheCondition.FRESH -> CacheFallback(CacheChoice.FRESH_CANDIDATE, CacheReason.ELIGIBLE, failure)
        CacheCondition.STALE -> if (allowStale) CacheFallback(CacheChoice.STALE_CANDIDATE, CacheReason.ELIGIBLE, failure) else unavailable(CacheReason.STALE_DISABLED)
        CacheCondition.ABSENT -> unavailable(CacheReason.ABSENT)
        CacheCondition.UNDECLARED -> unavailable(CacheReason.UNDECLARED)
        CacheCondition.INVALID -> unavailable(CacheReason.INVALID)
    }
}
