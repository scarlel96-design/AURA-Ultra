# 작업 보고서 — GB-02 / 회차 04

상태: GO (독립 모듈 제출). 제품 출시 NO-GO. PR #3은 병합하지 않는다. 외부 PR 통합 HOLD는 유지한다.
일자, 작업자, 검토자: 2026-11-28, Grok Build, 자기 재검토. 독립 검토자 없음.
기준 브랜치/HEAD: 작업 브랜치 `agent/grok/GB-02`. PR #3. 착수 전 원격 PR HEAD는 `58e9f9f83135f89c56962bac902151e37355af4b`였다. 그 시점의 `origin/main`은 `c6fca7a3c95a735bb2a05b0cc420d138177c6e6d`였고 이미 이 브랜치에 들어 있었다. 구현 커밋 직전 `origin/main`은 `55721ea5a865f135cfcfcd212bcd16d01ae58e2a`로 이동했다. 재기반과 강제 푸시 없이 병합 커밋 `8177073ce12682a10e7e3f47275603ee7748ddbe`로 반영했다. 그 병합은 `modules/intelligence`, `modules/domain`, `.github`를 수정하지 않았다.
PRE-FLIGHT: 최신 `origin/main` `55721ea5a865f135cfcfcd212bcd16d01ae58e2a`의 `docs/STATUS.md`, `docs/operations/agent-orders/README.md`, `docs/operations/BLOCKERS.md`를 확인했다. 기준일 2026-11-28. STATUS가 확인한 코드 SHA는 `110183ebf3ea3259be979292dde2400bb9f9dbb9` (GPT-06 R01 통합 CI 성공)다. 활성 작업은 GPT-04 PARTIAL, GPT-05 PARTIAL R07 검증·통합, GPT-06 PARTIAL R01 통합 성공 / R02 보완 후보다. 다음 안전한 행동은 R02 보완 CI `46078480317` 검증 뒤 통합 검토와 R03 유리 소재다. 이 순서는 GB-02 소유 경로의 회차 04를 철회하지 않는다. 담당 표는 GB-02를 `R03 제출, R04 보완 필요 (HOLD)`로 적고, 소유 경로는 `modules/intelligence/**`와 `docs/evidence/GB-02/**`다. 제품 출시 NO-GO, 공식 WO GO 0/38, GPT 묶음 3/12. B-011의 도구 불일치는 해결로 적혀 있고 B-002/B-003 런타임/B-004/B-005/B-006/B-007/B-008은 유지된다. GPT06-D1은 GPT-06 링 후보의 미해결 항목이며 이 모듈의 새 차단으로 가져오지 않는다. `origin/main` 대비 `modules/domain`과 `.github` diff는 비어 있다. 병합으로 들어온 GPT-06 소재 파일과 중앙 문서는 수정하지 않았다. PRE-FLIGHT PASS. 제품 출시 NO-GO와 PR 병합 금지는 유지한다.
검증 대상 코드 SHA: `0161cf7bb1bd9c7a3c18760b0481208d39e5b0ca`
관련 요구사항 / WO / GPT ID: R-12, R-17, R-22의 상태 머신 경계. GPT-07과 WO-21/22/23의 정식 선행 조건은 해제하지 않는다.
관련 정본 문서: `docs/operations/agent-orders/GB-02.md`, `docs/DATA_INTELLIGENCE.md`, `docs/PERFORMANCE.md`, `modules/domain/docs/INTERFACE_CONTRACT.md`, `modules/intelligence/docs/INTERFACE_CONTRACT.md`
작업 목표, 포함/제외 범위: AUD-07을 해결한다. `PowerAxis`는 `NORMAL`/`LOW`/`CHARGING`을 유지하고, 신선한 낮은 배터리는 충전 축과 별도로 장식과 입자를 제한한다. 저전력 보호가 일반 디바운스와 최소 유지 때문에 지연되는 경로를 없앤다. revision 상한에서 보호 설정이 같은 revision으로 전달되게 한다. 상한에서 만료되거나 권한이 철회된 관측의 이전 숫자가 계속 공개되는 경로를 없앤다. 다른 축의 반복 변화가 한 축의 확정을 다시 시작하지 않게 한다. 기존 intelligence 47개와 domain 81개를 유지한다. 정본과 충돌하는 기대값만 근거를 적고 수정한다. 독립 CI 초안의 실행 조건과 JUnit 검사만 점검한다. 공통 워크플로는 수정하지 않는다. 구현 커밋은 `modules/intelligence/**`만 바꾼다. 증거는 `docs/evidence/GB-02/**`만 추가한다. 도메인 계약, 루트 Gradle, WFF, 공통 `.github/workflows`, 중앙 STATUS/WORK_LOG/BLOCKERS, GPT-04/05/06 파일은 수정하지 않는다.
선행 조건 및 이전 실패: 회차 03 코드 `c554ab06feb5cec50244eb9525b22203eba72c93`, 증거 `1956a29c9b003ea15e1e8a9a1278fd6dd6bc6dd6`, 나중 main 기록 `caace03645fb57454331fc3be8eabee3da448836`, CI 기록 `58e9f9f83135f89c56962bac902151e37355af4b`. 공통 bootstrap은 head `caace03`에서 push `46075778210`, pull_request `46075782846`가 success였고 각 job 26 steps success였다. 그 워크플로는 intelligence 시험을 실행하지 않았다. 회차 03은 AUD-07 분리를 기각했다. 회차 04는 `DATA_INTELLIGENCE.md`를 우선해 그 기각을 되돌린다. 회차 01부터 03의 보고서와 JUnit XML은 삭제하지 않았다.
변경 파일 소유권 / 변경 영향: 작업 트리는 `C:\Users\scarl\AppData\Local\Temp\aura-gb02-wt`. 병합 커밋이 가져온 GPT-06 파일은 수정하지 않았다. 구현 diff는 intelligence 소스, 시험, 모듈 문서 8개 파일이다.
참조 자료(정확한 URL·버전·확인일): 2026-11-28. Kotlin 2.4.21, https://kotlinlang.org/docs/releases.html, Apache-2.0, https://github.com/JetBrains/kotlin/blob/v2.4.21/license/LICENSE.txt. JUnit Jupiter 5.10.1 / Platform 1.10.1, EPL-2.0, https://junit.org/junit5/. Gradle Wrapper 9.3.1, Apache-2.0. Foojay toolchain resolver 1.0.0, Apache-2.0. 의존 구성은 회차 01 [test-runtime-classpath.log](test-runtime-classpath.log)와 같다. 이번 회차는 의존성을 추가하지 않았다.
가정 / 위험 / 승인 필요 사항: [modules/intelligence/docs/ASSUMPTIONS.md](../../../modules/intelligence/docs/ASSUMPTIONS.md)의 GB02-A1~A28. 15/20, 70/50, 60초는 제품 상수가 아니다. 호출자가 넣은 시각만 쓴다. 그래픽 전력 제한은 품질 프로필과 OS 절전 상태가 아니다. 도메인 초안에는 입자 필드가 없으므로 초안은 포커스 이름 `POWER`와 이유 `POWER_LOW`로 제한을 전달한다.
성공 기준 / 롤백 방법: 수정 전 네 경계가 재현되고, 수정 후 clean JDK 17에서 기존 47개와 `Round04Test` 5개가 실패 0이며, 도메인 81개가 유지된다. 롤백은 이 브랜치를 main에 병합하지 않으면 된다.

