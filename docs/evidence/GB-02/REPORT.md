# 작업 보고서 — GB-02 / 회차 01

상태: GO (독립 모듈 제출). 제품 출시 NO-GO. 총괄 통합은 대기.
일자, 작업자, 검토자: 2026-11-28, Grok Build, 자기 재검토. 독립 검토자 없음.
기준 브랜치/HEAD: 작업 브랜치 `agent/grok/GB-02`. 착수 시점의 `origin/main`은 `383915b708500381cd9c87831ee0fbdf03477711`였다. 커밋 전에 `50937487e790323daf947d5a6b10b912302d635c`로 fast-forward 했다. main에 병합하지 않았다.
PRE-FLIGHT: 최신 `origin/main` `50937487e790323daf947d5a6b10b912302d635c`에서 `docs/STATUS.md`, `docs/operations/agent-orders/README.md`, `docs/operations/agent-orders/GB-02.md`, `docs/operations/BLOCKERS.md`의 신규 절을 확인했다. 같은 작업에서 `docs/DATA_INTELLIGENCE.md`, `docs/PERFORMANCE.md`, `docs/QUALITY_GATES.md`, `docs/operations/VERIFICATION_PROTOCOL.md`, `modules/domain` 계약과 빌드 문서를 읽었다. 활성 작업은 GPT-04 PARTIAL, AG-01-R04, GB-02다. GB-02 지시서는 READY다. 제품 출시 NO-GO, 공식 WO GO 0/38, GPT 묶음 3/12. B-011의 현재 pin 불일치는 해결로 적혀 있고 B-002/B-003/B-004/B-005/B-006/B-007/B-008은 유지된다. GPT04-D1과 GPT04-D2는 해결, AM/PM 전체 CI는 별도 확인 대상이다. `383915b..5093748`의 `modules/domain` diff는 비어 있다. PRE-FLIGHT PASS. 제품 출시 NO-GO는 유지한다.
검증 대상 코드 SHA: `779f8aaeaaf709331758e3640b8e364e0d017d94`
관련 요구사항 / WO / GPT ID: R-12, R-17, R-22의 상태 머신 범위. GPT-07과 WO-21/22/23의 정식 선행 조건은 해제하지 않는다.
관련 정본 문서: `docs/operations/agent-orders/GB-02.md`, `docs/DATA_INTELLIGENCE.md`, `docs/PERFORMANCE.md`, `modules/domain/docs/INTERFACE_CONTRACT.md`
작업 목표, 포함/제외 범위: 상황 우선순위, 히스테리시스, 디바운스, 긴급 전환, 데이터 신뢰도, 절전·모션 정책을 순수 Kotlin 상태 머신으로 구현한다. 수정은 `modules/intelligence/**`와 `docs/evidence/GB-02/**`만이다. 도메인 계약, 루트 Gradle, WFF, CI, 중앙 STATUS/WORK_LOG/BLOCKERS, 다른 에이전트 파일은 제외한다.
선행 조건 및 이전 실패: GB-01은 main에 통합되어 있다. 도메인 시험 81개는 유지한다. GB01-E1 때문에 ASCII worktree를 사용한다.
변경 파일 소유권 / 변경 영향: 소유 경로만 추가했다. 작업 트리는 `C:\Users\scarl\AppData\Local\Temp\aura-gb02-wt`, 브랜치 `agent/grok/GB-02`. fast-forward로 들어온 GPT-04 파일은 수정하지 않았다.
참조 자료(정확한 URL·버전·확인일): 2026-11-28. Kotlin 2.4.21, https://kotlinlang.org/docs/releases.html, Apache-2.0, https://github.com/JetBrains/kotlin/blob/v2.4.21/license/LICENSE.txt. JUnit Jupiter 5.10.1 / Platform 1.10.1, EPL-2.0, https://junit.org/junit5/. opentest4j 1.3.0. JetBrains annotations 13.0, Apache-2.0. Gradle Wrapper 9.3.1, Apache-2.0. Foojay toolchain resolver 1.0.0, Apache-2.0, https://github.com/gradle/foojay-toolchains. 의존 버전은 [test-runtime-classpath.log](test-runtime-classpath.log)와 같다.
가정 / 위험 / 승인 필요 사항: [modules/intelligence/docs/ASSUMPTIONS.md](../../../modules/intelligence/docs/ASSUMPTIONS.md)의 GB02-A1~A24. 15/20, 70/50, 60초는 제품 상수가 아니다. 디바운스 후보 기본값은 0이다. 전원 축에 UNKNOWN을 추가하지 않았다.
성공 기준 / 롤백 방법: clean JDK 17 시험 실패 0, 도메인 81개 유지, 잘못된 관측을 신선한 값이나 0으로 올리지 않는 회귀가 있다. 롤백은 이 브랜치를 병합하지 않으면 된다. main은 변경하지 않았다.

