# GB-01 D01 — 관측값 불변성

상태: 후보. 독립 검수 전 HOLD. 제품 출시 NO-GO. PR #3 HOLD는 유지한다. GB-02 브랜치는 변경하지 않는다. R09, GB-03, GPT-07은 시작하지 않는다.

일자: 2026-11-28. 작업자: Grok Build. G5는 자기 재검토다.

기준: 착수 시점 `origin/main` `300edd17c95d22d6a0eceeba243299c9f8260664`. 보고 시점 `origin/main`은 `f3f3340ff5875176b526c5bb0e7c418c8c8a2739`다. 그 차이는 host repair, 중앙 문서, tools다. `modules/domain`과 겹치지 않고 PR #5는 MERGEABLE이다. D01은 그 커밋을 병합하지 않았고 tools와 중앙 문서를 수정하지 않았다. 브랜치 `agent/grok/GB-01-D01`. 동작 SHA `4cf85845a768e469d34fb26ae36914fffd009130`. 시험 배치 SHA `df843d75bff522dfd13f895e82ee07827626c9a5`. 두 SHA의 `modules/domain/src/main`은 같다. Intelligence 후보는 `e050937fd34709d143836e44bbf91ec5221bdc48`이고, 그 작업 트리의 `modules/domain/src/main`은 위 SHA와 차이가 없다. 연결은 `modules/intelligence/settings.gradle.kts`의 `includeBuild("../domain")`다. 증거 커밋은 `fd5a5c4547728d279ab1ffee9aa657bd40914fe5`다.

PRE-FLIGHT: PASS. PR #3은 OPEN이고 `mergedAt`은 null이며 head는 `0c4890ea7f69c6145791d17d51b98c97fed45c1d`다. STATUS의 다음 행동은 “Host 재현성 후보 4cf403199dd1; 3.14.7 PNG drift 재현. 공통 CI 확인 후 선택 통합. GPT-07/실기기 별도 승인.”이다. 그 문장을 바꾸지 않았다. 변경 전 Domain 시험은 81 PASS였다. 실제 소비 타입은 `Double`, `Boolean`, `String`, `Int`, `Long`, `Float`다.

## 구현

승인 상태에 넣는 값은 null, `Boolean`, `Byte`, `Short`, `Int`, `Long`, `Float`, `Double`, `Char`, `String`뿐이다. 그 외는 `IssueCode.UNSUPPORTED_PAYLOAD`로 거절하고 커서를 만들지 않는다. `classifiedValue()`는 그 값을 `Reading`으로 내리지 않고 `Inconsistent`로 둔다. `RevisionCursor` 생성과 `copy`는 예외로 막는다. 검증에 실패한 입력 객체는 복사하거나 고치지 않고 그대로 반환한다. 컬렉션은 읽기 전용 인터페이스여도 승인하지 않는다. 순환 객체는 내부를 따라가지 않는다. 새 의존성은 없다. 공개 생성자 시그니처는 바꾸지 않았다.

revision 비교, 중복, 충돌, TTL, 0, null, 단위, 오류 상태는 바꾸지 않았다. 더 높은 revision은 더 이른 관측 시각과 직전 `DENIED`를 대체한다. 이 우선순위는 권한 철회 시각과 충돌할 수 있다. 총괄 합의 없이 바꾸지 않았다.

## 재현과 시험

수정 전 로그 [payload-red-d01.log](payload-red-d01.log): 7개 중 5개 실패. 저장된 리스트가 `[kept]`에서 `[changed, more]`가 되었다. 분류 값과 커서가 돌려준 `[1]`이 `[9]`가 되었다. 순환 객체 라벨이 `cycle`에서 `changed`가 되었다. Map, Set, 중첩 리스트, 배열, 사용자 정의 객체는 커서로 승인되었다. 스칼라와 더 높은 revision 시험 둘은 그때도 통과했다.

`4cf8584`의 Domain Kotlin은 새 클래스 `PayloadIntegrityTest` 때문에 고정 검사기에서 `Unknown or duplicate suite`로 실패했다. Gradle 시험 자체는 그 회차에서 통과했다. `tools/check_domain_results.py`와 `tests/unit/test_domain_results.py`는 수정하지 않았다. `df843d7`은 같은 단언을 기존 메서드 `invalidIncomingDoesNotCreateOrReplaceCursor`, `higherRevisionReplacesAndGapIsAllowed`, `structurallyInvalidInputIsNotDegraded` 안으로 옮겼다. `@Test` 이름 집합은 81개다.

