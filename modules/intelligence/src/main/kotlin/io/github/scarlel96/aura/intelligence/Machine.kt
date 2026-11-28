package io.github.scarlel96.aura.intelligence

import io.github.scarlel96.aura.domain.ClassifiedValue
import io.github.scarlel96.aura.domain.Freshness
import io.github.scarlel96.aura.domain.Observation
import io.github.scarlel96.aura.domain.ObservationKind
import io.github.scarlel96.aura.domain.classifiedValue
import io.github.scarlel96.aura.domain.draft.PresentationIntentDraft
import java.time.DateTimeException
import java.time.Duration
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
    val batteryRevision: Long? = null,
    val precipitationRevision: Long? = null,
    val resync: Boolean = false,
)

/** 호출자가 준 revision만 저장한다. 없는 revision은 만들지 않는다. */
data class StreamCursor(
    val source: String,
    val observedAt: Instant?,
    val revision: Long?,
    val revoked: Boolean = false,
)

/** 관측 순서와 보관 TTL이다. 처리 시각과 표시 revision이 아니다. */
data class ObservationMemory(
    val battery: StreamCursor? = null,
    val precipitation: StreamCursor? = null,
    val batteryExpiresAt: Instant? = null,
    val precipitationExpiresAt: Instant? = null,
    val charging: StreamCursor? = null,
    val alert: StreamCursor? = null,
    val activity: StreamCursor? = null,
    val light: StreamCursor? = null,
    val connectivity: StreamCursor? = null,
    val userMode: StreamCursor? = null,
)

data class PendingSensors(
    val power: PowerAxis,
    val weather: WeatherAxis,
    val activity: ActivityAxis,
    val since: Instant,
    val powerSince: Instant,
    val weatherSince: Instant,
    val activitySince: Instant,
)

data class Emission(
    val quality: QualityCandidate,
    val motionAllowed: Boolean,
    val particleEffectsAllowed: Boolean,
    val graphicsPowerLimited: Boolean,
    val weatherNumbersKept: Boolean,
    val timeKept: Boolean,
    val publishedBatteryPercent: Double?,
    val publishedPrecipitation: Double?,
    val dataQuality: DataQuality,
    val reasonCodes: List<ReasonCode>,
)

data class CallerSettings(
    val motionReduction: Boolean,
    val ambientDisplay: Boolean,
) {
    fun raisedBy(motionReduction: Boolean, ambientDisplay: Boolean): CallerSettings {
        return CallerSettings(
            motionReduction = this.motionReduction || motionReduction,
            ambientDisplay = this.ambientDisplay || ambientDisplay,
        )
    }
}

data class MachineState(
    val power: PowerAxis,
    val weather: WeatherAxis,
    val activity: ActivityAxis,
    val light: LightAxis,
    val connectivity: ConnectivityAxis,
    val userMode: UserModeAxis,
    val focus: FocusBand,
    val committedAt: Instant,
    val powerCommittedAt: Instant,
    val weatherCommittedAt: Instant,
    val activityCommittedAt: Instant,
    val processedAt: Instant,
    val revision: Long,
    val pending: PendingSensors?,
    val emission: Emission,
    val settings: CallerSettings,
    val observationMemory: ObservationMemory = ObservationMemory(),
)

data class IntelligenceIntent(
    val focus: FocusBand,
    val quality: QualityCandidate,
    val motionAllowed: Boolean,
    val particleEffectsAllowed: Boolean,
    val graphicsPowerLimited: Boolean,
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
        graphicsPowerLimited = graphicsPowerLimited,
        weatherNumbersKept = weatherNumbersKept,
        timeKept = timeKept,
        publishedBatteryPercent = publishedBatteryPercent,
        publishedPrecipitation = publishedPrecipitation,
        dataQuality = dataQuality,
        reasonCodes = reasonCodes,
    )
}

sealed class StepResult {
    abstract val deliverySequence: Long
    abstract val deliveryEpoch: Long
    abstract val deliverySessionOpened: Boolean

    data class PolicyRejected(
        val issues: List<String>,
        val failSafe: IntelligenceIntent?,
        val state: MachineState?,
        override val deliverySequence: Long,
        override val deliveryEpoch: Long = 0L,
        override val deliverySessionOpened: Boolean = false,
    ) : StepResult()

    data class LimitReached(
        val reason: ReasonCode,
        val state: MachineState,
        override val deliverySequence: Long,
        override val deliveryEpoch: Long = 0L,
        override val deliverySessionOpened: Boolean = false,
    ) : StepResult()

    data class Advanced(
        val state: MachineState,
        val intent: IntelligenceIntent,
        override val deliverySequence: Long,
        override val deliveryEpoch: Long = 0L,
        override val deliverySessionOpened: Boolean = false,
    ) : StepResult()
}

fun StepResult.deliveredIntent(): IntelligenceIntent? {
    return when (this) {
        is StepResult.Advanced -> intent
        is StepResult.LimitReached -> null
        is StepResult.PolicyRejected -> null
    }
}

