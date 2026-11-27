# GPT-01 / 회차 02 — 과거 실패 재현과 메모리 검증
상태: GO(초기 빌드 토대) / 제품 NO-GO. 2026-11-27. 기준 HEAD 86f9df3f174f2356959ab04ec4ab6fae0379521e, main. GPT.
PRE-FLIGHT: AGENTS, STATUS, README, MASTER_ARCHITECTURE, ROADMAP, REQUIREMENTS, QUALITY_GATES, PERFORMANCE, RESUME_PROTOCOL, PROJECT_INVARIANTS, TASK_RECORD_PROTOCOL, VERIFICATION_PROTOCOL, TASK_REPORT_TEMPLATE, GPT_EXECUTION_PLAN, BLOCKERS, WORK_LOG, GPT-01, WO-01, REPORT-01, BUILD_GUIDE, 실제 workflow/Gradle/check_apk/profiles 확인. 이전 CI 45999371709 성공 재확인. B-001 과거 원인 미확인, B-010 RESOLVED.
범위: R-20/R-22/R-25. 현행 제품 코드/그래픽/패키징 설정 변경 제외. 이전 SHA 95e51cc 격리 checkout; APK 게시 금지. Work 전환 거절; CI 활용.
근거: https://github.com/google/watchface/releases/tag/release (memory-footprint.jar SHA-256 503c5f7bc9209ec4d4d4974f973cf66ad6fbb435e8422c310aac5b820f1f991a, Apache-2.0); https://github.com/google/watchface/blob/main/play-validations/README.md ; ResourceMemoryEvaluator.java, EvaluationSettings.kt, MemoryFootprint.kt 원문 확인. report mode는 제한 적용하지 않으므로 별도 exact bytes 검사. 1 MiB=1048576 bytes. 기존 예산 보존. offload 제한 적용, 추정 최적화 미사용.
| 요구 | 구현 | 시험 |
|---|---|---|
| R-20 | tools/verify_memory.py | 실제 3 APK JSON 평가, 70/7 MiB |
| R-22 | tests/unit/test_memory.py | 경계, 누락, 오류, 초과, 잘못된 데이터 |
| R-25/B-001 | reproduce-packaging.yml | 과거 SHA APK ZIP 항목, dex packages |
| R-22/R-25 | bootstrap.yml | 기존 회귀 및 debug apksigner |
검증: python -m unittest discover -s tests/unit -p 'test_*.py' -v; python tools/verify_memory.py; 기존 전체 CI. 역사적 재현의 실패 검출은 예상 결과로 별도 기록. 서명 검사 debug 한정. Release/실기기/AOD 픽셀/전력 NOT RUN.
G0 문서·이전 CI 확인. G1 후보 작성. G2~G6 새 시험 및 별도 자기 재검토 대기. G7 문서 기록 및 반영 확인 필요. 롤백: 해당 변경만 revert. 다음: 두 CI 로그와 SHA 확인, 메모리 바이트 및 서명 검증, 과거 APK 항목 및 클래스 확인. 기존 게이트 완화 금지.

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
