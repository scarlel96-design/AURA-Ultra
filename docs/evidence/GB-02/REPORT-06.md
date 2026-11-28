# GB-02 G01 / R06 감사 개선

상태: GO (독립 모듈 통합 후보). 제품 출시 NO-GO. PR #3은 병합하지 않는다. 외부 PR 통합 HOLD는 유지한다. R07은 시작하지 않는다.

일자: 2026-11-28. 작업자: Grok Build. 검토자: 없음. G5는 자기 재검토다.

기준 브랜치: `agent/grok/GB-02`. 구현 SHA: `14328ae19845a6c65c848e210a7d89991bdea812`. 이 보고서 커밋은 `modules/intelligence`를 바꾸지 않아야 한다. 확인은 `git diff 14328ae19845a6c65c848e210a7d89991bdea812 -- modules/intelligence`가 비어 있는지로 한다.

PRE-FLIGHT: PASS. 시작 시점 `origin/main`은 `860b51d4f26abf44aa1608fc12184716d1380169`다. 지시서가 적던 기준 `b6de0a245c5880c9c08ddb132d90c239b49ff6f2`보다 앞이다. 같은 SHA에서 `AGENTS.md`, `docs/STATUS.md`, `docs/operations/RESUME_PROTOCOL.md`, `PROJECT_INVARIANTS.md`, `TASK_RECORD_PROTOCOL.md`, `VERIFICATION_PROTOCOL.md`, `TASK_REPORT_TEMPLATE.md`, `GPT_EXECUTION_PLAN.md`, `BLOCKERS.md`, `WORK_LOG.md`, `docs/operations/agent-orders/README.md`, `GB-02-G01-R06.md`, `docs/evidence/MID-AUDIT/REPORT-R02.md`, `FINDINGS.md`, `REMEDIATION-PLAN.md`를 읽었다. PR #3 HEAD는 시작 시점 `122d81b05fb0fc56020fb3d03b667545eb6671c3`이고 구현 정본은 `1536fd7fad37b52375e7eccbb6114b8fd1f735c6`이었다. 그때 STATUS의 다음 행동은 F01 R02 후보 검증이었다. 그 문장을 직접 바꾸지 않았다. 배정표는 GB-02를 `R05 제출, G01 R06 지시서 작성·실행 미확인, HOLD`로 적는다. 사용자 지시는 그 HOLD 아래의 R06 실행이다. 통합 HOLD를 해제하지 않는다. 그 main 차이는 중앙 문서, 감사 증거, `tests/unit/test_f01_r01.py`, `tools/` 일부다. `modules/intelligence`, `modules/domain`, `.github`와 겹치지 않아 병합 커밋 `ed16d750f9e0f058b945d16e43f2247b72aeb166`로만 반영했다. 들어온 파일은 수정하지 않았다.

증거 커밋 직전 `origin/main`은 `12a5f609c8002df84547ec416566d582eef2c173`으로 이동했다. 차이는 `.github/workflows/domain-kotlin.yml`의 경로 필터, 중앙 문서, F01/F02 증거, `tests/unit/test_domain_results.py`, `tests/unit/test_f01_r02.py`, `tools/check_domain_results.py`, `tools/verify_wff.py`다. `modules/intelligence`, `modules/domain` 소스, `docs/evidence/GB-02`와 겹치지 않아 병합 커밋 `42dbb49fdcbef432c278caa4ec316d04af4d5141`로만 반영했다. 들어온 파일은 수정하지 않았다. 병합된 STATUS의 다음 행동은 `F02 R02 후보 Linux/Windows 최종 검증 → 아티팩트 확인 → 통합 조건 확인. GPT-07 및 실기기 설치는 별도 승인 대기.`다. 그 문장도 바꾸지 않는다.

작업 목표: AUD-R02-01, AUD-R02-05, AUD-R02-08, AUD-R01-06만 고친다. R05의 72개 intelligence 시험, 81개 domain 시험, 시드 `20261128`의 100000회 전이, `reasonCodes` 불변화는 유지한다. 공통 CI, domain, WFF, 중앙 문서는 수정하지 않는다.