fun step(
    previous: MachineState?,
    sample: IntelligenceSample,
    policy: PolicyCandidates,
    lastDeliverySequence: Long = 0L,
    lastDeliveryEpoch: Long = 0L,
    openDeliverySession: Boolean = false,
): StepResult {
    val delivery = nextDelivery(lastDeliverySequence, lastDeliveryEpoch, openDeliverySession)
    val sequence = delivery.sequence
    val policyIssues = policy.issues()
    if (policyIssues.isNotEmpty()) {
        val retained = retainedAfterRejectedPolicy(previous, sample)
        return StepResult.PolicyRejected(
            issues = policyIssues,
            failSafe = failSafeIntent(retained),
            state = retained,
            deliverySequence = sequence,
            deliveryEpoch = delivery.epoch,
            deliverySessionOpened = delivery.opened,
        )
    }
    if (previous != null && sample.referenceTime < previous.processedAt) {
        val raised = previous.settings.raisedBy(sample.motionReduction, sample.ambientDisplay)
        val skeleton = previous.copy(settings = raised)
        val inversionReasons = listOf(ReasonCode.CLOCK_INVERSION)
        return finish(
            skeleton = skeleton,
            intent = intentFor(
                state = skeleton,
                settings = raised,
                extraReasons = inversionReasons,
                publishedBattery = null,
                publishedPrecipitation = null,
                dataQuality = DataQuality.DEGRADED,
                graphicsLow = previous.emission.graphicsPowerLimited,
            ),
            previous = previous,
            publication = Publication(
                battery = null,
                precipitation = null,
                dataQuality = DataQuality.DEGRADED,
                batteryUnusable = false,
                precipitationUnusable = false,
                graphicsLow = false,
                batteryAccepted = false,
                precipitationAccepted = false,
            ),
            gateReasons = inversionReasons,
            sample = sample,
            delivery = delivery,
        )
    }
    val gated = gateSample(sample, policy)
    val batteryDecision = decideNumber(
        channel = gated.battery,
        observation = sample.batteryPercent,
        revision = sample.batteryRevision,
        previousCursor = previous?.observationMemory?.battery,
        previousPublished = previous?.emission?.publishedBatteryPercent,
        previousExpiresAt = previous?.observationMemory?.batteryExpiresAt,
        allowForecastPublication = false,
    )
    val precipitationDecision = decideNumber(
        channel = gated.precipitation,
        observation = sample.precipitationProbability,
        revision = sample.precipitationRevision,
        previousCursor = previous?.observationMemory?.precipitation,
        previousPublished = previous?.emission?.publishedPrecipitation,
        previousExpiresAt = previous?.observationMemory?.precipitationExpiresAt,
        allowForecastPublication = true,
    )
    val chargingOrder = orderChannel(gated.charging, sample.charging, previous?.observationMemory?.charging)
    val alertOrder = orderChannel(gated.alert, sample.weatherAlert, previous?.observationMemory?.alert)
    val activityOrder = orderChannel(gated.activity, sample.activity, previous?.observationMemory?.activity)
    val lightOrder = orderChannel(gated.light, sample.light, previous?.observationMemory?.light)
    val connectivityOrder = orderChannel(gated.connectivity, sample.connectivity, previous?.observationMemory?.connectivity)
    val userModeOrder = orderChannel(gated.userMode, sample.userMode, previous?.observationMemory?.userMode)
    val reasons = mutableListOf<ReasonCode>()
    reasons += gated.reasons
    listOf(
        batteryDecision.reason,
        precipitationDecision.reason,
        chargingOrder.reason,
        alertOrder.reason,
        activityOrder.reason,
        lightOrder.reason,
        connectivityOrder.reason,
        userModeOrder.reason,
    ).forEach { reason ->
        if (reason != null && reason !in reasons) {
            reasons += reason
        }
    }
    val desiredPower = desiredPower(chargingOrder.channel, batteryDecision.control, previous?.power, policy)
    val desiredWeather = desiredWeather(alertOrder.channel, precipitationDecision.control, previous?.weather, policy)
    val desiredActivity = when (val activity = activityOrder.channel) {
        Channel.Absent -> previous?.activity ?: ActivityAxis.UNKNOWN
        is Channel.Fresh -> activity.value
        is Channel.Unusable -> ActivityAxis.UNKNOWN
    }
    val light = when (val channel = lightOrder.channel) {
        Channel.Absent -> previous?.light ?: LightAxis.DAY
        is Channel.Fresh -> channel.value
        is Channel.Unusable -> previous?.light ?: LightAxis.DAY
    }
    val connectivity = when (val channel = connectivityOrder.channel) {
        Channel.Absent -> previous?.connectivity ?: ConnectivityAxis.ONLINE
        is Channel.Fresh -> channel.value
        is Channel.Unusable -> previous?.connectivity ?: ConnectivityAxis.ONLINE
    }
    val userMode = when (val channel = userModeOrder.channel) {
        Channel.Absent -> previous?.userMode ?: UserModeAxis.DEFAULT
        is Channel.Fresh -> channel.value
        is Channel.Unusable -> previous?.userMode ?: UserModeAxis.DEFAULT
    }
    val publishedBattery = batteryDecision.published
    val publishedPrecipitation = precipitationDecision.published
    val graphicsLow = if (batteryDecision.keepGraphics) {
        previous?.emission?.graphicsPowerLimited == true
    } else {
        freshBatteryIsLow(
            batteryDecision.control,
            previous?.emission?.graphicsPowerLimited == true,
            policy,
        )
    }
    val quality = if (
        gated.quality == DataQuality.FRESH &&
        (batteryDecision.reason in orderDowngrade || precipitationDecision.reason in orderDowngrade)
    ) {
        DataQuality.DEGRADED
    } else {
        gated.quality
    }
    val memory = ObservationMemory(
        battery = batteryDecision.cursor,
        precipitation = precipitationDecision.cursor,
        batteryExpiresAt = if (publishedBattery == null) null else batteryDecision.expiresAt,
        precipitationExpiresAt = if (publishedPrecipitation == null) null else precipitationDecision.expiresAt,
        charging = chargingOrder.cursor,
        alert = alertOrder.cursor,
        activity = activityOrder.cursor,
        light = lightOrder.cursor,
        connectivity = connectivityOrder.cursor,
        userMode = userModeOrder.cursor,
    )
    val publication = Publication(
        battery = publishedBattery,
        precipitation = publishedPrecipitation,
        dataQuality = quality,
        batteryUnusable = withdrawsNumber(gated.battery),
        precipitationUnusable = withdrawsNumber(gated.precipitation),
        graphicsLow = graphicsLow,
        batteryAccepted = batteryDecision.accepted,
        precipitationAccepted = precipitationDecision.accepted,
    )
    val settings = CallerSettings(sample.motionReduction, sample.ambientDisplay)
    if (previous == null) {
        val created = assemble(
            power = desiredPower,
            weather = desiredWeather,
            activity = desiredActivity,
            light = light,
            connectivity = connectivity,
            userMode = userMode,
            committedAt = sample.referenceTime,
            powerCommittedAt = sample.referenceTime,
            weatherCommittedAt = sample.referenceTime,
            activityCommittedAt = sample.referenceTime,
            processedAt = sample.referenceTime,
            revision = 1L,
            pending = null,
            settings = settings,
            graphicsLow = graphicsLow,
            observationMemory = memory,
        )
        return finish(
            skeleton = created,
            intent = intentFor(
                state = created,
                settings = settings,
                extraReasons = reasons,
                publishedBattery = publishedBattery,
                publishedPrecipitation = publishedPrecipitation,
                dataQuality = quality,
                graphicsLow = graphicsLow,
            ),
            previous = null,
            publication = publication,
            gateReasons = reasons,
            sample = sample,
            delivery = delivery,
        )
    }
    val powerChanged = desiredPower != previous.power
    val weatherChanged = desiredWeather != previous.weather
    val activityChanged = desiredActivity != previous.activity
    val urgent = desiredWeather == WeatherAxis.ALERT && previous.weather != WeatherAxis.ALERT
    val chargingException = desiredPower == PowerAxis.CHARGING && previous.power != PowerAxis.CHARGING ||
        previous.power == PowerAxis.CHARGING && desiredPower != PowerAxis.CHARGING
    val pending = previous.pending
    val powerSince = keptSince(powerChanged, pending?.power == desiredPower, pending?.powerSince, sample.referenceTime)
    val weatherSince = keptSince(weatherChanged, pending?.weather == desiredWeather, pending?.weatherSince, sample.referenceTime)
    val activitySince = keptSince(activityChanged, pending?.activity == desiredActivity, pending?.activitySince, sample.referenceTime)
    val powerDebounce = !powerChanged || debounceElapsed(powerSince, sample.referenceTime, policy)
    val weatherDebounce = !weatherChanged || debounceElapsed(weatherSince, sample.referenceTime, policy)
    val activityDebounce = !activityChanged || debounceElapsed(activitySince, sample.referenceTime, policy)
    val powerHold = !powerChanged || holdElapsed(previous.powerCommittedAt, sample.referenceTime, policy)
    val weatherHold = !weatherChanged || holdElapsed(previous.weatherCommittedAt, sample.referenceTime, policy)
    val activityHold = !activityChanged || holdElapsed(previous.activityCommittedAt, sample.referenceTime, policy)
    val commitPower = powerChanged && (chargingException || urgent || (powerDebounce && powerHold))
    val commitWeather = weatherChanged && (urgent || (weatherDebounce && weatherHold))
    val commitActivity = activityChanged && activityDebounce && activityHold
    if (commitWeather && urgent) {
        reasons += ReasonCode.URGENT
    }
    if (commitPower && chargingException) {
        reasons += ReasonCode.CHARGING_EXCEPTION
    }
    val waitingPower = powerChanged && !commitPower
    val waitingWeather = weatherChanged && !commitWeather
    val waitingActivity = activityChanged && !commitActivity
    if ((waitingPower && !powerDebounce) || (waitingWeather && !weatherDebounce) || (waitingActivity && !activityDebounce)) {
        reasons += ReasonCode.DEBOUNCE
    }
    if ((waitingPower && !powerHold) || (waitingWeather && !weatherHold) || (waitingActivity && !activityHold)) {
        reasons += ReasonCode.MINIMUM_HOLD
    }
    val power = if (commitPower) desiredPower else previous.power
    val weather = if (commitWeather) desiredWeather else previous.weather
    val activity = if (commitActivity) desiredActivity else previous.activity
    val committedAt = if (commitPower || commitWeather || commitActivity) {
        sample.referenceTime
    } else {
        previous.committedAt
    }
    val waitingSince = listOfNotNull(
        if (waitingPower) powerSince else null,
        if (waitingWeather) weatherSince else null,
        if (waitingActivity) activitySince else null,
    )
    val nextPending = if (waitingSince.isEmpty()) {
        null
    } else {
        PendingSensors(
            power = desiredPower,
            weather = desiredWeather,
            activity = desiredActivity,
            since = waitingSince.min(),
            powerSince = powerSince,
            weatherSince = weatherSince,
            activitySince = activitySince,
        )
    }
    val next = assemble(
        power = power,
        weather = weather,
        activity = activity,
        light = light,
        connectivity = connectivity,
        userMode = userMode,
        committedAt = committedAt,
        powerCommittedAt = if (commitPower) sample.referenceTime else previous.powerCommittedAt,
        weatherCommittedAt = if (commitWeather) sample.referenceTime else previous.weatherCommittedAt,
        activityCommittedAt = if (commitActivity) sample.referenceTime else previous.activityCommittedAt,
        processedAt = sample.referenceTime,
        revision = previous.revision,
        pending = nextPending,
        settings = settings,
        graphicsLow = graphicsLow,
        observationMemory = memory,
    )
    return finish(
        skeleton = next,
        intent = intentFor(
            state = next,
            settings = settings,
            extraReasons = reasons,
            publishedBattery = publishedBattery,
            publishedPrecipitation = publishedPrecipitation,
            dataQuality = quality,
            graphicsLow = graphicsLow,
        ),
        previous = previous,
        publication = publication,
        gateReasons = reasons,
        sample = sample,
        delivery = delivery,
    )
}

