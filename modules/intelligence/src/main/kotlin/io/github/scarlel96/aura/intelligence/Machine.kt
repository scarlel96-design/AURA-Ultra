package io.github.scarlel96.aura.intelligence

import io.github.scarlel96.aura.domain.Observation
import io.github.scarlel96.aura.domain.draft.PresentationIntentDraft
import java.time.Instant

data class IntelligenceSample(
    val referenceTime: Instant,
    val batteryPercent: Observation<Double>? = null,
    val charging: Observation<Boolean>? = null,
    val precipitationProbability: Observation<Double>? = null,
    val weatherAlert: Observation<Boolean>? = null,
    val activity: Observation<String>? = null,
    val light: Observation<String>? = null,
    val connectivity: Observation<String>? = null,
    val userMode: Observation<String>? = null,
    val motionReduction: Boolean = false,
    val ambientDisplay: Boolean = false,
)

data class PendingSensors(
    val power: PowerAxis,
    val weather: WeatherAxis,
    val activity: ActivityAxis,
    val since: Instant,
)

data class Emission(
    val quality: QualityCandidate,
    val motionAllowed: Boolean,
    val particleEffectsAllowed: Boolean,
    val weatherNumbersKept: Boolean,
    val timeKept: Boolean,
    val publishedBatteryPercent: Double?,
    val publishedPrecipitation: Double?,
    val dataQuality: DataQuality,
    val reasonCodes: List<ReasonCode>,
)

data class MachineState(
    val power: PowerAxis,
    val weather: WeatherAxis,
    val activity: ActivityAxis,
    val light: LightAxis,
    val connectivity: ConnectivityAxis,
    val userMode: UserModeAxis,
    val focus: FocusBand,
    val committedAt: Instant,
    val revision: Long,
    val pending: PendingSensors?,
    val emission: Emission,
)

data class IntelligenceIntent(
    val focus: FocusBand,
    val quality: QualityCandidate,
    val motionAllowed: Boolean,
    val particleEffectsAllowed: Boolean,
    val weatherNumbersKept: Boolean,
    val timeKept: Boolean,
    val publishedBatteryPercent: Double?,
    val publishedPrecipitation: Double?,
    val dataQuality: DataQuality,
    val reasonCodes: List<ReasonCode>,
    val revision: Long,
) {
    fun toPresentationDraft(): PresentationIntentDraft {
        return PresentationIntentDraft(
            focus = focus.name,
            paletteId = null,
            quality = quality.name,
            motionAllowed = motionAllowed,
            reasonCodes = reasonCodes.map { it.name },
            revision = revision,
        )
    }
}

fun IntelligenceIntent.emission(): Emission {
    return Emission(
        quality = quality,
        motionAllowed = motionAllowed,
        particleEffectsAllowed = particleEffectsAllowed,
        weatherNumbersKept = weatherNumbersKept,
        timeKept = timeKept,
        publishedBatteryPercent = publishedBatteryPercent,
        publishedPrecipitation = publishedPrecipitation,
        dataQuality = dataQuality,
        reasonCodes = reasonCodes,
    )
}

sealed class StepResult {
    data class PolicyRejected(val issues: List<String>) : StepResult()

    data class Advanced(
        val state: MachineState,
        val intent: IntelligenceIntent,
    ) : StepResult()
}

