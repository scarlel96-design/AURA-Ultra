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
## R01~R06 독립 구현 및 시험
기존 상세 원본은 [보관 문서](../archive/2026-11-28-gpt07-r04/GPT-07.md)에 보존한다. 기준 main d718f4e744984be88bcc130c29abaab011d2ca4a, 원본 blob f80e3cba859c29870b5f9e47e04d19b2d85bf347. 각 회차 정확한 코드·시험·명령·제약은 아래 보고서가 정본이다.
| 회차 | 후보 SHA | 기능 | 실제 명명 시험 |
|---|---|---|---:|
| R01 | 02533470f141077d530acbfa04f6b20136b3763e | [재시도 계산](https://github.com/scarlel96-design/AURA-Ultra/blob/02533470f141077d530acbfa04f6b20136b3763e/docs/evidence/GPT-07/R01/REPORT.md) | 21 |
| R02 | 24edfc5e82aae648d5918b749dd881cf11ed269c | [복구 회차](https://github.com/scarlel96-design/AURA-Ultra/blob/24edfc5e82aae648d5918b749dd881cf11ed269c/docs/evidence/GPT-07/R02/REPORT.md) | 22 |
| R03 | 7f2a197b624f48574a867d19b0789fa619f5863f | [기상 수치 정규화](https://github.com/scarlel96-design/AURA-Ultra/blob/7f2a197b624f48574a867d19b0789fa619f5863f/docs/evidence/GPT-07/R03/REPORT.md) | 20 |
| R04 | 200ea2fdaac30b0b2d9c47b70436aa2e0ea6428c | [강수 구간](https://github.com/scarlel96-design/AURA-Ultra/blob/200ea2fdaac30b0b2d9c47b70436aa2e0ea6428c/docs/evidence/GPT-07/R04/REPORT.md) | 20 |
| R05/R06 | 942b92be09dae7bc6334ae7fa17b79cb74b8ab3e | [캐시 대체 판단·공급원 오류](https://github.com/scarlel96-design/AURA-Ultra/blob/942b92be09dae7bc6334ae7fa17b79cb74b8ab3e/docs/evidence/GPT-07/R05-R06/REPORT.md) | 9+13 |
현재 누적 후보 branch candidate/gpt-07-r06, exact HEAD 942b92be09dae7bc6334ae7fa17b79cb74b8ab3e. 기존 R01~04 원본 18개 blob 및 mode 보존, 신규 4 Kotlin 파일·계획·원본 로그 2개 일치 확인. R04와 main d718f4e 공통 CI 각각 3/3 SUCCESS. R06 공통 CI: Windows 46154444055 queued, Bootstrap 46154444117 in_progress, 문서 46154444050 in_progress (조회 시점). Common CI는 독립 Kotlin 시험 실행 증거가 아니다.
R05는 명시적 비보호 범위의 캐시 메타데이터 판정만 구현한다. 현재 검증된 TTL/status 입력을 재사용하며 TTL 계산을 복제하지 않는다. 보호/불명 범위, 권한 거부·보안 실패·영구/불명/잘못된 응답은 대체 후보 거부. stale은 명시적 허용 시만 stale 후보로 유지한다. 실제 캐시 저장·읽기·암호화·삭제 및 보호 데이터 통합 NOT RUN. 호출자 범위 라벨은 권한 증명이 아니다.
R06은 분류된 공급원 오류를 기존 RetryFailure로 매핑한다. 오프라인 대기, 영구 오류 중단, ASCII 정수 초 단위 서버 지연 검증 및 밀리초 오버플로 거부. HTTP 날짜, 헤더 중복·공백 처리 및 실제 HTTP 분류는 어댑터 작업이다. 잘못된 지연값은 재시도 중단. 보안 실패의 원래 분류 보존, 오프라인 현재 요청의 취소/종료 및 재연결 횟수 제어, 유효 오류 분류의 캐시 전달은 실제 통합 책임이다. 실제 요청·권한·SDK 호출 없음.
실제 로컬 Kotlin 1.9.0/JDK21 JVM17 target: 105/105 PASS (R01~04 83+R05 9+R06 13). 기존 네 로그 재실행 바이트 동일. 합성 50,000 산술, 10,000 복구, 60,000 환산, 10,000 강수, 300 캐시 조합; 별도 시험 수가 아니다. R05/06 결함 주입 3/3 검출; 잘못된 클래스명으로 발생한 초기 실행 오류는 검출로 계산하지 않고 정정 후 실제 단언 실패 확인. 정식 Gradle/JDK17·실제 통합 NOT RUN. [계획](https://github.com/scarlel96-design/AURA-Ultra/blob/942b92be09dae7bc6334ae7fa17b79cb74b8ab3e/docs/evidence/GPT-07/R05-R06/PLAN.md) · [공급원 로그](https://github.com/scarlel96-design/AURA-Ultra/blob/942b92be09dae7bc6334ae7fa17b79cb74b8ab3e/docs/evidence/GPT-07/R05-R06/provider.log) · [캐시 로그](https://github.com/scarlel96-design/AURA-Ultra/blob/942b92be09dae7bc6334ae7fa17b79cb74b8ab3e/docs/evidence/GPT-07/R05-R06/fallback.log).
## 다음 작업 — R07 독립 개발 마감
R01~R06 독립 구현은 이번 후보까지로 제한한다. 다음 요청에서 main/candidate/기존 PR 최신 HEAD 및 CI → AGENTS PRE-FLIGHT → 전체 후보의 exact source/test/evidence와 실제 요구사항 대조, 공통 CI 확인, GPT-08/09 재사용 및 필수 통합 인계 정리. 실제 결함이나 누락된 필수 인터페이스 외에는 추가 독립 회차를 열지 않는다. GPT-07 PARTIAL 유지: 정식 빌드, 실제 캐시 저장·권한·소비자·공급원·기기 연동 미검증. F03/F04/RV02/AG 및 B-002~008 게이트 유지. 기존 PR HOLD, 제품 NO-GO. 관련 통합·소유권 인수·병합·실기기 변경 별도 승인. 이후 GPT-08 독립 준비 진입 조건 확인. GPT-09 변경 영향 중심 검증 및 GPT-12 최종 전면 감사 유지. 감사 14/16은 제품 완료율 아님.
