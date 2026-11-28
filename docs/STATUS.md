# 프로젝트 상태 — 단일 재개 체크포인트
2026-11-28 KST. [AGENTS.md](../AGENTS.md) PRE-FLIGHT를 적용한다. 최신 HEAD와 실제 CI를 확인한다. [archive](archive/README.md).

| 항목 | 현재 값 |
|---|---|
| 정본 | main |
| 최종 검증 코드 | 56db9192add22b7fef279dc6f4831516d7f00c32 |
| main 회귀 | [46094595911](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46094595911) SUCCESS 370 PASS; [46094595791](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46094595791) Windows 양쪽 370 PASS; [46094595812](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46094595812) 81 PASS; historical/doc SUCCESS |
| GPT-06 | 독립 준비 종료·중단 / PARTIAL (실기기 및 동적 효과 미검증) |
| GPT-04/05 | PARTIAL |
| GPT-07 | NOT STARTED / 사용자 별도 승인 대기 |
| 정식 WO GO | 0/38 |
| GPT 묶음 GO | 3/12 (PARTIAL 독립 준비 종료는 GO에 포함하지 않음) |
| 출시 | NO-GO |
| 다음 행동 | F03 R04 게시 checksum CI 확인 → provenance/strict 검증/잠금. GPT-07 및 실기기 설치는 별도 승인 대기. |

## 근거 및 이관
- [GPT-06 전체 종료 보고](evidence/GPT-06/REPORT-FINAL-CLOSURE.md). R01~R06 및 OPS-07 독립 준비 산출물 통합·자동 검증 완료. 결합 후보와 main 코드·시험·자산·CI 102개, 보호 경로 38개 blob 동일. 원본 아카이브 8개 SHA 동일. 활성 8개 문서 500021→24609 B(검증 코드 기준).
- [최종 개발용 APK](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46083911786/artifacts/15238910535): 114716 B, 직접 다운로드·SHA256·CRC·XML·PNG·RGBA 검증 PASS. WFF2~5 각 공식 평가기 2412312 B active/3181712 B AOD. 정적 Balanced 후보. 실제 RAM/전력 아님.
- [R05](evidence/GPT-06/REPORT-05-INTEGRATED.md): 152 SVG, 36 PNG, 최소 호스트 대비 5.729308:1, PNG 1266831→139710 B. [R06](evidence/GPT-06/REPORT-FINAL-INTEGRATION.md).
- [실기기 및 승격 게이트](operations/SIGNATURE_DEVICE_GATE.md): 실제 설치·렌더링·센서·동적 효과·발광 픽셀·전력 NOT RUN. Bootstrap 제품 리소스 유지. 실제 후보 프리뷰·육안 승인·사용자 승인 필요. 브랜치 보호 비활성화 확인(AUD-R01-01).
- AG-01 PR #2 HOLD, HEAD fc98c3ad5993e131f733a9444b5849e737a49086. GB-02 PR #3 HOLD, HEAD a1d1933391749ea65e07c1030f28c739f07fa1bc; R06 XML 82/81 및 공통 CI SUCCESS 확인, 로컬 호스트 2건 미해결, HOLD. [배정](operations/agent-orders/README.md). B-002/003/004/005/006/007/008 유지; [차단점](operations/BLOCKERS.md).
- [GPT-06](operations/GPT-06.md), [계획](operations/GPT_EXECUTION_PLAN.md), [이력](operations/WORK_LOG.md). 종료 기록 커밋은 문서만 변경한다. 검증 코드 SHA와 종료 기록 SHA를 구분한다. 새 문서 커밋 CI는 별도 상태를 확인한다.

## 중단
사용자 요청에 따라 GPT-06 전체 독립 준비 종료 후 중단한다. GPT-07 착수 금지. PARTIAL 및 제품 NO-GO 유지.

## 전체 중간 감사 — F01/F02 종료 / F03 진입
[최종 보고](evidence/MID-AUDIT/REPORT-FINAL.md) · [통합 결함 등록부](evidence/MID-AUDIT/FINDINGS.md) · [후속 개선 계획](evidence/MID-AUDIT/REMEDIATION-PLAN.md) · [26개 요구사항 추적](evidence/MID-AUDIT/REQUIREMENTS-TRACE.md).
- R01~R04 감사 보고와 증거를 유지한다. FINAL: GPT-06 대비 비문서 114/114 blob/mode 동일, 보존 ZIP 5/5 hash/CRC, Kotlin XML 17/162 cases, 외부 dependency 29/29 재검사.
- 40개 ID→39개(중복 1), P1 12/P2 24/P3 1/정책 2. 해결 판정 전 전부 OPEN. 전체 감사 접근 가능 조사 종료, 실기기/보안 전체 검증 PARTIAL, 출시 NO-GO.
- F01 검증기 → F02 재현성 → F03 공급망 → F04 보호 계약. G01/AG A01은 별도 사용자 지시 및 소유권, D01 별도 배정. F00 관리자 보호 설정, C01 실제 통합/실기기 별도 승인. 외부 PR HOLD, 감사 브랜치 병합 금지. GPT-07 미착수. 기존 B-002~008 유지.
- 최신 확인 main CI 46087742551 SUCCESS, doc 46088719146 SUCCESS; 46088719175 PENDING at report drafting. 기록 커밋 후 CI 별도 확인.

- F01/F02 완료 세부 이력: [F01 종료](evidence/MID-AUDIT/F01/REPORT-R04-FINAL.md), [F02 종료](evidence/MID-AUDIT/F02/REPORT-R04-FINAL.md), [이전 STATUS 원본](archive/2026-11-28-f03-r03-status/STATUS.md) (기준 f0a5b3c6e3b789607c6d0e4f1640f7a9d9eb1397). 11개 scoped RESOLVED.

- [F03 R01](evidence/MID-AUDIT/F03/REPORT-R01.md): c0a75d94dfc37e32a5fea1b52078dfaa215505c1, 19/19 Actions pin, checkout 5/5 false, 신규 9 methods. Red 370/9 policy errors; 중간 후보 Windows exit 처리 수정. 최종 후보 5 CI SUCCESS. Gradle OPEN.

- [F03 R02](evidence/MID-AUDIT/F03/REPORT-R02.md): 후보 370 PASS×3+81 Domain, 4 ZIP/8 APK/47 layout 직접 검증. 8 exact blob main 통합; 통합 CI SUCCESS.

- [F03 R03](evidence/MID-AUDIT/F03/REPORT-R03.md): pin/checkout 2개 scoped RESOLVED, main 370×3+81 PASS/4 ZIP 검증. Gradle audit 4cae0a70f3dfb6507846aad04336128229a85b6f, CI 46094868997 수집 중; trust/lock OPEN. F03 PARTIAL.

- [F03 R04](evidence/MID-AUDIT/F03/REPORT-R04.md): graph Android 177/Domain 19, 오류 0; 664 unique artifact UNREVIEWED. e7dd34de38012410d057460b03a74e4c12378d1d, 46095415032 checksum 수집 중. GB R06 17 XML 대조, PR #3 HOLD. strict/lock OPEN.
