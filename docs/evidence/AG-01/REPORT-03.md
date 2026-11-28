# 작업 보고서 — AG-01 / 회차 03

- **상태**: `PARTIAL` (정적 스키마 60건·검사기 실패 탐지·실시간 SDK/AVD 환경 조사·런타임 안전 절차 및 회귀 22건 PASS; 실제 Wear OS 에뮬레이터·실기기 런타임 렌더링은 사용자 승인 전 시스템 이미지 미설치로 `NOT RUN`)
- **일자 / 작업자 / 검토자**: `2026-11-28` / `Antigravity` / 자기 재검토 (`G5`, 독립 외부 검토 아님)
- **기준 브랜치 / 기준 HEAD**: `agent/antigravity/AG-01` (PR #2 기준 SHA: `74f04aab7abb4e846e3ca5fd798721bd732a1146`)
- **PRE-FLIGHT**:
  - 확인한 최신 `origin/main` SHA: `a9664b2e3eb72f99a06c2d973259cb80d7cc4337` (`docs: preserve Kotlin CI success and official tool digest change blocker [skip ci]`)
  - 실제 읽은 필수 문서: `origin/main`의 `docs/operations/agent-orders/AG-01-R03.md`, `docs/STATUS.md`, `docs/operations/BLOCKERS.md`, `docs/operations/WORK_LOG.md`, `docs/operations/VERIFICATION_PROTOCOL.md`, `docs/operations/TASK_REPORT_TEMPLATE.md`, `docs/evidence/OPS-05/REPORT.md` 및 로컬 `tools/verify_wff.py`, `compatibility/profiles.json`
  - 활성 작업 및 차단점: `AG-01-R03` (`AG01-AUD-01/02/03` 수정 및 안전한 Wear OS 런타임 절차 구축); `B-002`/`B-003` 런타임/`B-004`/`B-007`/`B-011` OPEN. `B-011`(공식 Google watchface JAR pin 교체)에 대해 중앙 `STATUS.md` 지침대로 본 브랜치는 기존 고정 도구(`wff-validator.jar` SHA-256 `0e2204137fca618264e82f9a053c6c9ec6d4fad08d2b56aa8a57d75c0508a804`, `memory-footprint.jar` SHA-256 `503c5f7bc9209ec4d4d4974f973cf66ad6fbb435e8422c310aac5b820f1f991a`)를 유지하며 중앙 승인 이후 전환한다.
  - PRE-FLIGHT 판정: `PASS`
- **검증 대상 코드 기준**: `agent/antigravity/AG-01` 회차 03 변경분 (기준 부모 `74f04aab7abb4e846e3ca5fd798721bd732a1146` 위 작업; 기존 `REPORT.md`, `REPORT-02.md`, `docs/evidence/AG-01/logs/*` 보존)
- **관련 작업지시서 / 감사 ID**: `docs/operations/agent-orders/AG-01-R03.md`, `AG01-AUD-01`, `AG01-AUD-02`, `AG01-AUD-03`
- **작업 목표, 포함/제외 범위**:
  - **포함**: (1) `sdkmanager --list`, `avdmanager list device`, `avdmanager list avd`, `emulator -list-avds`, `adb devices -l`의 실제 실행·원문 보존·파싱 및 하드코딩 추정 후보 분리(`AG01-AUD-01`), (2) `require_rejection`의 정확한 대상 XML·WFF 버전 명시적 `FAILED` + `[Line:Column] SEVERE` 검증 강화 및 `duration`/`Reference` 단일 결함 Negative 픽스처 2종 분리(`AG01-AUD-02`), (3) `REPORT-02.md` 날짜·경로·여유 공간·G6 정의·AOD 평가기 범위 정정(`AG01-AUD-03`), (4) Wear OS AVD 전용 안전한 설치·워치 페이스 선택 확인·AOD 상태 확인·전환 영상 녹화 절차(`wear_emulator_runtime.py`) 구현 및 단위 회귀 시험.
  - **제외**: 사용자 명시 승인 없는 신규 SDK 시스템 이미지 다운로드 및 AVD 생성, 기존 폰 AVD(`Medium_Phone_API_36.1`) 및 실제 사용자 워치 변경, 제품 소스(`apps/**`, `tools/**`, `compatibility/**`), 공통 Gradle/CI, 중앙 운영 문서 직접 수정, `main` 직접 병합.
- **변경 파일 소유권 / 변경 영향**: 허용 경로 `tests/compatibility/ag-01/**`, `docs/evidence/AG-01/**` 내부 파일만 추가/수정. 기존 제품 코드·빌드·CI 및 회차 01/02 보존 증거(`REPORT.md`, `REPORT-02.md`, `logs/*`) 변경 `0`건.
- **가정 / 위험 / 승인 필요 사항**:
  - 실제 Wear OS 에뮬레이터 렌더링·AOD 전환 영상 검증을 수행하려면 사용자 명시 승인 후 `system-images;android-36;android-wear-signed;x86_64` (WFF 4, 추정 약 `3.0 GiB`) 및 `system-images;android-37.0;android-wear-signed;x86_64` (WFF 5, 추정 약 `3.2 GiB`) 다운로드 및 전용 Wear AVD 생성이 필요하다.
- **성공 기준 / 롤백 방법**:
  - 성공 기준: `AG01-AUD-01/02/03` 전 항목 코드·테스트·원본 로그로 입증, 22개 단위/회귀 테스트(68 validator subtests) 및 60건 엄격 스키마 매트릭스 PASS, 기존 6 APK/4 ablation 원본 증거 무손상 보존, PR #2 갱신.
  - 롤백 방법: `agent/antigravity/AG-01`에서 회차 03 커밋을 `git revert`하여 `74f04aab7abb4e846e3ca5fd798721bd732a1146` 상태로 즉시 복구 가능.

---

## 1. 구현 및 결정

| 파일·모듈 | 변경 및 이유 | 관련 요구사항 / 감사 ID | 확인할 영향 |
|---|---|---|---|
| `tests/compatibility/ag-01/run_ag01_verification.py` | (1) 하드코딩 목록을 `ESTIMATED_WEAR_IMAGE_CANDIDATES` 추정 후보로 분리하고 `sdkmanager --list`, `avdmanager list device`, `avdmanager list avd`, `emulator -list-avds`, `adb devices -l` 실시간 실행·파싱·원문 로그 보존 및 `READY`/`NOT RUN`/`UNKNOWN` 엄격 판정 구현.<br>(2) `require_rejection`에 `returncode == 0`, 공식 배너, `0 PASSED`, 정확한 대상 XML 경로·WFF 버전의 명시적 `FAILED` 1건, `[Line:Column] SEVERE` 진단 포함 조건 강제.<br>(3) 분리된 2종 Negative 픽스처(`SEPARATED_NEGATIVE_SPECS`)를 포함해 총 60건 스키마 매트릭스 로그(`schema-matrix-60-r03.log`) 지원. | `AG01-AUD-01`, `AG01-AUD-02` | `test_ag01_suite.py` 및 `docs/evidence/AG-01/logs-r03/*` |
| `tests/compatibility/ag-01/fixtures/negative/neg_wff4_variant_duration_out_of_range.xml` | `Variant duration="1.35"` 범위 위반(`maxInclusive '1.0E0'`)만 단독으로 포함하는 단일 결함 픽스처 분리. | `AG01-AUD-02` | WFF 2·3·4·5 공식 validator 4건 추가 검증 |
| `tests/compatibility/ag-01/fixtures/negative/neg_wff4_reference_invalid_parent.xml` | `<DigitalClock>` 직속 자식 `<Reference>` 허용 부모 위반만 단독으로 포함하는 단일 결함 픽스처 분리. | `AG01-AUD-02` | WFF 2·3·4·5 공식 validator 4건 추가 검증 |
| `tests/compatibility/ag-01/wear_emulator_runtime.py` | 실제 Wear OS AVD 전용 안전한 설치·워치 페이스 선택 확인(`dumpsys wallpaper`)·Active/AOD 상태 확인(`dumpsys power`/`display`)·전환 영상 녹화(`screenrecord`)·스크린샷 캡처 절차 및 하드 안전장치(물리 기기·폰 AVD·`--force` 차단, `-s <emulator-serial>` 강제, `ro.build.characteristics` `watch` 및 `minSdk` 검증) 신규 구현. | `AG-01-R03` §4 | 승인 후 Wear OS 6/7 에뮬레이터 런타임 시험 진입점 |
| `tests/compatibility/ag-01/test_ag01_suite.py` | 기존 12개 테스트(60 validator subtests)를 유지하고, 강화된 `require_rejection` 실패 탐지 5건, 실시간 SDK/AVD/ADB 파싱·도구 부재/오류/빈 출력(`UNKNOWN`)·폰 AVD/물리 기기 분리(`NOT RUN`)·런타임 안전장치 4건, 분리된 Negative 2종(8 validator subtests) 및 격리 검증 1건을 추가해 총 **22개 테스트(68 validator subtests)**로 확장. | `AG01-AUD-01`, `AG01-AUD-02`, `AG-01-R03` §4 | 전체 검사기 신뢰성 회귀 검증 |
| `tests/compatibility/ag-01/README.md` | 회차 03 변경 사항 및 새 로그 경로(`docs/evidence/AG-01/logs-r03`), `wear_emulator_runtime.py --plan-only` 실행 방법 반영. | `AG-01-R03` | 후속 에이전트 재현성 |
| `docs/evidence/AG-01/logs-r03/*` | `sdkmanager-list.raw.log`, `avdmanager-list-device.raw.log`, `avdmanager-list-avd.raw.log`, `emulator-readiness-r03.log`, `schema-matrix-60-r03.log` 5개 원본 로그 신규 보존 (기존 `logs/*` 무변경). | `AG01-AUD-01`, `AG01-AUD-02`, `AG01-AUD-03` | 감사 대조용 원본 증거 |
| `docs/evidence/AG-01/REPORT-03.md` | 회차 03 상세 검증, `REPORT-02.md` 정정표(Errata), 실시간 환경 조사 대조, 안전한 런타임 절차 및 G0~G7 평가 기록. | `AG01-AUD-03`, `AG-01-R03` §5 | PR #2 갱신 및 중앙 감사 대상 |

### 결정 및 기각 사유

- **도구 실행 오류(`returncode != 0`)를 예상 스키마 실패로 처리하지 않음**: 실제 `wff-validator.jar` v1.7.0은 정상 기동하여 스키마 실패를 보고할 때 **항상 `Exit Code: 0`**을 반환하며 `INFO: ❌  FAILED : <path> is NOT valid against watch face format version #<N>`과 `SEVERE: [Line X:Column Y]: ...`를 출력한다(`docs/evidence/AG-01/logs/schema-matrix-52.log` 28건 실패 전원 `Exit Code: 0` 확인). 따라서 `returncode != 0`은 JVM crash, JAR 누락, 인자 오류 등의 도구 실행 오류이므로 `require_rejection`에서 즉시 `ValueError`를 발생시키도록 결정했다.
- **추측된 브로드캐스트 워치 페이스 선택 컴포넌트명 제거 (G5 자기 재검토 `AG01-R03-REV-01`)**: 초안에서 `wear_emulator_runtime.py` 3단계에 비검증 `watchfacestudio/.../EditorSession` 브로드캐스트 명령을 포함했으나, WFF 리소스 전용 패키지의 실제 런타임 선택 메커니즘과 다를 위험이 있어 제거하고 공식 Wear OS Watch Face Picker 선택 + `adb -s <serial> shell dumpsys wallpaper` 바인딩 확인으로 정정했다.

---

## 2. 회차 02 정정표 (`AG01-AUD-03` — 기존 `REPORT-02.md` 및 `logs/*` 보존, 추가 기록 정정)

> 기존 `docs/evidence/AG-01/REPORT.md`, `docs/evidence/AG-01/REPORT-02.md`, `docs/evidence/AG-01/logs/*`는 원형 그대로 보존하며, 총괄 감사(`OPS-05`)에서 확인된 불일치 항목을 아래와 같이 정정 기록한다.

| 정정 ID | 위치 (`REPORT-02.md`) | 기존 기재 내용 (오류) | 원본 증거 기반 정정 내용 | 근거 |
|---|---|---|---|---|
| `ERR-01` | 헤더 및 §10 (`WORK_LOG` 제안) | 작업 일시 `2026-04-20` | 회차 02 실제 작업·커밋·로그 생성 시점은 **`2026-11-27`** (회차 03은 **`2026-11-28`**) | Git 커밋 타임스탬프 및 `docs/STATUS.md` 기준일(`2026-11-27`/`2026-11-28`) |
| `ERR-02` | §3 (컴파일된 Manifest 검사 기준) | `compatibility/version-profiles.json` | 실제 저장소 파일 경로는 **`compatibility/profiles.json`** | 로컬 `compatibility/` 디렉터리 및 `tools/profile_contract.py` 확인 |
| `ERR-03` | §1, §7.1, §7.2, §10 | 가용 디스크 여유 공간 `93.88 GiB` | 회차 02 커밋된 `docs/evidence/AG-01/logs/environment-and-emulator.log` 13행의 실제 기록값은 **`93.67 GiB`** (`REPORT-02.md` 작성 직후 `--mode emulator` 재실행 시 변동된 값을 본문에 동기화하지 못함). 회차 03 최신 실측값은 `docs/evidence/AG-01/logs-r03/emulator-readiness-r03.log` 13행 기준 **`98.98 GiB`** | `logs/environment-and-emulator.log` L13, `logs-r03/emulator-readiness-r03.log` L13 |
| `ERR-04` | §9.2 (`G6` 게이트 정의 및 판정) | `G6 (런타임/에뮬레이터 검증): NOT RUN (정직한 기록으로 게이트 조건 충족)` | `docs/operations/VERIFICATION_PROTOCOL.md` 기준 **G6는 "증거 및 판정 감사"**(최종 SHA, 대상 파일/명령/종료 상태/로그 일치 및 요구사항 충족 감사)이다. 런타임/에뮬레이터 시험 미실시 및 환경 조사 결함(`AG01-AUD-01`)이 존재한 상태에서 G6를 충족으로 처리한 것은 오판이며, **G4(기술 분야별 런타임) = `NOT RUN`**, **회차 02 시점 G6 = `FAIL`/`PARTIAL`**, **회차 03 최종 작업 판정 = `PARTIAL`**이 정확하다. | `origin/main:docs/operations/VERIFICATION_PROTOCOL.md` G4, G6 |
| `ERR-05` | §6 (AOD 메모리 `+810,000` bytes 결론 적용 범위) | 바이트코드 및 통제 비교 결과가 실제 AOD 메모리 특성을 일반화하는 것처럼 읽힐 여지 존재 | `+810,000` bytes (`450 × 450 × 4`) 결론은 **공식 정적 자산 추정 도구(`memory-footprint.jar` v1.5.1, `--apply-v1-offload-limitations`)의 평가 모델 조건 범위 내**에서만 성립한다. 실제 Wear OS 기기의 런타임 RAM, GPU 텍스처, 전력 소모, 렌더링 프레임은 **`NOT RUN`**이다. 또한 `--verbose` 로그의 `Using system default font for unknown font family SYNC_TO_DEVICE` → `Counting resource Roboto; 2371712 bytes` 경고는 평가 도구가 `SYNC_TO_DEVICE`를 시스템 기본 폰트(`Roboto`) 크기로 대체 추정한 결과이며, 실제 기기에서의 폰트 렌더링 품질·메트릭을 보장하지 않는다. | `docs/evidence/AG-01/logs/aod-memory-ablation.log` L28~37, `OPS-05/REPORT.md` |

---

## 3. 실시간 SDK / AVD / ADB 환경 조사 결과 및 추정 후보 대조 (`AG01-AUD-01`)

> 원본 로그 (실제 실행 stdout/stderr/종료 코드 원문):
> - `docs/evidence/AG-01/logs-r03/sdkmanager-list.raw.log` (`115,512 bytes`, SHA-256: `25932ec596d117fc756742f4b8c0667e7ab373374009d46954b2930b0fd6b078`)
> - `docs/evidence/AG-01/logs-r03/avdmanager-list-device.raw.log` (`7,789 bytes`, SHA-256: `a8684cf9e8e47cf68dfa1429ff8ee80e6170cecd59f600ce0f76d44fcce29d1f`)
> - `docs/evidence/AG-01/logs-r03/avdmanager-list-avd.raw.log` (`695 bytes`, SHA-256: `578ccd3076fecccc796256301ec4b4f0f5a345ba1a1202dac71366a5eeb298ec`)
> - `docs/evidence/AG-01/logs-r03/emulator-readiness-r03.log` (`6,408 bytes`, SHA-256: `84895a6db8851b56a91853e0e0f3cd47115cb5d093eeacc7eaf3abe7a4c4f7b2`)

### 3.1 실시간 도구 실행 상태 (`2026-11-28` 무다운로드 읽기 전용 조회)

| 도구 | 실행 명령 | 종료 코드 | 상태 | 파싱된 실제 관측 요약 |
|---|---|---|---|---|
| `sdkmanager` | `sdkmanager.bat --list` | `0` | `OK` | 설치된 Wear 이미지 **`0`개** (일반 폰 이미지 `android-36.1;google_apis_playstore;x86_64`만 설치됨); 원격 카탈로그 Wear 이미지 **20개** 파싱 |
| `avdmanager` (devices) | `avdmanager.bat list device` | `0` | `OK` | 공식 Wear OS 디바이스 프로필 **4개** 관측 (`wearos_large_round` id 59, `wearos_rect` id 60, `wearos_small_round` id 61, `wearos_square` id 62, 모두 `OEM=Google`, `Tag=android-wear`) |
| `avdmanager` (avds) | `avdmanager.bat list avd` | `0` | `OK` | **Wear OS AVD `0`개**, 일반 폰 AVD `1`개 (`Medium_Phone_API_36.1`, `device=medium_phone (Generic)`, `Tag/ABI=google_apis_playstore/x86_64`)로 분리 판정 |
| `emulator` | `emulator.exe -list-avds` | `0` | `OK` | `['Medium_Phone_API_36.1']` |
| `adb` | `adb.exe devices -l` | `0` | `OK` | 실행 중인 검증된 Wear 에뮬레이터 **`0`대**, 비-Wear 에뮬레이터 `0`대, 물리 기기 `0`대 |
| **디스크 여유 공간** | `shutil.disk_usage(sdk)` | - | - | **`98.98 GiB`** (`emulator-readiness-r03.log` L13 실측 일치) |
| **최종 Wear 에뮬레이터 준비 판정** | `determine_emulator_readiness` | - | **`NOT RUN`** | 설치된 Wear 이미지 `0`개, Wear OS AVD `0`개 (승인 전 다운로드·AVD 생성 금지) |

### 3.2 추정 후보(`ESTIMATED_WEAR_IMAGE_CANDIDATES`) vs 실제 `sdkmanager --list` 관측 대조표

> 용량 수치는 `sdkmanager --list`가 제공하지 않으므로 **추정치(`est.`)**임을 명시하고, 패키지 ID·리비전·설명·설치 여부는 **실제 `sdkmanager-list.raw.log` 파싱 결과**와 대조하였다.

| 추정 후보 패키지 ID (`x86_64`) | 목표 WFF | 우선순위 (승인 시 단계) | 추정 디스크 용량 (후보 추정치) | 실제 설치 여부 (관측) | 실제 `sdkmanager --list` 카탈로그 존재 여부 (관측) | 실제 관측 Revision | 실제 관측 Description (`sdkmanager-list.raw.log`) |
|---|---|---|---|---|---|---|---|
| `system-images;android-36;android-wear-signed;x86_64` | WFF 4 | **Stage 1 (P0)** | `~3.0 GiB (est.)` | `False` | **`True`** | `1` | `Wear OS 6.0 Intel x86_64 Atom System Image (signed)` |
| `system-images;android-37.0;android-wear-signed;x86_64` | WFF 5 | **Stage 2 (P0)** | `~3.2 GiB (est.)` | `False` | **`True`** | `1` | `Wear OS 7.0 Intel x86_64 Atom System Image (signed)` |
| `system-images;android-36.1;android-wear-signed;x86_64` | WFF 4 | Optional (P2) | `~3.0 GiB (est.)` | `False` | **`True`** | `1` | `Wear OS 6.1 Intel x86_64 Atom System Image (signed)` |
| `system-images;android-35-ext15;android-wear;x86_64` | WFF 3 | Stage 3 (P1 확장) | `~2.8 GiB (est.)` | `False` | **`True`** | `1` | `Wear OS 5.1 Intel x86_64 Atom System Image` |
| `system-images;android-34;android-wear;x86_64` | WFF 2 | Stage 4 (P1 확장) | `~2.6 GiB (est.)` | `False` | **`True`** | `1` | `Wear OS 5 Intel x86_64 Atom System Image` |

---

## 4. 안전한 실제 Wear OS 에뮬레이터 런타임 검증 절차 (`wear_emulator_runtime.py`)

신규 SDK 다운로드 및 AVD 생성은 **사용자 명시 승인 이후에만** 수행하며, 승인 시 **WFF 4 → WFF 5부터 1개씩 순차 시험**하고 필요 시 WFF 3/2로 확장한다.

### 4.1 코드 수준 안전장치 (`test_ag01_suite.py` 단위 회귀로 검증 완료)

1. **기존 폰 AVD 및 물리 기기 차단**:
   - `validate_emulator_serial(serial)`: `^emulator-\d+$` 패턴이 아닌 모든 시리얼(물리 워치/폰 시리얼, 빈 문자열)을 `UnsafeTargetError`로 하드 차단한다.
   - `validate_wear_avd_record(avd)`: `Tag/ABI` 또는 `Device`에 `android-wear`/`wearos`가 없는 일반 폰 AVD(`Medium_Phone_API_36.1` 등)를 하드 차단한다.
   - `validate_wear_device_properties(characteristics, sdk_int, min_sdk)`: 실행 중인 에뮬레이터의 `ro.build.characteristics`에 `watch`가 없거나 `ro.build.version.sdk < min_sdk`이면 즉시 중단한다.
2. **기존 AVD 덮어쓰기 금지 (`--force` 제거)**:
   - `build_safe_setup_commands`는 모든 `avdmanager create avd` 명령에서 `--force` 플래그를 배제한다.
3. **명시적 `-s <emulator-serial>` 강제 및 실제 상태 확인**:
   - 모든 `adb` 명령은 반드시 `adb -s <emulator-serial>`을 포함한다.
   - 단순 `adb install`만으로 캡처하지 않고, `dumpsys wallpaper`에서 대상 패키지(`io.github.scarlel96.aura.watchface.wff4` 등)가 **실제 활성 워치 페이스로 선택되었음**을 검증한 뒤에만 Active/AOD 캡처로 진행한다.
   - Active 캡처 전 `dumpsys power`의 `mWakefulness=Awake` / `Display Power: state=ON`을 확인하고, AOD 캡처 전 `mWakefulness=Dozing` 또는 `Display Power: state=DOZE`/`DOZE_SUSPEND` 진입을 실제로 확인한다.

### 4.2 사용자 명시 승인 후 1단계(WFF 4) 실행 절차 예시 (`--force` 없음)

```powershell
# [승인 후 1단계: WFF 4 전용 Wear OS 6.0 이미지 및 AVD 준비]
& "$env:LOCALAPPDATA\Android\Sdk\cmdline-tools\latest\bin\sdkmanager.bat" "system-images;android-36;android-wear-signed;x86_64"
& "$env:LOCALAPPDATA\Android\Sdk\cmdline-tools\latest\bin\avdmanager.bat" create avd -n aura_wear36_round -k "system-images;android-36;android-wear-signed;x86_64" -d wearos_large_round
& "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -avd aura_wear36_round -no-snapshot -no-boot-anim

# [부팅 후 실제 Wear 에뮬레이터 시리얼(예: emulator-5554) 확인 및 단계별 실행]
adb devices -l
python tests/compatibility/ag-01/wear_emulator_runtime.py --plan-only --serial emulator-5554 --apk <isolated-wff4.apk> --package-id io.github.scarlel96.aura.watchface.wff4 --wff-version 4 --out-dir docs/evidence/AG-01/runtime-wff4
# Watch Face Picker에서 해당 WFF 4 패키지 선택 후 실행:
python tests/compatibility/ag-01/wear_emulator_runtime.py --serial emulator-5554 --apk <isolated-wff4.apk> --package-id io.github.scarlel96.aura.watchface.wff4 --wff-version 4 --out-dir docs/evidence/AG-01/runtime-wff4
```

---

## 5. 요구사항 및 검증 추적표

| 요구사항 / 감사 ID | 구현 파일·경로 | 시험 ID | 예상 결과 | 실제 결과 | 원본 증거 경로·SHA-256 | 판정 |
|---|---|---|---|---|---|---|
| `AG01-AUD-01`: 실시간 `sdkmanager`/`avdmanager` 조회, 후보 분리, 오류→`UNKNOWN`, 폰/물리 분리→`NOT RUN` | `tests/compatibility/ag-01/run_ag01_verification.py` | `T-R03-01`, `T-R03-02` | 실제 stdout/stderr/rc 원문 보존; 도구 누락/오류/빈 출력=`UNKNOWN`; 폰 AVD·물리 기기=`NOT RUN`; Wear 이미지 단독=`NOT RUN` | 단위 회귀 3건 PASS + 실제 조회 `rc=0`, Wear 이미지 0, Wear AVD 0, 폰 AVD 1 (`Medium_Phone_API_36.1`), `NOT RUN` | `docs/evidence/AG-01/logs-r03/emulator-readiness-r03.log` (`84895a6d...`), `sdkmanager-list.raw.log` (`25932ec5...`), `avdmanager-list-device.raw.log` (`a8684cf9...`), `avdmanager-list-avd.raw.log` (`578ccd30...`) | **PASS** |
| `AG01-AUD-02`: 대상 파일/버전 명시적 `FAILED` + `[Line:Column] SEVERE`, 도구 오류 거부, duration/Reference 분리 | `run_ag01_verification.py`, `fixtures/negative/neg_wff4_variant_duration_out_of_range.xml`, `fixtures/negative/neg_wff4_reference_invalid_parent.xml` | `T-R03-03`, `T-R03-04`, `T-R03-05` | `rc!=0`/배너 누락/다른 경로·버전/SEVERE 외 문자열 모두 `ValueError`; 기존 52건(60 subtests) + 분리 8건 = 60건(68 subtests) PASS | 단위 실패 탐지 5건 PASS; 분리 2종 격리 검증 PASS; 60건 엄격 스키마 매트릭스 및 68 validator subtests 전원 PASS (`CASE 55~56`: `cvc-maxInclusive-valid` `1.35`, `CASE 59~60`: `Invalid content ... 'Reference'`) | `docs/evidence/AG-01/logs-r03/schema-matrix-60-r03.log` (`d3bc08f4...`), `neg_wff4_variant_duration_out_of_range.xml` (`bbe08715...`), `neg_wff4_reference_invalid_parent.xml` (`320ae29c...`) | **PASS** |
| `AG01-AUD-03`: 날짜·경로·수치·G6·ablation 범위 및 font fallback 정정, 이전 증거 보존 | `docs/evidence/AG-01/REPORT-03.md` (§2) | `T-R03-06` | `REPORT.md`, `REPORT-02.md`, `logs/*` 무변경 보존; 5개 정정 항목 원본 대조 기록 | `git diff`에서 기존 `REPORT.md`, `REPORT-02.md`, `logs/*` 변경 `0`건; `ERR-01`~`ERR-05` 기록 완료 | `docs/evidence/AG-01/REPORT-03.md` §2 | **PASS** |
| `AG-01-R03` §4: Wear AVD 전용 안전 설치·선택·AOD·영상 절차 (`--force` 금지, `-s` 강제) | `tests/compatibility/ag-01/wear_emulator_runtime.py` | `T-R03-07`, `T-R03-08` | 물리 기기·폰 AVD·`watch` 누락·`minSdk` 미달 차단, `--force` 미포함, `-s` 강제, Awake/Doze·wallpaper 선택 파싱 PASS | 단위 안전장치 시험 PASS + `--plan-only` dry-run 출력 검증 PASS (실제 에뮬레이터 실행은 승인 대기 `NOT RUN`) | `tests/compatibility/ag-01/wear_emulator_runtime.py` (`90f463c4...`) | **PASS (절차/안전장치)** / **NOT RUN (실행)** |
| `AG-01-R03` §5: 기존 6 APK / 4 ablation 증거 유지 및 저장소 기존 회귀 PASS | `docs/evidence/AG-01/logs/{isolated-apk-verification.log,aod-memory-ablation.log}` | `T-R03-09`, `T-R03-10` | 기존 6 APK·4 ablation 로그 보존; 기존 `tests/unit` 40건 및 `tools/check_foundation.py` PASS | 기존 로그 무변경 보존; `tests/unit` 40/40 PASS; `check_foundation.py` PASS | `docs/evidence/AG-01/logs/isolated-apk-verification.log`, `docs/evidence/AG-01/logs/aod-memory-ablation.log` | **PASS** |

---

## 6. 검증 결과 상세

| 시험 ID | 필수/선택 | 종류 | 명령·대상 | 기대 결과 | 실제 결과 | 판정 | 원본 로그 |
|---|---|---|---|---|---|---|---|
| `T-R03-01` | 필수 | 단위/회귀 | `python -m unittest discover -s tests/compatibility/ag-01 -p "test_*.py" -v` (22 tests, 68 validator subtests) | 22 tests, 0 failures, 0 errors | `Ran 22 tests in 92.608s -> OK` (G5 수정 후 재실행 포함) | **PASS** | 콘솔 출력 및 `logs-r03/schema-matrix-60-r03.log` |
| `T-R03-02` | 필수 | 실시간 환경 조사 (무다운로드) | `python tests/compatibility/ag-01/run_ag01_verification.py --mode emulator --logs-dir docs/evidence/AG-01/logs-r03` | `sdkmanager`/`avdmanager`/`emulator`/`adb` 모두 `rc=0`, 원문 로그 4종 생성, `NOT RUN` 판정 | `status=NOT RUN`, Wear 이미지 `0`, Wear AVD `0`, 폰 AVD `['Medium_Phone_API_36.1']`, 여유 공간 `98.98 GiB` | **PASS** (환경 조사) / **NOT RUN** (에뮬레이터 런타임) | `docs/evidence/AG-01/logs-r03/{sdkmanager-list.raw.log,avdmanager-list-device.raw.log,avdmanager-list-avd.raw.log,emulator-readiness-r03.log}` |
| `T-R03-03` | 필수 | 공식 스키마 매트릭스 (60건) | `python tests/compatibility/ag-01/run_ag01_verification.py --mode schema --logs-dir docs/evidence/AG-01/logs-r03` | 60/60 엄격 판정 PASS (24 VALID + 36 명시적 `FAILED` + `[Line:Column] SEVERE`) | `60/60 PASS` (`CASE 01/60`~`CASE 60/60`, 분리 2종 `CASE 53~60` 포함) | **PASS** | `docs/evidence/AG-01/logs-r03/schema-matrix-60-r03.log` |
| `T-R03-04` | 필수 | 런타임 절차 dry-run | `python tests/compatibility/ag-01/wear_emulator_runtime.py --plan-only --serial emulator-5554 ...` | 명시적 `-s emulator-5554`, `--force` 부재, Watch Face Picker + `dumpsys wallpaper` + Awake/Doze + `screenrecord` JSON 출력 | 기대 JSON 정상 출력, `exit 0` | **PASS** | `tests/compatibility/ag-01/wear_emulator_runtime.py` |
| `T-R03-05` | 필수 | 저장소 기존 회귀 | `python -m unittest discover -s tests/unit -p "test_*.py"` & `python tools/check_foundation.py` | 40 tests OK & foundation PASS | `Ran 40 tests in 0.038s -> OK`, `check_foundation.py` PASS | **PASS** | 콘솔 출력 |
| `T-R03-06` | 조건부 (승인 후) | Wear OS 에뮬레이터 런타임 | 실제 Wear OS 6/7 AVD 설치·선택·AOD 전환 영상 캡처 | 승인된 Wear AVD에서 Active/AOD 렌더링 및 전환 확인 | 사용자 승인 전 시스템 이미지 미설치로 미실행 | **NOT RUN** | `docs/evidence/AG-01/logs-r03/emulator-readiness-r03.log` |
| `T-R03-07` | 조건부 | 실기기 워치 설치/성능/배터리 | Galaxy Watch 실기기 시험 | 별도 승인 전 실기기 변경 금지 | 미실행 | **NOT RUN** | 규정상 제외 |

- **환경 및 도구 버전**: Windows 11 Build 26300 (`AMD64`), Python `3.14.7`, OpenJDK `21.0.5+11-LTS`, Android SDK Platform-Tools `36.0.2`, Emulator `36.4.9`, Build-Tools `36.0.0`/`36.1.0`, `wff-validator.jar` v1.7.0 (SHA-256 `0e2204137fca618264e82f9a053c6c9ec6d4fad08d2b56aa8a57d75c0508a804`), `memory-footprint.jar` v1.5.1 (SHA-256 `503c5f7bc9209ec4d4d4974f973cf66ad6fbb435e8422c310aac5b820f1f991a`).
- **총 시험 집계 (회차 03 실행 기준)**:
  - 단위/회귀 테스트: `62`건 실행 (`AG-01` 22건[68 validator subtests 포함] + `tests/unit` 40건) → **`62 PASS / 0 FAIL / 0 SKIP`**
  - 공식 스키마 매트릭스 실행: `60`건 → **`60 PASS / 0 FAIL`**
  - 격리 6 APK + 4 Ablation APK 빌드 증거: 회차 02 원본 로그 보존(`docs/evidence/AG-01/logs/isolated-apk-verification.log`, `docs/evidence/AG-01/logs/aod-memory-ablation.log`, XML/APK 소스 변경 없음)
  - Wear OS 에뮬레이터 런타임 및 실기기 시험: **`NOT RUN`** (승인 전 Wear 시스템 이미지 다운로드 금지 규정 준수)

---

## 7. 구현 후 검토 (G5 — 자기 재검토)

- **검토 유형**: 자기 재검토 (동일 모델·에이전트 수행; 독립 외부 승인 아님)
- **검토 대상**: 회차 03 변경 diff (`run_ag01_verification.py`, `wear_emulator_runtime.py`, `test_ag01_suite.py`, 분리 Negative 픽스처 2종, `logs-r03/*`)

| 결함 ID | 심각도 | 위치·재현 | 증거 | 수정/이관 | 재검증 |
|---|---|---|---|---|---|
| `AG01-R03-REV-01` | P2 | `tests/compatibility/ag-01/wear_emulator_runtime.py` `build_safe_runtime_verification_plan` 3단계 | 초안에서 비검증 브로드캐스트 컴포넌트명(`com.google.android.wearable.watchfacestudio/androidx.wear.watchface.editor.EditorSession`)을 워치 페이스 선택 명령으로 기재함. 리소스 전용 WFF 패키지 선택 방식과 불일치할 수 있음. | 해당 비검증 브로드캐스트 명령을 제거하고 `dumpsys package`, 홈 화면 이동 후 공식 Wear OS Watch Face Picker 선택 안내, 그리고 `dumpsys wallpaper` 활성 바인딩 검증 절차로 정정함. | 수정 후 `test_ag01_suite.py` 22건(`92.608s`) 및 `wear_emulator_runtime.py --plan-only` 재실행 전수 `PASS`. |

---

## 8. 종료 게이트 (G0~G7 — `VERIFICATION_PROTOCOL.md` 기준 준수)

| 게이트 | 결과 | 증거 또는 미적용 사유 |
|---|---|---|
| **G0 사전 검증** | **PASS** | 최신 `origin/main` (`a9664b2e3eb72f99a06c2d973259cb80d7cc4337`)의 `AGENTS.md`, `AG-01-R03.md`, `STATUS.md`, `BLOCKERS.md`, `WORK_LOG.md`, `OPS-05/REPORT.md`, `VERIFICATION_PROTOCOL.md`, `TASK_REPORT_TEMPLATE.md` 확인 완료. 허용 경로 외 변경 `0`건. |
| **G1 구현/요구사항** | **PASS** | `AG01-AUD-01/02/03` 및 §4 안전 런타임 절차 요구사항 100% 구현·문서화 완료 (§5 추적표 참조). |
| **G2 검증 도구** | **PASS** | `require_rejection`의 도구 오류(`rc!=0`)·배너 누락·경로/버전 불일치·`SEVERE` 외 문자열 오판 차단 시험 5건, `inspect_emulator_environment`의 도구 부재/오류/빈 출력(`UNKNOWN`)·폰 AVD/물리 기기(`NOT RUN`) 시험 3건, 런타임 안전장치 시험 1건 전수 PASS. |
| **G3 시험/회귀** | **PASS** | G5 수정 후 `test_ag01_suite.py` 22건(68 validator subtests) PASS, `tests/unit` 40건 PASS, `check_foundation.py` PASS, 60건 엄격 스키마 매트릭스 PASS. |
| **G4 분야별 검증** | **PARTIAL** | WFF 정적 스키마(60건)·격리 패키징/서명(6 APK)·정적 메모리 모델 통제 비교(4 Ablation)는 `PASS`이나, Wear OS 에뮬레이터 및 실기기 런타임 렌더링·모션 연속성·센서·전력은 사용자 승인 전 시스템 이미지 미설치로 **`NOT RUN`**. |
| **G5 별도 재검토** | **PASS (자기 재검토)** | 자기 재검토에서 `AG01-R03-REV-01` 발견·수정 후 전체 회귀 재실행 PASS. 독립 외부 검토는 PR #2에서 총괄 검토 예정. |
| **G6 증거 및 판정** | **PARTIAL** | 회차 03의 모든 파일 SHA-256, 실시간 `sdkmanager`/`avdmanager`/`adb` 원문 로그 4종, 60건 스키마 원문 로그, 회차 02 정정표(`ERR-01`~`ERR-05`)가 100% 일치함을 확인함. 단, Wear OS 런타임 시험이 `NOT RUN`이므로 전체 작업 완료 기준상 최종 판정을 `PARTIAL`로 유지함. |
| **G7 문서/재개** | **PASS (브랜치 범위)** | `REPORT-03.md` 작성, 기존 `REPORT.md`/`REPORT-02.md`/`logs/*` 보존, 중앙 문서(`STATUS`/`WORK_LOG`/`BLOCKERS`)는 직접 수정하지 않고 갱신 제안 기록, `agent/antigravity/AG-01` 푸시 및 PR #2 갱신 대상. |

- **최종 작업 판정 및 이유**: **`PARTIAL`** — `AG01-AUD-01`, `AG01-AUD-02`, `AG01-AUD-03` 결함 수정, 60건 엄격 스키마·22건 단위 회귀·실시간 SDK/AVD 원문 증거·안전한 런타임 절차 구축은 모두 `PASS`했으나, 실제 Wear OS 6/7 에뮬레이터 및 실기기 런타임 렌더링 검증이 사용자 승인 대기로 `NOT RUN` 상태이다.
- **제품 출시 판정(별도)**: **`NO-GO`** 유지 (실기기·에뮬레이터 런타임, 그래픽/모션 연속성, 전력/발광 픽셀 미검증).
- **미해결 장애 / 이관 및 해결 조건**:
  - `BLK-AG01-EMULATOR`: Wear OS 시스템 이미지 미설치(`NOT RUN`). 사용자 명시 승인 후 `system-images;android-36;android-wear-signed;x86_64` (WFF 4) → `system-images;android-37.0;android-wear-signed;x86_64` (WFF 5) 순으로 1개씩 설치·AVD 생성(`--force` 없음)하여 `wear_emulator_runtime.py`로 실행하면 해소 가능.
  - `B-011`: 공식 Google watchface JAR pin 교체는 중앙 통합 승인 이후 후속 회차에서 반영.
- **다음 작업 및 첫 명령**:
  1. 총괄 검토자가 PR #2(`agent/antigravity/AG-01`)의 회차 03 커밋과 `docs/evidence/AG-01/REPORT-03.md`, `docs/evidence/AG-01/logs-r03/*`를 감사한다.
  2. 사용자가 Wear OS 시스템 이미지 설치를 승인할 경우 첫 명령:
     - `sdkmanager "system-images;android-36;android-wear-signed;x86_64"`
     - `avdmanager create avd -n aura_wear36_round -k "system-images;android-36;android-wear-signed;x86_64" -d wearos_large_round`
     - 기대 결과: Wear OS 6.0 (API 36) 원형 AVD 생성 후 `run_ag01_verification.py --mode emulator`가 `status=READY`, `wear_avds=['aura_wear36_round']`로 전환됨.
- **중앙 운영 문서 갱신 여부**: 본 브랜치에서 직접 수정하지 않음 (아래 제안 제공).
  - `STATUS.md` / `WORK_LOG.md` 제안: `AG-01 회차 03 완료 (PR #2 갱신): AG01-AUD-01/02/03 수정, 실시간 sdkmanager/avdmanager/adb 원문 로그 4종 및 엄격 60건 스키마 로그(logs-r03/) 보존, 단일 결함 Negative 2종 분리, 22개 단위/68 validator subtests PASS, 안전한 Wear OS 런타임 절차(wear_emulator_runtime.py) 마련. Wear 런타임 NOT RUN(승인 대기), AG-01 PARTIAL, 출시 NO-GO 유지.`
- **저장소 반영 확인**: `agent/antigravity/AG-01` 브랜치에 커밋 후 `origin/agent/antigravity/AG-01` 푸시 및 PR #2 갱신으로 확인 (자기 참조 커밋 SHA는 본 문서에 기재하지 않고 최종 보고 응답 및 PR 코멘트에서 확인한다).
