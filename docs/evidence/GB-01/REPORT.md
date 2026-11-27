# 작업 보고서 — GB-01 / 회차 01

상태: GO
일자, 작업자, 검토자: 2026-11-27, Grok Build, 자기 재검토. 독립 검토자 없음.
기준 브랜치/HEAD: main `fe4e19d7c6e97c043e4f31cb5960bdb430fd507b`
PRE-FLIGHT: 착수 시 origin/main과 로컬 main이 `fe4e19d7c6e97c043e4f31cb5960bdb430fd507b`였다. 작업 트리는 clean이었다. 같은 SHA에서 AGENTS.md, docs/STATUS.md, docs/operations/RESUME_PROTOCOL.md, PROJECT_INVARIANTS.md, TASK_RECORD_PROTOCOL.md, VERIFICATION_PROTOCOL.md, TASK_REPORT_TEMPLATE.md, GPT_EXECUTION_PLAN.md의 GPT-07 행, BLOCKERS.md, WORK_LOG.md, agent-orders/README.md, agent-orders/GB-01.md, DATA_INTELLIGENCE.md, REQUIREMENTS.md의 R-04/R-12/R-17/R-21/R-22, MASTER_ARCHITECTURE.md, QUALITY_GATES.md, README.md를 읽었다. 활성 작업은 GPT-03 READY와 GB-01 READY다. 차단은 B-002 BLOCKED, B-003/B-004/B-005/B-006/B-007/B-008 OPEN, B-001/B-010 RESOLVED다. 제품 코드의 최신 성공 CI는 [46002470824](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46002470824), 코드 SHA `f284b1bd69a767ef0f7285449fe7c45f05895e53`이며 이 SHA는 기준 HEAD의 조상이다. 기준 HEAD 자체는 `[skip ci]` 문서 커밋이라 새 제품 CI가 없다. PRE-FLIGHT PASS. 제품 출시 NO-GO는 유지한다.
검증 대상 코드 SHA: `098dd35e1d7111a5ece9f8417142cf1c6ecc2fd3`
관련 요구사항 / WO / GPT ID: R-04, R-12, R-17, R-21, R-22의 계약 준비. GPT-07 / WO-17~23의 선행 조건은 해제하지 않는다. 정식 WO GO로 계산하지 않는다.
관련 정본 문서: docs/DATA_INTELLIGENCE.md, docs/MASTER_ARCHITECTURE.md, docs/REQUIREMENTS.md, docs/operations/agent-orders/GB-01.md
작업 목표, 포함/제외 범위: 기상·건강·배터리·상태 판단이 나중에 공유할 순수 Kotlin 데이터 계약을 구현한다. Observation, 출처, 단위, 시각, 상태, 종류, TTL, revision 순서, 단위 시험, 초안 인터페이스를 포함한다. FSM, 캐시 저장소, 네트워크, Android SDK, 실제 건강·기상 값, Wear/phone 앱, WFF, 그래픽, 루트 Gradle, CI, 중앙 STATUS/WORK_LOG/BLOCKERS는 제외한다.
선행 조건 및 이전 실패: GB-01은 독립 준비 작업이다. 기존 제품 실패와 실기기 미검증은 이 모듈의 통과로 바꾸지 않는다. 직전 도메인 모듈은 없었다.
변경 파일 소유권 / 변경 영향: 소유 경로는 `modules/domain/**`와 `docs/evidence/GB-01/**`다. 루트 설정과 앱은 수정하지 않았다. 작업 도중 공유 체크아웃이 `agent/antigravity/AG-01`로 바뀌어 있었다. 그 브랜치의 `tests/compatibility/**`는 스테이징하지 않았다. 커밋은 별도 worktree `C:\Users\scarl\AppData\Local\Temp\aura-gb01-wt`에서 했다.
참조 자료(정확한 URL·버전·확인일): 2026-11-27 확인. Kotlin 2.4.21, https://kotlinlang.org/docs/releases.html, Apache-2.0, https://github.com/JetBrains/kotlin/blob/v2.4.21/license/LICENSE.txt. JUnit Jupiter 5.10.1 / Platform 1.10.1, EPL-2.0, https://junit.org/junit5/. opentest4j 1.3.0. Gradle Wrapper 9.3.1, Apache-2.0. Foojay toolchain resolver 1.0.0, Apache-2.0, https://github.com/gradle/foojay-toolchains. JetBrains annotations 13.0은 kotlin-stdlib의 전이 의존성이다.
가정 / 위험 / 승인 필요 사항: [modules/domain/docs/ASSUMPTIONS.md](../../../modules/domain/docs/ASSUMPTIONS.md)의 A1~A26. 출처 목록, 단위 환산, 값 범위, TTL 길이, 미래 시각, 확률 스케일, FSM 어휘, applicationId는 승인하지 않았다.
성공 기준 / 롤백 방법: 독립 모듈이 JDK 17에서 컴파일되고 단위 시험이 실패 0이다. 잘못된 상태 조합을 정상 값으로 바꾸지 않는다. 롤백은 이 브랜치를 병합하지 않으면 된다. main은 변경하지 않았다.

