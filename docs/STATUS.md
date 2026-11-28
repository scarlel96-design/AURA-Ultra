# 프로젝트 상태 — 단일 재개 체크포인트
2026-11-28 KST. [AGENTS.md](../AGENTS.md) PRE-FLIGHT를 적용한다. 최신 HEAD와 실제 CI를 확인한다. [archive](archive/README.md).

| 항목 | 현재 값 |
|---|---|
| 정본 | main |
| 최종 검증 코드 | b7c8542123901cc49430a35f696a01e21efba915 |
| main 회귀 | [46117540962](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46117540962) Linux 383 PASS; [46117540990](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46117540990) Windows 383×2 PASS; [Domain](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46117540979) 81 PASS·검사기 15 PASS; doc SUCCESS. |
| GPT-06 | 독립 준비 종료·중단 / PARTIAL (실기기 및 동적 효과 미검증) |
| GPT-04/05 | PARTIAL |
| GPT-07 | NOT STARTED / 사용자 별도 승인 대기 |
| 정식 WO GO | 0/38 |
| GPT 묶음 GO | 3/12 (PARTIAL 독립 준비 종료는 GO에 포함하지 않음) |
| 출시 | NO-GO |
| 다음 행동 | D01 GO·종료. [ADR-008](adr/ADR-008.md) 소유자 검토 완료·보완. [RV01](operations/agent-orders/GB-01-RV01.md) 사용자 전달 대기; HOLD/F03/F04 차단. |

## 근거 및 이관
- [GPT-06 전체 종료 보고](evidence/GPT-06/REPORT-FINAL-CLOSURE.md). R01~R06 및 OPS-07 독립 준비 산출물 통합·자동 검증 완료. 결합 후보와 main 코드·시험·자산·CI 102개, 보호 경로 38개 blob 동일. 원본 아카이브 8개 SHA 동일. 활성 8개 문서 500021→24609 B(검증 코드 기준).
- [최종 개발용 APK](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46083911786/artifacts/15238910535): 114716 B, 직접 다운로드·SHA256·CRC·XML·PNG·RGBA 검증 PASS. WFF2~5 각 공식 평가기 2412312 B active/3181712 B AOD. 정적 Balanced 후보. 실제 RAM/전력 아님.
- [R05](evidence/GPT-06/REPORT-05-INTEGRATED.md): 152 SVG, 36 PNG, 최소 호스트 대비 5.729308:1, PNG 1266831→139710 B. [R06](evidence/GPT-06/REPORT-FINAL-INTEGRATION.md).
- [실기기 및 승격 게이트](operations/SIGNATURE_DEVICE_GATE.md): 실제 설치·렌더링·센서·동적 효과·발광 픽셀·전력 NOT RUN. Bootstrap 제품 리소스 유지. 실제 후보 프리뷰·육안 승인·사용자 승인 필요. 브랜치 보호 비활성화 확인(AUD-R01-01).
- AG-01 PR #2 HOLD, HEAD fc98c3ad5993e131f733a9444b5849e737a49086. GB-02 PR #3 HOLD, HEAD 0c4890ea7f69c6145791d17d51b98c97fed45c1d; 최종 XML 108/81·8 jobs 및 PR 인계 확인. [최종 검토](evidence/MID-AUDIT/GB-02-R08-CLOSEOUT-REVIEW.md). G01 독립 종료. [Host](evidence/MID-AUDIT/HOST-REPRO/REPORT.md) main 374×3 PASS, 범위 GO. [배정](operations/agent-orders/README.md). B-002/003/004/005/006/007/008 유지; [차단점](operations/BLOCKERS.md).
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

- [F03 R04](evidence/MID-AUDIT/F03/REPORT-R04.md): graph Android 177/Domain 19, 오류 0; 664 unique artifact UNREVIEWED. e7dd34de38012410d057460b03a74e4c12378d1d, 46095415032 checksum 결과 234 MATCH/430 미확보(고유), 0 mismatch. GB R06 17 XML 대조, PR #3 HOLD. strict/lock OPEN.

- [F03 R05](evidence/MID-AUDIT/F03/REPORT-R05.md): checksum 234/664 일치, 430 미확보(HTTP404), trust OPEN; audit host 378×3 PASS. strict/lock pilot fc3ffa3da8f06e911c5177be09843fa18db8c58f, CI 46095753190 진행 중. main 제품 코드 미변경.

- [F03 R06](evidence/MID-AUDIT/F03/REPORT-R06.md): Domain strict 81 PASS, 합성 변조/잠금 누락 거부 PASS. Android 178/178 lock graph 정확, 기존 count gate 차단; 수정 3609f3890c69267653badcef03961d75934de35a, CI 46096211808 진행 중. trust OPEN.

- [F03 R07](evidence/MID-AUDIT/F03/REPORT-R07.md): Domain strict/graph/negative PASS, audit host 383×3 PASS. Android HTTP429로 중단, 동일 SHA 단일 job 재시도 PENDING. [출처 검증 이관](evidence/MID-AUDIT/F03/PROVENANCE-HANDOFF.md). F03 PARTIAL.

- [F03 R08](evidence/MID-AUDIT/F03/REPORT-R08.md): 46096211808 Android retry strict PASS, WFF2~5 Debug/Release 8종, Domain 81, 197 configs/6 locks exact, 2 ZIP 직접 검사. 430 미확보 및 독립 출처 신뢰 OPEN. F03 PARTIAL. GPT-09 종료 감사 추가 계획은 기능 개발 재개 시 적용.

- [F03 R09](evidence/MID-AUDIT/F03/REPORT-R09.md): 373 components/664 artifacts provisional SBOM; OSV 21 MATCH/352 NO_KNOWN_MATCH/52 IDs, POM 237 declared/74 no direct/61 no pinned/1 hash mismatch. [CI](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46101636971) 증거 직접 검증, audit 정책 수정 CI PENDING. trust/출시 BLOCKED.

- [R10/GB R07 검토](evidence/MID-AUDIT/F03/REPORT-R10-START.md): R09 정책 수정 CI SUCCESS; audit 7bb1331b024f80d47ab349dc51c37ff0defa0ae8 상세 수집 시작. GB R08 지시서 등록, HOLD.

- [F03 R10](evidence/MID-AUDIT/F03/REPORT-R10.md): 52/52 권고 원문, CRITICAL 3/HIGH 21/MODERATE 26/LOW 2; 92 버전 일치, 관측상 buildscript/UTP. Portal 원본 해시 일치, Central 별도 metadata; trust OPEN. R11 개선 후보 검토.

- [F03 R11](evidence/MID-AUDIT/F03/REPORT-R11.md): 공식 호환 후보 AGP9.5.1/Gradle9.6.1, scratch audit 6a651984c3e3377b5cf15baf8d175cf5e26a38d8, CI 46103946447 8 builds PASS, OSV 8 MATCH/9 IDs로 fail-closed, ZIP 직접 검사. 43 IDs 관측상 감소, 새 UTP coverage OPEN. [결과](evidence/MID-AUDIT/F03/REPORT-R11-RESULT.md). 제품 미변경.

- [R12](evidence/MID-AUDIT/F03/REPORT-R12-RESULT.md) 9 IDs 잔여; [R13](evidence/MID-AUDIT/F03/REPORT-R13.md)~[R15](evidence/MID-AUDIT/F03/REPORT-R15.md) 출처 검토; [R16](evidence/MID-AUDIT/F03/REPORT-R16.md) 427/430; [R17](evidence/MID-AUDIT/F03/REPORT-R17.md) Portal 일치, JAR 2 redirect 차단. trust OPEN.
