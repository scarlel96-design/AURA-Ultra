# GPT-02 — 호환성 및 다중 WFF 개발 기반
상태: PARTIAL / 회차 01 CI 성공 / WO-01 PARTIAL. 독립 준비 작업으로 시작한다. 요구사항 R-01, R-02, R-20, R-22, R-23, R-25. 이전 GPT-01 GO(빌드 토대), CI 46000111754/46000111676.
## 착수
AGENTS.md PRE-FLIGHT로 최신 HEAD, STATUS, 이 명세, 공식 근거, 현재 CI를 확인한다. 필요하면 WO-01 남은 산출물과 상세 WO-02 명세를 작성한다.
## 범위와 검증
1. Google 공식 WFF 버전별 지원 OS/API, 스키마 및 배포 요구사항을 대조한다. WFF5 공식 규격 및 실제 지원 상태를 확인한다. 미확인 API 레벨을 가정하지 않는다.
2. 삼성 공식 제품 자료에서 Watch7 이후 현재 판매/발표 모델과 해상도, 출시 OS, 설치 OS 확인 방법을 조사한다. 확인할 수 없는 기기·펌웨어는 unknown으로 유지한다.
3. AGP, Gradle, JDK, Android SDK, emulator 및 WFF 도구의 호환성을 확인한다. 기존 3개 빌드 및 26개 시험을 보존한다.
4. WFF5 build flavor는 공식 SDK와 스키마, 설치 조건이 확인되는 경우에만 추가한다. 미충족 시 B-003 기록 및 다음 검증 경로를 제시한다.
5. 별도 debug application ID와 정식 패키지/스토어/업데이트의 가능한 정책을 ADR로 비교한다. 정식 서명 및 배포는 사용자 승인 전 변경하지 않는다.
6. 버전별 소스·리소스 분리, 스키마 검사·실제 APK 경로·메모리·서명 검사에 대한 공통 프로필 계약을 검토하고 최소 구현한다. WFF 상위 전용 기능을 하위 빌드에 넣지 않는다.
7. 정상·실패 fixture, 공식 검증, 영향받는 모든 APK clean build와 CI 결과를 기록한다. 실기기 확인은 증거 없으면 NOT RUN.
## 산출물 및 판정
docs/evidence/GPT-02/REPORT-NN.md, WO-01 관련 TOOLCHAIN/DEVICE_MATRIX/API_CAPABILITIES/SOURCES, COMPATIBILITY.md, 필요시 ADR 및 상세 WO-02. 필수 공식 근거·프로필 계약·회귀 증거가 충족되면 범위 GO. 미확정 실기기/SDK/정식 배포는 해당 검증 미완료로 별도 보존. B-002/003/004/007에 대한 근거 및 남은 조건을 기록한다. 제품 출시 NO-GO 유지. 롤백: 해당 커밋만 revert.

## 회차 02 시작 조건
회차 01 증거: ../evidence/GPT-02/REPORT-01.md. API37 전환은 검증 브랜치 또는 격리 CI에서 수행한다. 공식 wrapper JAR 및 배포 SHA-256, AGP9.1.1/Gradle9.3.1/JDK17, SDK37/build-tools36.0.0 확인. WFF5 활성화 후보와 test_build_tasks 기대 목록, SDK 및 서명 도구 경로, 모든 프로필 계약을 동시에 갱신한다. 4개 APK 정상/실패 스키마·clean build·raw XML·memory·signature 전부 검증한다. 실제 WFF5 전용 기능 및 설치는 후속 PoC. 원본 XML 불일치 오류 주입 검사 추가. 실패 시 기존 main 유지 및 원인 기록. 정식 패키지/서명/배포 변경 제외.
