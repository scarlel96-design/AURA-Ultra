package io.github.scarlel96.aura.intelligence

import java.io.File
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotEquals
import kotlin.test.assertTrue

class JunitXmlCheckTest {
    @Test
    fun acceptsMatchingFreshResults() {
        val dir = fixtureDir()
        writeSuite(dir, "Alpha", 2, Instant.parse("2026-11-28T00:10:00Z"))
        writeSuite(dir, "Beta", 3, Instant.parse("2026-11-28T00:11:00Z"))
        val result = runCheck(dir, files = 2, tests = 5, notBefore = "2026-11-28T00:00:00Z")
        assertEquals(0, result.exitCode, result.output)
        assertTrue(result.output.contains("OK files=2 tests=5"))
    }

    @Test
    fun rejectsMissingResultFile() {
        val dir = fixtureDir()
        val result = runCheck(dir, files = 1, tests = 1, notBefore = null)
        assertNotEquals(0, result.exitCode)
        assertTrue(result.output.contains("no JUnit XML"))
    }

    @Test
    fun rejectsMissingDirectory() {
        val missing = File(fixtureDir(), "absent")
        val result = runCheck(missing, files = 1, tests = 1, notBefore = null)
        assertNotEquals(0, result.exitCode)
        assertTrue(result.output.contains("missing directory"))
    }

    @Test
    fun rejectsEmptyFile() {
        val dir = fixtureDir()
        File(dir, "TEST-empty.xml").writeText("")
        val result = runCheck(dir, files = 1, tests = 1, notBefore = null)
        assertNotEquals(0, result.exitCode)
        assertTrue(result.output.contains("empty XML"))
    }

    @Test
    fun rejectsCorruptXml() {
        val dir = fixtureDir()
        File(dir, "TEST-corrupt.xml").writeText("<testsuite>")
        val result = runCheck(dir, files = 1, tests = 1, notBefore = null)
        assertNotEquals(0, result.exitCode)
        assertTrue(result.output.contains("corrupt XML"))
    }

    @Test
    fun rejectsZeroTests() {
        val dir = fixtureDir()
        File(dir, "TEST-zero.xml").writeText("""<testsuite name="zero" tests="0" failures="0" errors="0" skipped="0"/>""")
        val result = runCheck(dir, files = 1, tests = 1, notBefore = null)
        assertNotEquals(0, result.exitCode)
        assertTrue(result.output.contains("discovered no tests"))
    }

    @Test
    fun rejectsCountMismatch() {
        val dir = fixtureDir()
        writeSuite(dir, "Alpha", 2, Instant.parse("2026-11-28T00:10:00Z"))
        val result = runCheck(dir, files = 1, tests = 9, notBefore = null)
        assertNotEquals(0, result.exitCode)
        assertTrue(result.output.contains("!="))
    }

    @Test
    fun rejectsHiddenFailure() {
        val dir = fixtureDir()
        File(dir, "TEST-hidden.xml").writeText(
            """
            <testsuite name="hidden" tests="1" failures="0" errors="0" skipped="0" timestamp="2026-11-28T00:10:00Z">
              <testcase classname="hidden" name="one"><failure message="boom"/></testcase>
            </testsuite>
            """.trimIndent(),
        )
        val result = runCheck(dir, files = 1, tests = 1, notBefore = null)
        assertNotEquals(0, result.exitCode)
        assertTrue(result.output.contains("hidden or mismatched failures"))
    }

    @Test
    fun rejectsHiddenError() {
        val dir = fixtureDir()
        File(dir, "TEST-error.xml").writeText(
            """
            <testsuite name="error" tests="1" failures="0" errors="0" skipped="0" timestamp="2026-11-28T00:10:00Z">
              <testcase classname="error" name="one"><error message="boom"/></testcase>
            </testsuite>
            """.trimIndent(),
        )
        val result = runCheck(dir, files = 1, tests = 1, notBefore = null)
        assertNotEquals(0, result.exitCode)
        assertTrue(result.output.contains("hidden or mismatched errors"))
    }

    @Test
    fun rejectsHiddenSkip() {
        val dir = fixtureDir()
        File(dir, "TEST-skip.xml").writeText(
            """
            <testsuite name="skip" tests="1" failures="0" errors="0" skipped="0" timestamp="2026-11-28T00:10:00Z">
              <testcase classname="skip" name="one"><skipped/></testcase>
            </testsuite>
            """.trimIndent(),
        )
        val result = runCheck(dir, files = 1, tests = 1, notBefore = null)
        assertNotEquals(0, result.exitCode)
        assertTrue(result.output.contains("hidden or mismatched skips"))
    }

    @Test
    fun rejectsDuplicateSuiteAndTestcase() {
        val dir = fixtureDir()
        val body = """
            <testsuite name="same" tests="1" failures="0" errors="0" skipped="0" timestamp="2026-11-28T00:10:00Z">
              <testcase classname="same" name="one"/>
            </testsuite>
        """.trimIndent()
        File(dir, "TEST-a.xml").writeText(body)
        File(dir, "TEST-b.xml").writeText(body)
        val result = runCheck(dir, files = 2, tests = 2, notBefore = null)
        assertNotEquals(0, result.exitCode)
        assertTrue(result.output.contains("duplicate"))
    }

    @Test
    fun rejectsStaleTimestamp() {
        val dir = fixtureDir()
        writeSuite(dir, "Old", 1, Instant.parse("2020-01-01T00:00:00Z"))
        val result = runCheck(dir, files = 1, tests = 1, notBefore = "2026-11-28T00:00:00Z")
        assertNotEquals(0, result.exitCode)
        assertTrue(result.output.contains("stale XML"))
    }

    @Test
    fun rejectsHeaderCaseMismatch() {
        val dir = fixtureDir()
        File(dir, "TEST-header.xml").writeText(
            """
            <testsuite name="header" tests="2" failures="0" errors="0" skipped="0" timestamp="2026-11-28T00:10:00Z">
              <testcase classname="header" name="only"/>
            </testsuite>
            """.trimIndent(),
        )
        val result = runCheck(dir, files = 1, tests = 2, notBefore = null)
        assertNotEquals(0, result.exitCode)
        assertTrue(result.output.contains("header tests"))
    }

    private fun writeSuite(dir: File, name: String, cases: Int, timestamp: Instant) {
        val body = buildString {
            append("""<testsuite name="$name" tests="$cases" failures="0" errors="0" skipped="0" timestamp="$timestamp">""")
            repeat(cases) { index ->
                append("""<testcase classname="$name" name="case$index"/>""")
            }
            append("</testsuite>")
        }
        File(dir, "TEST-$name.xml").writeText(body)
    }

    private fun fixtureDir(): File {
        val dir = File(System.getProperty("java.io.tmpdir"), "gb02-junit-${System.nanoTime()}")
        check(dir.mkdirs())
        return dir
    }

    private fun runCheck(dir: File, files: Int, tests: Int, notBefore: String?): CheckResult {
        val script = File(System.getProperty("aura.intelligence.junitTool") ?: error("junit tool path is missing"))
        assertTrue(script.isFile, script.path)
        val command = mutableListOf("python", script.absolutePath, "--dir", dir.absolutePath, "--files", files.toString(), "--tests", tests.toString())
        if (notBefore != null) {
            command += listOf("--not-before", notBefore)
        }
        val process = ProcessBuilder(command).redirectErrorStream(true).start()
        val output = process.inputStream.bufferedReader().readText()
        return CheckResult(process.waitFor(), output)
    }

    private data class CheckResult(val exitCode: Int, val output: String)
}