## 구현 및 결정

| 파일 | 변경 | 요구사항 |
|---|---|---|
| `Gate.kt` | `DENIED`/`ERROR`/`UNAVAILABLE`은 TTL이 null이거나 만료여도 그 사유를 유지하고 `Freshness`를 같이 둔다. 숫자는 공개하지 않는다. | AUD-R02-01 |
| `Machine.kt` | 만료 freshness는 `STALE_IGNORED`, 미선언 freshness는 `UNDECLARED_IGNORED`를 상태 사유와 함께 낸다. 유효 TTL은 추가하지 않는다. | AUD-R02-01 |
| `Policy.kt`, `Gate.kt` | 공백·NUL·제어문자 단위는 정책을 거절한다. `gateDouble`의 비유한 경계와 뒤집힌 최소·최대는 값을 `Fresh`로 만들지 않고 `REJECTED`다. 0과 100 포함 경계는 유지한다. | AUD-R02-05, AUD-R02-08 |
| `check_junit_xml.py` | 빈 classname·메서드, suite와 다른 classname, 빠진 카운터, `TEST-{suite}.xml` 불일치, 중첩 `testcase`, `--not-after`보다 늦은 시각을 거절한다. | AUD-R01-06 |
| `Round06Test.kt`, `JunitXmlCheckTest.kt` | 수정 전 실패를 그대로 두는 부정 시험. 기존 시험 단언은 바꾸지 않았다. | 회귀 |

결정: freshness를 상태 사유로 덮지 않는다. 미래 시각의 허용 오차는 호출자가 주는 `--not-after`다. 그 시각과 같으면 통과하고, 더 늦으면 거절한다. 관측 시각의 제품 오차는 정하지 않았다. 공통 JUnit 검사기와 `.github/workflows`는 수정하지 않았다. 제안 구조는 `CI_PROPOSAL.md`에만 있다.

시도한 접근: 카운터를 모두 뺀 XML과 헤더 수와 어긋난 중첩 `testcase`는 기존 검사기가 이미 다른 이유로 거절했다. 수용되던 형태는 `tests`만 있고 `failures`/`errors`/`skipped`가 없는 XML, 그리고 헤더가 중첩 `testcase`까지 세는 XML이다. 재현 로그는 그 형태다.

## 요구사항 추적

| ID | 시험 | 수정 전 | 수정 후 | 판정 |
|---|---|---|---|---|
| AUD-R02-01 | `permissionStatusStaysDistinctFromTtl` | `DENIED`+null TTL이 `UNDECLARED` | 9조합에서 원 상태 유지, freshness 분리, 공개 숫자 null | PASS |
| AUD-R02-05 | `abnormalUnitTokensAreRejected` | `" percent"`가 `issues=[]` | 7개 비정상 토큰 `PolicyRejected`, `percent`와 0은 유지 | PASS |
| AUD-R02-08 | `nonFiniteAndInvertedBoundsAreRejected` | NaN 경계가 `Fresh(999)` | NaN·Infinity·역전 경계 `REJECTED`, 0·100·NaN 값 거절 유지 | PASS |
| AUD-R01-06 | `JunitXmlCheckTest` 7개 | 6개는 exit 0, 미래 시각은 `--not-after` 미지원 | 7개 거절. 기존 13개와 정상 10/82·7/81 유지 | PASS |
| R05 회귀 | 기존 72 + domain 81 + `longRunKeepsInvariants` | 유지 대상 | 82 PASS, 81 PASS, 100000회 1메서드 PASS | PASS |

시험 메서드 수와 단언 수를 구분한다. 신규 메서드는 `Round06Test` 3개와 `JunitXmlCheckTest` 7개다. AUD-R02-01 메서드 1개 안에 상태 3개 × TTL 3개의 단언이 있다. 100000회는 `Round05Test.longRunKeepsInvariants` 1개 메서드 안의 전이다. 100000개 시험이 아니다.

## 검증 결과