## 구현 및 결정

| 파일·모듈 | 변경 및 이유 | 관련 요구사항 | 확인할 영향 |
|---|---|---|---|
| `modules/intelligence` Gradle | 도메인을 `includeBuild`로만 연결한다. 루트 설정은 그대로다. | R-22 | `:apps:watchface`를 구성하지 않음 |
| `Policy.kt` | 문서 후보를 호출자가 교체할 수 있는 값으로 둔다. | R-12 | 잘못된 구간과 음수 시간은 거절 |
| `Gate.kt` | 도메인 `deriveStatus`와 단위 검사를 통과한 신선 VALID만 사용한다. | R-17 | 단위 환산과 0 치환 없음 |
| `Machine.kt` | 우선순위, 히스테리시스, 유지, 긴급·충전 예외, 모션과 품질 후보를 한 전이로 계산한다. | R-12 | 도메인 초안 어휘를 얼리지 않음 |
| `Axes.kt` | 명세에 있는 축 이름만 둔다. 품질 이름은 Balanced/Eco/AOD 후보다. | R-12 | Ultra는 선택하지 않음 |
| 시험 | 정상, 경계, 충돌, 반복, 역전, 잘못된 값, 충전·긴급, 오프라인, 모션 감소를 고정한다. | R-22 | 기존 도메인 시험은 수정하지 않음 |
| 모듈 문서 | 계약, 가정, 빌드 명령을 모듈 안에 둔다. | R-22 | 중앙 문서는 수정하지 않음 |

결정, 대안, 기각 사유 및 ADR: 전원 축의 UNKNOWN은 명세에 없어 거절했다. 사용할 수 없는 배터리는 직전 축을 유지하고 숫자는 공개하지 않는다. 날씨와 활동의 UNKNOWN은 명세에 있으므로 유지한다. 품질 이름 AMBIENT 대신 성능 문서의 AOD를 쓴다. 긴급은 경보로 들어갈 때만이다. 충전 예외는 신선한 충전 참의 진입과 신선한 충전 거짓의 해제다. 센서 세 축은 한 타이머를 공유한다. 밝기·연결·사용자 모드는 그 타이머를 재설정하지 않는다. revision은 축뿐 아니라 공개 내용이 바뀔 때도 증가한다. 같은 내용의 반복은 증가하지 않는다. ADR은 만들지 않았다.

시도한 접근과 실패 원인: 첫 컴파일은 `classifiedValue` 확장 함수를 import하지 않아 실패했다. import 후 같은 시험이 통과했다. 전원 UNKNOWN과 AMBIENT 이름, revision이 공개 내용 변경을 놓치던 경로는 증거를 남긴 clean 실행 전에 고쳤다.

사용법, 환경, 재현 명령, 설정 변경: [modules/intelligence/docs/BUILD.md](../../../modules/intelligence/docs/BUILD.md). ASCII worktree에서 `.\gradlew -p modules/intelligence clean test --rerun-tasks --offline`와 `.\gradlew -p modules/domain test --rerun-tasks --offline`.

## 요구사항 및 검증 추적표

