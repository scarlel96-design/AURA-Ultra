# 기기 및 WFF 호환성
조사 기준 2026-11-27. 공식 제품 사양과 실제 시험을 구분한다. 모든 실기기 설치/렌더링/성능 시험 NOT RUN.
| 목표 기기 | 화면 해상도 | 출시 OS | 실기기 |
|---|---|---|---|
| Watch7 40 / 44mm | 432 / 480 | Wear OS 5 | NOT RUN |
| Watch Ultra 2024 | 480 | Wear OS 5 | NOT RUN |
| Watch8 40 / 44mm | 438 / 480 | Wear OS 6 | NOT RUN |
| Watch8 Classic 46mm | 438 | Wear OS 6 | NOT RUN |
| Watch Ultra 2025 | 480 | 출고 OS 추가 확인 | NOT RUN |
| Watch9 40 / 44mm | 438 / 480 | Wear OS 7 | NOT RUN |
| Watch Ultra2 47mm | 498 | Wear OS 7 | NOT RUN |
| 이후 모델 | unknown | unknown | 신규 프로필 필요 |

공식 근거: [기기 매트릭스](evidence/WO-01/DEVICE_MATRIX.md), [출처](evidence/WO-01/SOURCES.md). 설치된 OS와 실제 지원 규격을 확인한다. 출시 OS를 현재 OS로 간주하지 않는다.

| WFF | OS/API | 빌드 상태 | 기능 계획 |
|---|---|---|---|
| 2 | Wear OS 5 / 34 | enabled | 날씨, 기본 소재 및 모션 |
| 3 | Wear OS 5.1 / 35 | enabled | 혼합 모드 |
| 4 | Wear OS 6 / 36 | enabled | AOD transition, Reference, 색상 변환 |
| 5 | Wear OS 7 / 37 (OS 및 API 근거; 공식 WFF 버전 표는 4까지) | enabled; debug CI PASS | 확장 혼합, 텍스트·설정 기능 |

WFF5는 공식 발표 및 스키마 존재 확인. API37 지원 toolchain 격리 검증 PASS. WFF2/3/4 최소 API 및 ID를 유지한다. 공식 지원과 프로젝트 설치 호환성은 다르다. [API 매트릭스](evidence/WO-01/API_CAPABILITIES.md).
프로필 계약 compatibility/profiles.json 및 tools/profile_contract.py. 공통 src/main/res/raw/watchface.xml, 필요한 경우 src/wffN/res/raw/watchface.xml override. 활성 프로필별 스키마·실제 APK·메모리·서명 검사. 비활성 프로필 스키마 검사만으로 APK/설치를 주장하지 않는다. [패키지 정책 ADR](adr/ADR-007.md).

## 기기 프로필 및 시험
deviceModel, screenWidth, screenHeight, installedWearOs, apiLevel, supportedWffVersion, firmwareBuild, region, capabilities, testEvidenceRef. 미확인 값 unknown. 신규 기기 자동 지원 보장 금지.
ADB 읽기 전용 확인: adb devices -l; adb -s DEVICE shell getprop ro.product.model; adb -s DEVICE shell getprop ro.build.version.sdk; adb -s DEVICE shell getprop ro.build.fingerprint; adb -s DEVICE shell wm size. 실제 WFF 지원 및 설치는 별도 검증한다. 에뮬레이터/Remote Test Lab 이용 가능 여부 및 실물 센서·AOD·밝기·전력 시험은 후속 검증. 원격 시험을 배터리 측정으로 대체하지 않는다.

## 확인된 자동 시험
CI 46001149417: WFF2~5 공통 XML schema PASS 및 invalid XML 4/4 검출, WFF2/3/4 Debug APK 빌드·원본 XML·메모리·서명 PASS. WFF5 APK와 기기 시험 NOT RUN. 자세한 증거: [REPORT-01](evidence/GPT-02/REPORT-01.md).

CI 46002470824: SDK37.0, WFF2~5 Debug APK/스키마/원본 XML/메모리/서명 4/4 PASS. 실제 WFF5 전용 기능, 설치, 기기 호환성 NOT RUN. [REPORT-02](evidence/GPT-02/REPORT-02.md).
