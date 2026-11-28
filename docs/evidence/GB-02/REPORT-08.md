# GB-02 G01 / R08 보호 계약 최종 보완

상태: G01 독립 모듈 통합 후보의 종료 회차. 제품 출시 NO-GO. PR #3은 병합하지 않는다. HOLD를 유지한다. R09, GB-03, GPT-07은 시작하지 않는다.

일자: 2026-11-28. 작업자: Grok Build. 검토자: 없음. G5는 자기 재검토다.

기준 브랜치: `agent/grok/GB-02`. 기준 구현: `aacc744ef5844632c8b7ac588532fcf6441e8f88`. 이번 구현 SHA: `671e999d668811ee402042e692bda7293bba24d2`. CI head: `1f6d9605b59670a3489a0a76746c857e7fc7cf99`. 증거 커밋 SHA는 이 문서를 담은 커밋을 기록 커밋에서 가리킨다. 기록 커밋은 `[skip ci]`이고 `modules/intelligence`를 바꾸지 않는다. 확인은 `git diff 671e999d668811ee402042e692bda7293bba24d2 -- modules/intelligence`가 비어 있는지로 한다.

PRE-FLIGHT: PASS. 작업 시작 HEAD는 `2389ea1a3e857515cf312938cafc9c45def35e9f`다. `origin/main`은 `c8541f504b2417f5680c5358f476f1ba3383ccdd`였고 차이는 중앙 문서와 R08 지시서뿐이라 병합 `8df2ac8`로만 반영했다. 푸시 직전 `origin/main`은 `9eb0c86`이고 F03 R11 문서뿐이라 병합 `1f6d9605b59670a3489a0a76746c857e7fc7cf99`로만 반영했다. `modules/intelligence`, `modules/domain`, `.github`, `tools`, Gradle과 겹치지 않았다. 들어온 파일은 수정하지 않았다. 같은 기준에서 `AGENTS.md`, `docs/STATUS.md`, `RESUME_PROTOCOL.md`, `PROJECT_INVARIANTS.md`, `TASK_RECORD_PROTOCOL.md`, `VERIFICATION_PROTOCOL.md`, `TASK_REPORT_TEMPLATE.md`, `GPT_EXECUTION_PLAN.md`, `BLOCKERS.md`, `WORK_LOG.md`, `GB-02-G01-R08.md`, R07 계약·가정·빌드 문서와 `Machine.kt`를 읽었다. PR #3은 OPEN이고 HEAD는 푸시 전 `2389ea1`이었다. 현재 STATUS의 다음 행동은 F03 R11 이후의 공급망 검토와 GPT-07 승인 대기다. 그 문장을 바꾸지 않는다.

작업 목표: R07 독립 검토가 남긴 보호 전달 상한, 소비자 3축, 잘못된 정책의 TTL·권한, 관측 순서, 예보·재동기화 경계를 수정 전 재현한 뒤 확인된 결함만 고친다. 기존 93개 intelligence 시험, 81개 domain 시험, 시드 `20261128`의 100000회 전이, JUnit 부정 7종, 권한/TTL 분리는 유지한다.

## 구현 및 결정

| 파일 | 변경 | 요구사항 |
|---|---|---|
| `Machine.kt` | 같은 epoch의 전달 순서는 감싸지 않는다. 상한에서는 보호를 켜는 변경만 남긴다. `openDeliverySession`만 epoch를 1 올린다. epoch 상한은 열지 않는다. 음수 순서는 1이고 세션을 열지 않는다. | P1 전달 상한 |
| `Round07Test.ProtectionConsumer` | AOD, 모션 감소, 그래픽 전력 제한을 따로 기록한다. 이전 epoch와 음수 순서는 버린다. 세션이 열린 더 큰 epoch만 해제를 포함한 새 워터마크다. | P1 소비자 |
| `Machine.kt` | 잘못된 정책은 새 숫자를 받지 않는다. 시계가 역전되지 않았고 보관 TTL이 지났거나 `DENIED`/`ERROR`/`UNAVAILABLE`이면 공개 숫자를 null로 거둔다. `deliveredIntent()`는 null이고 `issues`는 유지한다. | P1 정책 TTL |
| `Machine.kt` | `DENIED`/`ERROR`/`UNAVAILABLE`은 철회 커서를 남긴다. 그 시각보다 이른 배터리·강수는 다시 공개하지 않는다. 충전·경보·활동·조도·연결·사용자 모드도 더 이른 관측과 예보로 축을 바꾸지 않는다. | P2 관측 순서 |
| `Machine.kt` | 배터리 예보는 숫자·전원·그래픽을 바꾸지 않는다. 강수 예보는 커서가 없을 때만 숫자를 공개하고 날씨 축은 바꾸지 않는다. 상한 `resync`는 검증을 통과한 새 관측만 받는다. 미래 관측은 상한에서도 이전 숫자를 지우지 않는다. | P2 예보·재동기화 |

