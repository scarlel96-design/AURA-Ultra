# 외부 개발 에이전트 — 1차 작업 배정
등록: 2026-11-27. 기준 main c1c66b76b7af4a20bb7a08a369fb5962d28b973f. 아직 두 에이전트의 실제 실행 결과는 없다.
| 담당 | ID | 상태 | 브랜치 | 소유 경로 |
|---|---|---|---|---|
| ChatGPT | GPT-03 | READY | 정본 규정에 따름 | 그래픽 토큰, 생성 도구, 자산, 공통 빌드 및 중앙 운영 문서 |
| Grok Build | [GB-01](GB-01.md) | READY | agent/grok/GB-01 | modules/domain/**, docs/evidence/GB-01/** |
| Antigravity CLI | [AG-01](AG-01.md) | READY | agent/antigravity/AG-01 | tests/compatibility/ag-01/**, docs/evidence/AG-01/** |
| Codex | 미배정 | NOT STARTED | 추후 지정 | 고난도 통합 및 실기기 |
모든 에이전트는 AGENTS.md의 PRE-FLIGHT와 G0~G7을 적용한다. 이 배정표는 분리된 외부 작업의 파일 소유권을 정한다. 중앙 STATUS/WORK_LOG/BLOCKERS 및 정본 명세는 ChatGPT가 검토 후 갱신한다. 외부 에이전트는 자기 evidence에 중앙 문서 갱신 제안을 기록한다. 동일 파일 수정 금지. 독립 브랜치에서만 변경하고 별도 커밋/PR로 제출한다. 자동 병합 및 강제 푸시 금지. 사용자가 각 CLI에 작업을 지시한 뒤 실행한다. 착수/검증 결과는 실제 증거로 갱신한다. 별도 에이전트 사용은 Codex 절감을 위한 실험이며 절감 수치는 미측정.
