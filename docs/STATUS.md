# 프로젝트 상태 — 단일 재개 체크포인트
2026-11-28 KST. [AGENTS.md](../AGENTS.md) PRE-FLIGHT를 적용한다. 최신 HEAD와 실제 CI를 확인한다. [archive](archive/README.md).

| 항목 | 현재 값 |
|---|---|
| 정본 | main |
| 최종 검증 코드 | 53d43d918c3e3c1002b70473f5de843c0f946d8e |
| main 회귀 | [46083911786](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46083911786) SUCCESS 316 PASS/0 FAIL/0 SKIP; [46083911794](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46083911794) SUCCESS 7 PASS/12개 문서 |
| GPT-06 | 독립 준비 종료·중단 / PARTIAL (실기기 및 동적 효과 미검증) |
| GPT-04/05 | PARTIAL |
| GPT-07 | NOT STARTED / 사용자 별도 승인 대기 |
| 정식 WO GO | 0/38 |
| GPT 묶음 GO | 3/12 (PARTIAL 독립 준비 종료는 GO에 포함하지 않음) |
| 출시 | NO-GO |
| 다음 행동 | 전체 중간 감사 R04: 보안·공급망·요구사항 추적 및 종합 판정. GPT-07 및 실기기 설치는 별도 승인 대기. |

## 근거 및 이관
- [GPT-06 전체 종료 보고](evidence/GPT-06/REPORT-FINAL-CLOSURE.md). R01~R06 및 OPS-07 독립 준비 산출물 통합·자동 검증 완료. 결합 후보와 main 코드·시험·자산·CI 102개, 보호 경로 38개 blob 동일. 원본 아카이브 8개 SHA 동일. 활성 8개 문서 500021→24609 B(검증 코드 기준).
- [최종 개발용 APK](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46083911786/artifacts/15238910535): 114716 B, 직접 다운로드·SHA256·CRC·XML·PNG·RGBA 검증 PASS. WFF2~5 각 공식 평가기 2412312 B active/3181712 B AOD. 정적 Balanced 후보. 실제 RAM/전력 아님.
- [R05](evidence/GPT-06/REPORT-05-INTEGRATED.md): 152 SVG, 36 PNG, 최소 호스트 대비 5.729308:1, PNG 1266831→139710 B. [R06](evidence/GPT-06/REPORT-FINAL-INTEGRATION.md).
- [실기기 및 승격 게이트](operations/SIGNATURE_DEVICE_GATE.md): 실제 설치·렌더링·센서·동적 효과·발광 픽셀·전력 NOT RUN. Bootstrap 제품 리소스 유지. 실제 후보 프리뷰·육안 승인·사용자 승인 필요. 브랜치 보호 비활성화 확인(AUD-R01-01).
- AG-01 PR #2 HOLD, HEAD fc98c3ad5993e131f733a9444b5849e737a49086. GB-02 PR #3 HOLD, HEAD 122d81b05fb0fc56020fb3d03b667545eb6671c3; R05 증거 및 독립 Kotlin CI 확인. [배정](operations/agent-orders/README.md). B-002/003/004/005/006/007/008 유지; [차단점](operations/BLOCKERS.md).
- [GPT-06](operations/GPT-06.md), [계획](operations/GPT_EXECUTION_PLAN.md), [이력](operations/WORK_LOG.md). 종료 기록 커밋은 문서만 변경한다. 검증 코드 SHA와 종료 기록 SHA를 구분한다. 새 문서 커밋 CI는 별도 상태를 확인한다.

## 중단
사용자 요청에 따라 GPT-06 전체 독립 준비 종료 후 중단한다. GPT-07 착수 금지. PARTIAL 및 제품 NO-GO 유지.

## 전체 중간 감사 (사용자 승인, 기능 개발 아님)
- [R01](evidence/MID-AUDIT/REPORT-R01.md): 실제 main CI 46084484983 316 PASS 및 APK 4/4 재검사. P1/P2 발견 7개. 브랜치 보호 OFF, 검증기 결함.
- [R02](evidence/MID-AUDIT/REPORT-R02.md): [격리 Kotlin CI](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46086659055) SUCCESS, domain 81/81, intelligence 72/72, 신규 감사 9개 정상 실행(결함 관찰 포함). [원시 XML](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46086659055/artifacts/15239207748) 17개 직접 검사. TTL 오류 사유 소실, 관측 순서·보호 정책 통합 위험, 검증기 및 Windows CRLF 결함 재현. 제품 소스 변경 없음. 감사 브랜치 병합 금지.
- 감사 PARTIAL, 제품 NO-GO. 종합 판정 전 결함 수정·외부 PR 병합·GPT-07 착수 금지. 상세 우선순위는 보고서 및 BLOCKERS 참조.

- [R03](evidence/MID-AUDIT/REPORT-R03.md): 격리 [CI](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46087379624) SUCCESS, main host 316/316, AG-01 38/38, AG 원본 23개 blob 일치. 소재 XML/PNG 재생성 동일. 16 관찰 중 정상 대조 3, 12 위험 관찰, 1 ffprobe NOT RUN(CI). [보충 CI](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46087610218) SUCCESS; 로컬 exact 58개 source blob, 실제 ffprobe 정상 12/12, 서로 다른 컨테이너/디코딩 입력을 VERIFIED로 승인하는 결함 재현. PNG/Manifest/선택/덮어쓰기/모션 순서/메모리/복구 범위 문제. 실제 기기 NOT RUN. 두 감사 브랜치 병합 금지. AG-01/GB-02 HOLD. 제품 소스 변경 없음.
