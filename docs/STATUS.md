# 프로젝트 상태 — 단일 재개 체크포인트

2026-11-28 KST. [AGENTS.md](../AGENTS.md) PRE-FLIGHT를 적용한다. 최신 HEAD와 실제 CI를 확인한다. [archive](archive/README.md).

| 항목 | 현재 값 |
|---|---|
| 정본 | main |
| 검증된 결합 후보 | 65c45f51bebce19b7df8091e1e55ed2afb4ec312; CI 46083441184 SUCCESS, 316 PASS |
| 최신 통합 | R06/OPS-07 정확한 14개 blob 및 현재 문서 반영; 이 문서가 포함된 통합 커밋의 main CI PENDING |
| 활성 GPT | GPT-04/05 PARTIAL; GPT-06 PARTIAL, 마지막 main 회귀 및 전체 종료 감사 대기 |
| 활성 WO | WO-01 PARTIAL; WO-02~04 독립 준비; 정식 GO 0/38 |
| GPT 묶음 GO | 3/12 |
| 출시 | NO-GO |
| 다음 행동 | main 최신 통합 SHA 및 두 CI 확인 → 실제 로그/아티팩트/보호 파일 확인 → GPT-06 전체 종료 또는 소진 보고 및 중단 |

## 근거
- R01~R05 소재 기반, 링, 유리, 광원 및 대비/압축 호스트 검증 완료. [R05](evidence/GPT-06/REPORT-05-INTEGRATED.md): 301 PASS, 152 SVG, 36 PNG, 최소 대비 5.729308:1, 중복 패널 RGBA 81200 B, PNG 1266831→139710 B.
- R06/OPS 결합 [CI](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46083441184): 316 PASS/0 FAIL/0 SKIP; 공식 WFF2~5 스키마, 네 소재 APK, 서명, 메모리 및 패키지 검사 통과. [결합 검증 보고](evidence/GPT-06/REPORT-FINAL-INTEGRATION.md). [개발용 APK](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46083441184/artifacts/15238376046) 114706 B, 직접 다운로드 및 ZIP/APK/XML/PNG/RGBA 해시/CRC 일치, DEX 없음. active 2412312 B, ambient 3181712 B per APK (공식 평가기 추정, 실제 RAM/전력 아님). R06 이전 [증거](evidence/GPT-06/REPORT-06-ARTIFACT-READBACK.md).
- OPS-07 [전용 CI](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46083441202): 7 PASS, 12개 활성 문서 상한 준수. 공통 Bootstrap에도 검사 추가. [기록 규정](operations/TASK_RECORD_PROTOCOL.md) v1.4. GitHub 필수 상태 검사 설정 미확인. 원본 8개 아카이브 동일 blob 보존.
- [실기기/승격 규정](operations/SIGNATURE_DEVICE_GATE.md): 실제 설치·렌더링·센서·발광 픽셀·전력 NOT RUN. 실제 프리뷰·사용자 승인·실기기 확인 전 제품 승격 금지. 제품 XML Bootstrap 유지.
- AG-01 PR #2 HOLD, R07 사용량 제한; HEAD fc98c3ad5993e131f733a9444b5849e737a49086. GB-02 PR #3 HOLD, R04 보고 52 intelligence/81 domain; R05 지시 전달; HEAD 63e85277c1edb0b9f7b2227f23babae65f10b5aa. [배정](operations/agent-orders/README.md). 보호 경로 38개 동일.
- B-002/003/004/005/006/007/008 유지, B-011 현재 pin 해결. [차단점](operations/BLOCKERS.md), [GPT-06](operations/GPT-06.md), [계획](operations/GPT_EXECUTION_PLAN.md), [이력](operations/WORK_LOG.md), [핵심 목표](operations/PROJECT_INVARIANTS.md).

## 중단 조건
GPT-06 전체 독립 준비 종료/소진 시 결과를 명시적으로 보고하고 중단한다. GPT-07은 사용자 별도 승인 전 착수 금지. 전체 제품 GO와 구분한다.
