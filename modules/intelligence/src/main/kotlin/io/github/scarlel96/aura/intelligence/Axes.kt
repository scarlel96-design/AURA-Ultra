package io.github.scarlel96.aura.intelligence

enum class FocusBand {
    CRITICAL,
    POWER,
    EXERCISE,
    WEATHER,
    CONTEXT,
    DECORATIVE,
}

enum class PowerAxis {
    NORMAL,
    LOW,
    CHARGING,
}

enum class WeatherAxis {
    NORMAL,
    PRECIP,
    ALERT,
    UNKNOWN,
}

enum class ActivityAxis {
    REST,
    ACTIVE,
    EXERCISE,
    UNKNOWN,
}

enum class LightAxis {
    DAY,
    NIGHT,
}

enum class ConnectivityAxis {
    ONLINE,
    OFFLINE,
}

enum class UserModeAxis {
    DEFAULT,
    WORK,
    SLEEP,
    MANUAL,
}

enum class QualityCandidate {
    BALANCED,
    ECO,
    AOD,
}

enum class DataQuality {
    SETTINGS_ONLY,
    FRESH,
    DEGRADED,
}

enum class ReasonCode {
    POLICY_REJECTED,
    CLOCK_INVERSION,
    REVISION_EXHAUSTED,
    DEBOUNCE,
    MINIMUM_HOLD,
    URGENT,
    CHARGING_EXCEPTION,
    STALE_IGNORED,
    UNDECLARED_IGNORED,
    DENIED_IGNORED,
    ERROR_IGNORED,
    UNAVAILABLE_IGNORED,
    REJECTED_IGNORED,
    INCONSISTENT_IGNORED,
    UNIT_UNCHECKED,
    OUTSIDE_CANDIDATE_SCALE,
    TOKEN_UNCHECKED,
    POWER_LOW,
    POWER_CHARGING,
    WEATHER_ALERT,
    WEATHER_PRECIP,
    EXERCISE,
    CONTEXT,
    DECORATIVE,
    MOTION_REDUCTION,
    AOD,
    OFFLINE,
    FUTURE_OBSERVATION,
    SUPERSEDED_OBSERVATION,
    DUPLICATE_OBSERVATION,
    OBSERVATION_CONFLICT,
    FORECAST_SEPARATE,
}

enum class UnusableReason {
    REJECTED,
    STALE,
    UNDECLARED,
    UNAVAILABLE,
    DENIED,
    ERROR,
    INCONSISTENT,
    UNIT_UNCHECKED,
    OUTSIDE_CANDIDATE_SCALE,
    TOKEN_UNCHECKED,
    FUTURE_OBSERVATION,
}

fun UnusableReason.toReasonCode(): ReasonCode {
    return when (this) {
        UnusableReason.REJECTED -> ReasonCode.REJECTED_IGNORED
        UnusableReason.STALE -> ReasonCode.STALE_IGNORED
        UnusableReason.UNDECLARED -> ReasonCode.UNDECLARED_IGNORED
        UnusableReason.UNAVAILABLE -> ReasonCode.UNAVAILABLE_IGNORED
        UnusableReason.DENIED -> ReasonCode.DENIED_IGNORED
        UnusableReason.ERROR -> ReasonCode.ERROR_IGNORED
        UnusableReason.INCONSISTENT -> ReasonCode.INCONSISTENT_IGNORED
        UnusableReason.UNIT_UNCHECKED -> ReasonCode.UNIT_UNCHECKED
        UnusableReason.OUTSIDE_CANDIDATE_SCALE -> ReasonCode.OUTSIDE_CANDIDATE_SCALE
        UnusableReason.TOKEN_UNCHECKED -> ReasonCode.TOKEN_UNCHECKED
        UnusableReason.FUTURE_OBSERVATION -> ReasonCode.FUTURE_OBSERVATION
    }
}