## 구현 및 결정

| 파일·모듈 | 변경 및 이유 | 관련 요구사항 | 확인할 영향 |
|---|---|---|---|
| `Machine.kt` | 전원 축은 유지한다. 신선한 낮은 배터리는 `graphicsPowerLimited`로 포커스를 `POWER`로 하고 입자를 끈다. 축이 `LOW`로 확정되기 전에는 품질 `BALANCED`와 모션 허용을 유지한다. | R-12, AUD-07, `DATA_INTELLIGENCE.md` | 충전 축을 지우지 않음. 장식과 입자는 즉시 제한 |
| `Machine.kt` | 그래픽 제한은 디바운스와 최소 유지를 기다리지 않는다. 전원 축의 확정은 기존 기한을 유지한다. | R-12 | 대기 중에도 입자 꺼짐, 품질은 Eco가 아님 |
| `Machine.kt` | `StepResult.deliveredIntent()`는 `Advanced`의 의도만 돌려준다. 상한에서도 전해야 할 보호는 같은 revision의 `Advanced`다. | R-22 | revision이 늘지 않아도 소비자가 보호를 적용 |
| `Machine.kt` | 상한에서 `Unusable`인 배터리·강수 채널은 이전 공개 숫자를 null로 거둔다. 생략은 유지한다. 역전은 거두지 않는다. 새 신선한 숫자는 상한에서 반영하지 않는다. | R-22 | null은 0이 아님. 이미 켜진 보호는 꺼지지 않음 |
| `Machine.kt` | `powerCommittedAt`, `weatherCommittedAt`, `activityCommittedAt`과 축별 보류 시작을 둔다. `committedAt`은 마지막 센서 확정 시각으로 남긴다. | R-12 | 다른 축의 반복이 한 축의 기한을 다시 시작하지 않음 |
| 기존 시험 4곳 | 정본과 충돌하던 포커스 기대만 수정했다. 근거는 각 시험의 주석과 아래 추적표다. | AUD-07 | 축 개수, 품질, 모션 허용은 유지 |
| `Round04Test.kt` | 충전 유지와 장식 제한, 즉시 그래픽 제한, 상한 전달, 숫자 거두기, 축별 타이머 5개를 고정한다. | R-12, R-22 | 재현 클래스는 로그를 남기고 삭제 |
| `CI_PROPOSAL.md` | 기대 수량을 `TEST-*.xml` 7파일 52시험과 domain 7파일 81시험으로 올린다. main push와 `workflow_dispatch`는 유지한다. 실행하지 않는다. | R-22 | `.github` 미수정 |