private data class Publication(
    val battery: Double?,
    val precipitation: Double?,
    val dataQuality: DataQuality,
    val batteryUnusable: Boolean,
    val precipitationUnusable: Boolean,
    val graphicsLow: Boolean,
    val batteryAccepted: Boolean,
    val precipitationAccepted: Boolean,
)

private fun finish(
    skeleton: MachineState,
    intent: IntelligenceIntent,
    previous: MachineState?,
    publication: Publication,
    gateReasons: List<ReasonCode>,
    sample: IntelligenceSample,
    delivery: DeliveryStamp,
): StepResult {
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
    if (previous != null && previous.revision == Long.MAX_VALUE && (axesChanged || emissionChanged)) {
        return deliverAtCeiling(skeleton, previous, publication, gateReasons, sample, delivery)
    }
    val revision = when {
        previous == null -> 1L
        axesChanged || emissionChanged -> previous.revision + 1
        else -> previous.revision
    }
    return StepResult.Advanced(
        state = skeleton.copy(revision = revision, emission = emission),
        intent = intent.copy(revision = revision),
        deliverySequence = delivery.sequence,
        deliveryEpoch = delivery.epoch,
        deliverySessionOpened = delivery.opened,
    )
}

private fun deliverAtCeiling(
    skeleton: MachineState,
    previous: MachineState,
    publication: Publication,
    gateReasons: List<ReasonCode>,
    sample: IntelligenceSample,
    delivery: DeliveryStamp,
): StepResult {
    val raised = previous.settings.raisedBy(
        skeleton.settings.motionReduction,
        skeleton.settings.ambientDisplay,
    )
    val graphics = previous.emission.graphicsPowerLimited || publication.graphicsLow
    val clockInverted = gateReasons.contains(ReasonCode.CLOCK_INVERSION)
    val memory = previous.observationMemory
    val now = skeleton.processedAt
    val batteryExpired = storedTtlExpired(memory.batteryExpiresAt, now, previous.emission.publishedBatteryPercent)
    val precipitationExpired = storedTtlExpired(
        memory.precipitationExpiresAt,
        now,
        previous.emission.publishedPrecipitation,
    )
    val adoptBattery = !clockInverted && sample.resync && publication.batteryAccepted
    val adoptPrecipitation = !clockInverted && sample.resync && publication.precipitationAccepted
    val withdrawBattery = !adoptBattery && previous.emission.publishedBatteryPercent != null &&
        (publication.batteryUnusable || (!clockInverted && batteryExpired))
    val withdrawPrecipitation = !adoptPrecipitation && previous.emission.publishedPrecipitation != null &&
        (publication.precipitationUnusable || (!clockInverted && precipitationExpired))
    val settingsRose = raised != previous.settings
    val graphicsRose = graphics && !previous.emission.graphicsPowerLimited
    val withdrew = withdrawBattery || withdrawPrecipitation
    val adopted = adoptBattery || adoptPrecipitation
    val batteryCursor = ceilingCursor(adoptBattery, skeleton.observationMemory.battery, memory.battery)
    val precipitationCursor = ceilingCursor(
        adoptPrecipitation,
        skeleton.observationMemory.precipitation,
        memory.precipitation,
    )
    val nextMemory = memory.copy(
        batteryExpiresAt = when {
            withdrawBattery -> null
            adoptBattery -> sample.batteryPercent?.expiresAt
            else -> memory.batteryExpiresAt
        },
        precipitationExpiresAt = when {
            withdrawPrecipitation -> null
            adoptPrecipitation -> sample.precipitationProbability?.expiresAt
            else -> memory.precipitationExpiresAt
        },
        battery = batteryCursor,
        precipitation = precipitationCursor,
    )
    if (!settingsRose && !graphicsRose && !withdrew && !adopted && nextMemory == memory) {
        return StepResult.LimitReached(
            ReasonCode.REVISION_EXHAUSTED,
            previous,
            delivery.sequence,
            delivery.epoch,
            delivery.opened,
        )
    }
    val sensorDropped = skeleton.power != previous.power ||
        skeleton.weather != previous.weather ||
        skeleton.activity != previous.activity ||
        skeleton.light != previous.light ||
        skeleton.connectivity != previous.connectivity ||
        skeleton.userMode != previous.userMode
    val freshNumberDropped = (!publication.batteryUnusable &&
        publication.battery != null &&
        publication.battery != previous.emission.publishedBatteryPercent) ||
        (!publication.precipitationUnusable &&
            publication.precipitation != null &&
            publication.precipitation != previous.emission.publishedPrecipitation)
    val focus = focusOf(
        power = previous.power,
        weather = previous.weather,
        activity = previous.activity,
        light = previous.light,
        connectivity = previous.connectivity,
        userMode = previous.userMode,
        graphicsLow = graphics,
    )
    val stateBase = previous.copy(
        focus = focus,
        settings = raised,
        processedAt = skeleton.processedAt,
        revision = Long.MAX_VALUE,
    )
    val extra = buildList {
        addAll(gateReasons.filter { it != ReasonCode.REVISION_EXHAUSTED })
        if (sensorDropped || freshNumberDropped || withdrew || adopted) {
            add(ReasonCode.REVISION_EXHAUSTED)
        }
    }
    val publishedBattery = ceilingNumber(
        adopt = adoptBattery,
        withdraw = withdrawBattery,
        incoming = publication.battery,
        previous = previous.emission.publishedBatteryPercent,
    )
    val publishedPrecipitation = ceilingNumber(
        adopt = adoptPrecipitation,
        withdraw = withdrawPrecipitation,
        incoming = publication.precipitation,
        previous = previous.emission.publishedPrecipitation,
    )
    val delivered = intentFor(
        state = stateBase,
        settings = raised,
        extraReasons = extra,
        publishedBattery = publishedBattery,
        publishedPrecipitation = publishedPrecipitation,
        dataQuality = if (withdrew || adopted) DataQuality.DEGRADED else previous.emission.dataQuality,
        graphicsLow = graphics,
    ).copy(revision = Long.MAX_VALUE)
    return StepResult.Advanced(
        state = stateBase.copy(emission = delivered.emission(), observationMemory = nextMemory),
        intent = delivered,
        deliverySequence = delivery.sequence,
        deliveryEpoch = delivery.epoch,
        deliverySessionOpened = delivery.opened,
    )
}

