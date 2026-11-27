plugins {
    id("com.android.application")
}

android {
    namespace = "io.github.scarlel96.aura.watchface"
    compileSdk = 37

    defaultConfig {
        applicationId = "io.github.scarlel96.aura.watchface"
        minSdk = 34
        targetSdk = 37
        versionCode = 1
        versionName = "0.1.0-bootstrap"
    }

    flavorDimensions += "format"
    productFlavors {
        create("wff2") {
            dimension = "format"
            minSdk = 34
            applicationIdSuffix = ".wff2"
            manifestPlaceholders["wffVersion"] = "2"
        }
        create("wff3") {
            dimension = "format"
            minSdk = 35
            applicationIdSuffix = ".wff3"
            manifestPlaceholders["wffVersion"] = "3"
        }
        create("wff4") {
            dimension = "format"
            minSdk = 36
            applicationIdSuffix = ".wff4"
            manifestPlaceholders["wffVersion"] = "4"
        }
        create("wff5") {
            dimension = "format"
            minSdk = 37
            applicationIdSuffix = ".wff5"
            manifestPlaceholders["wffVersion"] = "5"
        }
    }
    buildTypes {
        // Remove generated code without shrinking declarative face resources.
        debug {
            isMinifyEnabled = true
            isShrinkResources = false
        }
        release {
            isMinifyEnabled = true
            isShrinkResources = false
        }
    }
    buildFeatures {
        buildConfig = false
    }
}
