# 차단점 및 불확실성 등록부
현재 항목만 관리한다. 이전 판정·증거 원본: [archive](../archive/README.md). OPEN/BLOCKED는 해결 증거 전 유지한다.

| ID | 상태 / 우선도 | 내용 및 증거 | 해결 조건 | 담당 |
|---|---|---|---|---|
| B-002 | BLOCKED / P1 | 현재 채팅 환경에 Android SDK/ADB 및 연결된 워치 없음 | CI로 대체 가능한 검증 수행; 실제 설치·센서·전력 시험은 접근 가능한 환경에서 수행 | GPT / Codex / 사용자 |
| B-003 | OPEN / P1 (SDK/빌드 해결) | CI 46002470824 SDK37.0 및 WFF5 Debug APK PASS. WFF5 실제 설치·런타임·전용 기능 미확인 | 실제 기기 및 P12 PoC 증거 | WO-08/35 |
| B-004 | OPEN / P1 | Watch7 크기/펌웨어/OS 및 최신 Samsung 기기 공식 매트릭스 미확인 | 공식 사양 확인, 실제 지원 대상별 기기/OS 기록 | WO-01 / 34 / 35 |
| B-005 | OPEN / P1 | WFF4 Reference, Variant, 숫자 전환, Gyro, 모션 트리거 및 최종 그래픽 품질 미검증 | P03~09의 실제 증거 | GPT-05/06 / Codex |
| B-006 | OPEN / P2 | 실제 KMA API 자격·할당량, Samsung Health 권한/파트너 및 독점 지표, Watch Face Push 조건 미확정 | 공식 조건 확인 및 실제 승인된 환경 시험 | GPT-08/09/11 |
| B-007 | OPEN / P1 | 정식 패키지 ID, 라이선스, 서명/배포 정책 미확정 | ADR 및 필요한 사용자 승인 | WO-29/38 |
| B-008 | OPEN / P2 | 전력/발열/실기기 소재 및 접근성 승인 미확보 | 비교 시험, 영상, 측정 및 사용자 승인 | WO-30~38 |

| 추가 항목 | 상태 / 조치 |
|---|---|
| AG01-AUD-01~09 | PR #2 HOLD. R07 원시 로그 38 PASS 확인, 실제 runtime NOT RUN. 최종 감사 완료, AG A01 해결 및 별도 검토 전 HOLD. |
| GB02-AUD-05~08 및 revision 보호 | PR #3 HOLD. R05 제출, 별도 Kotlin CI 72+81 PASS. 소비자·TTL·관측 순서 및 검증기 결함 해결 전 HOLD. |
| GB01-E1 | 비ASCII Windows Gradle worker 제한. ASCII worktree 사용. |
| GPT06-D1 | 호스트 링 충돌 해결: CI 46080386050. 실제 소재 승인 미확보. |
| B-011 | 현재 validator/evaluator pin RESOLVED: CI 46056609237. release 변경 시 재확인. |
| B-001/B-009/B-010, GPT04-D1/D2, GPT05-D1/D2/D3 | 이전 호스트 수정 검증 기록은 archive/evidence 참조. 재발 시 재개. |
| R06 | 소재 APK 후보 CI 46082882539 SUCCESS, 결합 CI 46083441184 SUCCESS, main CI 46083911786 SUCCESS. 공식 WFF, 패키지, 메모리, 서명 및 실제 렌더링 별도 게이트. |

신규 차단점은 ID, 심각도, 재현, 증거, 담당 및 해결 조건을 기록한다. 과거 세부 이력은 보관소 및 해당 evidence에 연결한다.

OPS-07: 문서 검사 CI 46083441202 SUCCESS; GitHub main 보호 OFF 및 ruleset 0 확인. 통합 및 main CI 46083911794 SUCCESS. 실기기 설치 승인/접근 없음; 기기 검사 NOT RUN.

R06 아티팩트 직접 다운로드/파일 검사 성공. 설치, 실제 렌더링, 로컬 서명 재검사 미실행; main 회귀 성공. B-002/005/008 유지.

GPT-06 독립 준비 종료/STOPPED. [종료 보고](../evidence/GPT-06/REPORT-FINAL-CLOSURE.md). 실제 기기, 동적 광학·모션, 후보 프리뷰 및 승격 승인 미충족. B-002/005/008 및 제품 NO-GO 유지. GPT-07 별도 승인 대기.

