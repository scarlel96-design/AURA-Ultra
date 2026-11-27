# AG-01 회차 05(R05) 검증 보고서 — 런타임 검증기 다중 사용자·복수 디스플레이·실패 복구·PNG 무결성 강화 및 전체 회귀 검증

- **작성일**: 2026-11-28 (KST)
- **에이전트 / 브랜치**: `AG-01` / `agent/antigravity/AG-01`
- **대상 PR**: [PR #2 (`agent/antigravity/AG-01` → `main`)](https://github.com/scarlel96-design/AURA-Ultra/pull/2)
- **작업 시작 기준 커밋 (R04 HEAD)**: `197f4ebd5d542393b52edc258f3fa381599934c7`
- **최신 `origin/main` 기준 커밋**: `2ed5d2eb29219a9d1350cef1412db7b67efe96a2` (`[skip ci] Record GPT-04 R10 verified integration and hardening candidate`)
- **회차 판정**: **`PARTIAL`** (정적 스키마 60/60 `PASS`, 격리 PoC APK 6/6 `PASS`, 통제 AOD 메모리 비교 4/4 `PASS`, AG-01 단위·회귀 시험 28/28 [68 validator subtests] `PASS`, 호스트 단위 시험 88/88 `PASS`, `check_foundation.py` `PASS` / 실제 Wear OS 에뮬레이터 런타임 실행은 사용자 시스템 이미지 다운로드 승인 대기 중으로 **`NOT RUN`**)
- **제품 출시 판정**: **`NO-GO`** (실제 Wear OS 에뮬레이터/실기기 런타임 렌더링 및 AOD 전환 실측 `NOT RUN`)

---

## 1. PRE-FLIGHT, 소유권 경계 및 기존 증거 보존 확인

### 1.1 PRE-FLIGHT 점검 결과
1. **원격 저장소 및 브랜치 기준 확인**:
   - `git fetch origin` 수행 완료.
   - 최신 `origin/main` HEAD: `2ed5d2eb29219a9d1350cef1412db7b67efe96a2`
   - PR #2 시작 기준 브랜치(`agent/antigravity/AG-01`) HEAD: `197f4ebd5d542393b52edc258f3fa381599934c7` (`OPEN`, `MERGEABLE`).
2. **공식 WFF 검증 도구 Pin 동기화 확인 (`git diff HEAD..origin/main -- tools/verify_wff.py tools/verify_memory.py` 차이 0건)**:
   - `.aura-tools/wff-validator.jar`: version `1.7.0`, SHA-256 `6ef308dbc306a9187b5b1f4997a662eb57e26ac3650cebbf2ab583cd38bb609e`
   - `.aura-tools/memory-footprint.jar`: `version: 1.5.1 hash: 18d3844`, SHA-256 `1ec683365aee86627f0eb502b52fc71f71eff1872776edc5bc6ef7c7b37d28bc`
3. **소유권 및 안전 제약 준수**:
   - 변경 경로는 오직 `tests/compatibility/ag-01/**` 및 `docs/evidence/AG-01/**` 내부로만 제한하였다.
   - 제품 소스(`apps/**`), 공통 도구(`tools/**`), 워크플로(`.github/**`), Gradle 설정, 중앙 운영 문서(`docs/STATUS.md`, `WORK_LOG.md`, `BLOCKERS.md`)는 일절 수정하지 않았다.
   - 사용자 명시 승인 전 신규 Wear OS 시스템 이미지 다운로드 및 AVD 생성을 수행하지 않았으며, 기존 폰 AVD(`Medium_Phone_API_36.1`) 및 실제 사용자 워치를 변경하지 않았다.
   - `main` 브랜치에 직접 병합하지 않았다.

### 1.2 이전 회차(R01~R04) 보고서 및 원본 로그 보존 확인
| 구분 | 경로 | 보존 상태 |
|---|---|---|
| 회차 01 보고서 | `docs/evidence/AG-01/REPORT.md` | 무수정 보존 (`git diff` 0건) |
| 회차 02 보고서 | `docs/evidence/AG-01/REPORT-02.md` | 무수정 보존 (`git diff` 0건) |
| 회차 03 보고서 | `docs/evidence/AG-01/REPORT-03.md` | 무수정 보존 (`git diff` 0건) |
| 회차 04 보고서 | `docs/evidence/AG-01/REPORT-04.md` | 무수정 보존 (`git diff` 0건) |
| 회차 02 원본 로그 (4종) | `docs/evidence/AG-01/logs/*` | 무수정 보존 (`git diff` 0건) |
| 회차 03 원본 로그 (7종) | `docs/evidence/AG-01/logs-r03/*` | 무수정 보존 (`git diff` 0건) |
| 회차 04 원본 로그 (7종) | `docs/evidence/AG-01/logs-r04/*` | 무수정 보존 (`git diff` 0건) |
| 회차 05 원본 로그 (6종) | `docs/evidence/AG-01/logs-r05/*` | 신규 생성 및 SHA-256 기록 완료 |

---

## 2. 회차 05 핵심 결함 4종 원인 분석 및 수정 내역

### 2.1 결함 1 — 현재 사용자 바인딩 부재 시 타 사용자 워치 페이스로 오판하는 경로 차단 (`verify_active_watchface_selected`)
- **기존 결함 원인**:
  - 회차 04의 `verify_active_watchface_selected`는 `mCurrentUserId`가 존재할 때 `user_filtered = [b for b in bindings if b["user_id"] in (current_user, None)]`를 계산한 뒤 `if user_filtered: bindings = user_filtered`로 조건부 대입을 수행했다.
  - 그 결과, 현재 사용자(예: `mCurrentUserId=0`)의 활성 `mWallpaperComponent` 바인딩이 없고 다른 사용자(예: `WallpaperData 10 userId=10`)의 바인딩만 존재하는 `dumpsys wallpaper` 출력에서 `user_filtered`가 빈 리스트(`[]`)가 되어 필터링을 건너뛰고 타 사용자(`userId=10`)의 워치 페이스를 현재 사용자의 활성 워치 페이스로 오판(`SELECTED`)하는 결함이 있었다.
- **회차 05 수정 내역 (`tests/compatibility/ag-01/wear_emulator_runtime.py`)**:
  1. **타 사용자 Fallback 전면 금지**: 사용자 섹션(`WallpaperData ... userId=<id>` 또는 `User <id>:`)이 존재하는 덤프에서 `mCurrentUserId`와 정확히 일치(`b["user_id"] == current_user`)하는 바인딩만 필터링하며, `user_filtered`가 비어 있을 경우 타 사용자 바인딩으로 절대 넘어가지 않고 즉시 `status="UNKNOWN"`, `selected=False`를 반환한다.
  2. **`mCurrentUserId` 누락 및 상충 차단**:
     - 사용자 섹션(`userId=...`)이 존재하는데 `mCurrentUserId`가 누락된 경우 어느 사용자가 활성 사용자인지 확정할 수 없으므로 `status="UNKNOWN"`, `selected=False`를 반환한다.
     - `mCurrentUserId`가 복수 개로 상충하는 경우(`mCurrentUserId=0` 및 `mCurrentUserId=10`) `status="UNKNOWN"`, `selected=False`를 반환한다.
  3. **혼합 스코프 및 비기본 사용자 무섹션 덤프 차단 (G5 자기 재검토 보강)**:
     - 하나의 덤프 안에 섹션 헤더 없는 바인딩(`user_id=None`)과 섹션 헤더가 있는 바인딩(`user_id != None`)이 혼재할 경우 `status="UNKNOWN"`, `selected=False`를 반환한다.
     - `mCurrentUserId`가 기본 사용자(`"0"`)가 아닌 값(예: `"10"`)인데 `userId=` 섹션 구분이 전혀 없는 덤프는 바인딩의 소유 사용자를 확정할 수 없으므로 `status="UNKNOWN"`, `selected=False`를 반환한다.

### 2.2 결함 2 — 복수 디스플레이 상태 및 상충하는 전원/디스플레이 상태 정보 처리 (`parse_power_and_display_state`)
- **기존 결함 원인**:
  - 회차 04의 `parse_power_and_display_state`는 `re.search`로 첫 번째 매치 하나만 읽고 멈추었으며, `dumpsys power`에서 디스플레이 상태를 찾으면 `dumpsys display`를 확인하지 않았다.
  - 따라서 (a) `dumpsys power`는 `ON`인데 `dumpsys display`는 `OFF` 또는 `DOZE`인 상충 상태, (b) 복수 디스플레이(`Display Id=0`은 `ON`, `Display Id=1`은 `DOZE`)의 상충 상태, (c) 복수 `mWakefulness=` 라인의 상충 상태를 감지하지 못하고 첫 번째 매치만으로 `ACTIVE` 또는 `AOD`로 오판했다.
- **회차 05 수정 내역 (`tests/compatibility/ag-01/wear_emulator_runtime.py`)**:
  1. **전수 수집(`re.findall` / `finditer`)**:
     - `dumpsys power` 내의 모든 `mWakefulness=` 값을 수집하고, `dumpsys power`와 `dumpsys display` 양쪽에서 모든 디스플레이 상태 패턴(`Display Power: state=`, `mScreenState=`, `Display State:`, `mDisplayState=`, `mGlobalDisplayState=`, `DisplayDeviceInfo{... state ...}`)을 전수 수집한다.
  2. **상충·누락·불완전 복수 디스플레이 정보의 `UNKNOWN` 판정**:
     - `mWakefulness`가 누락되었거나, 2개 이상의 서로 다른 값이 존재하거나, 허용 집합(`Awake`, `Dozing`, `Asleep`, `Dreaming`) 밖의 토큰이면 `status="UNKNOWN"`, `is_active=False`, `is_aod=False`로 판정한다.
     - `dumpsys power`와 `dumpsys display` 간, 또는 복수 디스플레이 간 서로 다른 디스플레이 상태(예: `ON` vs `OFF`, `ON` vs `DOZE`)가 관찰되면 `display_state="CONFLICT"`, `status="UNKNOWN"`, `is_active=False`, `is_aod=False`로 판정한다.
     - 복수 `Display Id`(`len(display_ids) > 1`)가 감지되었으나 상태 관찰 개수가 디스플레이 ID 개수보다 적어 일부 디스플레이의 상태가 불명확한 경우 `display_state="INCOMPLETE_MULTI_DISPLAY"`, `status="UNKNOWN"`으로 판정한다.
  3. **비정합 조합 차단**:
     - `Awake + DOZE`, `Awake + OFF`, `Dozing + ON` 등 비정합 상태 조합은 모두 `status="UNKNOWN"`, `is_active=False`, `is_aod=False`로 판정한다.
     - 오직 단일 일관된 `Awake + ON`만 `status="ACTIVE", is_active=True`가 되며, 오직 단일 일관된 `Dozing|Asleep + DOZE|DOZE_SUSPEND`만 `status="AOD", is_aod=True`가 된다 (`Dozing|Asleep + OFF`는 `status="SCREEN_OFF", is_aod=False`).

### 2.3 결함 3 — 실패 복구 과정의 ADB 종료 코드·타임아웃·녹화 프로세스 종료·최종 Awake 복귀·원격 파일 삭제 검증 (`execute_runtime_verification` & `RecoveryFailureError`)
- **기존 결함 원인**:
  - 회차 04의 `execute_runtime_verification` `finally` 블록은 (a) `recorder.kill()` 호출 후 `recorder.wait()`로 종료를 확인하지 않았고, (b) 실패 복구 시 `KEYCODE_WAKEUP` 명령의 예외를 `except Exception: pass`로 무시했으며 복구 후 `dumpsys power`/`display`로 실제 `Awake+ON` 복귀 여부를 재검증하지 않았고, (c) 실패 경로에서 `rm -f` 실패를 무시했으며 삭제 후 원격 파일이 실제로 사라졌는지(`test ! -e`) 확인하지 않았다.
- **회차 05 수정 내역 (`tests/compatibility/ag-01/wear_emulator_runtime.py`)**:
  1. **녹화 프로세스 완전 종료 및 Reap 검증**:
     - `finally`에서 `recorder.poll() is None`이면 `recorder.terminate()` 후 `recorder.wait(timeout=5)`를 수행하고, 타임아웃 시 `recorder.kill()` 후 다시 `recorder.wait(timeout=5)`를 호출하며, 최종 `recorder.poll() is None` 여부를 검사한다. 이미 종료된 경우에도 `recorder.wait(timeout=5)`로 좀비 프로세스 회수를 보장한다. 미종료 또는 예외 발생 시 `recovery_errors`에 `recorder_termination_failed`를 기록한다.
  2. **최종 `Awake + ON` 복귀 검증**:
     - 본 실행에서 `power_restored["is_active"]`가 확인되지 않은 상태에서 `finally`에 진입하면, `run_checked_adb`로 `KEYCODE_WAKEUP` (종료 코드 `0` 및 15초 타임아웃 검증)을 실행한 뒤, `run_checked_adb`로 `dumpsys power`와 `dumpsys display`를 다시 조회하여 `parse_power_and_display_state`가 `is_active == True` (`Awake + ON`)인지 검증한다. 실패 시 `recovery_errors`에 `awake_recovery_failed`를 기록한다.
  3. **원격 임시 녹화 파일 삭제 및 부재 확인**:
     - `finally`에서 `run_checked_adb`로 `adb -s <serial> shell rm -f <remote_video>` (종료 코드 `0` 및 타임아웃 검증)를 실행한 뒤, 이어서 `run_checked_adb`로 `adb -s <serial> shell test ! -e <remote_video>`를 실행해 원격 파일이 실제로 존재하지 않음을 검증한다. 실패 시 `recovery_errors`에 `remote_cleanup_failed`를 기록한다.
  4. **복구 실패 예외 전파 (`RecoveryFailureError`)**:
     - `recovery_errors`가 1건이라도 존재하면 절대 조용히 삼키지 않고 `primary_error`, `recovery_errors`, `recovery_report`를 모두 담은 `RecoveryFailureError`를 발생시킨다. 또한 `validate_mp4_bytes` 실패 시 로컬에 풀(pull)된 깨진 MP4 파일도 즉시 `unlink(missing_ok=True)`로 정리한다.

### 2.4 결함 4 — PNG 전체 구조 및 무결성 검사 보완 (`validate_png_bytes`)
- **기존 결함 원인**:
  - 회차 04의 `validate_png_bytes`는 `data.startswith(b"\x89PNG")` 4바이트 매직과 최소 바이트 길이만 확인하여, 8바이트 시그니처 불일치, 잘린 파일, 청크 CRC-32 손상, `IHDR`/`IDAT`/`IEND` 누락, 손상된 `IDAT` zlib 스트림, `IEND` 뒤의 쓰레기 바이트가 붙은 깨진 PNG를 모두 통과시켰다.
- **회차 05 수정 내역 (`tests/compatibility/ag-01/wear_emulator_runtime.py`)**:
  - Python 표준 라이브러리(`struct`, `zlib`)만 사용하여 ISO/IEC 15948 PNG 명세 전 구간을 검증하도록 `validate_png_bytes`를 구현하고 Active/Ambient 캡처 양쪽에 적용하였다:
    1. **8바이트 정규 시그니처**: `b"\x89PNG\r\n\x1a\n"` 정확 일치 확인.
    2. **청크 프레이밍 및 경계**: 모든 청크의 길이(4B big-endian), 4글자 ASCII 청크 타입(4B), 데이터 영역, CRC(4B)가 버퍼 경계 내에 정확히 맞물리는지 확인.
    3. **전 청크 CRC-32 검증**: 모든 청크에 대해 `zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF == expected_crc`를 검증.
    4. **`IHDR` 검증**: 첫 번째 청크가 반드시 13바이트 `IHDR`인지, 중복 `IHDR`가 없는지, `width >= min_width`, `height >= min_height`, `color_type in {0, 2, 3, 4, 6}`, 각 `color_type`별 허용 `bit_depth`, `compression == 0`, `filter_method == 0`, `interlace in (0, 1)`인지 검증.
    5. **`PLTE` 및 `IDAT` zlib 압축 해제·스캔라인 무결성**: `color_type == 3`(팔레트 이미지)일 때 `IDAT` 이전 유효한 `PLTE` 청크 존재 여부를 검증하고, 최소 1개 이상의 `IDAT` 청크 연결 페이로드가 `zlib.decompress`로 오류 없이 압축 해제되는지 확인. 비인터레이스(`interlace == 0`) PNG의 경우 압축 해제된 총 바이트 수가 정확히 `height * (1 + ceil(width * channels * bit_depth / 8))`과 일치하는지, 그리고 각 행(row)의 첫 번째 스캔라인 필터 타입 바이트가 `0..4` 범위인지 검증.
    6. **`IEND` 및 Trailing Bytes 차단**: 마지막 청크가 길이 0인 `IEND`이고 `IEND` 이후 단 1바이트의 잉여 데이터도 없음을 검증.

---

## 3. 결함 재현 시험 및 전체 회귀 시험 결과

### 3.1 회차 05 신규 및 확장 재현 시험 (`tests/compatibility/ag-01/test_ag01_suite.py`)
기존 25개 단위 시험(68개 공식 검증기 subtests 포함)을 전부 유지하고, 회차 05 결함 재현 시험 메서드를 추가하여 **총 28개 단위 시험(68개 공식 검증기 subtests 포함)**으로 확장하였다:

| 시험 메서드 | 검증 대상 및 재현 시나리오 | 결과 |
|---|---|---|
| `test_r05_missing_current_user_binding_never_falls_back_to_other_user` | (1) `mCurrentUserId=0`이고 `userId=10`에만 대상 패키지 바인딩 존재 → `UNKNOWN`/`selected=False`, (2) `mCurrentUserId` 없이 `userId=10` 바인딩만 존재 → `UNKNOWN`, (3) 복수 `mCurrentUserId` 충돌 → `UNKNOWN`, (4) `userId=0`(타 패키지) + `userId=10`(대상 패키지) 동시 존재 시 `userId=0` 기준 `NOT_SELECTED`, (5) unscoped + user-scoped 혼합 덤프 → `UNKNOWN`, (6) 비기본 `mCurrentUserId=10` 무섹션 덤프 → `UNKNOWN` | `PASS` |
| `test_r05_multi_display_and_conflicting_power_states_return_unknown` | (1) `dumpsys power` `ON` vs `dumpsys display` `OFF` 상충 → `UNKNOWN`, (2) 복수 디스플레이 `Display Id=0 ON` vs `Display Id=1 DOZE` 상충 → `UNKNOWN`, (3) 복수 `mWakefulness`(`Awake` + `Dozing`) 상충 → `UNKNOWN`, (4) 비정합 `Awake + DOZE` → `UNKNOWN`, (5) 비정합 `Dozing + ON` → `UNKNOWN`, (6) 일관된 `Awake + ON` → `ACTIVE`, (7) 복수 `Display Id` 중 일부 상태 누락 → `UNKNOWN`, (8) `mGlobalDisplayState=DOZE` 상충 → `UNKNOWN` | `PASS` |
| `test_r05_png_full_structure_and_integrity_validation` | (1) 4바이트 가짜 헤더(`b"\x89PNG..."`) 거부, (2) `IEND` 절단 PNG 거부, (3) `IHDR` CRC-32 1바이트 변조 거부, (4) `IEND` 뒤 trailing garbage 거부, (5) 유효 CRC를 가진 손상된 `IDAT` zlib 스트림 거부, (6) 스캔라인 길이 불일치 `IDAT` 거부, (7) `width=0` `IHDR` 거부, (8) 잘못된 스캔라인 필터 바이트(`9 > 4`) 거부, (9) `color_type=3` `PLTE` 누락 거부 | `PASS` |
| `test_execute_runtime_verification_enforces_exit_codes_awake_restore_and_cleanup` | (1) 정상 경로 `rm -f` + `test ! -e` 및 PNG 메타데이터 확인, (2) 중간 실패 시 `terminate` 타임아웃 후 `kill`+`wait` 복구 및 `KEYCODE_WAKEUP`+`dumpsys` 재검증 확인, (3) `unkillable` 녹화 프로세스 + 복구 `KEYCODE_WAKEUP` 타임아웃 + `rm -f` 실패 시 3종 복구 오류를 모두 담은 `RecoveryFailureError` 발생 확인, (4) `rm -f` 후 `test ! -e` 실패 시 `RecoveryFailureError` 발생 확인, (5) 타 사용자 바인딩만 있을 때 `RuntimeVerificationIncompleteError` 확인, (6) 4바이트 가짜 PNG 캡처 시 즉시 거부 확인 | `PASS` |

### 3.2 전체 회귀 시험 요약표
| 검증 항목 | 실행 명령 | 결과 | 원본 로그 / 증거 경로 |
|---|---|---|---|
| AG-01 통합 단위·검증기 시험 (28 tests / 68 validator subtests) | `python -m unittest discover -s tests/compatibility/ag-01 -p "test_*.py" -v` | **28/28 `PASS`** (68/68 subtests `PASS`) | 콘솔 및 `test_ag01_suite.py` |
| 공식 WFF 검증기 60건 스키마 매트릭스 (6 PoC × 4 + 7 Baseline Neg × 4 + 2 Single-Fault Neg × 4) | `python tests/compatibility/ag-01/run_ag01_verification.py --mode schema --logs-dir docs/evidence/AG-01/logs-r05` | **60/60 `PASS`** | `docs/evidence/AG-01/logs-r05/schema-matrix-60-r05.log` |
| 격리 6개 PoC APK 클린 빌드·매니페스트·메모리·v2 서명 회귀 | `python tests/compatibility/ag-01/run_ag01_verification.py --mode apk --logs-dir docs/evidence/AG-01/logs-r05` | **6/6 `PASS`** | `docs/evidence/AG-01/logs-r05/isolated-apk-verification.log` |
| 실시간 에뮬레이터 환경 및 SDK/AVD 조사 | `python tests/compatibility/ag-01/run_ag01_verification.py --mode emulator --logs-dir docs/evidence/AG-01/logs-r05` | **`NOT RUN`** (정상 판정: Wear 이미지 0, Wear AVD 0, 비-Wear 폰 AVD 1 제외) | `docs/evidence/AG-01/logs-r05/emulator-readiness-r05.log` 외 3종 raw 로그 |
| 런타임 검증기 Dry-Run 실행 계획 출력 | `python tests/compatibility/ag-01/wear_emulator_runtime.py --plan-only --serial emulator-5554 --avd-name aura_wear36_round --apk watchface-wff4-debug.apk --package-id io.github.scarlel96.aura.watchface.wff4 --wff-version 4 --out-dir docs/evidence/AG-01/runtime-wff4` | **`PASS`** (`test ! -e` 및 복구 기준 포함 JSON 출력 확인) | `wear_emulator_runtime.py` |
| 저장소 호스트 단위 시험 (88 tests) | `python -m unittest discover -s tests/unit -p "test_*.py"` | **88/88 `PASS`** | `tests/unit/` |
| 저장소 Foundation 정적 계약 검사 | `python tools/check_foundation.py` | **`PASS`** | `tools/check_foundation.py` |

### 3.3 6개 격리 PoC APK 회귀 검증 결과 (`isolated-apk-verification.log`)
최신 승인된 공식 도구(`wff-validator.jar` `v1.7.0`, `memory-footprint.jar` `version: 1.5.1 hash: 18d3844`)로 6개 PoC APK를 격리 임시 디렉터리에서 클린 빌드·검증한 결과는 다음과 같다:

| # | PoC ID | Profile (WFF / minSdk) | Source & Packaged XML SHA-256 | Isolated APK SHA-256 (Size) | Resource-Only (`0 .dex`, `0 .so`) | `maxActiveBytes` (한도 70 MiB) | `maxAmbientBytes` (한도 7 MiB) | APK Signature v2 |
|---|---|---|---|---|---|---|---|---|
| 1 | `poc_wff2_static_aod` | `wff2` (WFF#2 / API 34) | `eb7c3a8d8df08a4035e63140dc9dc4a17d45cb0586d67905cb5d40290e6413b0` | `bd8de2ff24f685a2736ac40651dd30477174da931db4d3b321eb42f14d4ca8c4` (27,139 B) | `PASS` | `2,371,712` B (2.26 MiB) | `2,371,712` B (2.26 MiB) | `PASS` |
| 2 | `poc_wff3_part_blend_aod` | `wff3` (WFF#3 / API 35) | `848f206f5d5e1320e3745b2bc2922f1793481a95fa4d146db95b8f39ed784c3c` | `c85258d910fb57e08819655972f56dc92a23f0bf7f929b47da0891432d9c92a4` (27,139 B) | `PASS` | `2,371,712` B (2.26 MiB) | `2,371,712` B (2.26 MiB) | `PASS` |
| 3 | `poc_wff4_continuity` | `wff4` (WFF#4 / API 36) | `124c3855fa4296f0e58c8a2936895986eb82b87a8321750de69f1f5dc617a34f` | `66a69539249ef76ff18d99a06c0e85ebde92e3b43c44b8ecbc3d280560655ab5` (27,139 B) | `PASS` | `2,371,712` B (2.26 MiB) | `2,371,712` B (2.26 MiB) | `PASS` |
| 4 | `poc_wff5_blend_features` | `wff5` (WFF#5 / API 37) | `42419a8116bb4965de93d54da4fa03b57c1ae503651a60bf6d6ebdbda399622e` | `6bc0ec47bd8d8864f8a4b293dc266e8b92bc41e4d6c7583f378469f2f984ef81` (27,139 B) | `PASS` | `2,371,712` B (2.26 MiB) | `2,371,712` B (2.26 MiB) | `PASS` |
| 5 | `poc_wff4_reference_complication` | `wff4` (WFF#4 / API 36) | `484e84c53ff00e4f7dd8c254fb98f220df54e98b66f9d2926525a198aa524b47` | `713dea16b5f9956b0243fcca10babff5feec8e92fd7455a2d0cc301ebee7c2e6` (27,139 B) | `PASS` | `2,371,712` B (2.26 MiB) | `2,371,712` B (2.26 MiB) | `PASS` |
| 6 | `poc_wff4_motion_triggers` | `wff4` (WFF#4 / API 36) | `c693bf723c105f7d5d5be90d4a49918b38c682b0349751dc1173b442b8e04ac2` | `3dd6808d06baa48024139ecf6193111d3ceae3baa8be3efe19794c13fa0291e9` (27,139 B) | `PASS` | `2,371,712` B (2.26 MiB) | `3,181,712` B (3.03 MiB) | `PASS` |

---

## 4. 회차 05 산출물 및 원본 로그 SHA-256 해시 명세

| 구분 | 상대 경로 | 크기 (Bytes) | SHA-256 |
|---|---|---|---|
| 런타임 검증기 (R05 강화) | `tests/compatibility/ag-01/wear_emulator_runtime.py` | `57,758` | `991a89ff262c5f679da6bb488bbefa85ed3274d020cb3eda2aab9972f5bab7a5` |
| AG-01 단위·회귀 시험 스위트 (28 tests) | `tests/compatibility/ag-01/test_ag01_suite.py` | `59,164` | `a1fe8215eed6b2d7f45132e858e7ad4cb9ef449b34cd21df534b4c6ff3e5bdb7` |
| AG-01 통합 검증 실행기 | `tests/compatibility/ag-01/run_ag01_verification.py` | `64,484` | `8db94569859225811d1a4ab89a41c6fea2aa482bd1383e7aa3c48d67ba5feb04` |
| AG-01 README 문서 | `tests/compatibility/ag-01/README.md` | `3,417` | `0deeb3e461ce8ae11fcee4cb7a1cf95894eda3096c30d3b0fb5260b55d5151b6` |
| R05 60건 스키마 매트릭스 로그 | `docs/evidence/AG-01/logs-r05/schema-matrix-60-r05.log` | `55,125` | `d19e33e2713f06ba9adcaf63ea3769f4ae56a64ea1cca75aa8d1475f2b6816aa` |
| R05 6개 격리 APK 검증 로그 | `docs/evidence/AG-01/logs-r05/isolated-apk-verification.log` | `36,660` | `43d7687fd3b89024eadc95e143ff8ec440d2dd27e7b802555302328de2e3d51b` |
| R05 에뮬레이터 준비 상태 요약 로그 | `docs/evidence/AG-01/logs-r05/emulator-readiness-r05.log` | `6,450` | `f91b708184ecf3732891d569de78857f23071cb7cccd2406f706a0ff008775d8` |
| R05 실시간 `sdkmanager --list` 원본 로그 | `docs/evidence/AG-01/logs-r05/sdkmanager-list.raw.log` | `115,512` | `25932ec596d117fc756742f4b8c0667e7ab373374009d46954b2930b0fd6b078` |
| R05 실시간 `avdmanager list device` 원본 로그 | `docs/evidence/AG-01/logs-r05/avdmanager-list-device.raw.log` | `7,789` | `a8684cf9e8e47cf68dfa1429ff8ee80e6170cecd59f600ce0f76d44fcce29d1f` |
| R05 실시간 `avdmanager list avd` 원본 로그 | `docs/evidence/AG-01/logs-r05/avdmanager-list-avd.raw.log` | `695` | `578ccd3076fecccc796256301ec4b4f0f5a345ba1a1202dac71366a5eeb298ec` |

---

## 5. G5 별도 자기 재검토 (Independent Self-Review Pass)

코드 편집 및 1차 시험 통과 직후, `wear_emulator_runtime.py`의 4대 수정 영역에 대해 경계 조건을 비판적으로 재검토하여 4건의 잠재 경계 결함을 발견하고 즉시 수정·검증하였다:

| 재검토 ID | 발견된 경계 조건 | 조치 및 재검증 결과 |
|---|---|---|
| `AG01-R05-REV-01` | `dumpsys wallpaper`에서 섹션 헤더 이전에 unscoped `mWallpaperComponent`가 나오고 뒤에 `WallpaperData ... userId=10` 섹션이 함께 나오는 혼합 덤프, 또는 `mCurrentUserId=10`(비기본 사용자)인데 `userId=` 섹션 구분이 전혀 없는 덤프가 들어올 경우 바인딩 소유 사용자를 확정할 수 없음. | `has_user_sections and any(b["user_id"] is None for b in bindings)` 및 `current_user != "0" and not has_user_sections`인 경우 모두 `status="UNKNOWN"`, `selected=False`를 반환하도록 수정하고 `test_r05_missing_current_user_binding_never_falls_back_to_other_user` Case 5·6으로 검증 완료. |
| `AG01-R05-REV-02` | 복수 디스플레이(`Display Id=0`, `Display Id=1`)가 덤프에 존재하나 그중 1개 디스플레이만 상태(`ON`)를 출력하고 나머지 디스플레이 상태가 누락된 경우, 또는 `DisplayManagerService`의 `mGlobalDisplayState=`가 개별 디스플레이 상태와 충돌하는 경우. | `mGlobalDisplayState=([A-Z_]+)` 추출 패턴을 추가하고, `len(display_ids) > 1 and len(display_observations) < len(display_ids)`일 때 `display_state="INCOMPLETE_MULTI_DISPLAY"`, `status="UNKNOWN"`을 반환하도록 수정. `test_r05_multi_display_and_conflicting_power_states_return_unknown` Case 7·8로 검증 완료. |
| `AG01-R05-REV-03` | `validate_png_bytes`에서 압축 해제된 `IDAT` 바이트 길이만 우연히 일치하고 스캔라인 첫 바이트(필터 타입 `0..4`)가 유효 범위를 벗어난 손상 데이터, 중복 `IHDR` 청크, 또는 팔레트 PNG(`color_type == 3`)에서 필수 `PLTE` 청크가 누락된 경우. | 중복 `IHDR` 차단, `color_type == 3`의 `IDAT` 이전 `PLTE` 필수 검사, 비인터레이스 각 행의 filter type 바이트(`0 <= filter_byte <= 4`) 전수 검사를 추가하고 `test_r05_png_full_structure_and_integrity_validation` Case 8·9로 검증 완료. |
| `AG01-R05-REV-04` | `adb pull`로 로컬에 가져온 MP4 파일이 `validate_mp4_bytes` 검증에서 실패할 때 디스크(`local_video`)에 깨진 파일이 잔류할 수 있으며, `recorder`가 이미 종료된 상태에서 실패 경로로 진입할 때 `wait()` 회수가 호출되지 않을 수 있음. | `validate_mp4_bytes` 실패 시 `local_video.unlink(missing_ok=True)`를 수행하고, `finally`에서 `recorder.poll() is not None`일 때도 `recorder.wait(timeout=5)`를 호출하도록 보완 완료. |

---

## 6. 게이트 판정 요약 (G0 ~ G7)

| 게이트 | 항목 | 판정 | 근거 |
|---|---|---|---|
| **G0** | 사전 조건·소유권·공식 도구 Pin 동기화 | **`PASS`** | 최신 `origin/main` (`2ed5d2eb29219a9d1350cef1412db7b67efe96a2`) 및 공식 도구 SHA-256 일치, 소유 경로 외 수정 0건, 기존 R01~R04 증거 완전 보존. |
| **G1** | 공식 WFF 스키마 정적 검증 (60건 매트릭스) | **`PASS`** | 6 PoC × 4 버전(24건) + 7 기본 Negative × 4 버전(28건) + 2 단일 결함 Negative × 4 버전(8건) = 60/60 `PASS` (`logs-r05/schema-matrix-60-r05.log`). |
| **G2** | 격리 APK 패키징·매니페스트·v2 서명 검증 | **`PASS`** | 6개 격리 PoC APK 모두 `0 .dex`, `0 .so`, `0 assets/`, XML 바이트 일치, 매니페스트 계약 및 APK Signature Scheme v2 `PASS` (`logs-r05/isolated-apk-verification.log`). |
| **G3** | 정적 메모리 한도 및 AOD 통제 비교 검증 | **`PASS`** | 6개 PoC APK 및 2×2 통제 비교 4종 모두 Active 70 MiB / Ambient 7 MiB 한도 이내 (`2.26 MiB` / `2.26~3.03 MiB`), `+810,000` bytes 원인이 AOD 가시 `PartText` 레이어임을 입증. |
| **G4** | 단위·회귀 시험 및 런타임 안전/복구/PNG 검증 | **`PASS`** | `test_ag01_suite.py` 28/28 `PASS` (68 validator subtests), 호스트 단위 시험 88/88 `PASS`, `check_foundation.py` `PASS`. 다중 사용자 오판, 복수 디스플레이 상충, 실패 복구(`RecoveryFailureError`, `test ! -e`), PNG 전체 무결성 검증 완료. |
| **G5** | 별도 자기 재검토 (Independent Self-Review) | **`PASS`** | `AG01-R05-REV-01` ~ `AG01-R05-REV-04` 4건 발견·수정 및 전체 테스트 재실행 `PASS`. |
| **G6** | 실제 Wear OS 에뮬레이터 런타임 렌더링·AOD 전환 검증 | **`NOT RUN`** | 로컬 SDK에 Wear OS 시스템 이미지(`0`개) 및 Wear OS AVD(`0`개) 미설치 (`logs-r05/emulator-readiness-r05.log`). 승인 없는 다운로드 금지 규칙에 따라 `NOT RUN`으로 정직하게 유지. |
| **G7** | 최종 작업 및 제품 출시 판정 | **`PARTIAL` / 출시 `NO-GO`** | 정적·패키징·메모리·런타임 하네스 검증은 모두 `PASS`이나, G6 실제 에뮬레이터 런타임 실측이 `NOT RUN`이므로 작업 상태는 `PARTIAL`, 제품 출시 판정은 **`NO-GO`**를 유지한다. |