| 요구사항/완료 기준 | 구현 파일·경로 | 시험 ID | 예상 결과 | 실제 결과 | 증거·SHA | 판정 |
|---|---|---|---|---|---|---|
| 우선순위 CRITICAL > POWER > EXERCISE > WEATHER > CONTEXT > DECORATIVE | `Machine.kt` `focusOf` | MachineTest 우선순위 | 경보가 저전력·운동·강수·상황보다 앞선다. 충전은 POWER가 아니다. | PASS | 779f8aa | PASS |
| 히스테리시스 15/20, 70/50 | `Policy.kt`, `lowPower`, `precipActive` | MachineTest 경계 | 진입 이하·이상과 해제 경계가 갈리고, 사이 구간은 직전 상태만 유지한다. ALERT는 PRECIP가 아니다. | PASS | 779f8aa | PASS |
| 디바운스와 최소 유지 60초 | `step` | MachineTest 유지·디바운스 | 59초는 유지, 60초에 반영. 디바운스 끝점에서 반영. 밝기 변경은 유지 시각을 재설정하지 않는다. | PASS | 779f8aa | PASS |
| 긴급·충전 예외 | `step` | MachineTest 긴급·충전 | 유지 중에도 ALERT 진입과 충전 진입·해제는 즉시 반영된다. 저전력은 예외가 아니다. | PASS | 779f8aa | PASS |
| STALE/UNAVAILABLE/DENIED/ERROR/UNDECLARED와 잘못된 값 | `Gate.kt` | GateTest, MachineTest 나쁜 값 | 신선한 숫자나 0으로 올리지 않는다. 운동으로 추론하지 않는다. | PASS | 779f8aa | PASS |
| 오프라인, 모션 감소, 저전력에서 숫자·시간 유지 | `intentFor` | MachineTest 절전·모션 | 입자는 끄고 신선한 강수 숫자와 timeKept는 유지한다. | PASS | 779f8aa | PASS |
| 시계 역전과 불변 입력 | `step` | MachineTest 역전 | 축을 유지하고 숫자를 공개하지 않는다. 입력 Observation은 그대로다. | PASS | 779f8aa | PASS |
| 도메인 계약 유지 | 비수정 `modules/domain` | GB02-DOMAIN | 기존 81 PASS | 81 PASS / 0 FAIL / 0 SKIP / 0 ERROR | 779f8aa 작업 트리. domain diff 없음 | PASS |
| 실기기, 실공급원, 그래픽 | 없음 | 없음 | 실행하지 않음 | NOT RUN | 없음 | NOT RUN |

## 검증 결과

| 시험 ID | 필수/선택 | 종류 | 명령·대상 버전 | 기대 결과 | 실제 결과 | 판정 | 로그 |
|---|---|---|---|---|---|---|---|
| GB02-UNIT | 필수 | clean JDK 17 | `gradlew -p modules/intelligence clean test --rerun-tasks --offline`, toolchain 17 | 실패 0 | 28 PASS, 0 FAIL, 0 SKIP, 0 ERROR. BUILD SUCCESSFUL in 32s. XML `2026-11-27T20:50:02Z` | PASS | [intelligence-test-summary.log](intelligence-test-summary.log), [junit](junit) |
| GB02-DOMAIN | 필수 | 회귀 | `gradlew -p modules/domain test --rerun-tasks --offline` | 81 PASS | 81 PASS, 0 FAIL, 0 SKIP, 0 ERROR. BUILD SUCCESSFUL in 19s | PASS | [domain-regression-summary.log](domain-regression-summary.log) |
| GB02-SCAN | 필수 | 실패 주입 | SourceScanTest | 심은 `Instant.now(`와 네트워크 import를 잡고, 본소스에는 없다 | PASS | PASS | 같은 intelligence 로그 |
| 실기기, 네트워크 공급원, 그래픽, OS 절전 측정 | 제외 | 실기기 | 미실행 | NOT RUN | NOT RUN | NOT RUN | 없음 |
| intelligence용 GitHub CI | 제외 | CI | `.github` 미수정 | 이 워크플로에는 없음 | NOT RUN | NOT RUN | 없음 |

