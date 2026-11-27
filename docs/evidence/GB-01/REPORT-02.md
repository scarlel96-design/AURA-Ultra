# 작업 보고서 — GB-01 / 회차 02

상태: GO (독립 모듈 보완). 제품 출시 NO-GO. 총괄 통합은 대기.
일자, 작업자, 검토자: 2026-11-27, Grok Build, 자기 재검토. 독립 검토자 없음.
기준 브랜치/HEAD: 작업 브랜치 `agent/grok/GB-01`. 최신 `origin/main`은 `b5dd320c0718f9451b9749637c83db22584664b0`. 이 브랜치에 main을 병합하지 않았다. 회차 시작 시점의 브랜치 HEAD는 `d7e60c06c84809676162c37a0f8b19511518f68c`였다.
PRE-FLIGHT: `origin/main` `b5dd320c0718f9451b9749637c83db22584664b0`에서 AGENTS.md, docs/STATUS.md, docs/operations/RESUME_PROTOCOL.md, PROJECT_INVARIANTS.md, TASK_RECORD_PROTOCOL.md, VERIFICATION_PROTOCOL.md, TASK_REPORT_TEMPLATE.md, GPT_EXECUTION_PLAN.md, BLOCKERS.md, WORK_LOG.md, agent-orders/README.md, agent-orders/GB-01.md, agent-orders/GB-01-R02.md, docs/evidence/OPS-04/REPORT.md를 읽었다. 활성 작업은 GPT-03 PARTIAL, GB-01 보완, AG-01 원격 증거 대기다. 차단은 B-002/B-003/B-004/B-005/B-006/B-007/B-008 유지, B-001/B-010 해결 유지. 제품 코드 성공 CI는 [46002470824](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46002470824), SHA `f284b1bd69a767ef0f7285449fe7c45f05895e53`. GPT-03 후보 CI [46006560829](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46006560829) success. PRE-FLIGHT PASS. 제품 출시 NO-GO는 유지한다.
검증 대상 코드 SHA: `46caded706c54f7eb501dd5d8385fc52bca961b1`
관련 요구사항 / WO / GPT ID: R-17, R-22의 계약 보정. R-04, R-12, R-21은 회차 01 범위로 유지. GPT-07 / WO-17~23의 선행 조건은 해제하지 않는다.
관련 정본 문서: docs/operations/agent-orders/GB-01-R02.md, docs/evidence/OPS-04/REPORT.md, docs/DATA_INTELLIGENCE.md, modules/domain/docs/INTERFACE_CONTRACT.md, modules/domain/docs/ASSUMPTIONS.md
작업 목표, 포함/제외 범위: 총괄 검토가 지적한 단위 문자열, 배타적 정수 범위, 극값, 검증 파이프라인을 재현하고 확인된 결함만 고친다. 기존 70개 시험을 유지하고 회귀 시험을 추가한다. JDK 17 clean 시험, JUnit XML, 비ASCII 경로 원인, Kotlin CI 최소 제안을 기록한다. 신규 제품 기능, 루트 Gradle, `.github`, 중앙 STATUS/WORK_LOG/BLOCKERS, main 병합은 제외한다.
선행 조건 및 이전 실패: 회차 01 코드 `098dd35e1d7111a5ece9f8417142cf1c6ecc2fd3`, 로컬 70 PASS. 총괄은 독립 Kotlin 재실행을 하지 않았고 통합을 보류했다. GB01-E1은 환경 제한으로 남아 있었다.
변경 파일 소유권 / 변경 영향: `modules/domain/**`, `docs/evidence/GB-01/**`. 작업 트리는 `C:\Users\scarl\AppData\Local\Temp\aura-gb01-wt`, 브랜치 `agent/grok/GB-01`. 공유 체크아웃의 AG-01 파일은 수정하지 않았다.
참조 자료(정확한 URL·버전·확인일): 2026-11-27. Kotlin 2.4.21, https://kotlinlang.org/docs/releases.html, Apache-2.0, https://github.com/JetBrains/kotlin/blob/v2.4.21/license/LICENSE.txt. JUnit Jupiter 5.10.1 / Platform 1.10.1, EPL-2.0, https://junit.org/junit5/. opentest4j 1.3.0. JetBrains annotations 13.0, Apache-2.0. Gradle Wrapper 9.3.1, Apache-2.0. Foojay toolchain resolver 1.0.0, Apache-2.0, https://github.com/gradle/foojay-toolchains. 의존 버전은 아래 `testRuntimeClasspath` 출력과 같다.
가정 / 위험 / 승인 필요 사항: A13, A24, A25를 재현 결과에 맞게 고쳤다. A27은 인접 Double 열린 구간을 빈 범위로 거절하지 않는다는 미확정 정책이다. 단위 어휘, TTL 길이, 확률 스케일, FSM, applicationId는 승인하지 않았다.
성공 기준 / 롤백 방법: 재현된 결함이 회귀 시험으로 고정되고 clean JDK 17 시험이 실패 0이다. 기존 70개 시험과 host 40개 시험을 유지한다. 롤백은 이 커밋을 병합하지 않으면 된다. main은 변경하지 않았다.

