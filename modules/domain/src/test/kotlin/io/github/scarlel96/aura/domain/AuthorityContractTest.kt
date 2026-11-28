package io.github.scarlel96.aura.domain

import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNull
import kotlin.test.assertTrue

class AuthorityContractTest {
    private val origin = Instant.parse("2026-11-28T00:00:00Z")

    @Test
    fun unknownAndDeniedCannotAcquire() {
        assertIs<DomainParse.Rejected>(AuthorityScope.parse(" ", "principal", "health"))
        assertIs<DomainParse.Rejected>(AuthoritySession.parse(""))
        val coordinator = AuthorityCoordinator.open(session())
        val health = scope()
        val pulse = request()
        val unknown = coordinator.acquire(health, pulse)
        assertEquals(AuthorityOutcome.REJECTED, unknown.outcome)
        assertEquals(AuthorityIssue.NOT_GRANTED, unknown.issue)
        assertEquals(AuthorityState.UNKNOWN, unknown.view.state)
        val denied = complete(coordinator, health, TrustedCheckResult.DENIED)
        assertEquals(AuthorityState.DENIED, denied.view.state)
        val deniedAgain = complete(coordinator, health, TrustedCheckResult.DENIED)
        assertEquals(AuthorityOutcome.ACCEPTED, deniedAgain.outcome)
        assertEquals(AuthorityState.DENIED, deniedAgain.view.state)
        assertEquals(denied.view.generation, deniedAgain.view.generation)
        val blocked = coordinator.acquire(health, pulse)
        assertEquals(AuthorityOutcome.REJECTED, blocked.outcome)
        assertEquals(AuthorityIssue.NOT_GRANTED, blocked.issue)
        assertNull(blocked.value)
    }

    @Test
    fun currentIssuedCheckCanGrant() {
        val coordinator = AuthorityCoordinator.open(session())
        val health = scope()
        val pulse = request()
        val granted = complete(coordinator, health, TrustedCheckResult.GRANTED)
        assertEquals(AuthorityOutcome.ACCEPTED, granted.outcome)
        assertEquals(AuthorityState.GRANTED, granted.view.state)
        val generation = granted.view.generation
        val first = coordinator.acquire(health, pulse)
        assertEquals(AuthorityOutcome.ACCEPTED, first.outcome)
        val capability = checkNotNull(first.value)
        assertTrue(coordinator.permits(capability, pulse))
        val repeated = complete(coordinator, health, TrustedCheckResult.GRANTED)
        assertEquals(AuthorityOutcome.ACCEPTED, repeated.outcome)
        assertEquals(generation, repeated.view.generation)
        assertEquals(AuthorityState.GRANTED, repeated.view.state)
        assertTrue(coordinator.permits(capability, pulse))
        val second = coordinator.acquire(health, pulse)
        assertTrue(coordinator.permits(checkNotNull(second.value), pulse))
        assertTrue(capability.acquisitionId != checkNotNull(second.value).acquisitionId)
    }

