# 누적 개발 이력
이 문서는 시간순 append-only 기록이다. 사실 정정은 새 항목으로 추가한다. 현재 상태의 정본은 ../STATUS.md다.

## 2026-11-27 / 설계 기준선
- 커밋 6f074fbc86c1382a52bfeac57023c1a3f7a7559e: 초기 설계 문서 18개, 요구사항 26개, 38 WO 계획, 8개 테마, 15개 PoC.
- 실제 제품 코드 및 실기기 시험 미실시. 원본 심층 연구 보고서는 저장소에 별도 첨부하지 않음.

## 2026-11-27 / Bootstrap
- 커밋 171fca407653001f085683ee30c20608c8336b31: Gradle Wrapper 8.11.1/JDK17/AGP8.10.1/SDK36, WFF2/3/4 flavor, 기본 WFF XML, 임시 프리뷰, 자동 검증.
- CI 45997002132: Wrapper/구조 PASS, sdkmanager 미설치로 FAIL.
- 커밋 544a7010f4bed515d667bfa6a9bbda1389f5bc92: SDK 설치 action 추가.
- CI 45997124733: SDK/공식 WFF validator/Gradle assemble PASS, WFF2 APK 실행 코드 검사 FAIL, Artifact SKIP. WFF3/4 내용은 검사 중단으로 미확인. B-001 등록.
- 메모리, AOD 품질, 실제 워치 실행은 NOT RUN.

## 2026-11-27 / 세션 독립형 운영
- 기준 부모 SHA 544a7010f4bed515d667bfa6a9bbda1389f5bc92. GPT 선행 개발 목표, 작업 큐, 재개 규칙, 차단점·진행률·인계 정책 및 현재 CI 증거 기록.
- 사용자 승인: "다음 작업"으로 현재 상태를 기반으로 다음 작업을 자율 선택·수행.
- 이번 커밋은 운영 문서만 변경. 앱 코드 및 APK 오류 미수정.
- 다음: GPT-01 / B-001의 정확한 APK 항목 확인 및 원인 수정.

## 2026-11-27 / 운영 및 검증 규정 강화
- 기준 부모 SHA 28f51fd89b08cac0e183bbc6c5dfab98dd0f81fa. 기존 AGENTS, 재개 규정, 품질 게이트, 작업 양식 및 체크포인트를 대조 검토했다.
- 작업별 영속 기록, G0~G7 검증, 요구사항 추적표, 검사기 실패 검출, 구현 후 별도 리뷰, 증거 감사, 보고서 양식을 추가했다.
- CI 45998056978 로그에서 공식 validator PASSED #2/#3/#4, Gradle BUILD SUCCESSFUL, APK 검사 FAIL을 확인했다. B-001 유지. 검증 스크립트의 일반 VALID 포함 조건 위험 B-010 등록. 실제 오판은 미재현.
- 변경 범위: 운영 문서. APK 검사와 validator 스크립트는 미수정. 다음 작업은 GPT-01 유지.
- 증거: docs/evidence/OPS-02/REPORT.md. 최종 저장소 반영은 해당 커밋 이력에서 확인한다.

## 2026-11-27 / 매 턴 PRE-FLIGHT 진입 게이트
- 기준 부모 SHA 951593e4fbbac33f2c675ea5cbbf07edbe22353d. 사용자 요청에 따라 루트 AGENTS.md 최상단에 필수 확인 순서 배치. README와 STATUS 상단에서 연결.
- 매 턴 최신 HEAD 및 필수 문서 확인, 활성 작업·실제 소스·CI 대조, 보고서에 PRE-FLIGHT 판정 기록. 동일 대화 및 재시도에도 적용.
- 문서 기준 SHA 951593e4fbbac33f2c675ea5cbbf07edbe22353d, CI 45998609726 (completed/failure): Official WFF validation: success; Build debug APKs: success; Check APK contents: failure; Upload debug APKs: skipped. https://github.com/scarlel96-design/AURA-Ultra/actions/runs/45998609726. 운영 문서 변경 실행이며 제품 코드 변경 없음. B-001/B-010 해결 증거 없음.
- 운영 규정·기록·검증·보고서 양식 동기화. 제품 코드 변경 없음. 다음 GPT-01/B-001/B-010 유지.
- 증거: docs/evidence/OPS-03/REPORT.md. 커밋 후 실제 등록과 링크 확인.

