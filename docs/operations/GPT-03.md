# GPT-03 — 결정적 그래픽 자산 및 WFF 생성 기반
상태: READY / 독립 준비 작업. 관련 WO-09/10, WO-02/03 준비, R-02/R-05/R-10/R-20/R-22/R-25. GPT-02 개발 기반 GO, WO-01 PARTIAL. WO-09/10 공식 선행 조건 미충족 상태를 유지한다.
## 작업 전
AGENTS PRE-FLIGHT 수행. 최신 프로필 계약과 4 APK CI 46002470824 확인. DESIGN_SYSTEM, MOTION_SPEC, PERFORMANCE, bootstrap tokens 및 실제 WFF XML, preview asset, 생성 대상의 소유권을 읽는다. 기존 초기 얼굴과 기준 자산을 보존한다.
## 작업
1. 공통 토큰의 타입, 필수 필드, 색상, 좌표, 논리 캔버스 및 안전 영역 계약을 정리한다. 문서와 실제 파일의 불일치를 기록한다.
2. 원본과 생성 파일을 구분한다. 결정적 파일 생성(고정 정렬/인코딩/메타데이터/해시), manifest 및 재생성·stale 검사를 구현한다. 생성 파일을 수동 편집하지 않는다.
3. 최초 범위는 bootstrap 레이아웃 및 자산의 재현이다. 고급 소재/모션은 승인된 PoC 뒤 구현한다. 지원되지 않는 XML 태그 삽입 금지. 원본 시각 의미를 변경하지 않는다.
4. 프로필별 공통/override source resolution을 검증한다. 별도 임시 작업 공간에서 실제 flavor override 빌드 및 원본 불일치 실패 검출을 검토한다. 테스트용 자산을 배포 APK에 혼입하지 않는다.
5. 정상·누락·중복·잘못된 색상/좌표/경로·재생성 차이 등의 실패 검출 fixture를 추가한다. 동일 입력 반복 실행의 산출물 해시를 비교한다.
6. 생성 결과의 공식 WFF2~5 schema, 4 APK clean build, raw XML 일치, asset memory, signature, 기존 40 테스트 회귀 및 새 단위 시험을 실행한다. 검증 실패 시 원인 수정 후 재실행한다.
## 산출물 및 종료
코드, 테스트, 원본/생성 계약, 사용 명령, 생성 자산 해시, docs/evidence/GPT-03/REPORT-NN.md, 관련 ADR 및 STATUS/WORK_LOG/BLOCKERS. 실제 재현/회귀 증거 충족 시 준비 작업 GO. 프리미엄 그래픽 품질/실기기 검증 미실시는 별도 기록. WO-09/10 GO로 계산하지 않는다. 제품 NO-GO. 신규 외부 라이브러리 없이 표준 도구 우선; 필요한 경우 공식 출처/라이선스/버전 기록. 롤백 해당 커밋만 revert.