    @Test
    fun unissuedForeignAndStaleTicketsCannotGrant() {
        val health = scope()
        val first = AuthorityCoordinator.open(session("shared-token"))
        val second = AuthorityCoordinator.open(session("shared-token"))
        val issuedFirst = checkNotNull(first.issueCheck(health).value)
        val issuedSecond = checkNotNull(second.issueCheck(health).value)
        assertEquals(issuedFirst.number, issuedSecond.number)
        val crossed = first.complete(issuedSecond, TrustedCheckResult.GRANTED)
        assertEquals(AuthorityOutcome.REJECTED, crossed.outcome)
        assertEquals(AuthorityIssue.FOREIGN_ISSUER, crossed.issue)
        assertEquals(AuthorityState.UNKNOWN, first.view(health).state)
        val forged = AuthorityCoordinator.CheckTicket(Any(), health, "shared-token", issuedFirst.generation, issuedFirst.number)
        val forgedDecision = first.complete(forged, TrustedCheckResult.GRANTED)
        assertEquals(AuthorityIssue.FOREIGN_ISSUER, forgedDecision.issue)
        assertEquals(AuthorityState.UNKNOWN, first.view(health).state)
        val superseded = checkNotNull(first.issueCheck(health).value)
        val current = checkNotNull(first.issueCheck(health).value)
        val stale = first.complete(superseded, TrustedCheckResult.GRANTED)
        assertEquals(AuthorityIssue.STALE_TICKET, stale.issue)
        assertEquals(AuthorityState.UNKNOWN, stale.view.state)
        val accepted = first.complete(current, TrustedCheckResult.GRANTED)
        assertEquals(AuthorityState.GRANTED, accepted.view.state)
        val older = first.complete(superseded, TrustedCheckResult.DENIED)
        assertEquals(AuthorityIssue.STALE_TICKET, older.issue)
        assertEquals(AuthorityState.GRANTED, first.view(health).state)
        assertEquals(accepted.view.generation, first.view(health).generation)
    }

    @Test
    fun invalidateWhileUnknownFencesPendingCheck() {
        val coordinator = AuthorityCoordinator.open(session())
        val health = scope()
        val pending = checkNotNull(coordinator.issueCheck(health).value)
        val first = coordinator.invalidate(health)
        assertEquals(AuthorityOutcome.ACCEPTED, first.outcome)
        assertEquals(AuthorityState.UNKNOWN, first.view.state)
        assertTrue(first.view.generation > pending.generation)
        val late = coordinator.complete(pending, TrustedCheckResult.GRANTED)
        assertEquals(AuthorityIssue.STALE_TICKET, late.issue)
        assertEquals(AuthorityState.UNKNOWN, coordinator.view(health).state)
        val second = coordinator.invalidate(health)
        assertEquals(AuthorityOutcome.ACCEPTED, second.outcome)
        assertEquals(AuthorityState.UNKNOWN, second.view.state)
        assertTrue(second.view.generation > first.view.generation)
        assertEquals(AuthorityIssue.NOT_GRANTED, coordinator.acquire(health, request()).issue)
    }

    @Test
    fun duplicateAndConflictingCompletionAreHandled() {
        val coordinator = AuthorityCoordinator.open(session())
        val health = scope()
        val ticket = checkNotNull(coordinator.issueCheck(health).value)
        val granted = coordinator.complete(ticket, TrustedCheckResult.GRANTED)
        val generation = granted.view.generation
        val duplicate = coordinator.complete(ticket, TrustedCheckResult.GRANTED)
        assertEquals(AuthorityOutcome.UNCHANGED, duplicate.outcome)
        assertEquals(generation, duplicate.view.generation)
        assertEquals(AuthorityState.GRANTED, duplicate.view.state)
        val conflict = coordinator.complete(ticket, TrustedCheckResult.DENIED)
        assertEquals(AuthorityOutcome.FENCED, conflict.outcome)
        assertEquals(AuthorityIssue.CONFLICT, conflict.issue)
        assertEquals(AuthorityState.UNKNOWN, conflict.view.state)
        assertTrue(conflict.view.generation > generation)
        val capability = coordinator.acquire(health, request())
        assertEquals(AuthorityIssue.NOT_GRANTED, capability.issue)
    }

