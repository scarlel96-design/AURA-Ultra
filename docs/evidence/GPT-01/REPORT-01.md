# GPT-01 / 회차 01 — 패키징 및 검증기 강화
상태: PARTIAL (회차 01 CI 성공) / 제품 NO-GO.
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

## GPT-01 회차 01 — CI 중간 체크포인트
검증 대상 코드 SHA: ef9f9c9bbb2020de835926a3bf0e4262b9c89d51. [CI 45999371709](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/45999371709), job 140506784499, status completed, conclusion success.

| 단계 | 실제 확인 상태 |
|---|---|
| Verify Gradle wrapper | success |
| Check project invariants | success |
| Validation tool regression tests | success |
| Install Android SDK | success |
| Confirm Android SDK tools | success |
| Official WFF validation | success |
| Build debug APKs | success |
| Check APK contents | success |
| Upload debug APKs | success |

새 코드와 변경 파일을 별도 자기 재검토했다. Google watchface의 DWFValidationApplication.java 원문에서 PASSED/FAILED 출력 형식을 확인했다. 현재 CI 실행 결과가 최종 판정되지 않았으면 B-001/B-010의 최종 해결 및 GPT-01 GO를 선언하지 않는다. 기존 APK의 정확한 실패 ZIP 항목은 아직 확보하지 못했다. 메모리 평가, 서명·설치·실기기 시험은 미실시. 다음 턴에는 이 실행의 최종 job/step 로그와 Artifact부터 확인한다. 증거 보존용 문서 커밋은 [skip ci]를 사용하여 진행 중인 코드 검증 실행을 취소하지 않는다. 이는 코드 검사 생략이나 성공 판정이 아니다.

## GPT-01 회차 01 — 최종 확인 결과
검증 코드 SHA: ef9f9c9bbb2020de835926a3bf0e4262b9c89d51. [CI 45999371709](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/45999371709), job 140506784499, conclusion success. 원본 로그와 Artifact API 대조 완료.
- 단위 회귀: 19 PASS / 0 FAIL. 공식 WFF validator: #2/#3/#4 명시적 PASSED. 각 버전의 잘못된 XML도 명시적 FAILED로 검출(3/3 예상 실패 검출 PASS).
- Clean Gradle assemble: 3/3 PASS, BUILD SUCCESSFUL in 54s. APK ZIP 및 컴파일된 Manifest: 3/3 PASS. 실제 파일 목록에서 실행 코드 없음 및 watchface.xml, watch_face_info.xml, preview.png, resources.arsc 보존 확인. hasCode=false, minSdk 34/35/36, WFF 2/3/4 및 package ID 일치.
- Artifact: [aura-bootstrap-debug-apks](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/45999371709/artifacts/15197113871), ID 15197113871, 20943 bytes, 만료일 2027-02-25 UTC, SHA-256 0a935c95824793ff1d69c745e12526501bdc6bc601c9304ceb0d8a38f5a1adc5. API에서 expired=false 확인. Artifact를 로컬 다운로드/재해시하지 않았다.

| APK | SHA-256 (CI 로그) |
|---|---|
| watchface-wff2-debug.apk | da2e9e8b90834a08988a174410f9b446adb28029564fa38995962d09a64c75c8 |
| watchface-wff3-debug.apk | fd47ddf5b8d8ca8ea9d3dd17b2b983d2c6673be910e4bb8d955d121690482e59 |
| watchface-wff4-debug.apk | 4eb47a0738922bfac7a9479a37df96980a7502fd11bdab66918624147ce336b1 |

B-010: RESOLVED. 명시적 대상별 성공, 정상/오류/불명확/버전 불일치 회귀 및 실제 스키마 실패 확인. B-001: 현재 APK 패키징 실패 해소(3/3 PASS 및 Artifact 확보). 과거 실패 APK의 정확한 ZIP 항목/생성 경로는 미확인으로 원래 종료 조건 전부 충족 전까지 OPEN 유지. R8에 의해 생성 코드가 제거된 것으로 추정하나 과거 APK 재현 없이 원인을 확정하지 않는다.
G0 PASS; G1 범위 내 구현 PASS; G2 검증기 회귀 PASS; G3 현재 Debug clean CI PASS; G4 ZIP/manifest/공식 스키마 PASS, 메모리·서명 별도 검사·Release 빌드·실기기 NOT RUN; G5 별도 자기 재검토 수행(독립 리뷰 아님); G6 SHA/CI/Artifact 대조 PASS; G7 문서 갱신 및 원격 반영 확인 필요. 회차 01 빌드/검증 개선 성공, 전체 GPT-01 PARTIAL, WO-01 PARTIAL, 출시 NO-GO. 다음: GPT-01 회차 02에서 기존 실패의 정확한 ZIP 항목을 격리 재현(기존 main 빌드 정책 유지), 공식 Memory Footprint Evaluator 통합/실제 측정 및 남은 필수 검사 검토. 별도 Release 빌드·실기기 시험은 미실시. 이번 문서만 변경하는 증거 커밋은 코드 검증 대상 SHA를 유지하기 위해 [skip ci]로 기록한다.
