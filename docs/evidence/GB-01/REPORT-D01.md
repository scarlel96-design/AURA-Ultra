# GB-01 D01 — 관측값 불변성

상태: 후보. 독립 검수 전 HOLD. 제품 출시 NO-GO. PR #3 HOLD는 유지한다. GB-02 브랜치는 변경하지 않는다. R09, GB-03, GPT-07은 시작하지 않는다.

일자: 2026-11-28. 작업자: Grok Build. G5는 자기 재검토다.

기준: 착수 시점 `origin/main` `300edd17c95d22d6a0eceeba243299c9f8260664`. 보고 시점 `origin/main`은 `f3f3340ff5875176b526c5bb0e7c418c8c8a2739`다. 그 차이는 host repair, 중앙 문서, tools다. `modules/domain`과 겹치지 않고 PR #5는 MERGEABLE이다. D01은 그 커밋을 병합하지 않았고 tools와 중앙 문서를 수정하지 않았다. 브랜치 `agent/grok/GB-01-D01`. 동작 SHA `4cf85845a768e469d34fb26ae36914fffd009130`. 시험 배치 SHA `df843d75bff522dfd13f895e82ee07827626c9a5`. 두 SHA의 `modules/domain/src/main`은 같다. Intelligence 후보는 `e050937fd34709d143836e44bbf91ec5221bdc48`이고, 그 작업 트리의 `modules/domain/src/main`은 위 SHA와 차이가 없다. 연결은 `modules/intelligence/settings.gradle.kts`의 `includeBuild("../domain")`다. 증거 커밋 SHA는 기록 커밋이 가리킨다.

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

## 게이트

| 게이트 | 결과 |
|---|---|
| G0 | PASS. 착수 main에서 새 브랜치. 제품 NO-GO. 이후 main `f3f3340`과 충돌 없음 |
| G1 | PASS, 한계 있음. 가변 페이로드는 거절. revision과 철회 시각의 우선순위는 합의 전 |
| G2 | PASS. 기존 81개 메서드와 고정 검사기 |
| G3 | PASS. 81, 108, 100000. FAIL/ERROR/SKIP 0 |
| G4 | PASS, 제한. 스칼라 소비자와 거절 경로. 실기기 NOT RUN |
| G5 | PASS, 자기 재검토. 독립 검수 NOT RUN |
| G6 | PASS, 제품 NO-GO. 로그와 XML. Bootstrap은 intelligence 시험이 아니다 |
| G7 | PASS, 제한. 이 보고서와 domain 가정 A28. 중앙 문서는 수정하지 않음 |

미해결: revision과 권한 철회 시각의 우선순위, F04, C01, intelligence 전용 CI, 실기기. 컬렉션 페이로드를 승인하는 계약은 없다. PR은 HOLD다.
