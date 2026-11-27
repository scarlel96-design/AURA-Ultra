package io.github.scarlel96.aura.domain

import java.io.File
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class SourceScanTest {
    @Test
    fun mainSourcesStayFreeOfPlatformClockAndNetwork() {
        val configured = System.getProperty("aura.domain.sources")
        assertTrue(!configured.isNullOrBlank(), "aura.domain.sources is missing")
        val root = File(configured)
        assertTrue(root.isDirectory, "missing source directory $configured")
        val forbidden = listOf(
            "import android",
            "androidx.",
            "import java.net",
            "Instant.now(",
            "System.currentTimeMillis(",
            "Clock.system",
            "okhttp3",
        )
        val hits = root.walkTopDown()
            .filter { it.isFile && it.extension == "kt" }
            .flatMap { file ->
                val text = file.readText()
                forbidden.filter { token -> text.contains(token) }.map { token -> "${file.path}: $token" }
            }
            .toList()
        assertEquals(emptyList(), hits)
    }
}