결정, 대안, 기각 사유 및 ADR: 회차 03은 충전 유지 시험의 `DECORATIVE`와 모션 허용을 이유로 장식 제한을 기각했다. 회차 04 지시는 정본을 우선하고, 충돌하는 기존 기대값만 근거를 적어 고치라고 한다. 정본은 독립 축 `NORMAL`/`LOW`/`CHARGING`, 우선순위 `CRITICAL > POWER > EXERCISE > WEATHER > CONTEXT > DECORATIVE`, 낮은 배터리에서 날씨 숫자 유지와 입자 제거, OS 절전과 AURA 품질 프로필의 구분을 요구한다. 그래서 축 값은 추가하지 않고, 충전 누락은 `CHARGING`을 유지하며, 신선한 낮은 배터리만 포커스와 입자를 제한한다. Eco와 모션 차단은 확정된 `LOW`에만 남겨 품질 프로필과 그래픽 제한을 나눈다. 상한에서 새 revision을 만들면 감싸기 금지를 깨므로 만들지 않는다. 소비자가 revision 증가만 보면 상한 보호를 놓치므로 `deliveredIntent()`가 null이 아니면 적용하는 계약을 제안하고 시험으로 고정했다. `LimitReached`는 적용할 의도가 없고 이전 상태 객체를 그대로 돌려준다. 상한의 숫자 거두기는 `Unusable` 채널에 한정한다. 생략과 역전과 새 신선한 값은 이전 숫자를 바꾸지 않는다. 센서 세 축의 기한은 축마다 둔다. 긴급은 날씨와 그 샘플의 목표 전원을 함께 확정하고, 충전 예외는 전원만 확정한다. 활동과 날씨는 그 예외를 물려받지 않는다. ADR은 만들지 않았다.

시도한 접근과 실패 원인: 수정 전 `Round04ReproTest` 4개는 [intelligence-repro-r04.log](intelligence-repro-r04.log)에서 모두 실패했다. 충전을 유지한 신선한 10%의 포커스는 `DECORATIVE`였다. 디바운스와 유지 대기 중의 신선한 10%도 `DECORATIVE`였다. `Long.MAX_VALUE`의 낮은 배터리와 만료 숫자는 `Advanced`가 아니라 `LimitReached`였다. 날씨 유지 중에 충전 예외가 확정되면 60초 뒤에도 날씨가 `ALERT`로 남았다. 이 재현 클래스는 로그를 남긴 뒤 삭제하고, 같은 경계를 `Round04Test`에 고정했다.

사용법, 환경, 재현 명령, 설정 변경: [modules/intelligence/docs/BUILD.md](../../../modules/intelligence/docs/BUILD.md). ASCII worktree에서 `.\gradlew -p modules/intelligence clean test --rerun-tasks --offline`와 `.\gradlew -p modules/domain test --rerun-tasks --offline`. 공통 CI에 넣을 초안은 [modules/intelligence/docs/CI_PROPOSAL.md](../../../modules/intelligence/docs/CI_PROPOSAL.md)다. 적용하지 않았다. 소비자는 `step` 결과의 `deliveredIntent()`가 null이 아니면 그 의도와 `toPresentationDraft()`를 적용한다.

## 요구사항 및 검증 추적표

