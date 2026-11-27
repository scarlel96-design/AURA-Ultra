# GPT-02 / 회차 01 — 공식 호환성 및 프로필 계약
상태: PARTIAL (회차 01 CI 성공) / 출시 NO-GO. 기준 HEAD d75c1a51dab60add9b80469d1081f11cf21587e0. 작업자 GPT.
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

## 회차 01 CI 체크포인트
검증 코드 SHA 7820f90cbb35220fe9c6da4f9702374714d143d1, [CI 46001149417](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46001149417), job 140512806931: in_progress/PENDING.
- Set up job: success
- Verify Gradle wrapper: success
- Check project invariants: success
- Validation tool regression tests: success
- Install Android SDK: success
- Confirm Android SDK tools: success
- Official WFF validation: success
- Build debug APKs: in_progress
- Check APK contents: pending
- Official asset memory evaluation: pending
- Verify debug APK signatures: pending
- Upload debug APKs: pending
원격 변경 코드 원문을 별도 자기 재검토했다. 프로필 계약의 2~4 필수 활성 및 5 선언, 공통/override 선택, Gradle matrix·minSDK 검증, APK raw XML 대조, 기존 메모리·서명 검사 보존 확인. 실제 flavor override는 합성 단위 시험만 적용하며 실제 flavor 전용 XML 빌드는 후속 PoC 대상. WFF5가 disabled 상태이면 schema 검사만 수행한다. 스키마 PASS는 기기 호환성 증거가 아니다. CI 전체 종료 및 원본 로그/Artifact 확인 전 G3/G4/G6 최종 판정 보류. WO-01/GPT-02 PARTIAL 유지. 다음 작업: CI 원본 로그와 37 단위 시험/4개 schema verdict/3 APK raw XML·메모리·서명 검사 확인. 이후 API37/AGP9.1.1 전환은 격리 검증. 문서 전용 [skip ci]로 기존 CI 실행 보존.

## 회차 01 최종 증거
검증 코드 SHA 7820f90cbb35220fe9c6da4f9702374714d143d1. [CI 46001149417](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46001149417), job 140512806931, completed/success. 원본 로그 확인.
- 단위 시험 37 PASS / 0 FAIL (기존 26 + 신규 11). Wrapper 및 구조 검사 PASS.
- Validator 1.7.0: 공통 XML에 대해 WFF #2/#3/#4/#5 명시적 PASSED, 잘못된 XML 예상 실패 검출 4/4 PASS. #5는 schema-only, disabled. 별도 WFF5 기능 구현/빌드/설치 아님.
- 동적 프로필 clean build: WFF2/3/4 PASS, BUILD SUCCESSFUL in 41s. 실제 APK raw XML과 선택 원본 일치, resource-only/Manifest 검사 3/3 PASS. 메모리 및 debug signature 3/3 PASS.
| 프로필 | APK SHA-256 (CI) | active/ambient bytes |
|---|---|---:|
| wff2 | 708f01cffb6fdaa24f799156bf069b39dccd0417f12081ba1fd4d334ae9fb759 | 2371712/2371712 |
| wff3 | f4e7b8777b60d5d41b1710d5330fcb2520f24cfee5ab937d6cdb73c2f4f4d327 | 2371712/2371712 |
| wff4 | 4a9ab88b530977433f94d8f4fc006486009239ac6ff2fdb36826a26cc82b2aac | 2371712/2371712 |
Artifact [15197783477](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46001149417/artifacts/15197783477), 20948 bytes, expired=false, expires_at 2027-02-25T12:44:18Z, digest sha256:7ae4762c4484d735aac159d7fcf4a2612175f3012f1f12c35c529c08ded67c15. 업로드 로그/API 메타데이터 확인; 다운로드/재해시 미실시.
G0 PASS; G1 현재 회차 범위 PASS; G2 단위 fixture 및 실제 validator 실패 검출 PASS; G3 전체 CI PASS; G4 현재 3 APK 및 #5 스키마 PASS, 실제 WFF5/기기/전용 overlay 빌드 NOT RUN; G5 원격 코드 자기 재검토 수행, 독립 리뷰 미실시; G6 코드 SHA·CI·Artifact 메타데이터 대조 PASS; G7 원격 등록 및 문서 링크 검사(변경 전 기록 커밋 7f77441 기준 0 오류), 최종 문서 반영 재확인 필요.
발견/한계: WFF5 신규 flavor 활성화 때 test_build_tasks 기대 목록과 SDK/build-tools 경로를 함께 갱신한다. 실제 flavor override는 합성 단위 시험만 수행. 신규 APK raw XML 대조는 실제 정상 3종에 적용; 오류 주입 검사는 후속 회차에 추가. B-003은 SDK37/AGP9 전환 및 실제 빌드/설치 필요; B-004는 실제 기기/Ultra2025 출고 OS 미확정; B-007 정식 정책 제안, 승인 필요. B-002 유지. GPT-02 PARTIAL, WO-01 PARTIAL, GPT 완료 1/12, WO GO 0/38, 제품 NO-GO.
다음 회차: 별도 브랜치 또는 격리 CI에서 AGP9.1.1 + Gradle9.3.1 + SDK37 + build-tools36.0.0의 공식 배포 및 checksum 확인, WFF5 활성화 후보 작성. 기존 2~4 및 5 전체 정상/실패 스키마·clean build·raw APK·memory·signature 회귀 성공 후에만 main 변경 고려. 실기기 지원은 별도 시험. 이번 증거 커밋은 문서 전용 [skip ci].
