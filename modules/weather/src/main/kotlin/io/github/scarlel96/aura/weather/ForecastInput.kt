package io.github.scarlel96.aura.weather

import java.time.DateTimeException
import java.time.Instant
import java.time.LocalDate
import java.time.LocalTime
import java.time.ZoneOffset
import java.util.Collections

/** Decoded KMA forecast row metadata. No value or access permission is carried here. */
data class KmaRowTime(val baseDate: String, val baseTime: String, val fcstDate: String, val fcstTime: String, val nx: Int, val ny: Int)
data class KmaForecastTime(val issuedAt: Instant, val validAt: Instant)

private fun kst(date: String, time: String): Instant? {
    if (date.length != 8 || time.length != 4 || (date + time).any { it !in '0'..'9' }) return null
    return try {
        val day = LocalDate.of(date.substring(0, 4).toInt(), date.substring(4, 6).toInt(), date.substring(6).toInt())
        if (day.year == 0) return null
        day.atTime(LocalTime.of(time.substring(0, 2).toInt(), time.substring(2).toInt())).toInstant(ZoneOffset.ofHours(9))
    } catch (_: DateTimeException) { null }
}

/** Use only for a decoder with a confirmed KST contract, not UTC archive files. */
fun validateKmaRowTime(row: KmaRowTime, expectedX: Int, expectedY: Int, expectedIssue: Instant, receivedAt: Instant): KmaForecastTime? {
    if (row.nx != expectedX || row.ny != expectedY) return null
    val issued = kst(row.baseDate, row.baseTime) ?: return null
    val valid = kst(row.fcstDate, row.fcstTime) ?: return null
    if (issued != expectedIssue || issued > receivedAt || valid < issued) return null
    return KmaForecastTime(issued, valid)
}

enum class HourlyField(val key: String, val metric: WeatherMetric, val precedingHour: Boolean) {
    TEMPERATURE("temperature_2m", WeatherMetric.TEMPERATURE, false),
    FEELS_LIKE("apparent_temperature", WeatherMetric.FEELS_LIKE, false),
    HUMIDITY("relative_humidity_2m", WeatherMetric.RELATIVE_HUMIDITY, false),
    PROBABILITY("precipitation_probability", WeatherMetric.PRECIPITATION_PROBABILITY, true),
    WIND("wind_speed_10m", WeatherMetric.WIND_SPEED, false),
    RAIN("rain", WeatherMetric.FORECAST_RAIN_DEPTH, true),
    SHOWERS("showers", WeatherMetric.FORECAST_RAIN_DEPTH, true),
}

data class HourlyColumn(val key: String, val unit: String, val values: List<Double?>)
data class ForecastDatum(val field: HourlyField, val validAt: Instant, val windowStart: Instant?, val quantity: QuantityResult)
enum class ForecastInputError { SHAPE, TIME, FIELD, UNIT, VALUE }
sealed interface OpenMeteoHourlyResult {
    data class Accepted(val data: List<ForecastDatum>, val liquidRain: List<ForecastRainInterval>, val receivedAt: Instant) : OpenMeteoHourlyResult
    data class Rejected(val reason: ForecastInputError) : OpenMeteoHourlyResult
}

private fun unit(field: HourlyField, raw: String): WeatherUnit? = when (field) {
    HourlyField.TEMPERATURE, HourlyField.FEELS_LIKE -> when (raw) { "°C" -> WeatherUnit.CELSIUS; "°F" -> WeatherUnit.FAHRENHEIT; else -> null }
    HourlyField.HUMIDITY, HourlyField.PROBABILITY -> if (raw == "%") WeatherUnit.PERCENT else null
    HourlyField.WIND -> when (raw) { "km/h" -> WeatherUnit.KILOMETERS_PER_HOUR; "m/s" -> WeatherUnit.METERS_PER_SECOND; "mph" -> WeatherUnit.MILES_PER_HOUR; else -> null }
    HourlyField.RAIN, HourlyField.SHOWERS -> when (raw) { "mm" -> WeatherUnit.MILLIMETER; "inch" -> WeatherUnit.INCH; else -> null }
}

