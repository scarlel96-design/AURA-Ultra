# 차단점 및 불확실성 등록부
OPEN은 미해결, BLOCKED는 외부 조건 필요, RESOLVED는 해결 증거가 있는 상태다. 기록을 삭제하지 않는다. 해결 시 검증 SHA와 증거를 추가한다.

| ID | 상태 / 우선도 | 내용 및 증거 | 해결 조건 | 담당 |
|---|---|---|---|---|
| B-001 | RESOLVED | 과거 WFF2 APK classes.dex 및 AGP 생성 R 클래스 5개 재현, 현행 3 APK 리소스 전용 검사 PASS | CI 46000111676/46000111754; REPORT-02 | GPT-01 |
| B-002 | BLOCKED / P1 | 현재 채팅 환경에 Android SDK/ADB 및 연결된 워치 없음 | CI로 대체 가능한 검증 수행; 실제 설치·센서·전력 시험은 접근 가능한 환경에서 수행 | GPT / Codex / 사용자 |
| B-003 | OPEN / P1 (SDK/빌드 해결) | CI 46002470824 SDK37.0 및 WFF5 Debug APK PASS. WFF5 실제 설치·런타임·전용 기능 미확인 | 실제 기기 및 P12 PoC 증거 | WO-08/35 |
| B-004 | OPEN / P1 | Watch7 크기/펌웨어/OS 및 최신 Samsung 기기 공식 매트릭스 미확인 | 공식 사양 확인, 실제 지원 대상별 기기/OS 기록 | WO-01 / 34 / 35 |
| B-005 | OPEN / P1 | WFF4 Reference, Variant, 숫자 전환, Gyro, 모션 트리거 및 최종 그래픽 품질 미검증 | P03~09의 실제 증거 | GPT-05/06 / Codex |
| B-006 | OPEN / P2 | 실제 KMA API 자격·할당량, Samsung Health 권한/파트너 및 독점 지표, Watch Face Push 조건 미확정 | 공식 조건 확인 및 실제 승인된 환경 시험 | GPT-08/09/11 |
| B-007 | OPEN / P1 | 정식 패키지 ID, 라이선스, 서명/배포 정책 미확정 | ADR 및 필요한 사용자 승인 | WO-29/38 |
| B-008 | OPEN / P2 | 전력/발열/실기기 소재 및 접근성 승인 미확보 | 비교 시험, 영상, 측정 및 사용자 승인 | WO-30~38 |
| B-009 | RESOLVED | CI 45997002132 SDK manager not found (exit 127) | CI 45997124733 SDK 설치·확인 PASS | 수정 544a7010 |

| B-010 | RESOLVED | tools/verify_wff.py의 성공 조건이 일반 VALID 포함 여부에 의존한다. 헤더 Validation도 매치되므로 명시적 성공을 검증하지 못할 위험. 실제 두 CI의 성공 로그는 버전별 PASSED를 확인했다. 오판 발생 자체는 미재현. | 공식 validator 결과 형식 확인, 성공·실패·불명확·버전 불일치 회귀 시험, 대상별 명시적 성공 검사 | GPT-01 |

B-001 해결 확인. 재발 시 관련 통합 작업의 GO를 중단한다. 독립 테스트·설계·도메인 작업은 RESUME_PROTOCOL의 선행 조건에 따라 진행 가능하다.

## 운영 점검 기록 (2026-11-27)
문서 기준 SHA 951593e4fbbac33f2c675ea5cbbf07edbe22353d, CI 45998609726 (completed/failure): Official WFF validation: success; Build debug APKs: success; Check APK contents: failure; Upload debug APKs: skipped. https://github.com/scarlel96-design/AURA-Ultra/actions/runs/45998609726. 운영 문서 변경 실행이며 제품 코드 변경 없음. B-001/B-010 해결 증거 없음.
신규 제품 차단점 없음. 기존 차단점은 해결되지 않았다. 매 턴 PRE-FLIGHT에서 최신 증거를 다시 확인한다.

