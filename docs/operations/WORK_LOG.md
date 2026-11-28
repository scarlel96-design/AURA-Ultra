# 작업 이력 — 최근 체크포인트
2026-11-28 KST. [직전 원본](../archive/2026-11-28-d01-junit/WORK_LOG.md), blob 8181dab04fcac39caa474e40304b30704856d8e7.

- F03 R14: be0bd7b2be4c, 46109868360 정책상 FAIL, 6+10 시험 PASS; 48 bytes/18 VALID/30 차단, 12 공식 키 대조. [보고](../evidence/MID-AUDIT/F03/REPORT-R14.md). 증거 ZIP 검증, 제품 변경 없음.
- F03 R15: d9a05594825f, 46110391691 SUCCESS(증거 수집), 7+10 PASS, 28 SHA512 404, 3 공식 출처 exact/Guava 키 대조. R14 공통 CI SUCCESS. [보고](../evidence/MID-AUDIT/F03/REPORT-R15.md). 승격 없음.
- F03 R16: 5c1df1f4ccf9, 46111088119 수집 392/389 일치, 3 차단, 7+10 PASS, ZIP 검증. R15 공통/main CI SUCCESS. [보고](../evidence/MID-AUDIT/F03/REPORT-R16.md). 427/430 누적, 신뢰 0.
- F03 R17: c2b15e0eb373, 46112122206 9+10 PASS/출처 게이트 FAIL; POM 2 경로 exact, JAR 2 redirect 차단. [보고](../evidence/MID-AUDIT/F03/REPORT-R17.md). 반복 수집 종료. 제품 코드 우선 원칙 반영.
- GB R08-CLOSEOUT 총괄 검토: 63fbb8056428, 20 XML 108/81, 7 red→PASS, 8 jobs SUCCESS; 기존 6 상태 단언 보강/PR 본문 인계. [검토](../evidence/MID-AUDIT/GB-02-R08-CLOSEOUT-REVIEW.md). R09 금지, D01 별도 승인.
- Host 재현성 후보 4cf403199dd1: CRLF 복구/정본 패키징 guard. 46113219202 Python3.14.7 4 PASS, PNG drift exact 재현·의도된 FAIL. [보고](../evidence/MID-AUDIT/HOST-REPRO/REPORT.md). 공통 CI PENDING; main 제품 미변경.
- G01 최종 검수: e050937fd347 5 시험 파일/6 단언 추가, 삭제 0. 최종 XML/Bootstrap/PR 기록 대기. [D01 지시서](agent-orders/GB-01-D01.md) 준비(별도 승인).
- Host 후보 4cf403199dd1: 374×3 PASS, 3 ZIP/8 APK 직접 확인, XML/PNG/RGBA 보존. 검증된 4개 경로 선택 통합. 3.14 진단 FAIL 유지, main CI PENDING.
- Host main 27c2f6f89173 374×3 PASS, 3 ZIP/8 APK 및 layout 47 exact, 범위 GO. G01 최종 0c4890ea7f69 XML 108/81·8 jobs/PR 대조, 독립 종료. D01 별도 승인; 제품 NO-GO.
- D01 PR #5 df843d75bff5: 81 PASS direct XML; 88 test CI checker FAIL. [마감 지시](agent-orders/GB-01-D01-CLOSEOUT.md). HOLD.

- D01 JUnit 후보 f476e37720e7: 81+7 exact, 15 checker PASS, Domain 81, host 383×3, 4 ZIP/8 APK 직접 검사. 3 경로 선택 통합, main CI PENDING. [보고](../evidence/MID-AUDIT/D01-JUNIT/REPORT.md). PR #5 HOLD.

- D01 JUnit main b7c854212390: Domain 81/검사기 15, host 383×3 PASS, 4 CI SUCCESS, 4 ZIP/8 APK/47 layout 직접 검증. 검사기 GO. D01 ef57005 시험 복원/PR 88 PASS 직접 XML 확인; push 구 검사기 FAIL, 최신 composite 증거 대기. [보고](../evidence/MID-AUDIT/D01-JUNIT/REPORT.md).

- D01 최종 검수: ef57005 → c7cef1d, 원본 XML 21개/88+108 PASS, red 1 FAIL, 9/10 CI jobs SUCCESS; push 구 검사기 FAIL. [검수](../evidence/MID-AUDIT/D01-CLOSEOUT-REVIEW.md). 최신 main 반영·push/PR CI 재검증 대기, HOLD.