| 시험 | 결과 | 로그 |
|---|---|---|
| Domain clean JDK 17 `--no-daemon --offline --no-build-cache` | 81 PASS, 0 FAIL, 0 ERROR, 0 SKIP. XML 7파일. `tools/check_domain_results.py`는 `DOMAIN_RESULT 81 PASS`. BUILD SUCCESSFUL in 27s. `2026-11-28T06:08:55.749Z`–`2026-11-28T06:08:56.145Z` | [domain-test-summary-d01.log](domain-test-summary-d01.log), [junit-d01](junit-d01) |
| Intelligence clean, 같은 도메인 본문 | 108 PASS, 0 FAIL, 0 ERROR, 0 SKIP. XML 13파일. `longRunKeepsInvariants` PASS. BUILD SUCCESSFUL in 56s. `2026-11-28T06:01:57.815Z`–`2026-11-28T06:02:02.846Z` | [intelligence-test-summary-d01.log](intelligence-test-summary-d01.log), [junit-d01-intelligence](junit-d01-intelligence) |

환경: Windows. ASCII 작업 트리. 테스트 JVM Eclipse Temurin 17.0.20.1. Gradle 9.3.1. Kotlin 2.4.21. `--offline`. 본문이 같으므로 Intelligence clean은 다시 돌리지 않았다.

## CI

코드 SHA `df843d75bff522dfd13f895e82ee07827626c9a5`. 실패, 오류, 취소 0. Historical WFF는 시작하지 않았다. Bootstrap push 1회차는 Maven Central 429였고 제품 결함이 아니다. 같은 run의 2회차가 성공했다.

| 워크플로 | 이벤트 | run | job | 결과 |
|---|---|---|---|---|
| Domain Kotlin | push | 46115368127 | 140887873581 | success. Clean Kotlin domain tests, Validate JUnit evidence |
| Domain Kotlin | pull_request | 46115371543 | 140887884058 | success. 같은 두 단계 |
| AURA Bootstrap | push | 46115368080 | 140888586503 | success, attempt 2, 31 steps. Validation tool, Build debug APKs, Isolated Signature without bundle |
| AURA Bootstrap | pull_request | 46115371572 | 140887883883 | success, 31 steps. 같은 단계 |
| Windows host reproducibility | push | 46115368098 | 140887873485 host(true), 140887873251 host(false) | success. Full host regression |
| Windows host reproducibility | pull_request | 46115371539 | 140887884074 host(true), 140887883908 host(false) | success. Full host regression |
| Active documentation budget | push | 46115368168 | 140887873158 | success |
| Active documentation budget | pull_request | 46115371563 | 140887883750 | success |

Bootstrap은 intelligence 시험이 아니다. Domain Kotlin이 이번 도메인 변경의 CI다.

## D01-CLOSEOUT

최종 코드 SHA `ef57005a2177bf87db3193c454ca6888be819df0`. 위 81개 배치의 본문에 `ClassifiedValue.Reading`, `StatusDerivation.Unchanged`, `StatusDerivation.DegradedToStale` 생성과 `copy`의 스칼라 검사를 더했다. `Observation`과 `StatusDerivation.Rejected`는 검증 전 입력으로 남긴다. 공개 생성자 시그니처는 바꾸지 않았다. 직접 생성 호출은 `classifiedValue()`와 `deriveStatus()`뿐이다. Intelligence는 이 생성자를 호출하지 않는다. revision 우선순위, F04, C01은 바꾸지 않았다.

`PayloadIntegrityTest` 7개 메서드를 `4cf8584`에서 복원했다. 기존 81개 `@Test` 이름과 단언은 유지했다. `df843d7`이 기존 메서드 안에 넣었던 보조 호출은 복원된 시험과 범위가 같아 제거했다. 검사는 숨기지 않았다. 공통 검사기와 CI는 수정하지 않았다.

GPT가 등록할 정확한 추가 메서드 이름은 다음 7개다.

- `mutableListDoesNotReplaceStoredScalarOrChangeDuplicateVerdict`
- `mapSetNestedArrayAndCustomPayloadsAreRejected`
- `cyclicCustomObjectIsRejectedWithoutBeingWalked`
- `classifiedValueDoesNotPublishAMutablePayload`
- `directCursorConstructionRejectsMutablePayload`
- `scalarZeroNullAndDeniedStayAccepted`
- `higherRevisionStillReplacesEarlierDenial`

생성자 보완 전 [junit-d01-boundary-red](junit-d01-boundary-red): `classifiedValueDoesNotPublishAMutablePayload` 1건 실패. `ClassifiedValue.Reading`이 가변 리스트 `[1]`을 `VALID`로 만들었다. 나머지 6개 메서드는 통과했다. 시각 `2026-11-28T06:36:50.463Z`.

수정 후 JDK 17 clean `--offline --no-daemon --no-build-cache`:

