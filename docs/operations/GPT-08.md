# GPT-08 — 기상/강수 공급원
IN_PROGRESS / PARTIAL. WO-18/19/23, R-04/14/15/17/18/21/22. 제품 NO-GO. 기존 GPT-07 [마감](GPT-07.md)과 R07 통합 인계를 재사용한다. 기본 KMA, 대체 Open-Meteo. 기존 설계 계약 범위 내 격리 코드/합성 시험만 허용한다. F03/F04/RV02/AG 및 B-002~008 관련 통합 차단 유지. 기존 PR #2/#3/#5/#6/#7 HOLD. 실제 API 키/계정/위치/기기/보호 데이터/생산 의존성/병합 별도 승인.
## R01 — 공급원 입력 경계
기준 main 07378e20af9249a546d49ab7e7ff6b1be95b7695; GPT-07 최종 후보 942b92be09dae7bc6334ae7fa17b79cb74b8ab3e; 새 후보 candidate/gpt-08-r01 @ 96f936d8dfb96c0b914fef0d1bb52ec487c63525.
[보고서](https://github.com/scarlel96-design/AURA-Ultra/blob/96f936d8dfb96c0b914fef0d1bb52ec487c63525/docs/evidence/GPT-08/R01/REPORT.md) · [시험 로그](https://github.com/scarlel96-design/AURA-Ultra/blob/96f936d8dfb96c0b914fef0d1bb52ec487c63525/docs/evidence/GPT-08/R01/forecast.log) · [계획](https://github.com/scarlel96-design/AURA-Ultra/blob/96f936d8dfb96c0b914fef0d1bb52ec487c63525/docs/evidence/GPT-08/R01/PLAN.md).
기상청: 명시 KST 계약에 한해 발표/예보 시각 엄격 파싱, 기대 격자·발표 일치, 수신 전 발표 및 예보 순서 확인. 정확한 단기예보 활용 가이드 ZIP 코드표 미확인, API별 시간대 및 특수값/범주형 PCP/SNO/WSD 확인 필요. 값 변환/페이지 조립 미구현. Open-Meteo: decoded hourly 열, 기대 필드·배열 길이·시간/단위·값 검증, UTC epoch 초·직전 1시간 구간, 비/소나기 성분 모두 있을 때만 합산. 하나라도 null이면 합산도 null. 전체 강수/눈은 비로 해석하지 않는다. R03 WeatherQuantity/R04 RainTimeline 재사용. 실제 JSON, 위치/요청 binding, issue/TTL/권한/캐시/전송 미구현. 공급원 이용 조건: KMA 인증키/출처표시, Open-Meteo 무료 비상업 조건과 CC BY 4.0, 배포 승인·할당량·상업 이용 결정 별도. 공식 자료 링크와 확인 범위는 보고서에 기록.
검증: Kotlin 1.9.0/JDK21 JVM17 target, 105 기존+15 신규=120 PASS, 3/3 결함 주입 검출. 기존 로그 6개 동일, 원격 prior 26+신규 4 blob 일치. main 07378e2 공통 3 CI SUCCESS, 후보 공통 CI 46158342339/340/312 진행 중(조회 시점). 공통 CI는 독립 Kotlin 시험 아님. 정식 Gradle/JDK17·실제 응답 NOT RUN.
## 다음 작업
1. 최신 main/candidate/기존 PR 및 CI 확인, AGENTS PRE-FLIGHT. 정확한 KMA 단기예보 API 가이드와 범주/시간/페이지/누락 코드 확인. 검증된 범위의 실제 공급원 값 매핑 및 bounded decoded response/fixture를 구현한다. 미확인 값은 승인하지 않는다.
2. Open-Meteo/KMA 구조적 응답 검증 및 source fallback/오류/재시도 연결을 필요한 범위로 묶는다. 기존 GPT-07 후보와 계약을 재사용한다. 실제 JSON/통신 구현은 의존성과 환경 제약에 맞춰 분리한다. 실제 API·키·계정·위치 접근은 승인 전 금지.
3. 독립 산출물 마감, 전체 관련 회귀 및 인계. 범위 밖 반복 감사 금지. 실제 통합은 F03/F04/RV02와 권한/기기 게이트 해결 이후에만 수행한다. GPT-09 변경 영향 검증 및 GPT-12 최종 감사 유지. WO GO 0/38, GPT GO 3/12, 감사 14/16은 별도 지표.
