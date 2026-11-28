# GB-02 G01 / R07 감사 개선

상태: 독립 모듈 통합 후보. 제품 출시 NO-GO. PR #3은 병합하지 않는다. 외부 PR 통합 HOLD는 유지한다. R08, GB-03, GPT-07은 시작하지 않는다.

일자: 2026-11-28. 작업자: Grok Build. 검토자: 없음. G5는 자기 재검토다.

기준 브랜치: `agent/grok/GB-02`. 구현 SHA: `aacc744ef5844632c8b7ac588532fcf6441e8f88`. 이 보고서 커밋은 `modules/intelligence`를 바꾸지 않아야 한다. 확인은 `git diff aacc744ef5844632c8b7ac588532fcf6441e8f88 -- modules/intelligence`가 비어 있는지로 한다. CI head는 구현 뒤의 문서 병합 `bd25b331a320670775a93cb90a84f7fc5a10d3b8`다.

PRE-FLIGHT: PASS. 작업 시작의 `origin/main`은 `3f1f57c`였고 담당 경로와 겹치지 않아 병합 `89f303de0ccf4f65555f3b99eba84c5841a75473`로만 반영했다. 푸시 직전 `origin/main`은 `44140ff58896668092ec6453fcba936ca408809a`다. 차이는 `docs/STATUS.md`, archive, F03 증거, `BLOCKERS.md`, `GPT_EXECUTION_PLAN.md`, `WORK_LOG.md`, 배정표뿐이다. `modules/intelligence`, `modules/domain`, `.github`와 겹치지 않아 병합 `bd25b331a320670775a93cb90a84f7fc5a10d3b8`로만 반영했다. 들어온 파일은 수정하지 않았다. 같은 기준에서 `AGENTS.md`, `docs/STATUS.md`, `RESUME_PROTOCOL.md`, `PROJECT_INVARIANTS.md`, `TASK_RECORD_PROTOCOL.md`, `VERIFICATION_PROTOCOL.md`, `TASK_REPORT_TEMPLATE.md`, `GPT_EXECUTION_PLAN.md`, `BLOCKERS.md`, `WORK_LOG.md`, `GB-02-G01-R07.md`, `FINDINGS.md`, `REPORT-R02.md`, `REPORT-R03.md`, `REPORT-06.md`, `INTERFACE_CONTRACT.md`, `ASSUMPTIONS.md`, `CI_PROPOSAL.md`와 Machine/Gate/Policy를 대조했다. 현재 STATUS의 다음 행동은 `F03 R08 strict pilot 검증 종료 → 독립 SBOM/CVE/license 조사 가능 범위 확인, provenance 적용 BLOCKED. GPT-07 및 실기기 설치는 별도 승인 대기.`다. 그 문장을 바꾸지 않는다. PR #3은 OPEN이고 HOLD다.

작업 목표: R06 이후 AUD-R02-02, AUD-R02-03, AUD-R02-04, AUD-R02-06, AUD-R02-07, AUD-R02-10, AUD-R02-11과 F04용 보호 전달 후보를 다룬다. R06의 82개 intelligence 시험, 81개 domain 시험, 시드 `20261128`의 100000회 전이, 9개 상태/TTL, JUnit 부정 7종은 유지한다.

## 구현 및 결정