    @Test
    fun trustedFailureAndUntrustedInputAreDistinct() {
        val coordinator = AuthorityCoordinator.open(session())
        val health = scope("health")
        val steps = scope("steps")
        complete(coordinator, steps, TrustedCheckResult.GRANTED)
        val stepsView = coordinator.view(steps)
        val failedTicket = checkNotNull(coordinator.issueCheck(health).value)
        val failed = coordinator.complete(failedTicket, TrustedCheckResult.FAILED)
        assertEquals(AuthorityOutcome.ACCEPTED, failed.outcome)
        assertEquals(AuthorityState.UNKNOWN, failed.view.state)
        val failedRepeat = coordinator.complete(failedTicket, TrustedCheckResult.FAILED)
        assertEquals(AuthorityOutcome.UNCHANGED, failedRepeat.outcome)
        assertEquals(failed.view.generation, failedRepeat.view.generation)
        assertEquals(stepsView.state, coordinator.view(steps).state)
        assertEquals(stepsView.generation, coordinator.view(steps).generation)
        val before = coordinator.view(health)
        val ignored = coordinator.rejectUntrusted(health)
        assertEquals(AuthorityIssue.UNTRUSTED_INPUT, ignored.issue)
        assertEquals(before.state, coordinator.view(health).state)
        assertEquals(before.generation, coordinator.view(health).generation)
        assertEquals(stepsView.generation, coordinator.view(steps).generation)
        val granted = complete(coordinator, health, TrustedCheckResult.GRANTED)
        val untrustedWhileGranted = coordinator.rejectUntrusted(health)
        assertEquals(AuthorityIssue.UNTRUSTED_INPUT, untrustedWhileGranted.issue)
        assertEquals(AuthorityState.GRANTED, coordinator.view(health).state)
        assertEquals(granted.view.generation, coordinator.view(health).generation)
    }

    @Test
    fun regrantRejectsPriorGeneration() {
        val coordinator = AuthorityCoordinator.open(session())
        val health = scope()
        val pulse = request()
        complete(coordinator, health, TrustedCheckResult.GRANTED)
        val old = checkNotNull(coordinator.acquire(health, pulse).value)
        assertTrue(coordinator.permits(old, pulse))
        val denied = complete(coordinator, health, TrustedCheckResult.DENIED)
        assertEquals(AuthorityState.DENIED, denied.view.state)
        assertFalse(coordinator.permits(old, pulse))
        val recovered = complete(coordinator, health, TrustedCheckResult.GRANTED)
        assertEquals(AuthorityState.GRANTED, recovered.view.state)
        assertTrue(recovered.view.generation > old.generation)
        assertFalse(coordinator.permits(old, pulse))
        val fresh = checkNotNull(coordinator.acquire(health, pulse).value)
        assertTrue(coordinator.permits(fresh, pulse))
        assertFalse(coordinator.permits(old, pulse))
    }

    @Test
    fun foreignScopeSessionAndRequestAreRejected() {
        val healthCoordinator = AuthorityCoordinator.open(session("health-session"))
        val stepsCoordinator = AuthorityCoordinator.open(session("steps-session"))
        val health = scope("health")
        val steps = scope("steps")
        val pulse = request("pulse")
        val gait = request("gait")
        complete(healthCoordinator, health, TrustedCheckResult.GRANTED)
        complete(stepsCoordinator, steps, TrustedCheckResult.GRANTED)
        val healthCapability = checkNotNull(healthCoordinator.acquire(health, pulse).value)
        val stepsCapability = checkNotNull(stepsCoordinator.acquire(steps, gait).value)
        assertTrue(healthCoordinator.permits(healthCapability, pulse))
        assertFalse(healthCoordinator.permits(healthCapability, gait))
        assertFalse(stepsCoordinator.permits(healthCapability, pulse))
        assertFalse(healthCoordinator.permits(stepsCapability, gait))
        assertEquals(AuthorityState.UNKNOWN, healthCoordinator.view(steps).state)
        assertEquals(AuthorityState.GRANTED, stepsCoordinator.view(steps).state)
        val isolated = healthCoordinator.invalidate(health)
        assertEquals(AuthorityState.UNKNOWN, isolated.view.state)
        assertEquals(AuthorityState.GRANTED, stepsCoordinator.view(steps).state)
        assertTrue(stepsCoordinator.permits(stepsCapability, gait))
        assertFalse(healthCoordinator.permits(healthCapability, pulse))
    }

