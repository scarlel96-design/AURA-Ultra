# 프로젝트 상태 — 단일 재개 체크포인트
2026-11-28 KST. [AGENTS.md](../AGENTS.md) PRE-FLIGHT를 적용한다. 최신 HEAD와 실제 CI를 확인한다. [archive](archive/README.md).

| 항목 | 현재 값 |
|---|---|
| 정본 | main |
| 최종 검증 코드 | 53d43d918c3e3c1002b70473f5de843c0f946d8e |
| main 회귀 | [46083911786](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46083911786) SUCCESS 316 PASS/0 FAIL/0 SKIP; [46083911794](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46083911794) SUCCESS 7 PASS/12개 문서 |
| GPT-06 | 독립 준비 종료·중단 / PARTIAL (실기기 및 동적 효과 미검증) |
| GPT-04/05 | PARTIAL |
| GPT-07 | NOT STARTED / 사용자 별도 승인 대기 |
| 정식 WO GO | 0/38 |
| GPT 묶음 GO | 3/12 (PARTIAL 독립 준비 종료는 GO에 포함하지 않음) |
| 출시 | NO-GO |
| 다음 행동 | 사용자 결정 대기. 별도 승인 후에만 실기기 확인 또는 다음 GPT 작업. |

## 근거 및 이관
- [GPT-06 전체 종료 보고](evidence/GPT-06/REPORT-FINAL-CLOSURE.md). R01~R06 및 OPS-07 독립 준비 산출물 통합·자동 검증 완료. 결합 후보와 main 코드·시험·자산·CI 102개, 보호 경로 38개 blob 동일. 원본 아카이브 8개 SHA 동일. 활성 8개 문서 500021→24609 B(검증 코드 기준).
- [최종 개발용 APK](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46083911786/artifacts/15238910535): 114716 B, 직접 다운로드·SHA256·CRC·XML·PNG·RGBA 검증 PASS. WFF2~5 각 공식 평가기 2412312 B active/3181712 B AOD. 정적 Balanced 후보. 실제 RAM/전력 아님.
- [R05](evidence/GPT-06/REPORT-05-INTEGRATED.md): 152 SVG, 36 PNG, 최소 호스트 대비 5.729308:1, PNG 1266831→139710 B. [R06](evidence/GPT-06/REPORT-FINAL-INTEGRATION.md).
- [실기기 및 승격 게이트](operations/SIGNATURE_DEVICE_GATE.md): 실제 설치·렌더링·센서·동적 효과·발광 픽셀·전력 NOT RUN. Bootstrap 제품 리소스 유지. 실제 후보 프리뷰·육안 승인·사용자 승인 필요. 브랜치 보호 설정 미확인.
- AG-01 PR #2 HOLD, HEAD fc98c3ad5993e131f733a9444b5849e737a49086. GB-02 PR #3 HOLD, HEAD 63e85277c1edb0b9f7b2227f23babae65f10b5aa. [배정](operations/agent-orders/README.md). B-002/003/004/005/006/007/008 유지; [차단점](operations/BLOCKERS.md).
- [GPT-06](operations/GPT-06.md), [계획](operations/GPT_EXECUTION_PLAN.md), [이력](operations/WORK_LOG.md). 종료 기록 커밋은 문서만 변경한다. 검증 코드 SHA와 종료 기록 SHA를 구분한다. 새 문서 커밋 CI는 별도 상태를 확인한다.

## 중단
사용자 요청에 따라 GPT-06 전체 독립 준비 종료 후 중단한다. GPT-07 착수 금지. PARTIAL 및 제품 NO-GO 유지.