## GPT-01 회차 01 수정 후보
B-001: CI 45998909046, job 140505251267에서 DEX build/merge 작업 및 APK FAIL 재확인. 정확한 이전 ZIP 항목은 미확인. Samsung 공식 WFF 가이드의 minify 활성화/resource shrink 비활성화 적용. 검사기는 모든 APK의 정확한 항목과 컴파일된 Manifest를 기록한다. 새 CI 검증 대기.
B-010: 명시적 파일/버전 PASSED 판정, 오류/종료 코드/중복 검사, 정상·실패 fixture 및 실제 잘못된 XML probe 추가. 새 CI 검증 대기. 두 차단점은 OPEN 유지.

- GPT-01 코드 SHA ef9f9c9bbb2020de835926a3bf0e4262b9c89d51, CI 45999371709: completed/success. 실제 최종 로그/Artifact 확인 전 B-001/B-010 OPEN 유지. STATUS의 단계별 결과 참조.

## GPT-01 회차 01 최종 증거
코드 ef9f9c9bbb2020de835926a3bf0e4262b9c89d51, CI 45999371709: 19 단위 시험 PASS, 공식 WFF 정상 3/3 및 잘못된 XML 명시적 실패 검출 3/3 PASS, 3 APK clean build/내용 검사 PASS, Artifact 15197113871 확보. B-010 해결, B-001 현재 빌드 실패 해소 및 과거 원인 증거만 보완 필요. REPORT-01 최종 결과 참조.

## GPT-01 회차 02 후보
B-001 과거 95e51cc 격리 재현 job 추가. 실행 결과 미확인. B-010 해결 유지. 메모리 및 debug 서명 검사 새 CI 대기. 실제 기기 접근 차단 B-002 유지.

- 회차 02 검증 코드 98a4f915577cf3175beeca19864a431061673e7b, CI 46000111754/46000111676. 메모리·서명·격리 재현 최종 증거 확인 전 B-001 OPEN. B-010 RESOLVED 유지. STATUS 참조.

## GPT-01 회차 02 최종 확인
B-001 RESOLVED: 과거 SHA 격리 재현 classes.dex 및 R 클래스 5개 확인, 현행 3개 APK 검사 PASS. B-010 RESOLVED 유지. 현행 메모리 2,371,712 bytes 활성/AOD, 3 Debug 서명 PASS. CI 46000111754/46000111676 SUCCESS. B-002/003/004/007 등 기존 실기기·WFF5·기기/배포 정책 차단점은 유지. 새 결함 없음.

## GPT-02 회차 01
B-003: 공식 WFF5 공개 및 Wear OS7/API37 확인, AGP9.1.1/Gradle9.3.1 전환 후보. 기존 SDK36 환경 유지. WFF5 schema-only 후보, SDK37 실제 빌드/설치 미확인. B-004: Watch7/8/9/Ultra2 공식 발표 해상도/출시 OS 확인. Ultra 2025 출고 OS 및 실제 설치 OS/기기 시험 미확정. B-007: ADR-007 제안, 정식 정책 승인 필요. B-002 유지. 새 CI 결과 미확인.

- 회차 01 CI 46001149417 in_progress/PENDING. B-003/004/007/002 유지. WFF5 스키마와 API37 toolchain·실기기 시험은 분리한다.

## GPT-02 회차 01 최종
CI 46001149417 SUCCESS, WFF5 스키마 정상 및 예상 실패 검출 PASS. B-003 OPEN: API37 toolchain/실제 WFF5 APK·설치 미확인. B-004 OPEN: 공식 주요 모델 사양 확인, 실제 OS/Ultra2025 출고 OS 미확정. B-007 OPEN: ADR-007 정식 정책 제안 상태. B-002 유지. 기존 B-001/B-010 해결 유지.

GPT-02 회차 02: B-003 API37 전환 후보 격리 검증 중. 스키마 PASS만으로 설치 지원을 주장하지 않는다. B-002/004/007 유지. B-001/010 해결 상태 유지; 회귀 검사 수행 예정.

## GPT-02 회차 02 최종
B-003: SDK 패키지 android-37.0 설치, 네 APK build/스키마/메모리/서명 PASS. 도구 전환 차단 해결. 실제 설치·기능 확인은 남음. B-002/004/007 유지. B-001/010 재발 없음. CI 46002470824, REPORT-02. 첫 CI 46002330942 실패도 보존.
