# 외부 개발 에이전트 — 현재 배정
2026-11-28 KST. 상태와 소유권을 분리한다. [이전 이력](../../archive/README.md).

| 담당 | ID | 상태 | 브랜치 | 소유 경로 |
|---|---|---|---|---|
| ChatGPT | GPT-04/05/06 | GPT-06 독립 준비 종료·중단 / PARTIAL; 중간 감사 종료; F01 R01 main 회귀 SUCCESS; F01 자동 범위 종료; F02 자동 범위 종료; F03 R17 자동 출처 수집 종료·신뢰 미승인 PARTIAL; GPT-07 미착수 | main 및 격리 후보 | 그래픽, 공통 도구/CI, 중앙 운영 문서 |
| Grok Build | [GB-01 D01](GB-01-D01-CLOSEOUT.md) | PR #5 HOLD; D01 불변성 GO·독립 종료, 88/108·10 jobs 확인; 권한 계약 별도 | agent/grok/GB-01-D01 | modules/domain/**, docs/evidence/GB-01/** |
| Grok Build | [GB-02](GB-02.md) | G01 R08-CLOSEOUT 108/81 XML·8 jobs 대조; 최종 XML 108/81·8 jobs/PR 대조, 독립 개발 종료, HOLD | agent/grok/GB-02 | modules/intelligence/**, docs/evidence/GB-02/** |
| Antigravity | [AG-01](AG-01.md) | R07 격리 재시험 38 PASS, 감사 결함 OPEN, A01 후속 지시/사용량 회복 대기, runtime NOT RUN, HOLD | agent/antigravity/AG-01 | tests/compatibility/ag-01/**, docs/evidence/AG-01/** |
| Codex | 미배정 | NOT STARTED | 추후 지정 | 고난도 통합·실기기 |

매 턴 AGENTS.md PRE-FLIGHT 및 G0~G7. 사용자 지시에 따라 각 CLI에서 실행한다. 동일 파일 수정 금지. 외부 에이전트는 자기 evidence에 중앙 갱신 제안을 기록한다. 총괄만 중앙 문서 갱신. PR #2/#3 자동 병합·강제 푸시 금지. 사용량 제한 중 AG 작업을 다른 에이전트에게 임의 인수하지 않는다. 신규 SDK/AVD 설치는 사용자 승인 전 금지. 독립 모듈의 자체 GO는 총괄 통합 GO가 아니다. 제품 NO-GO.

중간 감사 후속 배정 제안: [통합 등록부](../../evidence/MID-AUDIT/FINDINGS.md), [실행 계획](../../evidence/MID-AUDIT/REMEDIATION-PLAN.md). 기존 소유권 유지. D01 작업 제출 확인. 공통 JUnit 검사기 등록은 GPT 소유; PR #5 자동 병합 금지. 감사 branch 병합 금지. 제안은 agent 작업 시작 또는 병합 승인이 아니다.

[GB-02 G01 R06](GB-02-G01-R06.md): 사용자 전달용 후속 개선 지시. 기존 R05 및 소유권 유지, PR #3 HOLD.

[GB-02 G01 R07](GB-02-G01-R07.md): 사용자 전달용. 잔여 G01 및 F04 보호 계약 후보. R07 제출, XML/CI 대조 완료, PR #3 HOLD.

[GB-02 G01 R08](GB-02-G01-R08.md): 보호 계약 보완 제출 및 증거 대조 완료. [R08-CLOSEOUT](GB-02-G01-R08-CLOSEOUT.md): 3 경계 수정 후보 확인. [최종 인계](GB-02-G01-HANDOFF.md): 6 상태 단언 및 최종 인계 확인, 독립 개발 종료. [D01](GB-01-D01.md) 착수·PR #5 제출, [마감 보완](GB-01-D01-CLOSEOUT.md). R09 없음.

[권한 계약 검토](GB-REVOCATION-REVIEW.md): ADR-008 후보 검토 전용, 사용자 전달 후 실행. 제품 코드 변경 승인 아님.

[GB-01 RV01](GB-01-RV01.md): PR #6 68f52eb; C1/C2 마감 검수 GO·독립 종료. D01/G01/RV01 HOLD 유지.

GB/AG는 가용 시 배정(소진 시 약 1주 불가 가능). 인수는 사용자 승인·기존 담당 정지·정확한 상태 인계 후만 허용. 최종 감사 Codex 주력/GPT 독립 검수, GB/AG 선택 전문 검수. 필수 기술 게이트 유지.

[GB-02 RV02](GB-02-RV02.md): PR #7 7501dcf HOLD; 재현 5건 수정 검수 완료, 독립 개발 중지/PARTIAL. [잔여 계약 검증](../../evidence/MID-AUDIT/RV02-REVIEW.md) 승인 후 인계. F04/C01 및 실제 step 연동 금지.