## 2026-11-27 / GPT-01 회차 01 — 초기 패키징 및 검사 강화
- 기준 HEAD 95e51cca23210f930dc3716cb790e791585a7bf0. PRE-FLIGHT: 활성 문서와 요구사항·실제 도구 및 CI 45998909046 확인.
- 삼성 공식 WFF 가이드에 따라 debug/release R8 활성화 및 리소스 축소 비활성화. 이전 APK 항목 미확인으로 원인은 가설 상태.
- WFF 결과 명시적 파일/버전 성공 검증, 실제 invalid XML 검사, 모든 APK ZIP/manifest 검사, 단위 회귀 시험 추가.
- 새 CI 실행 결과 미확인. B-001/B-010 OPEN, GPT-01 NO-GO 유지. evidence/GPT-01/REPORT-01.md 참조.

- 회차 01 코드 SHA ef9f9c9bbb2020de835926a3bf0e4262b9c89d51, CI 45999371709 상태 completed/success 확인. 검증 세부 상태는 STATUS 및 REPORT-01에 저장. 별도 자기 재검토 완료. 제품 GO 미선언. 문서 전용 체크포인트는 실행 중 CI 보존 목적의 [skip ci].

- 최종 CI 45999371709 전체 SUCCESS. 19 단위 시험, WFF2/3/4 정상 및 실패 검출, 3 APK build/내용 검사, Artifact 15197113871 확인. B-010 RESOLVED, B-001 현재 실패 해소(과거 원인 증거 보완 전 OPEN). GPT-01 PARTIAL, WO-01 PARTIAL, 출시 NO-GO. 다음 회차: 과거 실패 격리 재현 및 공식 메모리 평가 통합. 정확한 검증 SHA 및 해시: docs/evidence/GPT-01/REPORT-01.md.

## 2026-11-27 / GPT-01 회차 02
- 기준 HEAD 86f9df3f174f2356959ab04ec4ab6fae0379521e. PRE-FLIGHT 및 이전 CI/Artifact 확인. 공식 memory-footprint release digest, CLI와 소스의 report/byte 단위 확인.
- 기존 70/7 MiB 예산 검증, 실패 검출 단위 시험, debug 서명 검사, 별도 과거 SHA 재현 CI 추가. 제품 XML/Gradle 설정 변경 없음. 새 CI PENDING. REPORT-02 참조.

- 회차 02 코드 98a4f915577cf3175beeca19864a431061673e7b, CI 46000111754 및 46000111676 확인. 원격 소스 자기 재검토 완료. 실제 단계별 상태와 재개 조건은 STATUS 및 REPORT-02에 저장. [skip ci] 문서 체크포인트.

- GPT-01 회차 02 최종: 코드 98a4f915577cf3175beeca19864a431061673e7b, 현행 CI 46000111754 및 과거 재현 CI 46000111676 SUCCESS. 26 PASS/0 FAIL, 메모리 2,371,712 bytes 양 모드 및 3 APK v2 서명 PASS, Artifact 15197747235. 과거 classes.dex/R 클래스 재현으로 B-001 RESOLVED. B-010 RESOLVED 유지. GPT-01 GO(빌드 토대), 1/12 GPT 묶음 완료, WO-01 PARTIAL, 출시 NO-GO. 다음 GPT-02. 증거 REPORT-02.

## 2026-11-27 / GPT-02 회차 01
- 기준 d75c1a51dab60add9b80469d1081f11cf21587e0. PRE-FLIGHT 및 GPT-01 CI 46000111754 success 확인. 공식 모델/SDK 근거, 프로필 공통 계약, 빌드/서명 자동화 및 스키마 검사 개선. WFF5는 API37 전환 이전 disabled 유지. ADR-007 제안. 새 CI PENDING; REPORT-01 참조.

- 회차 01 코드 7820f90cbb35220fe9c6da4f9702374714d143d1, CI 46001149417 in_progress/PENDING. 원격 소스 자기 재검토 수행. 기존 결과 보존, STATUS/REPORT-01에 재개 기록.