| 요구사항/완료 기준 | 구현 파일·경로 | 시험 ID | 예상 결과 | 실제 결과 | 증거·SHA | 판정 |
|---|---|---|---|---|---|---|
| 신선한 낮은 배터리는 장식과 입자를 제한하고 충전 축은 유지 | `freshBatteryIsLow`, `focusOf`, `intentFor` | `freshLowBatteryLimitsDecorationWithoutChangingTheChargingAxis`, `missingOrInvalidChargingDoesNotClearCharging`, `missingChargingAndLowBatteryDoNotAddAPowerAxis`, `chargingIsNotLowPowerAndBypassesHold` | 축 `CHARGING`, 포커스 `POWER`, 품질 `BALANCED`, 모션 허용, 입자 거짓, `POWER_LOW`, 공개 10. `PowerAxis.entries`는 세 값 | PASS | 0161cf7 | PASS |
| 그래픽 제한은 디바운스와 최소 유지를 기다리지 않음 | `graphicsLow` | `lowPowerGraphicsDoNotWaitForDebounceOrHold`, `immediateAxesDoNotResetTheSensorHold` | 10초 시점은 축 `NORMAL`, 포커스 `POWER`, 입자 거짓, 모션 허용, 품질 `BALANCED`. 60초에 `LOW`와 Eco, 모션 거짓 | PASS | 0161cf7 | PASS |
| 상한의 보호를 같은 revision으로 전달 | `deliveredIntent`, `deliverAtCeiling` | `ceilingProtectionIsDeliveredWhenRevisionStaysAtTheLimit`, `revisionCeilingAppliesProtectionWithoutWrapping` | `deliveredIntent()`의 revision은 `Long.MAX_VALUE`. 모션 감소 초안에 `MOTION_REDUCTION`. 낮은 배터리는 축 `NORMAL`, 포커스 `POWER`, 이전 숫자 80 유지. 보호를 끄는 입력은 이전 객체의 `LimitReached`이고 `deliveredIntent()`는 null | PASS | 0161cf7 | PASS |
| 상한에서 만료·권한 철회 숫자를 거두고 생략과 역전은 거두지 않음 | `deliverAtCeiling` | `ceilingWithdrawsExpiredAndDeniedPublications`, `revisionDoesNotWrapAndStopsAtTheLimit` | 만료 배터리는 null, 강수 70 유지, `DEGRADED`, `STALE_IGNORED`. 권한 철회 강수는 null, 배터리 40 유지, `DENIED_IGNORED`. 상한의 보호 없는 역전은 이전 객체 | PASS | 0161cf7 | PASS |
| 다른 축의 반복이 한 축의 기한을 다시 시작하지 않음 | `powerCommittedAt`, `keptSince` | `anotherAxisDoesNotRestartDebounceOrHold` | 충전 예외 뒤 60초에 날씨는 `NORMAL`, 전원은 `CHARGING`. 활동이 20초와 40초에 바뀌어도 전원 디바운스는 40초에 확정되고 활동은 `REST` | PASS | 0161cf7 | PASS |
| 회차 03까지 intelligence 47개 유지 | 기존 시험 | Gate 4, Machine 17, Policy 5, Round02 12, Round03 7, SourceScan 2 | 메서드 유지. 정본과 충돌하는 포커스 기대만 수정 | 47 PASS. 추가 5개와 합쳐 52 | 0161cf7 | PASS |
| 도메인 81개 유지 | 비수정 `modules/domain` | GB02-DOMAIN | 81 PASS | 81 PASS / 0 FAIL / 0 SKIP / 0 ERROR. XML 파일 7 | domain diff 없음 | PASS |
| 모듈 CI를 공통 워크플로에 넣지 않고 제안만 점검 | `CI_PROPOSAL.md` | 초안 | `TEST-*.xml`, main push, 7/52와 7/81, 빈 XML과 `tests=0` 실패 | 파일만 갱신. 실행은 NOT RUN | 0161cf7 | NOT RUN |
| 실기기, 실공급원, 그래픽 | 없음 | 없음 | 실행하지 않음 | NOT RUN | 없음 | NOT RUN |

수정한 기존 기대와 근거:

- `Round02Test.missingOrInvalidChargingDoesNotClearCharging`: 충전 생략과 신선한 10%의 포커스를 `DECORATIVE`에서 `POWER`로, 입자를 거짓으로, `POWER_LOW`를 요구하도록 바꿨다. 축 `CHARGING`, 품질 `BALANCED`, 모션 허용, 공개 10, `CHARGING_EXCEPTION` 없음은 유지했다. 근거는 `DATA_INTELLIGENCE.md`의 낮은 배터리 입자 제거와 `POWER`가 `DECORATIVE`보다 앞이라는 우선순위다. 사용할 수 없는 충전과 단위 불일치는 축 유지 단언을 바꾸지 않았다.
- `Round03Test.missingChargingAndLowBatteryDoNotAddAPowerAxis`: 같은 분리로 포커스와 입자와 `POWER_LOW`를 바꿨다. `PowerAxis.entries`가 세 값인 단언과 `POWER_CHARGING`은 유지했다.
- `MachineTest.chargingIsNotLowPowerAndBypassesHold`: 충전 참과 신선한 10%의 포커스를 `DECORATIVE`에서 `POWER`로 바꿨다. 품질 `BALANCED`, 모션 허용, 축 `CHARGING`은 유지하고 입자 거짓과 `POWER_LOW`를 추가했다. 충전 축이 Eco가 아니라는 기존 의미는 품질과 모션 단언이 유지한다.
- `MachineTest.immediateAxesDoNotResetTheSensorHold`: 전원 축이 아직 `NORMAL`인 신선한 10%와 `NIGHT`의 포커스를 `CONTEXT`에서 `POWER`로 바꿨다. `POWER`가 `CONTEXT`보다 앞이다. 밝기 `NIGHT`와 유지 시각을 재설정하지 않는 단언은 유지했다.