## 구현 및 결정

| 파일·모듈 | 변경 및 이유 | 관련 요구사항 | 확인할 영향 |
|---|---|---|---|
| Validation.kt | 값이 있는 단위의 내부 공백과 비공백 ISO 제어 문자를 거절 | R-17 | 정상 토큰 `mm`, `°C`, `m/s`는 유지 |
| Constraints.kt | 표현 가능한 Long이 없는 배타 구간을 `RANGE_EMPTY`로 거절 | R-17 | 포함 극값과 인접한 유효 정수는 유지 |
| PipelineTest.kt, ValidationTest.kt | 재현 실패와 회귀. 기존 시험 메서드는 삭제하지 않음 | R-22 | 70개 유지, 11개 추가 |
| ASSUMPTIONS.md, INTERFACE_CONTRACT.md, BUILD.md | 확인된 규칙, 미확정 Double 구간, argfile 원인 | R-21, R-22 | 중앙 문서는 수정하지 않음 |
| CI_PROPOSAL.md | 공통 `.github`에 넣지 않는 최소 workflow 제안 | R-22 | 실행되지 않는 문서 |
| build.gradle.kts | 테스트 JVM 메타데이터를 로그에 남김 | R-22 | 판정 로직 변화 없음 |

결정, 대안, 기각 사유 및 ADR: 내부 공백은 기존 `UNIT_PADDED`로 보고한다. 비공백 제어 문자는 `UNIT_CONTROL`이다. 공백인 제어 문자는 `UNIT_BLANK` 또는 `UNIT_PADDED`다. 값이 null이면 단위 문자 검사는 하지 않는다. `classifiedValue`에 구조 검사와 TTL을 넣지 않았다. 표시 경로는 `applyRevision` 또는 `validateObservation`과 `deriveStatus`의 성공을 본다. `LongBounds.parse`만 빈 정수 구간을 거절한다. `NumericRange`의 인접 Double 열린 구간은 A27로 남긴다. ADR은 만들지 않았다.

시도한 접근과 실패 원인: 수정 전 새 fixture 11개 중 6개가 실패했다. `mm Hg`와 `mm\u000BHg`는 이슈가 없었고, `mm\u0000`도 이슈가 없었다. `(5, 6)`, `(Long.MAX_VALUE-1, Long.MAX_VALUE)`, 배타 하한 `Long.MAX_VALUE`, 배타 상한 `Long.MIN_VALUE`는 `LongBounds.parse`가 `Accepted`였다. 기대 단위가 그 문자열과 같아도 `deriveStatus`는 `Unchanged`였다. 비교식 자체는 빈 정수 구간의 값을 이미 모두 거절했다. 결함은 parse가 그 구간을 빈 범위로 알리지 않은 것이다. 포함 끝점 `Long.MIN_VALUE`와 `Long.MAX_VALUE`, 배타 이웃 정수 1과 9는 수정 전에도 통과했다. `DENIED`, `ERROR`, `STALE`, TTL 미선언은 수정 전 통합 fixture에서도 신선한 `VALID` 읽기로 바뀌지 않았다. 이 네 상태는 코드를 바꾸지 않았다.

