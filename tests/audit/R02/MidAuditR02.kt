package io.github.scarlel96.aura.audit

import io.github.scarlel96.aura.domain.*
import io.github.scarlel96.aura.intelligence.*
import java.time.Instant
import java.time.Duration
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertTrue
import kotlin.test.assertFalse
import kotlin.test.assertNull

class MidAuditR02 {
    private val origin = Instant.parse("2026-01-01T00:00:00Z")
    private val source = (SourceId.parse("audit") as DomainParse.Accepted).value
    private val policy = PolicyCandidates.documented().copy(minimumHold = Duration.ZERO, debounce = Duration.ZERO)
    private fun t(seconds: Long) = origin.plusSeconds(seconds)
    private fun <T> obs(value: T?, unit: String, status: ObservationStatus = ObservationStatus.VALID,
                       seen: Long = 0, received: Long = seen, expires: Long? = 100,
                       kind: ObservationKind = ObservationKind.SYSTEM): Observation<T> =
        Observation(value, unit, source, t(seen), t(received), expires?.let(::t), status, kind)
    private fun run(s: MachineState?, sample: IntelligenceSample, p: PolicyCandidates = policy) =
        assertIs<StepResult.Advanced>(step(s, sample, p))
    private fun result(id: String, actual: Any?) = println("AUDIT_R02 " + id + " " + actual)

