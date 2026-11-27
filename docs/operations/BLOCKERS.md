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

GPT-03 회차 01 후보 CI 46006560829 진행 중. 기존 차단점 유지, 신규 결함 확정 없음. 실제 flavor override 및 독립 생성 프로세스 시험 후속. REPORT-01 참조.

외부 작업 접수: GB-01은 독립 재실행·통합 전 검토 보완 필요. 비ASCII Windows Gradle 테스트 워커 ClassNotFoundException은 환경 제한 GB01-E1, 제품 차단 추가 아님. AG-01 원격 SHA 미확인; push 후 증거 확인. B-002/003/004/005/006/007/008 유지. GPT-03 후보 CI 성공, main 통합 및 재생성/override 시험 남음.

2026-11-28 OPS-05: GB01-D2/D3 수정 코드 및 JUnit 81건 증거 확인. 독립 CI 46056345699 진행. GB01-E1 비ASCII Windows 제한 유지. AG 원격 접근 해소; AG01-AUD-01/02/03의 증거 및 검사기 보완, 실제 Wear runtime NOT RUN. B-002/003/005 유지. 4분할 시계 자체가 아니라 가시 PartText 추가 layer 810000 bytes (공식 평가기 조건). B-001/010 해결 유지. GPT03/GB01 통합 CI 46056345651/46056345699 확인 후 판정.


## OPS-05 독립 CI 최종 및 공식 도구 갱신 후보
- 통합 코드 c6ae81217641dda75b7b3e3fbc0063fd11469c6c: Kotlin CI [46056345699](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46056345699), job 140699646163, SUCCESS. 로그 JDK17 Eclipse Temurin, BUILD SUCCESSFUL in 50s, DOMAIN_RESULT 81 PASS / 0 FAIL / 0 ERROR / 0 SKIP. Artifact [15226378043](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46056345699/artifacts/15226378043), 5180 bytes, digest sha256:a3fec194673e455f63b3a12103ea24c00b20d294ab6a227b6628644d47c5320f, expired=false. 메타데이터 확인, 재다운로드/재해시 미실시. GB-01 독립 CI PASS; main 통합은 아래 공통 게이트 실패로 보류.
- Bootstrap [46056345651](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46056345651), job 140699646086, FAILURE. 독립 프로세스 --write/--check/missing/stale/repair/byte equality PASS, host 68 PASS/0 FAIL, SDK PASS. 공식 validator 단계 'Validator download size or digest mismatch. Review the official release before updating the pin.' exit 1. 이후 schema/build/APK/memory/signature/Artifact SKIP. 실제 스키마 위반으로 판정하지 않는다.
- B-011 OPEN/P0: 공식 Google watchface 가변 release 태그에서 JAR 두 개 교체. 공식 [release](https://github.com/google/watchface/releases/tag/release) ID 460768397 published 2026-11-27T15:21:34Z, tag commit 18d3844de1729f0c5128f59cfa359b0e34b66612. [PR 118](https://github.com/google/watchface/pull/118)의 XML DOM parser 설정 통합 변경 파일 및 핵심 diff 확인. validator asset 800984124 SHA256 6ef308dbc306a9187b5b1f4997a662eb57e26ac3650cebbf2ab583cd38bb609e; memory asset 800984064 SHA256 1ec683365aee86627f0eb502b52fc71f71eff1872776edc5bc6ef7c7b37d28bc. 이전 공식 pin과 다름. 공식 release API 메타데이터를 확인했으며 독립 바이너리/소스 재현은 하지 않았다. 정확한 해시 검증을 유지한 새 pin 후보 0cec62250a2dc05cd02773f6969726867946fe4f를 integration/gpt03-gb01에만 반영. 기존 main과 에이전트 증거의 이전 pin은 보존. 도구 실행 버전, 출력, 정상/실패 schema 및 4 APK/메모리/서명 전체 성공 전 병합 금지.
- 신규 후보 CI: AURA Bootstrap 46056609237 in_progress/PENDING. 최종 원본 로그 미확인. Kotlin 소스는 c6ae812와 동일; 새 SHA에서 도메인 재실행 여부 구분. AG-01-R03은 현재 자기 브랜치의 고정 도구를 사용하며 새 도구 전환은 중앙 승인 이후. B-011 해결은 후보 전체 게이트 및 SHA 대조 후 판정. GPT-03 PARTIAL/GB-01 독립 CI PASS/AG-01 PARTIAL, 정식 WO 0/38, 출시 NO-GO.

B-011 RESOLVED(현재 도구 버전): CI 46056609237 공식 validator 및 evaluator 신규 pin, 4 APK 전체 PASS. 가변 release에 따른 재발 가능성은 남는다. 이전 실패 로그 유지. GB01-E1 및 AG01-AUD 항목 유지. 실제 Wear OS runtime 미실시.

GPT-03 회차 02: B-011 현재 pin 해결 유지, main GB01 독립 CI 81 PASS 재확인. 격리 flavor 후보 CI 46059190750 및 main CI 46059108841 진행/최종 확인 대기. 향후 실제 제품 override 도입 전 현재 common-only fixture를 일반화한다. B-002/003/004/005/006/007/008 및 GB01-E1 유지. AG-01 소유권 유지, PR #2 미병합.

GPT-03 회차 03: CI 46059190750 SUCCESS, 격리 source precedence 및 stale APK 검출·복원 PASS. B-011 해결 유지. 기존 실기기/외부 데이터/정식 배포 차단 유지. 제품 override 확장 전 fixture 일반화.

GPT-04 회차 01: 정적 원형 기하 4화면 PASS; 후보 전체 CI 46059943214 최종 확인 대기. 신규 확정 제품 결함 없음. 실제 글리프/렌더링/해상도 검증은 B-002/004/008 유지. GB-02/AG-01 변경 없음.

GPT-04 회차 01 전체 CI 성공; 기하 후보 통합 승인. 기존 실기기·글리프·공급원 차단 유지.

GPT-04 회차 02: 124/124 합성 호스트 글꼴 조합 fit; 기기 font/실제 표시 및 locale·native HR/날씨 runtime 미실시, 기존 B-002/004/006/008 유지. 후보 전체 CI 46060479503 최종 확인 대기. AG/GB 소유권 및 기존 main 제품 유지.

OPS-06: GPT04-D1 OPEN/P0 후보 Group name 필수 속성 누락(46060479503), 수정 374dec9 재검증 CI 46062170635. AG01-AUD-04 OPEN/P1 runtime package/display 오판 4종 분리 함수 재현. AG 원격 환경 0 Wear AVD, 실제 실행 NOT RUN. AG 기존 pin CI 실패; main pin 해결 유지. GB-01 통합 완료, GB-02 READY.

GPT04-D1 RESOLVED: CI 46062170635 SUCCESS, 100 host and 12 APK PASS. Runtime/locale/glyph/AOD pixel verification still pending. No product or external owner edits.

GPT04-D2 OPEN/P0(후보 검증): 초기 프리뷰 46064026867 실패, percent regex 수정 82fef7c, CI 46064080195 재검증 중. 실제 기기/AMPM/글꼴 검증 미실시 유지. GPT04-D1 해결 유지. 외부 소유권 및 기존 product 변경 없음.

GPT04-D2 RESOLVED: CI 46064080195 SUCCESS, 120 host/12 APK and 40 synthetic preview outputs. Runtime blockers unchanged. Official IS_24_HOUR_MODE WFF1 identified, marker implementation pending.
