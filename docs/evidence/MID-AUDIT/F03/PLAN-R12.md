# F03 R12 — bounded stable patch and lint coverage
2026-11-28 KST. ChatGPT. PARTIAL / NOT RUN at preparation. R-21/R-22, WO-02, AUD-R04-05 OPEN. main 133e394d18b1c94282ab10045e1973ea3dad1d8b; audit parent 6a651984c3e3377b5cf15baf8d175cf5e26a38d8. GB f8dc433dd93b2c5febd0b6496e1fd729a5e09a26; AG fc98c3ad5993e131f733a9444b5849e737a49086. No owner path change or merge.
PRE-FLIGHT: read AGENTS, STATUS, RESUME, INVARIANTS, TASK_RECORD, VERIFICATION, TEMPLATE, GPT plan, BLOCKERS, WORK_LOG, README, architecture, requirements, quality gates, roadmap, SECURITY, WO-02, findings/remediation, owner map, R11 plan/result, provenance handoff, root/app Gradle settings, wrapper, inventory init, candidate and workflow. Reviewed R11 job 140852386130 raw logs and directly downloaded artifact 15245579935; SHA256 8414d81f759b1e91620dbb38af74e8177fdba254c7e59872107f5bfc197e5c4f, CRC PASS, 12 unique paths, source and commands match. Common Linux job 140852386650 SUCCESS. R11 adverse gate FAIL, not build failure.
## Decision
Official https://developer.android.com/reference/tools/gradle-api and https://developer.android.com/studio/releases/fixed-bugs/studio/2026.2.2 list stable AGP 9.5.3. AGP 9.6 is preview; do not adopt. Keep Gradle 9.6.1 and existing verified pilot wrapper. No forced transitive upgrades. R11 named lint graph 69 modules and named work-action graph 18 modules. Source https://android.googlesource.com/platform/tools/base/+/12bae69b2de87fd281a02de08553c5750c2206d4 describes replacing UTP runner with JUnit launcher; exact release and detached coverage still require evidence. No connected tests, emulator, actual watch, or release adoption.
## Residual advisory patch floors (GitHub Advisory Database, 2026-11-28)
- guava 33.4.0-jre → 33.7.2 (GHSA-xxph-c9ww-hj94).
- commons-lang3 3.16.0 → 3.18.0 (GHSA-j288-q9x7-2f5v).
- httpclient 4.5.6 → 4.5.13 (GHSA-7r82-7xv7-xcpj, 4.x line).
- jose4j 0.9.5 → 0.9.6 (GHSA-3677-xxcr-wjqv).
- bcpkix-jdk18on 1.80.2 → 1.84 (GHSA-wg6q-6289-32hp).
- bcprov-jdk18on 1.80.2 → 1.85 (GHSA-9pwp-9qqc-pr26 critical; GHSA-qp49-qgx5-5m26). Keep BC family aligned if approved later.
- jdom2 2.0.6 → 2.0.6.1 (GHSA-2363-cqg2-863c).
- kotlin-gradle-plugin 2.2.10 → 2.4.20-Beta1 advisory floor; stable 2.4.20 or later requires supported upstream combination (GHSA-r937-wjx7-w2jp).
Advisory URLs use https://github.com/advisories/<ID>. Floors are not approved versions or proof of no other vulnerabilities.
## Implementation and acceptance
Retain R11 evidence by immutable SHA. Change the audit pilot only: stable patch, eight assemble and eight lint tasks, disable configuration/build caches, require nonempty named lint and test-worker graphs. Keep exact metadata/OSV fail-closed checks. Add two focused methods: task matrix and missing/empty coverage. CI existing pinned workflow retrieves original baseline; review exact candidate run and archive. Report observed OSV difference, task exit states and any new IDs. Never infer detached completeness from metadata or named graphs. Device tasks NOT RUN, full provenance, licenses, wrapper regeneration and release SBOM OPEN. Roll back only audit commit if needed. G2-G6 pending; product NO-GO, F03 PARTIAL 13/16, F04 gated, GPT-07 not started, PRs #2/#3 HOLD.
