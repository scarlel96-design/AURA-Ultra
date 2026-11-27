# GPT-01 — 빌드 및 검증 파이프라인 안정화
상태: GO(초기 빌드 토대) / WO-01 PARTIAL, WO-02·04 준비 작업. 최종 증거: ../evidence/GPT-01/REPORT-02.md.
요구사항: R-02, R-20, R-22, R-25.
기준 코드 SHA: 544a7010f4bed515d667bfa6a9bbda1389f5bc92.
관련 실패: B-001 (CI 45997124733 및 45998056978), B-010 (검증기 판정 조건 위험).

## 목표
WFF 2·3·4의 리소스 전용 APK를 공식 규격에 맞게 빌드하고 CI에서 검증한다. 다음 작업의 신뢰할 수 있는 토대를 확보한다.

## 실행
1. main HEAD와 최신 관련 CI의 SHA, 실행 결과를 확인한다.
2. tools/check_apk.py 및 apps/watchface/build.gradle.kts, 병합 Manifest와 APK 구성에 영향을 주는 설정을 확인한다.
3. 실패 메시지를 실제 ZIP 항목 이름으로 구체화한다. CI에서 APK 목록과 manifest 검사 증거를 안전하게 기록한다. 실행 코드의 실제 존재와 오탐 가능성을 구분한다.
4. Google 공식 WFF resource-only 패키징 요구사항과 AGP 동작을 확인한다.
5. 원인을 해결하는 최소 변경을 수행한다. 검사 규칙을 완화하거나 파일을 숨겨 문제를 통과시키지 않는다. 임의 APK 후처리로 서명을 손상시키지 않는다.
6. 정적 검사, 공식 WFF validator, 3개 debug APK assemble, APK payload 및 병합 manifest 검사, artifact 업로드를 실행한다.
7. tools/verify_wff.py의 성공 판정 조건을 검토한다. 공식 도구의 대상 버전별 명시적 PASSED 결과를 확인하고, 실패·불명확·버전 불일치 입력의 회귀 시험을 추가한다. B-010을 증거에 따라 판정한다.
8. 가능하면 공식 Memory Footprint Evaluator의 고정 버전·체크섬 및 CLI 사용을 검토한다. 활성/AOD 평가를 CI에 추가하고 결과를 기록한다. 도구 사용이 불가능하면 이유와 후속 작업을 기록한다.
9. 검증 결과에 따라 B-001, B-010 및 STATUS를 갱신한다. 실패가 남으면 원인 또는 다음 진단 명령을 기록한다.

## 완료 기준
필수: 공식 Validator의 WFF2/3/4 명시적 성공과 실패 검출 시험, 3 APK 빌드, 리소스 전용 조건 준수, Artifact 확보, 검사 실패 시 CI 실패 유지. 공식 도구와 별도 자체 검사를 구분한다.
GO(빌드 토대): 위 항목 전부 실제 증거로 충족. 실기기 호환성이나 WO-01 전체 GO를 의미하지 않는다.
PARTIAL: 빌드는 성공했으나 APK 내용·검사·Artifact 중 하나가 미확인.
NO-GO: 공식 규격 실패 또는 실행 코드 포함 문제가 미해결.
제외: 정식 서명, Play 배포, 신규 테마·센서·건강 기능, 무단 SDK 라이선스/패키지 정책 변경.
증거: docs/evidence/GPT-01/REPORT.md. 롤백: 해당 변경 커밋만 revert. 사용자 파일이나 기존 기록을 삭제하지 않는다.

## 종료 결과
CI 46000111754/46000111676 SUCCESS, 26 PASS/0 FAIL. B-001/B-010 RESOLVED. 3 APK 메모리 예산 및 Debug 서명 PASS. Release/실기기/AOD 픽셀/전력 NOT RUN. 다음 GPT-02. 제품 출시 NO-GO.
