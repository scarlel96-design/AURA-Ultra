package io.github.scarlel96.aura.weather

/** Identify the field before conversion. Do not infer the field from its unit. */
enum class WeatherMetric {
    TEMPERATURE, FEELS_LIKE, RELATIVE_HUMIDITY, PRECIPITATION_PROBABILITY,
    OBSERVED_RAIN_DEPTH, FORECAST_RAIN_DEPTH, WIND_SPEED,
}

enum class WeatherUnit {
    CELSIUS, FAHRENHEIT, KELVIN, PERCENT, FRACTION, MILLIMETER, INCH,
    METERS_PER_SECOND, KILOMETERS_PER_HOUR, MILES_PER_HOUR,
}

enum class QuantityError { UNIT_MISMATCH, NON_FINITE, OUT_OF_RANGE, CONVERSION_OVERFLOW, CONVERSION_UNDERFLOW }

sealed interface QuantityResult {
    data class Value(val metric: WeatherMetric, val unit: WeatherUnit, val value: Double) : QuantityResult
    data object Missing : QuantityResult
    data class Rejected(val reason: QuantityError) : QuantityResult
}

/**
 * Convert a typed scalar to a candidate common unit. Do not assign a data status or grant authority.
 * Supply the actual field and unit from verified provider metadata. Null means an absent scalar only.
 * Convert rain depth, not rain rate. Preserve the caller's observed or forecast field identity.
 * Physical limits are not provider-specific plausibility limits. Validate those separately.
 */
fun normalizeWeatherQuantity(metric: WeatherMetric, unit: WeatherUnit, raw: Double?): QuantityResult {
    val canonical = when (metric) {
        WeatherMetric.TEMPERATURE, WeatherMetric.FEELS_LIKE -> WeatherUnit.CELSIUS
        WeatherMetric.RELATIVE_HUMIDITY, WeatherMetric.PRECIPITATION_PROBABILITY -> WeatherUnit.PERCENT
        WeatherMetric.OBSERVED_RAIN_DEPTH, WeatherMetric.FORECAST_RAIN_DEPTH -> WeatherUnit.MILLIMETER
        WeatherMetric.WIND_SPEED -> WeatherUnit.METERS_PER_SECOND
    }
    val compatible = when (canonical) {
        WeatherUnit.CELSIUS -> unit == WeatherUnit.CELSIUS || unit == WeatherUnit.FAHRENHEIT || unit == WeatherUnit.KELVIN
        WeatherUnit.PERCENT -> unit == WeatherUnit.PERCENT || unit == WeatherUnit.FRACTION
        WeatherUnit.MILLIMETER -> unit == WeatherUnit.MILLIMETER || unit == WeatherUnit.INCH
        WeatherUnit.METERS_PER_SECOND -> unit == WeatherUnit.METERS_PER_SECOND || unit == WeatherUnit.KILOMETERS_PER_HOUR || unit == WeatherUnit.MILES_PER_HOUR
        else -> false
    }
    if (!compatible) return QuantityResult.Rejected(QuantityError.UNIT_MISMATCH)
    if (raw == null) return QuantityResult.Missing
    if (!raw.isFinite()) return QuantityResult.Rejected(QuantityError.NON_FINITE)
    val inRange = when (unit) {
        WeatherUnit.CELSIUS -> raw >= -273.15
        WeatherUnit.FAHRENHEIT -> raw >= -459.67
        WeatherUnit.PERCENT -> raw in 0.0..100.0
        WeatherUnit.FRACTION -> raw in 0.0..1.0
        else -> raw >= 0.0
    }
    if (!inRange) return QuantityResult.Rejected(QuantityError.OUT_OF_RANGE)
    val converted = when (unit) {
        WeatherUnit.FAHRENHEIT -> (raw - 32.0) / 1.8
        WeatherUnit.KELVIN -> raw - 273.15
        WeatherUnit.FRACTION -> raw * 100.0
        WeatherUnit.INCH -> raw * 25.4
        WeatherUnit.KILOMETERS_PER_HOUR -> raw / 3.6
        WeatherUnit.MILES_PER_HOUR -> raw * 0.44704
        else -> raw
    }
    if (!converted.isFinite()) return QuantityResult.Rejected(QuantityError.CONVERSION_OVERFLOW)
    if (canonical != WeatherUnit.CELSIUS && raw != 0.0 && converted == 0.0) {
        return QuantityResult.Rejected(QuantityError.CONVERSION_UNDERFLOW)
    }
    return QuantityResult.Value(metric, canonical, if (converted == 0.0) 0.0 else converted)
}
