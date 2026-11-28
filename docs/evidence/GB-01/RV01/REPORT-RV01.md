# GB-01 RV01 로컬 증거

상태: 로컬 구현과 로컬 시험만 완료. 브랜치 `agent/grok/GB-01-RV01`은 push하지 않았다. 제품 판정은 NO-GO. PR #3과 PR #5는 OPEN, HOLD, 미병합이다. 이 후보는 SDK 신뢰나 통합 허가가 아니다.

코드 SHA: `56675d84d1c95bee5554decc6564b3cc9faded60`
부모: `d847028dc914ebb0acfbf47ff6b83a179d9bf486` (`agent/grok/GB-01-D01`와 `origin/agent/grok/GB-01-D01`)
이 보고서 커밋은 코드 SHA가 아니다. 시험은 코드 SHA의 작업 트리에서 실행했다.

## 수용 계약

작업지시 `docs/operations/agent-orders/GB-01-RV01.md`와 ADR-008 Central disposition을 `origin/main` `be3ff9bbecb0ae7922ffa8c974918030cc805b73`에서 읽었다. Central disposition을 우선 적용했다. `origin/main`은 D01 브랜치에 병합하지 않았고, 이 브랜치에도 병합하지 않았다. main에는 D01 구현이 없고 ADR과 지시 문서가 있다.

## 변경

`d847028` 대비 추가분 4개 파일, 810줄이다.

- `modules/domain/src/main/kotlin/io/github/scarlel96/aura/domain/Authority.kt`
- `modules/domain/src/test/kotlin/io/github/scarlel96/aura/domain/AuthorityContractTest.kt`
- `modules/domain/docs/ASSUMPTIONS.md`의 A29
- `modules/domain/docs/INTERFACE_CONTRACT.md`의 권한 검증 절

기존 D01 소스와 시험 blob, Intelligence 소스, `tools/check_domain_results.py`, `.github`, 루트 Gradle, 중앙 STATUS는 이 커밋에서 바꾸지 않았다.

`AuthorityCoordinator`는 관측 revision과 분리된다. 상태는 `UNKNOWN`, `GRANTED`, `DENIED`다. ticket과 capability는 data class가 아니고, 발급 인스턴스의 seal과 session에 묶인다. 공개 `verified = true` 경로는 없다. 최신 미완료 ticket만 완료된다. 같은 완료의 반복은 `UNCHANGED`, 같은 ticket의 모순된 반복은 generation을 돌리고 `UNKNOWN`으로 닫는다. 신뢰된 무효화는 이미 `UNKNOWN`이어도 generation을 돌리고 미완료 확인을 취소한다. 검증되지 않은 입력은 scope를 바꾸지 않는다. 관측 `DENIED`, `ERROR`, `UNAVAILABLE`, `VALID`는 권한을 바꾸지 않는다. ticket과 generation이 `Long.MAX_VALUE`를 넘기려 하면 잠그고 감싸지 않는다. 획득 카운터도 같은 방식으로 잠근다. `openNearCeiling`은 모듈 내부에서 카운터 위치만 옮기며 `GRANTED`를 만들지 않는다. 재허가 이전 측정의 공개, SDK 접근, 동시성, 저장, 소비자 삭제는 구현하지 않았다. 같은 프로세스의 리플렉션을 막지 않는다.

## Domain 시험

작업 트리: `C:\Users\scarl\AppData\Local\Temp\aura-d01-wt`
명령: `.\gradlew.bat -p modules/domain clean test --offline --no-daemon --no-build-cache`
`JAVA_HOME`: `C:\Users\scarl\.jdks\temurin-17`
JVM: Temurin 17.0.20.1+1, `TEST_JVM path=C:\Users\scarl\.jdks\temurin-17`
Gradle: 9.3.1
HEAD: `56675d84d1c95bee5554decc6564b3cc9faded60`
결과: `BUILD SUCCESSFUL in 34s`, `GRADLE_EXIT=0`
XML: 9 files, `2026-11-28T08:57:00.401Z`–`2026-11-28T08:57:00.892Z`
집계: 102 tests, 0 failures, 0 errors, 0 skipped

구성: 기존 88 (`DraftContractTest` 12, `FreshnessTest` 11, `IdentityTest` 5, `PayloadIntegrityTest` 7, `PipelineTest` 5, `RevisionGateTest` 15, `SourceScanTest` 1, `ValidationTest` 32)와 `AuthorityContractTest` 14.

