# 프로젝트 상태 — 단일 재개 체크포인트
기준일: 2026-11-27. 이 문서는 매 작업 종료 시 업데이트한다.
현재 목표: GPT 선행 개발 최대화(작업량 추정 목표 65%, 조건부 상한 75%). 최종 프리미엄 품질 유지. Codex 중복 작업 최소화.

| 항목 | 현재 값 |
|---|---|
| 정본 브랜치 | main |
| 확인한 코드 SHA | 544a7010f4bed515d667bfa6a9bbda1389f5bc92 |
| 활성 GPT 작업 | GPT-01 / 빌드 안정화 |
| 활성 WO | WO-01 PARTIAL; WO-02·04 준비 작업만 일부 구현 |
| 다음 안전한 행동 | B-001: APK ZIP 내 실행 코드로 판정된 정확한 파일명 확인 → 원인 분석 → 최소 수정 → CI 재검증 |
| 다음 실행 명세 | operations/GPT-01.md |
| 현재 차단 | operations/BLOCKERS.md B-001 |
| 공식 WO GO | 0/38 |
| GPT 묶음 완료 | 0/12 |
| 실제 제품 완성도 | 미확정; 초기 빌드 토대 |
| 출시 판정 | NO-GO |

## 확인된 CI
코드 SHA 544a7010f4bed515d667bfa6a9bbda1389f5bc92, [CI 45997124733](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/45997124733), job 140499204563, 최종 conclusion failure.
- Wrapper SHA-256, 프로젝트 구조, SDK 설치·확인, 공식 WFF validator: PASS.
- Gradle WFF2/3/4 assemble: PASS (BUILD SUCCESSFUL).
- APK 내용 검사: FAIL (WFF2 실행 코드로 분류된 항목 존재; 파일명 및 원인 미확인).
- WFF3/4 개별 APK 내용 검사: NOT RUN (스크립트가 WFF2에서 종료).
- Artifact 업로드: SKIP.
- 메모리, 발광 픽셀, 실기기 렌더링·설치·센서·배터리: NOT RUN.
- 위 결과는 코드 SHA 기준이다. 운영 문서 커밋 후 새 CI가 있으면 실행 결과를 다시 확인한다.

## 재개 절차
AGENTS.md → operations/RESUME_PROTOCOL.md → operations/GPT_EXECUTION_PLAN.md → operations/BLOCKERS.md → operations/GPT-01.md → 실제 소스/CI.
main의 현재 HEAD를 먼저 확인한다. 확인한 코드 SHA와 최신 문서 SHA를 구분한다. 사용자가 "다음 작업"이라고 하면 재개 절차에 따라 실행한다.

## 남은 사항
실제 Watch7 크기/OS, 신형 기기 사양/설치, WFF5 지원, 정식 패키지/라이선스/서명은 미확정.
고급 소재·모션·8개 테마·외부 데이터·Wear Services·Companion은 아직 미완료. WFF4 Reference와 고급 모션은 PoC 필요.
문서 작업이 제품 기능을 완료한 것으로 계산되지 않는다. 다음 작업의 범위와 증거는 WORK_LOG와 해당 evidence에 추가한다.
