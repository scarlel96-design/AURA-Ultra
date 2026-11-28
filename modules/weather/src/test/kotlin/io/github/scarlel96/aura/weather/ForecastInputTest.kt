package io.github.scarlel96.aura.weather

import java.time.Instant

private val received = Instant.parse("2026-01-01T00:00:00Z")
private val row = KmaRowTime("20260101", "0800", "20260101", "1000", 1, 2)
private val issue = Instant.parse("2025-12-31T23:00:00Z")
private fun kma(r: KmaRowTime = row, expected: Instant = issue, receipt: Instant = received) = validateKmaRowTime(r, 1, 2, expected, receipt)
private fun col(f: HourlyField, u: String, vararg v: Double?) = HourlyColumn(f.key, u, v.toList())
private fun decode(vararg cols: HourlyColumn, times: List<Long> = listOf(3600, 7200), offset: Int = 0, timeUnit: String = "unixtime", max: Int = 2, expected: Set<HourlyField> = HourlyField.entries.filter { f -> cols.any { it.key == f.key } }.toSet()) = decodeOpenMeteoHourly(times, offset, timeUnit, cols.toList(), expected, received, max)
private fun reject(r: ForecastInputError) = OpenMeteoHourlyResult.Rejected(r)
private val temp = col(HourlyField.TEMPERATURE, "°C", 0.0, null)
private val rain = col(HourlyField.RAIN, "mm", 0.0, 1.0)
private val showers = col(HourlyField.SHOWERS, "mm", 0.0, 2.0)

fun main() {
    val tests: List<Pair<String, () -> Unit>> = listOf(
        "kstMidnightAndIssue" to { check(kma() == KmaForecastTime(issue, Instant.parse("2026-01-01T01:00:00Z"))) },
        "kstInvalidCalendarAndClock" to { for (r in listOf(row.copy(baseDate = "20260229"), row.copy(baseTime = "2400"), row.copy(fcstTime = "1060"), row.copy(baseDate = "２０２６0101"), row.copy(baseDate = "00000101"))) check(kma(r) == null) },
        "kmaRejectWrongGridOrIssue" to { check(kma(row.copy(nx = 9)) == null); check(kma(expected = issue.plusSeconds(1)) == null) },
        "kmaRejectFutureIssueAndEarlierForecast" to { check(kma(receipt = issue.minusSeconds(1)) == null); check(kma(row.copy(fcstTime = "0700")) == null) },
        "pointAndMissingPreserved" to { val a = decode(temp) as OpenMeteoHourlyResult.Accepted; check(a.receivedAt == received && a.liquidRain.isEmpty()); check(a.data[0] == ForecastDatum(HourlyField.TEMPERATURE, Instant.ofEpochSecond(3600), null, QuantityResult.Value(WeatherMetric.TEMPERATURE, WeatherUnit.CELSIUS, 0.0))); check(a.data[1].quantity == QuantityResult.Missing) },
        "probabilityPrecedingHour" to { val a = decode(col(HourlyField.PROBABILITY, "%", 20.0, 100.0)) as OpenMeteoHourlyResult.Accepted; check(a.data[0].windowStart == Instant.EPOCH && a.data[0].validAt == Instant.ofEpochSecond(3600)) },
        "rainAndShowersNotSnow" to { val a = decode(rain, showers) as OpenMeteoHourlyResult.Accepted; check(a.liquidRain == listOf(ForecastRainInterval(Instant.EPOCH, Instant.ofEpochSecond(3600), 0.0, WeatherUnit.MILLIMETER), ForecastRainInterval(Instant.ofEpochSecond(3600), Instant.ofEpochSecond(7200), 3.0, WeatherUnit.MILLIMETER))); check(analyzeRainTimeline(Instant.EPOCH, Instant.ofEpochSecond(7200), a.liquidRain, 2) == RainTimeline.WetWindow(Instant.ofEpochSecond(3600), Instant.ofEpochSecond(7200), WetEnd.HORIZON)); check(decode(HourlyColumn("precipitation", "mm", listOf(0.0, 1.0))) == reject(ForecastInputError.FIELD)) },
        "rainMissingNotZero" to { val a = decode(col(HourlyField.RAIN, "mm", null, 0.0), showers) as OpenMeteoHourlyResult.Accepted; check(a.liquidRain[0].depth == null); check(analyzeRainTimeline(Instant.EPOCH, Instant.ofEpochSecond(7200), a.liquidRain, 2) == RainTimeline.Unknown(Instant.EPOCH, UnknownRain.MISSING_DEPTH)) },
        "rainPairRequired" to { check(decode(rain) == reject(ForecastInputError.FIELD)); check(decode(showers) == reject(ForecastInputError.FIELD)) },
        "explicitUnitConversion" to { val a = decode(col(HourlyField.WIND, "km/h", 36.0, 0.0), col(HourlyField.FEELS_LIKE, "°F", 32.0, 50.0), col(HourlyField.HUMIDITY, "%", 30.0, 100.0)) as OpenMeteoHourlyResult.Accepted; check((a.data[0].quantity as QuantityResult.Value).value == 10.0); check((a.data[2].quantity as QuantityResult.Value).value == 0.0); check((a.data[5].quantity as QuantityResult.Value).value == 100.0) },
        "invalidUnitsEvenMissing" to { check(decode(col(HourlyField.TEMPERATURE, "%", null, null)) == reject(ForecastInputError.UNIT)); check(decode(col(HourlyField.WIND, "kn", 1.0, 2.0)) == reject(ForecastInputError.UNIT)) },
        "invalidValuesAndSumOverflow" to { check(decode(col(HourlyField.PROBABILITY, "%", 101.0, 0.0)) == reject(ForecastInputError.VALUE)); check(decode(col(HourlyField.TEMPERATURE, "°C", 1.0, Double.NaN)) == reject(ForecastInputError.VALUE)); check(decode(col(HourlyField.RAIN, "mm", Double.MAX_VALUE, 0.0), col(HourlyField.SHOWERS, "mm", Double.MAX_VALUE, 0.0)) == reject(ForecastInputError.VALUE)) },
        "shapeAndRequestedFields" to { check(decode(temp, max = 1) == reject(ForecastInputError.SHAPE)); check(decode(temp, times = emptyList()) == reject(ForecastInputError.SHAPE)); check(decode(temp.copy(values = listOf(0.0))) == reject(ForecastInputError.SHAPE)); check(decode(temp, temp) == reject(ForecastInputError.FIELD)); check(decode(temp, expected = setOf(HourlyField.TEMPERATURE, HourlyField.WIND)) == reject(ForecastInputError.FIELD)) },
        "timeContract" to { check(decode(temp, offset = 32400) == reject(ForecastInputError.TIME)); check(decode(temp, timeUnit = "iso8601") == reject(ForecastInputError.TIME)); for (t in listOf(listOf(3601L, 7201L), listOf(7200L, 3600L), listOf(3600L, 3600L), listOf(3600L, 10800L), listOf(Long.MAX_VALUE, 3600L))) check(decode(temp, times = t) == reject(ForecastInputError.TIME)) },
        "outputDoesNotRetainInputList" to { val values = mutableListOf<Double?>(1.0, 2.0); val a = decode(HourlyColumn(temp.key, temp.unit, values)) as OpenMeteoHourlyResult.Accepted; values[0] = 99.0; check((a.data[0].quantity as QuantityResult.Value).value == 1.0) },
    )
    check(tests.size == 15 && tests.map { it.first }.toSet().size == 15)
    for ((name, test) in tests) { test(); println("PASS $name") }
    println("FORECAST_INPUT_RESULT 15 PASS / 0 FAIL")
}
