# GB-02 RV02 로컬 증거

상태: 로컬 구현과 로컬 시험만 완료. 브랜치 `agent/grok/GB-02-RV02`는 push하지 않았다. 공통 CI와 검사기 등록 전이다. 제품 판정은 NO-GO. PR #3, PR #5, PR #6은 변경하지 않았고 병합하지 않았다.

부모: `0c4890ea7f69c6145791d17d51b98c97fed45c1d` (`agent/grok/GB-02` G01 최종 HEAD)
Domain 오버레이: `558e18804d08ebd4d79be620962c256e0af07f96`
이 오버레이의 `modules/domain` blob은 그 SHA와 같고, 이 브랜치 커밋에는 넣지 않는다.
작업 트리: `C:\Users\scarl\AppData\Local\Temp\aura-rv02-wt`
기준 `origin/main`: `29e938b7c783988922c46298ff67321ca0ed5350`

## 수용 계약

`docs/operations/agent-orders/GB-02-RV02.md`와 ADR-008 Central disposition, RV01 최종 검수를 읽었다. `step`, `MachineState`, 보호 전달 의미, 임계값, 소비자는 바꾸지 않았다. F04, C01, R09, GB-03, GPT-07, 실제 SDK와 소비자 통합은 시작하지 않았다.

## 구현

`ProtectedBoundary`가 설정된 합성 scope와 stream마다 슬롯 하나를 가진다. 수신은 현재 coordinator의 `permits(capability, scope, request)`가 통과할 때만 그 capability와 관측 인스턴스를 묶는다. `read`와 `commit`이 같은 검사를 다시 한다. 공개 인터페이스를 직접 구현한 기록과 다른 scope로 다시 붙인 기록은 거절한다.

권한 무효화는 generation을 돌리고 그 scope의 대기·공개 값을 지운다. 더 큰 데이터 revision이라도 이전 generation은 공개하지 않는다. 재허가 뒤의 이전 기록도 공개하지 않는다. 재허가 이전 이력을 공개하는 함수는 없다.

`ERROR`와 `UNAVAILABLE`은 해당 stream만 지우고 순서 울타리를 올린다. 권한 generation은 유지한다. 울타리 이전 기록은 다시 공개되지 않고, 회복은 새 순서가 필요하다. 누락과 가변 페이로드는 0이 되지 않는다. `FORECAST`와 TTL은 권한 변경이 아니다. 순서는 `Long.MAX_VALUE`에서 잠기고 감싸지 않는다. `placeOrderAtCeiling`은 허가하지 않는다.

`Machine.kt`, `Policy.kt`, `Gate.kt`, `Axes.kt`는 `0c4890e`와 차이가 없다. 나중에 비워야 할 기계 필드는 `modules/intelligence/docs/INTERFACE_CONTRACT.md`의 보호 수신 경계에만 적었다.

직렬화한 기록은 발급 증거가 아니다. `commit`을 무효화와 겹치지 않게 호출하는 compare-and-commit은 어댑터 의무다. 리플렉션 격리, SDK 인증, 동시성, 저장, 소비자 삭제는 증명하지 않는다.

## 신규 시험 식별자

클래스 `io.github.scarlel96.aura.intelligence.ProtectedBoundaryTest`

- `currentCapabilityPublishesOnlyItsScopeAndRequest()`
- `foreignScopeAndRequestCannotPublish()`
- `forgedRecordAndMutablePayloadCannotReplaceEnvelope()`
- `revocationRejectsQueuedHigherRevision()`
- `regrantRejectsOldResultAndAcceptsFreshAcquisition()`
- `finalReadRechecksPermitAndDropsQueuedMessage()`
- `ordinaryErrorWithdrawsOnlyThatStream()`
- `unavailableWithdrawsStreamWithoutChangingAuthority()`
- `staleReplayAfterWithdrawalCannotResurrect()`
- `independentStreamsStayIsolated()`
- `missingInvalidForecastAndTtlStaySeparateFromAuthority()`
- `orderSaturationFailsClosedWithoutWrapping()`
- `unknownMappingRejectsProtectedData()`
- `historyStaysUnpublishedByDefault()`
- `unprotectedObservationAndOtherScopeStayUntouched()`
- `genericRevisionStillAcceptsHigherRevisionOutsideTheBoundary()`

이 16개는 등록된 Intelligence 108개에 포함되지 않는다. 기존 108개 식별자와 기대는 유지한다.

## Intelligence

명령: `.\gradlew.bat -p modules/intelligence clean test --offline --no-daemon --no-build-cache`
`JAVA_HOME`: `C:\Users\scarl\.jdks\temurin-17`
JVM: Temurin 17.0.20.1
Gradle: 9.3.1
`includeBuild("../domain")`가 오버레이를 사용했다.
결과: `BUILD SUCCESSFUL in 45s`
XML: `junit-intelligence`, 14 files, `2026-11-28T11:04:08.756Z`–`2026-11-28T11:04:13.562Z`
집계: 124 tests, 0 failures, 0 errors, 0 skipped
기존 108개에 신규 16개를 더한 수량이다. `Round05Test.longRunKeepsInvariants()` PASSED. seed `20261128`, 반복 `100_000`.
컴파일 경고 1건은 기존 `Round08Test.kt:166`이다.

## Domain

명령: `.\gradlew.bat -p modules/domain clean test --offline --no-daemon --no-build-cache`
같은 JVM.
결과: `BUILD SUCCESSFUL in 35s`
XML: `junit-domain`, 9 files, `2026-11-28T11:04:57.708Z`–`2026-11-28T11:04:58.149Z`
집계: 102 tests, 0 failures, 0 errors, 0 skipped
`AuthorityContractTest` 14개와 기존 88개가 포함된다. Domain 소스는 이 브랜치에 커밋하지 않는다.

Gradle 디스크 XML은 CRLF다. Git blob은 autocrlf clean 뒤 LF다.

## 이번 로컬 후보가 닫지 않는 것

RV-01~16 제품 수용을 완료로 말하지 않는다. 실제 배터리·건강·날씨 권한 범주, SDK 결과 결합, 기계 필드 소거, 이력 허용 정책, OS 캐시, 동시성, 소비자 지연, 공통 CI, 검사기 등록은 NOT RUN이다. 합성 scope와 stream만 사용했다.

## G0–G7

G0: 작업지시, ADR-008 Central disposition, RV01 최종 검수, 현재 Authority와 Intelligence 계약을 확인했다.
G1: 격리된 수신·공개 경계만 추가했다.
G2: 로컬 clean 시험이다. 공통 CI는 실행하지 않았다.
G3: Intelligence 124 PASS, 그중 기존 108과 100000회. Domain 102 PASS. FAIL/ERROR/SKIP 0.
G4: SDK, 실기기, 동시성은 NOT RUN.
G5: 독립 검수 전이 아니다.
G6: 로컬 후보. 제품 NO-GO. PR HOLD 유지.
G7: 이 문서와 원본 XML.