- D01 bfb115a main 병합, Domain 소스 변경 없음, 신규 CI PENDING. [권한 철회 계약 후보·14 시험](../evidence/MID-AUDIT/REVOCATION-CONTRACT-REVIEW.md) 사전 검토, 미승인/PARTIAL. 소스 변경 없음.

- D01 FINAL-CI: bfb115a 8 runs/10 jobs SUCCESS, push/PR 88 exact, 검사기 15 each, Domain 17 source/test blobs 동일, 최종 d847028 기록만 변경. [검수](../evidence/MID-AUDIT/D01-CLOSEOUT-REVIEW.md). 불변성 범위 GO·독립 종료, HOLD; 권한 계약 합의 대기.

- 권한 계약 ADR-008 PROPOSED, 격리 oracle 16/16·부정 변형 5/5 검출; 실제 제품 시험 NOT RUN. [소유자 검토](agent-orders/GB-REVOCATION-REVIEW.md) 준비; D01/G01 종료 유지.

- ADR-008 GB 양 역할 검토 수령·총괄 대조; 권한 ticket 발급·무효화·provenance·출력 경계 보완. [RV01](agent-orders/GB-01-RV01.md) Domain 격리 후보 지시 준비, 사용자 전달 전 미착수. 기존 88/108 유지.

- RV01 로컬 보고 56675d8: 102/108, 100000 PASS(미독립 확인). [검사기](../evidence/MID-AUDIT/RV01-JUNIT/REPORT.md) 정확한 81/88/102 등록·24 자체 시험 PASS, main CI 대기. 사용자 승인: GPT-09 종료 전면 감사 대신 변경 영향 통합 검증, 최종 감사 유지.

- RV01 8f53bff 독립 검수: 22 XML 102/108, 26 Domain blob 동일, 15 CI SUCCESS; capability seal 재사용 및 대상 scope 미대조 정적 결함 2건. [마감](agent-orders/GB-01-RV01-CLOSEOUT.md), HOLD. 사용자 승인: 최종 감사 Codex 주력/GPT 검수, GB/AG 가용성 기반 배정.

- RV01-CLOSEOUT 558e188→68f52eb: red 2 FAIL, green 22 XML 102/108, 15 CI SUCCESS, 3 Domain 원본 로그 대조; C1/C2 범위 GO·독립 종료. [RV02](agent-orders/GB-02-RV02.md) 격리 데이터 경계 후보 준비, 사용자 전달 대기. HOLD 유지.

- RV02 로컬 보고 dbacc75→a611bda, 124/102·100000 PASS(미독립 확인). [CI 등록](../evidence/MID-AUDIT/RV02-CI/REPORT.md) 고정 108/124, RV01 26 blob overlay, 신규 자체 시험 10 PASS·YAML 구조 확인. main CI 대기; 원격 제출 전 확인.

- RV02 75c9ab4 검수: 23 XML 102/124, 29 Intelligence blob 동일, 16 CI SUCCESS, 실제 composite 로그 3건. [검수](../evidence/MID-AUDIT/RV02-REVIEW.md) 3 경계 보완, PARTIAL. [마감](agent-orders/GB-02-RV02-CLOSEOUT.md) 사용자 전달 대기.

- RV02-CLOSEOUT 8dd1c7c→7501dcf: red 5 FAIL, green 23 XML 102/124, 8 CI SUCCESS, 2 실제 복합 로그 대조. 재현 수정 검수 완료, 독립 개발 중지/PARTIAL. [잔여 계약 및 통합 인계](../evidence/MID-AUDIT/RV02-REVIEW.md); 승인 전 인수·병합 금지.

- F04 AUD-R04-08: [문서 정정](../evidence/MID-AUDIT/F04/REPORT-DOC.md) ADR-007 WFF2~5 ID/최소 API, BUILD_GUIDE 생성기·Python3.12·역사 기준선 정정. 제품 변경 0; CI 대기. AUD-R03-01/F03 차단 유지.

- AUD-R04-08 GO: ca008a7 공통 3 CI/4 jobs SUCCESS, Linux·Windows 402×3 host PASS, doc 7 PASS. 감사 14/16. [F03 로컬 인계](agent-orders/CODEX-F03-HANDOFF.md) 사용자 승인 대기; F04 구현 차단, PR HOLD.