fun step(
    previous: MachineState?,
    sample: IntelligenceSample,
    policy: PolicyCandidates,
): StepResult {
    val policyIssues = policy.issues()
    if (policyIssues.isNotEmpty()) {
        return StepResult.PolicyRejected(policyIssues)
    }
    if (previous != null && sample.referenceTime < previous.committedAt) {
        return finish(
            skeleton = previous,
            intent = intentFor(
                state = previous,
                sample = sample,
                policy = policy,
                extraReasons = listOf(ReasonCode.CLOCK_INVERSION),
                publishedBattery = null,
                publishedPrecipitation = null,
                dataQuality = DataQuality.DEGRADED,
            ),
            previous = previous,
        )
    }
    val gated = gateSample(sample, policy)
    val reasons = mutableListOf<ReasonCode>()
    reasons += gated.reasons
    val desiredPower = desiredPower(gated.charging, gated.battery, previous?.power, policy)
    val desiredWeather = desiredWeather(gated.alert, gated.precipitation, previous?.weather, policy)
    val desiredActivity = when (val activity = gated.activity) {
        Channel.Absent -> previous?.activity ?: ActivityAxis.UNKNOWN
        is Channel.Fresh -> activity.value
        is Channel.Unusable -> ActivityAxis.UNKNOWN
    }
    val light = when (val channel = gated.light) {
        Channel.Absent -> previous?.light ?: LightAxis.DAY
        is Channel.Fresh -> channel.value
        is Channel.Unusable -> previous?.light ?: LightAxis.DAY
    }
    val connectivity = when (val channel = gated.connectivity) {
        Channel.Absent -> previous?.connectivity ?: ConnectivityAxis.ONLINE
        is Channel.Fresh -> channel.value
        is Channel.Unusable -> previous?.connectivity ?: ConnectivityAxis.ONLINE
    }
    val userMode = when (val channel = gated.userMode) {
        Channel.Absent -> previous?.userMode ?: UserModeAxis.DEFAULT
        is Channel.Fresh -> channel.value
        is Channel.Unusable -> previous?.userMode ?: UserModeAxis.DEFAULT
    }
    val publishedBattery = (gated.battery as? Channel.Fresh)?.value
    val publishedPrecipitation = (gated.precipitation as? Channel.Fresh)?.value
    if (previous == null) {
        val created = assemble(
            power = desiredPower,
            weather = desiredWeather,
            activity = desiredActivity,
            light = light,
            connectivity = connectivity,
            userMode = userMode,
            committedAt = sample.referenceTime,
            revision = 1L,
            pending = null,
        )
        return finish(
            skeleton = created,
            intent = intentFor(
                state = created,
                sample = sample,
                policy = policy,
                extraReasons = reasons,
                publishedBattery = publishedBattery,
                publishedPrecipitation = publishedPrecipitation,
                dataQuality = gated.quality,
            ),
            previous = null,
        )
    }
    val sensorChanged = desiredPower != previous.power ||
        desiredWeather != previous.weather ||
        desiredActivity != previous.activity
    val urgent = desiredWeather == WeatherAxis.ALERT && previous.weather != WeatherAxis.ALERT
    val chargingException = desiredPower == PowerAxis.CHARGING && previous.power != PowerAxis.CHARGING ||
        previous.power == PowerAxis.CHARGING && desiredPower != PowerAxis.CHARGING
    val pending = if (!sensorChanged) {
        null
    } else if (urgent || chargingException) {
        null
    } else {
        val currentPending = previous.pending
        if (currentPending == null ||
            currentPending.power != desiredPower ||
            currentPending.weather != desiredWeather ||
            currentPending.activity != desiredActivity ||
            sample.referenceTime < currentPending.since
        ) {
            PendingSensors(desiredPower, desiredWeather, desiredActivity, sample.referenceTime)
        } else {
            currentPending
        }
    }
    val debounceElapsed = pending == null || !sample.referenceTime.isBefore(pending.since.plus(policy.debounce))
    val holdElapsed = !sample.referenceTime.isBefore(previous.committedAt.plus(policy.minimumHold))
    val commitSensors = sensorChanged && (urgent || chargingException || (pending == null) || (debounceElapsed && holdElapsed))
    if (commitSensors && urgent) {
        reasons += ReasonCode.URGENT
    }
    if (commitSensors && chargingException) {
        reasons += ReasonCode.CHARGING_EXCEPTION
    }
    if (sensorChanged && !commitSensors) {
        if (pending != null && sample.referenceTime.isBefore(pending.since.plus(policy.debounce))) {
            reasons += ReasonCode.DEBOUNCE
        }
        if (!holdElapsed && !urgent && !chargingException) {
            reasons += ReasonCode.MINIMUM_HOLD
        }
    }
    val power = if (commitSensors) desiredPower else previous.power
    val weather = if (commitSensors) desiredWeather else previous.weather
    val activity = if (commitSensors) desiredActivity else previous.activity
    val committedAt = if (commitSensors) sample.referenceTime else previous.committedAt
    val keptPending = if (commitSensors || !sensorChanged) null else pending
    val next = assemble(
        power = power,
        weather = weather,
        activity = activity,
        light = light,
        connectivity = connectivity,
        userMode = userMode,
        committedAt = committedAt,
        revision = previous.revision,
        pending = keptPending,
    )
    return finish(
        skeleton = next,
        intent = intentFor(
            state = next,
            sample = sample,
            policy = policy,
            extraReasons = reasons,
            publishedBattery = publishedBattery,
            publishedPrecipitation = publishedPrecipitation,
            dataQuality = gated.quality,
        ),
        previous = previous,
    )
}

