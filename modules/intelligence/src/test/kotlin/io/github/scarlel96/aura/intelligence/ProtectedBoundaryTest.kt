package io.github.scarlel96.aura.intelligence

import io.github.scarlel96.aura.domain.AuthorityCoordinator
import io.github.scarlel96.aura.domain.AuthorityOutcome
import io.github.scarlel96.aura.domain.AuthorityRequest
import io.github.scarlel96.aura.domain.AuthorityScope
import io.github.scarlel96.aura.domain.AuthoritySession
import io.github.scarlel96.aura.domain.AuthorityState
import io.github.scarlel96.aura.domain.DomainParse
import io.github.scarlel96.aura.domain.Observation
import io.github.scarlel96.aura.domain.ObservationKind
import io.github.scarlel96.aura.domain.ObservationStatus
import io.github.scarlel96.aura.domain.RevisionOutcome
import io.github.scarlel96.aura.domain.SourceId
import io.github.scarlel96.aura.domain.TrustedCheckResult
import io.github.scarlel96.aura.domain.UnsupportedPayloadException
import io.github.scarlel96.aura.domain.applyRevision
import io.github.scarlel96.aura.domain.observationKey
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNotEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

class ProtectedBoundaryTest {
    @Test
    fun currentCapabilityPublishesOnlyItsScopeAndRequest() {
        val coordinator = coordinator()
        val health = scope("health")
        val pulse = request("pulse")
        val boundary = boundary(coordinator, health to pulse)
        val capability = grant(coordinator, health, pulse)
        val observation = observed(12.0)
        val accepted = boundary.accept(capability, health, pulse, observation, 1, reference())
        assertEquals(ProtectionOutcome.ACCEPTED, accepted.outcome)
        assertEquals(observation, accepted.record?.payload())
        val published = boundary.read(health, pulse)
        assertEquals(ProtectionOutcome.PUBLISHED, published.outcome)
        assertEquals(12.0, published.record?.payload()?.value)
        assertEquals(capability.acquisitionId, published.record?.acquisitionId)
        assertTrue(coordinator.permits(capability, health, pulse))
    }

    @Test
    fun foreignScopeAndRequestCannotPublish() {
        val coordinator = coordinator()
        val other = coordinator("other-session")
        val health = scope("health")
        val steps = scope("steps")
        val pulse = request("pulse")
        val gait = request("gait")
        val boundary = boundary(coordinator, health to pulse, steps to gait)
        val healthCapability = grant(coordinator, health, pulse)
        val stepsCapability = grant(coordinator, steps, gait)
        val foreign = grant(other, health, pulse)
        boundary.accept(healthCapability, health, pulse, observed(1.0), 1, reference())
        assertEquals(
            ProtectionIssue.RETAG_REJECTED,
            boundary.commit(checkNotNull(boundary.read(health, pulse).record), steps, gait).issue,
        )
        assertEquals(
            ProtectionOutcome.REJECTED,
            boundary.accept(healthCapability, steps, gait, observed(2.0), 1, reference()).outcome,
        )
        assertEquals(
            ProtectionIssue.NOT_PERMITTED,
            boundary.accept(foreign, health, pulse, observed(3.0), 2, reference()).issue,
        )
        assertEquals(1.0, boundary.read(health, pulse).record?.payload()?.value)
        assertEquals(ProtectionIssue.ABSENT, boundary.read(steps, gait).issue)
        assertEquals(stepsCapability.scope, steps)
    }

