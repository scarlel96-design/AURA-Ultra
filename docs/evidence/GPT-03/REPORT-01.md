# GPT-03 / 회차 01 — Bootstrap 생성 기반
상태: IN_PROGRESS / 출시 NO-GO. 2026-11-27. 기준 main fe4e19d7c6e97c043e4f31cb5960bdb430fd507b, branch gpt-03-generator. 작업자 GPT.
PRE-FLIGHT: AGENTS, STATUS, GPT-03, agent-orders/README, RESUME_PROTOCOL, PROJECT_INVARIANTS, TASK_RECORD_PROTOCOL, VERIFICATION_PROTOCOL, TASK_REPORT_TEMPLATE, GPT_EXECUTION_PLAN, BLOCKERS, WORK_LOG, ROADMAP, WO-02, README, MASTER_ARCHITECTURE, REQUIREMENTS, QUALITY_GATES, DESIGN_SYSTEM, MOTION_SPEC, PERFORMANCE, 실제 tokens/XML/preview blob/check_foundation/profiles/workflow 확인. CI 46002470824 SUCCESS, main 코드 변경은 문서만 확인. GB-01/AG-01 원격 브랜치 미등록, 로컬 실행 여부 unknown. G0 PASS. 선행 WO-01 PARTIAL, WO-09/10 GO 아님.
범위 R-02/05/10/20/22/25. 기존 XML byte equality, preview blob 보존. 원본/생성 분리, strict token schema, 원형 bounds, SHA256 manifest, palette SVG(비패키징), stale/negative checks. 외부 에이전트 소유 경로 제외. 제품 기능/그래픽 변경 없음. 신규 라이브러리 없음. 기존 공식 validator/evaluator pin 유지.
| 요구 | 파일 | 시험 |
|---|---|---|
| R-05/10 | bootstrap tokens/template | 원본 XML 재현, 좌표/색상/글꼴 범위 |
| R-22 | generate_bootstrap.py, source preview, palette | 반복 출력 및 manifest 일치, stale/누락/경로 실패 |
| R-02/20/25 | bootstrap CI | 기존 40개 + 신규 22개 단위, 4 schema/build/raw APK/memory/signature |
검증 예정: python tools/generate_bootstrap.py --check; python -m unittest discover -s tests/unit -p 'test_*.py' -v; 기존 전체 CI. 기대 62 PASS/0 FAIL, 4 APK. 검증 브랜치에서 실패 원인 수정 후 재실행. 기존 XML과 preview blob 보존 여부 원격 diff 확인. 실제 flavor override 빌드/독립 과정 재현은 후속 회차. G1 후보, G2~G6 PENDING, G7 기록 및 반영 확인 예정. 롤백: 후보만 revert, 기존 main 보존.
