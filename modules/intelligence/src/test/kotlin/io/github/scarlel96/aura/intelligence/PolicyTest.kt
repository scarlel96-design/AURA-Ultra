package io.github.scarlel96.aura.intelligence

import java.time.Duration
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertTrue

class PolicyTest {
    @Test
    fun documentedCandidatesRemainConfigurable() {
        val documented = PolicyCandidates.documented()
        assertEquals(15.0, documented.powerEnterPercent)
        assertEquals(20.0, documented.powerExitPercent)
        assertEquals(70.0, documented.precipEnter)
        assertEquals(50.0, documented.precipExit)
        assertEquals(Duration.ofSeconds(60), documented.minimumHold)
        assertEquals(Duration.ZERO, documented.debounce)
        assertEquals(emptyList(), documented.issues())
        val replaced = documented.copy(powerEnterPercent = 30.0, powerExitPercent = 40.0, minimumHold = Duration.ofSeconds(5))
        assertEquals(emptyList(), replaced.issues())
        assertEquals(15.0, PolicyCandidates.documented().powerEnterPercent)
        assertEquals(Duration.ofSeconds(60), PolicyCandidates.documented().minimumHold)
    }

    @Test
    fun powerBandMustRise() {
        val policy = PolicyCandidates.documented().copy(powerEnterPercent = 20.0, powerExitPercent = 15.0)
        assertTrue(policy.issues().any { it.contains("power enter") })
    }

    @Test
    fun precipitationBandMustFall() {
        val policy = PolicyCandidates.documented().copy(precipEnter = 50.0, precipExit = 70.0)
        assertTrue(policy.issues().any { it.contains("precipitation enter") })
    }

    @Test
    fun durationsAndScalesAndUnitsMustBeUsable() {
        val negative = PolicyCandidates.documented().copy(debounce = Duration.ofSeconds(-1))
        assertTrue(negative.issues().any { it.contains("durations") })
        val infinite = PolicyCandidates.documented().copy(powerEnterPercent = Double.NaN)
        assertTrue(infinite.issues().any { it.contains("finite") })
        val scale = PolicyCandidates.documented().copy(percentMinimum = 10.0, percentMaximum = 0.0)
        assertTrue(scale.issues().any { it.contains("percent scale") })
        val blank = PolicyCandidates.documented().copy(tokenUnit = " ")
        assertTrue(blank.issues().any { it.contains("unit tokens") })
    }

    @Test
    fun rejectedPolicyDoesNotAdvance() {
        val policy = PolicyCandidates.documented().copy(powerEnterPercent = 20.0, powerExitPercent = 20.0)
        val result = assertIs<StepResult.PolicyRejected>(step(null, sample(battery = reading(10.0, "percent")), policy))
        assertEquals(policy.issues(), result.issues)
    }
}
