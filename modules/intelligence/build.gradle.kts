plugins {
    kotlin("jvm") version "2.4.21"
}

kotlin {
    jvmToolchain(17)
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
    }
}

java {
    toolchain {
        languageVersion.set(JavaLanguageVersion.of(17))
    }
}

dependencies {
    implementation("io.github.scarlel96.aura:aura-domain")
    testImplementation(kotlin("test-junit5"))
}

val intelligenceSources = layout.projectDirectory.dir("src/main/kotlin").asFile.absolutePath

tasks.withType<Test>().configureEach {
    useJUnitPlatform()
    val launcher = javaLauncher
    doFirst {
        val metadata = launcher.get().metadata
        logger.lifecycle(
            "TEST_JVM version=${metadata.languageVersion} vendor=${metadata.vendor} path=${metadata.installationPath}",
        )
    }
    systemProperty("aura.intelligence.sources", intelligenceSources)
    testLogging {
        events("passed", "failed", "skipped")
        exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
    }
}