    @Test
    fun restartRequiresFreshAuthority() {
        val token = session("restart-token")
        val previous = AuthorityCoordinator.open(token)
        val health = scope()
        val pulse = request()
        val ticket = checkNotNull(previous.issueCheck(health).value)
        previous.complete(ticket, TrustedCheckResult.GRANTED)
        val old = checkNotNull(previous.acquire(health, pulse).value)
        val restarted = AuthorityCoordinator.open(session("restart-token"))
        assertEquals(AuthorityState.UNKNOWN, restarted.view(health).state)
        assertEquals(0, restarted.view(health).generation)
        val replay = restarted.complete(ticket, TrustedCheckResult.GRANTED)
        assertEquals(AuthorityIssue.FOREIGN_ISSUER, replay.issue)
        assertEquals(AuthorityState.UNKNOWN, restarted.view(health).state)
        assertFalse(restarted.permits(old, pulse))
        assertTrue(previous.permits(old, pulse))
        val recovered = complete(restarted, health, TrustedCheckResult.GRANTED)
        assertEquals(AuthorityState.GRANTED, recovered.view.state)
        assertTrue(restarted.permits(checkNotNull(restarted.acquire(health, pulse).value), pulse))
        assertFalse(restarted.permits(old, pulse))
    }

    @Test
    fun ticketAndGenerationCeilingsFailClosed() {
        val health = scope()
        val pulse = request()
        val ticketProbe = AuthorityCoordinator.openNearCeiling(session("ticket-ceiling"), health, Long.MAX_VALUE, 0)
        val lastTicket = checkNotNull(ticketProbe.issueCheck(health).value)
        assertEquals(Long.MAX_VALUE, lastTicket.number)
        val grantedAtCeiling = ticketProbe.complete(lastTicket, TrustedCheckResult.GRANTED)
        assertEquals(AuthorityState.GRANTED, grantedAtCeiling.view.state)
        val ceilingCapability = checkNotNull(ticketProbe.acquire(health, pulse).value)
        assertTrue(ticketProbe.permits(ceilingCapability, pulse))
        val overflow = ticketProbe.issueCheck(health)
        assertEquals(AuthorityOutcome.REJECTED, overflow.outcome)
        assertEquals(AuthorityIssue.LOCKED, overflow.issue)
        assertEquals(AuthorityState.UNKNOWN, overflow.view.state)
        assertTrue(overflow.view.locked)
        assertTrue(overflow.view.generation >= 0L)
        assertFalse(overflow.view.generation == Long.MIN_VALUE)
        assertEquals(AuthorityIssue.NOT_GRANTED, ticketProbe.acquire(health, pulse).issue)
        assertFalse(ticketProbe.permits(ceilingCapability, pulse))

        val generationProbe = AuthorityCoordinator.openNearCeiling(session("generation-ceiling"), health, 1, Long.MAX_VALUE)
        val blocked = generationProbe.invalidate(health)
        assertEquals(AuthorityIssue.LOCKED, blocked.issue)
        assertEquals(Long.MAX_VALUE, blocked.view.generation)
        assertEquals(AuthorityState.UNKNOWN, blocked.view.state)
        assertTrue(blocked.view.locked)
        val repeated = generationProbe.invalidate(health)
        assertEquals(AuthorityIssue.LOCKED, repeated.issue)
        assertEquals(Long.MAX_VALUE, repeated.view.generation)

        val near = AuthorityCoordinator.openNearCeiling(session("near-ceiling"), health, 2, Long.MAX_VALUE - 1)
        val nearTicket = checkNotNull(near.issueCheck(health).value)
        val reached = near.complete(nearTicket, TrustedCheckResult.GRANTED)
        assertEquals(Long.MAX_VALUE, reached.view.generation)
        assertEquals(AuthorityState.GRANTED, reached.view.state)
        val capability = checkNotNull(near.acquire(health, pulse).value)
        assertTrue(near.permits(capability, pulse))
        val locked = near.invalidate(health)
        assertEquals(AuthorityIssue.LOCKED, locked.issue)
        assertEquals(Long.MAX_VALUE, locked.view.generation)
        assertEquals(AuthorityState.UNKNOWN, locked.view.state)
        assertFalse(near.permits(capability, pulse))

        val reopened = AuthorityCoordinator.open(session("reopened"))
        val recovered = complete(reopened, health, TrustedCheckResult.GRANTED)
        assertEquals(AuthorityState.GRANTED, recovered.view.state)
        assertFalse(reopened.view(health).locked)
        assertTrue(reopened.permits(checkNotNull(reopened.acquire(health, pulse).value), pulse))
    }