| 파일 | 변경 | 요구사항 |
|---|---|---|
| `Gate.kt`, `Axes.kt` | `FORECAST`가 아닌 `observedAt > referenceTime`은 `FUTURE_OBSERVATION`이다. 같은 시각은 허용한다. 허용 오차 상수는 없다. | AUD-R02-02 |
| `Machine.kt` | 배터리·강수는 출처, `observedAt`, 호출자가 준 revision만 기억한다. 없는 revision은 만들지 않는다. 더 이른 값과 같은 revision의 다른 값은 첫 숫자를 유지한다. | AUD-R02-03 |
| `Machine.kt` | 잘못된 정책은 `PolicyRejected`로 남고 `deliveredIntent()`는 null이다. `failSafe`가 AOD, 모션 감소, 기존 그래픽 제한을 유지한다. | AUD-R02-04 |
| `Machine.kt` | 상한에서 보관 TTL이 지나면 생략된 숫자를 null로 거둔다. `resync`만 새 숫자를 받고 revision은 넘기지 않는다. | AUD-R02-06 |
| `Machine.kt`, `PROTECTION_DELIVERY_CONTRACT.md` | `deliverySequence`는 1씩 증가하고 `Long.MAX_VALUE`에서 멈춘다. 더 작은 순서는 보호를 해제하지 못한다. | AUD-R02-07, AUD-R03-01 |
| `Machine.kt` | 그래픽 제한은 전원 축과 따로 후보 15/20 구간을 유지한다. 충전과 저전력 대기에서 17%는 제한을 끄지 않는다. | AUD-R02-10, AUD-R02-11 |

결정: 15/20, 70/50, 60초는 제품 상수로 올리지 않는다. 그래픽 유지는 기존 후보 구간을 재사용한다. 도메인 `Observation`에는 revision이 없고 출처 변경은 `KEY_MISMATCH`다. 도메인 수정은 D01 제안만 남긴다. 보호 계약은 총괄 합의 전 후보다. Wear Services와 WFF는 연결하지 않는다. 회차 05 소비자는 `deliverySequence`를 무시하면 그대로다.

전달 순서가 `Long.MAX_VALUE`이면 새 요청과 오래된 요청을 구분하지 못한다. 감싸지 않고 적용하지 않는다. 재시작은 소비자 워터마크와 `lastDeliverySequence`를 함께 되돌리는 호출이다. 그 상한에서 새 보호를 순서만으로 구분하는 것은 이 후보의 한계다.

## 요구사항 추적

| ID | 시험 | 수정 전 | 수정 후 | 판정 |
|---|---|---|---|---|
| AUD-R02-03 | `olderObservationDoesNotReplaceNewerBattery`, `equalRevisionConflictKeepsTheFirstBattery`, `deniedBatteryIsNotRedisplayedByAnOlderSample`, `newerSourceCanReplaceAnOlderSource`, `sameObservationTimeWithoutRevisionFollowsCallOrder` | 과거 10이 80을 덮음 | 80 유지, 충돌은 첫 값, 철회 뒤 과거 값은 null, 다른 출처의 더 늦은 값은 수신 | PASS |
| AUD-R02-04 | `badPolicyKeepsProtectionWithoutPretendingThePolicyIsValid` | 보호 전달 없음 | `issues` 유지, `deliveredIntent()` null, `failSafe`가 AOD·모션·그래픽을 유지. 첫 입력 revision 0 | PASS |
| AUD-R02-02 | `futureObservedValueIsRejectedWithoutAProductSkew`, `forecastDoesNotReplaceAnAcceptedObservation` | 미래 값이 Fresh | 미래 관측 거절, 같은 시각 허용, 예보는 관측 커서를 바꾸지 않음 | PASS. 출처별 허용 오차는 미합의 |
| AUD-R02-06 | `ceilingDropsOmittedBatteryAfterStoredTtlAndResyncCanReplaceIt` | 상한 생략이 `LimitReached`로 80을 유지 | 만료 시각에 null, 비-resync 10은 거절, resync 40은 상한 revision 유지 | PASS |
| AUD-R02-07 | `deliverySequenceKeepsLateReleaseFromClearingNewerProtection` | 호출 순서만 있음 | 늦은 해제는 무시, 더 큰 순서의 보호는 적용, `LimitReached`는 워터마크만 전진 | PASS. 순서 상한은 위 한계 |
| AUD-R02-10, AUD-R02-11 | `chargingAndLowWaitKeepGraphicsInsideTheCandidateBand` | 충전 17%와 대기 17%에서 그래픽 해제 | 17%는 제한 유지, 20%는 해제. 전원 축 히스테리시스는 유지 | PASS, 제품 임계값 승격은 PARTIAL |
| AUD-R03-01 | `ProtectionConsumer`와 `PROTECTION_DELIVERY_CONTRACT.md` | 공통 계약 없음 | 후보 표와 시험 전용 소비자. 런타임은 C01 | PARTIAL. 합의 전 |
| R06 회귀 | 기존 82, domain 81, `longRunKeepsInvariants`, `permissionStatusStaysDistinctFromTtl`, JUnit 7종 | 유지 대상 | 93 PASS, 81 PASS, 100000회 1메서드 PASS | PASS |

