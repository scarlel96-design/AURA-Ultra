# 프로젝트 상태 — 단일 재개 체크포인트

> [!IMPORTANT]
> 매 작업 턴 시작 시 [루트 AGENTS.md](../AGENTS.md)의 PRE-FLIGHT를 먼저 수행한다. 이 문서만 읽고 작업을 시작하지 않는다. 최신 HEAD, 필수 규정, 활성 작업 및 실제 CI 증거를 확인한다.
기준일: 2026-11-27. 이 문서는 매 작업 종료 시 업데이트한다.
현재 목표: GPT 선행 개발 최대화(작업량 추정 목표 65%, 조건부 상한 75%). 최종 프리미엄 품질 유지. Codex 중복 작업 최소화.

| 항목 | 현재 값 |
|---|---|
| 정본 브랜치 | main |
| 확인한 코드 SHA | f284b1bd69a767ef0f7285449fe7c45f05895e53 |
| 활성 GPT 작업 | GPT-03 PARTIAL / 회차 01 CI 성공, 통합 대기 |
| 활성 WO | WO-01 PARTIAL; WO-02·04 준비 작업만 일부 구현 |
| 다음 안전한 행동 | GPT-03 검증 후보 통합 및 독립 재생성·flavor override 시험; GB-01 보완 및 AG-01 원격 증거 확보 |
| 다음 실행 명세 | operations/GPT-03.md |
| 현재 차단 | B-003 SDK/빌드 해결; B-002/003 런타임/004/007 미해결 |
| 공식 WO GO | 0/38 |
| GPT 묶음 완료 | 2/12 |
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
AGENTS.md → operations/RESUME_PROTOCOL.md → operations/TASK_RECORD_PROTOCOL.md → operations/VERIFICATION_PROTOCOL.md → operations/GPT_EXECUTION_PLAN.md → operations/BLOCKERS.md → STATUS의 활성 작업 명세 → 실제 소스/CI.
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

## 회차 02 — 검증 체크포인트
검증 대상 코드 SHA 98a4f915577cf3175beeca19864a431061673e7b.
- [CI 46000111754](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46000111754), job 140509284826: in_progress/PENDING.
  - Set up job: success
  - Verify Gradle wrapper: success
  - Check project invariants: success
  - Validation tool regression tests: success
  - Install Android SDK: success
  - Confirm Android SDK tools: success
  - Official WFF validation: success
  - Build debug APKs: in_progress
  - Check APK contents: pending
  - Official asset memory evaluation: pending
  - Verify debug APK signatures: pending
  - Upload debug APKs: pending
- [CI 46000111676](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46000111676), job 140509283630: in_progress/PENDING.
  - Set up job: success
  - Verify historical source: success
  - Run android-actions/setup-android@138b5fb1cf087fdb4c5f3c621466fe304d0cf2e3: success
  - Rebuild historical WFF2: in_progress
  - Inspect historical APK (expected prohibited payload): pending
검증 도구 및 workflow의 원격 저장소 원문을 다시 읽고 요구사항과 대조했다(별도 자기 재검토, 독립 에이전트 아님). 기존 제품 XML/Gradle 설정은 유지한다. 과거 실패 재현 workflow는 과거 SHA를 체크아웃하고 금지 항목 확인 시 예상 실패 검출로 처리하며 APK를 게시하지 않는다. 실제 과거 APK 클래스 및 메모리 수치는 최종 로그 확인 전 미확정. 기존 B-001 OPEN, B-010 RESOLVED, GPT-01 PARTIAL 및 출시 NO-GO 유지. 새 CI가 완료되면 원본 로그·측정 수치·서명·Artifact·과거 APK 항목/클래스를 대조하고 다음 상태를 판정한다. 이번 기록은 문서 전용 [skip ci]로 코드 CI를 취소하지 않는다.

