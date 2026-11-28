package io.github.scarlel96.aura.intelligence

import io.github.scarlel96.aura.domain.AuthorityCoordinator
import io.github.scarlel96.aura.domain.AuthorityDecision
import io.github.scarlel96.aura.domain.AuthorityScope
import io.github.scarlel96.aura.domain.AuthorityRequest
import io.github.scarlel96.aura.domain.AuthorityView
import io.github.scarlel96.aura.domain.ClassifiedValue
import io.github.scarlel96.aura.domain.DomainParse
import io.github.scarlel96.aura.domain.Freshness
import io.github.scarlel96.aura.domain.Observation
import io.github.scarlel96.aura.domain.ObservationKind
import io.github.scarlel96.aura.domain.ObservationStatus
import io.github.scarlel96.aura.domain.RevisionCursor
import io.github.scarlel96.aura.domain.RevisionOutcome
import io.github.scarlel96.aura.domain.StatusDerivation
import io.github.scarlel96.aura.domain.applyRevision
import io.github.scarlel96.aura.domain.classifiedValue
import io.github.scarlel96.aura.domain.deriveStatus
import io.github.scarlel96.aura.domain.observationKey
import io.github.scarlel96.aura.domain.validateObservation
import java.time.Instant

/**
 * 획득 시작 때 순서와 capability를 묶고, 완료는 한 번만 받는다.
 * 페이로드는 최종 검사를 통과한 공개 기록에서만 나온다.
 * `step`, `MachineState`, 전달 epoch, AOD, 그래픽 제한을 바꾸지 않는다.
 * 직렬화한 기록은 발급 증거가 아니다. 실제 SDK 출처 구분은 어댑터의 몫이다.
 */