시험 메서드 수와 단언 수를 구분한다. 신규 메서드는 `Round07Test` 11개다. 93은 82에 11을 더한 수량이다. 100000회는 `Round05Test.longRunKeepsInvariants` 1개 메서드 안의 전이다. JUnit 부정 7종은 `rejectsEmptyMethod`, `rejectsMissingCounters`, `rejectsMissingClassname`, `rejectsUnrelatedClassname`, `rejectsSuiteFilenameMismatch`, `rejectsNestedTestcase`, `rejectsFutureTimestamp`다. 수정 전 재현 클래스는 `Round07ReproTest`이고 스위트에는 남지 않는다.

## 정책 후보와 미확정

| 항목 | 이 회차 | 승인 전 상태 |
|---|---|---|
| 그래픽 15/20 | 기존 후보를 전원 축과 분리해 유지. 10→17은 제한 유지, 20은 해제 | 실측 전 제품 상수 아님. 승격은 PARTIAL |
| 강수 70/50, 유지 60초 | 변경하지 않음 | 후보 유지 |
| 미래 시각 허용 | 0. 같은 시각만 허용 | 출처별 합의 없음 |
| 도메인 스트림 revision | 구현하지 않음 | D01 |
| 보호 전달 순서 | 후보. 회차 05 호출 순서는 필드를 무시하면 유지 | 총괄 합의 전. C01 NOT RUN |
| 순서 상한 | 감싸지 않음. 같은 상한은 적용하지 않음 | 쌍으로 재시작해야 새 보호를 다시 구분 |

## 검증 결과

| 시험 | 명령 | 결과 | 판정 | 로그 |
|---|---|---|---|---|
| 수정 전 재현 | intelligence `Round07ReproTest` | 4 completed, 4 failed | PASS, 재현 | [intelligence-repro-r07.log](intelligence-repro-r07.log) |
| intelligence clean JDK 17 | `gradlew -p modules/intelligence clean test --no-daemon --offline --no-build-cache` | 93 PASS, 0 FAIL, 0 ERROR, 0 SKIP. XML 11파일. BUILD SUCCESSFUL in 29s | PASS | [intelligence-test-summary-r07.log](intelligence-test-summary-r07.log), [junit-r07](junit-r07) |
| domain 회귀 | `gradlew -p modules/domain clean test --no-daemon --offline --no-build-cache` | 81 PASS, 0 FAIL, 0 ERROR, 0 SKIP. XML 7파일. BUILD SUCCESSFUL in 20s | PASS | [domain-regression-r07.log](domain-regression-r07.log), [junit-r07-domain](junit-r07-domain) |
| 장시간 전이 | 위 스위트의 `longRunKeepsInvariants` | PASSED. 시드 20261128, 한 메서드 안 100000회 | PASS | 같은 intelligence 로그 |
| JUnit 창 | `check_junit_xml.py` | `OK files=11 tests=93`, `OK files=7 tests=81` | PASS | 아래 시각 |
| 호스트 | `python -m unittest discover -s tests/unit -p test_*.py` | 370 ran, 368 PASS, 1 FAIL, 1 ERROR, 0 SKIP, 74.854s | 환경 | [host-unit-r07.log](host-unit-r07.log) |
| 문서 예산 | `python tools/check_doc_budget.py` | exit 0. STATUS 6550/8192 | PASS | 이 표 |
| 실기기, 공급원, WFF, intelligence 모듈 CI | 미실행 | NOT RUN | NOT RUN | 없음 |