    @Test
    fun forgedRecordAndMutablePayloadCannotReplaceEnvelope() {
        val coordinator = coordinator()
        val health = scope("health")
        val pulse = request("pulse")
        val boundary = boundary(coordinator, health to pulse)
        val capability = grant(coordinator, health, pulse)
        val observation = observed(4.0)
        val accepted = boundary.accept(capability, health, pulse, observation, 1, reference())
        val record = checkNotNull(accepted.record)
        val forged = object : ProtectedRecord {
            override val scope = record.scope
            override val request = record.request
            override val order = record.order
            override val generation = record.generation
            override val acquisitionId = record.acquisitionId
            override val dataRevision = record.dataRevision
            override fun payload(): Observation<*> = observed(99.0)
        }
        assertEquals(ProtectionIssue.FOREIGN_RECORD, boundary.commit(forged, health, pulse).issue)
        assertEquals(4.0, record.payload().value)
        assertEquals(4.0, observation.copy(value = 99.0).let { record.payload().value })
        assertTrue(ProtectedRecord::class.java.isInterface)
        assertTrue(record.javaClass.declaredMethods.none { it.name == "copy" })
        assertTrue(java.lang.reflect.Modifier.isPrivate(record.javaClass.modifiers))
        val mutable = mutableListOf(1)
        val unstable = Observation(
            value = mutable,
            unit = "1",
            source = source(),
            observedAt = reference(),
            receivedAt = reference(),
            expiresAt = later(),
            status = ObservationStatus.VALID,
            kind = ObservationKind.OBSERVED,
        )
        assertEquals(
            ProtectionIssue.INVALID_OBSERVATION,
            boundary.accept(capability, health, pulse, unstable, 2, reference()).issue,
        )
        mutable.add(2)
        assertEquals(ProtectionOutcome.PUBLISHED, boundary.read(health, pulse).outcome)
        assertEquals(4.0, boundary.read(health, pulse).record?.payload()?.value)
        assertFailsWith<UnsupportedPayloadException> {
            io.github.scarlel96.aura.domain.ClassifiedValue.Reading(mutable, ObservationStatus.VALID)
        }
    }

    @Test
    fun revocationRejectsQueuedHigherRevision() {
        val coordinator = coordinator()
        val health = scope("health")
        val pulse = request("pulse")
        val boundary = boundary(coordinator, health to pulse)
        val capability = grant(coordinator, health, pulse)
        val queued = boundary.accept(capability, health, pulse, observed(5.0), 5, reference())
        val generation = coordinator.view(health).generation
        boundary.invalidate(health)
        assertTrue(coordinator.view(health).generation > generation)
        assertEquals(AuthorityState.UNKNOWN, coordinator.view(health).state)
        val delayed = boundary.accept(capability, health, pulse, observed(50.0), 50, reference())
        assertEquals(ProtectionIssue.NOT_PERMITTED, delayed.issue)
        assertEquals(ProtectionOutcome.WITHDRAWN, boundary.commit(checkNotNull(queued.record), health, pulse).outcome)
        assertEquals(WithdrawalReason.AUTHORITY_INVALIDATED, boundary.read(health, pulse).withdrawal?.reason)
        assertNull(boundary.read(health, pulse).record)
    }

    @Test
    fun regrantRejectsOldResultAndAcceptsFreshAcquisition() {
        val coordinator = coordinator()
        val health = scope("health")
        val pulse = request("pulse")
        val boundary = boundary(coordinator, health to pulse)
        val oldCapability = grant(coordinator, health, pulse)
        val old = boundary.accept(oldCapability, health, pulse, observed(7.0), 7, reference())
        boundary.invalidate(health)
        val freshCapability = grant(coordinator, health, pulse)
        assertNotEquals(oldCapability.generation, freshCapability.generation)
        val rejectedOld = boundary.accept(oldCapability, health, pulse, observed(80.0), 80, reference())
        assertEquals(ProtectionIssue.NOT_PERMITTED, rejectedOld.issue)
        val fresh = boundary.accept(freshCapability, health, pulse, observed(1.0), 1, reference())
        assertEquals(ProtectionOutcome.ACCEPTED, fresh.outcome)
        assertEquals(1.0, boundary.read(health, pulse).record?.payload()?.value)
        assertEquals(
            WithdrawalReason.ORDER_FENCE,
            boundary.commit(checkNotNull(old.record), health, pulse).withdrawal?.reason,
        )
        assertEquals(1.0, boundary.read(health, pulse).record?.payload()?.value)
    }

    @Test
    fun finalReadRechecksPermitAndDropsQueuedMessage() {
        val coordinator = coordinator()
        val health = scope("health")
        val pulse = request("pulse")
        val boundary = boundary(coordinator, health to pulse)
        val capability = grant(coordinator, health, pulse)
        val queued = boundary.accept(capability, health, pulse, observed(8.0), 2, reference())
        assertEquals(ProtectionOutcome.ACCEPTED, queued.outcome)
        coordinator.invalidate(health)
        val read = boundary.read(health, pulse)
        assertEquals(ProtectionOutcome.WITHDRAWN, read.outcome)
        assertEquals(WithdrawalReason.NOT_PERMITTED, read.withdrawal?.reason)
        assertNull(read.record)
    }

