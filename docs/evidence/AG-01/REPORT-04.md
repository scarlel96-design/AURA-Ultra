# 작업 보고서 — AG-01 / 회차 04

- **상태**: `PARTIAL` (`AG01-AUD-04` 오판 4종 재현·수정, 사전 APK/AVD/ADB 종료 상태/MP4 헤더/최종 Awake 복귀/`finally` 정리 검증, 최신 `main` 공식 도구 pin 동기화 및 60건 스키마·6 APK·4 Ablation·25개 AG-01 단위 테스트·88개 호스트 단위 테스트 전수 PASS; 실제 Wear OS 6/7 에뮬레이터 및 실기기 런타임 렌더링은 사용자 명시 승인 대기로 `NOT RUN`)
- **일자 / 작업자 / 검토자**: `2026-11-28` / `Antigravity` / 자기 재검토 (`G5`, 독립 외부 검토 아님)
- **기준 브랜치 / 기준 HEAD**: `agent/antigravity/AG-01` (PR #2 회차 03 기준 SHA: `2749e35cd6f061dc61dcdd57e855d430ef9dbe38`)
- **PRE-FLIGHT**:
  - 확인한 최신 `origin/main` SHA: `383915b708500381cd9c87831ee0fbdf03477711` (`docs: audit AG round three and record GPT-04 schema fix [skip ci]`)
  - 실제 읽은 필수 문서: `origin/main`의 `docs/operations/agent-orders/AG-01-R04.md`, `docs/STATUS.md`, `docs/evidence/OPS-06/REPORT.md`, `tools/verify_wff.py`, `tools/verify_memory.py` 및 로컬 `tools/generate_bootstrap.py`, `.gitattributes`
  - 최신 `main` 병합 동기화: `AG-01-R04.md` §3 지시에 따라 오래된 브랜치의 공통 코드를 임의 수정하지 않고 `origin/main` (`383915b708500381cd9c87831ee0fbdf03477711`)을 `agent/antigravity/AG-01`에 정상 `git merge`하여 승인된 공식 WFF 도구 pin(`tools/verify_wff.py` SHA-256 `6ef308dbc306a9187b5b1f4997a662eb57e26ac3650cebbf2ab583cd38bb609e`, `tools/verify_memory.py` SHA-256 `1ec683365aee86627f0eb502b52fc71f71eff1872776edc5bc6ef7c7b37d28bc`)을 상속받았다. 병합 후 `git diff --name-only origin/main...HEAD`가 오직 AG-01 소유 경로(`tests/compatibility/ag-01/**`, `docs/evidence/AG-01/**`)만 포함함을 확인했다.
  - PRE-FLIGHT 판정: `PASS`
- **검증 대상 코드 기준**: `agent/antigravity/AG-01` 회차 04 변경분 (기존 `REPORT.md`, `REPORT-02.md`, `REPORT-03.md`, `docs/evidence/AG-01/logs/*`, `docs/evidence/AG-01/logs-r03/*`는 수정 없이 원형 보존)
- **관련 작업지시서 / 감사 ID**: `docs/operations/agent-orders/AG-01-R04.md`, `docs/evidence/OPS-06/REPORT.md`, `AG01-AUD-04`, `B-011`
- **작업 목표, 포함/제외 범위**:
  - **포함**:
    1. `AG01-AUD-04`에서 총괄 검토가 분리 실행으로 재현한 활성 워치 페이스 선택 및 Active/AOD 상태 판정 오판 4종을 단위 시험으로 직접 재현하고 엄격 파서로 수정(`wear_emulator_runtime.py`).
    2. 설치/변경 전 로컬 APK(존재, SHA-256, 리소스 전용 ZIP 엔트리, 컴파일된 Manifest `package`/`WFF version`/`minSdk`) 및 실행 에뮬레이터(전용 승인 Wear AVD 이름, `sys.boot_completed=1`, `ro.build.characteristics` 내 `watch`, API 레벨) 사전 검증, 모든 ADB 명령 종료 상태(`rc==0`) 및 타임아웃 검증, MP4 영상 파일(`>= 1024 bytes` + ISO BMFF `ftyp` 헤더) 검증, AOD 촬영 후 최종 Active(`Awake` + `ON`) 복귀 확인, 중간 실패 시 `finally` 정리/복구(`screenrecord` 종료, `KEYCODE_WAKEUP`, 원격 임시 MP4 삭제) 구현 및 실패 픽스처 시험.
    3. 최신 `main`의 승인된 공식 도구(`wff-validator.jar` SHA-256 `6ef308dbc306a9187b5b1f4997a662eb57e26ac3650cebbf2ab583cd38bb609e`, `memory-footprint.jar` SHA-256 `1ec683365aee86627f0eb502b52fc71f71eff1872776edc5bc6ef7c7b37d28bc`, `version: 1.5.1 hash: 18d3844`) 바이너리 해시 확인 및 60건 스키마 매트릭스·6개 격리 PoC APK·4개 통제 비교 Ablation APK·실시간 에뮬레이터 환경 조사 전체 재실행 후 새 로그 경로(`docs/evidence/AG-01/logs-r04/`)에 보존.
  - **제외**: 사용자 명시 승인 없는 신규 Wear OS 시스템 이미지 다운로드 및 AVD 생성, 기존 폰 에뮬레이터(`Medium_Phone_API_36.1`) 및 실제 사용자 워치 변경, 공통 `.github`/Gradle/제품 코드/중앙 운영 문서 수정, `main` 직접 병합.
- **변경 파일 소유권 / 변경 영향**: `origin/main...HEAD` 기준 변경 파일은 100% `tests/compatibility/ag-01/**` 및 `docs/evidence/AG-01/**` 내부에 위치하며, 회차 01~03 증거 파일은 단 1바이트도 수정하지 않았다.

---

## 1. 구현 및 결정 (`AG01-AUD-04` 및 `AG-01-R04` §1~§3)

| 파일·모듈 | 변경 및 이유 | 관련 요구사항 | 파일 크기 / SHA-256 |
|---|---|---|---|
| `tests/compatibility/ag-01/wear_emulator_runtime.py` | (1) `verify_active_watchface_selected`: 단순 문자열/단어 경계(`\b`) 검색을 제거하고 현재 사용자(`mCurrentUserId`)의 활성 `mWallpaperComponent=ComponentInfo{<pkg>/<cls>}` 레코드만 파싱하여 정확한 패키지 일치(`==`)를 요구. 비활성 `previousPackage`, `.other` suffix 충돌을 `NOT_SELECTED`(`selected=False`)로 거부하고, 미확인 WFF 호스트 형식이나 컴포넌트 부재는 `UNKNOWN`(`selected=False`)으로 처리.<br>(2) `parse_power_and_display_state`: `mWakefulness`와 디스플레이 상태(`ON`/`DOZE`/`DOZE_SUSPEND`/`OFF`)가 모두 확인될 때만 판정하며, 어느 하나라도 미확인이면 `status="UNKNOWN", is_active=False, is_aod=False` 반환. `Awake+ON`만 `is_active=True`, `Dozing|Asleep + DOZE|DOZE_SUSPEND`만 `is_aod=True`로 승인(`Dozing+OFF` 거부).<br>(3) `verify_local_apk_before_install`, `validate_dedicated_wear_avd_name`, `run_checked_adb`, `validate_mp4_bytes` 및 단일 `finally` 정리 블록(녹화 프로세스 종료·`KEYCODE_WAKEUP` 복구·원격 임시 MP4 `rm -f`) 구현. | `AG01-AUD-04`, `AG-01-R04` §1·§2 | `39,061 B` / `594d4e898ebfefa39b4fbaa2be535205e434d60ba59c7650a23af7952448741f` |
| `tests/compatibility/ag-01/run_ag01_verification.py` | 최신 `main`의 `verify_wff.SHA256` (`6ef308db...`) 및 `verify_memory.SHA256` (`1ec68336...`)과 연동하고, `memory-footprint.jar --version` 출력(`memory-footprint version: 1.5.1 hash: 18d3844`) 및 `logs-r04` 파일명을 지원하도록 갱신. | `AG-01-R04` §3 | `64,365 B` / `62c34d16a6c4f7038ddb65cd01932520bfc1c715638ace0e91e8a1a1c58e2d50` |
| `tests/compatibility/ag-01/test_ag01_suite.py` | 기존 22개 테스트(68 validator subtests)를 유지하고, (1) `test_official_tool_pins_match_latest_main` (새 공식 JAR pin 및 로컬 바이너리 SHA-256 일치 검증), (2) `test_aud04_four_reproduced_false_positives_are_rejected` (`OPS-06` 합성 오판 4종 + WFF 호스트 미확인 포맷 + 정상 케이스 검증), (3) `test_execute_runtime_verification_enforces_exit_codes_awake_restore_and_cleanup` 및 `test_runtime_safety_guards_and_preinstall_apk_checks` (APK 해시/패키지/WFF버전/dex 사전 차단, 전용 AVD 이름 불일치 차단, ADB `rc!=0` 차단, Awake 미복귀 차단, MP4 헤더 검증, 중간 실패 시 `finally` 정리 검증)를 추가해 총 **25개 테스트(68 validator subtests)**로 확장. | `AG01-AUD-04`, `AG-01-R04` §1·§2·§3 | `46,132 B` / `12112fd9bfb8612ff599ed3033c329ef4a4b1fd37afad11d569c94b2ebcb18dc` |
| `tests/compatibility/ag-01/README.md` | 회차 04 공식 도구 pin, `AG01-AUD-04` 안전장치 및 `logs-r04` 실행 명령 문서화. | `AG-01-R04` | `4,304 B` / `886d02a39f355ea2849a46b5332b14cbcaca8bc22c7eef7644e5d902af461102` |
| `docs/evidence/AG-01/logs-r04/*` | 최신 공식 도구 pin(`6ef308db...`, `1ec68336...`)으로 재실행한 60건 스키마 로그, 6개 격리 PoC APK 로그, 4개 통제 비교 Ablation 로그, 실시간 SDK/AVD/ADB 원문 로그 등 7종 보존. | `AG-01-R04` §3·§5 | 아래 §3 표 참조 |

---

## 2. `AG01-AUD-04` 오판 4종 재현 및 수정 검증 상세

총괄 검토(`OPS-06`)에서 재현한 4가지 합성 입력과 추가 경계 케이스에 대해 회차 03 코드의 오판 원인과 회차 04 수정 후 실제 실행 결과(`test_aud04_four_reproduced_false_positives_are_rejected`)는 다음과 같다.

| 케이스 | 합성 입력 (`dumpsys wallpaper` 또는 `dumpsys power`/`display`) | 회차 03 동작 (결함) | 회차 04 수정 후 실제 결과 | 판정 |
|---|---|---|---|---|
| **1. 비활성 참조 (`previousPackage`)** | `mWallpaperComponent=ComponentInfo{com.example.default/.Face}` + `previousPackage=io.github.scarlel96.aura.watchface.wff4` | 전체 텍스트 `\b` 검색으로 `selected=True` 오판 | `selected=False`, `status="NOT_SELECTED"`, `active_package="com.example.default"` | **PASS (거부 성공)** |
| **2. 패키지 suffix 충돌 (`.other`)** | `mWallpaperComponent=ComponentInfo{io.github.scarlel96.aura.watchface.wff4.other/.Face}` | 정규식 `\b`가 `.`을 경계로 인정해 `selected=True` 오판 | `selected=False`, `status="NOT_SELECTED"`, `active_package="io.github.scarlel96.aura.watchface.wff4.other"` (정확한 `==` 비교 강제) | **PASS (거부 성공)** |
| **3. 디스플레이 상태 누락 (`Awake` 단독)** | `mWakefulness=Awake` (display state 미포함) | `display_state in ("ON", "UNKNOWN")` 허용으로 `is_active=True` 오판 | `display_state="UNKNOWN"`, `status="UNKNOWN"`, `is_active=False`, `is_aod=False` | **PASS (거부 성공)** |
| **4. 화면 꺼짐 (`Dozing` + `OFF`)** | `mWakefulness=Dozing` + `Display Power: state=OFF` | `wakefulness == "Dozing" or ...` 조건으로 `is_aod=True` 오판 | `display_state="OFF"`, `status="TRANSITION_OR_OFF"`, `is_active=False`, `is_aod=False` | **PASS (거부 성공)** |
| **5. WFF 호스트 미확인 포맷** | `mWallpaperComponent=ComponentInfo{com.google.wear.watchface.runtime/.DwfHostService}` (바인딩 패키지 필드 없음) | `selected=False`이나 미확인 호스트 형식 구분 없음 | `selected=False`, `status="UNKNOWN"` → `execute_runtime_verification`에서 `RuntimeVerificationIncompleteError` 발생 (`UNKNOWN`/`NOT RUN` 처리) | **PASS (차단 성공)** |
| **6. 정상 활성 선택 및 정상 Active/AOD** | `mWallpaperComponent=ComponentInfo{<target>/.WatchFace}`, `Awake+ON`, `Dozing+DOZE_SUSPEND` | `True` | `status="SELECTED"` (`selected=True`), `ACTIVE` (`is_active=True`), `AOD` (`is_aod=True`) | **PASS** |

---

## 3. 최신 `main` 공식 도구 pin 동기화 및 회차 04 전체 재검증 증거 (`docs/evidence/AG-01/logs-r04/`)

### 3.1 동기화된 공식 도구 바이너리 검증

| 도구 | 로컬 캐시 경로 | 파일 크기 | 공식 SHA-256 (`origin/main` 일치) | 실행 버전 출력 |
|---|---|---|---|---|
| 공식 WFF Validator | `.aura-tools/wff-validator.jar` | `8,813,207 B` | `6ef308dbc306a9187b5b1f4997a662eb57e26ac3650cebbf2ab583cd38bb609e` | `WFF Validation Application Version 1.7.0. Maximum Supported Format Version #5` |
| 공식 Memory Evaluator | `.aura-tools/memory-footprint.jar` | `17,612,797 B` | `1ec683365aee86627f0eb502b52fc71f71eff1872776edc5bc6ef7c7b37d28bc` | `memory-footprint version: 1.5.1 hash: 18d3844` |

### 3.2 회차 04 신규 생성 원본 로그 목록 (`docs/evidence/AG-01/logs-r04/`)

> 회차 02(`docs/evidence/AG-01/logs/*`) 및 회차 03(`docs/evidence/AG-01/logs-r03/*`) 로그는 무변경 보존하였다.

| 로그 파일 경로 | 크기 | SHA-256 | 검증 결과 요약 |
|---|---|---|---|
| `docs/evidence/AG-01/logs-r04/schema-matrix-60-r04.log` | `55,125 B` | `d19e33e2713f06ba9adcaf63ea3769f4ae56a64ea1cca75aa8d1475f2b6816aa` | 새 validator(`6ef308db...`) 기준 60건(24 `PASSED` + 36 명시적 `FAILED` + `[Line:Column] SEVERE`, `rc=0`) **60/60 PASS** |
| `docs/evidence/AG-01/logs-r04/isolated-apk-verification.log` | `36,665 B` | `27625440260bc4eec3f339a82223d07d658b4ba76f75340becb77d3bd1dd2284` | 새 memory evaluator(`1ec68336...`, `18d3844`) 기준 격리 클린 빌드 6종 PoC APK 리소스 전용·Manifest·XML 일치·메모리·v2 서명 **6/6 PASS** (APK SHA-256 및 메모리 수치 `2,371,712` / `3,181,712` bytes 이전 핀과 100% 동일) |
| `docs/evidence/AG-01/logs-r04/aod-memory-ablation.log` | `18,272 B` | `7217044cf404c7396595fa19bf8ea62549de9114951c6aec43abd5147deee57e` | 새 memory evaluator(`1ec68336...`) 기준 4종 통제 비교 + 2종 기준선 APK 평가 **6/6 PASS** (`ablation_a/b/d = 2,371,712 B [layers=0]`, `ablation_c/motion_triggers = 3,181,712 B [layers=1, +810,000 B]`; 평가 도구 조건 범위 내 결과이며 실기기 `NOT RUN`) |
| `docs/evidence/AG-01/logs-r04/emulator-readiness-r04.log` | `6,450 B` | `278277a7b24d084bd93103ca70faace65ad5beb9194f98326484b7564e3bc98e` | 새 도구 해시·버전 기록, 실시간 도구 5종 `status=OK, rc=0`, 설치된 Wear 이미지 `0`, Wear AVD `0`, 일반 폰 AVD `['Medium_Phone_API_36.1']`, 여유 공간 `97.77 GiB`, 판정 **`NOT RUN`** |
| `docs/evidence/AG-01/logs-r04/sdkmanager-list.raw.log` | `115,512 B` | `25932ec596d117fc756742f4b8c0667e7ab373374009d46954b2930b0fd6b078` | 실시간 `sdkmanager --list` 원문 (`rc=0`) |
| `docs/evidence/AG-01/logs-r04/avdmanager-list-device.raw.log` | `7,789 B` | `a8684cf9e8e47cf68dfa1429ff8ee80e6170cecd59f600ce0f76d44fcce29d1f` | 실시간 `avdmanager list device` 원문 (`rc=0`) |
| `docs/evidence/AG-01/logs-r04/avdmanager-list-avd.raw.log` | `695 B` | `578ccd3076fecccc796256301ec4b4f0f5a345ba1a1202dac71366a5eeb298ec` | 실시간 `avdmanager list avd` 원문 (`rc=0`) |

### 3.3 Windows Git `.gitattributes` (`* text=auto`)와 `test_bootstrap_generator.py` 줄바꿈 발견 기록

- `origin/main`을 병합한 직후 Windows 기본 Git 설정(`core.autocrlf=true`, 기본 `core.eol=crlf`)에서는 `.gitattributes`의 `* text=auto` 규칙에 의해 `assets/generated/bootstrap/palette.svg`(20줄)가 워킹 트리에 `CRLF`(`1,329` bytes)로 체크아웃되어 `tests/unit/test_bootstrap_generator.py`의 `test_checked_in_outputs`(LF `1,309` bytes 기대)에서 줄바꿈 바이트 불일치가 발생함을 확인했다.
- 저장소 파일이나 `.gitattributes`를 수정하지 않고 로컬 `.git/config`에 `git config core.autocrlf false` 및 `git config core.eol lf`를 설정한 뒤 `palette.svg`를 재체크아웃하자 워킹 트리가 clean(`git status` 변경 `0`건) 상태를 유지하면서 `tests/unit` **88개 호스트 단위 테스트가 전수 PASS**(`0.146s`)했다.

---

## 4. 요구사항 및 검증 추적표

| 요구사항 / 완료 기준 | 구현 파일·경로 | 시험 ID | 예상 결과 | 실제 결과 | 원본 증거·SHA-256 | 판정 |
|---|---|---|---|---|---|---|
| `AG01-AUD-04`: 활성 워치 페이스 및 Active/AOD 상태 오판 4종 재현·수정, 미확인 호스트 `UNKNOWN` 처리 | `tests/compatibility/ag-01/wear_emulator_runtime.py`, `test_ag01_suite.py` | `T-R04-01` | 합성 오판 4종 모두 `False`/`UNKNOWN`, 미확인 WFF 호스트 `UNKNOWN` (`RuntimeVerificationIncompleteError`), 정확 일치만 `True` | 단위 회귀 전수 PASS (§2 표 참조) | `wear_emulator_runtime.py` (`594d4e89...`), `test_ag01_suite.py` (`12112fd9...`) | **PASS** |
| `AG-01-R04` §2: 사전 APK(패키지/WFF버전/해시/리소스 전용)·전용 AVD 이름·`watch`·API 레벨·ADB 종료 상태·MP4 헤더·최종 Awake 복귀·`finally` 정리 검증 | `wear_emulator_runtime.py`, `test_ag01_suite.py` | `T-R04-02`, `T-R04-03` | 사전 불일치 시 설치 전 차단; 모든 ADB `rc!=0` 시 실패; Awake 미복귀/빈 MP4 실패; 중간 실패 시 `finally`에서 녹화 종료·`KEYCODE_WAKEUP`·`rm -f` 실행 | 모든 정상/실패 픽스처 단위 시험 및 `--plan-only` dry-run PASS | `wear_emulator_runtime.py` (`594d4e89...`), `test_ag01_suite.py` (`12112fd9...`) | **PASS** |
| `AG-01-R04` §3: 최신 `main` 병합, 공식 도구 pin(`6ef308db...`, `1ec68336...`) 동기화, 60건 스키마·68 subtests·6 APK·4 Ablation·88 호스트 시험 재실행 | `run_ag01_verification.py`, `docs/evidence/AG-01/logs-r04/*` | `T-R04-04` ~ `T-R04-08` | 새 바이너리 해시 일치; 60건 스키마, 68 subtests, 6 APK, 4 Ablation, 88 호스트 단위 시험 전수 PASS; 이전 증거 보존 | 전 항목 PASS, 회차 01~03 증거 변경 `0`건 | `logs-r04/schema-matrix-60-r04.log` (`d19e33e2...`), `logs-r04/isolated-apk-verification.log` (`27625440...`), `logs-r04/aod-memory-ablation.log` (`7217044c...`) | **PASS** |
| `AG-01-R04` §4: 사용자 명시 승인 후에만 Wear OS 6/7 SDK 이미지 설치 및 AVD 생성·실제 런타임 검증 (승인 없으면 정적 작업만 수행하고 `NOT RUN`) | `wear_emulator_runtime.py`, `docs/evidence/AG-01/logs-r04/emulator-readiness-r04.log` | `T-R04-09` | 승인 전 자동 다운로드 금지, 실시간 환경 조사 후 `NOT RUN` 기록 및 승인 시 API 36 → API 37 순차 실행 절차 완비 | 무다운로드 준수, `status=NOT RUN` 기록 완료 | `logs-r04/emulator-readiness-r04.log` (`278277a7...`) | **NOT RUN (승인 대기)** |

---

## 5. 검증 결과 집계

| 시험 ID | 필수/선택 | 종류 | 실행 명령 | 기대 결과 | 실제 결과 | 판정 | 원본 로그 |
|---|---|---|---|---|---|---|---|
| `T-R04-01` | 필수 | AG-01 단위 및 공식 validator 회귀 | `python -m unittest discover -s tests/compatibility/ag-01 -p "test_*.py" -v` | 25 tests (68 validator subtests) OK | `Ran 25 tests -> OK` (G5 수정 후 재실행 포함) | **PASS** | 콘솔 출력 및 `logs-r04/schema-matrix-60-r04.log` |
| `T-R04-02` | 필수 | 저장소 호스트 단위 회귀 (`main` 동기화) | `python -m unittest discover -s tests/unit -p "test_*.py"` | 88 tests OK | `Ran 88 tests in 0.146s -> OK` | **PASS** | 콘솔 출력 |
| `T-R04-03` | 필수 | 저장소 기본 계약 회귀 | `python tools/check_foundation.py` | PASS | `PASS: resource-only manifest, XML structure, AOD invariant, preview, flavor matrix, tokens` | **PASS** | 콘솔 출력 |
| `T-R04-04` | 필수 | 최신 validator 60건 엄격 스키마 매트릭스 | `python tests/compatibility/ag-01/run_ag01_verification.py --mode schema --logs-dir docs/evidence/AG-01/logs-r04` | 60/60 PASS (`6ef308db...`) | `60/60 PASS` (24 `PASSED` + 36 명시적 `FAILED` + `SEVERE`) | **PASS** | `docs/evidence/AG-01/logs-r04/schema-matrix-60-r04.log` |
| `T-R04-05` | 필수 | 최신 memory evaluator 격리 6 APK 클린 빌드·검증 | `python tests/compatibility/ag-01/run_ag01_verification.py --mode apk --logs-dir docs/evidence/AG-01/logs-r04` | 6/6 APK PASS (`1ec68336...`) | `6/6 PASS` (APK SHA-256 및 메모리 `2,371,712` / `3,181,712` B 일치) | **PASS** | `docs/evidence/AG-01/logs-r04/isolated-apk-verification.log` |
| `T-R04-06` | 필수 | 최신 memory evaluator AOD 메모리 통제 비교 (6 APK) | `python tests/compatibility/ag-01/run_ag01_verification.py --mode ablation --logs-dir docs/evidence/AG-01/logs-r04` | 6/6 Ablation PASS (`1ec68336...`) | `6/6 PASS` (`+810,000` B 레이어 할당 재현) | **PASS** | `docs/evidence/AG-01/logs-r04/aod-memory-ablation.log` |
| `T-R04-07` | 필수 | 실시간 SDK/AVD/ADB 환경 조사 | `python tests/compatibility/ag-01/run_ag01_verification.py --mode emulator --logs-dir docs/evidence/AG-01/logs-r04` | 5개 도구 `rc=0`, 원문 로그 보존, `NOT RUN` | `status=NOT RUN`, Wear 이미지 `0`, Wear AVD `0`, 폰 AVD `1`, 여유 공간 `97.77 GiB` | **PASS (조사)** / **NOT RUN (런타임)** | `docs/evidence/AG-01/logs-r04/emulator-readiness-r04.log` 외 원문 3종 |
| `T-R04-08` | 필수 | 런타임 검증 계획 dry-run | `python tests/compatibility/ag-01/wear_emulator_runtime.py --plan-only --serial emulator-5554 --avd-name aura_wear36_round ...` | Step 0~5 JSON 정상 출력 (`exit 0`) | 기대 JSON 정상 출력 | **PASS** | 콘솔 출력 |
| `T-R04-09` | 조건부 (승인 후) | Wear OS 6 (API 36) / Wear OS 7 (API 37) 에뮬레이터 런타임 렌더링 및 AOD 전환 영상 | 사용자 명시 승인 후 `aura_wear36_round` → `aura_wear37_round` 순차 구축 및 실행 | 승인 전 실행 금지 | 사용자 명시 승인 대기로 미실행 | **NOT RUN** | `docs/evidence/AG-01/logs-r04/emulator-readiness-r04.log` |

- **총 시험 집계**:
  - 호스트 및 AG-01 단위/회귀 테스트: `113`건 (`AG-01` 25건[68 validator subtests 포함] + `tests/unit` 88건) → **`113 PASS / 0 FAIL / 0 SKIP`**
  - 최신 공식 도구 기반 스키마/격리 APK/Ablation 실행: 스키마 `60/60 PASS`, 격리 PoC APK `6/6 PASS`, Ablation APK `6/6 PASS`
  - Wear OS 에뮬레이터 및 실기기 런타임: **`NOT RUN`**

---

## 6. 구현 후 검토 (G5 — 자기 재검토)

- **검토 유형**: 자기 재검토 (동일 모델·에이전트 수행; 독립 외부 승인 아님)
- **검토 대상**: 회차 04 변경 diff (`wear_emulator_runtime.py`, `run_ag01_verification.py`, `test_ag01_suite.py`, `README.md`, `logs-r04/*`)

| 결함 ID | 심각도 | 위치·재현 | 증거 | 수정/이관 | 재검증 |
|---|---|---|---|---|---|
| `AG01-R04-REV-01` | P2 | `tests/compatibility/ag-01/wear_emulator_runtime.py` `execute_runtime_verification`의 `try ... finally` 블록 분리 결함 | 초안에서 AOD 전환 녹화용 `try ... finally`와 MP4 `pull`/`rm -f`용 `try ... finally`가 두 블록으로 나뉘어 있어, 첫 번째 블록(예: `KEYCODE_SLEEP` 실패 또는 AOD 진입 실패)에서 예외가 발생하면 두 번째 블록의 `rm -f <remote_video>`에 도달하지 못해 에뮬레이터 `/sdcard/`에 임시 녹화 파일이 남을 수 있었음. | 녹화·AOD 검증·Awake 복귀·MP4 `pull` 및 `validate_mp4_bytes`를 단일 `try` 블록으로 통합하고, 단일 `finally` 블록에서 (1) `recorder` 프로세스 강제 종료(`terminate`/`wait`), (2) `KEYCODE_WAKEUP` 복구 전송, (3) `rm -f <remote_video>` 원격 임시 파일 삭제가 항상 모두 실행되도록 수정함. 또한 `test_ag01_suite.py`에서 중간 `KEYCODE_SLEEP` 실패(`rc=1`) 시 `active_recorder.terminated == True`, `rm -f` 호출, 복구 `KEYCODE_WAKEUP` 호출을 모두 단언(assert)하도록 회귀 시험을 강화함. | 수정 후 `test_ag01_suite.py` 25건 전체 재실행 `PASS`. |

---

## 7. 종료 게이트 (G0~G7) 및 최종 판정

| 게이트 | 결과 | 증거 또는 미적용 사유 |
|---|---|---|
| **G0 사전 검증** | **PASS** | 최신 `origin/main` (`383915b708500381cd9c87831ee0fbdf03477711`) 확인 및 정상 병합, `AG-01-R04.md`·`STATUS.md`·`OPS-06/REPORT.md` 확인 완료. 허용 경로 외 변경 `0`건. |
| **G1 구현/요구사항** | **PASS** | `AG01-AUD-04` 오판 4종 수정, 사전 APK/AVD/명령 종료코드/MP4/최종 Awake 복귀/`finally` 정리, 최신 공식 도구 pin 동기화 및 재검증 완료. |
| **G2 검증 도구** | **PASS** | `test_aud04_four_reproduced_false_positives_are_rejected`, `test_runtime_safety_guards_and_preinstall_apk_checks`, `test_execute_runtime_verification_enforces_exit_codes_awake_restore_and_cleanup`, `test_official_tool_pins_match_latest_main` 포함 25개 테스트(68 validator subtests) PASS. |
| **G3 시험/회귀** | **PASS** | 새 공식 도구(`6ef308db...`, `1ec68336...`)로 60건 스키마·6개 격리 PoC APK·6개 Ablation APK·25개 AG-01 단위 테스트·88개 호스트 단위 테스트·`check_foundation.py` 전수 재실행 PASS. |
| **G4 분야별 검증** | **PARTIAL** | WFF 정적 스키마(60건)·격리 APK 패키징/서명(6종)·정적 메모리 평가 모델 통제 비교(4종) PASS. 실제 Wear OS 6/7 에뮬레이터 및 실기기 런타임 렌더링·모션·센서·전력은 사용자 명시 승인 대기로 **`NOT RUN`**. |
| **G5 별도 재검토** | **PASS (자기 재검토)** | 자기 재검토로 `AG01-R04-REV-01`(중간 실패 시 원격 임시 파일 `rm -f` 누락 위험)을 발견·수정하고 단위 회귀 단언을 추가하여 재검증 PASS. |
| **G6 증거 및 판정** | **PARTIAL** | 모든 변경 파일과 `logs-r04/*` 7개 원본 로그의 크기·SHA-256·도구 해시(`6ef308db...`, `1ec68336...`) 일치 확인. 런타임 검증이 `NOT RUN`이므로 작업 판정을 `PARTIAL`로 정직하게 유지함. |
| **G7 문서/재개** | **PASS (브랜치 범위)** | 기존 회차 01~03 보고서·로그 무변경 보존, `REPORT-04.md` 및 `logs-r04/*` 작성, `agent/antigravity/AG-01` 푸시 및 PR #2 갱신 완료. |

- **최종 작업 판정**: **`PARTIAL`** (정적 스키마·패키징·메모리 통제 비교·최신 도구 동기화·런타임 검사기 신뢰성 보완 `PASS`; 실제 Wear OS 에뮬레이터 및 실기기 런타임 `NOT RUN`)
- **제품 출시 판정**: **`NO-GO`** 유지
- **사용자 승인 시 다음 첫 실행 명령 (Stage 1: Wear OS 6 / API 36 / WFF 4)**:
  1. `sdkmanager "system-images;android-36;android-wear-signed;x86_64"`
  2. `avdmanager create avd -n aura_wear36_round -k "system-images;android-36;android-wear-signed;x86_64" -d wearos_large_round`
  3. `emulator -avd aura_wear36_round -no-snapshot -no-boot-anim`
  4. 부팅 및 Watch Face Picker에서 `io.github.scarlel96.aura.watchface.wff4` 선택 후:
     `python tests/compatibility/ag-01/wear_emulator_runtime.py --serial emulator-5554 --avd-name aura_wear36_round --apk <wff4-debug.apk> --apk-sha256 cd2732fb26bbf3a6d22f7e459fbaba8ea4047f9b6530051005ce8c135afb8da7 --package-id io.github.scarlel96.aura.watchface.wff4 --wff-version 4 --out-dir docs/evidence/AG-01/runtime-wff4`