환경: Windows. ASCII worktree `C:\Users\scarl\AppData\Local\Temp\aura-gb02-wt`. 테스트 JVM Eclipse Temurin 17, `C:\Users\scarl\.jdks\temurin-17`. Gradle 9.3.1. Kotlin 2.4.21. Python 3.14.7. Intelligence XML `2026-11-28T02:56:29.938Z`부터 `2026-11-28T02:56:34.298Z`. Domain XML `2026-11-28T02:56:54.933Z`부터 `2026-11-28T02:56:55.347Z`. 시각은 UTC다. 검사기 비교는 그 끝점을 포함한다.

호스트 1 ERROR는 `test_bootstrap_generator.GeneratorTests.test_checked_in_outputs`의 `assets/generated/bootstrap/palette.svg` stale이다. 1 FAIL은 `test_f01_r01.F01SignatureTests.test_normal_artifact_preserved`의 PNG 다이제스트다. 둘 다 Python 3.14.7 로컬 결과이고 GPT 담당이다. 원본과 `tools/`는 수정하지 않았다.

공통 Bootstrap 성공은 intelligence 시험 성공이 아니다. intelligence 모듈 CI는 `CI_PROPOSAL.md`에만 있고 적용하지 않았다. 기대 수량은 11파일 93시험, domain 7파일 81시험이다.

## CI

CI head: `bd25b331a320670775a93cb90a84f7fc5a10d3b8`. 구현 `aacc744ef5844632c8b7ac588532fcf6441e8f88`의 부모이며 `modules/intelligence` diff는 비어 있다. 적용 대상은 Bootstrap, 문서 예산, Windows 재현의 push와 pull_request다. 재확인한 step conclusion의 `BAD`는 0이다. Domain Kotlin과 Historical WFF는 이 푸시 경로에 없어 시작하지 않았다. Bootstrap은 intelligence 시험을 실행하지 않는다.

| 워크플로 | 이벤트 | run | job | steps | URL |
|---|---|---|---|---|---|
| AURA Bootstrap | push | 46100634036 | 140842044619 | 31 | https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46100634036 |
| AURA Bootstrap | pull_request | 46100637283 | 140842055690 | 31 | https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46100637283 |
| Active documentation budget | push | 46100634050 | 140842044574 | 9 | https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46100634050 |
| Active documentation budget | pull_request | 46100637215 | 140842055298 | 9 | https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46100637215 |
| Windows host reproducibility | push | 46100634064 | 140842044865 `host (true)`, 140842045033 `host (false)` | 12, 12 | https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46100634064 |
| Windows host reproducibility | pull_request | 46100637217 | 140842055546 `host (true)`, 140842055384 `host (false)` | 12, 12 | https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46100637217 |

Bootstrap step 13 `Validation tool regression tests`, step 23 `Isolated Signature basic display without bundle`, Windows step 9 `Full host regression suite`는 push와 pull_request 모두 success다. 로컬 Python 3.14.7의 palette.svg와 PNG 다이제스트 실패는 그 Windows 전체 스위트에서 재현되지 않았다.

## G0~G7

