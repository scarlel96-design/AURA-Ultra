# Chat-assisted bootstrap
Baseline parent: 6f074fbc86c1382a52bfeac57023c1a3f7a7559e
Scope: resource-only Gradle module, WFF2/3/4 debug variants, shared face, preview, tokens, capability manifest, wrapper, static checks and CI. WFF5 deferred until SDK and schema confirmed. No release or production identity decision.
Gradle wrapper jar copied from official v8.11.1 Git blob; GitHub source/destination blob SHA matched a4b76b9530d66f5e68d973ea569d8e19de379189. CI checks published SHA-256 and distribution checksum. Official validator release digest pinned based on GitHub API metadata.
Validation: connector tree/commit verification to be checked after publication; local Gradle/SDK/ADB unavailable. CI and APK validation results must be retrieved before marking build PASS. Memory evaluator, renderer, all physical watches, power tests and full WFF compatibility NOT RUN.
Decisions: provisional debug namespace, API36 compile/target, flavor application ID suffixes, shared baseline XML, original approximate preview, Java17/AGP8.10.1/Gradle8.11.1. No production signing. No WFF runtime executable code. No wholesale creation of empty modules.
