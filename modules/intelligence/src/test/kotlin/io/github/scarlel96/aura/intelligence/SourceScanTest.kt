package io.github.scarlel96.aura.intelligence

import java.io.File
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

internal val forbiddenSourceTokens = listOf(
    "import android",
    "androidx.",
    "import java.net",
    "java.net.URL",
    "HttpURLConnection",
    "Instant.now(",
    "LocalDate.now(",
    "LocalDateTime.now(",
    "ZonedDateTime.now(",
    "System.currentTimeMillis(",
    "System.nanoTime(",
    "Clock.system",
    "okhttp3",
)

internal fun forbiddenSourceHits(text: String): List<String> {
    return forbiddenSourceTokens.filter { token -> text.contains(token) }
}

class SourceScanTest {
    @Test
    fun plantedClockAndNetworkTokensAreDetected() {
        assertEquals(listOf("Instant.now("), forbiddenSourceHits("val clock = Instant.now()"))
        assertEquals(
            listOf("import java.net", "HttpURLConnection"),
            forbiddenSourceHits("import java.net.HttpURLConnection"),
        )
        assertEquals(emptyList(), forbiddenSourceHits("import java.time.Instant\nval t = Instant.parse(\"2026-11-28T00:00:00Z\")"))
    }

    @Test
    fun mainSourcesStayFreeOfPlatformClockAndNetwork() {
        val configured = System.getProperty("aura.intelligence.sources")
        assertTrue(!configured.isNullOrBlank(), "aura.intelligence.sources is missing")
        val root = File(configured)
        assertTrue(root.isDirectory, "missing source directory $configured")
        val hits = root.walkTopDown()
            .filter { it.isFile && it.extension == "kt" }
            .flatMap { file ->
                forbiddenSourceHits(file.readText()).map { token -> "${file.name}: $token" }
            }
            .toList()
        assertEquals(emptyList(), hits)
    }
}
