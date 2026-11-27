# AG-01 회차 07(R07) 검증 보고서 — 런타임 검증기 최종 안정화(독립 복구·MP4 샘플/청크 대응·`ffprobe` 부분 디코딩 구분·디스플레이 섹션 경계) 및 전체 회귀 검증

- **작성일**: 2026-11-28 (KST)
- **에이전트 / 브랜치**: `AG-01` / `agent/antigravity/AG-01`
- **대상 PR**: [PR #2 (`agent/antigravity/AG-01` → `main`)](https://github.com/scarlel96-design/AURA-Ultra/pull/2)
- **회차 시작 기준 커밋 (R06 HEAD)**: `c2bad6d3117dde01344d1ade15bb8a2c7592c50e`
- **최신 `origin/main` 동기화 기준 커밋**: `c6fca7a3c95a735bb2a05b0cc420d138177c6e6d` (`[skip ci] Record GPT-06 R01 material candidate and mandatory GPT-07 stop gate`) — `git merge origin/main`으로 충돌 0건 동기화 완료
- **회차 판정**: **`PARTIAL`** (정적 스키마 60/60 `PASS`, 격리 PoC APK 6/6 `PASS`, AG-01 단위·회귀 시험 **38/38 [68 validator subtests] `PASS`**, 최신 `origin/main` 전체 호스트 단위 시험 **246/246 `PASS`**, `check_foundation.py` `PASS` / 실제 Wear OS 에뮬레이터 런타임 실행 및 `ffprobe` 실제 영상 디코드 실측은 **`NOT RUN`**)
- **제품 출시 판정**: **`NO-GO`** (실제 Wear OS 에뮬레이터/실기기 렌더링·AOD 전환 실측 `NOT RUN`, 로컬 호스트 `ffprobe` 미설치로 실제 영상 디코딩 검증 `NOT RUN`)

---

## 1. PRE-FLIGHT, 소유권 경계 및 기존 증거 보존 확인

1. **원격 저장소 및 최신 `origin/main` 동기화**:
   - `git fetch origin` 수행 → 최신 `origin/main` HEAD SHA `c6fca7a3c95a735bb2a05b0cc420d138177c6e6d` 및 PR #2 시작 기준 HEAD `c2bad6d3117dde01344d1ade15bb8a2c7592c50e` 확인.
   - `git merge --no-edit origin/main`으로 최신 `origin/main`을 `agent/antigravity/AG-01` 브랜치에 충돌 0건으로 병합 완료.
2. **공식 WFF 검증 도구 Pin 일치 확인**:
   - `.aura-tools/wff-validator.jar`: `v1.7.0`, SHA-256 `6ef308dbc306a9187b5b1f4997a662eb57e26ac3650cebbf2ab583cd38bb609e`
   - `.aura-tools/memory-footprint.jar`: `version: 1.5.1 hash: 18d3844`, SHA-256 `1ec683365aee86627f0eb502b52fc71f71eff1872776edc5bc6ef7c7b37d28bc`
3. **소유권 경계 및 안전 제약 준수**:
   - `git diff --name-only origin/main...HEAD` 기준 변경 파일은 오직 `tests/compatibility/ag-01/**` 및 `docs/evidence/AG-01/**` 내부에만 존재한다.
   - 공통 코드(`tools/**`, `apps/**`, `.github/**`, Gradle 설정) 및 타 에이전트 소유 경로·중앙 운영 문서는 일절 수정하지 않았다.
   - 기존 회차 보고서(`REPORT.md` ~ `REPORT-06.md`) 및 원본 로그(`logs/`, `logs-r03/` ~ `logs-r06/`)는 단 1바이트도 수정하지 않고 그대로 보존하였다.
   - 사용자 명시 승인 전 Wear OS 시스템 이미지 다운로드 및 AVD 생성을 수행하지 않았으며, 기존 폰 AVD(`Medium_Phone_API_36.1`) 및 실제 사용자 워치를 변경하지 않았다. `main` 직접 병합 금지.

---

## 2. 회차 07 5대 안정화 결함 수정 전·후 재현 및 대조표

수정 전 R06 `wear_emulator_runtime.py` (`c5a23026cea262ae99737619141b60ee3395f833da0f952b3b3e8d2802807d12`)에서 5대 결함을 직접 재현하여 `docs/evidence/AG-01/logs-r07/pre-fix-reproduction-r07.log`에 보존하고, 수정 후 R07 `wear_emulator_runtime.py` (`1d65bb7142d05e004d3d229e442c2e799b72bc599ab6c2e4b5a6977742876789`)에서 동일 시나리오를 재실행하여 `docs/evidence/AG-01/logs-r07/post-fix-verification-r07.log`에 보존하였다:

| 항목 | 재현 시나리오 | 수정 전 결과 (`pre-fix-reproduction-r07.log`) | 수정 내역 (`wear_emulator_runtime.py`) | 수정 후 결과 (`post-fix-verification-r07.log`) |
|---|---|---|---|---|
| **1. `staged_video.unlink` 실패 격리**<br>**2. 복구 단계별 독립 실행·오류 수집** | **1A**: `finally` 진입 시 `staged_video.unlink`에서 `PermissionError(WinError 32)` 발생 | `staged_video.unlink`가 `try/except` 없이 `finally` 첫 줄에서 예외를 던져 **이후 녹화 프로세스 종료(`terminated=False`), Awake 복귀(`False`), 원격 `rm -f`(`False`)가 전부 차단됨** | `finally`를 5개 독립 단계(Step R1 프로세스 `terminate`/`kill`/`wait` 각각 내부 보호, Step R2 `staged_video.unlink` 독립 `try/except`, Step R3 `KEYCODE_WAKEUP` 및 `dumpsys power`/`display` 독립 `try/except`, Step R4 `dumpsys wallpaper` 독립 `try/except`, Step R5 원격 `rm -f` 및 `test ! -e` 각각 독립 `try/except`)로 분리하여 어느 단계가 실패해도 나머지 모든 복구 단계가 끝까지 실행되고 오류가 독립 수집됨. | `RecoveryFailureError`에 `staged_cleanup_failed`가 기록되면서도 **`recorder_terminated=True`, `recovery_wakeup_ran=True`, `remote_rm_ran=True`** 전 단계 정상 완료 (`FIXED=YES`) |
| **3. MP4 샘플 크기·청크 대응 및 범위 검증** | **3A**: `stbl` 내 중복 `stsz` 박스(첫 번째는 0 샘플, 두 번째가 덮어씀)<br>**3B**: 단일 청크(3×64B=192B)가 `mdat` 끝 64B 전에 시작해 2·3번째 샘플이 `mdat` 밖으로 128B 이탈<br>**3C**: `stsz` 샘플 1개 vs `stco` 청크 3개 불일치 | **3A~3C** 모두 `parse_and_validate_mp4_structure` **허위 `PASS`** (`stbl_by_type` 덮어쓰기 및 첫 샘플 최소 크기만 확인한 결함) | (1) `stbl` 내 단일 샘플 테이블(`stsd`, `stsz`, `stz2`, `stsc`, `stco`, `co64`, `stts`, `ctts`, `stss`) 중복 및 `stco`+`co64` 공존 즉시 거부.<br>(2) `sample_count < chunk_count` 거부, 다중 청크 시 `stsc` 필수 및 `stsc` 전개 샘플 총합 == `stsz` `sample_count` 검증.<br>(3) 각 청크의 누적 샘플 바이트 구간 `[off, off + chunk_byte_size)`가 단일 `mdat` 페이로드 내에 완전히 포함되고 청크 구간끼리 겹치지 않는지 검증. | **3A**: `REJECTED` (Duplicate `'stsz'`)<br>**3B**: `REJECTED` (chunk byte span `[160, 352)` overflows `'mdat'` `[(32, 224)]`)<br>**3C**: `REJECTED` (`sample_count (1) < chunk_count (3)`) |
| **4. `ffprobe` `codec_type`·디코딩 오류·부분 디코딩 구분** | **4A**: `ffprobe` 스트림 JSON에서 `codec_type` 누락<br>**4B**: `rc=0`이나 `stderr`에 `[h264] error while decoding` 출력 및 24프레임 중 3프레임만 디코딩<br>**4C**: `stderr` 없이 24프레임 중 3프레임만 부분 디코딩 | **4A, 4B** 모두 `status="VERIFIED"` **허위 `PASS`** (`codec_type` 누락 허용, `stderr` 미검사, `decoded >= 1`만 확인) | (1) `vstream.get("codec_type") != "video"` 및 `codec_name` 누락 즉시 거부.<br>(2) `proc.stderr.strip()`이 비어 있지 않거나 JSON `error`가 있으면 즉시 디코딩 오류로 거부.<br>(3) 컨테이너 `stsz`의 `expected_container_frames` 및 스트림 `nb_frames`와 실제 디코딩된 `nb_read_frames`가 정확히 일치(`decoded_frames == expected_container_frames`)할 때만 전체 영상 정상(`VERIFIED`)으로 판정하고 일부 프레임만 읽힌 부분 디코딩을 즉시 거부(도구 부재 시 `NOT RUN` 유지). | **4A**: `REJECTED` (`codec_type=None`)<br>**4B**: `REJECTED` (`stderr` decoding error)<br>**4C**: `REJECTED` (`Partial video decoding: decoded 3, container declares 24`) |
| **5. 디스플레이 파서 섹션 경계 Display ID 누수 차단** | **5A**: `Logical Display 0:`에 상태가 없고 빈 줄 뒤 별도 `Display Power Controller:`에 `state=ON` 존재<br>**5B**: 첫 줄 `DisplayDeviceInfo{displayId 0, state ON}` 다음 줄에 ID 없는 `DisplayDeviceInfo{state DOZE}` 존재 | **5A**: `Logical Display 0`의 ID `0`이 빈 줄/새 섹션 경계를 넘어 적용되어 **허위 `ACTIVE`**<br>**5B**: 두 번째 ID 없는 `DisplayDeviceInfo`의 `DOZE`가 `Display Id=0`에 잘못 합쳐짐 | (1) 인라인 `DisplayDeviceInfo{...}`는 해당 줄에만 Display ID를 적용하고 줄 종료 즉시 `current_display_id = None` 리셋.<br>(2) 빈 줄, 구분선(`---`/`===`), 상위 들여쓰기 복귀(`indent < current_header_indent`), 최상위 섹션 경계(`TOP_SECTION_BOUNDARY_RE`) 및 동등 레벨 새 섹션 헤더에서 `current_display_id = None` 리셋(단, 블록 내부의 들여쓰기된 하위 서브헤더는 유지).<br>(3) 동일 덤프 내 선언된 Display ID와 섹션 밖 미귀속 상태(`unscoped_states`)가 공존하면 즉시 `UNKNOWN` 판정. | **5A**: `status=UNKNOWN` (`by_id={'0': []}`, `unscoped=['ON']`)<br>**5B**: `status=UNKNOWN` (`by_id={'0': ['ON']}`, `unscoped=['DOZE']`) |

---

## 3. 전체 회귀 시험 및 최신 `origin/main` 전체 호스트 시험(246건) 결과

| 검증 항목 | 실행 명령 | 결과 | 원본 로그 경로 |
|---|---|---|---|
| AG-01 단위·안정화·검증기 시험 (38 tests / 68 validator subtests) | `python -m unittest discover -s tests/compatibility/ag-01 -p "test_*.py" -v` | **38/38 `PASS`** (기존 33 + 신규 R07 5, 68/68 subtests `PASS`) | `docs/evidence/AG-01/logs-r07/ag01-unit-suite-r07.log` |
| **최신 `origin/main` 전체 호스트 단위 시험 (246 tests)** | `python -m unittest discover -s tests/unit -p "test_*.py" -v` | **246/246 `PASS`** (`Ran 246 tests ... OK`) | `docs/evidence/AG-01/logs-r07/main-host-unit-suite-r07.log` |
| 공식 WFF 검증기 60건 스키마 매트릭스 | `python tests/compatibility/ag-01/run_ag01_verification.py --mode schema --logs-dir docs/evidence/AG-01/logs-r07` | **60/60 `PASS`** | `docs/evidence/AG-01/logs-r07/schema-matrix-60-r07.log` |
| 6개 격리 PoC APK 클린 빌드·매니페스트·메모리·v2 서명 회귀 | `python tests/compatibility/ag-01/run_ag01_verification.py --mode apk --logs-dir docs/evidence/AG-01/logs-r07` | **6/6 `PASS`** | `docs/evidence/AG-01/logs-r07/isolated-apk-verification.log` |
| 저장소 Foundation 정적 계약 검사 | `python tools/check_foundation.py` | **`PASS`** | 콘솔 출력 확인 |
| 실시간 Wear OS 에뮬레이터 환경 및 SDK/AVD 조사 | `python tests/compatibility/ag-01/run_ag01_verification.py --mode emulator --logs-dir docs/evidence/AG-01/logs-r07` | **`NOT RUN`** (Wear 이미지 0, Wear AVD 0, 비-Wear 폰 AVD `Medium_Phone_API_36.1` 제외) | `docs/evidence/AG-01/logs-r07/emulator-readiness-r07.log` 외 3종 raw 로그 |
| 수정 전 5대 안정화 결함 재현 원본 로그 | Python 재현 실행 (R06 `wear_emulator_runtime.py` 대상) | **5/5 결함 재현 확인** | `docs/evidence/AG-01/logs-r07/pre-fix-reproduction-r07.log` |
| 수정 후 5대 안정화 결함 대조 검증 원본 로그 | Python 대조 실행 (R07 `wear_emulator_runtime.py` 대상) | **5/5 결함 수정·차단 확인** | `docs/evidence/AG-01/logs-r07/post-fix-verification-r07.log` |

---

## 4. 회차 07 산출물 및 원본 로그 SHA-256 해시 명세

| 구분 | 상대 경로 | 크기 (Bytes) | SHA-256 |
|---|---|---|---|
| 런타임 검증기 (R07 최종 안정화) | `tests/compatibility/ag-01/wear_emulator_runtime.py` | `100,929` | `1d65bb7142d05e004d3d229e442c2e799b72bc599ab6c2e4b5a6977742876789` |
| AG-01 단위·회귀 시험 스위트 (38 tests) | `tests/compatibility/ag-01/test_ag01_suite.py` | `106,266` | `9f16c8ce6a9394201b2b3832a026b1b0a3b3e3d7a91d7bc268e8f75263d7fe83` |
| AG-01 통합 검증 실행기 | `tests/compatibility/ag-01/run_ag01_verification.py` | `64,484` | `8db94569859225811d1a4ab89a41c6fea2aa482bd1383e7aa3c48d67ba5feb04` |
| AG-01 README 문서 | `tests/compatibility/ag-01/README.md` | `4,476` | `2c69f4c3c5879e08eb91d0e96fc92a90f823a574282387e936139fdde40288f1` |
| R07 수정 전 결함 재현 원본 로그 | `docs/evidence/AG-01/logs-r07/pre-fix-reproduction-r07.log` | `2,593` | `8f6a11af2fc3e9b70ab2bf73123d1e2b30e8d90366c017588cf445302f7a2889` |
| R07 수정 후 결함 대조 검증 원본 로그 | `docs/evidence/AG-01/logs-r07/post-fix-verification-r07.log` | `2,260` | `a63d9cc09021822d379f621eaf5a0ca020ecab7a1224fd90f8bd4547d682e681` |
| R07 AG-01 38개 단위 시험 원본 로그 | `docs/evidence/AG-01/logs-r07/ag01-unit-suite-r07.log` | `9,244` | `14ae4df00b795e473a64560a775910604f2f38f23433cfaee496ffb284221ac8` |
| R07 최신 `main` 246개 호스트 시험 원본 로그 | `docs/evidence/AG-01/logs-r07/main-host-unit-suite-r07.log` | `25,536` | `254717684205dd09c1880cba1e59a3523e24c1e8ab2906ff70a03d33431ffb62` |
| R07 60건 스키마 매트릭스 원본 로그 | `docs/evidence/AG-01/logs-r07/schema-matrix-60-r07.log` | `55,125` | `d19e33e2713f06ba9adcaf63ea3769f4ae56a64ea1cca75aa8d1475f2b6816aa` |
| R07 6개 격리 APK 회귀 원본 로그 | `docs/evidence/AG-01/logs-r07/isolated-apk-verification.log` | `36,660` | `4f1697c2dc0582091aee78e07f8f37d648a549a0fb86b2bb6bfeb9c8430820e0` |
| R07 에뮬레이터 준비 상태 요약 로그 | `docs/evidence/AG-01/logs-r07/emulator-readiness-r07.log` | `6,450` | `8c287f8097b92676696d20fc5cddb86bfd8e111d87cad4cd865b86fcee49f173` |
| R07 실시간 `sdkmanager --list` 원본 로그 | `docs/evidence/AG-01/logs-r07/sdkmanager-list.raw.log` | `115,512` | `25932ec596d117fc756742f4b8c0667e7ab373374009d46954b2930b0fd6b078` |
| R07 실시간 `avdmanager list device` 원본 로그 | `docs/evidence/AG-01/logs-r07/avdmanager-list-device.raw.log` | `7,789` | `a8684cf9e8e47cf68dfa1429ff8ee80e6170cecd59f600ce0f76d44fcce29d1f` |
| R07 실시간 `avdmanager list avd` 원본 로그 | `docs/evidence/AG-01/logs-r07/avdmanager-list-avd.raw.log` | `695` | `578ccd3076fecccc796256301ec4b4f0f5a345ba1a1202dac71366a5eeb298ec` |

---

## 5. G5 별도 자기 재검토 (Independent Self-Review Pass)

1차 구현 직후 `wear_emulator_runtime.py`를 다시 비판적으로 재검토하여 2건의 경계 조건을 발견·보강하고 전체 시험을 재실행하였다:

| 재검토 ID | 발견된 경계 조건 | 조치 및 재검증 결과 |
|---|---|---|
| `AG01-R07-REV-01` | 디스플레이 블록(예: `Logical Display 0:`, `indent=0`) 내부에 더 깊게 들여쓰기된 일반 하위 서브헤더(예: `  SubSection Details:`, `indent=2 > 0`)가 나올 때 일반 콜론 헤더 정규식이 들여쓰기 깊이를 비교하지 않으면 블록 스코프를 조기 리셋할 수 있음. | 최상위 섹션 경계(`TOP_SECTION_BOUNDARY_RE`)와 일반 섹션 헤더(`GENERIC_SECTION_HEADER_RE`)를 분리하여, 일반 섹션 헤더는 `indent <= current_header_indent`(동등 또는 상위 들여쓰기)일 때만 스코프를 리셋하고 하위 들여쓰기 서브헤더는 스코프를 유지하도록 수정 (`test_r07_display_parser_never_bleeds_previous_display_id_across_section_boundaries` Case 5 검증 완료). |
| `AG01-R07-REV-02` | Step R5에서 `rm -f`와 `test ! -e`를 독립 `try/except`로 분리할 때 `test ! -e` 실패 메시지에 `remote_cleanup_failed` 상위 분류 태그가 함께 포함되어야 기존 감사 규칙 및 세부 단계(`remote_absence_check_failed`) 양쪽에서 일관되게 추적 가능함. | `remote_cleanup_failed (remote_absence_check_failed): ...` 형식으로 통일하여 38/38 단위 시험 통과 확인. |

---

## 6. 게이트 판정 요약 (G0 ~ G7)

| 게이트 | 항목 | 판정 | 근거 |
|---|---|---|---|
| **G0** | PRE-FLIGHT·최신 `origin/main` 동기화·소유권·증거 보존 | **`PASS`** | 최신 `origin/main` (`c6fca7a3c95a735bb2a05b0cc420d138177c6e6d`) 병합, 소유 경로 외 수정 0건, R01~R06 증거 완전 보존. |
| **G1** | 공식 WFF 스키마 정적 검증 (60건 매트릭스) | **`PASS`** | 60/60 `PASS` (`logs-r07/schema-matrix-60-r07.log`). |
| **G2** | 격리 6개 PoC APK 패키징·매니페스트·v2 서명 | **`PASS`** | 6/6 `PASS` (`logs-r07/isolated-apk-verification.log`). |
| **G3** | 정적 메모리 한도 검증 | **`PASS`** | 6/6 APK 모두 Active 70 MiB / Ambient 7 MiB 한도 이내 (`2.26 MiB` / `2.26~3.03 MiB`). |
| **G4** | 단위·회귀 시험 및 최신 `main` 전체 호스트 시험 | **`PASS`** | AG-01 **38/38 `PASS`** (68 validator subtests), 최신 `origin/main` 전체 호스트 단위 시험 **246/246 `PASS`**, `check_foundation.py` `PASS`, R07 5대 안정화 결함 수정 전·후 재현 로그 보존 완료. |
| **G5** | 별도 자기 재검토 | **`PASS`** | `AG01-R07-REV-01` ~ `AG01-R07-REV-02` 보강 후 전체 시험 재실행 `PASS`. |
| **G6** | 실제 Wear OS 에뮬레이터 런타임 및 영상 디코딩 실측 | **`NOT RUN`** | 로컬 SDK Wear OS 이미지 0건·Wear AVD 0건, 호스트 `ffprobe` 미설치 (`NOT_FOUND`). 승인 전 다운로드 금지 및 영상 도구 부재 시 `NOT RUN` 유지 규정에 따라 정직하게 `NOT RUN` 유지. |
| **G7** | 최종 작업 및 제품 출시 판정 | **`PARTIAL` / 출시 `NO-GO`** | G0~G5 `PASS`, G6 `NOT RUN`이므로 작업 상태 `PARTIAL`, 제품 출시 판정 **`NO-GO`** 유지 (`main` 직접 병합 금지). |