| 시험 | 결과 | 로그 |
|---|---|---|
| Domain | 88 PASS, 0 FAIL, 0 ERROR, 0 SKIP. XML 8파일. `2026-11-28T06:38:45.360Z`–`2026-11-28T06:38:45.616Z`. BUILD SUCCESSFUL in 31s | [domain-test-summary-d01-closeout.log](domain-test-summary-d01-closeout.log), [junit-d01-closeout](junit-d01-closeout) |
| Intelligence `e050937`, `includeBuild("../domain")`, 도메인 본문 SHA256 8파일 일치 | 108 PASS, 0 FAIL, 0 ERROR, 0 SKIP. XML 13파일. `longRunKeepsInvariants` PASS. `2026-11-28T06:40:10.945Z`–`2026-11-28T06:40:15.670Z`. BUILD SUCCESSFUL in 46s | [intelligence-test-summary-d01-closeout.log](intelligence-test-summary-d01-closeout.log), [junit-d01-closeout-intelligence](junit-d01-closeout-intelligence) |

로컬 `tools/check_domain_results.py`는 `Unknown or duplicate suite: io.github.scarlel96.aura.domain.PayloadIntegrityTest`로 실패했다. 이 실패를 PASS로 적지 않는다. 이 브랜치는 검사기를 수정하지 않았다.

## CI

코드 SHA `ef57005a2177bf87db3193c454ca6888be819df0`. Historical WFF는 시작하지 않았다. 마감 증거 커밋은 `3f35eb7d2d6b9da4235d79cc6c722568add7e539`다.

브랜치 push의 Domain Kotlin은 등록 전 검사기다. `Clean Kotlin domain tests`는 success이고 `Validate JUnit evidence`만 실패했다. 원인은 `Unknown or duplicate suite: io.github.scarlel96.aura.domain.PayloadIntegrityTest`다. 이 결과를 PASS로 적지 않는다.

main `6645d35`가 같은 7개 메서드를 D01 목록으로 등록했다. pull_request는 그 목록으로 병합 커밋을 검사해 `DOMAIN_RESULT 88 PASS / 0 FAIL / 0 ERROR / 0 SKIP`을 출력했다. 이 브랜치에 tools나 workflow를 병합하지 않았다.

| 워크플로 | 이벤트 | run | job | 결과 |
|---|---|---|---|---|
| Domain Kotlin | push | 46117711549 | 140895136540 | failure. 시험 success, JUnit 목록 단계 failure |
| Domain Kotlin | pull_request | 46117715542 | 140895149260 | success. Clean Kotlin domain tests, Validate JUnit evidence, 88 PASS |
| AURA Bootstrap | push | 46117711548 | 140895137119 | success, 31 steps |
| AURA Bootstrap | pull_request | 46117715589 | 140895149661 | success, 31 steps |
| Windows host reproducibility | push | 46117711553 | 140895136633 host(true), 140895136808 host(false) | success. Full host regression |
| Windows host reproducibility | pull_request | 46117715539 | 140895149268 host(true), 140895149536 host(false) | success. Full host regression |
| Active documentation budget | push | 46117711562 | 140895136381 | success |
| Active documentation budget | pull_request | 46117715521 | 140895149024 | success |

보고 시점 `origin/main`은 `c646860948860d14b376a548fb50019a88c3dc9f`다. 차이는 중앙 문서와 이 마감 지시서다. Domain 파일과 겹치지 않아 병합하지 않았다. 중앙 STATUS 문장은 바꾸지 않았다.

## 게이트

| 게이트 | 결과 |
|---|---|
| G0 | PASS. 착수 main에서 새 브랜치. 제품 NO-GO. 이후 main `f3f3340`과 충돌 없음 |
| G1 | PASS, 한계 있음. 가변 페이로드는 거절. revision과 철회 시각의 우선순위는 합의 전 |
| G2 | 브랜치 push 검사기는 등록 전 FAIL. main과 합친 pull_request 검사는 `DOMAIN_RESULT 88 PASS` |
| G3 | PASS. Domain 88, Intelligence 108, 100000. JUnit FAIL/ERROR/SKIP 0 |
| G4 | PASS, 제한. 스칼라 소비자와 거절 경로. 실기기 NOT RUN |
| G5 | PASS, 자기 재검토. 독립 검수 NOT RUN |
| G6 | PASS, 제품 NO-GO. 로그와 XML. Bootstrap은 intelligence 시험이 아니다 |
| G7 | PASS, 제한. 이 보고서와 domain 가정 A28. 중앙 문서는 수정하지 않음 |

미해결: revision과 권한 철회 시각의 우선순위, F04, C01, intelligence 전용 CI, 실기기. 컬렉션 페이로드를 승인하는 계약은 없다. PR은 HOLD다.
