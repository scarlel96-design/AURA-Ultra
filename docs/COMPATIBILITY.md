# 기기 및 WFF 호환성
상태: 목표 목록. 실제 지원 판정은 미실시. 조사 기준 2026-11-27. 신형 모델명과 사양은 WO-01에서 삼성 공식 자료로 재확인한다.

| 목표 기기 | 화면 후보 | 출시 OS 후보 | 시험 상태 |
|---|---|---|---|
| Watch7 40/44mm | 432/480 정사각 픽셀의 원형 화면 | Wear OS 5 | NOT RUN |
| Watch Ultra 2024 | 480 | 5 | NOT RUN |
| Watch8 40/44mm | 438/480 | 6 | NOT RUN |
| Watch8 Classic | 438 | 6 | NOT RUN |
| Watch Ultra 2025 | 480 | 6 | NOT RUN |
| Watch9 40/44mm | 438/480 | 7 | 공식 사양 재확인 |
| Watch Ultra2 | 498 | 7 | 공식 사양 재확인 |
| 이후 모델 | 미정 | 미정 | 신규 프로필 필요 |

실제 기기의 설치된 OS와 WFF 지원 수준을 기준으로 빌드를 선택한다. 업데이트 상태·지역·모델 차이를 기록한다. 출시 OS를 현재 OS로 간주하지 않는다.

| WFF | OS / API 기준 후보 | 빌드 | 기능 |
|---|---|---|---|
| 2 | Wear OS 5 / 34 | Compatibility | 날씨, 기본 소재 및 모션 |
| 3 | Wear OS 5.1 / 35 | Compatibility+ | 지원 혼합 모드·텍스트 개선 |
| 4 | Wear OS 6 / 36 | Continuity | AOD transition, Reference, 색상 변환 |
| 5 | Wear OS 7 / 공식 API 확인 | Next | 확장 혼합, 텍스트·설정 기능 |

공식 버전별 스키마를 확인한다. 상위 빌드에만 해당 기능을 포함한다. 공통 디자인 토큰에서 버전별 XML을 생성한다. OS 업그레이드 후 설정 호환성과 업데이트 경로를 검증한다. 패키지 식별자와 스토어 배포 방식은 WO-02에서 확정한다.

## 프로필 계약
deviceModel, screenWidth, screenHeight, installedWearOs, apiLevel, supportedWffVersion, firmwareBuild, region, capabilities, testEvidenceRef. 미확인 값은 unknown으로 유지한다. 미래 모델은 프로필·스키마·실기기 시험을 추가한다. 자동 지원 보장은 금지한다.

## 시험
에뮬레이터로 화면 크기와 기본 스키마를 검증한다. Samsung Remote Test Lab은 접근 가능 기기를 확인한 후 사용한다. 실물 센서, AOD, 밝기, 전력 및 사용자 체감은 실기기에서 검증한다. 원격 시험을 배터리 시험으로 대체하지 않는다.
