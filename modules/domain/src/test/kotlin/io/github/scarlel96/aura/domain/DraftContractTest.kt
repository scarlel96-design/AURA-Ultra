package io.github.scarlel96.aura.domain

import io.github.scarlel96.aura.domain.draft.ContextSnapshotDraft
import io.github.scarlel96.aura.domain.draft.PresentationIntentDraft
import io.github.scarlel96.aura.domain.draft.WeatherSnapshotDraft
import io.github.scarlel96.aura.domain.draft.validateContextSnapshotDraft
import io.github.scarlel96.aura.domain.draft.validatePresentationIntentDraft
import io.github.scarlel96.aura.domain.draft.validateWeatherSnapshotDraft
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

class DraftContractTest {
    private val observedAt = Instant.parse("2026-11-27T00:00:00Z")
    private val validFrom = Instant.parse("2026-11-27T03:00:00Z")
    private val validTo = Instant.parse("2026-11-27T06:00:00Z")

    private fun rain(kind: ObservationKind, value: Double?): Observation<Double> {
        return observation(
            value = value,
            unit = "mm",
            observedAt = observedAt,
            kind = kind,
            status = if (value == null) ObservationStatus.UNAVAILABLE else ObservationStatus.VALID,
        )
    }

    @Test
    fun forecastWindowIsSeparateFromObservedAt() {
        val forecast = rain(ObservationKind.FORECAST, 1.5)
        val draft = weather(forecastRain = forecast)
        assertTrue(validateWeatherSnapshotDraft(draft).accepted)
        assertEquals(validFrom, draft.validFrom)
        assertEquals(observedAt, draft.forecastRain?.observedAt)
        assertTrue(draft.validFrom != draft.forecastRain?.observedAt)
    }

    @Test
    fun observedAndForecastRainStayDistinctIncludingZero() {
        val draft = weather(
            observedRain = rain(ObservationKind.OBSERVED, 0.0),
            forecastRain = rain(ObservationKind.FORECAST, 4.0),
        )
        assertTrue(validateWeatherSnapshotDraft(draft).accepted)
        assertEquals(ObservationKind.OBSERVED, draft.observedRain?.kind)
        assertEquals(ObservationKind.FORECAST, draft.forecastRain?.kind)
        assertEquals(0.0, draft.observedRain?.value)
        assertEquals(4.0, draft.forecastRain?.value)
    }

    @Test
    fun missingRainStaysNull() {
        val draft = weather(observedRain = null, forecastRain = null, probability = null)
        assertTrue(validateWeatherSnapshotDraft(draft).accepted)
        assertNull(draft.observedRain)
        assertNull(draft.forecastRain)
        assertNull(draft.probability)
    }

    @Test
    fun wrongRainKindIsReportedAndNotCoerced() {
        val draft = weather(
            observedRain = rain(ObservationKind.FORECAST, 1.0),
            forecastRain = rain(ObservationKind.ESTIMATED, 2.0),
        )
        val codes = validateWeatherSnapshotDraft(draft).codes()
        assertEquals(listOf(IssueCode.KIND_MISMATCH, IssueCode.KIND_MISMATCH), codes)
        assertEquals(ObservationKind.FORECAST, draft.observedRain?.kind)
        assertEquals(ObservationKind.ESTIMATED, draft.forecastRain?.kind)
    }

    @Test
    fun probabilityKindIsNotRewritten() {
        val probability = rain(ObservationKind.FORECAST, 0.4)
        val draft = weather(probability = probability)
        assertTrue(validateWeatherSnapshotDraft(draft).accepted)
        assertEquals(ObservationKind.FORECAST, draft.probability?.kind)
        assertEquals(0.4, draft.probability?.value)
    }

    @Test
    fun invertedAndEmptyValidityWindowsFail() {
        val inverted = weather(validFrom = validTo, validTo = validFrom)
        val empty = weather(validFrom = validFrom, validTo = validFrom)
        assertEquals(listOf(IssueCode.VALIDITY_WINDOW_INVERTED), validateWeatherSnapshotDraft(inverted).codes())
        assertEquals(listOf(IssueCode.VALIDITY_WINDOW_EMPTY), validateWeatherSnapshotDraft(empty).codes())
    }

    @Test
    fun blankLocationIsRejected() {
        val draft = weather(locationId = " ")
        assertEquals(listOf(IssueCode.LOCATION_ID_BLANK), validateWeatherSnapshotDraft(draft).codes())
    }

    @Test
    fun nestedInvalidObservationFailsTheDraft() {
        val broken = observation(
            value = 1.0,
            unit = "",
            kind = ObservationKind.OBSERVED,
        )
        val draft = weather(observedRain = broken)
        assertEquals(listOf(IssueCode.UNIT_BLANK), validateWeatherSnapshotDraft(draft).codes())
    }

    @Test
    fun contextDraftDoesNotDefaultMissingAxes() {
        val draft = ContextSnapshotDraft(
            weather = null,
            activity = null,
            power = null,
            timeOfDay = null,
            connectivity = null,
            userMode = null,
            dataQuality = null,
        )
        assertTrue(validateContextSnapshotDraft(draft).accepted)
        assertNull(draft.activity)
        assertNull(draft.power)
        assertNull(draft.dataQuality)
    }

    @Test
    fun contextBlankTokenIsRejectedAndZeroCharacterStaysOpaque() {
        val padded = ContextSnapshotDraft(null, " ", null, null, null, null, null)
        val empty = padded.copy(activity = "")
        val zeroCharacter = padded.copy(activity = "0")
        assertEquals(listOf(IssueCode.TOKEN_BLANK), validateContextSnapshotDraft(padded).codes())
        assertEquals(listOf(IssueCode.TOKEN_BLANK), validateContextSnapshotDraft(empty).codes())
        assertTrue(validateContextSnapshotDraft(zeroCharacter).accepted)
        assertEquals("0", zeroCharacter.activity)
    }

    @Test
    fun presentationRevisionZeroIsDistinctFromNull() {
        val unassigned = PresentationIntentDraft(null, null, null, null, null, null)
        val zero = unassigned.copy(revision = 0)
        assertTrue(validatePresentationIntentDraft(unassigned).accepted)
        assertTrue(validatePresentationIntentDraft(zero).accepted)
        assertNull(unassigned.revision)
        assertEquals(0, zero.revision)
        assertNull(unassigned.motionAllowed)
    }

    @Test
    fun blankReasonCodeIsRejected() {
        val draft = PresentationIntentDraft("time", "signature", null, true, listOf("ok", " "), 3)
        assertEquals(listOf(IssueCode.TOKEN_BLANK), validatePresentationIntentDraft(draft).codes())
    }

    private fun weather(
        locationId: String? = "fixture-location",
        validFrom: Instant? = this.validFrom,
        validTo: Instant? = this.validTo,
        probability: Observation<Double>? = null,
        observedRain: Observation<Double>? = null,
        forecastRain: Observation<Double>? = null,
    ): WeatherSnapshotDraft {
        return WeatherSnapshotDraft(
            locationId = locationId,
            issuedAt = observedAt,
            validFrom = validFrom,
            validTo = validTo,
            probability = probability,
            observedRain = observedRain,
            forecastRain = forecastRain,
        )
    }
}
