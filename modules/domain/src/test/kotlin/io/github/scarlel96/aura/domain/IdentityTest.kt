package io.github.scarlel96.aura.domain

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertNotEquals

class IdentityTest {
    @Test
    fun sourceIdKeepsCanonicalToken() {
        val parsed = SourceId.parse("kma.observation")
        assertIs<DomainParse.Accepted<SourceId>>(parsed)
        assertEquals("kma.observation", parsed.value.value)
    }

    @Test
    fun sourceIdRejectsBlankWhitespaceAndControl() {
        assertEquals(ParseCode.BLANK, (SourceId.parse("") as DomainParse.Rejected).code)
        assertEquals(ParseCode.BLANK, (SourceId.parse("   ") as DomainParse.Rejected).code)
        assertEquals(ParseCode.PADDED, (SourceId.parse(" kma ") as DomainParse.Rejected).code)
        assertEquals(ParseCode.CONTROL_CHARACTER, (SourceId.parse("kma\nid") as DomainParse.Rejected).code)
    }

    @Test
    fun sourceIdIsCaseSensitiveAndDoesNotTrim() {
        val lower = SourceId.parse("kma")
        val upper = SourceId.parse("KMA")
        assertIs<DomainParse.Accepted<SourceId>>(lower)
        assertIs<DomainParse.Accepted<SourceId>>(upper)
        assertNotEquals(lower.value, upper.value)
        assertIs<DomainParse.Rejected>(SourceId.parse("kma "))
    }

    @Test
    fun subjectAcceptsUnnormalizedKoreanToken() {
        val parsed = observationKey(acceptedSource(), "심박")
        assertIs<DomainParse.Accepted<ObservationKey>>(parsed)
        assertEquals("심박", parsed.value.subject)
    }

    @Test
    fun subjectRejectsBlankAndPaddedToken() {
        assertEquals(ParseCode.BLANK, (observationKey(acceptedSource(), "") as DomainParse.Rejected).code)
        assertEquals(ParseCode.PADDED, (observationKey(acceptedSource(), " hr ") as DomainParse.Rejected).code)
    }
}
