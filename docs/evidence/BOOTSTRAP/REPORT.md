# Chat-assisted bootstrap
Baseline parent: 6f074fbc86c1382a52bfeac57023c1a3f7a7559e
Scope: resource-only Gradle module, WFF2/3/4 debug variants, shared face, preview, tokens, capability manifest, wrapper, static checks and CI. WFF5 deferred until SDK and schema confirmed. No release or production identity decision.
Gradle wrapper jar copied from official v8.11.1 Git blob; GitHub source/destination blob SHA matched a4b76b9530d66f5e68d973ea569d8e19de379189. CI checks published SHA-256 and distribution checksum. Official validator release digest pinned based on GitHub API metadata.
Validation: connector tree/commit verification to be checked after publication; local Gradle/SDK/ADB unavailable. CI and APK validation results must be retrieved before marking build PASS. Memory evaluator, renderer, all physical watches, power tests and full WFF compatibility NOT RUN.
Decisions: provisional debug namespace, API36 compile/target, flavor application ID suffixes, shared baseline XML, original approximate preview, Java17/AGP8.10.1/Gradle8.11.1. No production signing. No WFF runtime executable code. No wholesale creation of empty modules.

## CI attempt 1
https://github.com/scarlel96-design/AURA-Ultra/actions/runs/45997002132 : wrapper SHA-256 and project invariants PASS. SDK setup FAIL (sdkmanager command not found, exit 127); official schema and APK assembly skipped. Add pinned android-actions/setup-android v4.0.3 and explicit SDK verification. Follow-up run pending; no build success claimed.

## CI attempt 2 (verified)
https://github.com/scarlel96-design/AURA-Ultra/actions/runs/45997124733, job 140499204563, code SHA 544a7010f4bed515d667bfa6a9bbda1389f5bc92. SDK setup/verification, wrapper integrity, project invariants, official WFF validation and WFF2/3/4 assembly PASS. Gradle log: BUILD SUCCESSFUL in 54s. APK contents check FAIL: executable payload in watchface-wff2-debug.apk. The exact entry name and cause were not printed. WFF3/4 contents NOT RUN; upload SKIP. Overall conclusion failure. See operations/BLOCKERS.md B-001 and operations/GPT-01.md for the next diagnostic. Memory/device tests NOT RUN.
