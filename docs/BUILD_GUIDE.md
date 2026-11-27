# Bootstrap build guide
Status: provisional development foundation. Not the approved Signature design.

## Toolchain
JDK 17, Gradle Wrapper 8.11.1, AGP 8.10.1, Android SDK 36, build-tools 35.0.0, Python 3.10+. AGP 8.10 supports API 36 and requires Gradle 8.11.1/JDK17. See https://developer.android.com/build/releases/agp-8-10-0-release-notes and https://gradle.org/release-checksums/.
Gradle wrapper scripts and JAR are from the Gradle v8.11.1 tag. Distribution checksum is pinned. CI checks the official wrapper checksum before execution. Retain original notices.

## Windows
Install Android Studio, SDK 36, build-tools 35.0.0 and JDK17. Configure JAVA_HOME and ANDROID_HOME or local.properties. Do not commit local.properties.
Run:
```powershell
python tools/check_foundation.py
python tools/verify_wff.py
.\gradlew.bat :apps:watchface:assembleWff2Debug :apps:watchface:assembleWff3Debug :apps:watchface:assembleWff4Debug
python tools/check_apk.py
```
Linux: use ./gradlew with the same tasks. The official validator script verifies a pinned release digest; if Google replaces the asset, stop and review the new release. No unverified fallback.

## Select a debug APK
| Variant | Minimum API | Application ID suffix |
|---|---:|---|
| wff2Debug | 34 | .wff2 |
| wff3Debug | 35 | .wff3 |
| wff4Debug | 36 | .wff4 |
WFF5 is a planned profile, not a built variant. Current shared WFF XML deliberately uses only baseline constructs. Newer variants do not yet implement exclusive effects. Debug IDs are provisional and allow side-by-side tests. Production package identity, signing and version migration require ADR approval.

Output: apps/watchface/build/outputs/apk/<variant>/debug/. GitHub Actions uploads debug APKs only after validation and build succeed.
Use Android Studio's watch face run configuration or adb -s <verified-device> install -r <apk-path>. Check the actual OS and use a supported profile. Do not activate a face automatically on an unknown device. Select the installed face in the watch face picker. No release signing or Play publication is configured.

## Scope
Bootstrap shows time/date, battery and step/goal in active mode. Ambient hides decoration and shows thin time. Preview is an original approximate bitmap, not a runtime screenshot. Replace it with the actual approved face capture. Health, weather, Reference, WFF4 continuity, WFF5, services and companion app are not implemented. The token JSON is a starting contract, not a generator. Keep shared resources until the next feature-specific WO warrants an override or build-time generator.