## 회차 02 — 최종 결과
검증 코드 SHA: 98a4f915577cf3175beeca19864a431061673e7b. [현행 CI 46000111754](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46000111754), job 140509284826, SUCCESS. [과거 재현 CI 46000111676](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46000111676), job 140509283630, SUCCESS. 두 실행의 원본 로그와 현행 Artifact 메타데이터 확인.
- 전체 단위 시험: 26 PASS / 0 FAIL (기존 19 + 신규 7). 프로젝트 구조, Wrapper, 공식 WFF 검사와 이전 실패 검출, 3개 Debug APK clean build 및 실제 APK 내용 검사 모두 CI PASS.
- Memory Footprint Evaluator 1.5.1, Git hash b87dde8. 고정 JAR SHA-256: 503c5f7bc9209ec4d4d4974f973cf66ad6fbb435e8422c310aac5b820f1f991a. --report 및 --apply-v1-offload-limitations 사용.
- 3개 프로필별 totalBytes, maxActiveBytes, maxAmbientBytes 각각 2,371,712 bytes (약 2.26 MiB), 활성 70 MiB 및 AOD 7 MiB 기준 PASS. 자산 메모리 추정치이며 실제 워치 RAM/배터리/발광 픽셀 측정 아님.

| APK 프로필 | SHA-256 (CI 로그) | 활성/AOD bytes | 서명 |
|---|---|---:|---|
| wff2 | e7d3e9663262cf14de3b085b07160961c491a134de7ea2baacc668a456594901 | 2371712 / 2371712 | PASS |
| wff3 | f16486af6226ee404cb0e56849833c64dc7cad6cd51ab0227234eda3e145bfa9 | 2371712 / 2371712 | PASS |
| wff4 | f6568e7e8fbb16721cf445f8f5dfa0c353f00849ae9dfc9d96847b6c1ed0f636 | 2371712 / 2371712 | PASS |

apksigner: 3/3 Verifies, v2=true, signer count=1; 동일 실행의 인증서 SHA-256 84d43adb36cc3e3c053955d74f74c9de2838f1f404972a4674e81eb4908fb6e2. Debug 서명만 확인. 정식 배포 인증서/CI 간 서명 동일성/설치 업데이트 검증 아님.
Artifact: [15197747235](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46000111754/artifacts/15197747235), 20,939 bytes, expired=false, expires_at 2027-02-25T12:36:54Z, SHA-256 60bd249bdaab275dbdd6e0e94d5b94c0a60302be446502189648622620ea3c30. API 메타데이터 및 업로드 로그 대조. 로컬 다운로드·재해시 미실시.

### B-001 원인 재현
과거 95e51cca23210f930dc3716cb790e791585a7bf0을 별도 job에서 checkout하고 clean WFF2 build. 역사적 APK SHA-256 92d7d6be103b730b705c83516d8f449726fcd3eb97cb541547bf73f296483ef5. ZIP 금지 항목 정확히 ['classes.dex']. apkanalyzer dex packages --defined-only 결과 io.github.scarlel96.aura.watchface.R, R$drawable, R$raw, R$string, R$xml (5개 정의 클래스). AGP 자동 생성 R 클래스의 DEX 패키징 원인 재현. 현행 R8 적용 빌드는 실행 코드 없음과 필수 자산 보존 검사 PASS. 과거 파일의 원본과 동일 바이트임을 주장하지 않는다. 과거 APK는 업로드하지 않음. B-001 RESOLVED, B-010 RESOLVED 유지.

### 최종 판정 및 검토
G0 PASS, G1 PASS(작업 범위), G2 PASS(26 단위 시험 및 기존 공식 스키마 실패 검출), G3 PASS(현행 전체 CI 및 격리 재현), G4 PASS(작업 범위의 메모리 추정/Debug APK/서명/스키마), G5 별도 자기 재검토 수행(독립 에이전트 아님), G6 PASS(코드 SHA·원본 로그·Artifact 메타데이터 일치), G7 문서 기록 및 원격 반영 확인 대상. 실기기, 실제 메모리/발광 픽셀/전력, Release 및 설치·업데이트는 NOT RUN; 후속 WO에서 수행. GPT-01 GO(초기 빌드 토대), WO-01 PARTIAL, 정식 WO GO 0/38, GPT 묶음 1/12, 출시 NO-GO. 다음 GPT-02(준비 작업): 공식 플랫폼/기기/SDK/API 및 패키지 정책 확정, 다중 WFF 기반 개선. WFF5 및 기기 지원은 증거 확보 전 미확정. 별도 실행 명세 docs/operations/GPT-02.md 참조. 문서만 변경하므로 [skip ci] 적용.