사용법, 환경, 재현 명령, 설정 변경: [modules/domain/docs/BUILD.md](../../../modules/domain/docs/BUILD.md). ASCII worktree에서 `.\gradlew -p modules/domain clean test --rerun-tasks --offline`.

## 요구사항 및 검증 추적표

| 요구사항/완료 기준 | 구현 파일·경로 | 시험 ID | 예상 결과 | 실제 결과 | 증거·SHA | 판정 |
|---|---|---|---|---|---|---|
| 단위 내부 공백·제어 문자 | Validation.kt | ValidationTest 신규 5개 | 정상 토큰 수락, 내부 공백·제어 문자 거절 | 수정 전 3 FAIL, clean 후 PASS | 46caded | PASS |
| 배타 정수 빈 구간과 극값 | Constraints.kt | ValidationTest 신규 3개 | 빈 구간 `RANGE_EMPTY`, 유효 정수와 포함 극값 수락 | 수정 전 2 FAIL, clean 후 PASS | 46caded | PASS |
| rejected/denied/error/stale/TTL 미선언 | Freshness.kt, RevisionGate.kt, PipelineTest.kt | PipelineTest 신규 3개와 기존 FreshnessTest | 정상 신선 읽기로 승격되지 않음 | 상태 승격 2개는 수정 전 PASS. 오염 단위 1개는 수정 후 PASS | 46caded | PASS. `classifiedValue`는 TTL을 보지 않음 |
| 기존 70개 유지 | 기존 시험 | 회차 01 시험 메서드 | 삭제 0, 실패 0 | 수정 전 75 PASS 안에 포함, clean 81 PASS | 46caded | PASS |
| JDK 17 clean 재현 | modules/domain Gradle | GB01-UNIT-R02 | 실패 0, XML 보존 | 81 PASS / 0 FAIL / 0 SKIP / 0 ERROR | 46caded | PASS |
| host 40과 foundation | 비수정 | HOST-40, FOUNDATION | 기존 결과 유지 | 40 PASS, foundation PASS | 46caded worktree | PASS |
| 제품 통합, 실기기, Kotlin CI 실제 실행 | 없음. 제안만 작성 | 없음 | 실행하지 않음 | NOT RUN | CI_PROPOSAL.md | NOT RUN |

## 검증 결과

| 시험 ID | 필수/선택 | 종류 | 명령·대상 버전 | 기대 결과 | 실제 결과 | 판정 | 로그 |
|---|---|---|---|---|---|---|---|
| GB01-REPRO | 필수 | 실패 검출 | 수정 전 `gradlew -p modules/domain test --offline` | 지적한 결함이 실패로 보임 | 81 completed, 6 failed. 나머지 75 PASS | PASS | [domain-test-summary-r02.log](domain-test-summary-r02.log) |
| GB01-UNIT-R02 | 필수 | clean 단위·회귀 | `gradlew -p modules/domain clean test --rerun-tasks --offline`, toolchain 17 | 실패 0 | 81 PASS, 0 FAIL, 0 SKIP, 0 ERROR. BUILD SUCCESSFUL in 41s. XML `2026-11-27T14:24:54.596Z` | PASS | 같은 로그, [junit-r02](junit-r02) |
| HOST-40 | 필수 | 회귀 | `python -m unittest discover -s tests/unit -p test_*.py` | 40 PASS | 40 PASS, 0.042s. Python 3.14.7 | PASS | 같은 로그 |
| FOUNDATION | 선택 | 구조 | `python tools/check_foundation.py` | 기존 구조 PASS | PASS. 스크립트가 적는 공식 스키마·실기기는 NOT RUN | PASS, 스크립트 범위 | 같은 로그 |
| GB01-E1 | 필수 | 환경 재현 | 비ASCII 접합에서 `IdentityTest` | 원인과 ASCII 통과를 구분 | 접합은 `ClassNotFoundException`. ASCII clean은 81 PASS | 원인 확인. 비ASCII 경로는 미해결 | BUILD.md |
| WFF bootstrap | 회귀 | 기존 CI | push [46015880941](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46015880941), job 140562742792. PR [46015887551](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46015887551), job 140562766104 | 기존 파이프라인 success | 두 실행 모두 conclusion success. head `46caded`. Kotlin 시험은 이 워크플로에 없음 | PASS, 기존 파이프라인 | 위 URL |
| 실기기, 네트워크, 건강 데이터, 제안 workflow 실행 | 제외 | 실기기·CI | 미실행 | NOT RUN | NOT RUN | NOT RUN | 없음 |

