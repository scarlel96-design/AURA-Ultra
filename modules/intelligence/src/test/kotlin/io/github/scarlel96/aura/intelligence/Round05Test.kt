package io.github.scarlel96.aura.intelligence

import io.github.scarlel96.aura.domain.Observation
import io.github.scarlel96.aura.domain.ObservationStatus
import java.time.Duration
import java.time.Instant
import kotlin.random.Random
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

class Round05Test {
    private fun run(
        previous: MachineState?,
        sample: IntelligenceSample,
        policy: PolicyCandidates = openPolicy(),
    ): StepResult.Advanced {
        return assertIs(step(previous, sample, policy))
    }

    @Test
    fun compositeConflictsKeepCanonicalPriority() {
        val policy = PolicyCandidates.documented()
        val chargingLow = run(
            null,
            sample(
                battery = reading(10.0, "percent"),
                charging = reading(true, "flag"),
                activity = reading("EXERCISE", "token"),
            ),
            policy,
        )
        assertEquals(PowerAxis.CHARGING, chargingLow.state.power)
        assertEquals(ActivityAxis.EXERCISE, chargingLow.state.activity)
        assertEquals(FocusBand.POWER, chargingLow.state.focus)
        assertEquals(QualityCandidate.BALANCED, chargingLow.intent.quality)
        assertTrue(chargingLow.intent.motionAllowed)
        assertFalse(chargingLow.intent.particleEffectsAllowed)
        assertTrue(chargingLow.intent.graphicsPowerLimited)
        assertEquals(10.0, chargingLow.intent.publishedBatteryPercent)
        assertTrue(chargingLow.intent.reasonCodes.contains(ReasonCode.POWER_LOW))
        assertTrue(chargingLow.intent.reasonCodes.contains(ReasonCode.POWER_CHARGING))
        val omittedBattery = run(chargingLow.state, sample(moment = at(1)), policy)
        assertEquals(PowerAxis.CHARGING, omittedBattery.state.power)
        assertEquals(FocusBand.EXERCISE, omittedBattery.state.focus)
        assertFalse(omittedBattery.intent.graphicsPowerLimited)
        assertTrue(omittedBattery.intent.particleEffectsAllowed)
        assertNull(omittedBattery.intent.publishedBatteryPercent)
        assertFalse(omittedBattery.intent.reasonCodes.contains(ReasonCode.POWER_LOW))
        val alert = run(
            null,
            sample(
                battery = reading(10.0, "percent"),
                precipitation = reading(90.0, "percent"),
                alert = reading(true, "flag"),
                activity = reading("EXERCISE", "token"),
            ),
            policy,
        )
        assertEquals(WeatherAxis.ALERT, alert.state.weather)
        assertEquals(PowerAxis.LOW, alert.state.power)
        assertEquals(ActivityAxis.EXERCISE, alert.state.activity)
        assertEquals(FocusBand.CRITICAL, alert.state.focus)
        assertEquals(QualityCandidate.ECO, alert.intent.quality)
        assertFalse(alert.intent.motionAllowed)
        assertFalse(alert.intent.particleEffectsAllowed)
        assertEquals(90.0, alert.intent.publishedPrecipitation)
        assertEquals(10.0, alert.intent.publishedBatteryPercent)
        assertTrue(alert.intent.reasonCodes.contains(ReasonCode.WEATHER_ALERT))
        assertTrue(alert.intent.reasonCodes.contains(ReasonCode.POWER_LOW))
        val expiredCharging = run(
            chargingLow.state,
            sample(
                moment = at(1),
                battery = reading(40.0, "percent", expiresAt = at(1)),
                charging = reading(true, "flag"),
            ),
            policy,
        )
        assertEquals(PowerAxis.CHARGING, expiredCharging.state.power)
        assertNull(expiredCharging.intent.publishedBatteryPercent)
        assertEquals(DataQuality.DEGRADED, expiredCharging.intent.dataQuality)
        assertTrue(expiredCharging.intent.reasonCodes.contains(ReasonCode.STALE_IGNORED))
        val protected = run(
            null,
            sample(
                battery = reading(80.0, "percent"),
                ambientDisplay = true,
                motionReduction = true,
            ),
            policy,
        )
        assertEquals(QualityCandidate.AOD, protected.intent.quality)
        assertFalse(protected.intent.motionAllowed)
        assertFalse(protected.intent.particleEffectsAllowed)
        assertTrue(protected.intent.reasonCodes.contains(ReasonCode.AOD))
        assertTrue(protected.intent.reasonCodes.contains(ReasonCode.MOTION_REDUCTION))
        val offlineDenied = run(
            null,
            sample(
                connectivity = reading("OFFLINE", "token"),
                battery = reading(null, "percent", status = ObservationStatus.DENIED),
                precipitation = reading(null, "percent", status = ObservationStatus.DENIED),
            ),
            policy,
        )
        assertEquals(ConnectivityAxis.OFFLINE, offlineDenied.state.connectivity)
        assertEquals(FocusBand.CONTEXT, offlineDenied.state.focus)
        assertNull(offlineDenied.intent.publishedBatteryPercent)
        assertNull(offlineDenied.intent.publishedPrecipitation)
        assertTrue(offlineDenied.intent.reasonCodes.contains(ReasonCode.DENIED_IGNORED))
        assertTrue(offlineDenied.intent.reasonCodes.contains(ReasonCode.OFFLINE))
        assertFailsWith<UnsupportedOperationException> {
            (protected.intent.reasonCodes as MutableList<ReasonCode>).add(ReasonCode.DECORATIVE)
        }
    }

