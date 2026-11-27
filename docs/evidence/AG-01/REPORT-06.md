# AG-01 회차 06(R06) 검증 보고서 — `AG01-AUD-05`~`AG01-AUD-09` 수정, 수정 전·후 원본 재현 증거, 최신 `main` 전체 호스트 시험(198건) 및 회귀 검증

- **작성일**: 2026-11-28 (KST)
- **에이전트 / 브랜치**: `AG-01` / `agent/antigravity/AG-01`
- **대상 PR**: [PR #2 (`agent/antigravity/AG-01` → `main`)](https://github.com/scarlel96-design/AURA-Ultra/pull/2)
- **회차 시작 기준 커밋 (R05 HEAD)**: `4a89ec8f8028f05c3599d18dedbd43ad8433245e`
- **최신 `origin/main` 동기화 기준 커밋**: `209d69d311bf2ce3fa56a36c802a4909c2f85555` (`[skip ci] Record GPT-05 R04 Fluid Digits candidate and verified R02 integration`) — `git merge origin/main`으로 충돌 0건 동기화 완료
- **회차 판정**: **`PARTIAL`** (정적 스키마 60/60 `PASS`, 격리 PoC APK 6/6 `PASS`, AG-01 단위·회귀 시험 33/33 [68 validator subtests] `PASS`, 최신 `origin/main` 전체 호스트 단위 시험 **198/198 `PASS`**, `check_foundation.py` `PASS` / 실제 Wear OS 에뮬레이터 런타임 실행 및 `ffprobe` 영상 프레임 디코드 실측은 **`NOT RUN`**)
- **제품 출시 판정**: **`NO-GO`** (실제 Wear OS 에뮬레이터/실기기 렌더링·AOD 전환 실측 `NOT RUN`, 로컬 호스트 `ffprobe` 미설치로 실제 영상 프레임 검증 `NOT RUN`)

---

## 1. PRE-FLIGHT, 소유권 경계 및 기존 증거 보존 확인

### 1.1 PRE-FLIGHT 및 최신 `origin/main` 동기화 결과
1. `git fetch origin` 수행 → 최신 `origin/main` HEAD SHA `209d69d311bf2ce3fa56a36c802a4909c2f85555` 및 PR #2 기준 HEAD `4a89ec8f8028f05c3599d18dedbd43ad8433245e` 확인.
2. `origin/main`의 `AGENTS.md`, `docs/STATUS.md`, `docs/operations/agent-orders/README.md` 및 `tools/verify_wff.py`, `tools/verify_memory.py`를 확인한 뒤, `git merge --no-edit origin/main`으로 최신 `origin/main`을 `agent/antigravity/AG-01` 브랜치에 충돌 0건으로 병합하였다.
3. 공식 WFF 검증 도구 Pin 일치 확인:
   - `.aura-tools/wff-validator.jar`: `v1.7.0`, SHA-256 `6ef308dbc306a9187b5b1f4997a662eb57e26ac3650cebbf2ab583cd38bb609e`
   - `.aura-tools/memory-footprint.jar`: `version: 1.5.1 hash: 18d3844`, SHA-256 `1ec683365aee86627f0eb502b52fc71f71eff1872776edc5bc6ef7c7b37d28bc`
4. 호스트 영상 검증 도구 조사 결과:
   - `ffprobe`: `NOT_FOUND`, `ffmpeg`: `NOT_FOUND` → `AG01-AUD-07` 규칙에 따라 실제 영상 프레임 디코드 검증은 **`NOT RUN`**으로 판정하며 절대로 `PASS` 처리하지 않는다.
5. **소유권 경계 및 안전 제약 준수**:
   - `git diff --name-only origin/main...HEAD` 기준 변경 파일은 오직 `tests/compatibility/ag-01/**` 및 `docs/evidence/AG-01/**` 내부에만 존재한다.
   - 공통 코드(`tools/**`, `apps/**`, `.github/**`, Gradle 설정) 및 타 에이전트 소유 경로·중앙 운영 문서는 일절 수정하지 않았다.
   - 사용자 명시 승인 전 Wear OS 시스템 이미지 다운로드 및 AVD 생성을 수행하지 않았으며, 기존 폰 AVD(`Medium_Phone_API_36.1`) 및 실제 사용자 워치를 변경하지 않았다. `main` 직접 병합 금지.

### 1.2 이전 회차(R01~R05) 보고서 및 원본 로그 보존 확인
| 구분 | 경로 | 보존 상태 |
|---|---|---|
| R01~R05 보고서 | `docs/evidence/AG-01/REPORT.md` ~ `REPORT-05.md` | 무수정 보존 (`git diff` 0건) |
| R02~R05 원본 로그 | `docs/evidence/AG-01/logs/*`, `logs-r03/*`, `logs-r04/*`, `logs-r05/*` | 무수정 보존 (`git diff` 0건) |
| R06 수정 전·후 및 회귀 원본 로그 (10종) | `docs/evidence/AG-01/logs-r06/*` | 신규 생성 및 SHA-256 기록 완료 |

---

## 2. `AG01-AUD-05` ~ `AG01-AUD-09` 수정 전 재현 및 수정 후 검증 대조표

수정 전 R05 `wear_emulator_runtime.py` (`991a89ff262c5f679da6bb488bbefa85ed3274d020cb3eda2aab9972f5bab7a5`)에서 5대 결함을 직접 재현하여 `docs/evidence/AG-01/logs-r06/pre-fix-reproduction-r06.log`에 보존하고, 수정 후 R06 `wear_emulator_runtime.py` (`c5a23026cea262ae99737619141b60ee3395f833da0f952b3b3e8d2802807d12`)에서 동일 시나리오를 재실행하여 `docs/evidence/AG-01/logs-r06/post-fix-verification-r06.log`에 보존하였다:

| 감사 ID | 재현 케이스 | 수정 전 결과 (`pre-fix-reproduction-r06.log`) | 수정 내역 (`wear_emulator_runtime.py`) | 수정 후 결과 (`post-fix-verification-r06.log`) |
|---|---|---|---|---|
| **AG01-AUD-05** | **5A**: `Display Id=0`에 `ON` 중복 2줄 + `Display Id=1` 상태 누락<br>**5B**: 보조 `Display Id=1`만 존재하고 대상 기본 `Display Id=0` 누락 | **5A**: `ACTIVE` (`is_active=True`) 오판 (중복 관측을 2개 디스플레이 증거로 오인)<br>**5B**: `ACTIVE` (`is_active=True`) 오판 | `_extract_display_states_by_id`로 디스플레이 ID별 상태 집합(`states_by_id`)을 명시 대응하여 동일 ID 중복 관측을 중복 제거. 선언된 ID 중 상태 누락(`INCOMPLETE_DISPLAY_MAPPING`), 대상 디스플레이(기본 `"0"`) 누락(`TARGET_DISPLAY_MISSING`), 다중 ID 한 줄 혼재(`AMBIGUOUS_DISPLAY_LINE`), ID 내·간 상충(`CONFLICT`) 모두 `UNKNOWN` 판정. | **5A**: `status=UNKNOWN` (`INCOMPLETE_DISPLAY_MAPPING`, `by_id={'0': ['ON'], '1': []}`)<br>**5B**: `status=UNKNOWN` (`TARGET_DISPLAY_MISSING`) |
| **AG01-AUD-06** | **6A**: 미지원 `interlace=1`(Adam7) + 1바이트 가짜 페이로드<br>**6B**: `IDAT` 내 zlib 스트림 뒤 `TRAILING_ZLIB_GARBAGE` 추가<br>**6C**: `tEXt`로 분리된 비연속 `IDAT`<br>**6D**: `6000×6000` 144MB 압축 해제 폭탄 | **6A~6D** 모두 `validate_png_bytes` **허위 `PASS`** | 입력 크기(`16 MiB`), 해상도(`4096×4096`), 압축 해제 크기(`64 MiB`) 상한 강제. `interlace != 0` 명시적 거부. 비연속 `IDAT`, 중복/`IDAT` 이후/그레이스케일 `PLTE`, `IDAT` 이후 `tRNS`, 미확인 critical 청크 및 APNG(`acTL`/`fcTL`/`fdAT`) 거부. `zlib.decompressobj()`로 `expected_len + 1` 제한 해제 후 `eof`, `unused_data`, `unconsumed_tail` 전수 검사. | **6A**: `REJECTED` (Unsupported interlace=1)<br>**6B**: `REJECTED` (21 unused bytes)<br>**6C**: `REJECTED` (non-contiguous IDAT)<br>**6D**: `REJECTED` (exceeds 4096×4096) |
| **AG01-AUD-07** | **7A**: `ftyp` 헤더 12바이트만 있고 뒤가 0으로 채워진 가짜 MP4<br>**7B**: 유효 MP4 구조 + `ffprobe` 미설치 호스트 | **7A**: `validate_mp4_bytes` **허위 `PASS`** (`size=2060`)<br>**7B**: 도구 부재 `NOT RUN` 처리 경로 부재 | `parse_and_validate_mp4_structure`로 ISO BMFF 박스(`ftyp`, `moov`, `mdat`, `trak/mdia/hdlr(vide)`, `minf/stbl/stsd`/`stsz`/`stco|co64`) 구조·영상 트랙·샘플 수(`>=1`)·`mdat` 내 샘플 범위 검증. `verify_mp4_video_artifact`로 `ffprobe` 기반 실제 디코드 프레임(`nb_read_frames >= 1`) 검증하며 도구 미설치 시 `status="NOT_RUN"`, `video_verification_status="NOT RUN"` 반환 및 `execute_runtime_verification`에서 `RuntimeVerificationIncompleteError` 발생. | **7A**: `REJECTED` (Invalid non-printable MP4 box type)<br>**7B**: `status=NOT_RUN`, `video_verification_status=NOT RUN` |
| **AG01-AUD-08** | **8A**: 전체 Active→AOD→Restore 흐름 중 활성 워치 페이스 재확인 횟수 및 캡처 전후 상태 불일치 감지 | **8A**: 초기 1회만 확인 후 Active·AOD 캡처 전후 및 최종 복귀 시점 워치 페이스 변경/화면 상태 이탈 미감지 | `_assert_watchface_selected` 및 `_assert_screen_state`를 (1) 초기, (2) Active 캡처 전, (3) Active 캡처 후, (4) AOD 캡처 전, (5) AOD 캡처 후, (6) 최종 Awake 복귀 — 총 **6개 체크포인트**에서 매번 실행하여 선택 변경 및 화면 상태 불일치 즉시 차단. | **8A**: 6개 체크포인트 전수 확인 (`wp_count=6`), 각 시점 이탈·상태 불일치 즉시 실패 |
| **AG01-AUD-09** | **9A**: 기존 `active_wff4.png` 존재 시 덮어쓰기 여부<br>**9B**: `spawn_recorder()` 예외 시 복구·정리 실행 여부 및 Step 4 캡처 실패 복구 | **9A**: 기존 증거 파일 **무단 덮어쓰기** (`overwritten=True`)<br>**9B**: `spawn_recorder()` 예외 시 복구·정리 **미실행** (`False`) | Step 0A 사전 존재 검사 + `open(..., "xb")` 배타적 쓰기 + 임시 파일 스테이징 승격(`EvidenceOverwriteError`)으로 기존 증거 파일 덮어쓰기 원천 차단. 최초 상태 변경(`Step 4 KEYCODE_WAKEUP`)부터 단일 `try...finally` 복구 범위에 포함해 캡처 실패·`spawn_recorder()` 실패 시에도 `Awake+ON`, 활성 워치 페이스, 원격 `rm -f`+`test ! -e`를 모두 검증. | **9A**: `BLOCKED` (`EvidenceOverwriteError`, 기존 바이트 보존 `True`)<br>**9B**: `recovery_wakeup=True`, `remote_cleanup=True` |

---

## 3. 전체 회귀 시험 및 최신 `origin/main` 전체 호스트 단위 시험 결과

> [!IMPORTANT]
> 회차 06 요구사항 7번에 따라 기존 R05의 88개 호스트 단위 시험 결과를 재사용하지 않고, 최신 `origin/main` (`209d69d311bf2ce3fa56a36c802a4909c2f85555`)을 병합한 상태에서 **`tests/unit` 전체 198개 호스트 단위 시험**을 새로 실행하여 원문 로그(`docs/evidence/AG-01/logs-r06/main-host-unit-suite-r06.log`)로 보존하였다.

| 검증 항목 | 실행 명령 | 결과 | 원본 로그 경로 |
|---|---|---|---|
| AG-01 단위·결함 재현·검증기 시험 (33 tests / 68 validator subtests) | `python -m unittest discover -s tests/compatibility/ag-01 -p "test_*.py" -v` | **33/33 `PASS`** (기존 28 + 신규 R06 5, 68/68 subtests `PASS`) | `docs/evidence/AG-01/logs-r06/ag01-unit-suite-r06.log` |
| **최신 `origin/main` 전체 호스트 단위 시험 (198 tests)** | `python -m unittest discover -s tests/unit -p "test_*.py" -v` | **198/198 `PASS`** (`Ran 198 tests ... OK`) | `docs/evidence/AG-01/logs-r06/main-host-unit-suite-r06.log` |
| 공식 WFF 검증기 60건 스키마 매트릭스 | `python tests/compatibility/ag-01/run_ag01_verification.py --mode schema --logs-dir docs/evidence/AG-01/logs-r06` | **60/60 `PASS`** | `docs/evidence/AG-01/logs-r06/schema-matrix-60-r06.log` |
| 6개 격리 PoC APK 클린 빌드·매니페스트·메모리·v2 서명 회귀 | `python tests/compatibility/ag-01/run_ag01_verification.py --mode apk --logs-dir docs/evidence/AG-01/logs-r06` | **6/6 `PASS`** (전부 `0 .dex`/`0 .so`, Active 2.26 MiB, Ambient 2.26~3.03 MiB, v2 서명 PASS) | `docs/evidence/AG-01/logs-r06/isolated-apk-verification.log` |
| 저장소 Foundation 정적 계약 검사 | `python tools/check_foundation.py` | **`PASS`** | 콘솔 출력 확인 |
| 실시간 Wear OS 에뮬레이터 환경 및 SDK/AVD 조사 | `python tests/compatibility/ag-01/run_ag01_verification.py --mode emulator --logs-dir docs/evidence/AG-01/logs-r06` | **`NOT RUN`** (Wear 이미지 0, Wear AVD 0, 비-Wear 폰 AVD `Medium_Phone_API_36.1` 제외) | `docs/evidence/AG-01/logs-r06/emulator-readiness-r06.log` 외 3종 raw 로그 |
| 수정 전 5대 결함 재현 원본 로그 | Python 재현 실행 (R05 `wear_emulator_runtime.py` 대상) | **5/5 결함 재현 확인** | `docs/evidence/AG-01/logs-r06/pre-fix-reproduction-r06.log` |
| 수정 후 5대 결함 대조 검증 원본 로그 | Python 대조 실행 (R06 `wear_emulator_runtime.py` 대상) | **5/5 결함 수정·차단 확인** | `docs/evidence/AG-01/logs-r06/post-fix-verification-r06.log` |

---

## 4. 회차 06 산출물 및 원본 로그 SHA-256 해시 명세

| 구분 | 상대 경로 | 크기 (Bytes) | SHA-256 |
|---|---|---|---|
| 런타임 검증기 (R06 강화) | `tests/compatibility/ag-01/wear_emulator_runtime.py` | `88,217` | `c5a23026cea262ae99737619141b60ee3395f833da0f952b3b3e8d2802807d12` |
| AG-01 단위·회귀 시험 스위트 (33 tests) | `tests/compatibility/ag-01/test_ag01_suite.py` | `85,744` | `bdd4f59f9152bd45149b444a57ceb76f12e43f9a58782890d0a1cbbb8b5acd8b` |
| AG-01 통합 검증 실행기 | `tests/compatibility/ag-01/run_ag01_verification.py` | `64,484` | `8db94569859225811d1a4ab89a41c6fea2aa482bd1383e7aa3c48d67ba5feb04` |
| AG-01 README 문서 | `tests/compatibility/ag-01/README.md` | `3,830` | `047d17a16be4b9eea43e62deb672ad1ebc85db3dae5a808017c2d89d3b74a131` |
| R06 수정 전 결함 재현 원본 로그 | `docs/evidence/AG-01/logs-r06/pre-fix-reproduction-r06.log` | `3,362` | `778cd8b184b9f2fe80b9a8550fb9c83d5764f2220422aa422d2cac8a6eed8acd` |
| R06 수정 후 결함 대조 검증 원본 로그 | `docs/evidence/AG-01/logs-r06/post-fix-verification-r06.log` | `2,202` | `6bd9a8f03a68522620a4e570f4b5546fe313c9473c93e67875ca7ab1b72a7921` |
| R06 AG-01 33개 단위 시험 원본 로그 | `docs/evidence/AG-01/logs-r06/ag01-unit-suite-r06.log` | `7,477` | `5b8671fbf29405afb002ecffabdebe7d3b6ff0acfb4521b793e3a318088968f8` |
| R06 최신 `main` 198개 호스트 시험 원본 로그 | `docs/evidence/AG-01/logs-r06/main-host-unit-suite-r06.log` | `19,172` | `999872c14cf83e1fbe63fa132ac1b08522698c9b991292c0ecec5ed0b2ed699a` |
| R06 60건 스키마 매트릭스 원본 로그 | `docs/evidence/AG-01/logs-r06/schema-matrix-60-r06.log` | `55,125` | `d19e33e2713f06ba9adcaf63ea3769f4ae56a64ea1cca75aa8d1475f2b6816aa` |
| R06 6개 격리 APK 회귀 원본 로그 | `docs/evidence/AG-01/logs-r06/isolated-apk-verification.log` | `36,660` | `cf1b2a899830ca6ee0c3ca73224dd649c2e4b476a2553ab0a1b088e2fb0618e8` |
| R06 에뮬레이터 준비 상태 요약 로그 | `docs/evidence/AG-01/logs-r06/emulator-readiness-r06.log` | `6,450` | `8d66f3ef1c54bcc353ce6d3830516635825d20e7e72e8c7c1601c850842b360a` |
| R06 실시간 `sdkmanager --list` 원본 로그 | `docs/evidence/AG-01/logs-r06/sdkmanager-list.raw.log` | `115,512` | `25932ec596d117fc756742f4b8c0667e7ab373374009d46954b2930b0fd6b078` |
| R06 실시간 `avdmanager list device` 원본 로그 | `docs/evidence/AG-01/logs-r06/avdmanager-list-device.raw.log` | `7,789` | `a8684cf9e8e47cf68dfa1429ff8ee80e6170cecd59f600ce0f76d44fcce29d1f` |
| R06 실시간 `avdmanager list avd` 원본 로그 | `docs/evidence/AG-01/logs-r06/avdmanager-list-avd.raw.log` | `695` | `578ccd3076fecccc796256301ec4b4f0f5a345ba1a1202dac71366a5eeb298ec` |

---

## 5. G5 별도 자기 재검토 (Independent Self-Review Pass)

1차 구현 및 33개 단위 시험 통과 직후 `wear_emulator_runtime.py`를 다시 비판적으로 재검토하여 4건의 추가 경계 조건을 발견·보강하고 전체 회귀 시험을 재실행하였다:

| 재검토 ID | 발견된 경계 조건 | 조치 및 재검증 결과 |
|---|---|---|
| `AG01-R06-REV-01` | 한 줄에 2개 이상의 서로 다른 Display ID와 상태가 동시에 나타날 때 기존에는 `unscoped_states`에 넣어 우연히 `target_state`와 같으면 통과할 위험이 있었음. | `ambiguous_lines`로 별도 수집하여 1건이라도 발견되면 즉시 `display_state="AMBIGUOUS_DISPLAY_LINE"`, `status="UNKNOWN"`을 반환하도록 보강. |
| `AG01-R06-REV-02` | `validate_png_bytes`에서 `inflater.decompress(idat, expected+1)` 직후 바로 무제한 `inflater.flush()`를 호출하고 있었으며, `IDAT` 이후 `tRNS` 청크 배치를 명시 차단하지 않았음. | `flush()` 호출 전에 `inflater.unconsumed_tail or len(decompressed) > expected_decompressed_len`를 먼저 차단하고 `flush()`에도 잔여 상한을 전달했으며, `IDAT` 이후 `tRNS` 청크를 명시적으로 거부하도록 보강. |
| `AG01-R06-REV-03` | MP4 `stco`/`co64` 청크 오프셋이 `mdat` 끝 직전(`m_end - 1`)에 걸쳐 있어 실제 샘플 크기만큼 공간이 없는 경우를 놓칠 수 있었고, `ffprobe`의 `codec_type` 확인이 없었음. | 모든 청크 오프셋에 대해 `m_start <= off and (off + min_sample_size) <= m_end`를 검증하고, `ffprobe` 출력의 `codec_type == "video"`를 명시 확인하도록 보강. |
| `AG01-R06-REV-04` | 임시 스테이징 MP4 경로가 고정 파일명(`transition_wff*.mp4.tmp`)이라 이전 잔류 파일과 충돌할 여지가 있었음. | 프로세스 고유 임시 파일명(`transition_wff{v}.mp4.{os.getpid()}.tmp`)으로 격리하여 안전성 강화. |

---

## 6. 게이트 판정 요약 (G0 ~ G7)

| 게이트 | 항목 | 판정 | 근거 |
|---|---|---|---|
| **G0** | PRE-FLIGHT·최신 `origin/main` 동기화·소유권·증거 보존 | **`PASS`** | `origin/main` (`209d69d311bf2ce3fa56a36c802a4909c2f85555`) 충돌 0건 병합, 공식 도구 pin 일치, 소유 경로 외 수정 0건, R01~R05 증거 완전 보존. |
| **G1** | 공식 WFF 스키마 정적 검증 (60건 매트릭스) | **`PASS`** | 60/60 `PASS` (`logs-r06/schema-matrix-60-r06.log`). |
| **G2** | 격리 6개 PoC APK 패키징·매니페스트·v2 서명 | **`PASS`** | 6/6 `PASS` (`logs-r06/isolated-apk-verification.log`). |
| **G3** | 정적 메모리 한도 검증 | **`PASS`** | 6/6 APK 모두 Active 70 MiB / Ambient 7 MiB 한도 이내 (`2.26 MiB` / `2.26~3.03 MiB`). |
| **G4** | 단위·회귀 시험 및 최신 `main` 전체 호스트 시험 | **`PASS`** | AG-01 33/33 `PASS` (68 validator subtests), 최신 `origin/main` 전체 호스트 단위 시험 **198/198 `PASS`**, `check_foundation.py` `PASS`, 수정 전·후 5대 결함 재현·차단 입증 완료. |
| **G5** | 별도 자기 재검토 | **`PASS`** | `AG01-R06-REV-01` ~ `AG01-R06-REV-04` 4건 보강 후 전체 시험 재실행 `PASS`. |
| **G6** | 실제 Wear OS 에뮬레이터 런타임 및 영상 프레임 실측 | **`NOT RUN`** | 로컬 SDK Wear OS 이미지 0건·Wear AVD 0건, 호스트 `ffprobe` 미설치 (`NOT_FOUND`). 승인 전 다운로드 금지 규정에 따라 `NOT RUN` 유지. |
| **G7** | 최종 작업 및 제품 출시 판정 | **`PARTIAL` / 출시 `NO-GO`** | G0~G5 `PASS`, G6 `NOT RUN`이므로 작업 상태 `PARTIAL`, 제품 출시 판정 **`NO-GO`** 유지 (`main` 직접 병합 금지). |