| 시험 | 명령 | 결과 | 판정 | 로그 |
|---|---|---|---|---|
| 수정 전 재현 | intelligence `Round06Test`와 JUnit 7개 | 10 completed, 10 failed | PASS, 재현 | [intelligence-repro-r06.log](intelligence-repro-r06.log) |
| intelligence clean JDK 17 | `gradlew -p modules/intelligence test --rerun-tasks --offline` | 82 PASS, 0 FAIL, 0 ERROR, 0 SKIP. XML 10파일. BUILD SUCCESSFUL in 53s | PASS | [intelligence-test-summary-r06.log](intelligence-test-summary-r06.log), [junit-r06](junit-r06) |
| domain 회귀 | `gradlew -p modules/domain test --rerun-tasks --offline` | 81 PASS, 0 FAIL, 0 ERROR, 0 SKIP. XML 7파일. BUILD SUCCESSFUL in 21s | PASS | [domain-regression-r06.log](domain-regression-r06.log), [junit-r06-domain](junit-r06-domain) |
| 장시간 전이 | 위 스위트의 `longRunKeepsInvariants` | PASSED. 시드 20261128, 한 메서드 안 100000회 | PASS | 같은 intelligence 로그 |
| JUnit 창 | `check_junit_xml.py --not-before 2026-11-28T01:20:51.968Z --not-after 2026-11-28T01:22:09.401Z` | `OK files=10 tests=82`, `OK files=7 tests=81` | PASS | 같은 실행의 XML |
| 호스트, 구현 직후 | `python -m unittest discover -s tests/unit -p test_*.py` | 330 ran, 328 PASS, 1 FAIL, 1 ERROR, 0 SKIP, 60.654s | 환경 | [host-unit-r06.log](host-unit-r06.log) |
| 호스트, main `12a5f60` 병합 후 | 같은 명령 | 346 ran, 344 PASS, 1 FAIL, 1 ERROR, 0 SKIP, 36.858s | 환경 | [host-unit-r06-postmerge.log](host-unit-r06-postmerge.log) |
| 문서 예산, 같은 병합 후 | `python tools/check_doc_budget.py` | 모든 활성 문서가 한도 안. exit 0 | PASS | 이 표 |
| domain 증거 검사, 같은 병합 후 | `python tools/check_domain_results.py docs/evidence/GB-02/junit-r06-domain` | `DOMAIN_RESULT 81 PASS / 0 FAIL / 0 ERROR / 0 SKIP` | PASS | 저장한 domain XML |
| 실기기, 공급원, WFF, 배터리, intelligence용 GitHub CI | 미실행 | NOT RUN | NOT RUN | 없음 |

환경: Windows. ASCII worktree `C:\Users\scarl\AppData\Local\Temp\aura-gb02-wt`. 테스트 JVM Eclipse Temurin 17, `C:\Users\scarl\.jdks\temurin-17`. Gradle 9.3.1. Kotlin 2.4.21. Python 3.14.7. Intelligence XML `2026-11-28T01:21:20Z`대, domain XML `2026-11-28T01:21:46Z`대. 시각은 UTC다.

호스트 1 ERROR는 기존 Windows `palette.svg` CRLF다. 소유 경로 밖이라 수정하지 않았다. 1 FAIL은 `tests/unit/test_f01_r01.py`의 `test_normal_artifact_preserved`다. Windows에서 `signature_material.generate()`가 만든 PNG 다이제스트가 기록된 값과 다르다. `tools/`는 수정하지 않았다. 두 결과는 구현 직후 330개와 main `12a5f60` 병합 후 346개에서 같다. 추가된 16개는 PASS다. main Ubuntu CI `46090317180`은 당시 330개를 PASS로 기록했다. 이 브랜치의 Ubuntu bootstrap이 현재 스위트를 다시 실행한다. `modules/intelligence`와 `modules/domain` 소스는 두 번째 main 병합으로 바뀌지 않아 82개와 81개 Gradle 시험은 재실행하지 않았다. 저장한 domain XML은 병합된 `check_domain_results.py`에서 81 PASS다.

CI 실행 ID: 이 보고서 시점에는 회차 06 head의 bootstrap이 아직 없다. push 뒤의 기록 커밋에 적는다. bootstrap은 intelligence 시험을 실행하지 않는다. 모듈 시험은 위 로컬 로그가 정본이다.