    @Test
    fun sameStateCheckDoesNotResurrectInvalidatedGrant() {
        val coordinator = AuthorityCoordinator.open(session())
        val health = scope()
        val pulse = request()
        val ticket = checkNotNull(coordinator.issueCheck(health).value)
        val granted = coordinator.complete(ticket, TrustedCheckResult.GRANTED)
        val capability = checkNotNull(coordinator.acquire(health, pulse).value)
        val invalidated = coordinator.invalidate(health)
        assertEquals(AuthorityState.UNKNOWN, invalidated.view.state)
        assertTrue(invalidated.view.generation > granted.view.generation)
        val replay = coordinator.complete(ticket, TrustedCheckResult.GRANTED)
        assertEquals(AuthorityIssue.STALE_TICKET, replay.issue)
        assertEquals(AuthorityState.UNKNOWN, coordinator.view(health).state)
        assertEquals(invalidated.view.generation, coordinator.view(health).generation)
        assertFalse(coordinator.permits(capability, pulse))
        assertEquals(AuthorityIssue.NOT_GRANTED, coordinator.acquire(health, pulse).issue)
    }

    @Test
    fun capabilityConstructionAndCopyCannotForgeAcceptance() {
        val coordinator = AuthorityCoordinator.open(session())
        val health = scope()
        val pulse = request()
        complete(coordinator, health, TrustedCheckResult.GRANTED)
        val real = checkNotNull(coordinator.acquire(health, pulse).value)
        val forged = AuthorityCoordinator.AcquisitionCapability(Any(), health, "session-1", real.generation, pulse, real.acquisitionId)
        assertFalse(coordinator.permits(forged, pulse))
        assertTrue(coordinator.permits(real, pulse))
        val before = coordinator.view(health)
        val unused = AuthorityDecision(AuthorityOutcome.ACCEPTED, null, before, forged)
        assertEquals(AuthorityOutcome.ACCEPTED, unused.outcome)
        assertEquals(before.state, coordinator.view(health).state)
        assertEquals(before.generation, coordinator.view(health).generation)
        assertTrue(coordinator.permits(real, pulse))
        assertFalse(coordinator.permits(forged, pulse))
        assertTrue(AuthorityCoordinator.CheckTicket::class.java.declaredMethods.none { it.name == "copy" })
        assertTrue(AuthorityCoordinator.AcquisitionCapability::class.java.declaredMethods.none { it.name == "copy" })
        assertTrue(AuthorityDecision::class.java.declaredMethods.none { it.name == "copy" })
    }

    @Test
    fun ordinaryDataStatusDoesNotGrantOrRevokeAuthority() {
        val coordinator = AuthorityCoordinator.open(session())
        val health = scope()
        val before = coordinator.view(health)
        for (status in ObservationStatus.entries) {
            val noted = coordinator.noteObservationStatus(health, status)
            assertEquals(AuthorityIssue.DATA_STATUS_IGNORED, noted.issue)
            assertEquals(before.state, coordinator.view(health).state)
            assertEquals(before.generation, coordinator.view(health).generation)
            assertFalse(coordinator.view(health).locked)
        }
        complete(coordinator, health, TrustedCheckResult.GRANTED)
        val granted = coordinator.view(health)
        for (status in listOf(ObservationStatus.DENIED, ObservationStatus.ERROR, ObservationStatus.UNAVAILABLE, ObservationStatus.VALID)) {
            coordinator.noteObservationStatus(health, status)
            assertEquals(granted.state, coordinator.view(health).state)
            assertEquals(granted.generation, coordinator.view(health).generation)
        }
        assertEquals(AuthorityIssue.NOT_GRANTED, coordinator.acquire(scope("other"), request()).issue)
    }