/**
 * Decode a single requested UTC hourly forecast batch after structural JSON parsing.
 * Require stable inputs. Validate the entire batch before returning data.
 * Use unix seconds and zero offset. Keep model issue time unknown.
 * Combine large-scale rain and showers only; exclude snow and total precipitation.
 * No result grants access, confirms provenance or establishes freshness.
 */
fun decodeOpenMeteoHourly(
    epochSeconds: List<Long>, offsetSeconds: Int, timeUnit: String,
    columns: List<HourlyColumn>, expectedFields: Set<HourlyField>,
    receivedAt: Instant, maxHours: Int,
): OpenMeteoHourlyResult {
    fun reject(reason: ForecastInputError) = OpenMeteoHourlyResult.Rejected(reason)
    if (maxHours <= 0 || epochSeconds.isEmpty() || epochSeconds.size > maxHours || columns.isEmpty() || columns.size > HourlyField.entries.size) return reject(ForecastInputError.SHAPE)
    if (offsetSeconds != 0 || timeUnit != "unixtime") return reject(ForecastInputError.TIME)
    val times = ArrayList<Instant>(epochSeconds.size)
    for (seconds in epochSeconds) {
        if (seconds % 3600L != 0L) return reject(ForecastInputError.TIME)
        val instant = try { Instant.ofEpochSecond(seconds) } catch (_: DateTimeException) { return reject(ForecastInputError.TIME) }
        if (times.isNotEmpty() && seconds - times.last().epochSecond != 3600L) return reject(ForecastInputError.TIME)
        times.add(instant)
    }
    val fields = HashSet<HourlyField>()
    val data = ArrayList<ForecastDatum>()
    val rain = HashMap<HourlyField, List<Double?>>()
    for (column in columns) {
        val field = HourlyField.entries.firstOrNull { it.key == column.key } ?: return reject(ForecastInputError.FIELD)
        if (!fields.add(field) || field !in expectedFields) return reject(ForecastInputError.FIELD)
        if (column.values.size != times.size) return reject(ForecastInputError.SHAPE)
        val sourceUnit = unit(field, column.unit) ?: return reject(ForecastInputError.UNIT)
        val depths = ArrayList<Double?>()
        for ((index, time) in times.withIndex()) {
            val q = normalizeWeatherQuantity(field.metric, sourceUnit, column.values[index])
            if (q is QuantityResult.Rejected) return reject(ForecastInputError.VALUE)
            val start = if (field.precedingHour) try { time.minusSeconds(3600) } catch (_: DateTimeException) { return reject(ForecastInputError.TIME) } else null
            data.add(ForecastDatum(field, time, start, q))
            if (field == HourlyField.RAIN || field == HourlyField.SHOWERS) depths.add((q as? QuantityResult.Value)?.value)
        }
        if (field == HourlyField.RAIN || field == HourlyField.SHOWERS) rain[field] = depths
    }
    if (fields != expectedFields) return reject(ForecastInputError.FIELD)
    val intervals = ArrayList<ForecastRainInterval>()
    if (rain.isNotEmpty()) {
        val large = rain[HourlyField.RAIN] ?: return reject(ForecastInputError.FIELD)
        val showers = rain[HourlyField.SHOWERS] ?: return reject(ForecastInputError.FIELD)
        for ((index, time) in times.withIndex()) {
            val a = large[index]
            val b = showers[index]
            val sum = if (a == null || b == null) null else a + b
            if (sum != null && !sum.isFinite()) return reject(ForecastInputError.VALUE)
            intervals.add(ForecastRainInterval(time.minusSeconds(3600), time, sum, WeatherUnit.MILLIMETER))
        }
    }
    return OpenMeteoHourlyResult.Accepted(Collections.unmodifiableList(data), Collections.unmodifiableList(intervals), receivedAt)
}