## GPT-02 회차 01 후보
공식 Watch7/8/9/Ultra2 화면 사양, Wear OS 7/API37, AGP9.1.1 호환성 확인. profile contract, flavor source resolution, dynamic build/signature, APK raw XML 대조 및 WFF5 schema-only probe 추가. WFF5 APK 비활성 유지. 새 CI PENDING. 상세 [REPORT-01](evidence/GPT-02/REPORT-01.md). GPT-02 PARTIAL/제품 NO-GO.

## 회차 01 CI 체크포인트
검증 코드 SHA 7820f90cbb35220fe9c6da4f9702374714d143d1, [CI 46001149417](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46001149417), job 140512806931: in_progress/PENDING.
- Set up job: success
- Verify Gradle wrapper: success
- Check project invariants: success
- Validation tool regression tests: success
- Install Android SDK: success
- Confirm Android SDK tools: success
- Official WFF validation: success
- Build debug APKs: in_progress
- Check APK contents: pending
- Official asset memory evaluation: pending
- Verify debug APK signatures: pending
- Upload debug APKs: pending
원격 변경 코드 원문을 별도 자기 재검토했다. 프로필 계약의 2~4 필수 활성 및 5 선언, 공통/override 선택, Gradle matrix·minSDK 검증, APK raw XML 대조, 기존 메모리·서명 검사 보존 확인. 실제 flavor override는 합성 단위 시험만 적용하며 실제 flavor 전용 XML 빌드는 후속 PoC 대상. WFF5가 disabled 상태이면 schema 검사만 수행한다. 스키마 PASS는 기기 호환성 증거가 아니다. CI 전체 종료 및 원본 로그/Artifact 확인 전 G3/G4/G6 최종 판정 보류. WO-01/GPT-02 PARTIAL 유지. 다음 작업: CI 원본 로그와 37 단위 시험/4개 schema verdict/3 APK raw XML·메모리·서명 검사 확인. 이후 API37/AGP9.1.1 전환은 격리 검증. 문서 전용 [skip ci]로 기존 CI 실행 보존.

## 회차 01 최종 증거
검증 코드 SHA 7820f90cbb35220fe9c6da4f9702374714d143d1. [CI 46001149417](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46001149417), job 140512806931, completed/success. 원본 로그 확인.
- 단위 시험 37 PASS / 0 FAIL (기존 26 + 신규 11). Wrapper 및 구조 검사 PASS.
- Validator 1.7.0: 공통 XML에 대해 WFF #2/#3/#4/#5 명시적 PASSED, 잘못된 XML 예상 실패 검출 4/4 PASS. #5는 schema-only, disabled. 별도 WFF5 기능 구현/빌드/설치 아님.
- 동적 프로필 clean build: WFF2/3/4 PASS, BUILD SUCCESSFUL in 41s. 실제 APK raw XML과 선택 원본 일치, resource-only/Manifest 검사 3/3 PASS. 메모리 및 debug signature 3/3 PASS.
| 프로필 | APK SHA-256 (CI) | active/ambient bytes |
|---|---|---:|
| wff2 | 708f01cffb6fdaa24f799156bf069b39dccd0417f12081ba1fd4d334ae9fb759 | 2371712/2371712 |
| wff3 | f4e7b8777b60d5d41b1710d5330fcb2520f24cfee5ab937d6cdb73c2f4f4d327 | 2371712/2371712 |
| wff4 | 4a9ab88b530977433f94d8f4fc006486009239ac6ff2fdb36826a26cc82b2aac | 2371712/2371712 |
Artifact [15197783477](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46001149417/artifacts/15197783477), 20948 bytes, expired=false, expires_at 2027-02-25T12:44:18Z, digest sha256:7ae4762c4484d735aac159d7fcf4a2612175f3012f1f12c35c529c08ded67c15. 업로드 로그/API 메타데이터 확인; 다운로드/재해시 미실시.
G0 PASS; G1 현재 회차 범위 PASS; G2 단위 fixture 및 실제 validator 실패 검출 PASS; G3 전체 CI PASS; G4 현재 3 APK 및 #5 스키마 PASS, 실제 WFF5/기기/전용 overlay 빌드 NOT RUN; G5 원격 코드 자기 재검토 수행, 독립 리뷰 미실시; G6 코드 SHA·CI·Artifact 메타데이터 대조 PASS; G7 원격 등록 및 문서 링크 검사(변경 전 기록 커밋 7f77441 기준 0 오류), 최종 문서 반영 재확인 필요.
발견/한계: WFF5 신규 flavor 활성화 때 test_build_tasks 기대 목록과 SDK/build-tools 경로를 함께 갱신한다. 실제 flavor override는 합성 단위 시험만 수행. 신규 APK raw XML 대조는 실제 정상 3종에 적용; 오류 주입 검사는 후속 회차에 추가. B-003은 SDK37/AGP9 전환 및 실제 빌드/설치 필요; B-004는 실제 기기/Ultra2025 출고 OS 미확정; B-007 정식 정책 제안, 승인 필요. B-002 유지. GPT-02 PARTIAL, WO-01 PARTIAL, GPT 완료 1/12, WO GO 0/38, 제품 NO-GO.
다음 회차: 별도 브랜치 또는 격리 CI에서 AGP9.1.1 + Gradle9.3.1 + SDK37 + build-tools36.0.0의 공식 배포 및 checksum 확인, WFF5 활성화 후보 작성. 기존 2~4 및 5 전체 정상/실패 스키마·clean build·raw APK·memory·signature 회귀 성공 후에만 main 변경 고려. 실기기 지원은 별도 시험. 이번 증거 커밋은 문서 전용 [skip ci].

