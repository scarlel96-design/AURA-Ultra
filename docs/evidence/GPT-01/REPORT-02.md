# GPT-01 / 회차 02 — 과거 실패 재현과 메모리 검증
상태: IN_PROGRESS / 제품 NO-GO. 2026-11-27. 기준 HEAD 86f9df3f174f2356959ab04ec4ab6fae0379521e, main. GPT.
PRE-FLIGHT: AGENTS, STATUS, README, MASTER_ARCHITECTURE, ROADMAP, REQUIREMENTS, QUALITY_GATES, PERFORMANCE, RESUME_PROTOCOL, PROJECT_INVARIANTS, TASK_RECORD_PROTOCOL, VERIFICATION_PROTOCOL, TASK_REPORT_TEMPLATE, GPT_EXECUTION_PLAN, BLOCKERS, WORK_LOG, GPT-01, WO-01, REPORT-01, BUILD_GUIDE, 실제 workflow/Gradle/check_apk/profiles 확인. 이전 CI 45999371709 성공 재확인. B-001 과거 원인 미확인, B-010 RESOLVED.
범위: R-20/R-22/R-25. 현행 제품 코드/그래픽/패키징 설정 변경 제외. 이전 SHA 95e51cc 격리 checkout; APK 게시 금지. Work 전환 거절; CI 활용.
근거: https://github.com/google/watchface/releases/tag/release (memory-footprint.jar SHA-256 503c5f7bc9209ec4d4d4974f973cf66ad6fbb435e8422c310aac5b820f1f991a, Apache-2.0); https://github.com/google/watchface/blob/main/play-validations/README.md ; ResourceMemoryEvaluator.java, EvaluationSettings.kt, MemoryFootprint.kt 원문 확인. report mode는 제한 적용하지 않으므로 별도 exact bytes 검사. 1 MiB=1048576 bytes. 기존 예산 보존. offload 제한 적용, 추정 최적화 미사용.
| 요구 | 구현 | 시험 |
|---|---|---|
| R-20 | tools/verify_memory.py | 실제 3 APK JSON 평가, 70/7 MiB |
| R-22 | tests/unit/test_memory.py | 경계, 누락, 오류, 초과, 잘못된 데이터 |
| R-25/B-001 | reproduce-packaging.yml | 과거 SHA APK ZIP 항목, dex packages |
| R-22/R-25 | bootstrap.yml | 기존 회귀 및 debug apksigner |
검증: python -m unittest discover -s tests/unit -p 'test_*.py' -v; python tools/verify_memory.py; 기존 전체 CI. 역사적 재현의 실패 검출은 예상 결과로 별도 기록. 서명 검사 debug 한정. Release/실기기/AOD 픽셀/전력 NOT RUN.
G0 문서·이전 CI 확인. G1 후보 작성. G2~G6 새 시험 및 별도 자기 재검토 대기. G7 문서 기록 및 반영 확인 필요. 롤백: 해당 변경만 revert. 다음: 두 CI 로그와 SHA 확인, 메모리 바이트 및 서명 검증, 과거 APK 항목 및 클래스 확인. 기존 게이트 완화 금지.
