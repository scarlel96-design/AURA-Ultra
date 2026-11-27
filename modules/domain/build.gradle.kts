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
    testImplementation(kotlin("test-junit5"))
}

val domainSources = layout.projectDirectory.dir("src/main/kotlin").asFile.absolutePath

tasks.withType<Test>().configureEach {
    useJUnitPlatform()
    systemProperty("aura.domain.sources", domainSources)
    testLogging {
        events("passed", "failed", "skipped")
        exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
    }
}
