# GPT-04 — 원형 레이아웃 및 가독성 준비
상태: PARTIAL / 독립 준비 작업. 회차 01 원형 기하 후보 CI 진행. 관련 WO-03/04/09/16, R-01/03/10/17/18/20/22/26. GPT-03 GO. WO-01/02 PARTIAL; 정식 WO 완료 아님.
## 범위
1. 450 논리 좌표의 원형 안전 영역과 정보 영역 사이 간격을 정량화한다. 432/438/480/498 화면에 투영한다. 실제 설치 OS와 화면을 확인한 것으로 간주하지 않는다.
2. 공통 시간·날짜·배터리·걸음과 향후 심박/날씨용 영역을 명시한다. 표시되지 않은 값은 합성 예시로만 사용한다. 기존 제품 XML 유지. 글리프 너비와 실제 런타임 시험을 기하 시험과 구분한다.
3. 논리→픽셀 좌표의 정수 반올림·최소 크기·원형 경계·영역 충돌 검사와 정상/경계/오류 테스트를 구현한다. 개발용 SVG 와이어프레임과 기하 보고서를 결정적으로 생성한다. 합성 텍스트는 제품/런타임 스크린샷으로 간주하지 않는다.
4. 다음 회차에서 실제 WFF 텍스트 데이터, 시간/날짜 유지, AOD, 오류 상태, 12/24시간/한영 샘플의 공식 지원 및 글리프 검증을 검토한다. GB 도메인/FSM·AG 모션/Reference·실기기 영역은 제외한다.
## 검증 및 종료
기존 CI와 신규 좌표/경계/충돌/재현/누락·stale 실패 fixture를 실행한다. 각 화면별 증거를 기록한다. 프리뷰는 제품 자산에 포함하지 않는다. 실기기 가독성 미실시를 유지한다. 실제 제품 기본 표시 및 요구사항 충족 확인 전 GPT-04 전체 GO 금지. 별도 브랜치, 회귀·보고서·상태·차단점 기록. 출시 NO-GO.

회차 01 후보 5fd747b9cdb02be28ed0af8de24b82a200e5696e, CI 46059943214. 정적 기하 PASS. 전체 로그/재생성 증거 확인 후 통합. [REPORT-01](../evidence/GPT-04/REPORT-01.md).

## 회차 01 최종 CI 확인 (2026-11-28)
기준 main 2c3f26025a05849e00f65940819cc9121a204d7b. 후보 5fd747b9cdb02be28ed0af8de24b82a200e5696e. main CI 46059859835 job 140711216317 SUCCESS, 74 host tests, 4+4 APK/메모리/서명/오류 주입 PASS, artifact 15228870609. 후보 [CI 46059943214](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46059943214) job 140711488660 SUCCESS, 88 host tests PASS, 4+4 APK clean build, 공식 WFF 검사, 메모리 2371712 bytes active/ambient per APK, 서명 및 격리 실패/복원 PASS. 5개 LAYOUT_RESULT 해시가 write/check 두 프로세스에서 동일. JSON 3a09b6f3918634ed603670cf34523b80f343b0ed7d9941d05f0c69a1c14dc4b1. Artifact 15228217232, digest sha256:0ef0deb9c23336848ce9dd2719eb174afb17c0a03aa0f4fd15db5cdbbacacf58, 78990 bytes, expired=false. 로그와 메타데이터 확인, artifact 재다운로드 미실시. 기하 후보 코드 통합 승인, 기존 제품 XML 및 외부 소유 경로 변경 없음. G0/G1/G2/G3/G4(기하)/G6 PASS, G5 자기 재검토, G7 저장소 반영 확인 대상. 실제 글리프·런타임·데이터 상태 검증 미실시. GPT-04 PARTIAL, GPT 3/12, WO GO 0/38, 출시 NO-GO. 다음: 원형 레이아웃 기반 WFF 기본 데이터 표시 후보를 격리 생성/빌드, locale·오류 표시 fixture와 host evidence 보완.
