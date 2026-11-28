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
| GB02-AUD-05~08 및 revision 보호 | PR #3 HOLD. R06 로컬 Kotlin XML 82/81 PASS 대조, 공통 CI SUCCESS. R07 잔여 관측/TTL/보호 순서 및 정책 검토와 전용 CI 미적용; HOLD. 로컬 Python 3.14.7 호스트 2건 OPEN. |
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
[통합 등록부](../evidence/MID-AUDIT/FINDINGS.md): 39개(12 P1, 24 P2, 1 P3, 2 정책), 이전 원본 R01~04 링크 및 모든 ID 보존. 중복 R03-08=R01-04. [개선 계획](../evidence/MID-AUDIT/REMEDIATION-PLAN.md). F01~04 GPT, G01 GB, A01 AG, D01 domain 별도 승인, F00 관리자. 관련 P1 및 필수 결함 해결 전 통합 GO 금지. 전체 공급망/CVE/license/SBOM 및 실기기 검증 미완료. F01 사용자 승인으로 진행. PR #2/#3 HOLD, GPT-07 금지.

## 현재 후속 감사 차단점
- F01 자동 범위 7/7 RESOLVED: [종료](../evidence/MID-AUDIT/F01/REPORT-R04-FINAL.md). F02 자동 범위 4/4 RESOLVED: [종료](../evidence/MID-AUDIT/F02/REPORT-R04-FINAL.md). 이전 세부 원본 [보관](../archive/2026-11-28-225f9dd/operations/BLOCKERS.md).
- F03 AUD-R01-07/R04-06 RESOLVED: [R03](../evidence/MID-AUDIT/F03/REPORT-R03.md). setup-java v4 major migration 별도. AUD-R04-05 OPEN: [R08](../evidence/MID-AUDIT/F03/REPORT-R08.md) Android/Domain strict pilot PASS, 197 configs/6 locks exact, synthetic tamper/missing lock 거부. 미승인 metadata/lock main 적용 금지. 234/664 sidecar 일치도 독립 publisher trust 아님; 430 미확보. settings/detached coverage, owner 승인, isolated snapshot, 전체 CVE/license/SBOM 및 독립 검토 OPEN. GitHub 보안 API 조회 차단으로 경보 UNKNOWN. [이관](../evidence/MID-AUDIT/F03/PROVENANCE-HANDOFF.md). 동일 pilot 반복하지 않는다. [R09](../evidence/MID-AUDIT/F03/REPORT-R09.md): 373/664 provisional SBOM, OSV 21 MATCH/52 advisory IDs, 352 NO_KNOWN_MATCH, POM 1 hash mismatch/74 no direct/61 no pinned/237 declared. R10 상세 권고 및 marker 출처 검증, CI 재확인. trust 적용 차단 유지.
- F04 AUD-R03-01: F03 및 G01 보호 계약 합의 전 구현 착수 금지. AUD-R04-08 문서 개선 별도 범위. G01 R08-CLOSEOUT 108/81·8 jobs 대조, 3 경계 수정 후보 확인; [인계](agent-orders/GB-02-G01-HANDOFF.md) 최종 XML 108/81·8 jobs/PR 확인, 독립 개발 종료. [D01](agent-orders/GB-01-D01-CLOSEOUT.md) PR #5 HOLD: 불변성 GO, 10 jobs SUCCESS; RV01 C1/C2 범위 GO, PR #6 HOLD. RV02 #7 HOLD·3 경계 보완/F04/C01 OPEN. PR #2/#3 HOLD. 제품 NO-GO, GPT-07 미착수.

R10: 52 권고 상세 확인, CRITICAL 3/HIGH 21; Portal marker 기존 hash 일치, Central metadata 상이. 독립 trust, 업스트림 호환 개선, 라이선스 및 실제 범위 검증 OPEN. [보고](../evidence/MID-AUDIT/F03/REPORT-R10.md).

R11: AGP9.5.1/Gradle9.6.1 격리 후보 46103946447 8 builds PASS, 8 MATCH/9 IDs, CRITICAL 잔여; 새 UTP/lint/detached coverage와 trust OPEN. [결과](../evidence/MID-AUDIT/F03/REPORT-R11-RESULT.md). [보고](../evidence/MID-AUDIT/F03/REPORT-R11.md).

R12: [결과](../evidence/MID-AUDIT/F03/REPORT-R12-RESULT.md). AGP9.5.3 16 tasks PASS, 잔여 9 IDs 동일·CRITICAL OPEN. 제품 적용 금지; detached/실기기·trust/license OPEN. 동일 후보 반복 및 강제 전이 버전 적용 금지.

R13: [보고](../evidence/MID-AUDIT/F03/REPORT-R13.md). 우선 48 exact bytes/.asc 확보; 기존 미확보 38개 바이트 보완(원본 sidecar는 여전히 430 UNAVAILABLE). 서명 검증·신뢰·라이선스 승인 0; 나머지 392 바이트 재확인 및 전체 범위 OPEN.

R14: [보고](../evidence/MID-AUDIT/F03/REPORT-R14.md). 48 바이트 일치, 18 강한 서명 검증(12 공식 키 대조/6 발견 전용), 28 SHA-1/2 공개키 미확보 차단. 신뢰 승격 0; 독립 강한 출처, 서명자 승인, 전체 라이선스/392 바이트 범위 OPEN.

R15: [보고](../evidence/MID-AUDIT/F03/REPORT-R15.md). Apache JAR 강한 배포 checksum 일치, JDOM JAR 및 jose4j 태그 POM exact; Guava 소비자 키 대조. SHA512 sidecar 28/28 HTTP404, jose4j 키 미확보, 신뢰 승인 0. 동일 조회 반복 금지. 392 미확보 바이트 범위 및 라이선스 OPEN.

R16: [보고](../evidence/MID-AUDIT/F03/REPORT-R16.md). 392 검사/389 일치/1 POM 불일치/2 Kotlin compiler JAR 미확보. 누적 427/430, 전체 661/664에 sidecar 또는 byte 일치 근거, 신뢰 승인 0. 425 baseline 서명 존재/12 강한 서명 검증. [R17](../evidence/MID-AUDIT/F03/REPORT-R17.md): Portal POM exact, 원본 Gradle route 미확정; JAR 2개 Central 양쪽 github.com redirect 차단. 428/430 byte 근거(경로별), 662/664 combined. 자동 출처 수집 종료, 독립 네트워크 및 trust/CVE/license/strict 도입 승인 차단. 동일 수집 반복 금지.

Host: [보고](../evidence/MID-AUDIT/HOST-REPRO/REPORT.md). Python3.14.7 zlib-ng PNG hash drift 재현, RGBA/XML 동일; fresh LF 정상. CRLF-only 복구/정본 PNG 차단 main 374×3 PASS, 범위 GO. 실제 로컬 palette 원인 미확정; 3.14 호환 미승인. 로컬 사용자는 검증된 Python3.12 사용.