private fun finish(
    skeleton: MachineState,
    intent: IntelligenceIntent,
    previous: MachineState?,
): StepResult.Advanced {
    val emission = intent.emission()
    val axesChanged = previous != null && (
        skeleton.power != previous.power ||
            skeleton.weather != previous.weather ||
            skeleton.activity != previous.activity ||
            skeleton.light != previous.light ||
            skeleton.connectivity != previous.connectivity ||
            skeleton.userMode != previous.userMode ||
            skeleton.focus != previous.focus
        )
    val emissionChanged = previous != null && emission != previous.emission
    val revision = when {
        previous == null -> 1L
        axesChanged || emissionChanged -> previous.revision + 1
        else -> previous.revision
    }
    return StepResult.Advanced(
        state = skeleton.copy(revision = revision, emission = emission),
        intent = intent.copy(revision = revision),
    )
}

private data class GatedSample(
    val battery: Channel<Double>,
    val charging: Channel<Boolean>,
    val precipitation: Channel<Double>,
    val alert: Channel<Boolean>,
    val activity: Channel<ActivityAxis>,
    val light: Channel<LightAxis>,
    val connectivity: Channel<ConnectivityAxis>,
    val userMode: Channel<UserModeAxis>,
    val reasons: List<ReasonCode>,
    val quality: DataQuality,
)

private fun gateSample(sample: IntelligenceSample, policy: PolicyCandidates): GatedSample {
    val battery = gateDouble(
        sample.batteryPercent,
        sample.referenceTime,
        policy.percentUnit,
        policy.percentMinimum,
        policy.percentMaximum,
    )
    val charging = gateFlag(sample.charging, sample.referenceTime, policy.flagUnit)
    val precipitation = gateDouble(
        sample.precipitationProbability,
        sample.referenceTime,
        policy.probabilityUnit,
        policy.probabilityMinimum,
        policy.probabilityMaximum,
    )
    val alert = gateFlag(sample.weatherAlert, sample.referenceTime, policy.flagUnit)
    val activity = gateToken(sample.activity, sample.referenceTime, policy.tokenUnit, ::parseActivity)
    val light = gateToken(sample.light, sample.referenceTime, policy.tokenUnit, ::parseLight)
    val connectivity = gateToken(sample.connectivity, sample.referenceTime, policy.tokenUnit, ::parseConnectivity)
    val userMode = gateToken(sample.userMode, sample.referenceTime, policy.tokenUnit, ::parseUserMode)
    val channels = listOf(battery, charging, precipitation, alert, activity, light, connectivity, userMode)
    val reasons = channels.mapNotNull { channel ->
        (channel as? Channel.Unusable)?.reason?.toReasonCode()
    }.distinct()
    val supplied = channels.filter { it !is Channel.Absent }
    val quality = when {
        supplied.isEmpty() -> DataQuality.SETTINGS_ONLY
        supplied.all { it is Channel.Fresh<*> } -> DataQuality.FRESH
        else -> DataQuality.DEGRADED
    }
    return GatedSample(
        battery,
        charging,
        precipitation,
        alert,
        activity,
        light,
        connectivity,
        userMode,
        reasons,
        quality,
    )
}