## 검증 결과

| 시험 ID | 필수/선택 | 종류 | 명령·대상 버전 | 기대 결과 | 실제 결과 | 판정 | 로그 |
|---|---|---|---|---|---|---|---|
| GB02-R04-REPRO | 필수 | 수정 전 실패 주입 | `gradlew -p modules/intelligence test --offline --tests Round04ReproTest` | 네 경계가 회차 03 코드에서 실패 | 4 completed, 4 failed. BUILD FAILED in 30s | PASS, 재현 | [intelligence-repro-r04.log](intelligence-repro-r04.log) |
| GB02-UNIT-R04 | 필수 | clean JDK 17 | `gradlew -p modules/intelligence clean test --rerun-tasks --offline`, toolchain 17 | 기존 47 + Round04Test 5, 실패 0 | 52 PASS, 0 FAIL, 0 SKIP, 0 ERROR. XML 파일 7. BUILD SUCCESSFUL in 32s. XML `2026-11-27T22:51:15Z` | PASS | [intelligence-test-summary-r04.log](intelligence-test-summary-r04.log), [junit-r04](junit-r04) |
| GB02-DOMAIN-R04 | 필수 | 회귀 | `gradlew -p modules/domain test --rerun-tasks --offline` | 81 PASS | 81 PASS, 0 FAIL, 0 SKIP, 0 ERROR. XML 파일 7. BUILD SUCCESSFUL in 20s. XML `2026-11-27T22:51:35Z` | PASS | [domain-regression-r04.log](domain-regression-r04.log) |
| GB02-SCAN | 필수 | 실패 주입 | SourceScanTest | 심은 `Instant.now(`와 네트워크 import를 잡고, 본소스에는 없다 | PASS | PASS | 같은 intelligence 로그 |
| 실기기, 네트워크 공급원, 그래픽, OS 절전 측정 | 제외 | 실기기 | 미실행 | NOT RUN | NOT RUN | NOT RUN | 없음 |
| intelligence용 GitHub CI | 제외 | CI | `.github` 미수정 | 이 워크플로에는 없음 | NOT RUN | NOT RUN | [CI_PROPOSAL.md](../../../modules/intelligence/docs/CI_PROPOSAL.md) |