class ProtectedBoundary(
    private val coordinator: AuthorityCoordinator,
    bindings: Collection<Pair<AuthorityScope, AuthorityRequest>>,
) {
    private val slots = LinkedHashMap<StreamKey, Slot>()

    init {
        for (binding in bindings) {
            slots.putIfAbsent(StreamKey(binding.first, binding.second), Slot())
        }
    }

    fun begin(
        capability: AuthorityCoordinator.AcquisitionCapability,
        scope: AuthorityScope,
        request: AuthorityRequest,
    ): ProtectionDecision {
        val key = StreamKey(scope, request)
        val slot = slots[key] ?: return reject(ProtectionIssue.UNKNOWN_MAPPING)
        if (!coordinator.permits(capability, scope, request)) {
            return reject(ProtectionIssue.NOT_PERMITTED)
        }
        if (capability.scope != scope || capability.request != request) {
            return reject(ProtectionIssue.RETAG_REJECTED)
        }
        if (slot.open != null || capability.acquisitionId <= slot.seenAcquisition) {
            return reject(ProtectionIssue.DUPLICATE_ACQUISITION)
        }
        val order = issueOrder(slot) ?: return reject(ProtectionIssue.ORDER_LOCKED)
        slot.seenAcquisition = capability.acquisitionId
        val open = BoundAcquisition(capability, scope, request, order, capability.generation, capability.acquisitionId)
        slot.open = open
        return ProtectionDecision(ProtectionOutcome.ACCEPTED, null, null, null, open)
    }

    fun accept(
        receipt: ProtectedReceipt,
        observation: Observation<*>,
        dataRevision: Long,
        referenceTime: Instant,
        provenance: ResultProvenance,
    ): ProtectionDecision {
        val bound = receipt as? BoundAcquisition ?: return reject(ProtectionIssue.FOREIGN_RECORD)
        val key = StreamKey(bound.scope, bound.request)
        val slot = slots[key] ?: return reject(ProtectionIssue.UNKNOWN_MAPPING)
        if (slot.open !== bound) {
            return reject(ProtectionIssue.STALE_RECEIPT)
        }
        if (provenance != ResultProvenance.CURRENT) {
            slot.open = null
            return reject(ProtectionIssue.PROVENANCE_REJECTED)
        }
        val screened = screen(observation, referenceTime)
        if (screened != null) {
            return reject(screened)
        }
        if (!coordinator.permits(bound.capability, bound.scope, bound.request)) {
            withdrawScope(bound.scope, WithdrawalReason.NOT_PERMITTED)
            return withdrawn(slot)
        }
        val parsedKey = observationKey(observation.source, bound.request.stream)
        if (parsedKey is DomainParse.Rejected) {
            return reject(ProtectionIssue.INVALID_OBSERVATION)
        }
        val observationKey = (parsedKey as DomainParse.Accepted).value
        val revision = revise(slot, observationKey, dataRevision, observation)
        if (revision != null) {
            return reject(revision)
        }
        bound.observation = observation
        bound.dataRevision = dataRevision
        bound.referenceTime = referenceTime
        slot.open = null
        slot.pending = bound
        slot.cursor = revisionCursor(observationKey, dataRevision, observation)
        return ProtectionDecision(ProtectionOutcome.ACCEPTED, null, null, null, bound)
    }

    fun commit(
        receipt: ProtectedReceipt,
        scope: AuthorityScope,
        request: AuthorityRequest,
        referenceTime: Instant,
    ): ProtectionDecision {
        if (receipt.scope != scope || receipt.request != request) {
            return reject(ProtectionIssue.RETAG_REJECTED)
        }
        val key = StreamKey(scope, request)
        val slot = slots[key] ?: return reject(ProtectionIssue.UNKNOWN_MAPPING)
        if (receipt === slot.pending) {
            return finish(slot, slot.pending!!, key, referenceTime)
        }
        if (receipt === slot.published) {
            return recheck(slot, slot.published!!, key, referenceTime)
        }
        if (receipt is BoundAcquisition || receipt is IssuedRecord) {
            return reject(ProtectionIssue.STALE_RECEIPT)
        }
        return reject(ProtectionIssue.FOREIGN_RECORD)
    }

    fun read(
        scope: AuthorityScope,
        request: AuthorityRequest,
        referenceTime: Instant,
    ): ProtectionDecision {
        val key = StreamKey(scope, request)
        val slot = slots[key] ?: return reject(ProtectionIssue.UNKNOWN_MAPPING)
        val pending = slot.pending
        if (pending != null) {
            return commit(pending, scope, request, referenceTime)
        }
        val published = slot.published
        if (published != null) {
            return commit(published, scope, request, referenceTime)
        }
        val withdrawal = slot.withdrawal
        if (withdrawal != null) {
            return ProtectionDecision(ProtectionOutcome.WITHDRAWN, null, null, withdrawal)
        }
        return reject(ProtectionIssue.ABSENT)
    }

    fun invalidate(scope: AuthorityScope): AuthorityDecision<AuthorityView> {
        val decision = coordinator.invalidate(scope)
        withdrawScope(scope, WithdrawalReason.AUTHORITY_INVALIDATED)
        return decision
    }

    fun noteStreamFault(
        scope: AuthorityScope,
        request: AuthorityRequest,
        status: ObservationStatus,
    ): ProtectionDecision {
        val reason = when (status) {
            ObservationStatus.ERROR -> WithdrawalReason.STREAM_ERROR
            ObservationStatus.UNAVAILABLE -> WithdrawalReason.STREAM_UNAVAILABLE
            else -> return reject(ProtectionIssue.INVALID_OBSERVATION)
        }
        val key = StreamKey(scope, request)
        val slot = slots[key] ?: return reject(ProtectionIssue.UNKNOWN_MAPPING)
        clearSlot(slot, reason, key)
        return withdrawn(slot)
    }

    /** 카운터만 상한으로 옮긴다. capability를 만들거나 권한을 허가하지 않는다. */
    internal fun placeOrderAtCeiling(scope: AuthorityScope, request: AuthorityRequest) {
        val slot = slots[StreamKey(scope, request)] ?: return
        slot.nextOrder = Long.MAX_VALUE
        slot.orderLocked = false
    }

    internal fun peekNextOrder(scope: AuthorityScope, request: AuthorityRequest): Long? {
        return slots[StreamKey(scope, request)]?.nextOrder
    }

    private fun finish(
        slot: Slot,
        pending: BoundAcquisition,
        key: StreamKey,
        referenceTime: Instant,
    ): ProtectionDecision {
        val observation = pending.observation ?: return reject(ProtectionIssue.STALE_RECEIPT)
        val timeReason = expiryReason(pending.referenceTime, observation, referenceTime)
        if (timeReason != null) {
            clearSlot(slot, timeReason, key)
            return withdrawn(slot)
        }
        if (!coordinator.permits(pending.capability, key.scope, key.request)) {
            withdrawScope(key.scope, WithdrawalReason.NOT_PERMITTED)
            return withdrawn(slot)
        }
        val record = IssuedRecord(
            capability = pending.capability,
            scope = pending.scope,
            request = pending.request,
            order = pending.order,
            generation = pending.generation,
            acquisitionId = pending.acquisitionId,
            dataRevision = pending.dataRevision,
            referenceTime = checkNotNull(pending.referenceTime),
            observation = observation,
        )
        slot.pending = null
        slot.published = record
        slot.withdrawal = null
        return ProtectionDecision(ProtectionOutcome.PUBLISHED, null, record, null)
    }

    private fun recheck(
        slot: Slot,
        published: IssuedRecord,
        key: StreamKey,
        referenceTime: Instant,
    ): ProtectionDecision {
        val timeReason = expiryReason(published.referenceTime, published.observation, referenceTime)
        if (timeReason != null) {
            clearSlot(slot, timeReason, key)
            return withdrawn(slot)
        }
        if (!coordinator.permits(published.capability, key.scope, key.request)) {
            withdrawScope(key.scope, WithdrawalReason.NOT_PERMITTED)
            return withdrawn(slot)
        }
        return ProtectionDecision(ProtectionOutcome.PUBLISHED, null, published, null)
    }

    private fun screen(observation: Observation<*>, referenceTime: Instant): ProtectionIssue? {
        if (!validateObservation(observation).accepted) {
            return ProtectionIssue.INVALID_OBSERVATION
        }
        if (observation.kind == ObservationKind.FORECAST) {
            return ProtectionIssue.FORECAST_SEPARATE
        }
        if (observation.kind != ObservationKind.OBSERVED || observation.status != ObservationStatus.VALID) {
            return ProtectionIssue.KIND_SEPARATE
        }
        if (observation.classifiedValue() !is ClassifiedValue.Reading) {
            return ProtectionIssue.VALUE_MISSING
        }
        return when (val derived = deriveStatus(observation, referenceTime)) {
            is StatusDerivation.Rejected -> ProtectionIssue.INVALID_OBSERVATION
            is StatusDerivation.DegradedToStale -> ProtectionIssue.TTL_SEPARATE
            is StatusDerivation.Unchanged ->
                if (derived.freshness == Freshness.FRESH) {
                    null
                } else {
                    ProtectionIssue.TTL_SEPARATE
                }
        }
    }

    private fun expiryReason(
        acceptedAt: Instant?,
        observation: Observation<*>,
        referenceTime: Instant,
    ): WithdrawalReason? {
        if (acceptedAt == null || referenceTime < acceptedAt) {
            return WithdrawalReason.CLOCK_ROLLBACK
        }
        return when (val derived = deriveStatus(observation, referenceTime)) {
            is StatusDerivation.DegradedToStale -> WithdrawalReason.EXPIRED
            is StatusDerivation.Rejected -> WithdrawalReason.EXPIRED
            is StatusDerivation.Unchanged ->
                if (derived.freshness == Freshness.FRESH) {
                    null
                } else {
                    WithdrawalReason.EXPIRED
                }
        }
    }

    @Suppress("UNCHECKED_CAST")
    private fun <T> revise(
        slot: Slot,
        key: io.github.scarlel96.aura.domain.ObservationKey,
        dataRevision: Long,
        observation: Observation<T>,
    ): ProtectionIssue? {
        val current = slot.cursor as RevisionCursor<T>?
        val decision = applyRevision(current, key, dataRevision, observation)
        return when (decision.outcome) {
            RevisionOutcome.ACCEPTED -> null
            RevisionOutcome.DUPLICATE,
            RevisionOutcome.DUPLICATE_CONFLICT,
            RevisionOutcome.SUPERSEDED_REJECTED,
            -> ProtectionIssue.SUPERSEDED
            else -> ProtectionIssue.INVALID_OBSERVATION
        }
    }

    private fun <T> revisionCursor(
        key: io.github.scarlel96.aura.domain.ObservationKey,
        dataRevision: Long,
        observation: Observation<T>,
    ): RevisionCursor<T> {
        return RevisionCursor(key, dataRevision, observation)
    }

    private fun issueOrder(slot: Slot): Long? {
        if (slot.orderLocked) {
            return null
        }
        val order = slot.nextOrder
        if (order == Long.MAX_VALUE) {
            slot.orderLocked = true
        } else {
            slot.nextOrder = order + 1
        }
        return order
    }

    private fun withdrawScope(scope: AuthorityScope, reason: WithdrawalReason) {
        for ((key, slot) in slots) {
            if (key.scope == scope) {
                clearSlot(slot, reason, key)
            }
        }
    }

    private fun clearSlot(slot: Slot, reason: WithdrawalReason, key: StreamKey) {
        val issued = if (slot.orderLocked) slot.nextOrder else slot.nextOrder - 1
        if (issued > slot.fence) {
            slot.fence = issued
        }
        slot.open = null
        slot.pending = null
        slot.published = null
        slot.cursor = null
        slot.withdrawal = StreamWithdrawal(key.scope, key.request, slot.fence, reason)
    }

    private fun withdrawn(slot: Slot): ProtectionDecision {
        return ProtectionDecision(ProtectionOutcome.WITHDRAWN, null, null, slot.withdrawal)
    }

    private fun reject(issue: ProtectionIssue): ProtectionDecision {
        return ProtectionDecision(ProtectionOutcome.REJECTED, issue, null, null)
    }

    private data class StreamKey(val scope: AuthorityScope, val request: AuthorityRequest)

    private class Slot {
        var nextOrder: Long = 1
        var orderLocked: Boolean = false
        var fence: Long = 0
        var seenAcquisition: Long = 0
        var open: BoundAcquisition? = null
        var pending: BoundAcquisition? = null
        var published: IssuedRecord? = null
        var cursor: RevisionCursor<*>? = null
        var withdrawal: StreamWithdrawal? = null
    }

    private class BoundAcquisition(
        val capability: AuthorityCoordinator.AcquisitionCapability,
        override val scope: AuthorityScope,
        override val request: AuthorityRequest,
        override val order: Long,
        override val generation: Long,
        override val acquisitionId: Long,
    ) : ProtectedReceipt {
        var observation: Observation<*>? = null
        var dataRevision: Long = 0
        var referenceTime: Instant? = null
    }

    private class IssuedRecord(
        val capability: AuthorityCoordinator.AcquisitionCapability,
        override val scope: AuthorityScope,
        override val request: AuthorityRequest,
        override val order: Long,
        override val generation: Long,
        override val acquisitionId: Long,
        override val dataRevision: Long,
        val referenceTime: Instant,
        val observation: Observation<*>,
    ) : ProtectedRecord {
        override fun payload(): Observation<*> = observation
    }
}