`AuthorityContractTest` 식별자:

- `unknownAndDeniedCannotAcquire()`
- `currentIssuedCheckCanGrant()`
- `unissuedForeignAndStaleTicketsCannotGrant()`
- `invalidateWhileUnknownFencesPendingCheck()`
- `duplicateAndConflictingCompletionAreHandled()`
- `trustedFailureAndUntrustedInputAreDistinct()`
- `regrantRejectsPriorGeneration()`
- `foreignScopeSessionAndRequestAreRejected()`
- `restartRequiresFreshAuthority()`
- `ticketAndGenerationCeilingsFailClosed()`
- `sameStateCheckDoesNotResurrectInvalidatedGrant()`
- `capabilityConstructionAndCopyCannotForgeAcceptance()`
- `ordinaryDataStatusDoesNotGrantOrRevokeAuthority()`
- `genericRevisionAndScalarContractRemainIndependent()`

102개 전체 식별자는 `domain-junit-summary.txt`와 `junit-domain/` XML에 있다. `PayloadIntegrityTest.higherRevisionStillReplacesEarlierDenial()`은 유지됐고 PASSED다.

Gradle이 디스크에 쓴 XML은 CRLF다. 이 저장소 커밋의 blob은 Git `autocrlf` clean 필터를 거친 LF다. `AuthorityContractTest` XML의 clean 해시 `6edc11af370c3e9eee20f17e823cee00c6264b27`는 빌드 파일의 `git hash-object`와 같다. 시험 식별자와 집계 문자는 같다.

## 등록된 검사기

`tools/check_domain_results.py`는 수정하지 않았다. 같은 XML에 대해 두 프로파일을 실행했다. 둘 다 종료 코드 1이다. `DOMAIN_RESULT` 줄은 출력되지 않았다. 이 거절은 등록 전 상태이며 PASS가 아니다. CI는 실행하지 않았다.

baseline:

```
DOMAIN_INVENTORY baseline
ValueError: Unknown or duplicate suite: io.github.scarlel96.aura.domain.AuthorityContractTest
```

d01:

```
DOMAIN_INVENTORY d01
ValueError: Unknown or duplicate suite: io.github.scarlel96.aura.domain.AuthorityContractTest
```

원문 로그: `checker-baseline.txt`, `checker-d01.txt`.

## Intelligence 호환

일회용 작업 트리: `C:\Users\scarl\AppData\Local\Temp\aura-d01-intel`
HEAD: `e050937fd34709d143836e44bbf91ec5221bdc48` (detached, 커밋하지 않음)
`modules/intelligence`는 그 HEAD와 차이가 없다 (`git diff --quiet` 종료 0).
`modules/domain`은 코드 SHA `56675d84d1c95bee5554decc6564b3cc9faded60`와 차이가 없다 (`git diff --quiet` 종료 0). Gradle `includeBuild("../domain")`가 그 트리를 사용했다.
명령: `.\gradlew.bat -p modules/intelligence clean test --offline --no-daemon --no-build-cache`
같은 Temurin 17.0.20.1.
결과: `BUILD SUCCESSFUL in 45s`, `GRADLE_EXIT=0`
XML: 13 files, `2026-11-28T08:59:03.080Z`–`2026-11-28T08:59:08.454Z`
집계: 108 tests, 0 failures, 0 errors, 0 skipped
`Round05Test.longRunKeepsInvariants()` PASSED. 소스의 seed는 `20261128`, 반복은 `100_000`이다. Intelligence 소스는 수정하지 않았다.
식별자 원본: `intelligence-junit-summary.txt`, `junit-intelligence/`.
컴파일 경고 1건은 `Round08Test.kt:166`의 기존 safe call이며 이 작업의 변경이 아니다. 시험은 PASSED다.

## G0–G7