## GPT-02 회차 02 후보
기준 main bfe56169a60eea1a40e71ba6db4a679a6192595b, 격리 브랜치 gpt-02-api37. AGP9.1.1/Gradle9.3.1/SDK37/build-tools36.0.0, WFF5 flavor 활성화 후보, APK XML 오류 주입 시험 추가. 4개 APK 및 전체 회귀 CI PENDING. main 반영 전 실제 결과 확인. 기기·출시 미검증. [REPORT-02](evidence/GPT-02/REPORT-02.md).

## GPT-02 회차 02 종료

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
다음: GPT-03 독립 준비 작업 — 그래픽 자산 및 WFF 생성 자동화. WO-09/10의 선행 PoC는 아직 미충족이므로 공통 토큰/재현 가능한 생성·검증 기반에 한정한다. 프리미엄 소재 품질과 실제 모션을 확정하지 않는다. [GPT-03 명세](operations/GPT-03.md).

## 외부 에이전트 1차 병행 준비
[배정표](operations/agent-orders/README.md), [GB-01](operations/agent-orders/GB-01.md), [AG-01](operations/agent-orders/AG-01.md) 등록. Grok Build 순수 Kotlin 도메인 계약, Antigravity CLI WFF4/5 PoC. 상태 READY(실행 미확인), 별도 브랜치 및 파일 소유권. GPT-03 활성 유지, 중앙 문서는 총괄 담당자만 갱신한다. 제품 코드/판정 변경 없음.


## 회차 01 확인된 중간 증거
후보 SHA 0016b30609da0b7c38c0ea8ee5fe15c12e2d536d, branch gpt-03-generator, [CI 46006560829](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46006560829), job 140531069930, in_progress/PENDING.
- Set up job: success
- Verify Gradle wrapper: success
- Reproduce bootstrap assets: success
- Check project invariants: success
- Validation tool regression tests: success
- Install Android SDK: success
- Confirm Android SDK tools: success
- Official WFF validation: success
- Build debug APKs: in_progress
- Check APK contents: pending
- Official asset memory evaluation: pending
- Verify debug APK signatures: pending
- Upload debug APKs: pending
원격 diff 별도 자기 재검토: 제품 앱 리소스 변경 없음; source/packaged preview Git blob 동일 d073ea432797ca9e83a8ea2654de3c9f6440f41b; 외부 에이전트 소유 파일 변경 0; 후보 주요 문서 상대 링크 오류 0. 신규 시험 코드 22개 확인, 실제 총 시험 개수 및 SHA-256 manifest는 최종 원본 로그 확인 후 기록한다. 생성기는 같은 프로세스에서 재실행하며 독립 프로세스 재현 및 --write 실사용 시험은 후속. PNG 원본 복사 및 header 검사만 적용. 실제 렌더링/고급 소재/실기기 미실시. G0/G1 범위 확인, G2/G3/G4/G6 최종 CI 로그 대기, G5 자기 재검토 완료(독립 리뷰 아님), G7 main 문서 체크포인트 등록 대상. GPT-03 PARTIAL, WO 및 출시 판정 유지. main은 기존 코드 유지. 다음: CI 46006560829 최종 결과 및 원본 로그·Artifact 확인, 이후 후보의 안전한 병합 및 실제 flavor override 격리 시험. 중앙 문서의 병행 변경을 보존하며 통합한다. [skip ci]는 문서 전용 체크포인트에만 적용.

