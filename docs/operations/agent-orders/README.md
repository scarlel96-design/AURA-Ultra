# 외부 개발 에이전트 — 1차 작업 배정
등록: 2026-11-27. 기준 main c1c66b76b7af4a20bb7a08a369fb5962d28b973f. 1차 결과 접수. 담당자 판정과 총괄 검증/통합 판정을 구분한다.
| 담당 | ID | 상태 | 브랜치 | 소유 경로 |
|---|---|---|---|---|
| ChatGPT | GPT-04 | PARTIAL (AM/PM 후보 검증 완료, 통합 CI 확인) | 정본 규정에 따름 | 그래픽 토큰, 생성 도구, 자산, 공통 빌드 및 중앙 운영 문서 |
| Grok Build | [GB-01](GB-01.md) | GO (독립 모듈 통합 승인) | agent/grok/GB-01 | modules/domain/**, docs/evidence/GB-01/** |
| Antigravity CLI | [AG-01](AG-01.md) | PARTIAL / R03 증거 확인, runtime 검증 보완 | agent/antigravity/AG-01 | tests/compatibility/ag-01/**, docs/evidence/AG-01/** |
| Codex | 미배정 | NOT STARTED | 추후 지정 | 고난도 통합 및 실기기 |
모든 에이전트는 AGENTS.md의 PRE-FLIGHT와 G0~G7을 적용한다. 이 배정표는 분리된 외부 작업의 파일 소유권을 정한다. 중앙 STATUS/WORK_LOG/BLOCKERS 및 정본 명세는 ChatGPT가 검토 후 갱신한다. 외부 에이전트는 자기 evidence에 중앙 문서 갱신 제안을 기록한다. 동일 파일 수정 금지. 독립 브랜치에서만 변경하고 별도 커밋/PR로 제출한다. 자동 병합 및 강제 푸시 금지. 사용자가 각 CLI에 작업을 지시한 뒤 실행한다. 착수/검증 결과는 실제 증거로 갱신한다. 별도 에이전트 사용은 Codex 절감을 위한 실험이며 절감 수치는 미측정.

후속 지시: [GB-01 회차 02](GB-01-R02.md), [AG-01 회차 02](AG-01-R02.md). 새 기능 확장 전 증거 확보 및 결함 검토를 수행한다.

2026-11-28: [AG-01 회차 03](AG-01-R03.md) 즉시 착수 가능. [GB-02](GB-02.md)는 GB-01 통합 승인 이후 별도 브랜치에서 착수한다. 통합 후보 integration/gpt03-gb01, 기존 두 PR 직접 변경 금지. 총괄 OPS-05 증거 참조.

OPS-05: GB01 81 Kotlin 독립 CI PASS. 공통 도구 갱신 후보 0cec622 검증 대기(B-011). GB-02 통합 승인 조건 충족.

최신: GB-01 통합 승인. GB-02 READY, modules/intelligence/** 및 docs/evidence/GB-02/**만 변경. AG-01-R03 별도 작업 계속. 중앙 담당자는 GPT-03 공통 생성·빌드 검증만 변경한다.

GPT-03 종료. GPT-04는 design-system/layouts, 공통 그래픽/검증 도구, 중앙 문서만 변경. GB-02 및 AG-01 영역 제외.

OPS-06: GB-01 통합 완료(중복 보고), GB-02 READY. AG-01-R03 60 schema 로그 확인; [AG-01-R04](AG-01-R04.md) 대상/화면 상태 오판 수정 및 현재 main pin 재검증. 신규 SDK 다운로드/AVD 생성은 사용자 명시 승인 전 금지. GPT-04 후보 독립 CI 중.


## GPT-04 회차 06 — R05 최종 검증 및 통합 (2026-11-28 KST)
기준 main 50937487e790323daf947d5a6b10b912302d635c; 검증 후보 2fe3551d3279630a86571df3b6f6eee499027ee5. [main CI 46064940883](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46064940883) job 140727869837 SUCCESS (120 host); [candidate CI 46065067806](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46065067806) job 140728287603 SUCCESS (129 host, 0 FAIL). 양쪽 12 APK clean build, WFF2~5 정상/오류 fixture, APK contents/memory/signature, 40 SVG + manifest 독립 재생성 41/41 hash 일치. Candidate manifest 4a7a643654cd4e46374a3c0ce80e18547abb6c954bc7c4f03a62fbc7c170cdcd; XML 4bbe6db1a6a215538ea8e0d37509c35132845ad845a0fb42efb78c19f8f11313; Signature 4 profiles active 2371712 B / ambient 3181712 B. Asset estimator only. Evidence artifact 15229529952, digest sha256:6c2cf13d76b122b62a887d2d35fc4ba588eae2c38a8958303609c5edef4044b3; bootstrap artifact 15230945190, digest sha256:9c26e96b97f6f391ea6d23095e428619230ea8adb0a31794d4f9d627833a6111. Both unexpired; download/re-hash NOT RUN. Reviewed actual candidate diff and main divergence (only central documents), preserve R05 report checkpoint on main. Integrate nine validated generator/layout/test/document paths; product apps/watchface and GB/AG owner paths unchanged. New integrated SHA CI pending. GPT-04 PARTIAL, GPT 3/12, WO GO 0/38, release NO-GO. Runtime locale/setting/actual glyph/lit pixels/power NOT RUN. Next: confirm integrated CI, prepare host-only screenshot validation with strict dimension/black background/ambient lit-pixel metrics and negative fixtures, then isolated development package. Do not change AG runtime tools or production face; do not install on user watch.