private val orderDowngrade = setOf(
    ReasonCode.SUPERSEDED_OBSERVATION,
    ReasonCode.OBSERVATION_CONFLICT,
    ReasonCode.FORECAST_SEPARATE,
)

private data class NumberDecision(
    val control: Channel<Double>,
    val published: Double?,
    val cursor: StreamCursor?,
    val expiresAt: Instant?,
    val reason: ReasonCode?,
    val keepGraphics: Boolean,
    val accepted: Boolean = false,
)

private data class DeliveryStamp(
    val sequence: Long,
    val epoch: Long,
    val opened: Boolean,
)

/** 순서는 감싸지 않는다. 음수는 순서가 아니다. 세션은 호출자가 열 때만 증가한다. */
private fun nextDelivery(lastSequence: Long, lastEpoch: Long, openSession: Boolean): DeliveryStamp {
    val epoch = if (lastEpoch < 0L) 0L else lastEpoch
    if (openSession && epoch != Long.MAX_VALUE) {
        return DeliveryStamp(sequence = 1L, epoch = epoch + 1L, opened = true)
    }
    if (lastSequence < 0L) {
        return DeliveryStamp(sequence = 1L, epoch = epoch, opened = false)
    }
    if (lastSequence == Long.MAX_VALUE) {
        return DeliveryStamp(sequence = Long.MAX_VALUE, epoch = epoch, opened = false)
    }
    return DeliveryStamp(sequence = lastSequence + 1L, epoch = epoch, opened = false)
}