결정: 단순 overflow와 양쪽 워터마크를 0으로 되돌리는 재시작은 쓰지 않는다. 15/20, 70/50, 60초는 제품 상수로 올리지 않는다. 도메인 `Observation`에는 revision이 없다. 다른 축의 revision과 `applyRevision` 변경은 D01 제안만 남긴다. 보호 계약은 합의 전 후보다. Wear Services와 WFF는 연결하지 않는다. 순서 필드를 넘기지 않는 호출은 회차 05 호출 순서 계약을 유지한다.

한계: epoch가 `Long.MAX_VALUE`이면 새 세션을 열 수 없고 감싸지 않는다. 그 epoch의 순서 상한에서는 보호를 켜기만 한다. 시험 `ceilingRaiseSurvivesSaturatedUnprotectAndOldSessionRelease`가 이 한계를 고정한다.

## 요구사항 추적

| ID | 시험 | 수정 전 | 수정 후 | 판정 |
|---|---|---|---|---|
| P1 전달 상한 | `ceilingRaiseSurvivesSaturatedUnprotectAndOldSessionRelease`, `duplicateReverseNegativeAndSameTickStayOrdered` | 상한의 비보호 다음 신규 보호가 누락 | 세 보호가 강화로 적용. 이전 세션 해제는 무시. 새 세션의 더 큰 순서는 해제. 음수·역순·같은 tick·epoch 상한은 감싸지 않음 | PASS. epoch 상한은 위 한계 |
| P1 소비자 | 같은 두 메서드의 `ProtectionConsumer` | 모션 감소만 추적 | AOD·모션·그래픽을 독립 적용·유지·해제 | PASS |
| P1 정책 TTL | `rejectedPolicyWithdrawsExpiredAndRevokedNumbers` | 만료 10%가 `failSafe`에 남음 | 만료·DENIED·ERROR·UNAVAILABLE은 null. 미만료 10%는 유지. 반복 거절 후 정상 정책은 10%와 AOD·모션·그래픽을 다시 받는다. 시계 역전의 철회는 80%를 유지 | PASS |
| P2 관측 순서 | `denialThenMidpointAndOtherStreamsDoNotRepublish` | t20 철회 뒤 t15가 10을 공개 | t15는 null과 `SUPERSEDED_OBSERVATION`. t22는 수신. A→B→A의 이른 A는 거절. 강수 철회가 배터리 70을 막지 않음 | PASS |
| P2 예보·축 | `forecastAndOlderAxesDoNotRewriteState` | 늦은 충전 거짓이 `CHARGING`을 끔. 충전 예보가 `CHARGING` | 이른 관측과 예보는 충전·경보·활동·조도·연결·사용자 모드를 유지. 배터리 예보는 null이고 그래픽을 켜지 않음. 강수 예보 90은 숫자만 공개하고 날씨 축은 `NORMAL` | PASS |
| P2 resync | `ceilingResyncDoesNotBypassValidation` | 예보 resync가 만료 시각을 90까지 늘려 30초에도 80이 남음 | 예보·이른 값·철회·미래·역전은 80을 바꾸거나 TTL을 늘리지 않음. 30초에 배터리와 강수가 함께 null. 생략 resync는 0이 아님 | PASS |
| 후보 15/20 | 기존 `chargingAndLowWaitKeepGraphicsInsideTheCandidateBand` | 유지 | 임계값을 바꾸지 않음 | PASS. 제품 승격은 PARTIAL |
| AUD-R03-01 | `PROTECTION_DELIVERY_CONTRACT.md` | 상한에서 신규 보호 누락 | 후보 표를 3축·세션·상한 강화로 고침. 런타임은 C01 | PARTIAL. 합의 전 |
| D01 | 없음 | 도메인 revision 없음 | 로컬 커서만 사용. `applyRevision`을 호출하지 않음 | PARTIAL |
| 회귀 | 기존 93, domain 81, `longRunKeepsInvariants`, JUnit 7종 | 유지 대상 | 99 PASS, 81 PASS, 100000회 1메서드 PASS | PASS |