| 게이트 | 결과 | 근거 |
| --- | --- | --- |
| G0 | PASS, 제한 | D01 HEAD에서 분기. main `be3ff9b`의 ADR과 지시를 읽고 병합하지 않음. PR #5 `d847028`, PR #3 `0c4890e` OPEN. 제품 NO-GO |
| G1 | PASS, 제한 | 순수 권한 계약만 추가. `applyRevision`, `classifiedValue`, `deriveStatus`, `step` 시그니처와 기존 88/108 식별자 유지 |
| G2 | 로컬 Gradle PASS, 검사기 거절 | Domain 102와 Intelligence 108. 등록 검사기는 `AuthorityContractTest`를 거절. 그 거절은 PASS가 아님. push CI 없음 |
| G3 | PASS, 로컬 | FAIL/ERROR/SKIP 0. 100000회 seed `20261128` 유지. 기존 단언을 약화하지 않음 |
| G4 | 모듈 범위 | 합성 scope와 신뢰 입력. 실기기, SDK, 동시성, 소비자 삭제 NOT RUN |
| G5 | 자기 재검토 | 독립 검수 NOT RUN |
| G6 | 로컬 증거 | 코드 SHA와 XML을 구분한다. 이 파일은 시험 후의 증거다. 원격 CI 없음 |
| G7 | 정지 | 총괄의 목록 등록과 브랜치 CI 프로파일 전 push 금지. F04, C01, R09, GB-03, GPT-07 미착수 |

## 하지 않은 일

이 절은 로컬 제출 시점의 기록이다. 원격 제출은 아래 절에 있다. D01 재작업, Intelligence 수정, 검사기 수정, 기존 시험 삭제, 단언 약화, PR #3·#5 변경, main 병합, 강제 푸시는 하지 않았다.

## 원격 제출

PRE-FLIGHT 기준 SHA는 `origin/main` `4dc69f8ca595f49b90b0660d9afc0ea248779cbb`다. AGENTS, STATUS, RESUME, INVARIANTS, TASK_RECORD, VERIFICATION, TASK_REPORT, GPT 계획, BLOCKERS, WORK_LOG, QUALITY_GATES, RV01 지시, 배정표를 그 SHA에서 읽었다. 출시는 NO-GO. PR #5는 `d847028dc914ebb0acfbf47ff6b83a179d9bf486`, PR #3은 `0c4890ea7f69c6145791d17d51b98c97fed45c1d`이며 둘 다 OPEN, 미병합이다.

등록 커밋 main CI 4건은 모두 success다.

| 워크플로 | run | 결과 |
| --- | --- | --- |
| Active documentation budget | 46129144032 | success |
| Domain Kotlin | 46129144051 | success |
| Windows host reproducibility | 46129144033 | success |
| AURA Bootstrap | 46129144036 | success |

그 다음에만 `origin/main`을 이 브랜치에 병합했다. 병합 SHA `1ec894d54ff3b0aa93e590194e1ab1982e077690`. 부모는 `0b9ae00`과 `4dc69f8`이다. `modules/domain/src` 19개 blob은 구현 SHA `56675d84d1c95bee5554decc6564b3cc9faded60`와 같다. domain 계약 문서 2개 blob도 같다. 검사기 blob `21b588b3dcd5c4b093879bc67c41aaafd3751d60`와 검사기 시험 blob `eac4b8ed30d6c46b09dd44ef9c922a2f48d456cc`는 main과 같다. 제품 코드와 시험이 같으므로 Intelligence 108과 100000회 증거는 재실행하지 않았다.

저장된 `junit-domain` XML에 대한 등록 프로파일 결과:

```
DOMAIN_INVENTORY rv01
DOMAIN_RESULT 102 PASS / 0 FAIL / 0 ERROR / 0 SKIP
```

종료 코드 0. 같은 XML의 baseline과 d01 프로파일은 `AuthorityContractTest`를 알 수 없는 suite로 거절한다. 그 거절은 PASS가 아니다.

push refspec은 `1ec894d54ff3b0aa93e590194e1ab1982e077690:refs/heads/agent/grok/GB-01-RV01`다. PR #6 https://github.com/scarlel96-design/AURA-Ultra/pull/6 은 OPEN, HOLD, 미병합이다. main은 `4dc69f8`에 그대로 있다.

`1ec894d`의 push와 pull_request CI 8건은 모두 success다. Domain Kotlin push `46129593048`과 pull_request `46129609178`은 각각 `BUILD SUCCESSFUL`, 검사기 자체 시험 24 ok, `DOMAIN_INVENTORY rv01`, `DOMAIN_RESULT 102 PASS / 0 FAIL / 0 ERROR / 0 SKIP`을 출력했다.

| 이벤트 | 워크플로 | run | 결과 |
| --- | --- | --- | --- |
| push | Active documentation budget | 46129593089 | success |
| push | Domain Kotlin | 46129593048 | success |
| push | Windows host reproducibility | 46129593060 | success |
| push | AURA Bootstrap | 46129593051 | success |
| pull_request | Active documentation budget | 46129609340 | success |
| pull_request | Domain Kotlin | 46129609178 | success |
| pull_request | Windows host reproducibility | 46129609259 | success |
| pull_request | AURA Bootstrap | 46129609199 | success |