## G0~G7

| 게이트 | 판정 | 근거 |
|---|---|---|
| G0 | PASS | PRE-FLIGHT 문서를 최신 main에서 읽었다. 범위는 네 감사 항목이다. |
| G1 | PASS | 9개 상태/TTL, 비정상 단위, 비유한·역전 경계, JUnit 7종이 구현과 연결된다. |
| G2 | PASS | 수정 전 10 failed. 수정 후 같은 시험이 거절한다. 기존 단언은 유지했다. |
| G3 | PASS | intelligence 82, domain 81, 100000회 1메서드. FAIL 0, ERROR 0, SKIP 0. |
| G4 | PASS, 제한 | 데이터/FSM의 TTL과 권한 사유를 분리했다. 실기기·공급원은 NOT RUN. |
| G5 | PASS, 자기 재검토 | 독립 검토자는 NOT RUN. 열린 P0/P1은 이 변경에 없다. |
| G6 | PASS, CI 기록 전 | 코드 SHA `14328ae`. bootstrap ID는 push 뒤 기록. 제품 GO로 올리지 않음. |
| G7 | PASS, 제한 | 중앙 STATUS/WORK_LOG/BLOCKERS는 수정하지 않았다. 제안만 아래에 둔다. |

최종 판정: 독립 모듈 통합 후보. 기존 72개와 domain 81개를 유지하고 신규 10개 메서드가 통과했다. intelligence와 domain은 FAIL 0, ERROR 0, SKIP 0이다. 100000회 불변 조건 위반은 0이다. 담당 경로 위반은 0이다. 공통 워크플로는 수정하지 않았고 main으로는 병합하지 않았다. 최신 main은 이 브랜치로만 병합했다.

제품 출시 판정: NO-GO.

## 통합 차단점

| ID | 상태 | 해결 조건 |
|---|---|---|
| AUD-R02-01/05/08, AUD-R01-06 | 이 모듈에서 시험으로 닫음 | 중앙 `FINDINGS.md` 갱신은 총괄이 한다. 이 보고서가 등록부를 닫지 않는다. |
| GB02-R05-ASYNC | P2 유지 | 호출 순서, null이 아닌 `deliveredIntent()`, 더 이른 `processedAt` 폐기. Wear/WFF 코드는 없다. |
| AUD-R02-02/03/04/06/07, AUD-R02-10/11 | R07 후보, 미구현 | R06 범위 밖. 미래 관측 오차와 제품 임계값은 정하지 않았다. |
| 공통 CI | 미적용 | 총괄이 `CI_PROPOSAL.md`를 적용한다. 기대 수량은 10/82와 7/81이다. |
| 호스트 Windows | 환경 | 병합 후 346개 중 344 PASS, 1 FAIL, 1 ERROR. CRLF와 로컬 PNG 다이제스트. Ubuntu bootstrap으로 재확인. |
| 제품 출시 | NO-GO | 실기기, 공급원, WFF, 배터리, 확정 임계값 없음. |

## 중앙 문서 제안

- STATUS: 현재 다음 행동인 F02 R02 후보 Linux/Windows 최종 검증을 빼지 않는다. GB-02 PR #3 회차 06은 로컬 intelligence 82 PASS, domain 81 PASS, 로컬 호스트 346 중 344 PASS / 1 FAIL / 1 ERROR, 실기기와 intelligence 모듈 CI는 NOT RUN, 제품 NO-GO, PR은 미병합이라고 한 줄 추가할 수 있다.
- WORK_LOG: 같은 한 줄을 추가할 수 있다.
- BLOCKERS: 변경하지 않는다. R07 후보와 GB02-R05-ASYNC는 이 보고서의 차단점이다.
- FINDINGS: 총괄이 네 ID의 해결 증거를 이 보고서와 맞춘 뒤에만 상태를 바꾼다.
- `.github/workflows`: 변경하지 않는다.

다음 행동: 총괄이 PR #3을 검토한다. main 병합, 공통 워크플로 수정, R07, GB-03, GPT-07은 시작하지 않는다.