환경 및 도구 버전: Windows. 테스트 JVM은 Eclipse Temurin 17.0.20.1+1, `C:\Users\scarl\.jdks\temurin-17`. 로그 한 줄은 `TEST_JVM version=17 vendor=Eclipse Temurin path=C:\Users\scarl\.jdks\temurin-17`. Gradle 9.3.1. Kotlin 2.4.21. ASCII worktree `C:\Users\scarl\AppData\Local\Temp\aura-gb02-wt`. Wrapper SHA-256 `b3a875ddc1f044746e1b1a55f645584505f4a10438c1afea9f15e92a7c42ec13`.
총 시험 수, PASS, FAIL, SKIP, NOT RUN, PENDING: intelligence 52 PASS / 0 FAIL / 0 SKIP / 0 ERROR. 구성은 기존 Gate 4, Machine 17, Policy 5, Round02Test 12, Round03Test 7, SourceScan 2에 Round04Test 5를 더한 것이다. 도메인 회귀 81 PASS / 0 FAIL / 0 SKIP / 0 ERROR. 실기기·실공급원·그래픽·모듈 GitHub CI는 NOT RUN. clean 시험은 병합 커밋 `8177073` 전에 실행했다. 그 병합은 `modules/intelligence`와 `modules/domain`을 바꾸지 않았고, 구현 커밋의 그 파일은 시험한 작업 트리와 같다.
CI 실행 ID / head SHA / job / step: 공통 bootstrap head는 증거 커밋 `27e8aa6f293e9d115b2cb539161dc465694d1d00`다. push [46079624268](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46079624268), job `140775321987`, conclusion success. pull_request [46079625581](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46079625581), job `140775326333`, 같은 head, conclusion success. 두 실행 모두 26 steps가 success였다. wrapper 검사, bootstrap 자산 재생성, 독립 재생성, 원형 레이아웃, 구조 검사, M01 synthetic motion evidence, validation tool regression, SDK 설치와 확인, 공식 WFF validation, debug APK build, APK 내용, 메모리 평가, debug 서명, isolated flavor, isolated Signature, 레이아웃 증거와 APK artifact 업로드가 포함된다. 실패한 step은 없다. 이 워크플로는 `modules/intelligence` 시험을 실행하지 않는다. 이번 52개와 도메인 81개는 로컬 증거다. 회차 03 head `caace03645fb57454331fc3be8eabee3da448836`의 push [46075778210](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46075778210)와 pull_request [46075782846](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46075782846)도 success였고, 그 실행 역시 intelligence 시험을 실행하지 않았다.
Artifact 파일명·해시·재생성 명령(해당 시): 이 모듈은 APK를 만들지 않는다. JUnit XML은 [junit-r04](junit-r04)에 있다. 재실행은 `.\gradlew -p modules/intelligence clean test --rerun-tasks`.
정상/실패/경계/회귀 시험 증거: 충전 참 다음의 생략과 신선한 10%는 축 `CHARGING`, 포커스 `POWER`, 품질 `BALANCED`, 모션 허용, 입자 거짓, `graphicsPowerLimited` 참, 공개 10, `POWER_LOW`와 `POWER_CHARGING`이다. 디바운스 30초와 문서 후보 유지에서 10초의 10%는 축 `NORMAL`, 보류 `LOW`, 포커스 `POWER`, 입자 거짓, 모션 허용, 품질 `BALANCED`, 공개 10이다. 60초에는 축 `LOW`, Eco, 모션과 입자 거짓이다. revision `Long.MAX_VALUE`의 모션 감소는 `deliveredIntent()`가 있고 revision은 최댓값이며 초안 품질 이름은 `BALANCED`이고 이유에 `MOTION_REDUCTION`이 있다. 같은 상한의 신선한 10%는 축 `NORMAL`, 포커스 `POWER`, 입자 거짓, 모션 허용, 공개 배터리는 이전 80, `REVISION_EXHAUSTED`다. 그 뒤 모션 감소를 끄는 입력은 이전 상태 객체와 같은 `LimitReached`이고 `deliveredIntent()`는 null이다. 상한의 만료 배터리는 null, 강수 70, `DEGRADED`, `STALE_IGNORED`, 축 `NORMAL`이다. 상한의 권한 철회 강수는 null, 배터리 40, `DENIED_IGNORED`다. 유지 60초에서 경보 해제 대기 중 10초의 충전 예외는 날씨 `ALERT`와 전원 `CHARGING`이고, 60초에는 날씨 `NORMAL`, 전원 `CHARGING`이다. 디바운스 30초에서 1초에 시작한 저전력은 20초의 활동 변경 뒤에도 `NORMAL`이고, 40초에 `LOW`가 되며 활동은 `REST`, 보류는 `ACTIVE`다. 1초 시점의 입자는 이미 거짓이다. 회차 03까지의 47개와 도메인 81개는 다시 통과했다.
검사 도구의 실패 검출 시험: 수정 전 재현 4건이 실패했다. SourceScanTest는 `Instant.now(`와 `import java.net`을 실패로 보고, 본소스에서는 보고하지 않는다. 독립 CI 초안은 `TEST-*.xml`이 없거나 개별 `tests`가 0이거나 기대 수량과 다르면 실패한다. 그 초안은 실행하지 않았다. 공통 bootstrap의 성공은 이 검사의 성공이 아니다.
실기기 및 성능 시험 미실시 이유: 지시 범위 밖이고 연결된 기기가 없다. B-002는 유지된다. 임계값은 실측 전 후보로 남긴다.

### 독립 CI 제안

공통 `bootstrap.yml`은 수정하지 않았다. 최신 main의 워크플로도 이 회차에서 수정하지 않았다. 총괄이 별도 워크플로로 통합할 때 필요한 명령은 다음 둘이다.

```text
./gradlew -p modules/intelligence test --rerun-tasks --no-daemon
./gradlew -p modules/domain test --rerun-tasks --no-daemon
```