이 절을 담은 커밋은 문서다. 그 커밋의 CI는 이 표에 포함하지 않는다.

## RV01-CLOSEOUT

독립 검수 `docs/evidence/MID-AUDIT/RV01-REVIEW.md`의 RV01-C1, RV01-C2를 고쳤다. 기준은 PR #6 `8f53bff`이고, 작업 전 `origin/main`은 `f05e9b81f68232abc3ab109512cbb966f222e110`이다. 그 문서를 병합한 SHA는 `6cdb674c1e5cb020fc87ac19d630b58f582edf14`다. 수정 코드 SHA는 `558e18804d08ebd4d79be620962c256e0af07f96`다. 제품은 NO-GO다. PR #6은 OPEN, HOLD, 미병합이다. PR #3·#5는 변경하지 않았다.

### 수정 전 재현

수정 전 `Authority.kt`에서 기존 시험 두 개의 단언만 일시적으로 바꿔 실행했다. 새 시험 식별자는 만들지 않았다. 명령은 `.\gradlew.bat -p modules/domain test --offline --no-daemon --no-build-cache --tests io.github.scarlel96.aura.domain.AuthorityContractTest.capabilityConstructionAndCopyCannotForgeAcceptance --tests io.github.scarlel96.aura.domain.AuthorityContractTest.foreignScopeSessionAndRequestAreRejected`다. JVM은 Temurin 17이다. 결과: 2 tests, 2 failed, `RED_EXIT=1`. 원본 XML은 `closeout-red/TEST-io.github.scarlel96.aura.domain.AuthorityContractTest.xml`이다. 시각은 `2026-11-28T10:06:32.484Z`다.

RV01-C1. 정상 capability의 seal로 같은 모듈에서 생성한 값이 `permits`를 통과했다. 실패 목록은 `same-seal-identical`, `same-seal-relabeled-request`, `same-seal-retagged-scope`, `old-seal-current-generation`이다. 앞의 세 검사는 재허가 전에 했고, 마지막은 DENIED 다음 GRANTED로 generation이 바뀐 뒤 이전 seal과 현재 generation으로 만든 값이다.

RV01-C2. 한 coordinator에서 alpha는 GRANTED, beta는 DENIED, stream은 같다. 당시 `permits`는 scope 인자가 없었다. `permits(alphaCapability, stream)`이 true였다. 실패 문장은 `C2 unscoped permits accepted alpha while beta is DENIED`다. 수정 후 시그니처의 빨간 시험은 실행하지 않았다. 그 시그니처는 수정 전에 없었다.

### 수정

capability의 공개 타입은 생성자가 없는 인터페이스다. 발급 구현 클래스와 발급 표식 타입은 coordinator 안에서 private이다. 표식은 scope의 generation마다 하나이고 목록으로 쌓지 않는다. generation이 돌거나 scope가 잠기면 표식을 바꾼다. 같은 상태의 GRANTED 또는 DENIED는 generation과 표식을 유지한다. `permits(capability, scope, request)`만 있다. 기대 scope의 기록과 발급 표식, session, generation, 요청을 함께 본다. 다른 구현체는 거절한다.

재시작은 새 coordinator다. 이전 coordinator는 호출자가 버릴 때까지 남는다. 세션 문자열을 새로 고르는 일은 어댑터의 책임이다. 결과 값 결합, 과거 측정 공개, SDK, 동시성, 소비자 삭제는 넣지 않았다. 리플렉션 격리는 주장하지 않는다.

### 단언 변경

식별자 14개는 유지했다. 기존 Domain 시험 88개의 blob은 `56675d84d1c95bee5554decc6564b3cc9faded60`와 같다. `AuthorityContractTest`만 시험 파일이 바뀌었다.

`capabilityConstructionAndCopyCannotForgeAcceptance`는 seal을 복사하는 생성자 호출을 빼었다. 그 생성자는 더 이상 호출할 수 없고 표식도 읽을 수 없다. 대신 공개 타입이 인터페이스이고 생성자가 없는지, 실제 객체의 클래스가 private인지, 같은 scope·generation·request·acquisitionId로 인터페이스를 직접 구현한 값이 거절되는지를 본다. 올바른 scope와 요청의 허가는 유지한다. 다른 요청, 다른 scope, `AuthorityDecision`으로 감싼 값, 재허가 뒤의 이전 capability 거절, `copy` 없음도 유지한다.