private fun ceilingCursor(adopt: Boolean, incoming: StreamCursor?, previous: StreamCursor?): StreamCursor? {
    if (adopt || incoming?.revoked == true) {
        return incoming
    }
    return previous
}

private fun storedTtlExpired(expiresAt: Instant?, now: Instant, published: Double?): Boolean {
    return published != null && expiresAt != null && !now.isBefore(expiresAt)
}

private fun ceilingNumber(adopt: Boolean, withdraw: Boolean, incoming: Double?, previous: Double?): Double? {
    return when {
        adopt -> incoming
        withdraw -> null
        else -> previous
    }
}

private fun retainedAfterRejectedPolicy(previous: MachineState?, sample: IntelligenceSample): MachineState {
    val raised = if (previous == null) {
        CallerSettings(sample.motionReduction, sample.ambientDisplay)
    } else {
        previous.settings.raisedBy(sample.motionReduction, sample.ambientDisplay)
    }
    if (previous != null) {
        val inverted = sample.referenceTime < previous.processedAt
        val battery = retainedPublished(
            inverted = inverted,
            now = sample.referenceTime,
            published = previous.emission.publishedBatteryPercent,
            expiresAt = previous.observationMemory.batteryExpiresAt,
            observation = sample.batteryPercent,
        )
        val precipitation = retainedPublished(
            inverted = inverted,
            now = sample.referenceTime,
            published = previous.emission.publishedPrecipitation,
            expiresAt = previous.observationMemory.precipitationExpiresAt,
            observation = sample.precipitationProbability,
        )
        val memory = previous.observationMemory.copy(
            batteryExpiresAt = if (battery == null) null else previous.observationMemory.batteryExpiresAt,
            precipitationExpiresAt = if (precipitation == null) null else previous.observationMemory.precipitationExpiresAt,
            battery = revokedCursor(sample.batteryPercent, previous.observationMemory.battery, inverted),
            precipitation = revokedCursor(sample.precipitationProbability, previous.observationMemory.precipitation, inverted),
        )
        return previous.copy(
            settings = raised,
            emission = previous.emission.copy(
                publishedBatteryPercent = battery,
                publishedPrecipitation = precipitation,
            ),
            observationMemory = memory,
        )
    }
    return assemble(
        power = PowerAxis.NORMAL,
        weather = WeatherAxis.NORMAL,
        activity = ActivityAxis.UNKNOWN,
        light = LightAxis.DAY,
        connectivity = ConnectivityAxis.ONLINE,
        userMode = UserModeAxis.DEFAULT,
        committedAt = sample.referenceTime,
        powerCommittedAt = sample.referenceTime,
        weatherCommittedAt = sample.referenceTime,
        activityCommittedAt = sample.referenceTime,
        processedAt = sample.referenceTime,
        revision = 0L,
        pending = null,
        settings = raised,
        graphicsLow = false,
        observationMemory = ObservationMemory(),
    )
}

