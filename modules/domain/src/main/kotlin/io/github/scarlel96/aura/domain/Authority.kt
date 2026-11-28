package io.github.scarlel96.aura.domain

/**
 * 순수 권한 검증 계약이다. 실제 SDK 접근, 기기 권한, 동시성, 이력 보관, 소비자 삭제를 허가하지 않는다.
 * 호출자가 준 Boolean, ticket 숫자, DTO, copy는 권한 증거가 아니다.
 * 같은 프로세스의 리플렉션이나 임의 코드 실행을 막지 않는다. 신뢰는 플랫폼 어댑터의 입력 구분에 있다.
 * 한 coordinator 호출은 호출자가 직렬화한다.
 */
enum class AuthorityState {
    UNKNOWN,
    GRANTED,
    DENIED,
}

/** 신뢰된 현재 확인의 결과. 호출자 Boolean으로 허가하지 않는다. */
enum class TrustedCheckResult {
    GRANTED,
    DENIED,
    FAILED,
}

enum class AuthorityOutcome {
    ACCEPTED,
    UNCHANGED,
    REJECTED,
    FENCED,
}

enum class AuthorityIssue {
    FOREIGN_ISSUER,
    FOREIGN_SESSION,
    STALE_TICKET,
    LOCKED,
    NOT_GRANTED,
    REQUEST_MISMATCH,
    UNTRUSTED_INPUT,
    DATA_STATUS_IGNORED,
    CONFLICT,
}

class AuthorityScope private constructor(
    val authority: String,
    val principal: String,
    val category: String,
) {
    override fun equals(other: Any?): Boolean {
        return other is AuthorityScope &&
            authority == other.authority &&
            principal == other.principal &&
            category == other.category
    }

    override fun hashCode(): Int = arrayOf(authority, principal, category).contentHashCode()

    companion object {
        fun parse(authority: String, principal: String, category: String): DomainParse<AuthorityScope> {
            val parsedAuthority = parseToken(authority)
            val parsedPrincipal = parseToken(principal)
            val parsedCategory = parseToken(category)
            if (parsedAuthority is DomainParse.Rejected) {
                return parsedAuthority
            }
            if (parsedPrincipal is DomainParse.Rejected) {
                return parsedPrincipal
            }
            if (parsedCategory is DomainParse.Rejected) {
                return parsedCategory
            }
            return DomainParse.Accepted(
                AuthorityScope(
                    (parsedAuthority as DomainParse.Accepted).value,
                    (parsedPrincipal as DomainParse.Accepted).value,
                    (parsedCategory as DomainParse.Accepted).value,
                ),
            )
        }
    }
}

class AuthoritySession private constructor(val token: String) {
    override fun equals(other: Any?): Boolean = other is AuthoritySession && token == other.token

    override fun hashCode(): Int = token.hashCode()

    companion object {
        fun parse(raw: String): DomainParse<AuthoritySession> {
            return when (val parsed = parseToken(raw)) {
                is DomainParse.Rejected -> parsed
                is DomainParse.Accepted -> DomainParse.Accepted(AuthoritySession(parsed.value))
            }
        }
    }
}

class AuthorityRequest private constructor(val stream: String) {
    override fun equals(other: Any?): Boolean = other is AuthorityRequest && stream == other.stream

    override fun hashCode(): Int = stream.hashCode()

    companion object {
        fun parse(raw: String): DomainParse<AuthorityRequest> {
            return when (val parsed = parseToken(raw)) {
                is DomainParse.Rejected -> parsed
                is DomainParse.Accepted -> DomainParse.Accepted(AuthorityRequest(parsed.value))
            }
        }
    }
}

class AuthorityView(
    val scope: AuthorityScope,
    val state: AuthorityState,
    val generation: Long,
    val locked: Boolean,
)

class AuthorityDecision<out T> internal constructor(
    val outcome: AuthorityOutcome,
    val issue: AuthorityIssue?,
    val view: AuthorityView,
    val value: T?,
)