환경 및 도구 버전: Windows 11. 테스트 JVM은 Eclipse Temurin 17.0.20.1+1, `C:\Users\scarl\.jdks\temurin-17`. 로그 한 줄은 `TEST_JVM version=17 vendor=Eclipse Temurin path=C:\Users\scarl\.jdks\temurin-17`. `java -version`은 `17.0.20.1`. `file.encoding`과 `sun.jnu.encoding`은 MS949. Gradle을 띄운 JVM은 Adoptium 21.0.5.11. Kotlin 2.4.21. Gradle 9.3.1. Python 3.14.7.
총 시험 수, PASS, FAIL, SKIP, NOT RUN, PENDING: 도메인 clean 81 PASS / 0 FAIL / 0 SKIP / 0 ERROR. 그중 기존 70, 신규 11. host 40 PASS. foundation PASS. 수정 전 재현은 6 FAIL / 75 PASS. 실기기, 제품 통합, 제안 workflow 실행은 NOT RUN. bootstrap CI는 success이며 도메인 81개는 그 워크플로에 없다.
CI 실행 ID / head SHA / job / step: push [46015880941](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46015880941), head `46caded706c54f7eb501dd5d8385fc52bca961b1`, job `140562742792`, conclusion success. pull_request [46015887551](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46015887551), job `140562766104`, 같은 head SHA, conclusion success. 두 실행 모두 wrapper, 구조 검사, validation tool regression, SDK 설치와 확인, 공식 WFF validation, debug APK build, APK 내용, 메모리 평가, debug 서명, artifact 업로드가 success였다. push 실행의 validation tool regression 로그는 `Ran 40 tests in 0.015s`다. 이 워크플로는 `modules/domain` 시험을 실행하지 않는다.
Artifact 파일명·해시·재생성 명령(해당 시): 도메인 모듈은 APK를 만들지 않는다. JUnit XML은 [junit-r02](junit-r02)에 있다. 재실행은 `.\gradlew -p modules/domain clean test --rerun-tasks`.
정상/실패/경계/회귀 시험 증거: `mm`, `°C`, `m/s` 수락. `mm Hg`, `mm\u000BHg`, `mm\u0000`, `\u0000`, `\u0007mm` 거절. 값이 null인 `\u0000` 단위는 기존처럼 단위 문자 검사를 건너뛴다. `(5, 6)`과 극값 배타 구간은 `RANGE_EMPTY`. `Long.MIN_VALUE`와 `Long.MAX_VALUE` 한 점 포함 구간은 그 값을 수락한다. 0 초과는 1을 수락하고 0을 거절한다. 10 미만은 9를 수락하고 10을 거절한다. 오염 단위는 커서를 바꾸지 않고 `deriveStatus`가 `Rejected`다. `DENIED`는 `Denied`, 만료된 `ERROR`는 `Failed`, 창 안의 `STALE`은 `Reading`이되 상태가 `STALE`이다. `expiresAt == null`은 `Freshness.UNDECLARED`이며 `FRESH`가 아니다.
검사 도구의 실패 검출 시험: 수정 전 6개 fixture가 빌드를 실패로 끝냈다. 테스트를 지우지 않고 구현을 고친 뒤 같은 fixture가 통과했다.
실기기 및 성능 시험 미실시 이유: 회차 02 범위 밖이고 B-002로 연결된 기기가 없다.