/** 잘못된 정책은 새 숫자를 받지 않는다. 시계 역전은 TTL과 철회를 적용하지 않는다. */
private fun retainedPublished(
    inverted: Boolean,
    now: Instant,
    published: Double?,
    expiresAt: Instant?,
    observation: Observation<*>?,
): Double? {
    if (published == null || inverted) {
        return published
    }
    if (expiresAt != null && !now.isBefore(expiresAt)) {
        return null
    }
    if (observation != null && isRevocation(observation)) {
        return null
    }
    return published
}

private fun revokedCursor(observation: Observation<*>?, previous: StreamCursor?, inverted: Boolean): StreamCursor? {
    if (inverted || observation == null || !isRevocation(observation)) {
        return previous
    }
    val source = observation.source.value
    return StreamCursor(
        source = source,
        observedAt = observation.observedAt,
        revision = if (source == previous?.source) previous.revision else null,
        revoked = true,
    )
}

private fun isRevocation(observation: Observation<*>): Boolean {
    return when (observation.classifiedValue()) {
        ClassifiedValue.Denied, ClassifiedValue.Failed, ClassifiedValue.Unavailable -> true
        else -> false
    }
}

private fun failSafeIntent(state: MachineState): IntelligenceIntent {
    val graphics = state.emission.graphicsPowerLimited
    return intentFor(
        state = state,
        settings = state.settings,
        extraReasons = listOf(ReasonCode.POLICY_REJECTED),
        publishedBattery = state.emission.publishedBatteryPercent,
        publishedPrecipitation = state.emission.publishedPrecipitation,
        dataQuality = DataQuality.DEGRADED,
        graphicsLow = graphics,
    ).copy(revision = state.revision)
}