- GPT-02 회차 01 최종: 코드 7820f90cbb35220fe9c6da4f9702374714d143d1, CI 46001149417 SUCCESS. 37 PASS/0 FAIL, 공식 WFF2~5 정상 및 invalid XML 검출, WFF2~4 APK build/raw XML/manifest/memory/signature PASS, Artifact 15197783477. WFF5 disabled, GPT-02 PARTIAL. 다음 API37 격리 전환. REPORT-01 참조.

## 2026-11-27 / GPT-02 회차 02
- 기준 bfe56169a60eea1a40e71ba6db4a679a6192595b. PRE-FLIGHT 및 CI 46001149417 확인. 공식 AGP9.1.1 호환 표와 Gradle9.3.1 checksum, 공식 wrapper JAR·스크립트 확인. 격리 브랜치 gpt-02-api37에서 WFF5 포함 4 APK 후보 및 검사기 회귀 작성. CI PENDING. main 유지. REPORT-02 참조.

## 첫 격리 CI 실패와 수정 후보
코드 51b39ab1064b4284e772e4330cd7dee744e7e5d0, [CI 46002330942](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46002330942), job 140516863415: FAILURE. Wrapper digest/구조 및 40 단위 시험 PASS. SDK 설치 실패: Warning: Failed to find package 'platforms;android-37', exit 1. 이후 모든 build/validator/APK/memory/signature 단계 SKIP. 외부 공개 Flutter SDK 지침(https://flutter.googlesource.com/mirrors/flutter/+/refs/heads/fuchsia_f32.1/.agents/skills/updating-android-sdk/SKILL.md)은 API37의 실제 패키지 식별자로 platforms;android-37.0을 명시한다. 설치 경로 및 source.properties 검사 변경. SDK 폴더 강제 이동/복제/비공식 다운로드 금지. compileSdk=37은 공식 Android 17 SDK 안내의 설정을 유지하며 실제 AGP 해석 결과를 확인한다. 새 CI 대기. main 코드 미변경.

- GPT-02 회차 02 최종: f284b1bd69a767ef0f7285449fe7c45f05895e53, CI 46002470824 SUCCESS. 이전 SDK 패키지 실패 해결(android-37.0), Gradle9.3.1/AGP9.1.1/SDK37.0/Build Tools36.0.0. 40 PASS/0 FAIL, WFF2~5 schema 및 invalid 4/4, 4 APK build/raw XML/manifest/memory/signature PASS. Artifact 15199096968. GPT-02 개발 기반 GO, 2/12 GPT 완료, WO-01 PARTIAL, 출시 NO-GO. 다음 GPT-03. 증거 REPORT-02. main 반영은 fast-forward 및 최종 확인 후 판정.

## 2026-11-27 / 외부 에이전트 1차 배정
- 기준 main c1c66b76b7af4a20bb7a08a369fb5962d28b973f 실제 조회 및 활성 GPT-03 확인. GB-01/AG-01 지시서와 소유권 배정표 등록. 사용자 직접 CLI 실행 전 상태 READY. 제품 코드 변경 없음. 기존 GPT/WO/출시 판정 유지. 병행 작업 증거는 독립 보고서로 수신 후 검토한다.

## GPT-03 회차 01 체크포인트
후보 0016b30609da0b7c38c0ea8ee5fe15c12e2d536d, branch gpt-03-generator, CI 46006560829 in_progress/PENDING. 실제 변경 14개, 외부 소유 경로 변경 없음. 원본 XML·preview 보존. 검증 단계별 상태 REPORT-01. main 제품 코드 유지. 다음 실행은 최종 CI 로그 확인 및 안전한 통합. GPT-03 PARTIAL.

## 2026-11-27 — 외부 에이전트 1차 결과 접수 및 총괄 검토
- GB-01: 원격 agent/grok/GB-01 @ d7e60c06c84809676162c37a0f8b19511518f68c, [PR #1](https://github.com/scarlel96-design/AURA-Ultra/pull/1) OPEN, 코드 SHA 098dd35e1d7111a5ece9f8417142cf1c6ecc2fd3. 담당자 GO(독립 모듈). REPORT.md와 domain-test-summary.log의 로컬 70 PASS/0 FAIL 및 host 40 PASS 확인. CI 46009884061 success(job 140542379520)는 기존 WFF 파이프라인이며 Kotlin 시험을 포함하지 않는다. 코드 이후 보고서/로그만 변경. 24개 변경 파일(22 모듈+2 증거), 소유권 위반 0. 총괄 소스 8개 및 build/settings/계약/가정 문서 검토. 독립 Kotlin 재실행 미실시. 통합은 보류.
- GB-01 검토 후속: Validation.kt의 unit 내부 제어문자 및 공백 계약 불일치 가능성, LongBounds.parse의 배타적 인접 정수 범위/Long.MIN_VALUE·MAX_VALUE 극값에서 표현 가능한 정수가 없는 경우를 시험한다. 소스 검토 관찰이며 재현 결과는 아직 없다. classifiedValue는 구조/TTL 전체를 검증하지 않으므로 통합 파이프라인에서 validate/applyRevision/deriveStatus 성공 여부를 명시적으로 확인한다. 독립 clean JDK17 CI 시험, 원본 JUnit XML·환경 증거, 비ASCII Windows 경로 제한, A1~A26 가정 유지. 루트 빌드 통합은 보류.
- AG-01: 사용자 전달 보고서에서 로컬 SHA 0ebe3a8d06f31bcaec959f61832efd864160fd6a, 52/52 스키마 기대 판정, 6/6 격리 APK 검사, 실기기/에뮬레이터 NOT RUN, 담당자 PARTIAL 확인. GitHub branch 목록에 agent/antigravity/AG-01 없음; 해당 SHA 조회 API 422 No commit found. 원문/실제 diff/시험 로그 검증 불가. 푸시 후 총괄 검토. reported 자산 추정치 2371712/2371712 bytes 일반, 2371712/3181712 bytes 자리별 시계; AOD 차이 810000 bytes. 제품 실측이나 원인 확정 근거로 사용하지 않는다. Variant/Reference/Animation/Gyro 발견은 후보로 보존. B-002/003/005 유지.
- GPT-03: 후보 0016b30609da0b7c38c0ea8ee5fe15c12e2d536d, [CI 46006560829](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46006560829) job 140531069930 completed/success. 원본 로그 62 tests OK, 생성·WFF2~5 schema/negative probe 4/4, clean build 59s, 4 APK 검사/메모리/서명 success. 각 active/ambient 2371712 bytes. Artifact 15201877307, 79010 bytes, expired=false, digest sha256:89d966146b9117376ea4c0d831cd0b0b88558de1dba37ea9f07fc8bb91d9d913. API metadata 확인, 재해시 미실시. 후보 아직 main 미병합. 다음: GPT-03 안전한 통합 및 독립 process/write/flavor override 검증. GPT-03 PARTIAL, GPT 완료 2/12, WO GO 0/38, 제품 NO-GO.

## 2026-11-28 — 외부 에이전트 회차 02 검토 (OPS-05)
- GB-01: [PR #1](https://github.com/scarlel96-design/AURA-Ultra/pull/1) OPEN, head 204f561cbe6b7f3910c034998c7d19f10caab886, 검증 코드 46caded706c54f7eb501dd5d8385fc52bca961b1. 원격 REPORT-02, 7개 JUnit XML의 tests/testcase 합계 81, failures/errors/skipped 0 확인. 원본 코드 Validation.kt의 공백·비공백 ISO control 거절, Constraints.kt의 overflow 방지와 빈 정수 범위 판정 확인. 보고된 수정 전 6 FAIL/75 PASS, 수정 후 81 PASS, 기존 40 host. 코드 이후 증거 9개만 추가. PR 전체 34개 파일 소유권 준수. CI 46015880941/46015887551/46016545164/46016552563 기존 bootstrap 성공 확인; Kotlin 미포함. GB01-D2/D3 수정 소스 및 담당자 증거 확인. GB01-E1 비ASCII Windows 경로 미해결; 담당자 argfile 인코딩 실험 보고, ASCII worktree 우회. A27 포함 가정은 미승인. 독립 CI 진행 전 총괄 통합 판정 PARTIAL.
- AG-01: [PR #2](https://github.com/scarlel96-design/AURA-Ultra/pull/2) OPEN, head 74f04aab7abb4e846e3ca5fd798721bd732a1146. 원격 26개 파일 소유권 준수, 원격 접근 차단 해소. schema-matrix-52.log의 52개 구간을 대상 파일/버전과 명시적 PASSED(24)/FAILED+SEVERE(28)로 대조, 불일치 0. isolated-apk-verification.log 6개 APK의 원본 검사 기록 확인; AG 기존 bootstrap CI 46017087843 성공(AG 전용 시험 실행은 아님). ablation log 6개 항목 및 evaluator layer 기록 확인. 일반/4분할/콜론 숨김 2371712 bytes, 가시 PartText 후행 3181712 bytes. 시험 조건에서 4분할 자체 증가 없음; 정적 가시 PartText가 450×450×4=810000 bytes 추가 레이어를 유발. 평가 도구 범위이며 실제 기기 RAM/전력/동작 아님. 원래 얼굴 가독성 유지.
- AG 독립 정적 검토 발견: AG01-AUD-01(P1, 증거 신뢰성) inspect_emulator_environment는 sdkmanager --list 및 avdmanager list device를 실행하지 않고 하드코딩한 카탈로그를 실제 조회 로그처럼 출력한다. 별도 수동 실행 여부 미확인. 실제 stdout/stderr/exit와 파싱, UNKNOWN/NOT RUN 처리 필요. any connected adb device 또는 설치 이미지로 READY 판정하는 로직은 실제 Wear AVD 실행 가능성을 보장하지 않는다. AG01-AUD-02(P2) require_rejection은 임의 nonzero 또는 FAILURE에 의존하며 대상 파일/버전의 명시적 FAILED를 요구하지 않는다. 현재 52개 로그는 올바른 명시적 실패 확인; 장래 검사 오판을 막아야 한다. combined invalid fixture는 첫 duration 오류만으로 통과할 수 있으므로 Reference 부모 위반 별도 fixture 필요. AG01-AUD-03(P3) 보고서 작업일 2026-04-20과 실제 11월 작업 시점 불일치, version-profiles.json(실제 profiles.json), 여유 공간 93.88 vs 로그 93.67 GiB, G6 정의 불일치. --force AVD 및 지정 없는 adb 설치/캡처 명령을 안전한 serial 지정 및 실제 face 선택/상태 확인 절차로 변경한다. memory tool 로그의 SYNC_TO_DEVICE font fallback은 런타임 렌더링 보장 아님. AG PARTIAL 유지; 새 이미지 다운로드·실제 사용자 워치 변경은 승인 전 금지. AG-01-R03 참조.
- 총괄 격리 통합 후보: branch integration/gpt03-gb01 @ c6ae81217641dda75b7b3e3fbc0063fd11469c6c. main b5dd320c0718f9451b9749637c83db22584664b0를 부모로 하고 GPT-03 0016b30609da0b7c38c0ea8ee5fe15c12e2d536d, GB-01 204f561cbe6b7f3910c034998c7d19f10caab886를 추가 부모로 보존. 49개 변경, 제품 apps/watchface 파일 변경 0, AG 소유 경로 변경 0. 기존 main 중앙 기록을 보존했다. 새 독립 JDK17 domain workflow, 81개 baseline JUnit 실제 case/누락/실패/skip/중복 검사, 6개 host fixture, 임시 디렉터리 별도 process --write/--check/missing/stale/repair 및 원본 바이트 검증. [통합 명세](https://github.com/scarlel96-design/AURA-Ultra/blob/c6ae81217641dda75b7b3e3fbc0063fd11469c6c/docs/evidence/OPS-05/INTEGRATION_PLAN.md). 신규 코드 CI 결과와 원본 로그 검토 전 main 병합 금지.
- CI 46056345651, job 140699646086: completed/failure; Set up job: success; Verify Gradle wrapper: success; Reproduce bootstrap assets: success; Independent bootstrap regeneration: success; Check project invariants: success; Validation tool regression tests: success; Install Android SDK: success; Confirm Android SDK tools: success; Official WFF validation: failure; Build debug APKs: skipped; Check APK contents: skipped; Official asset memory evaluation: skipped; Verify debug APK signatures: skipped; Upload debug APKs: skipped; Complete job: success.
- CI 46056345699, job 140699646163: completed/success; Set up job: success; Verify Gradle wrapper: success; Clean Kotlin domain tests: success; Validate JUnit evidence: success; Upload JUnit XML: success; Complete job: success.
- 다음: 통합 후보 두 CI의 실제 로그/Artifact 및 소스 SHA 대조, 필요 시 수정. 실제 flavor override의 별도 통합 재현 및 GPT-03 종료 검증. GB-02는 총괄 CI 및 GB-01 통합 승인 후 착수. AG-01-R03은 독립 작업 가능. GPT 완료 2/12, 정식 WO GO 0/38, 제품 NO-GO. 현행 main 제품 코드 유지.

## OPS-05 독립 CI 최종 및 공식 도구 갱신 후보
- 통합 코드 c6ae81217641dda75b7b3e3fbc0063fd11469c6c: Kotlin CI [46056345699](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46056345699), job 140699646163, SUCCESS. 로그 JDK17 Eclipse Temurin, BUILD SUCCESSFUL in 50s, DOMAIN_RESULT 81 PASS / 0 FAIL / 0 ERROR / 0 SKIP. Artifact [15226378043](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46056345699/artifacts/15226378043), 5180 bytes, digest sha256:a3fec194673e455f63b3a12103ea24c00b20d294ab6a227b6628644d47c5320f, expired=false. 메타데이터 확인, 재다운로드/재해시 미실시. GB-01 독립 CI PASS; main 통합은 아래 공통 게이트 실패로 보류.
- Bootstrap [46056345651](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46056345651), job 140699646086, FAILURE. 독립 프로세스 --write/--check/missing/stale/repair/byte equality PASS, host 68 PASS/0 FAIL, SDK PASS. 공식 validator 단계 'Validator download size or digest mismatch. Review the official release before updating the pin.' exit 1. 이후 schema/build/APK/memory/signature/Artifact SKIP. 실제 스키마 위반으로 판정하지 않는다.
- B-011 OPEN/P0: 공식 Google watchface 가변 release 태그에서 JAR 두 개 교체. 공식 [release](https://github.com/google/watchface/releases/tag/release) ID 460768397 published 2026-11-27T15:21:34Z, tag commit 18d3844de1729f0c5128f59cfa359b0e34b66612. [PR 118](https://github.com/google/watchface/pull/118)의 XML DOM parser 설정 통합 변경 파일 및 핵심 diff 확인. validator asset 800984124 SHA256 6ef308dbc306a9187b5b1f4997a662eb57e26ac3650cebbf2ab583cd38bb609e; memory asset 800984064 SHA256 1ec683365aee86627f0eb502b52fc71f71eff1872776edc5bc6ef7c7b37d28bc. 이전 공식 pin과 다름. 공식 release API 메타데이터를 확인했으며 독립 바이너리/소스 재현은 하지 않았다. 정확한 해시 검증을 유지한 새 pin 후보 0cec62250a2dc05cd02773f6969726867946fe4f를 integration/gpt03-gb01에만 반영. 기존 main과 에이전트 증거의 이전 pin은 보존. 도구 실행 버전, 출력, 정상/실패 schema 및 4 APK/메모리/서명 전체 성공 전 병합 금지.
- 신규 후보 CI: AURA Bootstrap 46056609237 in_progress/PENDING. 최종 원본 로그 미확인. Kotlin 소스는 c6ae812와 동일; 새 SHA에서 도메인 재실행 여부 구분. AG-01-R03은 현재 자기 브랜치의 고정 도구를 사용하며 새 도구 전환은 중앙 승인 이후. B-011 해결은 후보 전체 게이트 및 SHA 대조 후 판정. GPT-03 PARTIAL/GB-01 독립 CI PASS/AG-01 PARTIAL, 정식 WO 0/38, 출시 NO-GO.
