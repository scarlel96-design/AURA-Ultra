# 프로젝트 상태 — 단일 재개 체크포인트

2026-11-28 KST. 매 턴 [AGENTS.md](../AGENTS.md)의 PRE-FLIGHT를 적용한다. 최신 HEAD와 아래 증거를 직접 확인한다. 과거 기록은 [archive](archive/README.md)에 있다.

| 항목 | 현재 값 |
|---|---|
| 정본 | main |
| 검증된 코드 | a08ebb21e9cf14f62ef95b7da6897a14b8d46c9f (293 host PASS); R05 후보 f3212ae5ec7e5b62a12124fecdb46fae34af7d30 (301 host PASS) |
| 최신 통합 | c4791149928ce1d90fadc31dcb7af73403e6d02f; CI 46082669709 SUCCESS, 301 PASS |
| 활성 GPT | GPT-04/05 PARTIAL; GPT-06 PARTIAL, R05 반영, R06 소재 APK 4/4 검증 완료; 최종 결합 후보 CI 진행 |
| 활성 WO | WO-01 PARTIAL; WO-02~04 독립 준비; 정식 GO 0/38 |
| GPT 묶음 GO | 3/12 |
| 출시 | NO-GO |
| 다음 행동 | 최종 결합 CI 46083441184 검증 → 정확한 파일 통합 → main 회귀 확인 → GPT-06 전체 종료/소진 보고 및 중단 |

## 근거와 진입 조건
- R03/R04 통합 [46081405307](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46081405307): 293 PASS/0 FAIL/0 SKIP. R05 [46081519011](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46081519011): 301 PASS/0 FAIL/0 SKIP, 152 SVG, 36 PNG, 최소 패널 대비 5.729308:1, 중복 패널 RGBA 최대 81200 B, PNG 1266831→139710 B. 실제 WFF 렌더링·글리프·전력 NOT RUN. [R05 보고서](evidence/GPT-06/REPORT-05-VISUAL.md), [최신 검증 보고](evidence/GPT-06/REPORT-05-VERIFIED.md).
- [통합 CI 46082669709](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46082669709). 네 APK 기본 표시 검증과 소재 후보 검증은 구분한다. 제품 XML은 Bootstrap 유지.
- [GPT-06 실행 명세](operations/GPT-06.md), [계획](operations/GPT_EXECUTION_PLAN.md), [차단점](operations/BLOCKERS.md), [작업 기록](operations/WORK_LOG.md).
- AG-01 PR #2 HOLD; 사용자 보고 R07 수정 후 시험 미완료/쿼터 제한. HEAD fc98c3ad5993e131f733a9444b5849e737a49086. GB-02 PR #3 HOLD; R04 보고 52 intelligence/81 domain, 공통 CI만 확인; HEAD 63e85277c1edb0b9f7b2227f23babae65f10b5aa. R05 지시 사용자에게 전달. [배정](operations/agent-orders/README.md).
- B-002/003/004/005/006/007/008 유지. B-011 현재 pin 해결. 실기기, 승인된 시각, 센서, 전력·배포 정책 미확정. 실제 제품 완성도 미확정. [핵심 목표](operations/PROJECT_INVARIANTS.md) 및 WO 선행 조건 유지.

## 운영 원칙
현재 상태만 갱신한다. 상세 결과는 회차별 evidence에 1회 기록한다. 과거 상태를 반복 붙여넣지 않는다. GPT-06 독립 준비 종료 또는 소진 시 사용자에게 결과를 보고하고 중단한다. GPT-07은 별도 사용자 승인 전 시작하지 않는다.

## R06 현재 후보
- branch gpt-06-signature-material-apk, SHA e1a5f62abbf20cbaa6d9c741251b96d7a6caddd1, [CI 46082882539](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46082882539) SUCCESS, [보고서](https://github.com/scarlel96-design/AURA-Ultra/blob/e1a5f62abbf20cbaa6d9c741251b96d7a6caddd1/docs/evidence/GPT-06/REPORT-06-MATERIAL-APK.md). 신규 단위 시험 8개(전체 예상 309); WFF2~5 격리 소재 APK 빌드/공식 스키마/메모리/서명/XML·PNG read-back/개발 증거 업로드. 309 PASS/0 FAIL/0 SKIP, 네 소재 APK 검증 및 업로드 성공. 제품 XML, 실제 기기 미변경.
- 운영 경량화: 원본 8개 문서 blob 일치 보존. 활성 문서 500021 → 19464 B(초기 압축 시점); [archive](archive/README.md). 재개·기록 규정 v1.3. 상세 증거 중복 금지.

- R05 통합 46082669709 SUCCESS, 301 PASS/0 FAIL/0 SKIP, exact SHA c4791149928ce1d90fadc31dcb7af73403e6d02f. Bundle hash and APK/memory match verified. [최종 검증](evidence/GPT-06/REPORT-05-INTEGRATED.md).
- OPS-07 후보 46b22851d401bc5c4db548e1b45a3e9fbbca17b5, branch gpt-06-ops-guard, CI 46083109875 SUCCESS (308 PASS). 최종 결합 후보에서 별도 doc-budget CI도 성공. [보고서](https://github.com/scarlel96-design/AURA-Ultra/blob/46b22851d401bc5c4db548e1b45a3e9fbbca17b5/docs/evidence/OPS-07/REPORT.md). 7개 신규 문서 검사 시험, 활성 12개 파일 byte limit, archive/evidence 제외, PRE-FLIGHT 선택 열람, 실기기 체크 및 승격 기준. 후보 미통합. 제품 NO-GO.

## GPT-06 최종 결합 후보
- SHA 65c45f51bebce19b7df8091e1e55ed2afb4ec312, branch gpt-06-final-integration; [Bootstrap CI](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46083441184) IN_PROGRESS (316 expected host tests); [문서 검사](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46083441202) SUCCESS 7 PASS, 12 files within limits. R06/OPS 정확한 12개 원본 blob 보존, Bootstrap에 실제 doc-budget 검사 추가; 최신 GPT-06 명세 병합. 15 변경 경로, AG/GB 및 제품 파일 변경 없음.
- R06 CI 46082882539 SUCCESS: 309 PASS, WFF2~5 material APK 4/4; active 2412312 B, AOD 3181712 B per APK (official evaluator). [검증 보고](https://github.com/scarlel96-design/AURA-Ultra/blob/65c45f51bebce19b7df8091e1e55ed2afb4ec312/docs/evidence/GPT-06/REPORT-06-VERIFIED.md), [APK artifact](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46082882539/artifacts/15238230693), unexpired at check. 직접 다운로드 후 ZIP/APK/XML/PNG/RGBA 해시·CRC 검사 PASS. 실제 설치/렌더링/전력 NOT RUN.
- 사용자 재확인: GPT-06 전체 독립 준비가 끝나거나 외부 조건으로 소진되면 명시적으로 전체 결과 보고 후 중단. GPT-07 자동 착수 금지. 아직 완료 판정 아님.

- R06 다운로드 검증: [REPORT-06-ARTIFACT-READBACK](evidence/GPT-06/REPORT-06-ARTIFACT-READBACK.md). 114720 B, 4/4 APK, ZIP/PNG CRC 및 RGBA 해시 일치, DEX 없음. 최종 결합 CI 46083441184는 소재 APK 단계 IN_PROGRESS. 보호 경로 38개 blob 동일. 완료 판정 보류.