설정 변경안은 실행되지 않는 [modules/intelligence/docs/CI_PROPOSAL.md](../../../modules/intelligence/docs/CI_PROPOSAL.md)에 있다. 회차 04에서 점검한 내용은 다음이다. `push`는 `main`의 같은 경로 필터에서 실행하고 `workflow_dispatch`도 있다. `pull_request`와 같은 경로 필터다. Python 집계는 `TEST-*.xml`만 본다. 다른 XML이 수량을 늘리거나 빈 결과를 숨기지 못한다. intelligence는 파일 7개, 시험 52개, 실패 0, 오류 0, 건너뜀 0이 아니면 실패한다. domain은 파일 7개, 시험 81개, 실패 0, 오류 0, 건너뜀 0이 아니면 실패한다. XML이 없거나 한 파일의 `tests`가 0이면 실패한다. 52는 회차 03의 47개에 `Round04Test` 5개를 더한 수량이다. 81은 유지한다. 수량을 낮춰 미발견 시험을 통과시키지 않는다. concurrency 그룹은 `intelligence-kotlin-${{ github.ref }}`이고 `cancel-in-progress`는 true다. 이 초안은 실행하지 않는다. 공통 bootstrap의 concurrency 그룹 `aura-bootstrap-${{ github.ref }}`도 `cancel-in-progress`가 true다. 같은 브랜치의 나중 push는 이전 push를 취소할 수 있다. pull_request ref는 다르므로 그 두 이벤트는 서로 취소하지 않는다. 공통 bootstrap의 성공은 이 모듈 시험의 성공이 아니다. 루트 `settings.gradle.kts`에는 이 모듈을 넣지 않는다.

### 의존성

회차 01과 같다. `kotlin-stdlib` 2.4.21, `annotations` 13.0, 도메인 프로젝트 치환, `kotlin-test` 2.4.21, `kotlin-test-junit5` 2.4.21, JUnit Jupiter 5.10.1, JUnit Platform 1.10.1, `opentest4j` 1.3.0. Foojay 1.0.0은 settings 플러그인이다. Android SDK와 네트워크 클라이언트는 없다.

## 구현 후 검토

검토 유형(자기 재검토 / 다른 에이전트 / 사람): 자기 재검토. 독립 에이전트와 사람 검토는 NOT RUN. `0161cf7`의 `Machine.kt`, `Round04Test.kt`, 수정한 기존 시험 4곳, 모듈 계약, 가정, CI 제안을 시험 결과와 다시 대조했다.

검토 대상 diff 및 SHA: `0161cf7bb1bd9c7a3c18760b0481208d39e5b0ca`. intelligence 8개 파일, 428삽입, 122삭제.

| 결함 ID | 심각도 | 위치·재현 | 증거 | 수정/이관 | 재검증 |
|---|---|---|---|---|---|
| GB02-AUD-07 | P1, 표현 분리 | 충전 유지 중 신선한 낮은 배터리가 장식을 유지 | 재현 로그 `expected POWER but was DECORATIVE` | 축은 `CHARGING`. 포커스 `POWER`, 입자 거짓. Eco와 모션 차단은 확정된 `LOW`만 | 충전 유지 시험과 Round04 첫 시험 PASS |
| GB02-R04-HOLD | P1, 보호 지연 | 그래픽 제한이 디바운스와 최소 유지를 기다림 | 재현 로그 `expected POWER but was DECORATIVE` | 신선한 낮은 배터리는 즉시 제한. 축 확정은 기존 기한 | `lowPowerGraphicsDoNotWaitForDebounceOrHold` PASS |
| GB02-R04-REV | P1, revision | 상한에서 보호와 만료 거두기가 `LimitReached`로 버려짐 | `Expected Advanced, actual LimitReached` | `deliveredIntent()`가 같은 revision의 보호를 전달. `Unusable` 숫자만 거둠 | 상한 두 시험과 회차 02 상한 시험 PASS |
| GB02-R04-CLOCK | P1, 공유 타이머 | 다른 축의 확정이 날씨 유지를 다시 시작 | `expected NORMAL but was ALERT` | 축별 확정 시각과 보류 시작. 우회 범위는 회차 03과 같음 | `anotherAxisDoesNotRestartDebounceOrHold` PASS |
| GB02-AUD-08 | P2, CI | 제안 수량이 47에 머무르고 XML 글롭이 넓음 | 회차 03 제안은 6파일 47시험 | 제안만 7파일 52시험과 `TEST-*.xml`로 갱신. 공통 워크플로는 수정하지 않음 | NOT RUN |

남은 구현 결함은 없다. 상한에서 보호가 늘지 않고 숫자를 거둘 근거가 없는 입력은 이전 상태 객체를 그대로 돌려준다. 상한에서 이미 켜진 그래픽 제한과 모션 감소와 항상 표시는 끄지 않는다. 상한 아래의 역전은 숫자를 공개하지 않고 `CLOCK_INVERSION`을 남긴다. `Round04ReproTest`는 저장소에 없다.

## 종료 게이트