수정 전 재현은 `Round08ReproTest` 6개이고 6개가 실패했다. 그 클래스는 스위트에 남지 않는다. 실패 메서드는 `saturatedCeilingDropsANewProtectionRequest`, `rejectedPolicyKeepsExpiredAndRevokedNumbers`, `denialThenMidpointObservationRepublishes`, `lateChargingAndForecastChangeRealState`, `forecastChangesBatteryChargingAndGraphics`, `resyncForecastExtendsCeilingTtl`이다. 신규 영구 메서드는 `Round08Test` 6개다. 99는 93에 6을 더한 수량이다. 100000회는 `Round05Test.longRunKeepsInvariants` 1개 메서드다. JUnit 부정 7종은 `rejectsEmptyMethod`, `rejectsMissingCounters`, `rejectsMissingClassname`, `rejectsUnrelatedClassname`, `rejectsSuiteFilenameMismatch`, `rejectsNestedTestcase`, `rejectsFutureTimestamp`다. 이 7개는 `JunitXmlCheckTest` 20개 안에 있고 별도 파일이 아니다.

## 정책 후보와 미확정

| 항목 | 이 회차 | 승인 전 상태 |
|---|---|---|
| 그래픽 15/20, 강수 70/50, 유지 60초 | 값을 바꾸지 않음 | 실측 전 제품 상수 아님 |
| 미래 시각 허용 | 0. 같은 시각만 허용 | 출처별 합의 없음 |
| 도메인 스트림 revision | 구현하지 않음 | D01 |
| 보호 전달 | 후보. 세션은 `openDeliverySession` | 총괄 합의 전. C01 NOT RUN |
| epoch 상한 | 감싸지 않음. 새 세션을 열 수 없음 | 기록된 한계. 실사용 도달은 NOT RUN |

## 검증 결과

| 시험 | 명령 | 결과 | 판정 | 로그 |
|---|---|---|---|---|
| 수정 전 재현 | intelligence `Round08ReproTest` | 6 completed, 6 failed | PASS, 재현 | [intelligence-repro-r08.log](intelligence-repro-r08.log) |
| intelligence clean JDK 17 | `gradlew -p modules/intelligence clean test --no-daemon --offline --no-build-cache` | 99 PASS, 0 FAIL, 0 ERROR, 0 SKIP. XML 12파일. BUILD SUCCESSFUL in 44s | PASS | [intelligence-test-summary-r08.log](intelligence-test-summary-r08.log), [junit-r08](junit-r08) |
| domain 회귀 | `gradlew -p modules/domain clean test --no-daemon --offline --no-build-cache` | 81 PASS, 0 FAIL, 0 ERROR, 0 SKIP. XML 7파일. BUILD SUCCESSFUL in 31s | PASS | [domain-regression-r08.log](domain-regression-r08.log), [junit-r08-domain](junit-r08-domain) |
| 장시간 전이 | 위 스위트의 `longRunKeepsInvariants` | PASSED. 시드 20261128, 한 메서드 안 100000회 | PASS | 같은 intelligence 로그 |
| JUnit 창 | `check_junit_xml.py` | `OK files=12 tests=99`, `OK files=7 tests=81` | PASS | 아래 시각 |
| 호스트 | `python -m unittest discover -s tests/unit -p test_*.py` | 370 ran, 368 PASS, 1 FAIL, 1 ERROR, 0 SKIP, 65.637s | 환경 | [host-unit-r08.log](host-unit-r08.log) |
| 문서 예산 | `python tools/check_doc_budget.py` | exit 0. STATUS 7382/8192, WORK_LOG 9475/10240, BLOCKERS 5652/8192 | PASS | 이 표 |
| 실기기, 공급원, WFF, intelligence 모듈 CI | 미실행 | NOT RUN | NOT RUN | 없음 |

환경: Windows. ASCII worktree `C:\Users\scarl\AppData\Local\Temp\aura-gb02-wt`. 테스트 JVM Eclipse Temurin 17, `C:\Users\scarl\.jdks\temurin-17`. Gradle 9.3.1. Kotlin 2.4.21. Python 3.14.7. Intelligence XML `2026-11-28T03:53:52.029Z`부터 `2026-11-28T03:53:56.528Z`. Domain XML `2026-11-28T03:54:41.509Z`부터 `2026-11-28T03:54:41.895Z`. 시각은 UTC다. 검사기 비교는 그 끝점을 포함한다. `--offline`을 사용했다.