private fun decideNumber(
    channel: Channel<Double>,
    observation: Observation<Double>?,
    revision: Long?,
    previousCursor: StreamCursor?,
    previousPublished: Double?,
    previousExpiresAt: Instant?,
    allowForecastPublication: Boolean,
): NumberDecision {
    if (observation == null || channel is Channel.Absent) {
        return NumberDecision(Channel.Absent, null, previousCursor, previousExpiresAt, null, keepGraphics = false)
    }
    if (channel is Channel.Unusable) {
        if (channel.reason == UnusableReason.FUTURE_OBSERVATION) {
            return NumberDecision(
                Channel.Absent,
                previousPublished,
                previousCursor,
                previousExpiresAt,
                null,
                keepGraphics = true,
            )
        }
        if (isPermissionLoss(channel.reason)) {
            val source = observation.source.value
            return NumberDecision(
                control = channel,
                published = null,
                cursor = StreamCursor(
                    source = source,
                    observedAt = observation.observedAt,
                    revision = revision ?: if (source == previousCursor?.source) previousCursor.revision else null,
                    revoked = true,
                ),
                expiresAt = null,
                reason = null,
                keepGraphics = false,
            )
        }
        return NumberDecision(channel, null, previousCursor, null, null, keepGraphics = false)
    }
    val value = (channel as Channel.Fresh).value
    if (observation.kind == ObservationKind.FORECAST) {
        val publish = allowForecastPublication && previousCursor == null
        return NumberDecision(
            control = Channel.Absent,
            published = if (publish) value else previousPublished,
            cursor = previousCursor,
            expiresAt = if (publish) observation.expiresAt else previousExpiresAt,
            reason = ReasonCode.FORECAST_SEPARATE,
            keepGraphics = !publish,
        )
    }
    val observedAt = observation.observedAt
    val source = observation.source.value
    val higherRevision = revision != null &&
        previousCursor?.revision != null &&
        source == previousCursor.source &&
        revision > previousCursor.revision
    if (revision != null && previousCursor?.revision != null && source == previousCursor.source) {
        if (revision < previousCursor.revision) {
            return keptNumber(previousPublished, previousCursor, previousExpiresAt, ReasonCode.SUPERSEDED_OBSERVATION)
        }
        if (revision == previousCursor.revision) {
            val same = value == previousPublished
            return keptNumber(
                previousPublished,
                previousCursor,
                previousExpiresAt,
                if (same) ReasonCode.DUPLICATE_OBSERVATION else ReasonCode.OBSERVATION_CONFLICT,
            )
        }
    }
    if (!higherRevision && previousCursor?.revoked == true) {
        val newerOrEqualTime = observedAt != null &&
            previousCursor.observedAt != null &&
            !observedAt.isBefore(previousCursor.observedAt)
        if (!newerOrEqualTime) {
            return keptNumber(previousPublished, previousCursor, null, ReasonCode.SUPERSEDED_OBSERVATION)
        }
    } else if (!higherRevision && previousCursor?.observedAt != null && (observedAt == null || observedAt < previousCursor.observedAt)) {
        return keptNumber(previousPublished, previousCursor, previousExpiresAt, ReasonCode.SUPERSEDED_OBSERVATION)
    }
    val keptRevision = revision ?: if (source == previousCursor?.source) previousCursor.revision else null
    return NumberDecision(
        control = channel,
        published = value,
        cursor = StreamCursor(source, observedAt, keptRevision),
        expiresAt = observation.expiresAt,
        reason = null,
        keepGraphics = false,
        accepted = true,
    )
}

/** 미래 관측은 거절만 한다. 상한에서 이미 공개한 숫자를 지우지 않는다. */
private fun withdrawsNumber(channel: Channel<*>): Boolean {
    val unusable = channel as? Channel.Unusable ?: return false
    return unusable.reason != UnusableReason.FUTURE_OBSERVATION
}

private fun isPermissionLoss(reason: UnusableReason): Boolean {
    return reason == UnusableReason.DENIED || reason == UnusableReason.ERROR || reason == UnusableReason.UNAVAILABLE
}

private data class AxisDecision<T>(
    val channel: Channel<T>,
    val cursor: StreamCursor?,
    val reason: ReasonCode?,
)

/** 예보와 더 오래된 관측은 축을 바꾸지 않는다. 철회는 그 시각 이전의 재수용을 막는다. */
private fun <T> orderChannel(
    channel: Channel<T>,
    observation: Observation<*>?,
    previousCursor: StreamCursor?,
): AxisDecision<T> {
    if (observation == null || channel is Channel.Absent) {
        return AxisDecision(Channel.Absent, previousCursor, null)
    }
    if (observation.kind == ObservationKind.FORECAST) {
        return AxisDecision(Channel.Absent, previousCursor, ReasonCode.FORECAST_SEPARATE)
    }
    if (channel is Channel.Unusable) {
        if (isPermissionLoss(channel.reason)) {
            return AxisDecision(
                channel = channel,
                cursor = StreamCursor(
                    source = observation.source.value,
                    observedAt = observation.observedAt,
                    revision = null,
                    revoked = true,
                ),
                reason = null,
            )
        }
        return AxisDecision(channel, previousCursor, null)
    }
    val observedAt = observation.observedAt
    if (previousCursor?.revoked == true) {
        val newerOrEqual = observedAt != null &&
            previousCursor.observedAt != null &&
            !observedAt.isBefore(previousCursor.observedAt)
        if (!newerOrEqual) {
            return AxisDecision(Channel.Absent, previousCursor, ReasonCode.SUPERSEDED_OBSERVATION)
        }
    } else if (previousCursor?.observedAt != null && (observedAt == null || observedAt < previousCursor.observedAt)) {
        return AxisDecision(Channel.Absent, previousCursor, ReasonCode.SUPERSEDED_OBSERVATION)
    }
    return AxisDecision(channel, StreamCursor(observation.source.value, observedAt, null), null)
}

private fun keptNumber(
    published: Double?,
    cursor: StreamCursor,
    expiresAt: Instant?,
    reason: ReasonCode,
): NumberDecision {
    return NumberDecision(Channel.Absent, published, cursor, expiresAt, reason, keepGraphics = true)
}

private fun keptSince(
    changed: Boolean,
    pendingMatches: Boolean,
    pendingSince: Instant?,
    now: Instant,
): Instant {
    if (changed && pendingMatches && pendingSince != null && !now.isBefore(pendingSince)) {
        return pendingSince
    }
    return now
}

private fun debounceElapsed(since: Instant, now: Instant, policy: PolicyCandidates): Boolean {
    val deadline = plusOrNull(since, policy.debounce)
    return deadline != null && !now.isBefore(deadline)
}

private fun holdElapsed(committedAt: Instant, now: Instant, policy: PolicyCandidates): Boolean {
    val deadline = plusOrNull(committedAt, policy.minimumHold)
    return deadline != null && !now.isBefore(deadline)
}