| 게이트 | 결과 | 증거 또는 미적용 사유 |
|---|---|---|
| G0 사전 검증 | PASS | 최신 main `55721ea`, 병합 `8177073`, 착수 전 PR HEAD `58e9f9f`, 소유 경로 유지, 제품 NO-GO, 도메인과 `.github` diff 없음 |
| G1 구현/요구사항 | PASS | AUD-07 분리, 즉시 그래픽 제한, 상한 `deliveredIntent`, 만료·철회 거두기, 축별 타이머. CI는 제안만 |
| G2 검증 도구 | PASS | 수정 전 4 FAIL, SourceScan, 기존 정책 거절 |
| G3 시험/회귀 | PASS | 52 PASS, 도메인 81 PASS. 기존 47개 메서드 유지. 모듈 GitHub CI는 NOT RUN |
| G4 분야별 검증 | PASS, 데이터/FSM 범위 | 그래픽·성능 실측·건강 네트워크는 NOT RUN |
| G5 별도 재검토 | PASS, 자기 재검토 | 독립 검토자는 NOT RUN. 네 재현은 수정 전 실패 후 수정 |
| G6 증거 및 판정 | PASS | 코드 SHA `0161cf7`. 공통 CI head `27e8aa6`, push 46079624268과 PR 46079625581 모두 success. 각 job 26 steps success. intelligence 시험은 그 워크플로에 없다. 제품 GO로 올리지 않음 |
| G7 문서/재개 | PASS, 제한 적용 | 중앙 STATUS/WORK_LOG/BLOCKERS는 지시대로 수정하지 않았다. 제안만 아래에 둔다 |

최종 작업 판정 및 이유: 독립 모듈 제출 GO. AUD-07을 축 추가 없이 해결했다. 저전력 장식 제한은 디바운스와 최소 유지를 기다리지 않는다. 상한 보호는 `deliveredIntent()`로 같은 revision에 전달되고, 만료·권한 철회 숫자는 그 경로에서 거두어진다. 센서 축의 기한은 서로 다시 시작하지 않는다. 기존 intelligence 47개와 도메인 81개를 유지했다. 공통 CI와 main은 바꾸지 않았다. 총괄 통합 판정은 이 보고서의 권한이 아니다.
제품 출시 판정(별도): NO-GO. 실기기, 실공급원, 그래픽, 확정 임계값이 없다.
미해결 장애 / 이관 및 해결 조건: B-002/B-003/B-004/B-005/B-006/B-007/B-008 유지. PR #3 통합 HOLD 유지. 임계값과 이유 코드 어휘는 승인 전 후보다. 새 차단은 만들지 않았다.

다음 작업 ID, 읽을 문서, 첫 행동·명령, 기대 결과: 총괄이 PR #3을 검토한다. 먼저 이 보고서와 `modules/intelligence/docs/INTERFACE_CONTRACT.md`, `modules/intelligence/docs/CI_PROPOSAL.md`를 읽는다. main 병합과 공통 워크플로 수정은 하지 않는다. 기대 결과는 총괄의 통합 판정이며, 제품 출시 GO가 아니다. 다음 안전한 중앙 행동은 STATUS에 적힌 R02 보완 CI `46078480317` 검증이다.

STATUS / WORK_LOG / BLOCKERS / evidence / 정본 문서 갱신 여부: 회차 04 evidence와 모듈 문서만 갱신했다. 회차 01 `REPORT.md`, 회차 02 `REPORT-02.md`, 회차 03 `REPORT-03.md`는 유지했다. 중앙 문서 제안은 적용하지 않았다.

중앙 문서 제안:

- STATUS: 다음 안전한 행동인 R02 보완 CI `46078480317` 검증을 빼지 않는다. GB-02 PR #3에 회차 04가 추가됐고 로컬 intelligence 52 PASS, 도메인 81 PASS, 실기기와 모듈 CI는 NOT RUN, 제품 NO-GO, PR은 미병합이라고 한 줄 추가할 수 있다.
- WORK_LOG: 같은 한 줄을 추가할 수 있다.
- BLOCKERS: 변경하지 않는다.
- DATA_INTELLIGENCE: 변경하지 않는다. 후보 규칙은 모듈 가정에 있다.
- agent-orders README: 총괄이 PR을 받은 뒤에만 GB-02 상태를 검토 중으로 바꿀 수 있다. 통합 HOLD를 이 보고서가 해제하지 않는다.
- `.github/workflows`: 변경하지 않는다. 독립 워크플로 초안만 `modules/intelligence/docs/CI_PROPOSAL.md`에 있다.

저장소 반영 확인(커밋/브랜치; 자기 참조 SHA 금지): 구현 커밋 `0161cf7bb1bd9c7a3c18760b0481208d39e5b0ca`, 브랜치 `agent/grok/GB-02`. 이 보고서 커밋은 `modules/intelligence` 소스를 바꾸지 않아야 한다. 그 확인은 보고서 커밋 뒤 `git diff 0161cf7bb1bd9c7a3c18760b0481208d39e5b0ca -- modules/intelligence`가 비어 있는지로 한다.