    @Test
    fun ordinaryErrorWithdrawsOnlyThatStream() {
        val coordinator = coordinator()
        val health = scope("health")
        val pulse = request("pulse")
        val gait = request("gait")
        val boundary = boundary(coordinator, health to pulse, health to gait)
        val pulseCapability = grant(coordinator, health, pulse)
        val gaitCapability = grant(coordinator, health, gait)
        boundary.accept(pulseCapability, health, pulse, observed(1.0), 1, reference())
        boundary.accept(gaitCapability, health, gait, observed(2.0), 1, reference())
        boundary.read(health, pulse)
        boundary.read(health, gait)
        val generation = coordinator.view(health).generation
        val fault = boundary.noteStreamFault(health, pulse, ObservationStatus.ERROR)
        assertEquals(WithdrawalReason.STREAM_ERROR, fault.withdrawal?.reason)
        assertEquals(AuthorityState.GRANTED, coordinator.view(health).state)
        assertEquals(generation, coordinator.view(health).generation)
        assertEquals(ProtectionOutcome.WITHDRAWN, boundary.read(health, pulse).outcome)
        assertEquals(2.0, boundary.read(health, gait).record?.payload()?.value)
    }

    @Test
    fun unavailableWithdrawsStreamWithoutChangingAuthority() {
        val coordinator = coordinator()
        val health = scope("health")
        val pulse = request("pulse")
        val boundary = boundary(coordinator, health to pulse)
        val capability = grant(coordinator, health, pulse)
        val queued = boundary.accept(capability, health, pulse, observed(3.0), 1, reference())
        boundary.read(health, pulse)
        val generation = coordinator.view(health).generation
        boundary.noteStreamFault(health, pulse, ObservationStatus.UNAVAILABLE)
        assertEquals(AuthorityState.GRANTED, coordinator.view(health).state)
        assertEquals(generation, coordinator.view(health).generation)
        assertEquals(
            WithdrawalReason.ORDER_FENCE,
            boundary.commit(checkNotNull(queued.record), health, pulse).withdrawal?.reason,
        )
        assertEquals(ProtectionIssue.INVALID_OBSERVATION, boundary.noteStreamFault(health, pulse, ObservationStatus.DENIED).issue)
    }

    @Test
    fun staleReplayAfterWithdrawalCannotResurrect() {
        val coordinator = coordinator()
        val health = scope("health")
        val pulse = request("pulse")
        val boundary = boundary(coordinator, health to pulse)
        val capability = grant(coordinator, health, pulse)
        val old = boundary.accept(capability, health, pulse, observed(6.0), 4, reference())
        boundary.noteStreamFault(health, pulse, ObservationStatus.ERROR)
        assertEquals(ProtectionOutcome.WITHDRAWN, boundary.commit(checkNotNull(old.record), health, pulse).outcome)
        val recovered = boundary.accept(capability, health, pulse, observed(6.5), 5, reference())
        assertEquals(ProtectionOutcome.ACCEPTED, recovered.outcome)
        assertEquals(6.5, boundary.read(health, pulse).record?.payload()?.value)
        assertEquals(ProtectionOutcome.WITHDRAWN, boundary.commit(checkNotNull(old.record), health, pulse).outcome)
        assertEquals(AuthorityState.GRANTED, coordinator.view(health).state)
    }

    @Test
    fun independentStreamsStayIsolated() {
        val coordinator = coordinator()
        val health = scope("health")
        val steps = scope("steps")
        val pulse = request("pulse")
        val gait = request("gait")
        val boundary = boundary(coordinator, health to pulse, steps to gait)
        val healthCapability = grant(coordinator, health, pulse)
        val stepsCapability = grant(coordinator, steps, gait)
        boundary.accept(healthCapability, health, pulse, observed(11.0), 1, reference())
        boundary.accept(stepsCapability, steps, gait, observed(22.0), 1, reference())
        boundary.invalidate(health)
        assertEquals(ProtectionOutcome.WITHDRAWN, boundary.read(health, pulse).outcome)
        assertEquals(22.0, boundary.read(steps, gait).record?.payload()?.value)
        assertEquals(AuthorityState.GRANTED, coordinator.view(steps).state)
        assertEquals(AuthorityState.UNKNOWN, coordinator.view(health).state)
    }

