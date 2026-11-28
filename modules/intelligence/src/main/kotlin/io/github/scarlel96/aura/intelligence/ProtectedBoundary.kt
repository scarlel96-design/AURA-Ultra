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
 * 권한 capability와 관측 하나를 묶는 수신·공개 경계다.
 * `step`, `MachineState`, 전달 epoch, AOD, 그래픽 제한을 바꾸지 않는다.
 * 직렬화한 기록은 발급 증거가 아니다. 호출자가 `commit`을 권한 무효화와 같은 순서로 호출한다.
 * 실제 SDK 결과 결합, 저장, 이력 정책, 동시성은 어댑터의 몫이다.
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

    fun accept(
        capability: AuthorityCoordinator.AcquisitionCapability,
        scope: AuthorityScope,
        request: AuthorityRequest,
        observation: Observation<*>,
        dataRevision: Long,
        referenceTime: Instant,
    ): ProtectionDecision {
        val slot = slots[StreamKey(scope, request)]
            ?: return reject(ProtectionIssue.UNKNOWN_MAPPING)
        val screened = screen(observation, referenceTime)
        if (screened != null) {
            return reject(screened)
        }
        if (!coordinator.permits(capability, scope, request)) {
            return reject(ProtectionIssue.NOT_PERMITTED)
        }
        if (capability.scope != scope || capability.request != request) {
            return reject(ProtectionIssue.RETAG_REJECTED)
        }
        val parsedKey = observationKey(observation.source, request.stream)
        if (parsedKey is DomainParse.Rejected) {
            return reject(ProtectionIssue.INVALID_OBSERVATION)
        }
        val key = (parsedKey as DomainParse.Accepted).value
        val revision = revise(slot, key, dataRevision, observation)
        if (revision != null) {
            return reject(revision)
        }
        val order = issueOrder(slot) ?: return reject(ProtectionIssue.ORDER_LOCKED)
        val record = IssuedRecord(
            capability = capability,
            scope = scope,
            request = request,
            order = order,
            generation = capability.generation,
            acquisitionId = capability.acquisitionId,
            dataRevision = dataRevision,
            observation = observation,
        )
        slot.pending = record
        slot.cursor = revisionCursor(key, dataRevision, observation)
        return ProtectionDecision(ProtectionOutcome.ACCEPTED, null, record, null)
    }

    fun commit(
        record: ProtectedRecord,
        scope: AuthorityScope,
        request: AuthorityRequest,
    ): ProtectionDecision {
        val issued = record as? IssuedRecord ?: return reject(ProtectionIssue.FOREIGN_RECORD)
        if (issued.scope != scope || issued.request != request) {
            return reject(ProtectionIssue.RETAG_REJECTED)
        }
        val slot = slots[StreamKey(scope, request)]
            ?: return reject(ProtectionIssue.UNKNOWN_MAPPING)
        if (slot.pending !== issued && slot.published !== issued) {
            return withdrawn(issued, WithdrawalReason.ORDER_FENCE)
        }
        if (issued.order <= slot.fence) {
            drop(slot, issued, WithdrawalReason.ORDER_FENCE)
            return withdrawn(issued, WithdrawalReason.ORDER_FENCE)
        }
        if (!coordinator.permits(issued.capability, scope, request)) {
            drop(slot, issued, WithdrawalReason.NOT_PERMITTED)
            return withdrawn(issued, WithdrawalReason.NOT_PERMITTED)
        }
        slot.pending = if (slot.pending === issued) null else slot.pending
        slot.published = issued
        slot.withdrawal = null
        return ProtectionDecision(ProtectionOutcome.PUBLISHED, null, issued, null)
    }

    fun read(scope: AuthorityScope, request: AuthorityRequest): ProtectionDecision {
        val slot = slots[StreamKey(scope, request)]
            ?: return reject(ProtectionIssue.UNKNOWN_MAPPING)
        val pending = slot.pending
        if (pending != null) {
            return commit(pending, scope, request)
        }
        val published = slot.published
        if (published != null) {
            return commit(published, scope, request)
        }
        val withdrawal = slot.withdrawal
        if (withdrawal != null) {
            return ProtectionDecision(ProtectionOutcome.WITHDRAWN, null, null, withdrawal)
        }
        return reject(ProtectionIssue.ABSENT)
    }

    fun invalidate(scope: AuthorityScope): AuthorityDecision<AuthorityView> {
        val decision = coordinator.invalidate(scope)
        for ((key, slot) in slots) {
            if (key.scope == scope) {
                seal(slot, WithdrawalReason.AUTHORITY_INVALIDATED, key)
            }
        }
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
        seal(slot, reason, key)
        return ProtectionDecision(ProtectionOutcome.WITHDRAWN, null, null, slot.withdrawal)
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

    private fun seal(slot: Slot, reason: WithdrawalReason, key: StreamKey) {
        val issued = if (slot.orderLocked) slot.nextOrder else slot.nextOrder - 1
        if (issued > slot.fence) {
            slot.fence = issued
        }
        slot.pending = null
        slot.published = null
        slot.cursor = null
        slot.withdrawal = StreamWithdrawal(key.scope, key.request, slot.fence, reason)
    }

    private fun drop(slot: Slot, record: IssuedRecord, reason: WithdrawalReason) {
        if (slot.pending === record) {
            slot.pending = null
        }
        if (slot.published === record) {
            slot.published = null
        }
        if (slot.pending == null && slot.published == null) {
            slot.cursor = null
        }
        if (record.order > slot.fence) {
            slot.fence = record.order
        }
        slot.withdrawal = StreamWithdrawal(record.scope, record.request, record.order, reason)
    }

    private fun withdrawn(record: IssuedRecord, reason: WithdrawalReason): ProtectionDecision {
        return ProtectionDecision(
            ProtectionOutcome.WITHDRAWN,
            null,
            null,
            StreamWithdrawal(record.scope, record.request, record.order, reason),
        )
    }

    private fun reject(issue: ProtectionIssue): ProtectionDecision {
        return ProtectionDecision(ProtectionOutcome.REJECTED, issue, null, null)
    }

    private data class StreamKey(val scope: AuthorityScope, val request: AuthorityRequest)

    private class Slot {
        var nextOrder: Long = 1
        var orderLocked: Boolean = false
        var fence: Long = 0
        var pending: IssuedRecord? = null
        var published: IssuedRecord? = null
        var cursor: RevisionCursor<*>? = null
        var withdrawal: StreamWithdrawal? = null
    }

    private class IssuedRecord(
        val capability: AuthorityCoordinator.AcquisitionCapability,
        override val scope: AuthorityScope,
        override val request: AuthorityRequest,
        override val order: Long,
        override val generation: Long,
        override val acquisitionId: Long,
        override val dataRevision: Long,
        private val observation: Observation<*>,
    ) : ProtectedRecord {
        override fun payload(): Observation<*> = observation
    }
}

interface ProtectedRecord {
    val scope: AuthorityScope
    val request: AuthorityRequest
    val order: Long
    val generation: Long
    val acquisitionId: Long
    val dataRevision: Long

    fun payload(): Observation<*>
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
)