`foreignScopeSessionAndRequestAreRejected`의 두 coordinator 단언은 기대 scope를 명시하도록만 바꿨다. 같은 coordinator, 같은 stream, 서로 다른 scope를 추가했다. alpha가 허가되고 beta가 거부된 동안 beta 획득은 `NOT_GRANTED`이고 alpha capability는 beta에서 거절된다. beta를 나중에 허가해도 alpha capability는 beta로 바뀌지 않는다. 두 capability의 stream과 acquisition 번호가 같아도 scope가 다르면 서로 통과하지 않는다. 번호는 scope 안의 카운터다.

나머지 `permits` 호출은 기대 scope 인자를 받도록 고쳤다. 기존 허가·거부 단언은 유지했다.

### 수정 후 로컬 시험

작업 트리: `C:\Users\scarl\AppData\Local\Temp\aura-d01-wt`
명령: `.\gradlew.bat -p modules/domain clean test --offline --no-daemon --no-build-cache`
`JAVA_HOME`: `C:\Users\scarl\.jdks\temurin-17`
JVM: Temurin 17.0.20.1, `TEST_JVM path=C:\Users\scarl\.jdks\temurin-17`
Gradle: 9.3.1
코드 SHA: `558e18804d08ebd4d79be620962c256e0af07f96`
결과: `BUILD SUCCESSFUL in 37s`
XML: `closeout-green/junit-domain`, 9 files, `2026-11-28T10:20:06.243Z`–`2026-11-28T10:20:06.782Z`
집계: 102 tests, 0 failures, 0 errors, 0 skipped

같은 XML:

```
DOMAIN_INVENTORY rv01
DOMAIN_RESULT 102 PASS / 0 FAIL / 0 ERROR / 0 SKIP
```

종료 코드 0. 원문 `closeout-green/checker-rv01.txt`. `python -m unittest discover -s tests/unit -p test_domain_results.py -v`는 `Ran 24 tests` OK다. 검사기 소스는 바꾸지 않았다.

Intelligence는 제품 코드가 바뀌었으므로 다시 실행했다. 작업 트리 `C:\Users\scarl\AppData\Local\Temp\aura-d01-intel`는 detached `e050937fd34709d143836e44bbf91ec5221bdc48`이고 커밋하지 않았다. `modules/intelligence`는 그 HEAD와 차이가 없다. `modules/domain`은 `558e18804d08ebd4d79be620962c256e0af07f96`와 차이가 없다. 명령은 `.\gradlew.bat -p modules/intelligence clean test --offline --no-daemon --no-build-cache`다. `BUILD SUCCESSFUL in 51s`. XML은 `closeout-green/junit-intelligence`, 13 files, `2026-11-28T10:22:19.755Z`–`2026-11-28T10:22:24.983Z`다. 집계는 108 tests, 0 failures, 0 errors, 0 skipped다. `Round05Test.longRunKeepsInvariants()` PASSED. seed `20261128`, 반복 `100_000`. 컴파일 경고 1건은 기존 `Round08Test.kt:166`이다.

Gradle 디스크 XML은 CRLF다. Git blob은 autocrlf clean 뒤 LF다.

push refspec은 `558e18804d08ebd4d79be620962c256e0af07f96:refs/heads/agent/grok/GB-01-RV01`다. 이 SHA의 Domain Kotlin push `46134983359`와 pull_request `46134988468`은 각각 `BUILD SUCCESSFUL`, 검사기 `Ran 24 tests`, `DOMAIN_INVENTORY rv01`, `DOMAIN_RESULT 102 PASS / 0 FAIL / 0 ERROR / 0 SKIP`이다.

| 이벤트 | 워크플로 | run | 결과 |
| --- | --- | --- | --- |
| push | Active documentation budget | 46134983365 | success |
| push | Domain Kotlin | 46134983359 | success |
| push | Windows host reproducibility | 46134983399 | success |
| push | AURA Bootstrap | 46134983402 | success |
| pull_request | Active documentation budget | 46134988484 | success |
| pull_request | Domain Kotlin | 46134988468 | success |
| pull_request | Windows host reproducibility | 46134988488 | success |
| pull_request | AURA Bootstrap | 46134988466 | success |

위 8건은 모두 success다. 이 표를 담은 증거 커밋의 CI는 이 표에 포함하지 않는다.
