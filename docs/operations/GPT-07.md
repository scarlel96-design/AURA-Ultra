# GPT-07 — 도메인·장애 복구 기반
2026-11-28 KST. IN_PROGRESS / PARTIAL. 사용자 승인: 독립 기능 개발과 잔여 감사 차단점 분리. 실제 통합 및 출시 조건은 변경하지 않는다. 기준 main af06adc90e9d4c086b3441275092303691619802. R-03/04/11/12/13/14/15/16/17/18/21/22, WO-17~23. 정식 WO GO 0/38, GPT GO 3/12, 감사 14/16. 제품 NO-GO.
## 기존 후보 재사용 및 소유권
| 후보 | SHA | 범위 |
|---|---|---|
| D01 / #5 | d847028dc914ebb0acfbf47ff6b83a179d9bf486 | 불변성 88, 독립 종료 |
| RV01 / #6 | 68f52ebd1914c7045e34f093fd91516c73af116b | 권한 순수 계약 102, 독립 종료 |
| G01 / #3 | 0c4890ea7f69c6145791d17d51b98c97fed45c1d | FSM 108, 독립 종료 |
| RV02 / #7 | 7501dcfe990c7f16123b8fdc44a90baf7354533b | 경계 124, PARTIAL/독립 중지 |
기존 후보 모두 HOLD. 합성 시험을 재사용하고 기존 기능을 다시 작성하지 않는다. modules/domain/**, modules/intelligence/**, AG 경로 변경 및 인수는 별도 승인 전 금지한다. GPT는 신규 독립 경로와 중앙 운영 문서를 소유한다. F03/F04/RV02 및 기기 차단은 필수 통합 조건이다. [F03 검수](../evidence/MID-AUDIT/F03/REPORT-CODEX-REVIEW.md), [RV02 검수](../evidence/MID-AUDIT/RV02-REVIEW.md), [차단점](BLOCKERS.md).
## R01 — WO-23 재시도 계산기
후보 branch candidate/gpt-07-r01, commit 02533470f141077d530acbfa04f6b20136b3763e. [보고서](https://github.com/scarlel96-design/AURA-Ultra/blob/02533470f141077d530acbfa04f6b20136b3763e/docs/evidence/GPT-07/R01/REPORT.md), [시험 로그](https://github.com/scarlel96-design/AURA-Ultra/blob/02533470f141077d530acbfa04f6b20136b3763e/docs/evidence/GPT-07/R01/retry-test.log).
구현: modules/cache/src/main/kotlin/io/github/scarlel96/aura/cache/RetryPlanner.kt. 별도 순수 Kotlin 파일, 신규 의존성 및 Gradle 변경 없음. 합성 일시 오류/요청 제한, 지수 백오프·지연 상한·횟수·server delay floor·jitter·deadline·overflow. 실제 네트워크/캐시/권한/센서 사용 없음. 설정값은 호출자 입력이며 정식 정책 미확정. 허용된 retry 계획은 권한 증명이 아니다. 호출자는 실제 요청 직전 권한·세션·연결·AOD·기한·횟수를 검증해야 한다.
검증: 로컬 kotlinc 1.9.0 / JDK21 / JVM17 target; 21 named PASS, seed20261128 50,000 BigInteger 산술 대조, 결함 3/3 검출. exact source/test/log blob 일치. 기존 402 host, 102 Domain, 124 Intelligence와 별도 집계한다. 정식 Gradle/JDK17 및 실제 통합 NOT RUN. 후보 common CI doc 46151376704, Windows 46151376694, Bootstrap 46151376713 SUCCESS. 기준 main 3a494a2 CI 3건 SUCCESS. Common CI는 신규 Kotlin harness 실행 증거가 아니다. 이 후보의 제품 승격 또는 main 병합은 수행하지 않았다.
## R02 — WO-23 유한 복구 제어기
후보 candidate/gpt-07-r02, commit 24edfc5e82aae648d5918b749dd881cf11ed269c. [보고서](https://github.com/scarlel96-design/AURA-Ultra/blob/24edfc5e82aae648d5918b749dd881cf11ed269c/docs/evidence/GPT-07/R02/REPORT.md), [실행 로그](https://github.com/scarlel96-design/AURA-Ultra/blob/24edfc5e82aae648d5918b749dd881cf11ed269c/docs/evidence/GPT-07/R02/recovery.log).
R01을 변경 없이 재사용한다. RecoveryEpisode는 한 회차에서 동시에 한 요청만 계획한다. 지연 전 재시도와 오래된 완료 신호를 거부한다. 준비 상태가 해제되면 새 시작을 멈춘다. 횟수와 대기 시간은 보존한다. 완료, 취소, 기한 초과, 시계 후퇴, 재시도 중단은 종료 상태다. 실제 요청 취소 및 접근 권한 확인은 호출자 책임이다. 실제 권한/페이로드 경계와 별개이며 동시 호출은 아직 지원하지 않는다.
로컬 Kotlin 1.9.0/JDK21, JVM17 target: R01 21 + R02 22 = 43 PASS. seed20261128 산술 50,000/복구 회차 10,000, R02 결함 주입 3/3 검출. 원격 blob 일치. 초기 실행의 stdlib 경로 오류는 수정 후 전체 재실행 성공. 정식 Gradle/JDK17, SDK 및 소비자 통합 NOT RUN. 후보 문서 46152146761, Windows 46152146803, Bootstrap 46152146801 SUCCESS. 직전 main 0520cf5 CI 3건 SUCCESS. 기존 PR 및 main 제품 코드 변경 없음.
## R03 — WO-18/19 기상 수치 정규화
후보 candidate/gpt-07-r03, commit 7f2a197b624f48574a867d19b0789fa619f5863f. [보고서](https://github.com/scarlel96-design/AURA-Ultra/blob/7f2a197b624f48574a867d19b0789fa619f5863f/docs/evidence/GPT-07/R03/REPORT.md), [시험 로그](https://github.com/scarlel96-design/AURA-Ultra/blob/7f2a197b624f48574a867d19b0789fa619f5863f/docs/evidence/GPT-07/R03/quantity.log), [실행 계획](https://github.com/scarlel96-design/AURA-Ultra/blob/7f2a197b624f48574a867d19b0789fa619f5863f/docs/evidence/GPT-07/R03/PLAN.md).
Domain 검증을 대체하지 않는다. 7개 metric 및 10개 unit을 사용한다. 온도/체감은 Celsius, 습도/강수확률은 percent, 관측/예상 강수량은 mm, 풍속은 m/s로 환산한다. 명시적 단위·필드 일치, null/0 구분, 비유한 값·범위·overflow/완전 underflow 거부. 강수율과 강수량을 혼합하지 않는다. 공급원 문자열 매핑·실제 시간/범위·관측/예측 provenance·권한 검증은 별도다. 후보 공통 단위는 생산 계약 승인 전 확정하지 않는다.
로컬 Kotlin 1.9.0/JDK21, JVM17 target: 21+22+20=63 PASS. 20,000 입력 반복×3=60,000 환산 비교, 7×10 단위 매트릭스, 결함 주입 3/3 검출. R01/R02 원본 blob 및 재실행 출력 동일. 신규 source/test/log/plan blob 일치. 정식 Gradle/JDK17 및 실제 provider/SDK 통합 NOT RUN. 후보 공통 CI 확인 시점: AURA Bootstrap 46152779560 in_progress; Active documentation budget 46152779564 in_progress; Windows host reproducibility 46152779697 in_progress. 기존 PR 및 제품 코드 변경 없음.
## 남은 개발 순서
1. 후보 R03 공통 CI 및 정확한 blob 상태를 확인한다. R01~R03 실행 증거를 보존한다.
2. WO-17~23에서 기존 Domain/Intelligence와 중복되지 않는 독립 데이터 정규화·오류·복구 경계를 선택한다. 실제 소스와 요구사항을 대조한 후 시험 가능한 최소 구현부터 진행한다. 실제 권한/캐시 상태의 연결은 차단점 해결 이후다.
3. 필요한 경우 GPT-08/09와 연결할 인터페이스의 합성 시험을 준비한다. 생산 정책·수치·SDK를 미확정 상태에서 확정하지 않는다. 실제 네트워크 및 데이터 수집 금지.
4. 관련 필수 결함과 F03/F04/RV02를 해결한 후 승인된 통합 및 정식 JDK17/Gradle/실기기 검증을 진행한다. 기존 의존성 검증/라이선스/SBOM, 보호 철회·시간·순서·실제 소비자 계약을 유지한다.
완료 기준: 독립 산출물별 정확한 코드/시험/증거와 관련 게이트 검증. 합성 시험 PASS를 제품 GO로 계산하지 않는다. GPT-09 종료 변경 영향 중심 검증, GPT-12 종료 최종 전면 감사 유지. 다음 요청에서 main/candidate/기존 PR HEAD 및 CI 확인 → AGENTS PRE-FLIGHT → 위 2번 실행. 무관 변경·반복 감사 금지. 사용자 승인을 받기 전 실제 기기 변경/제품 통합 금지.