    @Test
    fun continuousChangesDoNotResetOtherAxisClocks() {
        val policy = PolicyCandidates.documented().copy(debounce = Duration.ofSeconds(30))
        var state = run(
            null,
            sample(
                battery = reading(80.0, "percent"),
                precipitation = reading(10.0, "percent"),
                activity = reading("REST", "token"),
            ),
            policy,
        ).state
        state = run(
            state,
            sample(
                moment = at(10),
                battery = reading(10.0, "percent"),
                precipitation = reading(80.0, "percent"),
                activity = reading("EXERCISE", "token"),
            ),
            policy,
        ).state
        assertEquals(PowerAxis.NORMAL, state.power)
        assertEquals(WeatherAxis.NORMAL, state.weather)
        assertEquals(ActivityAxis.REST, state.activity)
        assertEquals(at(10), state.pending?.powerSince)
        assertEquals(at(10), state.pending?.weatherSince)
        val shifted = run(
            state,
            sample(
                moment = at(20),
                battery = reading(10.0, "percent"),
                precipitation = reading(80.0, "percent"),
                activity = reading("ACTIVE", "token"),
            ),
            policy,
        )
        assertEquals(PowerAxis.NORMAL, shifted.state.power)
        assertEquals(WeatherAxis.NORMAL, shifted.state.weather)
        assertEquals(ActivityAxis.REST, shifted.state.activity)
        assertEquals(at(10), shifted.state.pending?.powerSince)
        assertEquals(at(10), shifted.state.pending?.weatherSince)
        assertEquals(at(20), shifted.state.pending?.activitySince)
        assertFalse(shifted.intent.particleEffectsAllowed)
        val charging = run(
            shifted.state,
            sample(
                moment = at(25),
                battery = reading(10.0, "percent"),
                precipitation = reading(80.0, "percent"),
                activity = reading("ACTIVE", "token"),
                charging = reading(true, "flag"),
            ),
            policy,
        )
        assertEquals(PowerAxis.CHARGING, charging.state.power)
        assertEquals(WeatherAxis.NORMAL, charging.state.weather)
        assertEquals(at(10), charging.state.pending?.weatherSince)
        assertEquals(origin, charging.state.weatherCommittedAt)
        val due = run(
            charging.state,
            sample(
                moment = at(60),
                battery = reading(10.0, "percent"),
                precipitation = reading(80.0, "percent"),
                activity = reading("ACTIVE", "token"),
                charging = reading(true, "flag"),
            ),
            policy,
        )
        assertEquals(PowerAxis.CHARGING, due.state.power)
        assertEquals(WeatherAxis.PRECIP, due.state.weather)
        assertEquals(ActivityAxis.ACTIVE, due.state.activity)
        assertEquals(FocusBand.POWER, due.state.focus)
        assertFalse(due.intent.particleEffectsAllowed)
    }