private fun freshBatteryIsLow(
    battery: Channel<Double>,
    previousGraphics: Boolean,
    policy: PolicyCandidates,
): Boolean {
    val fresh = battery as? Channel.Fresh ?: return false
    return lowPower(fresh.value, previousGraphics, policy)
}

private fun plusOrNull(start: Instant, amount: Duration): Instant? {
    return try {
        start.plus(amount)
    } catch (ex: DateTimeException) {
        null
    } catch (ex: ArithmeticException) {
        null
    }
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
    val reasons = channels.flatMap { channel ->
        val unusable = channel as? Channel.Unusable ?: return@flatMap emptyList()
        val codes = mutableListOf(unusable.reason.toReasonCode())
        when (unusable.freshness) {
            Freshness.UNDECLARED -> codes += ReasonCode.UNDECLARED_IGNORED
            Freshness.EXPIRED -> codes += ReasonCode.STALE_IGNORED
            Freshness.FRESH, null -> Unit
        }
        codes
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
    val chargingKnownOff = charging is Channel.Fresh
    if (previous == PowerAxis.CHARGING && !chargingKnownOff) {
        return PowerAxis.CHARGING
    }
    return when (battery) {
        is Channel.Fresh -> {
            val low = lowPower(battery.value, previous == PowerAxis.LOW, policy)
            if (low) PowerAxis.LOW else PowerAxis.NORMAL
        }
        else -> if (chargingKnownOff && previous == PowerAxis.CHARGING) {
            PowerAxis.NORMAL
        } else {
            previous ?: PowerAxis.NORMAL
        }
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
    powerCommittedAt: Instant,
    weatherCommittedAt: Instant,
    activityCommittedAt: Instant,
    processedAt: Instant,
    revision: Long,
    pending: PendingSensors?,
    settings: CallerSettings,
    graphicsLow: Boolean,
    observationMemory: ObservationMemory,
): MachineState {
    return MachineState(
        power = power,
        weather = weather,
        activity = activity,
        light = light,
        connectivity = connectivity,
        userMode = userMode,
        focus = focusOf(power, weather, activity, light, connectivity, userMode, graphicsLow),
        committedAt = committedAt,
        powerCommittedAt = powerCommittedAt,
        weatherCommittedAt = weatherCommittedAt,
        activityCommittedAt = activityCommittedAt,
        processedAt = processedAt,
        revision = revision,
        pending = pending,
        emission = Emission(
            quality = QualityCandidate.BALANCED,
            motionAllowed = true,
            particleEffectsAllowed = true,
            graphicsPowerLimited = false,
            weatherNumbersKept = true,
            timeKept = true,
            publishedBatteryPercent = null,
            publishedPrecipitation = null,
            dataQuality = DataQuality.SETTINGS_ONLY,
            reasonCodes = emptyList(),
        ),
        settings = settings,
        observationMemory = observationMemory,
    )
}

fun focusOf(
    power: PowerAxis,
    weather: WeatherAxis,
    activity: ActivityAxis,
    light: LightAxis,
    connectivity: ConnectivityAxis,
    userMode: UserModeAxis,
    graphicsLow: Boolean,
): FocusBand {
    if (weather == WeatherAxis.ALERT) {
        return FocusBand.CRITICAL
    }
    if (power == PowerAxis.LOW || graphicsLow) {
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
    settings: CallerSettings,
    extraReasons: List<ReasonCode>,
    publishedBattery: Double?,
    publishedPrecipitation: Double?,
    dataQuality: DataQuality,
    graphicsLow: Boolean,
): IntelligenceIntent {
    val quality = when {
        settings.ambientDisplay -> QualityCandidate.AOD
        state.power == PowerAxis.LOW -> QualityCandidate.ECO
        else -> QualityCandidate.BALANCED
    }
    val motionAllowed = !settings.motionReduction &&
        !settings.ambientDisplay &&
        state.power != PowerAxis.LOW
    val particleEffectsAllowed = motionAllowed && !graphicsLow && state.power != PowerAxis.LOW
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
        if ((graphicsLow || state.power == PowerAxis.LOW) && state.focus != FocusBand.POWER) {
            add(ReasonCode.POWER_LOW)
        }
        if (state.power == PowerAxis.CHARGING) {
            add(ReasonCode.POWER_CHARGING)
        }
        if (state.connectivity == ConnectivityAxis.OFFLINE) {
            add(ReasonCode.OFFLINE)
        }
        if (settings.motionReduction) {
            add(ReasonCode.MOTION_REDUCTION)
        }
        if (settings.ambientDisplay) {
            add(ReasonCode.AOD)
        }
    }.distinct()
    return IntelligenceIntent(
        focus = state.focus,
        quality = quality,
        motionAllowed = motionAllowed,
        particleEffectsAllowed = particleEffectsAllowed,
        graphicsPowerLimited = graphicsLow || state.power == PowerAxis.LOW,
        weatherNumbersKept = true,
        timeKept = true,
        publishedBatteryPercent = publishedBattery,
        publishedPrecipitation = publishedPrecipitation,
        dataQuality = dataQuality,
        reasonCodes = java.util.List.copyOf(reasons),
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