### 의존성

`testRuntimeClasspath`는 mavenCentral이다. `kotlin-stdlib` 2.4.21, `annotations` 13.0, `kotlin-test` 2.4.21, `kotlin-test-junit5` 2.4.21, `junit-jupiter-api` 5.10.1, `junit-jupiter-engine` 5.10.1, `junit-platform-engine` 1.10.1, `junit-platform-commons` 1.10.1, `junit-platform-launcher` 1.10.1, `opentest4j` 1.3.0. Foojay 1.0.0은 settings 플러그인이다. Android SDK와 네트워크 클라이언트는 없다. 라이선스는 Kotlin과 annotations와 Gradle과 Foojay가 Apache-2.0, JUnit 5가 EPL-2.0이다. 조회일 2026-11-27.

### Kotlin CI 제안

[modules/domain/docs/CI_PROPOSAL.md](../../../modules/domain/docs/CI_PROPOSAL.md). `bootstrap.yml`은 유지한다. 제안 workflow는 `modules/domain/**` 변경 때 `./gradlew -p modules/domain test`만 실행하고 JUnit XML을 artifact로 올린다. JDK 17 Temurin, wrapper SHA-256 `b3a875ddc1f044746e1b1a55f645584505f4a10438c1afea9f15e92a7c42ec13`. 공통 `.github`는 수정하지 않았다. 이 제안의 실행은 NOT RUN이다. Ubuntu 경로는 ASCII라서 GB01-E1을 재현하지 않는다.

### GB01-E1

Gradle 9.3.1은 테스트 워커 클래스패스를 UTF-8 `@argfile`로 쓴다. Temurin 17.0.20.1은 그 파일을 `sun.jnu.encoding=MS949`로 읽는다. 명령줄의 `-Dfile.encoding=UTF-8`은 argfile을 펼친 다음에 적용된다. 비ASCII 접합에서 `IdentityTest`는 `ClassNotFoundException`이었다. 같은 JDK에서 UTF-8 argfile의 클래스는 찾지 못했고 MS949 argfile의 같은 클래스는 실행됐다. ASCII worktree의 clean 81 PASS가 안전한 절차의 증거다.

## 구현 후 검토

검토 유형(자기 재검토 / 다른 에이전트 / 사람): 자기 재검토. 독립 에이전트와 사람 검토는 NOT RUN.
검토 대상 diff 및 SHA: `46caded706c54f7eb501dd5d8385fc52bca961b1`, modules/domain 9 files, +323/−15.

| 결함 ID | 심각도 | 위치·재현 | 증거 | 수정/이관 | 재검증 |
|---|---|---|---|---|---|
| GB01-D2 | P2, 종료 | 값 있는 단위의 내부 공백과 NUL이 구조 검사를 통과 | 수정 전 expected issues but was [] | 공백은 `UNIT_PADDED`, 비공백 제어 문자는 `UNIT_CONTROL` | clean 81 PASS |
| GB01-D3 | P2, 종료 | `LongBounds.parse`가 정수 없는 배타 구간을 `Accepted` | 수정 전 ClassCastException to Rejected | `longSpanEmpty`가 `RANGE_EMPTY` | clean 81 PASS. 비교식은 원래 그 값을 거절함 |
| GB01-D4 | 재현 후 결함 아님 | `DENIED`/`ERROR`/`STALE`/`UNDECLARED`가 신선 `VALID`로 승격되는지 | 수정 전 PipelineTest 2개 PASS | 코드 유지. A24대로 `classifiedValue`는 TTL을 보지 않음 | 같은 시험이 clean에서도 PASS |
| GB01-E1 | 환경 제한 | 비ASCII 경로 워커 `ClassNotFoundException` | argfile UTF-8 바이트와 MS949 디코딩 실험 | 모듈 시험 삭제로 우회하지 않음. BUILD.md에 원인과 ASCII 절차 | ASCII clean PASS. 비ASCII 경로는 미해결 |