    @Test
    fun sameInstantAndOlderSamplesKeepProtection() {
        val first = run(null, sample(battery = reading(50.0, "percent")))
        val repeated = run(first.state, sample(battery = reading(50.0, "percent")))
        assertEquals(1L, repeated.state.revision)
        assertEquals(origin, repeated.state.processedAt)
        assertFalse(repeated.intent.reasonCodes.contains(ReasonCode.CLOCK_INVERSION))
        val raised = run(
            repeated.state,
            sample(battery = reading(50.0, "percent"), motionReduction = true, ambientDisplay = true),
        )
        assertFalse(raised.intent.motionAllowed)
        assertFalse(raised.intent.particleEffectsAllowed)
        assertEquals(QualityCandidate.AOD, raised.intent.quality)
        val older = run(
            raised.state,
            sample(
                moment = origin.minusSeconds(1),
                battery = reading(1.0, "percent"),
                motionReduction = false,
                ambientDisplay = false,
            ),
        )
        assertEquals(raised.state.processedAt, older.state.processedAt)
        assertEquals(QualityCandidate.AOD, older.intent.quality)
        assertFalse(older.intent.motionAllowed)
        assertFalse(older.intent.particleEffectsAllowed)
        assertNull(older.intent.publishedBatteryPercent)
        assertTrue(older.intent.reasonCodes.contains(ReasonCode.CLOCK_INVERSION))
        assertEquals(PowerAxis.NORMAL, older.state.power)
    }

    @Test
    fun revisionOnlyConsumerMissesSameRevisionProtection() {
        val base = run(null, sample(battery = reading(80.0, "percent")))
        val maxed = base.state.copy(revision = Long.MAX_VALUE)
        val quiet = run(maxed, sample(moment = at(1), battery = reading(80.0, "percent")))
        val reduced = run(maxed, sample(moment = at(2), motionReduction = true))
        val blocked = assertIs<StepResult.LimitReached>(
            step(reduced.state, sample(moment = at(3), motionReduction = false), openPolicy()),
        )
        val rejected = step(
            null,
            sample(),
            PolicyCandidates.documented().copy(powerEnterPercent = 40.0, powerExitPercent = 10.0),
        )
        assertEquals(Long.MAX_VALUE, quiet.state.revision)
        assertTrue(quiet.intent.motionAllowed)
        assertNotNull(reduced.deliveredIntent())
        assertEquals(Long.MAX_VALUE, reduced.intent.revision)
        assertFalse(reduced.intent.motionAllowed)
        assertSame(reduced.state, blocked.state)
        assertNull(blocked.deliveredIntent())
        assertIs<StepResult.PolicyRejected>(rejected)
        assertNull(rejected.deliveredIntent())
        val revisionOnly = RevisionOnlyConsumer()
        revisionOnly.accept(quiet)
        revisionOnly.accept(reduced)
        revisionOnly.accept(blocked)
        revisionOnly.accept(rejected)
        assertTrue(revisionOnly.intent?.motionAllowed == true)
        val contract = ContractConsumer()
        contract.accept(quiet)
        contract.accept(reduced)
        contract.accept(blocked)
        contract.accept(rejected)
        assertFalse(contract.intent?.motionAllowed == true)
        assertEquals(reduced.intent, contract.intent)
        val draft = contract.intent?.toPresentationDraft()
        assertEquals("BALANCED", draft?.quality)
        assertEquals(false, draft?.motionAllowed)
        assertTrue(draft?.reasonCodes.orEmpty().contains(ReasonCode.MOTION_REDUCTION.name))
        assertNull(draft?.paletteId)
    }