private fun desiredPower(
    charging: Channel<Boolean>,
    battery: Channel<Double>,
    previous: PowerAxis?,
    policy: PolicyCandidates,
): PowerAxis {
    if (charging is Channel.Fresh && charging.value) {
        return PowerAxis.CHARGING
    }
    return when (battery) {
        is Channel.Fresh -> {
            val low = lowPower(battery.value, previous == PowerAxis.LOW, policy)
            if (low) PowerAxis.LOW else PowerAxis.NORMAL
        }
        Channel.Absent -> when (charging) {
            is Channel.Fresh ->
                if (previous == PowerAxis.CHARGING) PowerAxis.NORMAL else previous ?: PowerAxis.NORMAL
            is Channel.Unusable -> previous ?: PowerAxis.NORMAL
            Channel.Absent -> previous ?: PowerAxis.NORMAL
        }
        is Channel.Unusable -> previous ?: PowerAxis.NORMAL
    }
}

private fun desiredWeather(
    alert: Channel<Boolean>,
    precipitation: Channel<Double>,
    previous: WeatherAxis?,
    policy: PolicyCandidates,
): WeatherAxis {
    if (alert is Channel.Fresh && alert.value) {
        return WeatherAxis.ALERT
    }
    return when (precipitation) {
        is Channel.Fresh -> {
            val active = precipActive(precipitation.value, previous == WeatherAxis.PRECIP, policy)
            if (active) WeatherAxis.PRECIP else WeatherAxis.NORMAL
        }
        Channel.Absent -> when (alert) {
            is Channel.Fresh ->
                if (previous == WeatherAxis.ALERT) WeatherAxis.NORMAL else previous ?: WeatherAxis.NORMAL
            is Channel.Unusable -> WeatherAxis.UNKNOWN
            Channel.Absent -> previous ?: WeatherAxis.NORMAL
        }
        is Channel.Unusable -> WeatherAxis.UNKNOWN
    }
}

private fun lowPower(value: Double, previousLow: Boolean, policy: PolicyCandidates): Boolean {
    if (value <= policy.powerEnterPercent) {
        return true
    }
    if (value >= policy.powerExitPercent) {
        return false
    }
    return previousLow
}

private fun precipActive(value: Double, previousActive: Boolean, policy: PolicyCandidates): Boolean {
    if (value >= policy.precipEnter) {
        return true
    }
    if (value <= policy.precipExit) {
        return false
    }
    return previousActive
}

private fun assemble(
    power: PowerAxis,
    weather: WeatherAxis,
    activity: ActivityAxis,
    light: LightAxis,
    connectivity: ConnectivityAxis,
    userMode: UserModeAxis,
    committedAt: Instant,
    revision: Long,
    pending: PendingSensors?,
): MachineState {
    return MachineState(
        power = power,
        weather = weather,
        activity = activity,
        light = light,
        connectivity = connectivity,
        userMode = userMode,
        focus = focusOf(power, weather, activity, light, connectivity, userMode),
        committedAt = committedAt,
        revision = revision,
        pending = pending,
        emission = Emission(
            quality = QualityCandidate.BALANCED,
            motionAllowed = true,
            particleEffectsAllowed = true,
            weatherNumbersKept = true,
            timeKept = true,
            publishedBatteryPercent = null,
            publishedPrecipitation = null,
            dataQuality = DataQuality.SETTINGS_ONLY,
            reasonCodes = emptyList(),
        ),
    )
}