    @Test
    fun missingInvalidForecastAndTtlStaySeparateFromAuthority() {
        val coordinator = coordinator()
        val health = scope("health")
        val pulse = request("pulse")
        val boundary = boundary(coordinator, health to pulse)
        val capability = grant(coordinator, health, pulse)
        val generation = coordinator.view(health).generation
        assertEquals(
            ProtectionIssue.INVALID_OBSERVATION,
            boundary.accept(capability, health, pulse, observed(null), 1, reference()).issue,
        )
        assertEquals(
            ProtectionIssue.INVALID_OBSERVATION,
            boundary.accept(capability, health, pulse, observed(1.0, unit = " 1"), 1, reference()).issue,
        )
        assertEquals(
            ProtectionIssue.FORECAST_SEPARATE,
            boundary.accept(
                capability,
                health,
                pulse,
                observed(9.0, kind = ObservationKind.FORECAST),
                1,
                reference(),
            ).issue,
        )
        assertEquals(
            ProtectionIssue.TTL_SEPARATE,
            boundary.accept(capability, health, pulse, observed(9.0), 1, later()).issue,
        )
        assertEquals(
            ProtectionIssue.KIND_SEPARATE,
            boundary.accept(
                capability,
                health,
                pulse,
                observed(null, status = ObservationStatus.DENIED),
                1,
                reference(),
            ).issue,
        )
        assertEquals(generation, coordinator.view(health).generation)
        assertEquals(AuthorityState.GRANTED, coordinator.view(health).state)
        val explicitZero = boundary.accept(capability, health, pulse, observed(0.0), 1, reference())
        assertEquals(ProtectionOutcome.ACCEPTED, explicitZero.outcome)
        assertEquals(0.0, boundary.read(health, pulse).record?.payload()?.value)
        assertFalse(boundary.read(health, pulse).record?.payload()?.value == null)
    }

    @Test
    fun orderSaturationFailsClosedWithoutWrapping() {
        val coordinator = coordinator()
        val health = scope("health")
        val pulse = request("pulse")
        val boundary = boundary(coordinator, health to pulse)
        val capability = grant(coordinator, health, pulse)
        val before = coordinator.view(health)
        boundary.placeOrderAtCeiling(health, pulse)
        assertEquals(before.state, coordinator.view(health).state)
        assertEquals(before.generation, coordinator.view(health).generation)
        val accepted = boundary.accept(capability, health, pulse, observed(1.0), 1, reference())
        assertEquals(Long.MAX_VALUE, accepted.record?.order)
        assertEquals(ProtectionOutcome.PUBLISHED, boundary.read(health, pulse).outcome)
        val blocked = boundary.accept(capability, health, pulse, observed(2.0), 2, reference())
        assertEquals(ProtectionIssue.ORDER_LOCKED, blocked.issue)
        assertEquals(Long.MAX_VALUE, boundary.peekNextOrder(health, pulse))
        assertEquals(1.0, boundary.read(health, pulse).record?.payload()?.value)
    }

    @Test
    fun unknownMappingRejectsProtectedData() {
        val coordinator = coordinator()
        val health = scope("health")
        val steps = scope("steps")
        val pulse = request("pulse")
        val gait = request("gait")
        val boundary = boundary(coordinator, health to pulse)
        val capability = grant(coordinator, health, pulse)
        grant(coordinator, steps, gait)
        assertEquals(
            ProtectionIssue.UNKNOWN_MAPPING,
            boundary.accept(capability, steps, gait, observed(1.0), 1, reference()).issue,
        )
        assertEquals(ProtectionIssue.UNKNOWN_MAPPING, boundary.read(steps, gait).issue)
        assertEquals(ProtectionIssue.UNKNOWN_MAPPING, boundary.noteStreamFault(steps, gait, ObservationStatus.ERROR).issue)
        assertEquals(AuthorityState.GRANTED, coordinator.view(health).state)
        assertEquals(AuthorityState.GRANTED, coordinator.view(steps).state)
    }

    @Test
    fun historyStaysUnpublishedByDefault() {
        assertTrue(ProtectedBoundary::class.java.methods.none { it.name.contains("istorical") })
        val coordinator = coordinator()
        val health = scope("health")
        val pulse = request("pulse")
        val boundary = boundary(coordinator, health to pulse)
        val oldCapability = grant(coordinator, health, pulse)
        val historical = boundary.accept(oldCapability, health, pulse, observed(70.0), 3, reference())
        boundary.invalidate(health)
        val fresh = grant(coordinator, health, pulse)
        boundary.accept(fresh, health, pulse, observed(4.0), 1, reference())
        assertEquals(4.0, boundary.read(health, pulse).record?.payload()?.value)
        assertNull(boundary.commit(checkNotNull(historical.record), health, pulse).record)
    }