    @Test
    fun reorderedIntentCanOverwriteNewerProtection() {
        val base = run(null, sample(battery = reading(80.0, "percent")))
        val maxed = base.state.copy(revision = Long.MAX_VALUE)
        val quiet = run(maxed, sample(moment = at(1), battery = reading(80.0, "percent")))
        val reduced = run(maxed, sample(moment = at(2), motionReduction = true))
        val naive = NaiveConsumer()
        naive.accept(reduced)
        naive.accept(quiet)
        assertTrue(naive.intent?.motionAllowed == true)
        val ordered = ContractConsumer()
        ordered.accept(reduced)
        ordered.accept(quiet)
        assertFalse(ordered.intent?.motionAllowed == true)
        assertEquals(at(2), ordered.appliedAt)
    }

    @Test
    fun timeAndPolicyBoundariesStayInsideStep() {
        val base = run(null, sample(battery = reading(80.0, "percent")))
        val ancient = run(base.state, sample(moment = Instant.MIN, battery = reading(1.0, "percent", expiresAt = Instant.MAX)))
        assertEquals(base.state.processedAt, ancient.state.processedAt)
        assertNull(ancient.intent.publishedBatteryPercent)
        assertTrue(ancient.intent.reasonCodes.contains(ReasonCode.CLOCK_INVERSION))
        val nearMax = Instant.MAX.minusSeconds(1)
        val adjacent = run(
            null,
            sample(
                moment = nearMax,
                battery = reading(
                    10.0,
                    "percent",
                    expiresAt = Instant.MAX,
                    observedAt = nearMax.minusSeconds(1),
                    receivedAt = nearMax.minusSeconds(1),
                ),
            ),
        )
        assertEquals(nearMax, adjacent.state.processedAt)
        assertEquals(PowerAxis.LOW, adjacent.state.power)
        assertFalse(adjacent.intent.particleEffectsAllowed)
        val atLimit = run(
            adjacent.state,
            sample(
                moment = Instant.MAX,
                battery = reading(
                    10.0,
                    "percent",
                    expiresAt = Instant.MAX,
                    observedAt = nearMax,
                    receivedAt = nearMax,
                ),
            ),
        )
        assertEquals(Instant.MAX, atLimit.state.processedAt)
        assertNull(atLimit.intent.publishedBatteryPercent)
        assertTrue(atLimit.intent.reasonCodes.contains(ReasonCode.STALE_IGNORED))
        val huge = openPolicy(hold = Duration.ofSeconds(Long.MAX_VALUE))
        assertEquals(emptyList(), huge.issues())
        val held = run(null, sample(battery = reading(80.0, "percent")), huge)
        val still = run(held.state, sample(moment = at(1), battery = reading(10.0, "percent")), huge)
        assertEquals(PowerAxis.NORMAL, still.state.power)
        assertTrue(still.intent.reasonCodes.contains(ReasonCode.MINIMUM_HOLD))
        val nearCeiling = run(
            null,
            sample(
                moment = Instant.MAX.minusSeconds(10),
                battery = reading(
                    80.0,
                    "percent",
                    expiresAt = Instant.MAX,
                    observedAt = Instant.MAX.minusSeconds(20),
                    receivedAt = Instant.MAX.minusSeconds(20),
                ),
            ),
            huge,
        )
        val overflowHold = run(
            nearCeiling.state,
            sample(
                moment = Instant.MAX.minusSeconds(1),
                battery = reading(
                    10.0,
                    "percent",
                    expiresAt = Instant.MAX,
                    observedAt = Instant.MAX.minusSeconds(2),
                    receivedAt = Instant.MAX.minusSeconds(2),
                ),
            ),
            huge,
        )
        assertEquals(PowerAxis.NORMAL, overflowHold.state.power)
        assertTrue(overflowHold.intent.reasonCodes.contains(ReasonCode.MINIMUM_HOLD))
        val debounced = openPolicy(hold = Duration.ZERO, debounce = Duration.ofSeconds(5))
        val started = run(null, sample(battery = reading(80.0, "percent")), debounced)
        val waiting = run(started.state, sample(battery = reading(10.0, "percent")), debounced)
        val before = run(waiting.state, sample(moment = at(4), battery = reading(10.0, "percent")), debounced)
        val exact = run(before.state, sample(moment = at(5), battery = reading(10.0, "percent")), debounced)
        val after = run(exact.state, sample(moment = at(6), battery = reading(10.0, "percent")), debounced)
        assertEquals(PowerAxis.NORMAL, before.state.power)
        assertEquals(PowerAxis.LOW, exact.state.power)
        assertEquals(PowerAxis.LOW, after.state.power)
        val hold = PolicyCandidates.documented()
        val armed = run(null, sample(battery = reading(80.0, "percent")), hold)
        val justBefore = run(
            armed.state,
            sample(moment = at(60).minusNanos(1), battery = reading(10.0, "percent")),
            hold,
        )
        val onBoundary = run(justBefore.state, sample(moment = at(60), battery = reading(10.0, "percent")), hold)
        assertEquals(PowerAxis.NORMAL, justBefore.state.power)
        assertEquals(PowerAxis.LOW, onBoundary.state.power)
        val nan = run(null, sample(battery = reading(Double.NaN, "percent")))
        val infinite = run(null, sample(battery = reading(Double.POSITIVE_INFINITY, "percent")))
        assertNull(nan.intent.publishedBatteryPercent)
        assertNull(infinite.intent.publishedBatteryPercent)
        assertTrue(nan.intent.reasonCodes.contains(ReasonCode.REJECTED_IGNORED))
        assertTrue(infinite.intent.reasonCodes.contains(ReasonCode.REJECTED_IGNORED))
        val badPolicy = PolicyCandidates.documented().copy(powerEnterPercent = Double.NaN)
        assertTrue(badPolicy.issues().isNotEmpty())
        val rejected = step(null, sample(battery = reading(10.0, "percent")), badPolicy)
        assertIs<StepResult.PolicyRejected>(rejected)
        assertNull(rejected.deliveredIntent())
        val negative = openPolicy(hold = Duration.ofSeconds(-1))
        assertTrue(negative.issues().isNotEmpty())
        assertIs<StepResult.PolicyRejected>(step(null, sample(), negative))
        val wrongUnit = run(null, sample(battery = reading(10.0, "ratio")))
        assertNull(wrongUnit.intent.publishedBatteryPercent)
        assertTrue(wrongUnit.intent.reasonCodes.contains(ReasonCode.UNIT_UNCHECKED))
        val wrongToken = run(null, sample(activity = reading("JOG", "token")))
        assertEquals(ActivityAxis.UNKNOWN, wrongToken.state.activity)
        assertTrue(wrongToken.intent.reasonCodes.contains(ReasonCode.TOKEN_UNCHECKED))
        val expired = run(null, sample(moment = at(5), battery = reading(12.0, "percent", expiresAt = at(5))))
        assertNull(expired.intent.publishedBatteryPercent)
        assertTrue(expired.intent.reasonCodes.contains(ReasonCode.STALE_IGNORED))
    }