자기 재검토에서 추가 구현 결함은 찾지 못했다. 빈 정수 구간의 비교식은 값을 통과시키지 않았다. 단위 결함은 기대 단위가 같으면 `applyRevision`과 `deriveStatus`가 그 관측을 수락했다.

## 종료 게이트

| 게이트 | 결과 | 증거 또는 미적용 사유 |
|---|---|---|
| G0 사전 검증 | PASS | main `b5dd320` 필수 문서와 GB-01-R02, OPS-04. 제품 NO-GO 유지 |
| G1 구현/요구사항 | PASS | 회차 02의 확인된 결함만 수정. 신규 제품 기능 없음 |
| G2 검증 도구 | PASS | 수정 전 6 FAIL, 수정 후 같은 fixture PASS |
| G3 시험/회귀 | PASS | clean 81, host 40, foundation PASS. bootstrap 46015880941과 46015887551 success. 도메인 시험은 CI 밖 |
| G4 분야별 검증 | PASS, 모듈 범위 | 단위, 정수 범위, TTL 구분. 실기기·WFF 기능 NOT RUN |
| G5 별도 재검토 | 자기 재검토 | 독립 검토자 NOT RUN |
| G6 증거 및 판정 | PASS | 코드 SHA `46caded`와 push/PR CI head가 같다. 로컬 XML·로그와 CI step success를 대조했다. 도메인 81개는 CI가 실행하지 않는다 |
| G7 문서/재개 | 이 파일 | 중앙 문서는 제안만. 원격 반영은 증거 커밋 후 확인 |

최종 작업 판정 및 이유: 독립 모듈 보완 GO. 재현된 D2와 D3를 고쳤고 81개 clean 시험이 통과했다. D4는 기존 의도와 같았다. bootstrap은 코드 SHA에서 success다. 제품 출시 판정은 NO-GO다. 총괄 통합과 제안 workflow 실행은 남아 있다.
제품 출시 판정(별도): NO-GO
미해결 장애 / 이관 및 해결 조건: GB01-E1은 비ASCII Windows 경로에서 남는다. ASCII 경로로 재현한다. A27 Double 빈 구간은 정책 승인 전 변경하지 않는다. B-002/B-003/B-004/B-007은 이 회차가 해결하지 않는다.
다음 작업 ID, 읽을 문서, 첫 행동·명령, 기대 결과: 총괄이 PR #1과 이 보고서를 검토한다. 통합 시 `modules/domain/docs/CI_PROPOSAL.md`를 `.github/workflows/domain-kotlin.yml`로 옮기고 `./gradlew -p modules/domain test`가 CI에서 81 PASS인지 확인한다. 그 전에는 공통 workflow를 바꾸지 않는다.
STATUS / WORK_LOG / BLOCKERS / evidence / 정본 문서 갱신 여부: 중앙 문서는 수정하지 않았다. 아래 제안을 evidence에만 둔다.
저장소 반영 확인(커밋/브랜치; 자기 참조 SHA 금지): 코드 커밋 `46caded706c54f7eb501dd5d8385fc52bca961b1`은 `origin/agent/grok/GB-01`에 푸시했다. 이 보고서 커밋의 SHA는 여기에 적지 않는다.

## 중앙 문서 갱신 제안

STATUS: GB-01 회차 02 코드 SHA `46caded706c54f7eb501dd5d8385fc52bca961b1`. 로컬 도메인 81 PASS / 0 FAIL. D2·D3 수정, D4는 기존 동작 확인. GB01-E1 원인 확인, 비ASCII 경로는 미해결. Kotlin 시험은 아직 bootstrap에 없다. 통합은 보류. 제품 NO-GO.

WORK_LOG: 위 SHA, 도메인 81 PASS, host 40 PASS, [REPORT-02.md](REPORT-02.md), push CI 46015880941 success, PR CI 46015887551 success. Kotlin 시험은 CI에 아직 없다.

BLOCKERS: 새 제품 차단을 추가하지 않는다. GB01-E1은 환경 제한으로 유지한다. B-002/B-003/B-004/B-007은 유지한다.