    @Test
    fun genericRevisionAndScalarContractRemainIndependent() {
        val coordinator = AuthorityCoordinator.open(session())
        val health = scope()
        val pulse = request()
        complete(coordinator, health, TrustedCheckResult.GRANTED)
        val capability = checkNotNull(coordinator.acquire(health, pulse).value)
        val granted = coordinator.view(health)
        val key = acceptedKey()
        val opened = applyRevision(
            null,
            key,
            1,
            observation(10.0, source = key.source, observedAt = at(10), receivedAt = at(10), expiresAt = at(400)),
        )
        val denied = applyRevision(
            opened.cursor,
            key,
            2,
            observation(
                null,
                source = key.source,
                status = ObservationStatus.DENIED,
                observedAt = at(20),
                receivedAt = at(20),
                expiresAt = at(400),
            ),
        )
        assertEquals(RevisionOutcome.ACCEPTED, denied.outcome)
        val late = applyRevision(
            denied.cursor,
            key,
            3,
            observation(33.0, source = key.source, observedAt = at(12), receivedAt = at(25), expiresAt = at(400)),
        )
        assertEquals(RevisionOutcome.ACCEPTED, late.outcome)
        assertFalse(late.receiveTimeInversion)
        assertEquals(33.0, late.cursor?.observation?.value)
        val zero = applyRevision(
            null,
            acceptedKey(subject = "other.subject"),
            1,
            observation(0.0, source = key.source, observedAt = at(1), receivedAt = at(1), expiresAt = at(400)),
        )
        assertEquals(RevisionOutcome.ACCEPTED, zero.outcome)
        assertEquals(0.0, zero.cursor?.observation?.value)
        val items = mutableListOf("kept")
        val mutable = applyRevision(
            null,
            acceptedKey(subject = "mutable.subject"),
            1,
            observation(items, unit = "token", source = key.source, observedAt = at(1), receivedAt = at(1), expiresAt = at(400)),
        )
        assertEquals(RevisionOutcome.INVALID_OBSERVATION, mutable.outcome)
        assertEquals(listOf(IssueCode.UNSUPPORTED_PAYLOAD), mutable.issues.codes())
        assertNull(mutable.cursor)
        assertEquals(granted.state, coordinator.view(health).state)
        assertEquals(granted.generation, coordinator.view(health).generation)
        assertTrue(coordinator.permits(capability, pulse))
        coordinator.noteObservationStatus(health, ObservationStatus.DENIED)
        assertEquals(AuthorityState.GRANTED, coordinator.view(health).state)
    }

    private fun at(seconds: Long): Instant = origin.plusSeconds(seconds)

    private fun scope(category: String = "health"): AuthorityScope {
        val parsed = AuthorityScope.parse("platform", "principal", category)
        assertIs<DomainParse.Accepted<AuthorityScope>>(parsed)
        return parsed.value
    }

    private fun session(token: String = "session-1"): AuthoritySession {
        val parsed = AuthoritySession.parse(token)
        assertIs<DomainParse.Accepted<AuthoritySession>>(parsed)
        return parsed.value
    }

    private fun request(stream: String = "pulse"): AuthorityRequest {
        val parsed = AuthorityRequest.parse(stream)
        assertIs<DomainParse.Accepted<AuthorityRequest>>(parsed)
        return parsed.value
    }

    private fun complete(
        coordinator: AuthorityCoordinator,
        scope: AuthorityScope,
        result: TrustedCheckResult,
    ): AuthorityDecision<AuthorityView> {
        val ticket = coordinator.issueCheck(scope).value
        return coordinator.complete(checkNotNull(ticket), result)
    }
}