    @Test
    fun longRunKeepsInvariants() {
        val seed = 20261128
        val random = Random(seed)
        val policy = PolicyCandidates.documented().copy(
            debounce = Duration.ofSeconds(5),
            minimumHold = Duration.ofSeconds(15),
        )
        var state: MachineState? = null
        var clock = origin
        repeat(100_000) { index ->
            val generated = generatedSample(random, state, clock)
            clock = generated.clock
            val result = try {
                step(state, generated.sample, policy)
            } catch (ex: RuntimeException) {
                throw AssertionError("seed $seed step $index threw ${ex::class.simpleName}: ${ex.message}", ex)
            }
            checkStep(seed, index, state, generated, result)
            if (result is StepResult.Advanced) {
                state = result.state
            }
        }
        assertNotNull(state)
        assertTrue(state.revision >= 1L)
        assertTrue(state.timeKept())
    }

    private fun MachineState.timeKept(): Boolean = emission.timeKept

    private fun checkStep(
        seed: Int,
        index: Int,
        previous: MachineState?,
        generated: Generated,
        result: StepResult,
    ) {
        val where = "seed $seed step $index"
        when (result) {
            is StepResult.PolicyRejected -> throw AssertionError("$where rejected a usable policy")
            is StepResult.LimitReached -> throw AssertionError("$where reached the revision ceiling")
            is StepResult.Advanced -> {
                val intent = result.intent
                assertEquals(result.state.revision, intent.revision, where)
                assertTrue(intent.timeKept, where)
                assertTrue(intent.weatherNumbersKept, where)
                assertTrue(intent.revision >= 1L, where)
                if (previous != null) {
                    assertTrue(intent.revision >= previous.revision, where)
                    assertTrue(intent.revision <= Long.MAX_VALUE, where)
                }
                assertTrue(intent.reasonCodes.size <= 16, where)
                val battery = intent.publishedBatteryPercent
                val precipitation = intent.publishedPrecipitation
                assertTrue(battery == null || battery.isFinite(), where)
                assertTrue(precipitation == null || precipitation.isFinite(), where)
                if (!intent.motionAllowed) {
                    assertFalse(intent.particleEffectsAllowed, where)
                }
                if (intent.graphicsPowerLimited || result.state.power == PowerAxis.LOW) {
                    assertFalse(intent.particleEffectsAllowed, where)
                }
                if (result.state.settings.motionReduction) {
                    assertFalse(intent.motionAllowed, where)
                }
                if (result.state.settings.ambientDisplay) {
                    assertEquals(QualityCandidate.AOD, intent.quality, where)
                    assertFalse(intent.motionAllowed, where)
                    assertFalse(intent.particleEffectsAllowed, where)
                }
                if (generated.older) {
                    assertEquals(previous?.processedAt, result.state.processedAt, where)
                    assertEquals(previous?.power, result.state.power, where)
                    assertNull(battery, where)
                    assertTrue(intent.reasonCodes.contains(ReasonCode.CLOCK_INVERSION), where)
                } else {
                    assertTrue(!result.state.processedAt.isBefore(result.state.committedAt), where)
                    if (generated.freshLow) {
                        assertTrue(intent.graphicsPowerLimited, where)
                        assertFalse(intent.particleEffectsAllowed, where)
                    }
                    if (generated.unusableBattery) {
                        assertNull(battery, where)
                    }
                    if (generated.freshChargingTrue) {
                        assertEquals(PowerAxis.CHARGING, result.state.power, where)
                    }
                    if (generated.freshAlert) {
                        assertEquals(WeatherAxis.ALERT, result.state.weather, where)
                    }
                    if (battery == 0.0) {
                        assertTrue(generated.freshZeroBattery, where)
                    }
                }
                assertEquals(intent, result.deliveredIntent(), where)
            }
        }
    }

