# GB-02 RV02 로컬 증거

상태: RV02-C1, C2, C3만 PR #7에서 보완했다. 제품 판정은 NO-GO. PR #7은 HOLD이며 main에 병합하지 않았다. PR #3, PR #5, PR #6은 변경하지 않았고 병합하지 않았다.

구현 커밋: `dbacc75d559699963eeeb8d9da40692f07b8ddf2`
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

RV-01~16 제품 수용을 완료로 말하지 않는다. 실제 배터리·건강·날씨 권한 범주, SDK 결과 결합, 기계 필드 소거, 이력 허용 정책, OS 캐시, 동시성, 소비자 지연은 NOT RUN이다. 합성 scope와 stream만 사용했다.

## G0–G7

G0: 작업지시, ADR-008 Central disposition, RV01 최종 검수, 현재 Authority와 Intelligence 계약을 확인했다.
G1: 격리된 수신·공개 경계만 추가했다.
G2: 로컬 clean 시험과 등록된 Intelligence RV02 복합 CI를 실행했다. 아래 원격 제출을 본다.
G3: Intelligence 124 PASS, 그중 기존 108과 100000회. Domain 102 PASS. FAIL/ERROR/SKIP 0.
G4: SDK, 실기기, 동시성은 NOT RUN.
G5: 독립 검수 전이 아니다.
G6: 원격 후보. 제품 NO-GO. PR #7 HOLD. main 병합 없음.
G7: 이 문서와 원본 XML. 원본 XML 시각은 바꾸지 않았다.

## 원격 제출

등록 커밋 `00118b4228a5e18d0cb621cef90de8b246d247b5`의 main CI가 성공한 뒤에만 `origin/main`을 병합했다. main Intelligence RV02 `46139294149`는 도구 자체 시험 10개만 실행했다. main에서는 복합 Gradle 단계가 조건으로 빠진다. 그 실행을 Domain 102 또는 Intelligence 124로 세지 않는다.

병합 커밋: `20370a6fcacbd25df12edc4aabc97acf9ff66a1c`
부모: `a611bda7518f8d9971899048e318216319887201`, `00118b4228a5e18d0cb621cef90de8b246d247b5`
Intelligence 트리: `cbbb838836f206ae0363796bc1812f5dcc8e9083` (구현 커밋과 동일, 29개 파일)
`ProtectedBoundary.kt`: `22ae61652623ff20da274c825f6a6f4dde6c8857`
`ProtectedBoundaryTest.kt`: `c9423cebeba480e0cef874f5eadb94f9307107bb`
커밋된 Domain 트리: `65c0180c6706c138370e0a465a6cc53f92f331a4` (`origin/main`과 동일)
고정 Domain 트리: `c51dfeb3fe4e87201f123cd89aceb48b373a0aaf`, 26개 파일. 합성 복원만 사용한다.

로컬 스크래치 `C:\Users\scarl\AppData\Local\Temp\rv02-composite-20370a6`에서 등록 도구로 복원한 뒤 JDK 17 clean offline 시험을 다시 실행했다. 시험 전후 `--verify-only`가 같은 pin을 출력했다. `check_domain_results.py --profile rv01`은 102, `check_intelligence_results.py --profile rv02`는 124였다. 등록 도구 자체 시험은 10 PASS다.

`20370a6` push Intelligence RV02 `46140337455`:
`RV02_DOMAIN commit=558e18804d08ebd4d79be620962c256e0af07f96 tree=c51dfeb3fe4e87201f123cd89aceb48b373a0aaf files=26`
`RV02_INTELLIGENCE commit=20370a6fcacbd25df12edc4aabc97acf9ff66a1c tree=cbbb838836f206ae0363796bc1812f5dcc8e9083 files=29`
도구 시험 Ran 10 tests. `DOMAIN_RESULT 102 PASS / 0 FAIL / 0 ERROR / 0 SKIP`. `INTELLIGENCE_RESULT 124 PASS / 0 FAIL / 0 ERROR / 0 SKIP`. `longRunKeepsInvariants()` PASSED. 시험 후 verify-only가 같은 두 줄을 다시 출력했다. artifact `rv02-composite-junit-xml` ID 15261302261.

`20370a6` pull_request Intelligence RV02 `46140347797`는 GitHub PR 병합 checkout `90e75e0a00432d6caa3fd52385946c56fdefcfb5`를 검사했다. Intelligence 트리는 같은 `cbbb838836f206ae0363796bc1812f5dcc8e9083`, 29개 파일이다. Domain pin, 102, 124, 10 tests, longRun, verify-only, artifact 15261468125가 같다.