호스트 1 ERROR는 `test_bootstrap_generator.GeneratorTests.test_checked_in_outputs`의 `assets/generated/bootstrap/palette.svg` stale이다. 1 FAIL은 `test_f01_r01.F01SignatureTests.test_normal_artifact_preserved`의 PNG 다이제스트다. 둘 다 Python 3.14.7 로컬 결과이고 GPT 담당이다. 원본과 `tools/`는 수정하지 않았다.

공통 Bootstrap 성공은 intelligence 시험 성공이 아니다. intelligence 모듈 CI는 `CI_PROPOSAL.md`에만 있고 적용하지 않았다. 기대 수량은 12파일 99시험, domain 7파일 81시험이다.

## CI

CI head: `1f6d9605b59670a3489a0a76746c857e7fc7cf99`. 구현 `671e999d668811ee402042e692bda7293bba24d2` 뒤의 문서 병합이며 `modules/intelligence` diff는 비어 있다. 적용 대상은 Bootstrap, 문서 예산, Windows 재현의 push와 pull_request다. 재확인한 job conclusion은 success이고 step conclusion의 `BAD`는 0이다. Domain Kotlin과 Historical WFF는 이 푸시 경로에 없어 시작하지 않았다. Bootstrap은 intelligence 시험을 실행하지 않는다.

| 워크플로 | 이벤트 | run | job | steps | URL |
|---|---|---|---|---|---|
| AURA Bootstrap | push | 46105237284 | 140856389869 | 31 | https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46105237284 |
| AURA Bootstrap | pull_request | 46105242362 | 140856405218 | 31 | https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46105242362 |
| Active documentation budget | push | 46105237286 | 140856389924 | 9 | https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46105237286 |
| Active documentation budget | pull_request | 46105242339 | 140856404945 | 9 | https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46105242339 |
| Windows host reproducibility | push | 46105237244 | 140856390167 `host (true)`, 140856389904 `host (false)` | 12, 12 | https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46105237244 |
| Windows host reproducibility | pull_request | 46105242350 | 140856405544 `host (true)`, 140856405339 `host (false)` | 12, 12 | https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46105242350 |

Bootstrap step 13 `Validation tool regression tests`, step 23 `Isolated Signature basic display without bundle`, Windows step 9 `Full host regression suite`는 push와 pull_request 모두 success다. 로컬 Python 3.14.7의 palette.svg와 PNG 다이제스트 실패는 그 Windows 전체 스위트에서 재현되지 않았다.

## 종료 게이트

| 게이트 | 결과 | 증거 |
|---|---|---|
| G0 사전 검증 | PASS | 위 PRE-FLIGHT. 제품 NO-GO는 유지 |
| G1 구현 | PASS, 한계 있음 | 추적표. epoch 상한과 D01·C01은 닫지 않음 |
| G2 검증 도구 | PASS | JUnit 부정 7종을 포함한 `JunitXmlCheckTest` 20개와 창 검사 OK |
| G3 시험 | PASS | 99, 81, 100000. FAIL/ERROR/SKIP 0 |
| G4 분야 | PASS, 제한 | FSM·TTL·순서는 시험. 실기기·공급원·WFF는 NOT RUN |
| G5 검토 | PASS, 자기 재검토 | 독립 검토자는 NOT RUN |
| G6 증거 | PASS, 제품 NO-GO | 로그, XML, CI 표. Bootstrap을 intelligence CI로 기록하지 않음 |
| G7 문서 | PASS, 제한 | 이 보고서와 intelligence 문서. 중앙 STATUS/WORK_LOG/BLOCKERS/FINDINGS는 수정하지 않음 |

제안하는 STATUS 한 줄은 중앙 문서를 대체하지 않는다. `GB-02 R08 독립 후보 보완 종료. 구현 671e999. PR #3 HOLD. 제품 NO-GO. R09 자동 착수 없음.`

FINDINGS의 AUD-R02와 AUD-R03-01은 총괄이 갱신하기 전까지 OPEN이다. 이 보고서가 그 행을 닫지 않는다.

## 미해결

- D01: 도메인 관측에 revision이 없다. 다른 축은 로컬 `observedAt`만 비교한다.
- AUD-R03-01: 보호 계약은 후보다. 합의와 C01 전이다.
- 15/20, 70/50, 60초와 출처별 미래 허용은 실측·합의 전이다.
- epoch `Long.MAX_VALUE`에서는 새 세션을 열 수 없다.
- intelligence 모듈 CI는 적용하지 않았다.
- 로컬 Python 3.14.7 palette.svg와 PNG 다이제스트는 GPT 담당이다.