    private fun generatedSample(random: Random, previous: MachineState?, clock: Instant): Generated {
        val roll = random.nextInt(10)
        val older = roll == 1 && previous != null && previous.processedAt.isAfter(origin.plusSeconds(5))
        val same = roll == 0 && previous != null
        val nextClock = if (older || same) clock else clock.plusSeconds(1)
        val moment = when {
            older -> previous.processedAt.minusSeconds(1L + random.nextInt(4))
            same -> previous.processedAt
            else -> nextClock
        }
        val kind = random.nextInt(12)
        val freshLow = !older && (kind == 1 || kind == 2)
        val freshZero = !older && kind == 11
        val unusableBattery = !older && (kind == 5 || kind == 6 || kind == 7)
        val chargingTrue = !older && (kind == 2 || kind == 3)
        val alert = !older && kind == 4
        val battery = when (kind) {
            0 -> freshNumber(80.0, moment)
            1, 2 -> freshNumber(10.0, moment)
            5 -> reading(5.0, "percent", status = ObservationStatus.STALE, expiresAt = moment.plusSeconds(30), observedAt = moment.minusSeconds(1), receivedAt = moment.minusSeconds(1))
            6 -> reading<Double>(null, "percent", status = ObservationStatus.DENIED, expiresAt = moment.plusSeconds(30), observedAt = moment.minusSeconds(1), receivedAt = moment.minusSeconds(1))
            7 -> reading(Double.NaN, "percent", expiresAt = moment.plusSeconds(30), observedAt = moment.minusSeconds(1), receivedAt = moment.minusSeconds(1))
            11 -> freshNumber(0.0, moment)
            else -> null
        }
        val sample = sample(
            moment = moment,
            battery = battery,
            charging = if (kind == 2 || kind == 3 || kind == 8) {
                flag(kind != 8, moment)
            } else {
                null
            },
            precipitation = if (kind == 4 || kind == 9) freshNumber(if (kind == 4) 80.0 else 10.0, moment) else null,
            alert = if (kind == 4 || kind == 9) flag(kind == 4, moment) else null,
            activity = when (kind) {
                4, 10 -> token(if (kind == 10) "EXERCISE" else "REST", moment)
                else -> null
            },
            light = if (kind == 10) token("NIGHT", moment) else null,
            connectivity = if (kind == 6 || kind == 10) token(if (kind == 6) "OFFLINE" else "ONLINE", moment) else null,
            userMode = if (kind == 10) token("WORK", moment) else null,
            motionReduction = kind == 7 || (previous?.settings?.motionReduction == true && roll != 2),
            ambientDisplay = kind == 3 || kind == 7,
        )
        return Generated(
            sample = sample,
            clock = nextClock,
            older = older,
            freshLow = freshLow,
            freshChargingTrue = chargingTrue,
            freshAlert = alert,
            freshZeroBattery = freshZero,
            unusableBattery = unusableBattery,
        )
    }

