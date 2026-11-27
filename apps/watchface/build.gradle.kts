plugins {
    id("com.android.application")
}

android {
    namespace = "io.github.scarlel96.aura.watchface"
    compileSdk = 36

    defaultConfig {
        applicationId = "io.github.scarlel96.aura.watchface"
        minSdk = 34
        targetSdk = 36
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
    }
    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }
    buildFeatures {
        buildConfig = false
    }
}
