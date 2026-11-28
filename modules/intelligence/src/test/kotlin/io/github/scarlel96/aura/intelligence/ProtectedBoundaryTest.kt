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
        val started = boundary.begin(capability, health, pulse)
        assertEquals(ProtectionOutcome.ACCEPTED, started.outcome)
        assertNull(started.record)
        assertTrue(checkNotNull(started.receipt).javaClass.methods.none { it.name == "payload" })
        val accepted = boundary.accept(started.receipt, observation, 1, reference(), ResultProvenance.CURRENT)
        assertEquals(ProtectionOutcome.ACCEPTED, accepted.outcome)
        assertNull(accepted.record)
        assertEquals(started.receipt.order, accepted.receipt?.order)
        val published = boundary.read(health, pulse, reference())
        assertEquals(ProtectionOutcome.PUBLISHED, published.outcome)
        assertEquals(12.0, published.record?.payload()?.value)
        assertEquals(started.receipt.order, published.record?.order)
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
        val accepted = open(boundary, healthCapability, health, pulse, observed(1.0), 1, reference())
        val published = boundary.read(health, pulse, reference())
        assertEquals(
            ProtectionIssue.RETAG_REJECTED,
            boundary.commit(checkNotNull(published.record), steps, gait, reference()).issue,
        )
        assertEquals(
            ProtectionOutcome.REJECTED,
            boundary.begin(healthCapability, steps, gait).outcome,
        )
        assertEquals(
            ProtectionIssue.NOT_PERMITTED,
            boundary.begin(foreign, health, pulse).issue,
        )
        assertEquals(1.0, boundary.read(health, pulse, reference()).record?.payload()?.value)
        assertEquals(ProtectionIssue.ABSENT, boundary.read(steps, gait, reference()).issue)
        assertEquals(stepsCapability.scope, steps)
        assertEquals(ProtectionOutcome.ACCEPTED, accepted.outcome)
    }

    @Test
    fun forgedRecordAndMutablePayloadCannotReplaceEnvelope() {
        val coordinator = coordinator()
        val health = scope("health")
        val pulse = request("pulse")
        val boundary = boundary(coordinator, health to pulse)
        val capability = grant(coordinator, health, pulse)
        val observation = observed(4.0)
        val started = boundary.begin(capability, health, pulse)
        val accepted = boundary.accept(checkNotNull(started.receipt), observation, 1, reference(), ResultProvenance.CURRENT)
        assertNull(accepted.record)
        val forged = object : ProtectedRecord {
            override val scope = health
            override val request = pulse
            override val order = checkNotNull(started.receipt).order
            override val generation = capability.generation
            override val acquisitionId = capability.acquisitionId
            override val dataRevision = 1L
            override fun payload(): Observation<*> = observed(99.0)
        }
        assertEquals(ProtectionIssue.FOREIGN_RECORD, boundary.commit(forged, health, pulse, reference()).issue)
        assertEquals(ProtectionIssue.DUPLICATE_ACQUISITION, boundary.begin(capability, health, pulse).issue)
        assertEquals(
            ProtectionIssue.STALE_RECEIPT,
            boundary.accept(started.receipt, observed(99.0), 2, reference(), ResultProvenance.CURRENT).issue,
        )
        val published = boundary.read(health, pulse, reference())
        assertEquals(4.0, published.record?.payload()?.value)
        assertTrue(ProtectedRecord::class.java.isInterface)
        val record = checkNotNull(published.record)
        assertTrue(record.javaClass.declaredMethods.none { it.name == "copy" })
        assertTrue(java.lang.reflect.Modifier.isPrivate(record.javaClass.modifiers))
        assertTrue(checkNotNull(accepted.receipt).javaClass.methods.none { it.name == "payload" })
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
        val replacement = grant(coordinator, health, pulse)
        assertEquals(
            ProtectionIssue.INVALID_OBSERVATION,
            open(boundary, replacement, health, pulse, unstable, 2, reference()).issue,
        )
        mutable.add(2)
        assertEquals(4.0, boundary.read(health, pulse, reference()).record?.payload()?.value)
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
        val started = boundary.begin(capability, health, pulse)
        val queued = boundary.accept(checkNotNull(started.receipt), observed(5.0), 5, reference(), ResultProvenance.CURRENT)
        val generation = coordinator.view(health).generation
        boundary.invalidate(health)
        assertTrue(coordinator.view(health).generation > generation)
        assertEquals(AuthorityState.UNKNOWN, coordinator.view(health).state)
        assertEquals(ProtectionIssue.NOT_PERMITTED, boundary.begin(capability, health, pulse).issue)
        assertEquals(
            ProtectionIssue.STALE_RECEIPT,
            boundary.accept(started.receipt, observed(50.0), 50, reference(), ResultProvenance.CURRENT).issue,
        )
        assertEquals(ProtectionOutcome.REJECTED, boundary.commit(checkNotNull(queued.receipt), health, pulse, reference()).outcome)
        assertEquals(WithdrawalReason.AUTHORITY_INVALIDATED, boundary.read(health, pulse, reference()).withdrawal?.reason)
        assertNull(boundary.read(health, pulse, reference()).record)
    }

    @Test
    fun regrantRejectsOldResultAndAcceptsFreshAcquisition() {
        val coordinator = coordinator()
        val health = scope("health")
        val pulse = request("pulse")
        val boundary = boundary(coordinator, health to pulse)
        val oldCapability = grant(coordinator, health, pulse)
        val old = open(boundary, oldCapability, health, pulse, observed(7.0), 7, reference())
        boundary.invalidate(health)
        val freshCapability = grant(coordinator, health, pulse)
        assertNotEquals(oldCapability.generation, freshCapability.generation)
        assertEquals(ProtectionIssue.NOT_PERMITTED, boundary.begin(oldCapability, health, pulse).issue)
        val fresh = open(boundary, freshCapability, health, pulse, observed(1.0), 1, reference())
        assertEquals(ProtectionOutcome.ACCEPTED, fresh.outcome)
        assertNull(fresh.record)
        assertEquals(1.0, boundary.read(health, pulse, reference()).record?.payload()?.value)
        val stale = boundary.commit(checkNotNull(old.receipt), health, pulse, reference())
        assertEquals(ProtectionOutcome.REJECTED, stale.outcome)
        assertEquals(ProtectionIssue.STALE_RECEIPT, stale.issue)
        assertNull(stale.withdrawal)
        assertNull(stale.record)
        assertEquals(1.0, boundary.read(health, pulse, reference()).record?.payload()?.value)
    }

    @Test
    fun finalReadRechecksPermitAndDropsQueuedMessage() {
        val coordinator = coordinator()
        val health = scope("health")
        val steps = scope("steps")
        val pulse = request("pulse")
        val gait = request("gait")
        val boundary = boundary(coordinator, health to pulse, health to gait, steps to gait)
        val pulseCapability = grant(coordinator, health, pulse)
        val gaitCapability = grant(coordinator, health, gait)
        val stepsCapability = grant(coordinator, steps, gait)
        open(boundary, pulseCapability, health, pulse, observed(8.0), 1, reference())
        assertEquals(8.0, boundary.read(health, pulse, reference()).record?.payload()?.value)
        val queued = open(boundary, gaitCapability, health, gait, observed(3.0), 1, reference())
        assertEquals(ProtectionOutcome.ACCEPTED, queued.outcome)
        assertNull(queued.record)
        open(boundary, stepsCapability, steps, gait, observed(9.0), 1, reference())
        val generation = coordinator.view(health).generation
        coordinator.invalidate(health)
        val readPulse = boundary.read(health, pulse, reference())
        assertEquals(ProtectionOutcome.WITHDRAWN, readPulse.outcome)
        assertEquals(WithdrawalReason.NOT_PERMITTED, readPulse.withdrawal?.reason)
        assertNull(readPulse.record)
        val readGait = boundary.read(health, gait, reference())
        assertEquals(ProtectionOutcome.WITHDRAWN, readGait.outcome)
        assertNull(readGait.record)
        assertEquals(9.0, boundary.read(steps, gait, reference()).record?.payload()?.value)
        assertTrue(coordinator.view(health).generation > generation)
        val fresh = grant(coordinator, health, pulse)
        assertEquals(
            ProtectionOutcome.ACCEPTED,
            open(boundary, fresh, health, pulse, observed(1.0), 1, reference()).outcome,
        )
        assertEquals(ProtectionIssue.NOT_PERMITTED, boundary.begin(pulseCapability, health, pulse).issue)
        assertEquals(1.0, boundary.read(health, pulse, reference()).record?.payload()?.value)
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
        open(boundary, pulseCapability, health, pulse, observed(1.0), 1, reference())
        open(boundary, gaitCapability, health, gait, observed(2.0), 1, reference())
        boundary.read(health, pulse, reference())
        boundary.read(health, gait, reference())
        val generation = coordinator.view(health).generation
        val fault = boundary.noteStreamFault(health, pulse, ObservationStatus.ERROR)
        assertEquals(WithdrawalReason.STREAM_ERROR, fault.withdrawal?.reason)
        assertEquals(AuthorityState.GRANTED, coordinator.view(health).state)
        assertEquals(generation, coordinator.view(health).generation)
        assertEquals(ProtectionOutcome.WITHDRAWN, boundary.read(health, pulse, reference()).outcome)
        assertEquals(2.0, boundary.read(health, gait, reference()).record?.payload()?.value)
        assertEquals(ProtectionIssue.DUPLICATE_ACQUISITION, boundary.begin(pulseCapability, health, pulse).issue)
        val fresh = grant(coordinator, health, pulse)
        assertEquals(
            ProtectionOutcome.ACCEPTED,
            open(boundary, fresh, health, pulse, observed(4.0), 1, reference()).outcome,
        )
        assertEquals(4.0, boundary.read(health, pulse, reference()).record?.payload()?.value)
        assertEquals(2.0, boundary.read(health, gait, reference()).record?.payload()?.value)
    }

    @Test
    fun unavailableWithdrawsStreamWithoutChangingAuthority() {
        val coordinator = coordinator()
        val health = scope("health")
        val pulse = request("pulse")
        val boundary = boundary(coordinator, health to pulse)
        val capability = grant(coordinator, health, pulse)
        val queued = open(boundary, capability, health, pulse, observed(3.0), 1, reference())
        boundary.read(health, pulse, reference())
        val generation = coordinator.view(health).generation
        boundary.noteStreamFault(health, pulse, ObservationStatus.UNAVAILABLE)
        assertEquals(AuthorityState.GRANTED, coordinator.view(health).state)
        assertEquals(generation, coordinator.view(health).generation)
        val stale = boundary.commit(checkNotNull(queued.receipt), health, pulse, reference())
        assertEquals(ProtectionOutcome.REJECTED, stale.outcome)
        assertEquals(ProtectionIssue.STALE_RECEIPT, stale.issue)
        assertNull(stale.withdrawal)
        assertEquals(WithdrawalReason.STREAM_UNAVAILABLE, boundary.read(health, pulse, reference()).withdrawal?.reason)
        assertEquals(ProtectionIssue.INVALID_OBSERVATION, boundary.noteStreamFault(health, pulse, ObservationStatus.DENIED).issue)
    }

    @Test
    fun staleReplayAfterWithdrawalCannotResurrect() {
        val coordinator = coordinator()
        val health = scope("health")
        val pulse = request("pulse")
        val boundary = boundary(coordinator, health to pulse)
        val capability = grant(coordinator, health, pulse)
        val started = boundary.begin(capability, health, pulse)
        val old = boundary.accept(checkNotNull(started.receipt), observed(6.0), 4, reference(), ResultProvenance.CURRENT)
        boundary.noteStreamFault(health, pulse, ObservationStatus.ERROR)
        assertEquals(
            ProtectionIssue.STALE_RECEIPT,
            boundary.commit(checkNotNull(old.receipt), health, pulse, reference()).issue,
        )
        assertEquals(WithdrawalReason.STREAM_ERROR, boundary.read(health, pulse, reference()).withdrawal?.reason)
        assertEquals(
            ProtectionIssue.STALE_RECEIPT,
            boundary.accept(started.receipt, observed(6.5), 5, reference(), ResultProvenance.CURRENT).issue,
        )
        assertEquals(ProtectionIssue.DUPLICATE_ACQUISITION, boundary.begin(capability, health, pulse).issue)
        val historicalCapability = grant(coordinator, health, pulse)
        val historical = boundary.begin(historicalCapability, health, pulse)
        assertEquals(
            ProtectionIssue.PROVENANCE_REJECTED,
            boundary.accept(
                checkNotNull(historical.receipt),
                observed(6.5),
                5,
                reference(),
                ResultProvenance.HISTORICAL,
            ).issue,
        )
        val unknownCapability = grant(coordinator, health, pulse)
        val unknown = boundary.begin(unknownCapability, health, pulse)
        assertEquals(
            ProtectionIssue.PROVENANCE_REJECTED,
            boundary.accept(
                checkNotNull(unknown.receipt),
                observed(6.5),
                5,
                reference(),
                ResultProvenance.UNKNOWN,
            ).issue,
        )
        assertNull(boundary.read(health, pulse, reference()).record)
        val fresh = grant(coordinator, health, pulse)
        val recovered = open(boundary, fresh, health, pulse, observed(6.5), 5, reference())
        assertEquals(ProtectionOutcome.ACCEPTED, recovered.outcome)
        assertNull(recovered.record)
        assertEquals(6.5, boundary.read(health, pulse, reference()).record?.payload()?.value)
        assertEquals(
            ProtectionIssue.STALE_RECEIPT,
            boundary.commit(checkNotNull(old.receipt), health, pulse, reference()).issue,
        )
        assertEquals(6.5, boundary.read(health, pulse, reference()).record?.payload()?.value)
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
        open(boundary, healthCapability, health, pulse, observed(11.0), 1, reference())
        open(boundary, stepsCapability, steps, gait, observed(22.0), 1, reference())
        boundary.invalidate(health)
        assertEquals(ProtectionOutcome.WITHDRAWN, boundary.read(health, pulse, reference()).outcome)
        assertEquals(22.0, boundary.read(steps, gait, reference()).record?.payload()?.value)
        assertEquals(AuthorityState.GRANTED, coordinator.view(steps).state)
        assertEquals(AuthorityState.UNKNOWN, coordinator.view(health).state)
    }

    @Test
    fun missingInvalidForecastAndTtlStaySeparateFromAuthority() {
        val coordinator = coordinator()
        val health = scope("health")
        val pulse = request("pulse")
        val gait = request("gait")
        val boundary = boundary(coordinator, health to pulse, health to gait)
        val capability = grant(coordinator, health, pulse)
        val gaitCapability = grant(coordinator, health, gait)
        val generation = coordinator.view(health).generation
        val started = boundary.begin(capability, health, pulse)
        val receipt = checkNotNull(started.receipt)
        assertEquals(
            ProtectionIssue.INVALID_OBSERVATION,
            boundary.accept(receipt, observed(null), 1, reference(), ResultProvenance.CURRENT).issue,
        )
        assertEquals(
            ProtectionIssue.INVALID_OBSERVATION,
            boundary.accept(receipt, observed(1.0, unit = " 1"), 1, reference(), ResultProvenance.CURRENT).issue,
        )
        assertEquals(
            ProtectionIssue.FORECAST_SEPARATE,
            boundary.accept(
                receipt,
                observed(9.0, kind = ObservationKind.FORECAST),
                1,
                reference(),
                ResultProvenance.CURRENT,
            ).issue,
        )
        assertEquals(
            ProtectionIssue.TTL_SEPARATE,
            boundary.accept(receipt, observed(9.0), 1, later(), ResultProvenance.CURRENT).issue,
        )
        assertEquals(
            ProtectionIssue.KIND_SEPARATE,
            boundary.accept(
                receipt,
                observed(null, status = ObservationStatus.DENIED),
                1,
                reference(),
                ResultProvenance.CURRENT,
            ).issue,
        )
        assertEquals(generation, coordinator.view(health).generation)
        assertEquals(AuthorityState.GRANTED, coordinator.view(health).state)
        val queued = boundary.accept(receipt, observed(8.0), 1, reference(), ResultProvenance.CURRENT)
        assertEquals(ProtectionOutcome.ACCEPTED, queued.outcome)
        assertNull(queued.record)
        val expired = boundary.commit(receipt, health, pulse, expiry())
        assertEquals(ProtectionOutcome.WITHDRAWN, expired.outcome)
        assertEquals(WithdrawalReason.EXPIRED, expired.withdrawal?.reason)
        assertNull(expired.record)
        assertEquals(generation, coordinator.view(health).generation)
        val gaitObservation = observed(3.0, expiresAt = Instant.parse("2026-11-28T04:00:00Z"))
        assertEquals(
            ProtectionOutcome.ACCEPTED,
            open(boundary, gaitCapability, health, gait, gaitObservation, 1, reference()).outcome,
        )
        assertEquals(3.0, boundary.read(health, gait, expiry()).record?.payload()?.value)
        val freshCapability = grant(coordinator, health, pulse)
        open(boundary, freshCapability, health, pulse, observed(8.0), 1, reference())
        assertEquals(ProtectionOutcome.PUBLISHED, boundary.read(health, pulse, reference()).outcome)
        val publishedExpiry = boundary.read(health, pulse, expiry())
        assertEquals(ProtectionOutcome.WITHDRAWN, publishedExpiry.outcome)
        assertEquals(WithdrawalReason.EXPIRED, publishedExpiry.withdrawal?.reason)
        assertNull(publishedExpiry.record)
        assertEquals(3.0, boundary.read(health, gait, expiry()).record?.payload()?.value)
        val rollbackCapability = grant(coordinator, health, pulse)
        val rollback = open(boundary, rollbackCapability, health, pulse, observed(4.0), 1, mid())
        val rolled = boundary.commit(checkNotNull(rollback.receipt), health, pulse, reference())
        assertEquals(ProtectionOutcome.WITHDRAWN, rolled.outcome)
        assertEquals(WithdrawalReason.CLOCK_ROLLBACK, rolled.withdrawal?.reason)
        assertNull(rolled.record)
        assertEquals(generation, coordinator.view(health).generation)
        assertEquals(AuthorityState.GRANTED, coordinator.view(health).state)
        assertEquals(3.0, boundary.read(health, gait, reference()).record?.payload()?.value)
        val zeroCapability = grant(coordinator, health, pulse)
        val explicitZero = open(boundary, zeroCapability, health, pulse, observed(0.0), 1, reference())
        assertEquals(ProtectionOutcome.ACCEPTED, explicitZero.outcome)
        assertEquals(0.0, boundary.read(health, pulse, reference()).record?.payload()?.value)
        assertFalse(boundary.read(health, pulse, reference()).record?.payload()?.value == null)
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
        val started = boundary.begin(capability, health, pulse)
        assertEquals(Long.MAX_VALUE, started.receipt?.order)
        val accepted = boundary.accept(checkNotNull(started.receipt), observed(1.0), 1, reference(), ResultProvenance.CURRENT)
        assertEquals(ProtectionOutcome.ACCEPTED, accepted.outcome)
        assertEquals(ProtectionOutcome.PUBLISHED, boundary.read(health, pulse, reference()).outcome)
        assertEquals(ProtectionIssue.DUPLICATE_ACQUISITION, boundary.begin(capability, health, pulse).issue)
        val next = grant(coordinator, health, pulse)
        assertEquals(ProtectionIssue.ORDER_LOCKED, boundary.begin(next, health, pulse).issue)
        assertEquals(Long.MAX_VALUE, boundary.peekNextOrder(health, pulse))
        assertEquals(1.0, boundary.read(health, pulse, reference()).record?.payload()?.value)
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
        assertEquals(ProtectionIssue.UNKNOWN_MAPPING, boundary.begin(capability, steps, gait).issue)
        assertEquals(ProtectionIssue.UNKNOWN_MAPPING, boundary.read(steps, gait, reference()).issue)
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
        val historical = open(boundary, oldCapability, health, pulse, observed(70.0), 3, reference())
        boundary.invalidate(health)
        val fresh = grant(coordinator, health, pulse)
        val started = boundary.begin(fresh, health, pulse)
        assertEquals(
            ProtectionIssue.PROVENANCE_REJECTED,
            boundary.accept(
                checkNotNull(started.receipt),
                observed(70.0),
                3,
                reference(),
                ResultProvenance.HISTORICAL,
            ).issue,
        )
        val unknown = grant(coordinator, health, pulse)
        val unknownStart = boundary.begin(unknown, health, pulse)
        assertEquals(
            ProtectionIssue.PROVENANCE_REJECTED,
            boundary.accept(
                checkNotNull(unknownStart.receipt),
                observed(70.0),
                3,
                reference(),
                ResultProvenance.UNKNOWN,
            ).issue,
        )
        val current = grant(coordinator, health, pulse)
        open(boundary, current, health, pulse, observed(4.0), 1, reference())
        assertEquals(4.0, boundary.read(health, pulse, reference()).record?.payload()?.value)
        val replay = boundary.commit(checkNotNull(historical.receipt), health, pulse, reference())
        assertEquals(ProtectionOutcome.REJECTED, replay.outcome)
        assertNull(replay.record)
        assertNull(replay.withdrawal)
        assertEquals(4.0, boundary.read(health, pulse, reference()).record?.payload()?.value)
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
        open(boundary, stepsCapability, steps, gait, observed(44.0), 1, reference())
        boundary.read(steps, gait, reference())
        open(boundary, healthCapability, health, pulse, observed(1.0), 1, reference())
        boundary.invalidate(health)
        boundary.noteStreamFault(steps, gait, ObservationStatus.ERROR)
        assertEquals(33.0, outside.value)
        assertEquals(ObservationStatus.VALID, outside.status)
        assertEquals(ProtectionOutcome.WITHDRAWN, boundary.read(health, pulse, reference()).outcome)
        assertEquals(ProtectionOutcome.WITHDRAWN, boundary.read(steps, gait, reference()).outcome)
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
        open(boundary, capability, health, pulse, first, 1, reference())
        boundary.invalidate(health)
        assertEquals(ProtectionIssue.NOT_PERMITTED, boundary.begin(capability, health, pulse).issue)
        assertNull(boundary.read(health, pulse, reference()).record)
    }

    private fun open(
        boundary: ProtectedBoundary,
        capability: AuthorityCoordinator.AcquisitionCapability,
        scope: AuthorityScope,
        request: AuthorityRequest,
        observation: Observation<*>,
        revision: Long,
        time: Instant,
    ): ProtectionDecision {
        val started = boundary.begin(capability, scope, request)
        assertEquals(ProtectionOutcome.ACCEPTED, started.outcome, started.issue?.name)
        return boundary.accept(
            checkNotNull(started.receipt),
            observation,
            revision,
            time,
            ResultProvenance.CURRENT,
        )
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

    private fun mid(): Instant = Instant.parse("2026-11-28T01:00:00Z")

    private fun expiry(): Instant = Instant.parse("2026-11-28T02:00:00Z")

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