    @Test fun controlZeroAndExpiry() {
        assertEquals(Channel.Fresh(0.0), gateDouble(obs(0.0, "percent"), t(99), "percent", 0.0, 100.0))
        assertEquals(Channel.Unusable(UnusableReason.STALE), gateDouble(obs(0.0, "percent"), t(100), "percent", 0.0, 100.0))
        assertEquals(Channel.Unusable(UnusableReason.STALE), gateDouble(obs(15.0, "percent", ObservationStatus.STALE), t(1), "percent", 0.0, 100.0))
        assertEquals(Channel.Unusable(UnusableReason.REJECTED), gateDouble(obs(Double.NaN, "percent"), t(1), "percent", 0.0, 100.0))
        result("CTRL01", "zero, exact expiry, explicit stale and NaN correct")
    }
    @Test fun controlPriorityAndRevision() {
        val a = run(null, IntelligenceSample(t(0), batteryPercent=obs(10.0,"percent"), weatherAlert=obs(true,"flag"), activity=obs("EXERCISE","token")))
        assertEquals(FocusBand.CRITICAL,a.intent.focus)
        assertFalse(a.intent.particleEffectsAllowed)
        val b = run(a.state, IntelligenceSample(t(1), ambientDisplay=true))
        val c = run(b.state, IntelligenceSample(t(0), ambientDisplay=false))
        assertEquals(QualityCandidate.AOD,c.intent.quality)
        assertFalse(c.intent.motionAllowed)
        assertTrue(c.state.revision >= b.state.revision)
        result("CTRL02","critical priority, particle suppression, old sample cannot clear AOD")
    }
    @Test fun controlDomainRevisionAndTimestamp() {
        val key = (observationKey(source,"battery") as DomainParse.Accepted).value
        val initial = obs(20.0,"percent")
        val a = applyRevision(null,key,2L,initial)
        val b = applyRevision(a.cursor,key,1L,obs(80.0,"percent"))
        val c = applyRevision(a.cursor,key,2L,initial.copy(receivedAt=t(1)))
        assertEquals(RevisionOutcome.SUPERSEDED_REJECTED,b.outcome)
        assertEquals(RevisionOutcome.DUPLICATE,c.outcome)
        assertEquals(a.cursor,b.cursor)
        assertEquals(a.cursor,c.cursor)
        val f = validateObservation(obs(70.0,"percent",seen=20), ObservationConstraints<Double>(
            futureTimestamp=FutureTimestampPolicy.REJECT_AFTER_REFERENCE, referenceTime=t(1)))
        assertFalse(f.accepted)
        result("CTRL03","domain revision and opt-in future timestamp gate correct")
    }
    @Test fun statusReasonPrecedence() {
        val outcomes = listOf(ObservationStatus.DENIED,ObservationStatus.ERROR,ObservationStatus.UNAVAILABLE).flatMap { status ->
            listOf<Long?>(null,0,100).map { expires ->
                val x=gateDouble(obs<Double>(null,"percent",status,expires=expires),t(1),"percent",0.0,100.0)
                assertIs<Channel.Unusable>(x)
                result("R02-01", "status=$status expires=$expires result=$x")
                x
            }
        }
        assertEquals(9,outcomes.size)
    }
    @Test fun futureReadingAndOlderObservation() {
        val future = gateDouble(obs(70.0,"percent",seen=20,received=20,expires=100),t(1),"percent",0.0,100.0)
        result("R02-02","future observation=$future")
        val a=run(null,IntelligenceSample(t(10),batteryPercent=obs(80.0,"percent",seen=10)))
        val b=run(a.state,IntelligenceSample(t(11),batteryPercent=obs(10.0,"percent",seen=1,received=2)))
        result("R02-03","new sample clock but old observation: ${a.intent.publishedBatteryPercent} -> ${b.intent.publishedBatteryPercent}, power=${b.state.power}")
    }
    @Test fun invalidPolicyAndUnits() {
        val a=run(null,IntelligenceSample(t(0)))
        val bad=policy.copy(debounce=Duration.ofSeconds(-1))
        val rejected=step(a.state,IntelligenceSample(t(1),ambientDisplay=true,motionReduction=true),bad)
        assertIs<StepResult.PolicyRejected>(rejected)
        assertNull(rejected.deliveredIntent())
        result("R02-04","invalid policy with AOD/reduction: $rejected; no delivered intent")
        for (unit in listOf(" percent ","per cent","percent\u0000")) {
            val p=policy.copy(percentUnit=unit)
            val s=step(null,IntelligenceSample(t(1),batteryPercent=obs(10.0,unit)),p)
            result("R02-05","unit=${unit.toCharArray().map { it.code }} issues=${p.issues()} result=${s::class.simpleName}")
        }
    }
    @Test fun ceilingAndOmittedExpiry() {
        val a=run(null,IntelligenceSample(t(0),batteryPercent=obs(80.0,"percent",expires=2),precipitationProbability=obs(90.0,"percent",expires=2)))
        val max=a.state.copy(revision=Long.MAX_VALUE)
        val b=step(max,IntelligenceSample(t(3),ambientDisplay=true),policy)
        assertIs<StepResult.Advanced>(b)
        result("R02-06","ceiling omitted expired values: battery=${b.intent.publishedBatteryPercent}, precip=${b.intent.publishedPrecipitation}, AOD=${b.intent.quality}")
        val c=step(max,IntelligenceSample(t(100),batteryPercent=obs(90.0,"percent",seen=100,expires=200)),policy)
        assertIs<StepResult.LimitReached>(c)
        result("R02-07","ceiling ignored time=100; stored=${c.state.processedAt}")
    }
    @Test fun gateBoundsAndSnapshotMutability() {
        val g=gateDouble(obs(999.0,"percent"),t(1),"percent",Double.NaN,Double.NaN)
        result("R02-08","standalone gate with NaN bounds: $g")
        val key=(observationKey(source,"generic") as DomainParse.Accepted).value
        val list=mutableListOf(1)
        val a=applyRevision(null,key,1L,obs(list,"token"))
        assertEquals(RevisionOutcome.ACCEPTED,a.outcome)
        list.add(2)
        result("R02-09","mutable payload after accepted revision: ${a.cursor?.observation?.value}")
    }
    @Test fun lowPowerHysteresisDuringChargingAndPending() {
        val a=run(null,IntelligenceSample(t(0),batteryPercent=obs(10.0,"percent"),charging=obs(true,"flag")))
        val b=run(a.state,IntelligenceSample(t(1),batteryPercent=obs(17.0,"percent"),charging=obs(true,"flag")))
        result("R02-10","charging battery 10 -> 17; graphics=${a.intent.graphicsPowerLimited}->${b.intent.graphicsPowerLimited}; particles=${a.intent.particleEffectsAllowed}->${b.intent.particleEffectsAllowed}")
        val c=run(null,IntelligenceSample(t(0),batteryPercent=obs(80.0,"percent")))
        val p=policy.copy(minimumHold=Duration.ofSeconds(60))
        val d=run(c.state,IntelligenceSample(t(1),batteryPercent=obs(10.0,"percent")),p)
        val e=run(d.state,IntelligenceSample(t(2),batteryPercent=obs(17.0,"percent")),p)
        result("R02-11","pending low 10 -> 17; graphics=${d.intent.graphicsPowerLimited}->${e.intent.graphicsPowerLimited}; pending=${e.state.pending?.power}")
    }
}