환경 및 도구 버전: Windows. 테스트 JVM은 Eclipse Temurin 17.0.20.1+1, `C:\Users\scarl\.jdks\temurin-17`. 로그 한 줄은 `TEST_JVM version=17 vendor=Eclipse Temurin path=C:\Users\scarl\.jdks\temurin-17`. Gradle을 띄운 JVM은 Adoptium 21.0.5.11. Kotlin 2.4.21. Gradle 9.3.1. ASCII worktree `C:\Users\scarl\AppData\Local\Temp\aura-gb02-wt`.
총 시험 수, PASS, FAIL, SKIP, NOT RUN, PENDING: intelligence 28 PASS / 0 FAIL / 0 SKIP / 0 ERROR. 구성은 Gate 4, Machine 17, Policy 5, SourceScan 2. 도메인 회귀 81 PASS / 0 FAIL / 0 SKIP / 0 ERROR. 실기기·실공급원·그래픽·모듈 CI는 NOT RUN.
CI 실행 ID / head SHA / job / step: head `930ffd233538bf9bebb3c111725fa514f27e1dd2`. push [46066982767](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46066982767), job `140734564245`, conclusion success. pull_request [46066988024](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46066988024), job `140734582870`, 같은 head, conclusion success. 두 실행 모두 wrapper, 구조 검사, validation tool regression, SDK 설치와 확인, 공식 WFF validation, debug APK build, APK 내용, 메모리 평가, debug 서명, artifact 업로드가 success였다. 이 워크플로는 `modules/intelligence` 시험을 실행하지 않는다. 그 28개는 로컬 clean 증거다.
Artifact 파일명·해시·재생성 명령(해당 시): 이 모듈은 APK를 만들지 않는다. JUnit XML은 [junit](junit)에 있다. 재실행은 `.\gradlew -p modules/intelligence clean test --rerun-tasks`.
정상/실패/경계/회귀 시험 증거: 15는 LOW, 19는 직전이 LOW일 때만 LOW, 20은 NORMAL. 70은 PRECIP, 50은 NORMAL, 60은 직전 ALERT 다음에서 PRECIP가 아니다. 59초는 유지되고 60초에 반영된다. 경보 진입과 충전 전환은 1초 뒤에도 반영된다. 만료 시각과 같은 기준 시각, STALE, DENIED, ERROR, UNAVAILABLE, NaN, 스케일 밖, 다른 단위, `commute`/`exercise`/`WORK` 토큰은 신선한 운동이나 0이 아니다. 오프라인은 CONTEXT다. 저전력은 입자를 끄고 신선한 강수 숫자를 공개한다. 시계 역전은 숫자를 공개하지 않는다. 첫 revision은 1이다.
검사 도구의 실패 검출 시험: SourceScanTest는 `Instant.now(`와 `import java.net`이 들어 있는 문자열을 실패로 보고, 빈 시계 호출은 보고하지 않는다. 정책 거절 시험은 진입과 해제가 같은 정책을 `PolicyRejected`로 끝낸다. 사용할 수 없는 배터리 시험은 공개 값이 null인지 확인한다.
실기기 및 성능 시험 미실시 이유: 지시 범위 밖이고 연결된 기기가 없다. B-002는 유지된다. 임계값은 실측 전 후보로 남긴다.

### 의존성

`testRuntimeClasspath`는 mavenCentral이다. `kotlin-stdlib` 2.4.21, `annotations` 13.0, 도메인 프로젝트 치환, `kotlin-test` 2.4.21, `kotlin-test-junit5` 2.4.21, `junit-jupiter-api` 5.10.1, `junit-jupiter-engine` 5.10.1, `junit-platform-engine` 1.10.1, `junit-platform-commons` 1.10.1, `junit-platform-launcher` 1.10.1, `opentest4j` 1.3.0. Foojay 1.0.0은 settings 플러그인이다. Android SDK와 네트워크 클라이언트는 없다. 조회일 2026-11-28.

## 구현 후 검토

검토 유형(자기 재검토 / 다른 에이전트 / 사람): 자기 재검토. 독립 에이전트와 사람 검토는 NOT RUN. 구현 설명만으로 판정하지 않고 `779f8aa`의 소스와 시험을 다시 대조했다.

검토 대상 diff 및 SHA: `779f8aaeaaf709331758e3640b8e364e0d017d94`, `modules/intelligence`와 `docs/evidence/GB-02`.

| 결함 ID | 심각도 | 위치·재현 | 증거 | 수정/이관 | 재검증 |
|---|---|---|---|---|---|
| GB02-D1 | P0 후보, 컴파일 | `Gate.kt`가 `classifiedValue`를 import하지 않음 | 첫 `compileKotlin` 실패 | import와 `Reading<T>`로 수정 | clean 28 PASS |
| GB02-D2 | P1 후보, 어휘 | 전원 축 UNKNOWN은 명세에 없음 | `DATA_INTELLIGENCE.md` 축 목록 | 축에서 제거. 나쁜 배터리는 직전 값을 유지하고 숫자를 숨김 | MachineTest 나쁜 값 PASS |
| GB02-D3 | P2, 어휘 | 품질 이름 AMBIENT는 성능 문서 후보와 다름 | `PERFORMANCE.md` Ultra/Balanced/Eco/AOD | `AOD`로 변경. Ultra는 선택하지 않음 | 저전력·항상 표시 시험 PASS |
| GB02-D4 | P1 후보, revision | 축이 그대로면 저하·모션 변경도 같은 revision | 도메인의 오래된 revision 배제 | 공개 내용이 바뀔 때 revision 증가. 동일 반복은 유지 | `presentationChangesBumpRevisionWhenAxesStay` PASS |