## 구현 및 결정

| 파일·모듈 | 변경 및 이유 | 관련 요구사항 | 확인할 영향 |
|---|---|---|---|
| modules/domain/src/main/kotlin/.../Observation.kt | 승인된 필드, 상태, 종류, 분류 읽기 | R-17, R-04 | 누락과 0의 구분 |
| Validation.kt, Constraints.kt | 구조 검사, 단위, 범위, 미래 시각 정책 | R-17, R-22 | 오류를 성공으로 바꾸지 않음 |
| Freshness.kt | 호출자 기준 시각, 만료 경계, STALE 파생 | R-17 | 만료된 오류가 VALID가 되지 않음 |
| RevisionGate.kt | 오래된 revision 거절, 동률, 수신 역전 | R-17 | 커서 보존 |
| draft/SnapshotDrafts.kt | 이름이 있는 후속 필드만 초안 | R-04, R-12 | 예보 구간과 observedAt 분리 |
| modules/domain/build.gradle.kts, settings.gradle.kts | 루트에 넣지 않는 JVM 빌드 | R-22 | 앱 빌드 비포함 |
| modules/domain/docs/* | 빌드, 가정, 인터페이스 | R-04, R-12, R-21 | 미확정 항목 보존 |

결정, 대안, 기각 사유 및 ADR: 만료 경계는 `EXPIRED_AT_OR_AFTER`로 코드에 이름을 붙였다. 제품 상수 승인이 아니므로 ADR을 만들지 않았다. 동률 revision은 첫 수락을 유지한다. 마지막 수신 우선은 기각했다. 오류 문장 필드는 두지 않았다. WeatherSnapshot의 생략 필드는 추가하지 않았다. 중앙 문서와 루트 Gradle은 수정하지 않았다.

시도한 접근과 실패 원인: 비ASCII 저장소 경로에서 Gradle 테스트 워커가 `ClassNotFoundException`으로 실패했다. JDK 17과 JDK 21 모두 재현됐다. 클래스 파일과 테스트 클래스패스는 존재했다. ASCII worktree에서 같은 명령이 실행됐다. 테스트를 삭제하지 않았다. 커밋 전 `-0.0` 단언이 `Double.equals` 때문에 실패했다. 값을 `0.0`으로 바꾸지 않고 부호 비트를 유지하도록 단언과 중복 충돌 시험을 고쳤다.

사용법, 환경, 재현 명령, 설정 변경: [modules/domain/docs/BUILD.md](../../../modules/domain/docs/BUILD.md). 저장소 루트에서 `.\gradlew -p modules/domain test`. Windows에서 경로에 비ASCII 문자가 있으면 ASCII 접합 또는 worktree에서 같은 명령을 실행한다.

## 요구사항 및 검증 추적표

| 요구사항/완료 기준 | 구현 파일·경로 | 시험 ID | 예상 결과 | 실제 결과 | 증거·SHA | 판정 |
|---|---|---|---|---|---|---|
| R-17 누락, 오래된 값, 거부, 오류 구분 | Observation.kt, Validation.kt, Freshness.kt | ValidationTest, FreshnessTest, PipelineTest | 0과 null과 오류가 서로 바뀌지 않음 | 70개 중 해당 시험 PASS | 098dd35 | PASS, 모듈 범위 |
| R-04 관측량과 예측량 구분 | SnapshotDrafts.kt | DraftContractTest | kind가 유지되고 시각 필드가 분리됨 | 12개 PASS | 098dd35 | PASS, 초안 범위. 실공급원 NOT RUN |
| R-12 상황 강조 | SnapshotDrafts.kt의 Context/Presentation 초안 | DraftContractTest | 초안이 FSM을 실행하지 않음 | PASS | 098dd35 | 계약만 PASS. FSM NOT RUN |
| R-21 민감정보 비저장 | 소스와 시험 픽스처 | SourceScanTest | Android, 네트워크, 시계 API 없음 | PASS | 098dd35 | 정적 범위 PASS. 전송·업데이트 NOT RUN |
| R-22 재현 빌드 | modules/domain Gradle | domain test, host 40 | 독립 테스트와 기존 40개가 통과 | 70 PASS, 40 PASS | 098dd35 | 모듈 PASS. 이 브랜치 CI는 아래 기록 |
| 오래된 revision과 역전 | RevisionGate.kt | RevisionGateTest | 작은 revision이 커서를 바꾸지 않음 | 15 PASS | 098dd35 | PASS |
| 기존 40개 host 시험 유지 | 비수정 | tests/unit | 40 PASS | 40 PASS / 0 FAIL | 098dd35 worktree | PASS |
| 제품 통합, 실데이터, 실기기 | 없음 | 없음 | 실행하지 않음 | NOT RUN | 없음 | NOT RUN |

## 검증 결과

| 시험 ID | 필수/선택 | 종류 | 명령·대상 버전 | 기대 결과 | 실제 결과 | 판정 | 로그 |
|---|---|---|---|---|---|---|---|
| GB01-UNIT | 필수 | 단위, 경계, 오류 주입 | `.\gradlew -p modules/domain test --rerun-tasks --offline`, Kotlin 2.4.21, toolchain 17 | 실패 0 | 70 PASS, 0 FAIL, 0 SKIP, 0 ERROR. BUILD SUCCESSFUL in 34s. XML 시각 2026-11-27T13:43:17Z | PASS | [domain-test-summary.log](domain-test-summary.log) |
| GB01-FAIL-DETECT | 필수 | 검증기 실패 검출 | 커밋 전 `-0.0` 단언 실패, 오류 상태+값 0 주입 | 빌드 실패 후 수정본만 통과 | 수정 전 BUILD FAILED, 098dd35는 PASS | PASS | 같은 로그의 사전 실패 기록 |
| HOST-40 | 필수 | 회귀 | `python -m unittest discover -s tests/unit -p test_*.py` | 40 PASS | 40 PASS, 0.048s | PASS | 같은 로그 |
| FOUNDATION | 선택 | 구조 회귀 | `python tools/check_foundation.py` | 기존 구조 PASS | PASS. 공식 스키마는 그 스크립트가 NOT RUN으로 출력 | PASS, 스크립트 범위 | 같은 로그 |
| WFF 스키마, APK, 메모리, 서명 | 회귀 | 기존 CI | 코드 푸시 46009884061 | 기존 파이프라인 success | job 140542379520 success. 도메인 시험은 이 워크플로에 없음 | PASS, 기존 파이프라인 | 위 CI URL |
| 실기기, 네트워크, 건강 데이터 | 제외 | 실기기 | 미실행 | NOT RUN | NOT RUN | NOT RUN | 없음 |

환경 및 도구 버전: Windows. Gradle을 띄운 JVM은 Temurin 21.0.5+11. 모듈 toolchain은 Eclipse Temurin 17.0.20.1+1, `C:\Users\scarl\.jdks\temurin-17`. `--info` 컴파일에서 `JAVA_VERSION=17.0.20.1`, Kotlin `jdkHome`가 그 경로였다. 테스트 작업은 별도 launcher를 지정하지 않고 같은 Java toolchain을 사용한다. 통과한 테스트 프로세스 안에서 `java.version`을 출력하지는 않았다. Python 3.14.7.
총 시험 수, PASS, FAIL, SKIP, NOT RUN, PENDING: 도메인 70 PASS / 0 FAIL / 0 SKIP. host 40 PASS / 0 FAIL. foundation PASS. 실기기와 제품 통합은 NOT RUN. 도메인 70개는 로컬 Gradle이며 기존 CI 워크플로에 들어 있지 않다.
CI 실행 ID / head SHA / job / step: [AURA Bootstrap 46009884061](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46009884061), head SHA `098dd35e1d7111a5ece9f8417142cf1c6ecc2fd3`, job 140542379520, conclusion success. Wrapper, 구조, 회귀 시험, SDK, 공식 WFF validation, debug APK build, APK 내용, 메모리 평가, debug 서명, artifact 업로드가 success였다. 이 CI는 루트 앱 파이프라인이며 `modules/domain` 단위 시험을 실행하지 않는다. 도메인 70개의 증거는 로컬 실행이다. Node.js 20 deprecation과 setup-java v4 deprecation 경고가 있었고, 이번 작업은 워크플로를 수정하지 않는다.
Artifact 파일명·해시·재생성 명령(해당 시): 도메인 모듈은 APK를 만들지 않는다. 재실행 명령은 `.\gradlew -p modules/domain test`.
정상/실패/경계/회귀 시험 증거: 실제 0, 누락, 거부, 오류, 만료 시각 동률, 배타 범위, Long.MAX_VALUE, 음수 revision, 순서 역전, 중복, 페이로드 충돌, 단위 불일치, 유한하지 않은 수, 시간대 동일 Instant, 잘못된 kind.
검사 도구의 실패 검출 시험: 오류 상태에 숫자 0을 넣으면 `VALUE_FORBIDDEN`이고 값은 그대로다. 커밋 전 잘못된 단언은 빌드 종료 코드를 실패로 만들었다.
실기기 및 성능 시험 미실시 이유: GB-01 범위 밖이고 B-002로 연결된 기기가 없다.

## 구현 후 검토

검토 유형(자기 재검토 / 다른 에이전트 / 사람): 자기 재검토. 독립 에이전트와 사람 검토는 NOT RUN.
검토 대상 diff 및 SHA: `098dd35e1d7111a5ece9f8417142cf1c6ecc2fd3`, 22 files, modules/domain only.

| 결함 ID | 심각도 | 위치·재현 | 증거 | 수정/이관 | 재검증 |
|---|---|---|---|---|---|
| GB01-D1 | P3, 종료 | `-0.0`을 `Double.equals`로 `0.0`과 같다고 단언 | 커밋 전 BUILD FAILED | 부호 비트를 유지하고 동률 revision 충돌로 시험 | 098dd35 PASS |
| GB01-E1 | 환경 제한 | 비ASCII 경로의 Gradle 테스트 워커 ClassNotFoundException | 같은 모듈이 ASCII 경로에서는 70 PASS | 코드로 테스트를 지우지 않음. BUILD.md에 접합 절차 기록 | ASCII worktree PASS. 원래 경로의 워커는 미해결 |

열린 기능 결함은 없다. GB01-E1은 이 모듈의 판정 로직 결함이 아니다.

## 종료 게이트

| 게이트 | 결과 | 증거 또는 미적용 사유 |
|---|---|---|
| G0 사전 검증 | PASS | 위 PRE-FLIGHT. 제품 NO-GO는 유지 |
| G1 구현/요구사항 | PASS, 모듈 범위 | 추적표. 실공급원과 FSM은 범위 밖 |
| G2 검증 도구 | PASS | 주입된 오류와 커밋 전 실패 빌드 |
| G3 시험/회귀 | PASS | 로컬 70, host 40, foundation, 기존 WFF CI 46009884061 success. 도메인 시험은 그 CI에 없다 |
| G4 분야별 검증 | PARTIAL | 데이터 계약은 시험했다. 건강 네트워크, 성능, 실기기는 NOT RUN |
| G5 별도 재검토 | PASS, 자기 재검토 | 독립 검토 NOT RUN |
| G6 증거 및 판정 | PASS | 코드 SHA와 70개 XML이 일치. 보고서 커밋은 코드 SHA가 아니다 |
| G7 문서/재개 | PASS, 브랜치 기록 | 중앙 STATUS/WORK_LOG/BLOCKERS는 제안만 하고 수정하지 않음 |

최종 작업 판정 및 이유: GO. 독립 JVM 모듈의 컴파일, 70개 단위 시험, 실패 검출, 기존 40개 host 시험이 코드 SHA에서 통과했다. 미확정 항목은 가정으로 남겼다.
제품 출시 판정(별도): NO-GO. 실기기, 공급원, FSM, 그래픽, 배포 정책은 끝나지 않았다.
미해결 장애 / 이관 및 해결 조건: B-002, B-003 잔여, B-004, B-006, B-007 유지. A1~A26은 후속 승인이 필요하다. GB01-E1은 ASCII 경로로 회피했다.
다음 작업 ID, 읽을 문서, 첫 행동·명령, 기대 결과: 총괄 담당자가 이 브랜치를 검토한다. 병합 전에는 DATA_INTELLIGENCE와 ASSUMPTIONS를 다시 읽는다. 통합 시 루트 `settings.gradle.kts`에 이 모듈을 넣는 변경은 중앙 소유자가 한다. WFF 앱 안에 Kotlin을 넣지 않는다. 어댑터는 SDK 결과를 `Observation`으로 옮기고 `applyRevision`과 `deriveStatus`를 거친 뒤 `classifiedValue()`로 표시한다. 첫 확인 명령은 `.\gradlew -p modules/domain test`이며 기대 결과는 70 PASS다.
STATUS / WORK_LOG / BLOCKERS / evidence / 정본 문서 갱신 여부: evidence와 모듈 문서만 이 브랜치에 기록한다. 중앙 문서는 아래 제안이며 이번 커밋에서 수정하지 않는다.

### 중앙 문서 갱신 제안

STATUS: GB-01 독립 모듈 GO(데이터 계약 범위). 브랜치 `agent/grok/GB-01`, 코드 SHA `098dd35e1d7111a5ece9f8417142cf1c6ecc2fd3`. GPT-03 READY와 출시 NO-GO, 정식 WO GO 0/38은 유지. R-04/R-17의 제품 완료로 올리지 않는다.

WORK_LOG: `2026-11-27 / GB-01` 순수 Kotlin Observation 계약, 기준 `fe4e19d7`, 코드 `098dd35`, 시험 70 PASS와 host 40 PASS. 상세는 docs/evidence/GB-01/REPORT.md.

BLOCKERS: 새 제품 차단을 추가하지 않는다. B-006의 출처 목록 미확정은 유지. 비ASCII Windows 경로의 Gradle 테스트 워커 실패는 환경 제한으로 남기고, 식별자는 총괄 담당자가 필요하면 부여한다.

저장소 반영 확인(커밋/브랜치; 자기 참조 SHA 금지): 코드 커밋 `098dd35e1d7111a5ece9f8417142cf1c6ecc2fd3`은 `agent/grok/GB-01`에 푸시했다. 이 보고서 커밋의 SHA는 코드 검증 SHA가 아니다. main에는 병합하지 않는다.