interface ProtectedReceipt {
    val scope: AuthorityScope
    val request: AuthorityRequest
    val order: Long
    val generation: Long
    val acquisitionId: Long
}

interface ProtectedRecord : ProtectedReceipt {
    val dataRevision: Long

    fun payload(): Observation<*>
}

enum class ResultProvenance {
    CURRENT,
    HISTORICAL,
    UNKNOWN,
}

enum class ProtectionOutcome {
    ACCEPTED,
    PUBLISHED,
    WITHDRAWN,
    REJECTED,
}

enum class ProtectionIssue {
    UNKNOWN_MAPPING,
    NOT_PERMITTED,
    RETAG_REJECTED,
    FOREIGN_RECORD,
    STALE_RECEIPT,
    DUPLICATE_ACQUISITION,
    PROVENANCE_REJECTED,
    INVALID_OBSERVATION,
    FORECAST_SEPARATE,
    KIND_SEPARATE,
    TTL_SEPARATE,
    VALUE_MISSING,
    SUPERSEDED,
    ORDER_LOCKED,
    ABSENT,
}

enum class WithdrawalReason {
    AUTHORITY_INVALIDATED,
    STREAM_ERROR,
    STREAM_UNAVAILABLE,
    ORDER_FENCE,
    NOT_PERMITTED,
    EXPIRED,
    CLOCK_ROLLBACK,
}

class StreamWithdrawal(
    val scope: AuthorityScope,
    val request: AuthorityRequest,
    val order: Long,
    val reason: WithdrawalReason,
)

class ProtectionDecision(
    val outcome: ProtectionOutcome,
    val issue: ProtectionIssue?,
    val record: ProtectedRecord?,
    val withdrawal: StreamWithdrawal?,
    val receipt: ProtectedReceipt? = null,
)
