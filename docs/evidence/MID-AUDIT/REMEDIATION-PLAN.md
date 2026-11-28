# MID-AUDIT 후속 개선 실행 계획
상태: READY FOR USER DECISION. 제품 NO-GO. GPT-06 STOPPED/PARTIAL, GPT-07 NOT STARTED. 기준 main 3dae9dc885ebcd0091f72ee0e63ce64e9c9ada96. [결함 등록부](FINDINGS.md), [요구사항 추적](REQUIREMENTS-TRACE.md), [최종 감사](REPORT-FINAL.md). 이 문서는 기능 개발 승인이나 외부 에이전트 실행/병합 승인이 아니다.
## 실행 순서와 소유권
| 묶음 | 담당/수량 | 범위 | 시작 조건 | 종료 조건 |
|---|---|---|---|---|
| F00 | 사용자/관리자 1 | main 보호 및 required checks | 명시 승인 및 권한 | 실제 보호 API/설정 증거; 보호 규칙과 경로 필터 충돌 방지 |
| F01 | GPT 7 | Signature/Domain JUnit/WFF verdict/CI trigger/Fluid Digits/Manifest/profile parser | 사용자 후속 감사 개선 승인; 최신 main PRE-FLIGHT | 부정 fixture 최초 실패→수정 후 거부, 전체 호스트 회귀와 4 WFF 공식 validator/APK/서명/메모리, 정확한 아티팩트 |
| F02 | GPT 4 | LF, committed copy path, index flags, flavor isolation | F01 검증 및 fresh base | Linux 및 실제 Windows 전체 회귀, exact blob/재현, 기존 stale WFF4 거부 |
| F03 | GPT 3 | Actions SHA, checkout 권한, Gradle 전체 verification/lock | F01 후 검증 신뢰성 확보, F02 source 안정화 | 신뢰 근거 있는 pin/lock/metadata, clean build, 변조 거부, CVE/license 상태 및 미확인 명시 |
| G01 | GB 11 | GB-02 게이트, 상태/TTL/순서/정책/소비자 계약 및 자체 JUnit 검사 | 사용자 Grok Build 지시, 기존 branch/PR #3 소유권 유지 | 72+신규/81 baseline 및 100000+ 전이, 7개 부정 XML 및 R02 경계 검출; 정책/소비자 명세; 외부 검토 전 HOLD |
| D01 | 별도 domain 담당 1 | generic payload 불변성 | 기존 domain 소유권과 사용자 배정 확인 | 기존 81+신규, 불변성/복사/출처/revision 검증; GB와 계약 호환 |
| A01 | AG 10 | AG-01 안전한 사전검사/PNG/MP4/복구/증거 | 사용자 명시 AG 사용 가능 및 지시; PR #2 HOLD | 38+신규, 공식 스키마 매트릭스와 6개 APK 범위 유지, 실 ffprobe 및 bounded mock, 모든 위험 fixture 검출. 실제 runtime은 별도 승인 환경 |
| F04 | GPT 2 | 모션 보호 순서 및 문서 일치 | G01 계약 검토 및 F01~F03 | 동일/역순 보호 요청 시험, 문서 정정. 정적 host 모델과 runtime 구분 |
| C01 | Codex/사용자 | 실제 통합·런타임/실기기 | 관련 F/G/D/A 검증 및 독립 검토, 사용자 별도 승인 | 공식 지원 범위, SIGNATURE_DEVICE_GATE, QUALITY_GATES, 실제 센서/AOD/전력/오류/비동기 소비자 검증. 제품 승격 별도 승인 |
F00은 권한 이슈로 별도 병행 가능. F01→F02→F03은 공통 도구/CI 경로 순차. G01과 A01은 각각 소유 경로가 다르므로 사용자 승인 후 병행 가능. D01은 domain 변경 권한 확인 전 착수 금지. G01은 D01 결과와 호환성을 재시험하고 F04 전에 보호 계약을 합의한다. F04와 G01의 실제 적용 소비자는 C01에서 검증한다. 외부 agent 지시서는 실제 착수 시 최신 main/branch 기준으로 별도 생성한다. 사용량 제한 중 AG 작업을 다른 에이전트가 임의 인수하지 않는다.
## F01 상세 진입 명세
관련 R-02/05/07/10/20/22/25/26, WO-02/03/04/10/14/16/33/37 준비. 수정 허용: tools/signature_material.py, tools/check_domain_results.py, tools/verify_wff.py, tools/fluid_digits.py, tools/check_foundation.py, tools/profile_contract.py, 공통 Manifest 정책 helper(필요 최소), 관련 tests/unit/**, .github/workflows/domain-kotlin.yml, evidence 및 중앙 운영 문서. 실제 수정 파일은 최신 의존 관계 검사 후 범위 확정. 공통 APK 검사기와 기존 생성물 유지. 제품 apps/**, modules/domain/**, modules/intelligence/**, AG 경로 변경 금지. 테스트 도구를 먼저 강화한다. 원본 생성물 해시가 바뀌면 원인 분리 및 사용자 요구 보존 확인 전 통합하지 않는다.
1. 최신 HEAD 및 PRE-FLIGHT를 확인한다. 기준 SHA/원본 CI와 재현 fixture를 고정한다.
2. 격리 후보 브랜치를 만든다. 기존 문제를 현재 원본에서 먼저 재현한다.
3. 해당 검사기와 부정 회귀 시험을 함께 수정한다. 테스트 수량/검사 기준을 낮추지 않는다.
4. 호스트 전체 시험, Domain CI, doc-budget, Bootstrap 공식 4 profile 전체 단계 및 artifact 검사를 수행한다.
5. 후보 코드/시험/CI SHA와 원시 로그, manifest, APK hash, memory/signature의 대상 일치를 확인한다.
6. 별도 재검토 후 main 변경 여부를 확인한다. 검증된 경로만 non-force 반영한다. 변경된 main의 CI를 재확인한다. 타 에이전트 PR은 병합하지 않는다.
기존 호스트 316개와 domain 81개는 기준 수량이다. 추가 시험은 별도 집계한다. 원래 정당한 기능 변경 없이 baseline 시험 삭제 또는 SKIP 금지. 스키마 거부와 검사 도구 실패를 구분한다. artifact raw 로그/ZIP SHA/CRC/정확한 경로와 sourceCommit 일치 필수. 실패·미실행은 PASS 금지.
## 별도 종료 조건
- 모든 39개 ID가 해결, 승인된 정책 확정 또는 명시적 차단 이관으로 추적되어야 한다. 이관은 GO가 아니다. P1 관련 기능/검증 승격 전 필수 해결.
- 공급망: 전체 Git 이력 및 전체 dependency CVE/license/SBOM 검사, 저장소 보안 경보 조회 권한을 별도 확인. 미실행 시 UNKNOWN/NOT RUN. B-007 정식 서명·배포 정책 유지.
- 실제 Watch7 이후 지원 범위는 기기/설치 OS별 증거 확보 후 확정한다. 실기기 설치, 센서, 배터리, 발열, 8시간 안정성, 한영/12·24시, AOD 발광 픽셀 및 사용자 시각 승인 필수. SIGNATURE_DEVICE_GATE의 후보 승격과 정식 제품 출시를 분리한다.
- GPT-07의 실제 개발은 사용자 명시 승인 전 금지. 8개 테마·기상·건강·Wear Services·Mobile Studio의 기존 로드맵을 유지한다. 수정 단계는 로드맵의 신규 기능 작업으로 계산하지 않는다.
- 후속 첫 행동: 최신 main과 에이전트 HEAD 조회 → AGENTS.md/STATUS.md 및 운영 문서 → FINDINGS/본 계획 F01 → 현재 검사기/시험 원본과 최신 CI → 격리 재현. 예상 결과: 기존 결함 재현, 정상 대조 성공, 무관 경로 변경 0. 제품 NO-GO 유지.
롤백: 격리 후보는 병합하지 않거나 검증된 변경을 일반 revert한다. 강제 푸시, 원본 evidence 삭제, 사용자 기기 무단 변경 금지.