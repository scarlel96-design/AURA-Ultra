# GPT-02 / 회차 02 — API37 전환 격리 검증
상태: GO (개발 기반) / 제품 NO-GO. 날짜 2026-11-27. 기준 main bfe56169a60eea1a40e71ba6db4a679a6192595b; 검증 브랜치 gpt-02-api37. 작업자 GPT.
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

## 첫 격리 CI 실패와 수정 후보
코드 51b39ab1064b4284e772e4330cd7dee744e7e5d0, [CI 46002330942](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46002330942), job 140516863415: FAILURE. Wrapper digest/구조 및 40 단위 시험 PASS. SDK 설치 실패: Warning: Failed to find package 'platforms;android-37', exit 1. 이후 모든 build/validator/APK/memory/signature 단계 SKIP. 외부 공개 Flutter SDK 지침(https://flutter.googlesource.com/mirrors/flutter/+/refs/heads/fuchsia_f32.1/.agents/skills/updating-android-sdk/SKILL.md)은 API37의 실제 패키지 식별자로 platforms;android-37.0을 명시한다. 설치 경로 및 source.properties 검사 변경. SDK 폴더 강제 이동/복제/비공식 다운로드 금지. compileSdk=37은 공식 Android 17 SDK 안내의 설정을 유지하며 실제 AGP 해석 결과를 확인한다. 새 CI 대기. main 코드 미변경.

## 회차 02 최종 검증 및 판정
검증 코드 SHA f284b1bd69a767ef0f7285449fe7c45f05895e53, 격리 브랜치 gpt-02-api37. [CI 46002470824](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46002470824), job 140517331808, completed/success. 이전 실패 CI 46002330942의 원인은 sdkmanager package identifier 불일치: platforms;android-37 없음. platforms;android-37.0 설치 성공, source.properties Pkg.Revision=2, AndroidVersion.ApiLevel=37.0. compileSdk=37 설정으로 실제 빌드 성공. Gradle 9.3.1, JDK 17.0.21, wrapper checksum PASS. AGP9.1.1 고정. Build Tools 36.0.0 설치/서명 실행 PASS.
- 단위 시험 40 PASS / 0 FAIL (기존 37 + 신규 3). 정상·누락·불일치 raw XML fixture PASS. 공식 WFF Validator #2~#5 명시적 PASSED, invalid XML 예상 실패 검출 4/4 PASS.
- Clean Gradle build SUCCESSFUL in 49s. 네 APK의 minSdk/패키지/WFF 속성/리소스 전용/원본 XML 일치 검사 4/4 PASS. 기존 watchface.xml blob 및 앱 리소스 변경 없음.
- Memory Footprint Evaluator 1.5.1 b87dde8: 네 APK 각각 totalBytes, maxActiveBytes, maxAmbientBytes = 2371712 (약 2.26 MiB). 70/7 MiB 예산 PASS, 이전 자산 추정값과 동일. 실제 기기 RAM/전력 측정 아님.
- apksigner 4/4 Verifies, v2=true, signer count=1. Debug 서명 한정.
| 프로필 | 최소 API | APK SHA-256 (CI 로그) |
|---|---:|---|
| wff2 | 34 | 6be386fc4e2eafec8e49ea72b7f1ad1bcc2a428db1c34e5c4fe164ed8642bde8 |
| wff3 | 35 | 9a15baaf8816d8d4f365b1f9669ee188c0dde024834f9b2df97e722b9084dba0 |
| wff4 | 36 | 7e051ff1bf3ae937c0151ec923eecd7a52f34ca52379c078440928e4542d5756 |
| wff5 | 37 | 361d927a1a3d28917c731097cc44a3b59c468d07e953955b982373793399957f |
Artifact [15199096968](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46002470824/artifacts/15199096968), 79007 bytes, expired=false, expires_at 2027-02-25T12:53:51Z, digest sha256:9906e7c7af9608867c9ba05e3ea6bd5cedc66cb2ea75bf313b935ef7c90229f9. CI 업로드 로그 및 API 메타데이터 대조. 로컬 다운로드/재해시 미실시.
G0 PASS; G1 현재 작업 범위 PASS; G2 40 단위 및 공식 negative probe PASS; G3 격리 최종 코드 전체 CI PASS; G4 4 APK/스키마/메모리/서명 PASS, 실기기·전용 WFF5 기능·실제 flavor override·Release NOT RUN; G5 별도 자기 재검토(원격 diff, wrapper blob/실행 모드, 설정, 앱 리소스 불변 확인), 독립 에이전트 미실시; G6 최종 코드 SHA, 로그, Artifact 일치 PASS; G7 기록 및 main 반영 재확인 대상.
판정: GPT-02 GO (빌드·호환성 개발 기반 범위). WO-01 PARTIAL 및 정식 WO 0/38 유지. GPT 완료 2/12. 출시 NO-GO. B-003의 SDK/빌드 차단 해결; 실제 WFF5 런타임/기기 지원은 B-002/B-004 및 B-003 잔여로 계속 추적. B-007 정식 ID/배포 정책 승인 미실시. 기존 B-001/B-010 재발 없음. SDK37 전환을 main에 fast-forward할 수 있는 근거 확보. 문서만 변경하는 종료 커밋은 [skip ci], 코드 검증은 격리 SHA의 동일한 코드에 대한 증거다.
다음: GPT-03 독립 준비 작업 — 그래픽 자산 및 WFF 생성 자동화. WO-09/10의 선행 PoC는 아직 미충족이므로 공통 토큰/재현 가능한 생성·검증 기반에 한정한다. 프리미엄 소재 품질과 실제 모션을 확정하지 않는다. [GPT-03 명세](../../operations/GPT-03.md).
