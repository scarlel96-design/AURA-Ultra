# 프로젝트 상태 — 단일 재개 체크포인트

> [!IMPORTANT]
> 매 작업 턴 시작 시 [루트 AGENTS.md](../AGENTS.md)의 PRE-FLIGHT를 먼저 수행한다. 이 문서만 읽고 작업을 시작하지 않는다. 최신 HEAD, 필수 규정, 활성 작업 및 실제 CI 증거를 확인한다.
기준일: 2026-11-27. 이 문서는 매 작업 종료 시 업데이트한다.
현재 목표: GPT 선행 개발 최대화(작업량 추정 목표 65%, 조건부 상한 75%). 최종 프리미엄 품질 유지. Codex 중복 작업 최소화.

| 항목 | 현재 값 |
|---|---|
| 정본 브랜치 | main |
| 확인한 코드 SHA | 544a7010f4bed515d667bfa6a9bbda1389f5bc92 |
| 활성 GPT 작업 | GPT-01 / 빌드 안정화 |
| 활성 WO | WO-01 PARTIAL; WO-02·04 준비 작업만 일부 구현 |
| 다음 안전한 행동 | GPT-01 회차 01: 새 코드의 CI 결과 확인. 실패 시 정확한 ZIP 항목/manifest/validator 로그로 재현 및 수정. 성공 시 Artifact 확인 및 메모리 평가 통합 |
| 다음 실행 명세 | operations/GPT-01.md |
| 현재 차단 | operations/BLOCKERS.md B-001/B-010 수정 후보 검증 대기 |
| 공식 WO GO | 0/38 |
| GPT 묶음 완료 | 0/12 |
| 실제 제품 완성도 | 미확정; 초기 빌드 토대 |
| 출시 판정 | NO-GO |

## 확인된 CI
코드 SHA 544a7010f4bed515d667bfa6a9bbda1389f5bc92, [CI 45997124733](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/45997124733), job 140499204563, 최종 conclusion failure.
- Wrapper SHA-256, 프로젝트 구조, SDK 설치·확인, 공식 WFF validator: PASS.
- Gradle WFF2/3/4 assemble: PASS (BUILD SUCCESSFUL).
- APK 내용 검사: FAIL (WFF2 실행 코드로 분류된 항목 존재; 파일명 및 원인 미확인).
- WFF3/4 개별 APK 내용 검사: NOT RUN (스크립트가 WFF2에서 종료).
- Artifact 업로드: SKIP.
- 메모리, 발광 픽셀, 실기기 렌더링·설치·센서·배터리: NOT RUN.
- 위 결과는 코드 SHA 기준이다. 운영 문서 커밋 후 새 CI가 있으면 실행 결과를 다시 확인한다.

## 추가 CI 재확인
[CI 45998056978](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/45998056978), head SHA 28f51fd89b08cac0e183bbc6c5dfab98dd0f81fa, job 140502353294: 공식 validator 버전별 PASSED #2/#3/#4 및 BUILD SUCCESSFUL 확인. APK 내용 검사 동일 FAIL, Artifact SKIP. 해당 실행은 운영 문서 변경 SHA이며 제품 코드 변경 없음. B-001 미해결.
B-010: verify_wff.py의 VALID 문자열 포함 검사에 오판 위험을 발견했다. 실제 이번 로그에는 명시적 PASSED가 존재한다. 위험을 등록했으며 스크립트는 미수정.

## 재개 절차
AGENTS.md → operations/RESUME_PROTOCOL.md → operations/TASK_RECORD_PROTOCOL.md → operations/VERIFICATION_PROTOCOL.md → operations/GPT_EXECUTION_PLAN.md → operations/BLOCKERS.md → operations/GPT-01.md → 실제 소스/CI.
main의 현재 HEAD를 먼저 확인한다. 확인한 코드 SHA와 최신 문서 SHA를 구분한다. 사용자가 "다음 작업"이라고 하면 재개 절차에 따라 실행한다.

## 남은 사항
실제 Watch7 크기/OS, 신형 기기 사양/설치, WFF5 지원, 정식 패키지/라이선스/서명은 미확정.
고급 소재·모션·8개 테마·외부 데이터·Wear Services·Companion은 아직 미완료. WFF4 Reference와 고급 모션은 PoC 필요.
문서 작업이 제품 기능을 완료한 것으로 계산되지 않는다. 다음 작업의 범위와 증거는 WORK_LOG와 해당 evidence에 추가한다.

## 운영 규정 v1.1
매 작업마다 작업별 영속 기록, G0~G7 검증, 증거 감사 및 별도 재검토를 필수 적용한다. 작업 종료 전 실제 저장소 기록을 확인한다. 이번 변경은 문서만 수정하며 제품 판정을 변경하지 않는다.

## 운영 규정 v1.2 — 매 턴 PRE-FLIGHT
루트 AGENTS.md 최상단의 확인 게이트를 매 작업 턴마다 수행한다. 신규 세션뿐 아니라 동일 대화의 연속 작업에도 적용한다. 제품 코드 변경 없음. GPT-01/B-001/B-010 상태 유지.
문서 기준 SHA 951593e4fbbac33f2c675ea5cbbf07edbe22353d, CI 45998609726 (completed/failure): Official WFF validation: success; Build debug APKs: success; Check APK contents: failure; Upload debug APKs: skipped. https://github.com/scarlel96-design/AURA-Ultra/actions/runs/45998609726. 운영 문서 변경 실행이며 제품 코드 변경 없음. B-001/B-010 해결 증거 없음.

## GPT-01 회차 01 — 구현 및 CI 대기
기준 HEAD 95e51cca23210f930dc3716cb790e791585a7bf0. 이전 CI 45998909046: 공식 WFF #2/#3/#4 PASSED, assemble 성공, APK 검사 실패. Debug/release R8 활성화, resource shrinking 비활성화, 검사 강화 및 회귀 시험 작성. 후보 코드 커밋의 CI 결과는 아직 미확인(PENDING). B-001/B-010은 실제 새 증거 확인 전 OPEN 유지. 상세 기록: evidence/GPT-01/REPORT-01.md.
