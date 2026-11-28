package io.github.scarlel96.aura.weather

import java.util.Random
import kotlin.math.abs

private val temp = WeatherMetric.TEMPERATURE
private val hum = WeatherMetric.RELATIVE_HUMIDITY
private val prob = WeatherMetric.PRECIPITATION_PROBABILITY
private val obs = WeatherMetric.OBSERVED_RAIN_DEPTH
private val forecast = WeatherMetric.FORECAST_RAIN_DEPTH
private val wind = WeatherMetric.WIND_SPEED
private fun n(m: WeatherMetric, u: WeatherUnit, v: Double?) = normalizeWeatherQuantity(m, u, v)
private fun bad(reason: QuantityError) = QuantityResult.Rejected(reason)
private fun expect(m: WeatherMetric, u: WeatherUnit, v: Double?, out: WeatherUnit, expected: Double) {
    val result = n(m, u, v) as QuantityResult.Value
    check(result.metric == m && result.unit == out)
    check(abs(result.value - expected) <= 1e-10 * maxOf(1.0, abs(expected)))
}

fun main() {
    val tests: List<Pair<String, () -> Unit>> = listOf(
        "missingIsNotZero" to {
            check(n(obs, WeatherUnit.MILLIMETER, null) == QuantityResult.Missing)
            check(n(obs, WeatherUnit.MILLIMETER, 0.0) == QuantityResult.Value(obs, WeatherUnit.MILLIMETER, 0.0))
        },
        "missingWithWrongUnitRejected" to { check(n(temp, WeatherUnit.INCH, null) == bad(QuantityError.UNIT_MISMATCH)) },
        "nonFiniteRejected" to { for (x in listOf(Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY)) check(n(temp, WeatherUnit.CELSIUS, x) == bad(QuantityError.NON_FINITE)) },
        "celsiusIdentity" to { expect(temp, WeatherUnit.CELSIUS, -10.5, WeatherUnit.CELSIUS, -10.5) },
        "fahrenheitFreezingBoilingAndNegative" to { for ((f,c) in listOf(32.0 to 0.0,212.0 to 100.0,-40.0 to -40.0)) expect(temp, WeatherUnit.FAHRENHEIT, f, WeatherUnit.CELSIUS, c) },
        "kelvinConversion" to { expect(temp, WeatherUnit.KELVIN, 273.15, WeatherUnit.CELSIUS, 0.0) },
        "temperaturePhysicalFloor" to { for ((u,v) in listOf(WeatherUnit.CELSIUS to -273.15,WeatherUnit.FAHRENHEIT to -459.67,WeatherUnit.KELVIN to 0.0)) { expect(temp,u,v,WeatherUnit.CELSIUS,-273.15); check(n(temp,u,Math.nextDown(v)) == bad(QuantityError.OUT_OF_RANGE)) } },
        "feelsLikeIdentityPreserved" to { expect(WeatherMetric.FEELS_LIKE, WeatherUnit.FAHRENHEIT, 14.0, WeatherUnit.CELSIUS, -10.0) },
        "percentBoundary" to { for (m in listOf(hum,prob)) { expect(m,WeatherUnit.PERCENT,0.0,WeatherUnit.PERCENT,0.0); expect(m,WeatherUnit.PERCENT,100.0,WeatherUnit.PERCENT,100.0); check(n(m,WeatherUnit.PERCENT,Math.nextUp(100.0)) == bad(QuantityError.OUT_OF_RANGE)); check(n(m,WeatherUnit.PERCENT,-0.1) == bad(QuantityError.OUT_OF_RANGE)) } },
        "fractionBoundary" to { for (m in listOf(hum,prob)) { expect(m,WeatherUnit.FRACTION,1.0,WeatherUnit.PERCENT,100.0); expect(m,WeatherUnit.FRACTION,0.0,WeatherUnit.PERCENT,0.0); check(n(m,WeatherUnit.FRACTION,Math.nextUp(1.0)) == bad(QuantityError.OUT_OF_RANGE)); check(n(m,WeatherUnit.FRACTION,-0.01) == bad(QuantityError.OUT_OF_RANGE)) } },
        "fractionAndPercentExplicit" to { expect(prob,WeatherUnit.FRACTION,0.7,WeatherUnit.PERCENT,70.0); expect(prob,WeatherUnit.PERCENT,0.7,WeatherUnit.PERCENT,0.7) },
        "rainDepthUnitsAndFieldIdentity" to { for (m in listOf(obs,forecast)) { expect(m,WeatherUnit.INCH,2.0,WeatherUnit.MILLIMETER,50.8); expect(m,WeatherUnit.MILLIMETER,2.0,WeatherUnit.MILLIMETER,2.0) }; check(n(obs,WeatherUnit.INCH,1.0) != n(forecast,WeatherUnit.INCH,1.0)) },
        "negativeRainRejected" to { for (m in listOf(obs,forecast)) for (u in listOf(WeatherUnit.INCH,WeatherUnit.MILLIMETER)) check(n(m,u,-0.001)==bad(QuantityError.OUT_OF_RANGE)) },
        "windConversions" to { expect(wind,WeatherUnit.KILOMETERS_PER_HOUR,36.0,WeatherUnit.METERS_PER_SECOND,10.0); expect(wind,WeatherUnit.MILES_PER_HOUR,10.0,WeatherUnit.METERS_PER_SECOND,4.4704); expect(wind,WeatherUnit.METERS_PER_SECOND,4.0,WeatherUnit.METERS_PER_SECOND,4.0) },
        "negativeWindRejected" to { for (u in listOf(WeatherUnit.METERS_PER_SECOND,WeatherUnit.KILOMETERS_PER_HOUR,WeatherUnit.MILES_PER_HOUR)) check(n(wind,u,-1.0)==bad(QuantityError.OUT_OF_RANGE)) },
        "overflowRejected" to { check(n(obs,WeatherUnit.INCH,Double.MAX_VALUE)==bad(QuantityError.CONVERSION_OVERFLOW)); expect(obs,WeatherUnit.MILLIMETER,Double.MAX_VALUE,WeatherUnit.MILLIMETER,Double.MAX_VALUE) },
        "underflowDoesNotBecomeZero" to { for (u in listOf(WeatherUnit.KILOMETERS_PER_HOUR,WeatherUnit.MILES_PER_HOUR)) check(n(wind,u,Double.MIN_VALUE)==bad(QuantityError.CONVERSION_UNDERFLOW)); check((n(wind,WeatherUnit.METERS_PER_SECOND,Double.MIN_VALUE) as QuantityResult.Value).value == Double.MIN_VALUE) },
        "negativeZeroCanonicalized" to { val result = n(obs,WeatherUnit.INCH,-0.0) as QuantityResult.Value; check(result.value.toRawBits()==0L) },
        "crossUnitMatrix" to {
            val allowed = mapOf(temp to setOf(WeatherUnit.CELSIUS,WeatherUnit.FAHRENHEIT,WeatherUnit.KELVIN), WeatherMetric.FEELS_LIKE to setOf(WeatherUnit.CELSIUS,WeatherUnit.FAHRENHEIT,WeatherUnit.KELVIN),hum to setOf(WeatherUnit.PERCENT,WeatherUnit.FRACTION),prob to setOf(WeatherUnit.PERCENT,WeatherUnit.FRACTION),obs to setOf(WeatherUnit.INCH,WeatherUnit.MILLIMETER),forecast to setOf(WeatherUnit.INCH,WeatherUnit.MILLIMETER),wind to setOf(WeatherUnit.METERS_PER_SECOND,WeatherUnit.KILOMETERS_PER_HOUR,WeatherUnit.MILES_PER_HOUR))
            for (m in WeatherMetric.entries) for (u in WeatherUnit.entries) if (u in allowed.getValue(m)) check(n(m,u,0.0) is QuantityResult.Value) else check(n(m,u,0.0)==bad(QuantityError.UNIT_MISMATCH))
        },
        "seededConversionInvariants" to { val rng=Random(20261128L); repeat(20000) { val c=rng.nextDouble()*300-100; expect(temp,WeatherUnit.FAHRENHEIT,c*1.8+32,WeatherUnit.CELSIUS,c); val p=rng.nextDouble(); expect(prob,WeatherUnit.FRACTION,p,WeatherUnit.PERCENT,p*100); val speed=rng.nextDouble()*100; expect(wind,WeatherUnit.KILOMETERS_PER_HOUR,speed*3.6,WeatherUnit.METERS_PER_SECOND,speed) } },
    )
    check(tests.size == 20 && tests.map { it.first }.toSet().size == tests.size)
    for ((name,test) in tests) { test(); println("PASS $name") }
    println("QUANTITY_RESULT 20 PASS / 0 FAIL; seed=20261128 cases=20000 conversions=60000")
}
