# 외부 개발 에이전트 — 현재 배정
2026-11-28 KST. 상태와 소유권을 분리한다. [이전 이력](../../archive/README.md).

| 담당 | ID | 상태 | 브랜치 | 소유 경로 |
|---|---|---|---|---|
| ChatGPT | GPT-04/05/06 | PARTIAL, R06 APK 검증 완료; 최종 결합 대기 | main 및 격리 후보 | 그래픽, 공통 도구/CI, 중앙 운영 문서 |
| Grok Build | [GB-01](GB-01.md) | 독립 모듈 통합 GO | agent/grok/GB-01 | modules/domain/**, docs/evidence/GB-01/** |
| Grok Build | [GB-02](GB-02.md) | R04 제출, R05 지시, HOLD | agent/grok/GB-02 | modules/intelligence/**, docs/evidence/GB-02/** |
| Antigravity | [AG-01](AG-01.md) | R07 시험 미완료·사용량 제한, HOLD | agent/antigravity/AG-01 | tests/compatibility/ag-01/**, docs/evidence/AG-01/** |
| Codex | 미배정 | NOT STARTED | 추후 지정 | 고난도 통합·실기기 |

매 턴 AGENTS.md PRE-FLIGHT 및 G0~G7. 사용자 지시에 따라 각 CLI에서 실행한다. 동일 파일 수정 금지. 외부 에이전트는 자기 evidence에 중앙 갱신 제안을 기록한다. 총괄만 중앙 문서 갱신. PR #2/#3 자동 병합·강제 푸시 금지. 사용량 제한 중 AG 작업을 다른 에이전트에게 임의 인수하지 않는다. 신규 SDK/AVD 설치는 사용자 승인 전 금지. 독립 모듈의 자체 GO는 총괄 통합 GO가 아니다. 제품 NO-GO.
