# GPT-01 / 회차 01 — 패키징 및 검증기 강화
상태: IN_PROGRESS / 제품 NO-GO.
일자: 2026-11-27. 기준 HEAD: 95e51cca23210f930dc3716cb790e791585a7bf0. main. 작업자 GPT.
PRE-FLIGHT: PASS (기준 HEAD의 AGENTS, STATUS, README, MASTER_ARCHITECTURE, REQUIREMENTS, QUALITY_GATES, operations/RESUME_PROTOCOL, PROJECT_INVARIANTS, TASK_RECORD_PROTOCOL, VERIFICATION_PROTOCOL, TASK_REPORT_TEMPLATE, GPT_EXECUTION_PLAN, BLOCKERS, WORK_LOG, GPT-01, WO-01, BOOTSTRAP/REPORT, BUILD_GUIDE, 실제 빌드/manifest/검사/CI/profiles 확인). 활성 GPT-01, WO-01 PARTIAL, B-001/B-010.
기준 CI: https://github.com/scarlel96-design/AURA-Ultra/actions/runs/45998909046 (job 140505251267, head 95e51cca23210f930dc3716cb790e791585a7bf0). Validator 명시적 PASSED #2/#3/#4, BUILD SUCCESSFUL in 54s, DEX build/merge 작업 실행, WFF2 APK FAIL. 기존 정확한 ZIP 항목은 기록되지 않았다.
목적/범위: R-02/R-20/R-22/R-25의 초기 패키징 및 검사 신뢰도 개선. 그래픽·기능·권한·서명 정책 변경 제외.
참조(2026-11-27): https://developer.android.com/training/wearables/wff/setup ; https://developer.samsung.com/sdp/blog/en/2025/08/14/building-a-watch-face-with-watch-face-format (debug/release minify, resource shrinking 비활성화). 생성 R 클래스 DEX는 가설, 기존 APK의 실물 증거 미확보. R8 적용 결과로 검증할 예정. Work 환경 전환 미승인. 채팅에서 GitHub CI 활용.

## 변경 및 추적
| 요구/차단점 | 변경 | 검증 |
|---|---|---|
| R-25/B-001 | apps/watchface/build.gradle.kts: R8 코드 축소, 리소스 축소 비활성 | clean 3 APK assemble, ZIP 및 compiled Manifest 검사 |
| R-02/R-25/B-010 | tools/verify_wff.py: 명시적 file/version PASSED, 실패 및 중복 검사 | 정상/헤더/빈/실패/버전/경로 fixture, 공식 invalid XML probe |
| R-22/B-001 | tools/check_apk.py: 모든 프로필, 정확한 ZIP 이름, SHA-256, apkanalyzer manifest | 테스트 fixture 및 실제 APK |
| R-22 | tests/unit/test_validation_tools.py; CI clean build + 회귀 | unittest, official validator, assemble, APK inspection, Artifact |
| R-20 | 메모리 평가 미구현 | GPT-01 후속, NOT RUN |

명령: python -m unittest discover -s tests/unit -p 'test_*.py' -v; python tools/check_foundation.py; python tools/verify_wff.py; ./gradlew --no-daemon --stacktrace clean :apps:watchface:assembleWff2Debug :apps:watchface:assembleWff3Debug :apps:watchface:assembleWff4Debug; python tools/check_apk.py.
예상: 19 단위 시험 PASS, 3개 명시적 정상 및 3개 실패 probe, 3개 APK clean build, 리소스 전용 검사 및 Artifact. 새 실행 결과 PENDING. 실행 전 성공을 선언하지 않는다. 실기기/전력/메모리 NOT RUN.
롤백: 이 후보 커밋 revert; 검증 완화 및 서명 후 APK 변조 금지.
G0 PASS (기준 문서 및 실패 증거 확인), G1 구현 후보, G2/G3/G4 새 실행 대기, G5 별도 자기 재검토 필요, G6 새 CI SHA와 로그 대조 필요, G7 문서 갱신 및 원격 반영 확인 필요.
다음 행동: 최신 후보 코드 SHA의 CI step/원본 로그 확인. 실패하면 구체적 ZIP/manifest/validator 판정으로 원인 분석. 성공 시 Artifact와 시험 증거 확인, 공식 메모리 도구 통합 검토. 기존 차단점 해결 전 GO 금지.
