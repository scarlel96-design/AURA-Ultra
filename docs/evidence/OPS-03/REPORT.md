# OPS-03 — 매 작업 턴 PRE-FLIGHT
일자: 2026-11-27. 기준 SHA: 951593e4fbbac33f2c675ea5cbbf07edbe22353d.
목표: 대화 기억 대신 최신 저장소의 문서를 첫 확인 대상으로 고정한다.
범위: 운영 문서와 진입 경로. 제품 코드/CI 구성 변경 제외.
PRE-FLIGHT: 기준 HEAD 조회, AGENTS/README/STATUS/RESUME/TASK_RECORD/VERIFICATION/WORK_LOG/BLOCKERS/GPT-01 및 기존 보고서 양식 확인. 활성 GPT-01, B-001/B-010. 이전 v1.1의 세션 복원 규정에 따라 문서와 관련 CI 점검. 신규 v1.2의 적용은 이 변경 이후부터.
문서 기준 SHA 951593e4fbbac33f2c675ea5cbbf07edbe22353d, CI 45998609726 (completed/failure): Official WFF validation: success; Build debug APKs: success; Check APK contents: failure; Upload debug APKs: skipped. https://github.com/scarlel96-design/AURA-Ultra/actions/runs/45998609726. 운영 문서 변경 실행이며 제품 코드 변경 없음. B-001/B-010 해결 증거 없음.

## 요구사항 추적
| 요구 | 구현 | 검증 |
|---|---|---|
| 매 턴 첫 문서 확인 | AGENTS.md 최상단 PRE-FLIGHT | 위치, 순서, 필수 링크 검사 |
| 쉽게 발견 가능한 진입점 | README, STATUS 상단 | 링크 대상 및 앵커 검사 |
| 동일 대화 재개 포함 | RESUME_PROTOCOL | 매 턴 예외 없음 확인 |
| 실제 확인 기록 | TASK_RECORD_PROTOCOL, TASK_REPORT_TEMPLATE | 필수 필드 확인 |
| 검증 누락 시 착수 차단 | VERIFICATION_PROTOCOL G0 | BLOCKED 및 읽기 전용 진단 규칙 |
| 상태 보존 | STATUS, WORK_LOG, BLOCKERS | 활성 작업 및 결함 ID 유지 |

G0: 이전 문서와 최신 확인 가능한 CI 확인.
G1: 요구사항과 변경 문서 대조.
G2/G3/G4: 제품 코드·검증기 변경 없음. 제품 시험 신규 실행 여부는 CI 증거 기준. 문서 링크/구조 검사 적용.
G5: 같은 GPT의 별도 문서 검토; 독립 에이전트 미실시.
G6: 기존 제품 실패 유지, 코드 SHA와 문서 SHA 구분.
G7: STATUS/WORK_LOG/BLOCKERS/evidence 갱신. 커밋 후 원격 반영·링크 검사로 확인.
제약: 문서 규정은 향후 에이전트 행동을 지시하며, 모든 채팅 환경에서 자동 강제 실행된다는 보장은 아니다. 실제 별도 세션 복구 시험은 미실시.
다음: GPT-01 / B-001 APK 검사 실패 원인 확인 및 B-010 검사기 보완. 출시 NO-GO.