    @Test
    fun unprotectedObservationAndOtherScopeStayUntouched() {
        val coordinator = coordinator()
        val health = scope("health")
        val steps = scope("steps")
        val pulse = request("pulse")
        val gait = request("gait")
        val boundary = boundary(coordinator, health to pulse, steps to gait)
        val outside = observed(33.0)
        val healthCapability = grant(coordinator, health, pulse)
        val stepsCapability = grant(coordinator, steps, gait)
        boundary.accept(stepsCapability, steps, gait, observed(44.0), 1, reference())
        boundary.read(steps, gait)
        boundary.accept(healthCapability, health, pulse, observed(1.0), 1, reference())
        boundary.invalidate(health)
        boundary.noteStreamFault(steps, gait, ObservationStatus.ERROR)
        assertEquals(33.0, outside.value)
        assertEquals(ObservationStatus.VALID, outside.status)
        assertEquals(ProtectionOutcome.WITHDRAWN, boundary.read(health, pulse).outcome)
        assertEquals(ProtectionOutcome.WITHDRAWN, boundary.read(steps, gait).outcome)
    }

    @Test
    fun genericRevisionStillAcceptsHigherRevisionOutsideTheBoundary() {
        val source = source()
        val key = (observationKey(source, "pulse") as DomainParse.Accepted).value
        val first = observed(1.0)
        val higher = observed(2.0, receivedAt = Instant.parse("2026-11-28T00:00:00Z"))
        val cursor = checkNotNull(applyRevision(null, key, 1, first).cursor)
        val decision = applyRevision(cursor, key, 2, higher)
        assertEquals(RevisionOutcome.ACCEPTED, decision.outcome)
        assertEquals(2L, decision.cursor?.revision)
        val coordinator = coordinator()
        val health = scope("health")
        val pulse = request("pulse")
        val boundary = boundary(coordinator, health to pulse)
        val capability = grant(coordinator, health, pulse)
        boundary.accept(capability, health, pulse, first, 1, reference())
        boundary.invalidate(health)
        assertEquals(
            ProtectionIssue.NOT_PERMITTED,
            boundary.accept(capability, health, pulse, higher, 2, reference()).issue,
        )
        assertNull(boundary.read(health, pulse).record)
    }

    private fun boundary(
        coordinator: AuthorityCoordinator,
        vararg bindings: Pair<AuthorityScope, AuthorityRequest>,
    ): ProtectedBoundary {
        return ProtectedBoundary(coordinator, bindings.toList())
    }

    private fun coordinator(token: String = "rv02-session"): AuthorityCoordinator {
        val session = (AuthoritySession.parse(token) as DomainParse.Accepted).value
        return AuthorityCoordinator.open(session)
    }

    private fun grant(
        coordinator: AuthorityCoordinator,
        scope: AuthorityScope,
        request: AuthorityRequest,
    ): AuthorityCoordinator.AcquisitionCapability {
        val ticket = checkNotNull(coordinator.issueCheck(scope).value)
        assertEquals(AuthorityOutcome.ACCEPTED, coordinator.complete(ticket, TrustedCheckResult.GRANTED).outcome)
        return checkNotNull(coordinator.acquire(scope, request).value)
    }

    private fun scope(category: String): AuthorityScope {
        return (AuthorityScope.parse("synthetic-authority", "synthetic-principal", category) as DomainParse.Accepted).value
    }

    private fun request(stream: String): AuthorityRequest {
        return (AuthorityRequest.parse(stream) as DomainParse.Accepted).value
    }

    private fun source(): SourceId {
        return (SourceId.parse("synthetic-source") as DomainParse.Accepted).value
    }

    private fun reference(): Instant = Instant.parse("2026-11-28T00:10:00Z")

    private fun later(): Instant = Instant.parse("2026-11-28T03:00:00Z")

    private fun observed(
        value: Double?,
        status: ObservationStatus = ObservationStatus.VALID,
        kind: ObservationKind = ObservationKind.OBSERVED,
        unit: String = "1",
        receivedAt: Instant = Instant.parse("2026-11-28T00:00:01Z"),
        expiresAt: Instant? = Instant.parse("2026-11-28T02:00:00Z"),
    ): Observation<Double> {
        return Observation(
            value = value,
            unit = unit,
            source = source(),
            observedAt = Instant.parse("2026-11-28T00:00:00Z"),
            receivedAt = receivedAt,
            expiresAt = expiresAt,
            status = status,
            kind = kind,
        )
    }
}
