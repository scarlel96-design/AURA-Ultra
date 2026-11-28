package io.github.scarlel96.aura.weather

import java.time.Instant
import java.util.Random

private fun time(hour: Int) = Instant.ofEpochSecond(hour * 3600L)
private fun slot(a: Int, b: Int, depth: Double?, unit: WeatherUnit = WeatherUnit.MILLIMETER) = ForecastRainInterval(time(a), time(b), depth, unit)
private fun analyze(vararg slots: ForecastRainInterval, end: Int = 4, limit: Int = 10) = analyzeRainTimeline(time(0), time(end), slots.toList(), limit)
private fun wet(a: Int, b: Int, end: WetEnd) = RainTimeline.WetWindow(time(a), time(b), end)
private fun unknown(a: Int, reason: UnknownRain) = RainTimeline.Unknown(time(a), reason)
private fun rejected(reason: TimelineError, index: Int? = null) = RainTimeline.Rejected(reason, index)

fun main() {
    val tests: List<Pair<String, () -> Unit>> = listOf(
        "completeDryHorizon" to { check(analyze(slot(0, 1, 0.0), slot(1, 4, -0.0)) == RainTimeline.Dry) },
        "emptyIsUnknown" to { check(analyze() == unknown(0, UnknownRain.GAP)) },
        "missingBeforeWetIsUnknown" to { check(analyze(slot(0, 1, null), slot(1, 4, 1.0)) == unknown(0, UnknownRain.MISSING_DEPTH)) },
        "gapBeforeWetIsUnknown" to { check(analyze(slot(0, 1, 0.0), slot(2, 4, 1.0)) == unknown(1, UnknownRain.GAP)) },
        "trailingDryGapIsUnknown" to { check(analyze(slot(0, 3, 0.0)) == unknown(3, UnknownRain.GAP)) },
        "wetRunEndsAtDryBucket" to { check(analyze(slot(0, 1, 0.0), slot(1, 2, 0.1), slot(2, 3, 3.0), slot(3, 4, 0.0)) == wet(1, 3, WetEnd.NEXT_DRY_BUCKET)) },
        "wetAtHorizonDoesNotClaimCessation" to { check(analyze(slot(0, 4, 0.1)) == wet(0, 4, WetEnd.HORIZON)) },
        "wetRunStopsAtGap" to { check(analyze(slot(0, 1, 1.0), slot(2, 4, 1.0)) == wet(0, 1, WetEnd.GAP)) },
        "wetRunStopsAtMissing" to { check(analyze(slot(0, 2, 1.0), slot(2, 4, null)) == wet(0, 2, WetEnd.MISSING_DEPTH)) },
        "trailingWetGap" to { check(analyze(slot(0, 3, 1.0)) == wet(0, 3, WetEnd.GAP)) },
        "onlyFirstWetRun" to { check(analyze(slot(0, 1, 1.0), slot(1, 2, 0.0), slot(2, 4, 2.0)) == wet(0, 1, WetEnd.NEXT_DRY_BUCKET)) },
        "inchesAndTinyPositive" to { check(analyze(slot(0, 1, 0.1, WeatherUnit.INCH), slot(1, 4, Double.MIN_VALUE)) == wet(0, 4, WetEnd.HORIZON)) },
        "invalidHorizonAndLimit" to { check(analyze(end = 0) == rejected(TimelineError.INVALID_HORIZON)); check(analyze(limit = 0) == rejected(TimelineError.INVALID_LIMIT)); check(analyze(slot(0, 1, 0.0), slot(1, 4, 0.0), limit = 1) == rejected(TimelineError.TOO_MANY_INTERVALS)) },
        "invertedAndEmptyIntervals" to { check(analyze(slot(2, 1, 0.0)) == rejected(TimelineError.INVALID_INTERVAL, 0)); check(analyze(slot(1, 1, 0.0)) == rejected(TimelineError.INVALID_INTERVAL, 0)) },
        "noClipping" to { check(analyze(slot(-1, 1, 0.0)) == rejected(TimelineError.OUTSIDE_HORIZON, 0)); check(analyze(slot(0, 5, 0.0)) == rejected(TimelineError.OUTSIDE_HORIZON, 0)) },
        "overlapDuplicateAndUnsortedRejected" to { check(analyze(slot(0, 2, 1.0), slot(1, 4, 0.0)) == rejected(TimelineError.OVERLAP_OR_ORDER, 1)); check(analyze(slot(0, 2, 0.0), slot(0, 2, 0.0)) == rejected(TimelineError.OVERLAP_OR_ORDER, 1)); check(analyze(slot(2, 3, 0.0), slot(0, 1, 0.0)) == rejected(TimelineError.OVERLAP_OR_ORDER, 1)) },
        "wrongUnitEvenWhenMissing" to { check(analyze(slot(0, 4, null, WeatherUnit.PERCENT)) == rejected(TimelineError.INVALID_DEPTH, 0)) },
        "invalidDepthAfterFirstWindow" to { for (v in listOf(-1.0, Double.NaN, Double.POSITIVE_INFINITY)) check(analyze(slot(0, 1, 1.0), slot(1, 2, 0.0), slot(2, 4, v)) == rejected(TimelineError.INVALID_DEPTH, 2)); check(analyze(slot(0, 4, Double.MAX_VALUE, WeatherUnit.INCH)) == rejected(TimelineError.INVALID_DEPTH, 0)) },
        "instantExtremesWithoutArithmetic" to { check(analyzeRainTimeline(Instant.MIN, Instant.MAX, listOf(ForecastRainInterval(Instant.MIN, Instant.MAX, 1.0, WeatherUnit.MILLIMETER)), 1) == RainTimeline.WetWindow(Instant.MIN, Instant.MAX, WetEnd.HORIZON)) },
        "seededBucketOracle" to {
            val rng = Random(20261128L)
            repeat(10000) {
                // 0=dry, 1=wet, 2=missing, 3=gap. The oracle uses explicit bucket indices.
                val states = List(8) { rng.nextInt(4) }
                val intervals = states.mapIndexedNotNull { i, state -> when (state) { 0 -> slot(i, i + 1, 0.0); 1 -> slot(i, i + 1, 0.1); 2 -> slot(i, i + 1, null); else -> null } }
                val first = states.indexOfFirst { it != 0 }
                val expected = when {
                    first == -1 -> RainTimeline.Dry
                    states[first] == 2 -> unknown(first, UnknownRain.MISSING_DEPTH)
                    states[first] == 3 -> unknown(first, UnknownRain.GAP)
                    else -> {
                        val end = (first + 1 until states.size).firstOrNull { states[it] != 1 } ?: states.size
                        wet(first, end, if (end == states.size) WetEnd.HORIZON else when (states[end]) { 0 -> WetEnd.NEXT_DRY_BUCKET; 2 -> WetEnd.MISSING_DEPTH; else -> WetEnd.GAP })
                    }
                }
                check(analyzeRainTimeline(time(0), time(8), intervals, 8) == expected)
            }
        },
    )
    check(tests.size == 20 && tests.map { it.first }.toSet().size == 20)
    for ((name, test) in tests) { test(); println("PASS $name") }
    println("TIMELINE_RESULT 20 PASS / 0 FAIL; seed=20261128 cases=10000")
}
