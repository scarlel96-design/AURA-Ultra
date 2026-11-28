package io.github.scarlel96.aura.weather

import java.time.Instant

/** One forecast depth bucket. The adapter must verify its source and forecast provenance. */
data class ForecastRainInterval(
    val start: Instant,
    val endExclusive: Instant,
    val depth: Double?,
    val unit: WeatherUnit,
)

enum class TimelineError { INVALID_HORIZON, INVALID_LIMIT, TOO_MANY_INTERVALS, INVALID_INTERVAL, OUTSIDE_HORIZON, OVERLAP_OR_ORDER, INVALID_DEPTH }
enum class UnknownRain { GAP, MISSING_DEPTH }
enum class WetEnd { NEXT_DRY_BUCKET, GAP, MISSING_DEPTH, HORIZON }

sealed interface RainTimeline {
    data object Dry : RainTimeline
    data class Unknown(val at: Instant, val reason: UnknownRain) : RainTimeline
    data class WetWindow(val start: Instant, val endExclusive: Instant, val endEvidence: WetEnd) : RainTimeline
    data class Rejected(val reason: TimelineError, val intervalIndex: Int? = null) : RainTimeline
}

/**
 * Find the first contiguous run of positive forecast depth in one verified batch.
 * Supply intervals in time order inside the half-open horizon. Do not clip depth buckets.
 * A wet window describes forecast buckets, not the exact time when rain starts or stops.
 * A gap or missing depth before a wet window makes the first window unknown.
 * Require a stable input list during this call. Validate provenance and freshness separately.
 */
fun analyzeRainTimeline(
    horizonStart: Instant,
    horizonEndExclusive: Instant,
    intervals: List<ForecastRainInterval>,
    maxIntervals: Int,
): RainTimeline {
    if (horizonStart >= horizonEndExclusive) return RainTimeline.Rejected(TimelineError.INVALID_HORIZON)
    if (maxIntervals <= 0) return RainTimeline.Rejected(TimelineError.INVALID_LIMIT)
    if (intervals.size > maxIntervals) return RainTimeline.Rejected(TimelineError.TOO_MANY_INTERVALS)

    // Validate the whole batch, including intervals after the first wet window.
    var previousEnd = horizonStart
    val depths = ArrayList<Double?>(intervals.size)
    for ((index, interval) in intervals.withIndex()) {
        if (interval.start >= interval.endExclusive) return RainTimeline.Rejected(TimelineError.INVALID_INTERVAL, index)
        if (interval.start < horizonStart || interval.endExclusive > horizonEndExclusive) {
            return RainTimeline.Rejected(TimelineError.OUTSIDE_HORIZON, index)
        }
        if (interval.start < previousEnd) return RainTimeline.Rejected(TimelineError.OVERLAP_OR_ORDER, index)
        previousEnd = interval.endExclusive
        when (val result = normalizeWeatherQuantity(WeatherMetric.FORECAST_RAIN_DEPTH, interval.unit, interval.depth)) {
            is QuantityResult.Value -> depths.add(result.value)
            QuantityResult.Missing -> depths.add(null)
            is QuantityResult.Rejected -> return RainTimeline.Rejected(TimelineError.INVALID_DEPTH, index)
        }
    }

    var cursor = horizonStart
    var wetStart: Instant? = null
    for ((index, interval) in intervals.withIndex()) {
        if (interval.start > cursor) {
            return wetStart?.let { RainTimeline.WetWindow(it, cursor, WetEnd.GAP) }
                ?: RainTimeline.Unknown(cursor, UnknownRain.GAP)
        }
        val depth = depths[index]
        if (depth == null) {
            return wetStart?.let { RainTimeline.WetWindow(it, cursor, WetEnd.MISSING_DEPTH) }
                ?: RainTimeline.Unknown(cursor, UnknownRain.MISSING_DEPTH)
        }
        if (depth > 0.0) {
            if (wetStart == null) wetStart = interval.start
        } else if (wetStart != null) {
            return RainTimeline.WetWindow(wetStart, cursor, WetEnd.NEXT_DRY_BUCKET)
        }
        cursor = interval.endExclusive
    }
    if (wetStart != null) return RainTimeline.WetWindow(wetStart, cursor,
        if (cursor == horizonEndExclusive) WetEnd.HORIZON else WetEnd.GAP)
    return if (cursor == horizonEndExclusive) RainTimeline.Dry else RainTimeline.Unknown(cursor, UnknownRain.GAP)
}
