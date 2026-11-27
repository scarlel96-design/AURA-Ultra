# GPT-02 / 회차 01 — 공식 호환성 및 프로필 계약
상태: IN_PROGRESS / 출시 NO-GO. 기준 HEAD d75c1a51dab60add9b80469d1081f11cf21587e0. 작업자 GPT.
PRE-FLIGHT: AGENTS, STATUS, README, MASTER_ARCHITECTURE, REQUIREMENTS, QUALITY_GATES, ROADMAP, WO-01, COMPATIBILITY, REFERENCES, BUILD_GUIDE, RESUME_PROTOCOL, PROJECT_INVARIANTS, TASK_RECORD_PROTOCOL, VERIFICATION_PROTOCOL, TASK_REPORT_TEMPLATE, GPT_EXECUTION_PLAN, BLOCKERS, WORK_LOG, GPT-02, GPT-01 REPORT-02 및 실제 profiles/Gradle/workflow/검사 도구 확인. CI 46000111754 success 재확인. G0 PASS.
관련 R-01/02/20/22/23/25. 기존 WFF2/3/4, 26 시험 및 메모리 예산 유지. WFF5 스키마만 추가 확인, SDK 전환은 별도 회차. 실기기, 출시, 신규 그래픽 기능 제외.
근거: ../WO-01/SOURCES.md. 공식 제품 및 개발자 문서 확인. WFF5 공식 발표 및 API37 연결, 기존 WFF 버전 표 4까지라는 한계 기록.
| 요구 | 변경 | 검증 |
|---|---|---|
| R-01/R-23 | COMPATIBILITY/DEVICE_MATRIX | 공식 출처 대조, 실제 기기 NOT RUN |
| R-02/R-22 | profile_contract/build_profiles | 단위 fixture, enabled profile build |
| R-02/R-25 | check_foundation/verify_wff/check_apk | source precedence, raw APK equality, 2~5 schema + invalid fixture |
| R-20/R-22 | verify_memory/CI | 기존 모든 프로필 검사와 서명 |
| R-25 | ADR-007 | 개발용 ID 유지, 배포 제안 |
검증 명령: python -m unittest discover -s tests/unit -p 'test_*.py' -v; python tools/check_foundation.py; python tools/verify_wff.py; python tools/build_profiles.py assemble; python tools/check_apk.py; python tools/verify_memory.py; python tools/build_profiles.py signatures. 예상 37 단위 시험 및 3 APK, 4 schema probes. 새 CI PENDING. G1 후보 구현, G2~G6 결과 대기, G7 기록/반영 확인 예정. 롤백 변경 커밋 revert. 다음: CI 결과 검증 및 필요 수정, 이후 SDK37/AGP9 전환 격리 시험. GPT-02 PARTIAL, WO-01 PARTIAL, 제품 NO-GO.