남은 결함은 없다. `assemble`이 만드는 자리표시 Emission은 `finish`가 바꾸기 전에 반환되지 않는다. 호출 결과는 시험이 본 공개 내용과 같다.

## 종료 게이트

| 게이트 | 결과 | 증거 또는 미적용 사유 |
|---|---|---|
| G0 사전 검증 | PASS | 최신 main `5093748`, GB-02 READY, 제품 NO-GO, 도메인 diff 없음 |
| G1 구현/요구사항 | PASS | 추적표와 모듈 계약. 미구현은 실기기·실공급원·그래픽 |
| G2 검증 도구 | PASS | 심은 시계·네트워크 토큰, 정책 거절, 0 치환 금지 |
| G3 시험/회귀 | PASS | 28 PASS, 도메인 81 PASS. 모듈 GitHub CI는 NOT RUN |
| G4 분야별 검증 | PASS, 데이터/FSM 범위 | 그래픽·성능 실측·건강 네트워크는 NOT RUN |
| G5 별도 재검토 | PASS, 자기 재검토 | 독립 검토자는 NOT RUN. GB02-D1~D4는 증거 실행 전 수정 |
| G6 증거 및 판정 | PASS | 코드 SHA `779f8aa`. 공통 CI head `930ffd2`, push 46066982767과 PR 46066988024 모두 success. 제품 GO로 올리지 않음 |
| G7 문서/재개 | PASS, 제한 적용 | 중앙 STATUS/WORK_LOG/BLOCKERS는 지시대로 수정하지 않았다. 제안만 아래에 둔다 |

최종 작업 판정 및 이유: 독립 모듈 제출 GO. 요구한 상태 머신과 로컬 시험이 있고, 도메인 계약 파일을 바꾸지 않았다. 총괄 통합 판정은 이 보고서의 권한이 아니다.
제품 출시 판정(별도): NO-GO. 실기기, 실공급원, 그래픽, 확정 임계값이 없다.
미해결 장애 / 이관 및 해결 조건: B-002/B-003/B-004/B-005/B-006/B-007/B-008 유지. 임계값과 이유 코드 어휘는 승인 전 후보다. 새 차단은 만들지 않았다.

다음 작업 ID, 읽을 문서, 첫 행동·명령, 기대 결과: 총괄이 이 PR을 검토한다. 먼저 `docs/evidence/GB-02/REPORT.md`와 `modules/intelligence/docs/INTERFACE_CONTRACT.md`를 읽는다. 통합 전에는 `modules/intelligence`를 루트 설정에 넣지 않는다. 기대 결과는 총괄의 통합 판정이며, 제품 출시 GO가 아니다.

STATUS / WORK_LOG / BLOCKERS / evidence / 정본 문서 갱신 여부: evidence와 모듈 문서만 갱신했다. 중앙 문서 제안은 적용하지 않았다.

중앙 문서 제안:

- STATUS: 다음 안전한 행동을 GPT-04에서 빼지 않는다. GB-02 PR이 열렸고 로컬 28 PASS, 도메인 81 PASS, 실기기는 NOT RUN, 제품 NO-GO라고 한 줄 추가할 수 있다.
- WORK_LOG: 같은 한 줄을 추가할 수 있다.
- BLOCKERS: 변경하지 않는다.
- DATA_INTELLIGENCE: 변경하지 않는다. 후보 규칙은 모듈 가정에 있다.
- agent-orders README: 총괄이 PR을 받은 뒤에만 GB-02 상태를 검토 중으로 바꿀 수 있다.

저장소 반영 확인(커밋/브랜치; 자기 참조 SHA 금지): 구현 커밋 `779f8aaeaaf709331758e3640b8e364e0d017d94`, 브랜치 `agent/grok/GB-02`. 이 보고서 커밋은 `modules/intelligence` 소스를 바꾸지 않아야 한다. 그 확인은 보고서 커밋 뒤 `git diff 779f8aa -- modules/intelligence`가 비어 있는지로 한다.
