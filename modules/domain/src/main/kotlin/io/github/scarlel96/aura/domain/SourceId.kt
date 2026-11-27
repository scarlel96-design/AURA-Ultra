package io.github.scarlel96.aura.domain

@JvmInline
value class SourceId private constructor(val value: String) {
    companion object {
        fun parse(raw: String): DomainParse<SourceId> {
            return when (val token = parseToken(raw)) {
                is DomainParse.Rejected -> token
                is DomainParse.Accepted -> DomainParse.Accepted(SourceId(token.value))
            }
        }
    }
}