## 2026-11-27 — 외부 에이전트 1차 결과 접수 및 총괄 검토
- GB-01: 원격 agent/grok/GB-01 @ d7e60c06c84809676162c37a0f8b19511518f68c, [PR #1](https://github.com/scarlel96-design/AURA-Ultra/pull/1) OPEN, 코드 SHA 098dd35e1d7111a5ece9f8417142cf1c6ecc2fd3. 담당자 GO(독립 모듈). REPORT.md와 domain-test-summary.log의 로컬 70 PASS/0 FAIL 및 host 40 PASS 확인. CI 46009884061 success(job 140542379520)는 기존 WFF 파이프라인이며 Kotlin 시험을 포함하지 않는다. 코드 이후 보고서/로그만 변경. 24개 변경 파일(22 모듈+2 증거), 소유권 위반 0. 총괄 소스 8개 및 build/settings/계약/가정 문서 검토. 독립 Kotlin 재실행 미실시. 통합은 보류.
- GB-01 검토 후속: Validation.kt의 unit 내부 제어문자 및 공백 계약 불일치 가능성, LongBounds.parse의 배타적 인접 정수 범위/Long.MIN_VALUE·MAX_VALUE 극값에서 표현 가능한 정수가 없는 경우를 시험한다. 소스 검토 관찰이며 재현 결과는 아직 없다. classifiedValue는 구조/TTL 전체를 검증하지 않으므로 통합 파이프라인에서 validate/applyRevision/deriveStatus 성공 여부를 명시적으로 확인한다. 독립 clean JDK17 CI 시험, 원본 JUnit XML·환경 증거, 비ASCII Windows 경로 제한, A1~A26 가정 유지. 루트 빌드 통합은 보류.
- AG-01: 사용자 전달 보고서에서 로컬 SHA 0ebe3a8d06f31bcaec959f61832efd864160fd6a, 52/52 스키마 기대 판정, 6/6 격리 APK 검사, 실기기/에뮬레이터 NOT RUN, 담당자 PARTIAL 확인. GitHub branch 목록에 agent/antigravity/AG-01 없음; 해당 SHA 조회 API 422 No commit found. 원문/실제 diff/시험 로그 검증 불가. 푸시 후 총괄 검토. reported 자산 추정치 2371712/2371712 bytes 일반, 2371712/3181712 bytes 자리별 시계; AOD 차이 810000 bytes. 제품 실측이나 원인 확정 근거로 사용하지 않는다. Variant/Reference/Animation/Gyro 발견은 후보로 보존. B-002/003/005 유지.
- GPT-03: 후보 0016b30609da0b7c38c0ea8ee5fe15c12e2d536d, [CI 46006560829](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46006560829) job 140531069930 completed/success. 원본 로그 62 tests OK, 생성·WFF2~5 schema/negative probe 4/4, clean build 59s, 4 APK 검사/메모리/서명 success. 각 active/ambient 2371712 bytes. Artifact 15201877307, 79010 bytes, expired=false, digest sha256:89d966146b9117376ea4c0d831cd0b0b88558de1dba37ea9f07fc8bb91d9d913. API metadata 확인, 재해시 미실시. 후보 아직 main 미병합. 다음: GPT-03 안전한 통합 및 독립 process/write/flavor override 검증. GPT-03 PARTIAL, GPT 완료 2/12, WO GO 0/38, 제품 NO-GO.
