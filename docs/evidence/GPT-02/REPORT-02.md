# GPT-02 / 회차 02 — API37 전환 격리 검증
상태: IN_PROGRESS. 날짜 2026-11-27. 기준 main bfe56169a60eea1a40e71ba6db4a679a6192595b; 검증 브랜치 gpt-02-api37. 작업자 GPT.
PRE-FLIGHT: AGENTS, STATUS, README, MASTER_ARCHITECTURE, REQUIREMENTS, QUALITY_GATES, RESUME_PROTOCOL, PROJECT_INVARIANTS, TASK_RECORD_PROTOCOL, VERIFICATION_PROTOCOL, TASK_REPORT_TEMPLATE, GPT_EXECUTION_PLAN, BLOCKERS, WORK_LOG, GPT-02, WO-01, REPORT-01, COMPATIBILITY, TOOLCHAIN, SOURCES, 실제 Gradle/프로필/CI/검사 코드 확인. CI 46001149417 success 확인. G0 PASS.
범위 R-02/20/22/25: 격리된 API37 도구 전환, WFF5 debug flavor, 기존 2~4 회귀, APK XML 검사 실패 검출. 제품 XML/디자인/정식 배포/서명 정책 변경 제외. B-003 미해결.
근거: https://developer.android.com/build/releases/agp-9-1-0-release-notes ; https://developer.android.com/training/wearables/versions/7/setup ; https://gradle.org/release-checksums/ ; 공식 gradle/gradle v9.3.1 wrapper. JAR git blob 61285a659d17295f1de7c53e24fdf13ad755c379. 공식 wrapper SHA-256 b3a875ddc1f044746e1b1a55f645584505f4a10438c1afea9f15e92a7c42ec13. distribution SHA-256 b266d5ff6b90eada6dc3b20cb090e3731302e553a27c5d3e4df1f0d76beaff06.
| 요구 | 변경 | 검증 |
|---|---|---|
| R-02 | Gradle wrapper, AGP, SDK, wff5 flavor/profiles | SDK 설치 확인, 4 APK clean build |
| R-22 | CI 및 profile tasks | 기존 37 + 신규 3 단위 시험 |
| R-25 | R8/리소스 정책 유지, raw XML 검사 분리 | 일치/누락/불일치 fixture, 4 APK 실물 검사 |
| R-20 | memory tool 유지 | 4 APK 평가 예산 |
명령: python tools/check_foundation.py; python -m unittest discover -s tests/unit -p 'test_*.py' -v; python tools/verify_wff.py; python tools/build_profiles.py assemble; python tools/check_apk.py; python tools/verify_memory.py; python tools/build_profiles.py signatures. CI 결과 PENDING. 기존 main은 유지. 실패 시 원인 기록, 검증 브랜치에서 수정. 모든 필수 검사 성공 및 HEAD 대조 후에만 main fast-forward 검토. G1 후보, G2~G6 대기, G7 기록/반영 확인 예정. 실기기/Release/최종 그래픽 미실시. 제품 NO-GO.
