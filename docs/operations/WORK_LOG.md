# 누적 개발 이력
이 문서는 시간순 append-only 기록이다. 사실 정정은 새 항목으로 추가한다. 현재 상태의 정본은 ../STATUS.md다.

## 2026-11-27 / 설계 기준선
- 커밋 6f074fbc86c1382a52bfeac57023c1a3f7a7559e: 초기 설계 문서 18개, 요구사항 26개, 38 WO 계획, 8개 테마, 15개 PoC.
- 실제 제품 코드 및 실기기 시험 미실시. 원본 심층 연구 보고서는 저장소에 별도 첨부하지 않음.

## 2026-11-27 / Bootstrap
- 커밋 171fca407653001f085683ee30c20608c8336b31: Gradle Wrapper 8.11.1/JDK17/AGP8.10.1/SDK36, WFF2/3/4 flavor, 기본 WFF XML, 임시 프리뷰, 자동 검증.
- CI 45997002132: Wrapper/구조 PASS, sdkmanager 미설치로 FAIL.
- 커밋 544a7010f4bed515d667bfa6a9bbda1389f5bc92: SDK 설치 action 추가.
- CI 45997124733: SDK/공식 WFF validator/Gradle assemble PASS, WFF2 APK 실행 코드 검사 FAIL, Artifact SKIP. WFF3/4 내용은 검사 중단으로 미확인. B-001 등록.
- 메모리, AOD 품질, 실제 워치 실행은 NOT RUN.

## 2026-11-27 / 세션 독립형 운영
- 기준 부모 SHA 544a7010f4bed515d667bfa6a9bbda1389f5bc92. GPT 선행 개발 목표, 작업 큐, 재개 규칙, 차단점·진행률·인계 정책 및 현재 CI 증거 기록.
- 사용자 승인: "다음 작업"으로 현재 상태를 기반으로 다음 작업을 자율 선택·수행.
- 이번 커밋은 운영 문서만 변경. 앱 코드 및 APK 오류 미수정.
- 다음: GPT-01 / B-001의 정확한 APK 항목 확인 및 원인 수정.

## 2026-11-27 / 운영 및 검증 규정 강화
- 기준 부모 SHA 28f51fd89b08cac0e183bbc6c5dfab98dd0f81fa. 기존 AGENTS, 재개 규정, 품질 게이트, 작업 양식 및 체크포인트를 대조 검토했다.
- 작업별 영속 기록, G0~G7 검증, 요구사항 추적표, 검사기 실패 검출, 구현 후 별도 리뷰, 증거 감사, 보고서 양식을 추가했다.
- CI 45998056978 로그에서 공식 validator PASSED #2/#3/#4, Gradle BUILD SUCCESSFUL, APK 검사 FAIL을 확인했다. B-001 유지. 검증 스크립트의 일반 VALID 포함 조건 위험 B-010 등록. 실제 오판은 미재현.
- 변경 범위: 운영 문서. APK 검사와 validator 스크립트는 미수정. 다음 작업은 GPT-01 유지.
- 증거: docs/evidence/OPS-02/REPORT.md. 최종 저장소 반영은 해당 커밋 이력에서 확인한다.