## 중간 감사 OPEN
[통합 등록부](../evidence/MID-AUDIT/FINDINGS.md): 39개(12 P1, 24 P2, 1 P3, 2 정책), 이전 원본 R01~04 링크 및 모든 ID 보존. 중복 R03-08=R01-04. [개선 계획](../evidence/MID-AUDIT/REMEDIATION-PLAN.md). F01~04 GPT, G01 GB, A01 AG, D01 domain 별도 승인, F00 관리자. 관련 P1 및 필수 결함 해결 전 통합 GO 금지. 전체 공급망/CVE/license/SBOM/실기기 미실행. F01 사용자 승인으로 진행. PR #2/#3 HOLD, GPT-07 금지.

F01 R01: AUD-R01-02/R03-02/R04-01/R04-03 수정 후보 구현, red 22 실패 재현, green host 성공. 전체 CI/아티팩트/통합 후 재검증 전 OPEN 유지. [보고서](../evidence/MID-AUDIT/F01/REPORT-R01.md). R01-03/04/05 다음 R02. GPT-07 미착수.

F01 R01 4개 ID 후보 자동 검증 PASS, main 통합 회귀 PENDING. G01 R06 첫 개선 지시서 준비, 외부 실행 미확인. [검증](../evidence/MID-AUDIT/F01/REPORT-R01-VERIFIED.md). 전체 39개 등록부 이력 유지; 해결 판정은 main CI 이후.

F01 R01 main CI SUCCESS 330 PASS 및 소재 원본 hash 일치. F01 R02 AUD-R01-03/04/05 후보 구현, Red 20 실패 재현; 전체 Green 검증 및 main 통합 회귀 전 OPEN 유지. [보고](../evidence/MID-AUDIT/F01/REPORT-R02.md). GPT-07 금지.

F01 R03: R02 후보 전체 CI 및 직접 artifact 검사 PASS, 6 경로 통합. main 회귀 전 3개 ID OPEN 유지. 이전 main 46091179097 Gradle Maven Central HTTP 429 FAIL; 새 통합 CI로 확인, 재발 시 제한 재실행. [보고](../evidence/MID-AUDIT/F01/REPORT-R03.md).

F01 R04: 7개 F01 ID scoped RESOLVED. main Bootstrap 46091554292, Domain 46091554286, doc 46091554290 SUCCESS; 이전 HTTP 429 실패 이력 유지. F02 4개 재현 완료, Windows NOT RUN, 후보 검증 대기. [종료 보고](../evidence/MID-AUDIT/F01/REPORT-R04-FINAL.md). 제품/실기기 차단 유지.

F02 R01 4개 ID 후보 구현/재현·focused local PASS. 실제 Linux full APK 및 Windows 두 matrix 최종 결과/원시 로그/아티팩트, 인접 basic 비번들 입력 경로 검토, 통합 회귀 전 OPEN. [보고](../evidence/MID-AUDIT/F02/REPORT-R01.md). 사용자 실기기 미실행.

F02 R02: R01 전체 후보 CI/ZIP PASS. 추가 basic 비번들 경로 수정 후보, red 재현 및 일부 green 성공. 전체 Linux/Windows, 아티팩트, 통합 main 회귀 전 4개 F02 ID OPEN. [보고](../evidence/MID-AUDIT/F02/REPORT-R02.md).

F02 R03: R02 후보 전체 CI/3 ZIP 직접 검사 PASS, 10 경로 통합. 통합 main Linux/Windows/문서 및 아티팩트 확인 전 4개 ID OPEN 유지. [보고](../evidence/MID-AUDIT/F02/REPORT-R03.md). F03 미착수.

F02 R04: 4개 F02 ID 자동 범위 RESOLVED. main 361 PASS씩 3환경, doc 및 직접 artifact PASS. [종료 보고](../evidence/MID-AUDIT/F02/REPORT-R04-FINAL.md). F03 세 ID OPEN; 실기기 차단 유지.

F03 R01: AUD-R01-07/R04-06 후보 구현, red 확인. 최종 Linux/Windows/Domain/historical/doc 및 artifact 미완료, 통합 전 OPEN. setup-java v4 deprecated; major migration 별도. AUD-R04-05 Gradle 전체 검증/잠금 및 CVE/license/SBOM 미완료. [보고](../evidence/MID-AUDIT/F03/REPORT-R01.md).

F03 R02: pin/checkout 후보 5 CI 및 4 ZIP PASS, 8 경로 main 통합. 통합 CI·아티팩트 전 두 ID OPEN. Gradle root/domain 인벤토리, 신뢰 원본·strict/lock 및 소유권 확인 필요. [보고](../evidence/MID-AUDIT/F03/REPORT-R02.md).

F03 R03: AUD-R01-07/R04-06 scoped RESOLVED, main 5 CI 및 4 ZIP PASS. AUD-R04-05 OPEN: audit 46094868997 결과/신뢰 원본/strict/lock/변조 거부/도메인 소유권 확인. [보고](../evidence/MID-AUDIT/F03/REPORT-R03.md).