    private fun freshNumber(value: Double, moment: Instant): Observation<Double> {
        return reading(
            value,
            "percent",
            expiresAt = moment.plusSeconds(60),
            observedAt = moment.minusSeconds(1),
            receivedAt = moment.minusSeconds(1),
        )
    }

    private fun flag(value: Boolean, moment: Instant): Observation<Boolean> {
        return reading(
            value,
            "flag",
            expiresAt = moment.plusSeconds(60),
            observedAt = moment.minusSeconds(1),
            receivedAt = moment.minusSeconds(1),
        )
    }

    private fun token(value: String, moment: Instant): Observation<String> {
        return reading(
            value,
            "token",
            expiresAt = moment.plusSeconds(60),
            observedAt = moment.minusSeconds(1),
            receivedAt = moment.minusSeconds(1),
        )
    }

    private data class Generated(
        val sample: IntelligenceSample,
        val clock: Instant,
        val older: Boolean,
        val freshLow: Boolean,
        val freshChargingTrue: Boolean,
        val freshAlert: Boolean,
        val freshZeroBattery: Boolean,
        val unusableBattery: Boolean,
    )
}

private class RevisionOnlyConsumer {
    var intent: IntelligenceIntent? = null
    private var revision = -1L

    fun accept(result: StepResult) {
        val next = (result as? StepResult.Advanced)?.intent ?: return
        if (next.revision > revision) {
            revision = next.revision
            intent = next
        }
    }
}

private class ContractConsumer {
    var intent: IntelligenceIntent? = null
    var appliedAt: Instant? = null

    fun accept(result: StepResult) {
        val next = result.deliveredIntent() ?: return
        val at = (result as StepResult.Advanced).state.processedAt
        val previousAt = appliedAt
        if (previousAt != null && at < previousAt) {
            return
        }
        appliedAt = at
        intent = next
    }
}

private class NaiveConsumer {
    var intent: IntelligenceIntent? = null

    fun accept(result: StepResult) {
        intent = result.deliveredIntent() ?: return
    }
}
