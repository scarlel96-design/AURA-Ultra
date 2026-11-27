# 외부 개발 에이전트 — 1차 작업 배정
등록: 2026-11-27. 기준 main c1c66b76b7af4a20bb7a08a369fb5962d28b973f. 1차 결과 접수. 담당자 판정과 총괄 검증/통합 판정을 구분한다.
| 담당 | ID | 상태 | 브랜치 | 소유 경로 |
|---|---|---|---|---|
| ChatGPT | GPT-03 | PARTIAL (공통 기반 통합, flavor 시험) | 정본 규정에 따름 | 그래픽 토큰, 생성 도구, 자산, 공통 빌드 및 중앙 운영 문서 |
| Grok Build | [GB-01](GB-01.md) | GO (독립 모듈 통합 승인) | agent/grok/GB-01 | modules/domain/**, docs/evidence/GB-01/** |
| Antigravity CLI | [AG-01](AG-01.md) | PARTIAL / 원격 증거 확인, 검사기 보완 | agent/antigravity/AG-01 | tests/compatibility/ag-01/**, docs/evidence/AG-01/** |
| Codex | 미배정 | NOT STARTED | 추후 지정 | 고난도 통합 및 실기기 |
모든 에이전트는 AGENTS.md의 PRE-FLIGHT와 G0~G7을 적용한다. 이 배정표는 분리된 외부 작업의 파일 소유권을 정한다. 중앙 STATUS/WORK_LOG/BLOCKERS 및 정본 명세는 ChatGPT가 검토 후 갱신한다. 외부 에이전트는 자기 evidence에 중앙 문서 갱신 제안을 기록한다. 동일 파일 수정 금지. 독립 브랜치에서만 변경하고 별도 커밋/PR로 제출한다. 자동 병합 및 강제 푸시 금지. 사용자가 각 CLI에 작업을 지시한 뒤 실행한다. 착수/검증 결과는 실제 증거로 갱신한다. 별도 에이전트 사용은 Codex 절감을 위한 실험이며 절감 수치는 미측정.

후속 지시: [GB-01 회차 02](GB-01-R02.md), [AG-01 회차 02](AG-01-R02.md). 새 기능 확장 전 증거 확보 및 결함 검토를 수행한다.

2026-11-28: [AG-01 회차 03](AG-01-R03.md) 즉시 착수 가능. [GB-02](GB-02.md)는 GB-01 통합 승인 이후 별도 브랜치에서 착수한다. 통합 후보 integration/gpt03-gb01, 기존 두 PR 직접 변경 금지. 총괄 OPS-05 증거 참조.

OPS-05: GB01 81 Kotlin 독립 CI PASS. 공통 도구 갱신 후보 0cec622 검증 대기(B-011). GB-02 통합 승인 조건 충족.

최신: GB-01 통합 승인. GB-02 READY, modules/intelligence/** 및 docs/evidence/GB-02/**만 변경. AG-01-R03 별도 작업 계속. 중앙 담당자는 GPT-03 공통 생성·빌드 검증만 변경한다.