같은 SHA의 공통 CI는 모두 success다. 문서 예산 push `46140337718`, pull_request `46140347741`. Windows push `46140337616`, pull_request `46140347752`. Bootstrap push `46140337539`, pull_request `46140347724`.

Domain Kotlin push `46140337510`은 `DOMAIN_INVENTORY baseline`, `DOMAIN_RESULT 81 PASS / 0 FAIL / 0 ERROR / 0 SKIP`이다. 커밋된 baseline이며 overlay 102가 아니다. pull_request Domain Kotlin은 경로 필터로 시작되지 않았다.

도구 자체 시험 로그에 나오는 다른 `RV02_DOMAIN` SHA는 합성 저장소 시험이다. 제품 pin은 `558e188`뿐이다.

## RV02-CLOSEOUT

PRE-FLIGHT: main `958e69b3c00a7c95c68def03a69605d179db930e`는 검수 기록과 마감 지시만 추가했다. 병합 `de77cdf4f12a6b1087bf6c8b9d66645321eb4f87`. PR #3 `0c4890e`, PR #5 `d847028`, PR #6 `68f52eb`는 OPEN이다. 제품 NO-GO. 활성 지시는 RV02-C1, C2, C3이다.

수정 전 `75c9ab4` 코드에서 기존 16개 이름 중 5개가 실패했다. `closeout-red` 시각 `2026-11-28T12:32:46.627Z`, tests 16, failures 5, errors 0, skipped 0.

- C1: 장애 뒤 같은 capability의 지연 결과가 `ACCEPTED`였다. 같은 acquisition의 더 높은 revision 교체도 `ACCEPTED`였다.
- C2: `commit`에 `Instant` 매개변수가 없어 최종 시각을 전달할 수 없었다.
- C3: `ACCEPTED` 기록이 페이로드 `12.0`을 노출했다. 새 값이 남은 상태에서 오래된 기록의 `commit`은 `WITHDRAWN`이었다.

고친 단언은 그 세 가지를 더 이상 허용하지 않는다. 같은 capability 재사용을 통과시키던 `staleReplayAfterWithdrawalCannotResurrect`는 새 acquire와 `CURRENT`만 받는다. 승인 전 `payload()`를 읽던 단언은 영수증에 페이로드가 없음을 확인한다. 오래된 영수증의 `WITHDRAWN`은 `STALE_RECEIPT` 거절로 바꿨고, 새 공개 값은 지우지 않는다. 시험 식별자 16개와 기존 108개는 유지했다.

구현 `8dd1c7c6dab9c61f824d60f3bfed9fe2b2a2e239`. Intelligence 트리 `dcd75fb4809140dfe806c8f504da08cd565630eb`, 29개 파일. Domain 오버레이는 커밋하지 않았다.

스크래치 `C:\Users\scarl\AppData\Local\Temp\rv02-composite-8dd1c7c`. JDK 17 clean offline no-daemon no-build-cache. 시험 전후:

`RV02_DOMAIN commit=558e18804d08ebd4d79be620962c256e0af07f96 tree=c51dfeb3fe4e87201f123cd89aceb48b373a0aaf files=26`

`RV02_INTELLIGENCE commit=8dd1c7c6dab9c61f824d60f3bfed9fe2b2a2e239 tree=dcd75fb4809140dfe806c8f504da08cd565630eb files=29`

`DOMAIN_RESULT 102 PASS / 0 FAIL / 0 ERROR / 0 SKIP`. `INTELLIGENCE_RESULT 124 PASS / 0 FAIL / 0 ERROR / 0 SKIP`. `longRunKeepsInvariants()` PASSED. seed `20261128`, 반복 `100000`. 도구 자체 시험 10 PASS. 원본 `junit-domain`과 `junit-intelligence`는 그대로 두고, 초록 XML은 `closeout-green`에 뒀다. Domain 9개 `2026-11-28T12:38:47.482Z`–`2026-11-28T12:38:47.970Z`. Intelligence 14개 `2026-11-28T12:39:27.059Z`–`2026-11-28T12:39:31.780Z`.

이 기록 커밋은 `modules/intelligence`를 바꾸지 않는다. 복합 CI의 HEAD는 기록 커밋이고 Intelligence 트리는 `dcd75fb4809140dfe806c8f504da08cd565630eb`이다. 원격 실행 식별자는 PR 본문에 적는다. 여기 있는 102/124는 로컬 스크래치 결과다.
