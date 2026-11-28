pluginManagement {
    repositories {
        gradlePluginPortal()
        mavenCentral()
    }
}

plugins {
    id("org.gradle.toolchains.foojay-resolver-convention") version "1.0.0"
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        mavenCentral()
    }
}

rootProject.name = "aura-intelligence"

includeBuild("../domain") {
    dependencySubstitution {
        substitute(module("io.github.scarlel96.aura:aura-domain")).using(project(":"))
    }
}