fun focusOf(
    power: PowerAxis,
    weather: WeatherAxis,
    activity: ActivityAxis,
    light: LightAxis,
    connectivity: ConnectivityAxis,
    userMode: UserModeAxis,
): FocusBand {
    if (weather == WeatherAxis.ALERT) {
        return FocusBand.CRITICAL
    }
    if (power == PowerAxis.LOW) {
        return FocusBand.POWER
    }
    if (activity == ActivityAxis.EXERCISE) {
        return FocusBand.EXERCISE
    }
    if (weather == WeatherAxis.PRECIP) {
        return FocusBand.WEATHER
    }
    if (userMode != UserModeAxis.DEFAULT || connectivity == ConnectivityAxis.OFFLINE || light == LightAxis.NIGHT || activity == ActivityAxis.ACTIVE) {
        return FocusBand.CONTEXT
    }
    return FocusBand.DECORATIVE
}

private fun intentFor(
    state: MachineState,
    sample: IntelligenceSample,
    policy: PolicyCandidates,
    extraReasons: List<ReasonCode>,
    publishedBattery: Double?,
    publishedPrecipitation: Double?,
    dataQuality: DataQuality,
): IntelligenceIntent {
    val quality = when {
        sample.ambientDisplay -> QualityCandidate.AOD
        state.power == PowerAxis.LOW -> QualityCandidate.ECO
        else -> QualityCandidate.BALANCED
    }
    val motionAllowed = !sample.motionReduction &&
        !sample.ambientDisplay &&
        state.power != PowerAxis.LOW
    val reasons = buildList {
        addAll(extraReasons)
        when (state.focus) {
            FocusBand.CRITICAL -> add(ReasonCode.WEATHER_ALERT)
            FocusBand.POWER -> add(ReasonCode.POWER_LOW)
            FocusBand.EXERCISE -> add(ReasonCode.EXERCISE)
            FocusBand.WEATHER -> add(ReasonCode.WEATHER_PRECIP)
            FocusBand.CONTEXT -> add(ReasonCode.CONTEXT)
            FocusBand.DECORATIVE -> add(ReasonCode.DECORATIVE)
        }
        if (state.power == PowerAxis.CHARGING) {
            add(ReasonCode.POWER_CHARGING)
        }
        if (state.connectivity == ConnectivityAxis.OFFLINE) {
            add(ReasonCode.OFFLINE)
        }
        if (sample.motionReduction) {
            add(ReasonCode.MOTION_REDUCTION)
        }
        if (sample.ambientDisplay) {
            add(ReasonCode.AOD)
        }
    }.distinct()
    return IntelligenceIntent(
        focus = state.focus,
        quality = quality,
        motionAllowed = motionAllowed,
        particleEffectsAllowed = motionAllowed,
        weatherNumbersKept = true,
        timeKept = true,
        publishedBatteryPercent = publishedBattery,
        publishedPrecipitation = publishedPrecipitation,
        dataQuality = dataQuality,
        reasonCodes = reasons,
        revision = state.revision,
    )
}

private fun parseActivity(token: String): ActivityAxis? {
    return when (token) {
        "REST" -> ActivityAxis.REST
        "ACTIVE" -> ActivityAxis.ACTIVE
        "EXERCISE" -> ActivityAxis.EXERCISE
        else -> null
    }
}

private fun parseLight(token: String): LightAxis? {
    return when (token) {
        "DAY" -> LightAxis.DAY
        "NIGHT" -> LightAxis.NIGHT
        else -> null
    }
}

private fun parseConnectivity(token: String): ConnectivityAxis? {
    return when (token) {
        "ONLINE" -> ConnectivityAxis.ONLINE
        "OFFLINE" -> ConnectivityAxis.OFFLINE
        else -> null
    }
}

private fun parseUserMode(token: String): UserModeAxis? {
    return when (token) {
        "DEFAULT" -> UserModeAxis.DEFAULT
        "WORK" -> UserModeAxis.WORK
        "SLEEP" -> UserModeAxis.SLEEP
        "MANUAL" -> UserModeAxis.MANUAL
        else -> null
    }
}
