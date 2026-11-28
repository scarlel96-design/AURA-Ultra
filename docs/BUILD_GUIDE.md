# Bootstrap build guide
Status: current Bootstrap development build instructions. Signature remains a separate, unapproved development candidate. Product release is NO-GO. See [STATUS](STATUS.md) for the latest exact CI evidence.

## Toolchain
JDK 17, Gradle Wrapper 9.3.1, AGP 9.1.1, Android SDK package `platforms;android-37.0`, build-tools 36.0.0, and Python 3.12 (canonical CI and generation environment). AGP 9.1.1 supports API 37 and requires Gradle 9.3.1/JDK17. See https://developer.android.com/build/releases/agp-9-1-0-release-notes and https://gradle.org/release-checksums/.
Gradle wrapper scripts and JAR are from the Gradle v9.3.1 tag. Distribution checksum is pinned. CI checks the official wrapper checksum before execution. Retain original notices.

## Windows
Install Android Studio, SDK package `platforms;android-37.0`, build-tools 36.0.0, JDK 17 and Python 3.12. Use a fresh checkout. Do not accept regenerated asset hash differences from other Python/encoder versions. See [host reproducibility evidence](evidence/MID-AUDIT/HOST-REPRO/REPORT.md). Configure JAVA_HOME and ANDROID_HOME or local.properties. Do not commit local.properties.
Run:
```powershell
python tools/check_foundation.py
python -m unittest discover -s tests/unit -p 'test_*.py' -v
python tools/verify_wff.py
.\gradlew.bat :apps:watchface:assembleWff2Debug :apps:watchface:assembleWff3Debug :apps:watchface:assembleWff4Debug :apps:watchface:assembleWff5Debug
python tools/check_apk.py
```
Linux: use ./gradlew with the same tasks. The official validator script verifies a pinned release digest; if Google replaces the asset, stop and review the new release. No unverified fallback.

## Resource-only packaging and verification
Enable R8 code minification for debug and release. Disable resource shrinking to preserve WFF XML and referenced graphics. Samsung's WFF guide documents this configuration: https://developer.samsung.com/sdp/blog/en/2025/08/14/building-a-watch-face-with-watch-face-format. Do not manually modify a signed APK. Historical CI reproduced classes.dex containing five generated R classes. Current R8 removes them.
The official validator must emit an explicit PASSED line for the requested file/version. The script also probes schema-invalid XML in a temporary directory. APK inspection uses Android SDK apkanalyzer to read the compiled manifest and prints each ZIP entry and SHA-256. Install Android command-line tools and place apkanalyzer on PATH if needed.
 
## Select a debug APK
| Variant | Minimum API | Application ID suffix |
|---|---:|---|
| wff2Debug | 34 | .wff2 |
| wff3Debug | 35 | .wff3 |
| wff4Debug | 36 | .wff4 |
| wff5Debug | 37 | .wff5 |
WFF5 is enabled. All four debug APKs passed CI; installation evidence is separate. Current shared WFF XML deliberately uses only baseline constructs. Newer variants do not yet implement exclusive effects. Debug IDs are provisional and allow side-by-side tests. Production package identity, signing and version migration require ADR approval.

Output: apps/watchface/build/outputs/apk/<variant>/debug/. GitHub Actions uploads debug APKs only after validation and build succeed.
Use Android Studio's watch face run configuration or adb -s <verified-device> install -r <apk-path>. Check the actual OS and use a supported profile. Do not activate a face automatically on an unknown device. Select the installed face in the watch face picker. No release signing or Play publication is configured.

## Scope
Bootstrap shows time/date, battery and step/goal in active mode. Ambient hides decoration and shows thin time. Preview is an original approximate bitmap, not a runtime screenshot. Replace it with the actual approved face capture. The shipped Bootstrap resource set does not include health/weather adapters, Reference integration, WFF4 continuity, WFF5-specific effects, Wear Services or Mobile Studio. Independent module and graphics candidates do not change that status. `tools/generate_bootstrap.py` generates the common face and host palette from the token JSON and XML template. It copies the source preview unchanged. Use [ASSET_GENERATION](ASSET_GENERATION.md) for generation and source precedence. Signature basic/material builds are isolated development candidates. Do not replace the common face before the [device and promotion gate](operations/SIGNATURE_DEVICE_GATE.md) is satisfied.

## Asset memory and signature checks
After APK assembly and payload inspection, run `python tools/verify_memory.py`. It downloads Google's Apache-2.0 evaluator with a pinned SHA-256 and uses `--report --apply-v1-offload-limitations` without assuming optional image optimizations. The wrapper enforces the existing 70/7 MiB budgets on exact integer bytes. The evaluator estimates asset memory, not live RAM. CI also runs Android SDK apksigner verify on each debug APK. Historical packaging reproduction uses an isolated checkout, not a change to current minification settings; no historical APK is uploaded.

## Historical WFF2–4 baseline (2026-11-27)
CI 46000111754: all three debug APKs pass schema, package, asset memory (2,371,712 bytes active/ambient), v2 signature checks. Memory evaluator 1.5.1 (b87dde8). Historical CI 46000111676 reproduced classes.dex containing generated R classes. Current R8 configuration resolves the failure. See docs/evidence/GPT-01/REPORT-02.md for hashes and links. Debug certificates are not production signing identities; CI runner keys may differ between runs. Release and update installation are unverified.

## Profile contract
Run `python tools/build_profiles.py assemble` and `python tools/build_profiles.py signatures` after setting up the SDK. Enabled profiles are resolved from compatibility/profiles.json. Official schema checks cover all declared profiles; all four are enabled. The common face is selected unless an explicit src/wffN/res/raw/watchface.xml exists. The APK check compares the packaged raw face against that source. Unsupported source overrides are rejected. API37 migration passed all four APK and CI gates in run 46002470824. Do not enable WFF5 using SDK36.

## Historical API37 migration baseline (WFF2–5)
Use SDK Manager package `platforms;android-37.0`, not `platforms;android-37`. Use `compileSdk = 37` and `targetSdk = 37`. Install build-tools 36.0.0, JDK17. CI 46002470824 verified Gradle9.3.1/AGP9.1.1, all four debug APKs, 40 unit tests, schemas, asset memory and signatures. Artifact 15199096968. The initial CI 46002330942 failed due to the package identifier. This run verifies debug APKs, not device installation or production release. Current evidence is in [STATUS](STATUS.md). The production package ID, license, signing, update and distribution policy remain unapproved under [ADR-007](adr/ADR-007.md) and B-007.

## Bootstrap generation
Run `python tools/generate_bootstrap.py --write` after editing tokens or the XML template. Run `python tools/generate_bootstrap.py --check` to verify deterministic output and SHA-256 manifest (printed to stdout). `assets/source/bootstrap/preview.png` preserves the original preview; it is copied byte for byte. The generated palette SVG is a development reference, not an APK resource. Do not edit generated face, preview or palette directly. See [generation contract](ASSET_GENERATION.md).
