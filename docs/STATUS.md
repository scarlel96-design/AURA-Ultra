# 프로젝트 상태 — 단일 재개 체크포인트

> [!IMPORTANT]
> 매 작업 턴 시작 시 [루트 AGENTS.md](../AGENTS.md)의 PRE-FLIGHT를 먼저 수행한다. 이 문서만 읽고 작업을 시작하지 않는다. 최신 HEAD, 필수 규정, 활성 작업 및 실제 CI 증거를 확인한다.
기준일: 2026-11-27. 이 문서는 매 작업 종료 시 업데이트한다.
현재 목표: GPT 선행 개발 최대화(작업량 추정 목표 65%, 조건부 상한 75%). 최종 프리미엄 품질 유지. Codex 중복 작업 최소화.

| 항목 | 현재 값 |
|---|---|
| 정본 브랜치 | main |
| 확인한 코드 SHA | ef9f9c9bbb2020de835926a3bf0e4262b9c89d51 |
| 활성 GPT 작업 | GPT-01 PARTIAL / 회차 01 CI 성공 |
| 활성 WO | WO-01 PARTIAL; WO-02·04 준비 작업만 일부 구현 |
| 다음 안전한 행동 | GPT-01 회차 02: 이전 실패 APK ZIP 항목 격리 재현 및 공식 Memory Footprint Evaluator 통합·측정 |
| 다음 실행 명세 | operations/GPT-01.md |
| 현재 차단 | B-001 현재 APK PASS, 과거 원인 증거 보완 필요; B-010 RESOLVED |
| 공식 WO GO | 0/38 |
| GPT 묶음 완료 | 0/12 |
| 실제 제품 완성도 | 미확정; 초기 빌드 토대 |
| 출시 판정 | NO-GO |

## 확인된 CI
코드 SHA 544a7010f4bed515d667bfa6a9bbda1389f5bc92, [CI 45997124733](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/45997124733), job 140499204563, 최종 conclusion failure.
- Wrapper SHA-256, 프로젝트 구조, SDK 설치·확인, 공식 WFF validator: PASS.
- Gradle WFF2/3/4 assemble: PASS (BUILD SUCCESSFUL).
- APK 내용 검사: FAIL (WFF2 실행 코드로 분류된 항목 존재; 파일명 및 원인 미확인).
- WFF3/4 개별 APK 내용 검사: NOT RUN (스크립트가 WFF2에서 종료).
- Artifact 업로드: SKIP.
- 메모리, 발광 픽셀, 실기기 렌더링·설치·센서·배터리: NOT RUN.
- 위 결과는 코드 SHA 기준이다. 운영 문서 커밋 후 새 CI가 있으면 실행 결과를 다시 확인한다.

## 추가 CI 재확인
[CI 45998056978](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/45998056978), head SHA 28f51fd89b08cac0e183bbc6c5dfab98dd0f81fa, job 140502353294: 공식 validator 버전별 PASSED #2/#3/#4 및 BUILD SUCCESSFUL 확인. APK 내용 검사 동일 FAIL, Artifact SKIP. 해당 실행은 운영 문서 변경 SHA이며 제품 코드 변경 없음. B-001 미해결.
B-010: verify_wff.py의 VALID 문자열 포함 검사에 오판 위험을 발견했다. 실제 이번 로그에는 명시적 PASSED가 존재한다. 위험을 등록했으며 스크립트는 미수정.

## 재개 절차
AGENTS.md → operations/RESUME_PROTOCOL.md → operations/TASK_RECORD_PROTOCOL.md → operations/VERIFICATION_PROTOCOL.md → operations/GPT_EXECUTION_PLAN.md → operations/BLOCKERS.md → operations/GPT-01.md → 실제 소스/CI.
main의 현재 HEAD를 먼저 확인한다. 확인한 코드 SHA와 최신 문서 SHA를 구분한다. 사용자가 "다음 작업"이라고 하면 재개 절차에 따라 실행한다.

## 남은 사항
실제 Watch7 크기/OS, 신형 기기 사양/설치, WFF5 지원, 정식 패키지/라이선스/서명은 미확정.
고급 소재·모션·8개 테마·외부 데이터·Wear Services·Companion은 아직 미완료. WFF4 Reference와 고급 모션은 PoC 필요.
문서 작업이 제품 기능을 완료한 것으로 계산되지 않는다. 다음 작업의 범위와 증거는 WORK_LOG와 해당 evidence에 추가한다.

## 운영 규정 v1.1
매 작업마다 작업별 영속 기록, G0~G7 검증, 증거 감사 및 별도 재검토를 필수 적용한다. 작업 종료 전 실제 저장소 기록을 확인한다. 이번 변경은 문서만 수정하며 제품 판정을 변경하지 않는다.

## 운영 규정 v1.2 — 매 턴 PRE-FLIGHT
루트 AGENTS.md 최상단의 확인 게이트를 매 작업 턴마다 수행한다. 신규 세션뿐 아니라 동일 대화의 연속 작업에도 적용한다. 제품 코드 변경 없음. GPT-01/B-001/B-010 상태 유지.
문서 기준 SHA 951593e4fbbac33f2c675ea5cbbf07edbe22353d, CI 45998609726 (completed/failure): Official WFF validation: success; Build debug APKs: success; Check APK contents: failure; Upload debug APKs: skipped. https://github.com/scarlel96-design/AURA-Ultra/actions/runs/45998609726. 운영 문서 변경 실행이며 제품 코드 변경 없음. B-001/B-010 해결 증거 없음.

## GPT-01 회차 01 — 구현 및 CI 대기
기준 HEAD 95e51cca23210f930dc3716cb790e791585a7bf0. 이전 CI 45998909046: 공식 WFF #2/#3/#4 PASSED, assemble 성공, APK 검사 실패. Debug/release R8 활성화, resource shrinking 비활성화, 검사 강화 및 회귀 시험 작성. 후보 코드 커밋의 CI 결과는 아직 미확인(PENDING). B-001/B-010은 실제 새 증거 확인 전 OPEN 유지. 상세 기록: evidence/GPT-01/REPORT-01.md.

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

## GPT-01 회차 02 — 검증 후보
공식 메모리 평가 및 debug 서명 검사 CI 추가, 과거 SHA 격리 재현 워크플로 추가. 새 CI 결과 PENDING. 기존 B-001 원인 증거는 재현 로그 확인 전 OPEN. GPT-01 PARTIAL 및 출시 NO-GO 유지. evidence/GPT-01/REPORT-02.md 참조.
