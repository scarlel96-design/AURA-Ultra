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

브랜치를 push하지 않았다. `origin`에 `agent/grok/GB-01-RV01` ref는 없다. main 병합과 강제 푸시를 하지 않았다. PR #3과 PR #5의 본문, head, 상태를 바꾸지 않았다. D01 재작업, Intelligence 수정, 검사기 우회, 기존 시험 삭제, 단언 약화를 하지 않았다.