| 게이트 | 판정 | 근거 |
|---|---|---|
| G0 | PASS | PRE-FLIGHT 문서를 최신 main에서 읽었다. 들어온 문서는 수정하지 않았다. |
| G1 | PASS, 제한 | 관측 순서, 보호 유지, 미래 시각, 상한 TTL, 전달 순서, 그래픽 후보 구간이 시험과 연결된다. 제품 임계값과 도메인 revision은 확정하지 않았다. |
| G2 | PASS | 수정 전 4 failed. 수정 후 같은 결함을 거절한다. 기존 단언은 유지했다. JUnit 부정 7종은 통과한다. |
| G3 | PASS | intelligence 93, domain 81, 100000회 1메서드. FAIL 0, ERROR 0, SKIP 0. |
| G4 | PASS, 제한 | 관측과 예보, TTL, 히스테리시스를 분리했다. 실기기·공급원·WFF는 NOT RUN. |
| G5 | PASS, 자기 재검토 | 독립 검토자는 NOT RUN. 순서 상한과 D01과 후보 계약은 숨기지 않았다. |
| G6 | PASS | 코드 SHA `aacc744`. CI head `bd25b33`의 Bootstrap, 문서 예산, Windows push와 pull_request는 step success다. `BAD`는 0이다. 제품 GO로 올리지 않음. |
| G7 | PASS, 제한 | 중앙 STATUS/WORK_LOG/BLOCKERS는 수정하지 않았다. 제안만 아래에 둔다. |

최종 판정: 독립 모듈 통합 후보. 기존 82개와 domain 81개를 유지하고 신규 11개 메서드가 통과했다. 제품 출시 판정은 NO-GO다. PR #3 HOLD는 유지한다.

## 통합 차단점

| ID | 상태 | 해결 조건 |
|---|---|---|
| AUD-R02-03/04/06/07 | 이 모듈 시험에서 닫음. 순서 상한은 한계로 남음 | 중앙 `FINDINGS.md` 갱신은 총괄이 한다. |
| AUD-R02-02 | 후보 거절은 닫음 | 출처별 허용 오차 합의 전 제품 상수 아님 |
| AUD-R02-10/11 | 동작은 후보 15/20으로 닫음. 제품 승격은 PARTIAL | 실측 승인 전 새 숫자를 제품 정책으로 올리지 않음 |
| AUD-R03-01 | PARTIAL | 후보 계약 합의와 C01 런타임. Wear/WFF는 없음 |
| D01 | PARTIAL | 도메인 스트림 revision. 이 회차는 수정하지 않음 |
| GB02-R05-ASYNC | 회차 05 계약 유지 | `deliverySequence`를 넘기지 않는 소비자는 호출 순서를 쓴다 |
| 공통 CI | 미적용 | 총괄이 `CI_PROPOSAL.md`를 적용한다. 기대 수량은 11/93과 7/81 |
| 호스트 Windows | 로컬만 | 370개 중 368 PASS, 1 FAIL, 1 ERROR. GPT 담당. 원본 유지 |
| 제품 출시 | NO-GO | 실기기, 공급원, WFF, 배터리, 확정 임계값 없음 |

## 중앙 문서 제안

- STATUS: 현재 다음 행동인 F03 R08 strict pilot 검증 종료를 빼지 않는다. GB-02 PR #3 회차 07은 로컬 intelligence 93 PASS, domain 81 PASS, 구현 `aacc744`, CI head `bd25b33`의 Bootstrap 46100634036/46100637283, 문서 예산 46100634050/46100637215, Windows 46100634064/46100637217이 success, 실기기와 intelligence 모듈 CI는 NOT RUN, 제품 NO-GO, PR은 미병합이라고 한 줄 추가할 수 있다.
- WORK_LOG: 같은 한 줄을 추가할 수 있다.
- BLOCKERS: 변경하지 않는다. D01, AUD-R03-01, 제품 임계값, GB02-R05-ASYNC는 이 보고서의 차단점이다.
- FINDINGS: 총괄이 해결 증거를 이 보고서와 맞춘 뒤에만 상태를 바꾼다.
- `.github/workflows`: 변경하지 않는다.

다음 행동: 총괄이 PR #3을 검토한다. main 병합, 공통 워크플로 수정, R08, GB-03, GPT-07은 시작하지 않는다.
