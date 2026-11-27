# 프로젝트 상태 — 단일 재개 체크포인트

2026-11-28 KST. 매 턴 [AGENTS.md](../AGENTS.md)의 PRE-FLIGHT를 적용한다. 최신 HEAD와 아래 증거를 직접 확인한다. 과거 기록은 [archive](archive/README.md)에 있다.

| 항목 | 현재 값 |
|---|---|
| 정본 | main |
| 검증된 코드 | a08ebb21e9cf14f62ef95b7da6897a14b8d46c9f (293 host PASS); R05 후보 f3212ae5ec7e5b62a12124fecdb46fae34af7d30 (301 host PASS) |
| 최신 통합 | c4791149928ce1d90fadc31dcb7af73403e6d02f; CI 46082669709 진행 중, 최종 확인 필요 |
| 활성 GPT | GPT-04/05 PARTIAL; GPT-06 PARTIAL, R05 반영, R06 수직 통합 준비 |
| 활성 WO | WO-01 PARTIAL; WO-02~04 독립 준비; 정식 GO 0/38 |
| GPT 묶음 GO | 3/12 |
| 출시 | NO-GO |
| 다음 행동 | R05 통합 CI 확인; GPT-06 R06 격리 WFF 소재 APK 생성·검증; 종료 보고 후 GPT-07 전 중단 |

## 근거와 진입 조건
- R03/R04 통합 [46081405307](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46081405307): 293 PASS/0 FAIL/0 SKIP. R05 [46081519011](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46081519011): 301 PASS/0 FAIL/0 SKIP, 152 SVG, 36 PNG, 최소 패널 대비 5.729308:1, 중복 패널 RGBA 최대 81200 B, PNG 1266831→139710 B. 실제 WFF 렌더링·글리프·전력 NOT RUN. [R05 보고서](evidence/GPT-06/REPORT-05-VISUAL.md), [최신 검증 보고](evidence/GPT-06/REPORT-05-VERIFIED.md).
- [통합 CI 46082669709](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46082669709). 네 APK 기본 표시 검증과 소재 후보 검증은 구분한다. 제품 XML은 Bootstrap 유지.
- [GPT-06 실행 명세](operations/GPT-06.md), [계획](operations/GPT_EXECUTION_PLAN.md), [차단점](operations/BLOCKERS.md), [작업 기록](operations/WORK_LOG.md).
- AG-01 PR #2 HOLD; 사용자 보고 R07 수정 후 시험 미완료/쿼터 제한. HEAD fc98c3ad5993e131f733a9444b5849e737a49086. GB-02 PR #3 HOLD; R04 보고 52 intelligence/81 domain, 공통 CI만 확인; HEAD 63e85277c1edb0b9f7b2227f23babae65f10b5aa. R05 지시 사용자에게 전달. [배정](operations/agent-orders/README.md).
- B-002/003/004/005/006/007/008 유지. B-011 현재 pin 해결. 실기기, 승인된 시각, 센서, 전력·배포 정책 미확정. 실제 제품 완성도 미확정. [핵심 목표](operations/PROJECT_INVARIANTS.md) 및 WO 선행 조건 유지.

## 운영 원칙
현재 상태만 갱신한다. 상세 결과는 회차별 evidence에 1회 기록한다. 과거 상태를 반복 붙여넣지 않는다. GPT-06 독립 준비 종료 또는 소진 시 사용자에게 결과를 보고하고 중단한다. GPT-07은 별도 사용자 승인 전 시작하지 않는다.