class AuthorityCoordinator private constructor(
    private val session: AuthoritySession,
) {
    private val seal = Any()
    private val records = HashMap<AuthorityScope, ScopeRecord>()

    fun view(scope: AuthorityScope): AuthorityView = snapshot(scope, records[scope])

    fun issueCheck(scope: AuthorityScope): AuthorityDecision<CheckTicket> {
        val record = records.getOrPut(scope) { ScopeRecord() }
        if (record.locked || record.ticketsExhausted) {
            lock(record)
            return decide(AuthorityOutcome.REJECTED, AuthorityIssue.LOCKED, scope, record, null)
        }
        val number = record.nextTicket
        if (number == Long.MAX_VALUE) {
            record.ticketsExhausted = true
        } else {
            record.nextTicket = number + 1
        }
        val ticket = CheckTicket(seal, scope, session.token, record.generation, number)
        record.outstanding = ticket
        record.consumed = null
        record.consumedResult = null
        return decide(AuthorityOutcome.ACCEPTED, null, scope, record, ticket)
    }

    fun complete(ticket: CheckTicket, result: TrustedCheckResult): AuthorityDecision<AuthorityView> {
        if (ticket.seal !== seal) {
            return decide(AuthorityOutcome.REJECTED, AuthorityIssue.FOREIGN_ISSUER, ticket.scope, records[ticket.scope], null)
        }
        if (ticket.sessionToken != session.token) {
            return decide(AuthorityOutcome.REJECTED, AuthorityIssue.FOREIGN_SESSION, ticket.scope, records[ticket.scope], null)
        }
        val record = records[ticket.scope]
            ?: return decide(AuthorityOutcome.REJECTED, AuthorityIssue.STALE_TICKET, ticket.scope, null, null)
        if (record.locked) {
            return decide(AuthorityOutcome.REJECTED, AuthorityIssue.LOCKED, ticket.scope, record, null)
        }
        if (ticket === record.consumed) {
            if (result == record.consumedResult) {
                return decide(AuthorityOutcome.UNCHANGED, null, ticket.scope, record, null)
            }
            if (!rotate(record)) {
                return decide(AuthorityOutcome.REJECTED, AuthorityIssue.LOCKED, ticket.scope, record, null)
            }
            record.state = AuthorityState.UNKNOWN
            record.outstanding = null
            record.consumed = null
            record.consumedResult = null
            return decide(AuthorityOutcome.FENCED, AuthorityIssue.CONFLICT, ticket.scope, record, null)
        }
        if (ticket.generation != record.generation || ticket !== record.outstanding) {
            return decide(AuthorityOutcome.REJECTED, AuthorityIssue.STALE_TICKET, ticket.scope, record, null)
        }
        record.outstanding = null
        record.consumed = ticket
        record.consumedResult = result
        if (!apply(record, result)) {
            return decide(AuthorityOutcome.REJECTED, AuthorityIssue.LOCKED, ticket.scope, record, null)
        }
        return decide(AuthorityOutcome.ACCEPTED, null, ticket.scope, record, null)
    }

    fun invalidate(scope: AuthorityScope): AuthorityDecision<AuthorityView> {
        val record = records.getOrPut(scope) { ScopeRecord() }
        if (record.locked) {
            return decide(AuthorityOutcome.REJECTED, AuthorityIssue.LOCKED, scope, record, null)
        }
        if (!rotate(record)) {
            return decide(AuthorityOutcome.REJECTED, AuthorityIssue.LOCKED, scope, record, null)
        }
        record.state = AuthorityState.UNKNOWN
        clearOutstanding(record)
        return decide(AuthorityOutcome.ACCEPTED, null, scope, record, null)
    }

    fun rejectUntrusted(scope: AuthorityScope): AuthorityDecision<AuthorityView> {
        return decide(AuthorityOutcome.REJECTED, AuthorityIssue.UNTRUSTED_INPUT, scope, records[scope], null)
    }

    fun noteObservationStatus(scope: AuthorityScope, status: ObservationStatus): AuthorityDecision<AuthorityView> {
        require(status in ObservationStatus.entries)
        return decide(AuthorityOutcome.REJECTED, AuthorityIssue.DATA_STATUS_IGNORED, scope, records[scope], null)
    }

    fun acquire(scope: AuthorityScope, request: AuthorityRequest): AuthorityDecision<AcquisitionCapability> {
        val record = records[scope]
            ?: return decide(AuthorityOutcome.REJECTED, AuthorityIssue.NOT_GRANTED, scope, null, null)
        if (record.locked || record.state != AuthorityState.GRANTED) {
            return decide(AuthorityOutcome.REJECTED, AuthorityIssue.NOT_GRANTED, scope, record, null)
        }
        if (record.acquisitionsExhausted) {
            lock(record)
            return decide(AuthorityOutcome.REJECTED, AuthorityIssue.LOCKED, scope, record, null)
        }
        val acquisitionId = record.nextAcquisition
        if (acquisitionId == Long.MAX_VALUE) {
            record.acquisitionsExhausted = true
        } else {
            record.nextAcquisition = acquisitionId + 1
        }
        val capability = IssuedCapability(
            record.issuance,
            scope,
            session.token,
            record.generation,
            request,
            acquisitionId,
        )
        return decide(AuthorityOutcome.ACCEPTED, null, scope, record, capability)
    }

    fun permits(
        capability: AcquisitionCapability,
        scope: AuthorityScope,
        request: AuthorityRequest,
    ): Boolean {
        val issued = capability as? IssuedCapability ?: return false
        val record = records[scope]
        return issued.matches(
            scope,
            request,
            session.token,
            record?.issuance,
            record?.generation,
            granted = record?.state == AuthorityState.GRANTED,
            locked = record?.locked == true,
        )
    }

    private fun apply(record: ScopeRecord, result: TrustedCheckResult): Boolean {
        when (result) {
            TrustedCheckResult.FAILED -> {
                if (!rotate(record)) {
                    return false
                }
                record.state = AuthorityState.UNKNOWN
                record.outstanding = null
            }
            TrustedCheckResult.GRANTED -> {
                if (record.state != AuthorityState.GRANTED) {
                    if (!rotate(record)) {
                        return false
                    }
                    record.state = AuthorityState.GRANTED
                }
            }
            TrustedCheckResult.DENIED -> {
                if (record.state != AuthorityState.DENIED) {
                    if (!rotate(record)) {
                        return false
                    }
                    record.state = AuthorityState.DENIED
                }
            }
        }
        return true
    }

    private fun rotate(record: ScopeRecord): Boolean {
        if (record.generation == Long.MAX_VALUE) {
            lock(record)
            return false
        }
        record.generation += 1
        record.issuance = Issuance()
        return true
    }

    private fun lock(record: ScopeRecord) {
        record.locked = true
        record.state = AuthorityState.UNKNOWN
        record.issuance = Issuance()
        clearOutstanding(record)
    }

    private fun clearOutstanding(record: ScopeRecord) {
        record.outstanding = null
        record.consumed = null
        record.consumedResult = null
    }

    private fun snapshot(scope: AuthorityScope, record: ScopeRecord?): AuthorityView {
        if (record == null) {
            return AuthorityView(scope, AuthorityState.UNKNOWN, 0, locked = false)
        }
        return AuthorityView(scope, record.state, record.generation, record.locked)
    }

    private fun <T> decide(
        outcome: AuthorityOutcome,
        issue: AuthorityIssue?,
        scope: AuthorityScope,
        record: ScopeRecord?,
        value: T?,
    ): AuthorityDecision<T> {
        return AuthorityDecision(outcome, issue, snapshot(scope, record), value)
    }

    private class ScopeRecord {
        var state: AuthorityState = AuthorityState.UNKNOWN
        var generation: Long = 0
        var nextTicket: Long = 1
        var ticketsExhausted: Boolean = false
        var locked: Boolean = false
        var outstanding: CheckTicket? = null
        var consumed: CheckTicket? = null
        var consumedResult: TrustedCheckResult? = null
        var nextAcquisition: Long = 1
        var acquisitionsExhausted: Boolean = false
        var issuance: Issuance = Issuance()
    }

    private class Issuance

    class CheckTicket internal constructor(
        internal val seal: Any,
        val scope: AuthorityScope,
        internal val sessionToken: String,
        val generation: Long,
        val number: Long,
    )

    interface AcquisitionCapability {
        val scope: AuthorityScope
        val generation: Long
        val request: AuthorityRequest
        val acquisitionId: Long
    }

    private class IssuedCapability(
        private val issuance: Issuance,
        override val scope: AuthorityScope,
        private val sessionToken: String,
        override val generation: Long,
        override val request: AuthorityRequest,
        override val acquisitionId: Long,
    ) : AcquisitionCapability {
        fun matches(
            scope: AuthorityScope,
            request: AuthorityRequest,
            sessionToken: String,
            issuance: Issuance?,
            generation: Long?,
            granted: Boolean,
            locked: Boolean,
        ): Boolean {
            return !locked &&
                granted &&
                this.scope == scope &&
                this.request == request &&
                this.sessionToken == sessionToken &&
                this.generation == generation &&
                this.issuance === issuance
        }
    }

    companion object {
        fun open(session: AuthoritySession): AuthorityCoordinator = AuthorityCoordinator(session)

        /** 카운터 위치만 옮긴다. 상태를 GRANTED로 만들지 않는다. */
        internal fun openNearCeiling(
            session: AuthoritySession,
            scope: AuthorityScope,
            nextTicket: Long,
            generation: Long,
        ): AuthorityCoordinator {
            require(nextTicket >= 1L) { "ticket counter must be positive" }
            require(generation >= 0L) { "generation must be non-negative" }
            val coordinator = AuthorityCoordinator(session)
            val record = ScopeRecord()
            record.nextTicket = nextTicket
            record.generation = generation
            coordinator.records[scope] = record
            return coordinator
        }
    }
}
