# 작업 보고서 — AG-01 (회차 02: 원격 전달, 원본 검증 로그 영속화, 기술 결론 3단계 구분 및 AOD 메모리 통제 비교)

- 작업 ID: `AG-01` (회차 `02`, 작업지시서: `docs/operations/agent-orders/AG-01-R02.md`)
- 제목: WFF 4·5 기능 검증 및 모션 연속성 PoC — 원격 브랜치/PR 전달, 52건 스키마·6개 APK 원본 증거 보존, 기술 발견 구분 및 AOD 메모리 통제 변수 비교 시험
- 담당 에이전트: `Antigravity`
- 브랜치: `agent/antigravity/AG-01`
- 회차 01 기준 커밋 SHA: `0ebe3a8d06f31bcaec959f61832efd864160fd6a` (부모 `main` SHA: `fe4e19d7c6e97c043e4f31cb5960bdb430fd507b`)
- 확인한 최신 `origin/main` SHA: `b5dd320c0718f9451b9749637c83db22584664b0`
- 작업 일시: `2026-04-20`
- 최종 상태: `静态/패키징/메모리 통제 비교 검증 PASS` / `에뮬레이터 및 실기기 런타임 렌더링 NOT RUN (미설치된 Wear OS 시스템 이미지 및 승인 전 다운로드 금지 규정 준수)`

---

## 1. 작업 개요 및 회차 02 수행 범위

`docs/operations/agent-orders/AG-01-R02.md` 지시에 따라 다음 6개 핵심 과제를 완료하였다.

1. **원격 브랜치 푸시 및 `main` 대상 PR 전달**:
   - 로컬에만 존재하던 회차 01 커밋(`0ebe3a8d06f31bcaec959f61832efd864160fd6a`, 소유 파일 17종)의 working tree clean 여부와 소유권 경계를 확인한 후 `origin/agent/antigravity/AG-01`에 푸시하고, 회차 02 검증 증거를 추가 커밋하여 `main` 대상 PR을 생성하였다(`main` 직접 병합 금지 준수).
2. **52건 스키마 검사 및 6개 격리 PoC APK의 원본 검증 증거 영속 보존**:
   - 요약 표만으로는 검증 완료로 인정하지 않는 `VERIFICATION_PROTOCOL.md` 규정에 따라, 52건 전체의 공식 `wff-validator.jar` 원본 stdout/stderr 로그, 6개 격리 빌드 PoC APK의 SHA-256 해시, ZIP 엔트리 목록, `apkanalyzer manifest print` 원본 XML, `memory-footprint.jar --report` 및 `--verbose` 원본 출력, `apksigner verify --verbose --print-certs` 원본 출력을 `docs/evidence/AG-01/logs/` 아래에 파일로 영속 보존하고 본 보고서의 모든 판정 표와 1:1로 연결하였다.
3. **기술 결론의 4단계 엄격 분리 (공식 문서 vs 공식 XSD 스키마 vs 실제 시험 증거 vs `NOT RUN` 런타임)**:
   - `Variant`, `Reference`, `AnimationController`(`Transform`/`Animation`), `Gyro`, `WFF 5 Group/ComplicationSlot blendMode` 각각에 대해 공식 문서 명세, 공식 XSD 스키마(`wff-validator.jar` 내장 `watchface.xsd`) 제약, 로컬 실제 실행으로 입증된 정적/패키징 증거, 그리고 아직 실행되지 않은 런타임(`NOT RUN`) 항목을 명확히 분리하였다.
4. **자리별 시계(`poc_wff4_motion_triggers.xml`) AOD 메모리 `+810,000` bytes 증가 원인의 단일 변수 통제 비교 시험(Controlled Ablation) 및 바이트코드 수식 규명**:
   - `ActiveDecoration`(Gyro 및 4개 Transform Animation)을 100% 동일하게 고정한 채 `DigitalClock` 개수(1개 vs 4개)와 AOD 가시 정적 `<PartText name="ClockColon">` 개수(0개 vs 1개)만 2×2로 변화시킨 4종의 통제 비교 픽스처(`ablation_a` ~ `ablation_d`)를 격리 APK로 클린 빌드하고 `memory-footprint.jar`(`--report` 및 `--verbose`)와 평가기 바이트코드(`AmbientMemoryFootprintCalculator`)로 분석하였다.
   - 그 결과 `+810,000` bytes 증가(`2,371,712` → `3,181,712` bytes)는 **시계를 4개 자리로 분할했기 때문이 아니라**, `<DigitalClock>` 뒤에 **AOD에서 `alpha="0"`으로 숨겨지지 않은 정적 `<PartText name="ClockColon">`이 배치되면서 오프로드 렌더러용 풀스크린 RGBA8888 레이어 1개(`450 × 450 × 4 = 810,000` bytes)가 추가 할당되었기 때문**임을 실험과 수식 양쪽으로 입증하였다.
5. **Wear OS 에뮬레이터 시험 요구 환경 정밀 조사**:
   - 승인 없는 다운로드를 수행하지 않고 `sdkmanager --list` 읽기 전용 카탈로그 조회, `avdmanager list device` 프로필 조회, 로컬 디스크 여유 공간(`93.88 GiB`) 조사를 통해 WFF 2~5 에뮬레이터 시험에 필요한 정확한 패키지 식별자(`android-wear` 및 API 36/37의 `android-wear-signed`), 예상 용량, AVD 프로필 및 승인 후 즉시 실행 가능한 재현 명령을 정리하였다.
6. **기존 기록 보존 및 소유권 경계 준수**:
   - 회차 01 보고서(`docs/evidence/AG-01/REPORT.md`)를 덮어쓰지 않고 보존하였으며, 허용된 소유 경로(`tests/compatibility/ag-01/**`, `docs/evidence/AG-01/**`) 외의 제품 소스, 공통 Gradle/CI, 중앙 운영 문서는 일절 수정하지 않았다.

---

## 2. 변경 파일 및 원본 증거 아티팩트 목록

### 2.1 회차 01~02 전체 소유 파일 및 역할

| 구분 | 경로 | SHA-256 / 상태 | 설명 |
|---|---|---|---|
| 회차 01 보고서 | `docs/evidence/AG-01/REPORT.md` | 보존 (수정 없음) | 회차 01 최초 검증 보고서 (기존 기록 보존 규정 준수) |
| 회차 02 보고서 | `docs/evidence/AG-01/REPORT-02.md` | 신규 추가 | 회차 02 보완 검증, 원본 증거 연결, 통제 변수 비교 및 에뮬레이터 조사 보고서 |
| 원본 로그 1 | `docs/evidence/AG-01/logs/schema-matrix-52.log` | 신규 추가 | 52건(`6 PoC × 4 + 7 Negative × 4`) 공식 `wff-validator.jar` 원본 실행 로그 |
| 원본 로그 2 | `docs/evidence/AG-01/logs/isolated-apk-verification.log` | 신규 추가 | 6개 격리 PoC APK의 SHA-256, ZIP 엔트리, `apkanalyzer`, `memory-footprint.jar`(`--report`/`--verbose`), `apksigner` 원본 로그 |
| 원본 로그 3 | `docs/evidence/AG-01/logs/aod-memory-ablation.log` | 신규 추가 | AOD 메모리 `+810,000` bytes 인과 규명용 4종 통제 비교 APK + 2종 기준선 APK의 원본 평가 로그 |
| 원본 로그 4 | `docs/evidence/AG-01/logs/environment-and-emulator.log` | 신규 추가 | OS/Java/Python/JAR 해시 및 Wear OS SDK 패키지·AVD 프로필·디스크 공간 조사 원본 로그 |
| 정상 PoC (WFF 2) | `tests/compatibility/ag-01/fixtures/wff2/poc_wff2_static_aod.xml` | `2b77582a27a201c96925e631f8d6cd9147d207258b6161613fee063deb62f401` | WFF 2 정적 AOD 전환 및 단일 시계 객체 유지 PoC |
| 정상 PoC (WFF 3) | `tests/compatibility/ag-01/fixtures/wff3/poc_wff3_part_blend_aod.xml` | `4914c959de127803753c93609d79ed27e51006416129b6221adc3ce2331c7a5d` | WFF 3 `PartDraw`/`PartText` `blendMode` 및 정적 AOD 대체 PoC |
| 정상 PoC (WFF 4) | `tests/compatibility/ag-01/fixtures/wff4/poc_wff4_continuity.xml` | `f70f8ef90b3f3418381f1b749c8fd6ef3cb01a88dc5302008f560d045b04c582` | WFF 4 `Variant` 단계적 AOD 전환(6종 보간 모두 포함) 및 단일 시계 연속 모션 PoC |
| 정상 PoC (WFF 4) | `tests/compatibility/ag-01/fixtures/wff4/poc_wff4_reference_complication.xml` | `e7abd38b9c36efde20c1b40923aeed2a244750e1e0b7a5d77c2c58b4187a6f6d` | WFF 4 `Reference` 단일 발행자 및 합성 컴플리케이션 다중 그래픽 제어 PoC |
| 정상 PoC (WFF 4) | `tests/compatibility/ag-01/fixtures/wff4/poc_wff4_motion_triggers.xml` | `745df3951f3d0333f3baef8e7cc2e405fa6e8cba69ff052510f6a21d7ab507d3` | WFF 4 `Gyro`, 자리별 `TimeText`(`hh_10`, `hh_1`, `mm_10`, `mm_1`), `Transform` `Animation` PoC |
| 정상 PoC (WFF 5) | `tests/compatibility/ag-01/fixtures/wff5/poc_wff5_blend_features.xml` | `72b280c1f5579a05460dc5ea18164fae4a3125dd8ef0825034fb013164136f47` | WFF 5 `Group`/`ComplicationSlot` `blendMode`, `Stroke join`, `Font minSize` PoC |
| 통제 비교 A | `tests/compatibility/ag-01/fixtures/ablation/ablation_a_single_clock_only.xml` | `cc556dccfc1f870ab87b31343591c0b9a56c369a9271454dbc00cfe1608d6ffa` | 1 `DigitalClock` (`hh:mm`) + 0 AOD 가시 `PartText` |
| 통제 비교 B | `tests/compatibility/ag-01/fixtures/ablation/ablation_b_four_clocks_only.xml` | `87bfef608cbcf050f0b3ed330de0f7b2d93fe0ccbb2bd3609e4097714a366541` | 4 자리별 `DigitalClock` + 0 AOD 가시 `PartText` (`ClockColon` 제거) |
| 통제 비교 C | `tests/compatibility/ag-01/fixtures/ablation/ablation_c_single_clock_plus_parttext.xml` | `dc6bab7f94fe323619e3e0e3ca6dea2cc3f2d09b0d2b5b38ba2401344d2d5d49` | 1 `DigitalClock` (`hh:mm`) + 1 AOD 가시 `PartText` (`ClockColon`) |
| 통제 비교 D | `tests/compatibility/ag-01/fixtures/ablation/ablation_d_four_clocks_plus_ambient_hidden_parttext.xml` | `ad22841911a9952572871de8b3e5861b4d9eea97274ef6aa46b91e9724fc7e42` | 4 자리별 `DigitalClock` + 1 `PartText` (`ClockColon`에 `Variant mode="AMBIENT" alpha="0"` 적용) |
| Negative 1~7 | `tests/compatibility/ag-01/fixtures/negative/*.xml` | 보존 (7종 해시 동일) | 상위 버전 기능 하위 유출 및 스키마 범위 위반 검출용 음성 픽스처 7종 |
| 검증 실행기 | `tests/compatibility/ag-01/run_ag01_verification.py` | 회차 02 확장 | `--mode {all,schema,apk,ablation,emulator}` 및 `--logs-dir` 원본 로그 보존 지원 |
| 단위/회귀 스위트 | `tests/compatibility/ag-01/test_ag01_suite.py` | 회차 02 확장 | 12개 테스트 메서드 (52건 공식 validator 매트릭스 + 4종 Ablation 구조/스키마 검증) |
| 스위트 문서 | `tests/compatibility/ag-01/README.md` | 회차 02 갱신 | Ablation 픽스처 및 원본 로그 생성 명령 문서화 |

---

## 3. 시험 환경, 도구 버전·해시 및 판정 기준

> 원본 증거 로그: `docs/evidence/AG-01/logs/environment-and-emulator.log`

| 항목 | 버전 / 식별자 | SHA-256 / 경로 / 비고 |
|---|---|---|
| OS | Windows 11 Build 26300 (`AMD64`) | `Windows-11-10.0.26300-SP0` |
| Python | `3.14.7` (`MSC v.1944 64 bit`) | UTF-8 강제 인코딩 서브프로세스 실행 |
| JDK | OpenJDK `21.0.5+11-LTS` (Eclipse Temurin) | `-Dfile.encoding=UTF-8 -Dsun.stdout.encoding=UTF-8 -Dsun.stderr.encoding=UTF-8` |
| Gradle / AGP | Gradle `9.3.1` / Android Gradle Plugin `9.1.1` | 격리 임시 디렉터리(`tempfile.TemporaryDirectory`)에서 `--no-daemon --stacktrace` 실행 |
| Android SDK | `compileSdk 37`, `targetSdk 37` | Build-Tools `36.0.0`, `36.1.0` / Platform-Tools `36.0.2` / Emulator `36.4.9` |
| 공식 WFF Validator | `wff-validator.jar` (`v1.7.0`) | SHA-256: `0e2204137fca618264e82f9a053c6c9ec6d4fad08d2b56aa8a57d75c0508a804` |
| 공식 Memory Evaluator | `memory-footprint.jar` (`v1.5.1`, commit `b87dde8`) | SHA-256: `503c5f7bc9209ec4d4d4974f973cf66ad6fbb435e8422c310aac5b820f1f991a` |

### 정상(PASS) 및 실패(REJECT) 판정 기준 (`tools/verify_wff.py`, `tools/check_apk.py`, `tools/verify_memory.py` 계약)

1. **스키마 정상 판정(`PASS_EXPECTED_VALID` / `PASS_VALID_ON_HIGHER_VERSION`)**:
   - `wff-validator.jar` 종료 코드 `0`, 출력 내 `FAILURE` 또는 `SEVERE:` 정규식 매치 `0`건, 그리고 정확히 `INFO: ✅  PASSED : <절대경로> is valid against watch face format version #<N>` 라인이 일치해야 통과한다.
2. **스키마 거부 판정(`PASS_EXPECTED_REJECTED_ON_LOWER_VERSION` / `PASS_DETECTED_INVALID`)**:
   - 출력 내 `PASSED` 라인이 절대 없어야 하며, 종료 코드가 `0`이 아니거나 `FAILURE`/`SEVERE:` 라인이 존재해야 하고, 지정된 핵심 위반 키워드(`blendMode`, `Variant`, `Reference`, `join`, `1.35`)가 실제 `SEVERE:` 메시지에 포함되어야 통과한다.
3. **격리 APK 검증 판정**:
   - **리소스 전용 검사**: APK ZIP 내부에 `classes*.dex`, `*.so`, `assets/*`가 0개이고 필수 리소스(`AndroidManifest.xml`, `resources.arsc`, `res/drawable-nodpi-v4/preview.png`, `res/xml/watch_face_info.xml`, `res/raw/watchface.xml`)가 존재해야 한다.
   - **컴파일된 Manifest 검사**: `apkanalyzer manifest print` 출력에서 `package`, `minSdkVersion`, `targetSdkVersion="37"`, `android:hasCode="false"`, `com.google.android.wearable.standalone="true"`, `com.google.wear.watchface.format.version="<N>"`이 프로필 계약(`compatibility/version-profiles.json`)과 정확히 일치해야 한다.
   - **XML 바이트 일치 검사**: 원본 PoC XML의 SHA-256과 APK 내부 `res/raw/watchface.xml`의 SHA-256이 100% 일치해야 한다.
   - **메모리 예산 검사**: `memory-footprint.jar --watch-face <apk> --schema-version <N> --apply-v1-offload-limitations --report` 결과에서 `maxActiveBytes <= 73,400,320` (70 MiB), `maxAmbientBytes <= 7,340,032` (7 MiB)를 만족해야 한다.
   - **서명 검사**: `apksigner verify --verbose --print-certs` 결과 `Verifies` 및 `Verified using v2 scheme (APK Signature Scheme v2): true`를 만족해야 한다.

---

## 4. 52건 스키마 검사 및 6개 격리 PoC APK 원본 증거 연결

### 4.1 52건 공식 WFF Validator 스키마 매트릭스 (`docs/evidence/AG-01/logs/schema-matrix-52.log`)

모든 52건(`CASE 01/52` ~ `CASE 52/52`)의 전체 실행 명령, 종료 코드, 파일 SHA-256 및 `wff-validator.jar` 원본 stdout/stderr는 `docs/evidence/AG-01/logs/schema-matrix-52.log`에 보존되어 있다.

#### (1) 정상 PoC 6종 × WFF 2·3·4·5 (24건: `CASE 01/52` ~ `CASE 24/52`)

| 케이스 번호 | PoC ID | 원본 XML SHA-256 (앞 16자) | WFF 2 | WFF 3 | WFF 4 | WFF 5 | 원본 로그 참조 (`schema-matrix-52.log`) |
|---|---|---|---|---|---|---|---|
| `CASE 01~04` | `poc_wff2_static_aod` | `2b77582a27a201c9` | **VALID** (`rc=0`) | **VALID** (`rc=0`) | **VALID** (`rc=0`) | **VALID** (`rc=0`) | `CASE 01/52` ~ `CASE 04/52` |
| `CASE 05~08` | `poc_wff3_part_blend_aod` | `4914c959de127803` | **REJECT** (`blendMode`) | **VALID** (`rc=0`) | **VALID** (`rc=0`) | **VALID** (`rc=0`) | `CASE 05/52` ~ `CASE 08/52` |
| `CASE 09~12` | `poc_wff4_continuity` | `f70f8ef90b3f3418` | **REJECT** (`Variant`) | **REJECT** (`Variant`) | **VALID** (`rc=0`) | **VALID** (`rc=0`) | `CASE 09/52` ~ `CASE 12/52` |
| `CASE 13~16` | `poc_wff4_reference_complication` | `e7abd38b9c36efde` | **REJECT** (`Reference`) | **REJECT** (`Reference`) | **VALID** (`rc=0`) | **VALID** (`rc=0`) | `CASE 13/52` ~ `CASE 16/52` |
| `CASE 17~20` | `poc_wff4_motion_triggers` | `745df3951f3d0333` | **REJECT** (`Variant`) | **REJECT** (`Variant`) | **VALID** (`rc=0`) | **VALID** (`rc=0`) | `CASE 17/52` ~ `CASE 20/52` |
| `CASE 21~24` | `poc_wff5_blend_features` | `72b280c1f5579a05` | **REJECT** (`blendMode`) | **REJECT** (`blendMode`) | **REJECT** (`blendMode`) | **VALID** (`rc=0`) | `CASE 21/52` ~ `CASE 24/52` |

#### (2) 상위 기능 하위 유출 및 스키마 위반 Negative 픽스처 7종 × WFF 2·3·4·5 (28건: `CASE 25/52` ~ `CASE 52/52`)

| 케이스 번호 | Negative 픽스처 ID | 원본 XML SHA-256 (앞 16자) | WFF 2 | WFF 3 | WFF 4 | WFF 5 | 검출된 실제 `SEVERE:` 메시지 요약 (`schema-matrix-52.log`) |
|---|---|---|---|---|---|---|---|
| `CASE 25~28` | `neg_wff3_part_blend_in_wff2` | `375b388607476380` | **REJECT** | VALID | VALID | VALID | `Attribute 'blendMode' is not allowed to appear in element 'PartDraw'` |
| `CASE 29~32` | `neg_wff4_variant_transition_in_wff3` | `4f811993d67f5efe` | **REJECT** | **REJECT** | VALID | VALID | `Attribute 'duration' / 'interpolation' / 'startOffset' is not allowed to appear in element 'Variant'` |
| `CASE 33~36` | `neg_wff4_reference_in_wff3` | `d009a0629d018506` | **REJECT** | **REJECT** | VALID | VALID | `Invalid content was found starting with element 'Reference'` |
| `CASE 37~40` | `neg_wff5_group_blend_in_wff4` | `cf17eb33f7e688c9` | **REJECT** | **REJECT** | **REJECT** | VALID | `Attribute 'blendMode' is not allowed to appear in element 'Group'` |
| `CASE 41~44` | `neg_wff5_complicationslot_blend_in_wff4` | `d871d14b92c75874` | **REJECT** | **REJECT** | **REJECT** | VALID | `Attribute 'blendMode' is not allowed to appear in element 'ComplicationSlot'` |
| `CASE 45~48` | `neg_wff5_stroke_join_font_minsize_in_wff4` | `b7854925c66f21b7` | **REJECT** | **REJECT** | **REJECT** | VALID | `Attribute 'join' is not allowed in 'Stroke'` / `'minSize' is not allowed in 'Font'` |
| `CASE 49~52` | `neg_wff4_invalid_variant_and_reference_parent` | `1f686be34957a34b` | **REJECT** | **REJECT** | **REJECT** | **REJECT** | `Value '1.35' is not facet-valid with respect to maxInclusive '1.0E0'` & `'Reference' not allowed in 'DigitalClock'` |

### 4.2 6개 격리 PoC APK 클린 빌드 및 패키징·메모리·서명 원본 증거 (`docs/evidence/AG-01/logs/isolated-apk-verification.log`)

모든 6개 APK(`[APK 1/6]` ~ `[APK 6/6]`)의 컴파일된 `AndroidManifest.xml` 전문, ZIP 엔트리, `memory-footprint.jar`(`--report` 및 `--verbose`) 전문, `apksigner verify` 전문은 `docs/evidence/AG-01/logs/isolated-apk-verification.log`에 보존되어 있다.

| 순번 | PoC ID | 프로필 (`WFF#` / `minSdk`) | APK 크기 | 격리 빌드 APK SHA-256 | 원본 vs 패키징 XML SHA-256 | 리소스 전용 / Manifest / v2 서명 | Active 메모리 (`<= 70 MiB`) | Ambient 메모리 (`<= 7 MiB`) | 원본 로그 섹션 |
|---|---|---|---|---|---|---|---|---|---|
| `APK 1/6` | `poc_wff2_static_aod` | `wff2` (`#2` / `34`) | `73,238 B` | `a7d1235318e7b1c4af82454acccba5be2a500a35d83f0a23c496c81a41d923af` | `2b77582a27a201c96925e631f8d6cd9147d207258b6161613fee063deb62f401` (`True`) | PASS / PASS / PASS | `2,371,712 B` (`2.26 MiB`) | `2,371,712 B` (`2.26 MiB`, `layers=0`) | `[APK 1/6]` |
| `APK 2/6` | `poc_wff3_part_blend_aod` | `wff3` (`#3` / `35`) | `72,910 B` | `7a588ef13ed383c063bff225c08018f927bdc5d624aa470e735eaf981bf2ece5` | `4914c959de127803753c93609d79ed27e51006416129b6221adc3ce2331c7a5d` (`True`) | PASS / PASS / PASS | `2,371,712 B` (`2.26 MiB`) | `2,371,712 B` (`2.26 MiB`, `layers=0`) | `[APK 2/6]` |
| `APK 3/6` | `poc_wff4_continuity` | `wff4` (`#4` / `36`) | `73,574 B` | `cd2732fb26bbf3a6d22f7e459fbaba8ea4047f9b6530051005ce8c135afb8da7` | `f70f8ef90b3f3418381f1b749c8fd6ef3cb01a88dc5302008f560d045b04c582` (`True`) | PASS / PASS / PASS | `2,371,712 B` (`2.26 MiB`) | `2,371,712 B` (`2.26 MiB`, `layers=0`) | `[APK 3/6]` |
| `APK 4/6` | `poc_wff5_blend_features` | `wff5` (`#5` / `37`) | `73,574 B` | `df5de39bf7281a2887d3965f5a57007c6d37191ac7a98f9191a8fa87113b8681` | `72b280c1f5579a05460dc5ea18164fae4a3125dd8ef0825034fb013164136f47` (`True`) | PASS / PASS / PASS | `2,371,712 B` (`2.26 MiB`) | `2,371,712 B` (`2.26 MiB`, `layers=0`) | `[APK 4/6]` |
| `APK 5/6` | `poc_wff4_reference_complication` | `wff4` (`#4` / `36`) | `74,398 B` | `713dea16b5f9956b0243fcca10babff5feec8e92fd7455a2d0cc301ebee7c2e6` | `e7abd38b9c36efde20c1b40923aeed2a244750e1e0b7a5d77c2c58b4187a6f6d` (`True`) | PASS / PASS / PASS | `2,371,712 B` (`2.26 MiB`) | `2,371,712 B` (`2.26 MiB`, `layers=0`) | `[APK 5/6]` |
| `APK 6/6` | `poc_wff4_motion_triggers` | `wff4` (`#4` / `36`) | `73,658 B` | `3dd6808d06baa48024139ecf6193111d3ceae3baa8be3efe19794c13fa0291e9` | `745df3951f3d0333f3baef8e7cc2e405fa6e8cba69ff052510f6a21d7ab507d3` (`True`) | PASS / PASS / PASS | `2,371,712 B` (`2.26 MiB`) | `3,181,712 B` (`3.03 MiB`, `layers=1`) | `[APK 6/6]` |

---

## 5. 기술 결론 정리: 공식 문서 vs 공식 XSD 스키마 vs 실제 실행 증거 vs `NOT RUN` 런타임

`AG-01-R02.md` 3절 지시에 따라 각 기능 영역의 기술적 발견을 **공식 문서(Android Developers)**, **공식 XSD 스키마(`wff-validator.jar` 내장 `watchface.xsd`)**, **실제 시험 증거(로컬 실행 완료)**, **미검증 런타임(`NOT RUN`)**의 4개 층위로 구분하였다.

| 기능 영역 | [층위 1] 공식 문서 (Android Developers) | [층위 2] 공식 XSD 스키마 (`wff-validator.jar` v1.7.0 `docs.zip`) | [층위 3] 실제 시험 증거 (본 작업에서 실행·입증 완료) | [층위 4] 미실시 런타임 검증 (`NOT RUN`) |
|---|---|---|---|---|
| **1. `Variant` 기반 AOD 전환 및 보간 (WFF 2~3 vs WFF 4+)** | - WFF 4부터 `<Variant mode="AMBIENT">` 전환 애니메이션(`duration`, `startOffset`, `interpolation`, `controls`, `angleDirection`) 지원.<br>- **런타임 규칙**: `startOffset + duration > 1.0`이면 WFF 4 런타임 파서가 `startOffset`을 무시(`0.0`으로 리셋)함.<br>- WFF 2·3은 전환 속성 없이 즉시(static) 상태 전환만 지원. | - **WFF 2·3 `watchface.xsd`**: `<Variant>`에 `mode`, `target`, `value` 3개 속성만 정의됨.<br>- **WFF 4·5 `watchface.xsd`**: `duration`(`[0.0, 1.0]` `xs:float`), `startOffset`(`[0.0, 1.0]` `xs:float`), `interpolation`(`LINEAR`, `EASE_IN`, `EASE_OUT`, `EASE_IN_OUT`, `OVERSHOOT`, `CUBIC_BEZIER`), `controls`(4-float 리스트), `angleDirection`(`NONE`, `CLOCKWISE`, `COUNTER_CLOCKWISE`) 정의됨.<br>- 주의: XSD는 개별 속성이 `[0.0, 1.0]`인지만 검사하며 `startOffset + duration <= 1.0` 합산 제약은 XSD facet으로 강제하지 않음. | - `poc_wff4_continuity.xml`에서 6종 공식 `interpolation` 및 `angleDirection="CLOCKWISE"`가 WFF 4·5 스키마 검증 및 격리 APK 빌드를 통과함(`CASE 11~12`, `APK 3/6`).<br>- WFF 2·3에 `duration` 등을 포함하면 validator가 `SEVERE: Attribute 'duration' is not allowed`로 즉시 거부함(`CASE 29~30`).<br>- `duration="1.35"`와 같이 `1.0` 초과 시 validator가 `maxInclusive '1.0E0'` 위반으로 거부함(`CASE 49~52`).<br>- `startOffset + duration <= 1.0` 합산 규칙은 `test_ag01_suite.py` 단위 테스트로 정적 강제 완료. | - 실제 Wear OS 6(API 36) 렌더러에서 Active ↔ AOD 전환 시 `y`, `scaleX`, `scaleY` 보간 프레임의 시각적 연속성.<br>- 런타임 파서가 실제로 `startOffset + duration > 1.0`에서 `startOffset`을 무시하는 현상의 실기기/에뮬레이터 재현 (`NOT RUN`). |
| **2. `Reference` 및 합성 `Complication` 다중 요소 제어 (WFF 4+)** | - WFF 4에서 `<Reference name="..." source="..." defaultValue="..."/>` 도입.<br>- 동일 표현식을 `[REFERENCE.<name>]`으로 여러 요소에서 참조 가능.<br>- **런타임 규칙**: 문서 내 `name`은 고유해야 하며, 순환 참조(Circular Reference)가 발생하면 런타임에서 최초 1회 갱신 후 업데이트가 중단됨. | - **WFF 2·3 `watchface.xsd`**: `<Reference>` 엘리먼트 미정의.<br>- **WFF 4·5 `watchface.xsd`**: 허용 부모 **21종**(`Scene`, `Group`, `PartDraw`, `PartText`, `PartImage`, `PartAnimatedImage`, `Arc`, `Ellipse`, `Line`, `Rectangle`, `RoundRectangle`, `Fill`, `Stroke`, `WeightedStroke`, `LinearGradient`, `RadialGradient`, `SweepGradient`, `Font`, `BitmapFont`, `TextCircular`, `InlineImage`, `OutGlow`, `Outline`, `Shadow`), 금지 부모 **8종**(`DigitalClock`, `TimeText`, `AnalogClock`, `HourHand`, `MinuteHand`, `SecondHand`, `ComplicationSlot`, `Complication`).<br>- `<PartDraw>`는 최소 1개의 `DrawElement` 자식을 필수로 요구함(`cvc-complex-type.2.4.b`).<br>- UV 지수 소스가 WFF 4는 `[WEATHER.WEATHER.UV_INDEX]`, WFF 5는 `[WEATHER.UV_INDEX]`로 다름. | - `poc_wff4_reference_complication.xml`에서 비가시 `<Group alpha="0">` 발행자에 5개 단일 `<Reference>`를 선언하고 다중 그래픽 요소(링, 게이지, 배경 아크, 텍스트) 및 합성 `<ComplicationSlot slotId="101">` 내부에서 참조하여 WFF 4·5 validator 및 격리 APK 빌드를 통과함(`CASE 15~16`, `APK 5/6`).<br>- `<DigitalClock>` 하위에 `<Reference>`를 배치하면 validator가 `SEVERE`로 거부함을 입증(`CASE 49~52`).<br>- `<PartDraw>`에 도형 없이 `<Reference>`만 두면 실패하고 `<Group alpha="0">`에서는 통과함을 G5 리뷰(`AG01-REV-01`)에서 실증함. | - 실제 Wear OS 6+ 런타임에서 `[REFERENCE.*]` 값 변경 시 이를 구독하는 다중 그래픽 요소들의 동시 리렌더링 동기화.<br>- 순환 참조 시 최초 1회 갱신 후 멈추는 런타임 동작 및 합성 컴플리케이션 Provider 데이터 주입 시험 (`NOT RUN`). |
| **3. `AnimationController` (`Transform` / `Animation`) 및 모션 트리거** | - `<Transform target="..." value="...">` 하위의 `<Animation>`은 `value` 표현식 평가값이 변경될 때(`STEP_PERCENT`, `BATTERY_CHARGING_STATUS`, `MINUTE` 등) 이전 값에서 새 값으로 보간 애니메이션을 수행함.<br>- `<AnimatedImage>` / `<AnimatedImages>`는 `TAP`, `ON_VISIBLE`, `ON_NEXT_SECOND`, `ON_NEXT_MINUTE`, `ON_NEXT_HOUR` 이벤트 트리거를 지원함. | - `AnimationControllerType` 속성: `duration`(필수 `xs:float`), `interpolation`, `controls`, `angleDirection`, `repeat`(`xs:integer`, 기본 `0`), `fps`(`xs:integer`, 기본 `15`).<br>- `eventTriggerType` 열거형은 오직 5종(`TAP`, `ON_VISIBLE`, `ON_NEXT_SECOND`, `ON_NEXT_MINUTE`, `ON_NEXT_HOUR`)만 허용하며 `PartAnimatedImage` 계열에만 적용됨.<br>- `TimeText`의 `format` 열거형에 자리별 포맷 `hh_10`, `hh_1`, `mm_10`, `mm_1`, `ss_10`, `ss_1`이 공식 정의됨. | - `poc_wff4_motion_triggers.xml`에서 `[STEP_PERCENT]` 아크 진행(M05), `[BATTERY_CHARGING_STATUS]` 패널 확장·색상 전환(M13/M14), 자리별 `TimeText`(`hh_10`, `hh_1`, `mm_10`, `mm_1`) 컨테이너 `<Group>`의 `<Transform><Animation>`이 WFF 4·5 validator 및 격리 APK 빌드를 통과함(`CASE 19~20`, `APK 6/6`). | - 실제 런타임에서 상태 표현식 값 변경 시 `<Animation fps="30">`의 실제 프레임 드롭 여부 및 시각적 전환 품질 (`NOT RUN`). |
| **4. `Gyro` 패럴랙스 및 광학 반사 제어** | - `<Gyro>`는 손목 기울기(가속도계 각도)에 따라 부모 `Group` 또는 `Part*`의 `x`, `y`, `scaleX`, `scaleY`, `angle`, `alpha`를 실시간 변조함.<br>- AOD에서는 배터리 보호를 위해 비활성화하거나 부모 그룹을 숨겨야 함. | - `watchface.xsd`의 `<Gyro>` 속성은 일반 산술 표현식이 아니라 **`gyroArithmeticExpressionType`** 으로 제한되어, 데이터 소스로 오직 **`sensorSourceType`**(`ACCELEROMETER_IS_SUPPORTED`, `ACCELEROMETER_X`, `ACCELEROMETER_Y`, `ACCELEROMETER_Z`, `ACCELEROMETER_ANGLE_X`, `ACCELEROMETER_ANGLE_Y`, `ACCELEROMETER_ANGLE_Z`, `ACCELEROMETER_ANGLE_XY`)만 허용함(시간/날씨/레퍼런스 소스 혼합 시 스키마 거부). | - `poc_wff4_motion_triggers.xml`에서 `clamp([ACCELEROMETER_ANGLE_X], -30, 30) * 0.12` 등 `sensorSourceType`만 사용한 `<Gyro>`가 WFF 4·5 validator 및 APK 빌드를 통과함(`CASE 19~20`, `APK 6/6`). | - 실제 워치 하드웨어 또는 에뮬레이터 가상 센서에서 기울기 입력에 따른 패럴랙스 반응성 및 배터리 소모율 (`NOT RUN`). |
| **5. WFF 5 `Group` / `ComplicationSlot` `blendMode` 및 타이포그래피 확장** | - WFF 5(Wear OS 7 / API 37)에서 `<Group>` 및 `<ComplicationSlot>` 수준의 `blendMode` 합성과 텍스트·스트로크 세밀 제어 기능 추가. | - **WFF 3·4 `watchface.xsd`**: `blendMode`는 `Part*`에만 허용되며 `Group`과 `ComplicationSlot`에는 미정의.<br>- **WFF 5 `watchface.xsd`**: `<Group blendMode="...">`, `<ComplicationSlot blendMode="...">`, `<Stroke join="MITER|ROUND|BEVEL">`, `<Font minSize="...">`, `<Text lineSpacing="..." verticalAlign="...">`가 공식 추가됨. | - `poc_wff5_blend_features.xml`이 WFF 5에서 `PASSED`하고 WFF 2·3·4에서는 모두 `REJECT`됨(`CASE 21~24`, `APK 4/6`).<br>- WFF 4로 유출된 `Group blendMode`, `ComplicationSlot blendMode`, `Stroke join`, `Font minSize`가 각각의 Negative 픽스처(`CASE 37~48`)에서 100% 검출됨. | - API 37 런타임에서 `Group`/`ComplicationSlot` `blendMode` 합성 시 오프스크린 버퍼 렌더링 시각 결과 (`NOT RUN`). |

---

## 6. 자리별 시계(`poc_wff4_motion_triggers.xml`) AOD 메모리 `+810,000` bytes 증가 원인 규명 (바이트코드 분석 및 2×2 통제 변수 비교 시험)

> 원본 증거 로그: `docs/evidence/AG-01/logs/aod-memory-ablation.log`

### 6.1 문제 제기 (`AG-01-R02.md` 3절)

회차 01에서 다른 5종 PoC APK의 `maxAmbientBytes`는 모두 `2,371,712` bytes였으나, `poc_wff4_motion_triggers.xml`만 `maxAmbientBytes = 3,181,712` bytes(`+810,000` bytes 차이)로 측정되었다. 회차 01에서는 이를 "4개의 자리별 `DigitalClock` 분할에 따른 증가"로 서술했으나, 해당 XML에는 4개의 `DigitalClock`뿐만 아니라 AOD에서 숨겨지지 않은 정적 `<PartText name="ClockColon">:</PartText>`, `<Gyro>`, 4개의 `<Transform><Animation>` 등 여러 변수가 혼재되어 있었다.

### 6.2 공식 평가기(`memory-footprint.jar` v1.5.1) 바이트코드 역어셈블 수식 분석

`javap -c -p`로 `com.google.wear.watchface.dfx.memory.WatchFaceLayoutEvaluator`, `AmbientMemoryFootprintCalculator`, `AmbientMemoryFootprintCalculator$Visitor`의 바이트코드를 분석한 결과, 공식 평가기의 AOD 메모리 계산 수식은 다음과 같다:

$$\text{maxAmbientBytes} = (\text{width} \times \text{height} \times \text{numLayers} \times 4) + \text{maximumResourceUsage}$$

1. **기본 폰트 리소스 추정치 (`maximumResourceUsage = 2,371,712` bytes)**:
   - `SYNC_TO_DEVICE` 시스템 기본 폰트(Roboto)에 대해 평가기는 고정 리소스 풋프린트 `2,371,712` bytes (`2.26 MiB`)를 부여한다(`Counting resource Roboto; 2371712 bytes`).
2. **오프로드 풀스크린 레이어 단위 크기 (`450 × 450 × 4 = 810,000` bytes)**:
   - `WatchFaceLayoutEvaluator.getMemoryFootprint`는 `computeAmbientMemoryFootprint(450L, 450L)`을 호출하며, 레이어 1개당 정확히 `450 × 450 × 4 = 810,000` bytes (RGBA8888 풀스크린 버퍼 1장)를 더한다.
3. **`Visitor`가 `numLayers`를 증가시키는 정확한 조건 (`checkIfNewLayerIsRequired`)**:
   - `Visitor`는 시작 시 `numLayers = 0`, `prevNodeIsDrawnDynamically = true`, `numClocks = 0`으로 초기화된다.
   - `<Variant mode="AMBIENT" target="alpha" value="0"/>`이 선언된 노드(`ActiveDecoration` 그룹 전체)는 `VariantConfigValue.isNodeSkipped(node) == true`가 되어 서브트리 전체가 AOD 평가에서 건너뛰어진다.
   - 동적 시계 노드(`DigitalClock` 또는 `AnalogClock`)를 방문하면 `numClocks++` 후 `prevNodeIsDrawnDynamically = true`로 설정한다. **`DigitalClock` 자체는 이름이 `"Part"`로 시작하지 않으므로 `numLayers`를 증가시키지 않는다.**
   - 또한 `--apply-v1-offload-limitations` 플래그가 켜진 상태에서는 `if (numClocks > 2 && applyV1OffloadLimitations) return false;`에 의해 v1 오프로드 하드웨어 한계(최대 동적 시계 2개)를 초과하는 3번째·4번째 `DigitalClock`은 방문을 건너뛴다.
   - 반면 **AOD에서 건너뛰어지지 않은 `Part*` 노드(`PartText`, `PartDraw`, `PartImage`, `PartAnimatedImage`)를 방문할 때** `checkIfNewLayerIsRequired(node)`가 호출되어:
     ```java
     if (node.getNodeName().startsWith("Part") && this.prevNodeIsDrawnDynamically) {
         this.logger.verbose("Layer %d starts at: %s", this.numLayers + 1, WatchFaceDocuments.getNodePath(node));
         this.numLayers++;
         this.prevNodeIsDrawnDynamically = false;
     }
     ```
     에 의해 **`numLayers`가 `0`에서 `1`로 증가(`+810,000` bytes)** 한다!

### 6.3 2×2 단일 변수 통제 비교 시험(Controlled Ablation) 결과

위 바이트코드 수식을 실험적으로 검증하기 위해, `poc_wff4_motion_triggers.xml`의 `ActiveDecoration`(Gyro + 4개 Transform Animation + 날짜/배터리 텍스트)을 100% 동일하게 고정하고 **`DigitalClock` 개수(1개 vs 4개)**와 **AOD 가시 `<PartText name="ClockColon">` 유무(0개 vs 1개)**만 분리한 4종의 통제 비교 픽스처(`ablation_a` ~ `ablation_d`)를 격리 APK로 빌드하여 `memory-footprint.jar`(`--report` 및 `--verbose`)로 측정하였다(`docs/evidence/AG-01/logs/aod-memory-ablation.log`).

| 시험 ID | 통제 변수 1: `DigitalClock` 개수 | 통제 변수 2: AOD 가시 `PartText` (`ClockColon`) | XML SHA-256 (앞 16자) | 격리 APK SHA-256 (앞 16자) | 평가된 AOD `numLayers` | `maxActiveBytes` | `maxAmbientBytes` | 기준선 대비 증감 (`Delta`) | `--verbose` 레이어 시작 로그 (`aod-memory-ablation.log`) |
|---|---|---|---|---|---|---|---|---|---|
| **`ablation_a_single_clock_only`** | **1개** (`hh:mm`) | **0개** (없음) | `cc556dccfc1f870a` | `008880ab32888f52` | **`0`** | `2,371,712 B` | **`2,371,712 B`** | **`+0 B`** | `Number of layers: 0, maximumResourceUsage: 2371712` |
| **`ablation_b_four_clocks_only`** | **4개** (`hh_10`, `hh_1`, `mm_10`, `mm_1`) | **0개** (`ClockColon` 제거) | `87bfef608cbcf050` | `d3f77548320cdb6c` | **`0`** | `2,371,712 B` | **`2,371,712 B`** | **`+0 B`** | `Number of layers: 0, maximumResourceUsage: 2371712` |
| **`ablation_c_single_clock_plus_parttext`** | **1개** (`hh:mm`) | **1개** (`ClockColon` AOD 노출) | `dc6bab7f94fe3236` | `8fb7d10449eed27d` | **`1`** | `2,371,712 B` | **`3,181,712 B`** | **`+810,000 B`** | `Layer 1 starts at: .../FluidClockContainer/PartText name = "ClockColon"` |
| **`ablation_d_four_clocks_plus_ambient_hidden_parttext`** | **4개** (`hh_10`, `hh_1`, `mm_10`, `mm_1`) | **0개** (`ClockColon`에 `AMBIENT alpha=0` 부여) | `ad22841911a99525` | `6ef78d02866774cc` | **`0`** | `2,371,712 B` | **`2,371,712 B`** | **`+0 B`** | `Number of layers: 0, maximumResourceUsage: 2371712` |
| (기준선 1) `poc_wff4_continuity` | **1개** (`hh:mm`) | **0개** (없음) | `f70f8ef90b3f3418` | `cd2732fb26bbf3a6` | **`0`** | `2,371,712 B` | **`2,371,712 B`** | **`+0 B`** | `Number of layers: 0, maximumResourceUsage: 2371712` |
| (기준선 2) `poc_wff4_motion_triggers` | **4개** (`hh_10`, `hh_1`, `mm_10`, `mm_1`) | **1개** (`ClockColon` AOD 노출) | `745df3951f3d0333` | `3dd6808d06baa480` | **`1`** | `2,371,712 B` | **`3,181,712 B`** | **`+810,000 B`** | `Layer 1 starts at: .../FluidClockContainer/PartText name = "ClockColon"` |

### 6.4 인과 결론 및 후속 설계 가이드

1. **`DigitalClock` 분할(1개 → 4개)의 단독 AOD 메모리 증감 효과는 `0` bytes이다** (`ablation_a` vs `ablation_b` 모두 `2,371,712` bytes).
2. **`+810,000` bytes 증가의 100% 단일 원인은 AOD에서 숨겨지지 않은 정적 `<PartText name="ClockColon">` 1개이다** (`ablation_a` → `ablation_c`에서 단일 시계임에도 `PartText` 콜론 1개를 추가하자 정확히 `+810,000` bytes 증가하며, `poc_wff4_motion_triggers`에서 `ClockColon`에 `<Variant mode="AMBIENT" target="alpha" value="0"/>`만 추가한 `ablation_d`에서는 4개 시계를 유지한 채로 즉시 `2,371,712` bytes로 복귀함).
3. **v1 오프로드 렌더러의 동적 시계 개수 제약 주의**:
   - `AmbientMemoryFootprintCalculator$Visitor` 바이트코드에서 확인되었듯 `--apply-v1-offload-limitations` 모드(v1 오프로드 코프로세서)는 AOD에서 최대 **2개**의 동적 시계(`numClocks <= 2`)만 오프로드할 수 있다. 따라서 제품 워치 페이스에서 4자리 분할 시계(`hh_10`, `hh_1`, `mm_10`, `mm_1`)를 사용할 경우, 활성(Active) 모드에서만 4자리 분할 시계를 표시하고 AOD(`AMBIENT`) 진입 시에는 `<Variant mode="AMBIENT" target="alpha" value="0"/>`으로 숨기거나 단일 `<DigitalClock>`(`format="hh:mm"`)을 사용하는 아키텍처가 권장된다.

---

## 7. Wear OS 에뮬레이터 시험 요구 환경 조사 및 재현 방법

> 원본 증거 로그: `docs/evidence/AG-01/logs/environment-and-emulator.log`

사용자 승인 없는 신규 SDK 다운로드 및 실기기 변경 금지 규정을 준수하여, 로컬 설치 상태와 Google SDK 원격 카탈로그(`sdkmanager.bat --list`, 읽기 전용 조회)를 조사하였다.

### 7.1 현재 로컬 환경 상태

- **Android SDK 경로**: `C:\Users\scarl\AppData\Local\Android\Sdk`
- **가용 디스크 여유 공간**: **`93.88 GiB`**
- **설치된 에뮬레이터/하이퍼바이저**: Android Emulator `36.4.9`, Android Emulator Hypervisor Driver `2.2.0`, Platform-Tools `36.0.2` 설치 완료
- **현재 설치된 시스템 이미지**: `system-images;android-36.1;google_apis_playstore;x86_64` (일반 폰/태블릿용 이미지 1종만 존재, **Wear OS 시스템 이미지 0종**)
- **현재 생성된 AVD 및 연결된 ADB 기기**: 일반 폰용 AVD `Medium_Phone_API_36.1` 1개만 존재하며 **Wear OS AVD는 `0`개**, 연결된 ADB 기기는 `0`대(`adb devices -l` 빈 출력)

### 7.2 Wear OS 에뮬레이터 시험에 필요한 공식 SDK 시스템 이미지 패키지 (`sdkmanager --list` 확인 완료)

> **핵심 발견**: Google SDK 저장소에서 API 34·35 Wear OS 이미지는 태그가 `android-wear`이지만, **API 36(Wear OS 6 / WFF 4) 및 API 37(Wear OS 7 / WFF 5) Wear OS 이미지는 태그가 `android-wear-signed`** 로 등록되어 있다.

| 대상 WFF 버전 | 대상 API 레벨 | Wear OS 버전 | 정확한 `sdkmanager` 패키지 식별자 (`x86_64` 호스트 기준) | 리비전 | 예상 설치/AVD 디스크 소요량 | 우선순위 |
|---|---|---|---|---|---|---|
| **WFF 4 (핵심)** | **API 36.0** | Wear OS 6.0 (signed) | `system-images;android-36;android-wear-signed;x86_64` | `rev 1` | 다운로드 `~0.9 GiB` / 압축 해제+AVD `~3.0 GiB` | **P0 (필수: Variant 보간, Reference, Gyro)** |
| **WFF 5 (핵심)** | **API 37.0** | Wear OS 7.0 (signed) | `system-images;android-37.0;android-wear-signed;x86_64` | `rev 1` | 다운로드 `~1.0 GiB` / 압축 해제+AVD `~3.2 GiB` | **P0 (필수: Group/ComplicationSlot blendMode)** |
| WFF 4 (보조) | API 36.1 | Wear OS 6.1 (signed) | `system-images;android-36.1;android-wear-signed;x86_64` | `rev 1` | 다운로드 `~0.9 GiB` / 압축 해제+AVD `~3.0 GiB` | P2 (선택: 6.1 마이너 호환성) |
| WFF 3 (하위 호환) | API 35 (ext15) | Wear OS 5.1 | `system-images;android-35-ext15;android-wear;x86_64` | `rev 1` | 다운로드 `~0.8 GiB` / 압축 해제+AVD `~2.8 GiB` | P1 (권장: WFF 3 Part blendMode 및 정적 AOD) |
| WFF 2 (하위 호환) | API 34 | Wear OS 5.0 | `system-images;android-34;android-wear;x86_64` | `rev 1` | 다운로드 `~0.8 GiB` / 압축 해제+AVD `~2.6 GiB` | P1 (권장: WFF 2 최소 baseline 정적 AOD) |

- **총 예상 저장 공간**:
  - **최소 핵심 구성 (WFF 4 + WFF 5 이미지 2종 + AVD 2개)**: 약 **`6.2 GiB`** (현재 여유 공간 `93.88 GiB`의 6.6%)
  - **전체 호환성 구성 (WFF 2·3·4·5 이미지 4종 + AVD 4개)**: 약 **`11.6 GiB`** (현재 여유 공간 `93.88 GiB`의 12.4%)

### 7.3 로컬 `avdmanager`에서 사용 가능한 공식 Wear OS 디바이스 프로필 4종

| 프로필 ID (`-d` 인자) | 숫자 ID | OEM / Tag | 화면 형태 및 AURA Ultra 시험 용도 |
|---|---|---|---|
| **`wearos_large_round`** | `59` | Google / `android-wear` | **주 시험 타깃**: `450×450` 원형 캔버스 기준 활성/AOD 전환 및 연속 모션 렌더링 검증 |
| **`wearos_small_round`** | `61` | Google / `android-wear` | 소형 원형 디스플레이 DPI 다운스케일링 및 `Font minSize` 가독성 검증 |
| `wearos_square` | `62` | Google / `android-wear` | 정사각형 화면 레이아웃 클리핑 여부 확인 |
| `wearos_rect` | `60` | Google / `android-wear` | 직사각형 화면 레이아웃 클리핑 여부 확인 |

### 7.4 승인 후 즉시 실행 가능한 에뮬레이터 설치 및 런타임 검증 재현 명령

```powershell
# 1. Wear OS 6.0 (API 36, WFF 4) 및 Wear OS 7.0 (API 37, WFF 5) 시스템 이미지 설치 (사용자 승인 후 실행)
& "$env:LOCALAPPDATA\Android\Sdk\cmdline-tools\latest\bin\sdkmanager.bat" `
  "system-images;android-36;android-wear-signed;x86_64" `
  "system-images;android-37.0;android-wear-signed;x86_64"

# 2. 원형 Wear OS AVD 생성 (wearos_large_round 프로필)
echo "no" | & "$env:LOCALAPPDATA\Android\Sdk\cmdline-tools\latest\bin\avdmanager.bat" create avd `
  -n aura_wear36_round -k "system-images;android-36;android-wear-signed;x86_64" -d wearos_large_round --force
echo "no" | & "$env:LOCALAPPDATA\Android\Sdk\cmdline-tools\latest\bin\avdmanager.bat" create avd `
  -n aura_wear37_round -k "system-images;android-37.0;android-wear-signed;x86_64" -d wearos_large_round --force

# 3. 격리 에뮬레이터 부팅 및 PoC APK 설치·렌더링·AOD 전환 캡처
& "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -avd aura_wear36_round -no-snapshot -no-boot-anim
adb wait-for-device
adb install -r watchface-wff4-debug.apk
adb exec-out screencap -p > docs/evidence/AG-01/active_wff4.png
adb shell screenrecord --time-limit 5 /sdcard/aod_transition_wff4.mp4
adb shell input keyevent KEYCODE_SLEEP
adb exec-out screencap -p > docs/evidence/AG-01/ambient_wff4.png
adb pull /sdcard/aod_transition_wff4.mp4 docs/evidence/AG-01/aod_transition_wff4.mp4
```

---

## 8. 정확성 및 재현 명령 검증 결과

| 실행 명령 | 결과 | 원본 로그 / 검증 대상 |
|---|---|---|
| `python -m unittest discover -s tests/compatibility/ag-01 -p "test_*.py" -v` | **PASS** (12 tests, 60 validator subTests, 0 failures) | 6종 PoC, 7종 Negative, 4종 Ablation 구조 및 공식 validator 매트릭스 |
| `python tests/compatibility/ag-01/run_ag01_verification.py --mode schema --logs-dir docs/evidence/AG-01/logs` | **PASS** (52/52 cases expected verdict) | `docs/evidence/AG-01/logs/schema-matrix-52.log` |
| `python tests/compatibility/ag-01/run_ag01_verification.py --mode apk --logs-dir docs/evidence/AG-01/logs` | **PASS** (6/6 isolated APKs built & verified) | `docs/evidence/AG-01/logs/isolated-apk-verification.log` |
| `python tests/compatibility/ag-01/run_ag01_verification.py --mode ablation --logs-dir docs/evidence/AG-01/logs` | **PASS** (6/6 ablation & baseline APKs verified) | `docs/evidence/AG-01/logs/aod-memory-ablation.log` |
| `python tests/compatibility/ag-01/run_ag01_verification.py --mode emulator --logs-dir docs/evidence/AG-01/logs` | **NOT RUN** (환경 조사 및 로그 기록 완료) | `docs/evidence/AG-01/logs/environment-and-emulator.log` |
| `python -m unittest discover -s tests/unit -p "test_*.py"` | **PASS** (40 tests in 0.041s) | 저장소 기존 단위 테스트 회귀 이상 없음 |
| `python tools/check_foundation.py` | **PASS** | 저장소 기본 계약 및 불변성 회귀 이상 없음 |

---

## 9. 품질 게이트 (G0~G7) 및 G5 별도 자기 재검토

### 9.1 G5 구현 후 별도 코드 및 증거 재검토 기록

| 검토 ID | 발견 단계 | 결함 또는 잠재 문제 | 원인 분석 | 수정 조치 및 재검증 결과 |
|---|---|---|---|---|
| `AG01-R02-REV-01` | 회차 02 G5 코드 재검토 | `test_controlled_ablation_fixtures_isolate_clock_count_and_aod_parttext`에서 `ET.tostring()` 문자열 단순 비교 시 XML 주석 제거 위치의 들여쓰기 공백(`tail`) 차이로 인해 구조적으로 동일한 `ActiveDecoration`이 불일치로 판정됨. | `ElementTree.parse()`는 주석 노드를 제거하지만 주석 뒤의 줄바꿈/공백 텍스트(`tail`)는 부모/이전 형제 노드에 남겨 두기 때문. | 태그명, 정렬된 속성 목록, 공백 제거된 의미 텍스트, 자식 트리를 재귀 튜플로 비교하는 `canonical_tree(elem)`를 도입하여 의미 있는 텍스트(`Template`, `:` 등)와 속성은 100% 검증하면서 주석 공백 차이만 정규화함. 재실행 결과 12개 테스트 전수 `PASS`. |
| `AG01-R02-REV-02` | 회차 02 G5 로그 재검토 | 샌드박스 모드에서 `--mode emulator` 실행 시 `adb.exe`가 사용자 홈(`~/.android`) 접근 권한 거부 메시지를 `ADB Note`에 남김. | 샌드박스가 워크스페이스 외부(`~/.android`) 디렉터리 생성을 차단함. | `adb devices -l` 조회를 수행하는 `--mode emulator`를 승인된 호스트 권한으로 재실행하여 실제 연결 기기 `0`대(`ADB Note: ` 공란) 상태를 `environment-and-emulator.log`에 정확히 기록함. |

### 9.2 G0~G7 판정 요약

- **G0 (사전 절차 및 경계 확인)**: `PASS` — 최신 `origin/main` (`b5dd320c0718f9451b9749637c83db22584664b0`) 기준 `AGENTS.md`, `AG-01-R02.md` 확인 완료. 허용 경로 외 수정 `0`건.
- **G1 (스키마 및 정적 계약 검증)**: `PASS` — 52건 공식 validator 매트릭스 + 4종 Ablation WFF 4·5 스키마 검증 완료(`schema-matrix-52.log`).
- **G2 (테스트 및 음성 검출 검증)**: `PASS` — 12개 `unittest` 메서드(60개 validator subTests) 및 7종 Negative 픽스처 거부 검증 통과.
- **G3 (격리 APK 클린 빌드 및 패키징 검증)**: `PASS` — 6종 PoC APK + 4종 Ablation APK 모두 격리 임시 폴더에서 Clean Build, 리소스 전용, Manifest, XML SHA-256 일치, `apksigner` v2 서명 검증 통과(`isolated-apk-verification.log`).
- **G4 (메모리 예산 및 통제 변수 비교 검증)**: `PASS` — 모든 APK가 Active `<= 70 MiB`, Ambient `<= 7 MiB` 통과. 2×2 통제 비교 시험 및 바이트코드 역어셈블로 `+810,000` bytes 원인이 AOD 가시 `PartText` 콜론의 풀스크린 레이어(`450×450×4`) 할당임을 완벽히 규명(`aod-memory-ablation.log`).
- **G5 (구현 후 별도 자기 재검토)**: `PASS` — 위 9.1절의 2건 발견 및 즉시 수정·재검증 완료.
- **G6 (런타임/에뮬레이터 검증 및 정직한 보고)**: `NOT RUN` (정직한 기록으로 게이트 조건 충족) — 미설치된 Wear OS 시스템 이미지(`android-wear-signed` / `android-wear`) 및 승인 전 다운로드 금지 규정에 따라 `NOT RUN`으로 기록하고 정확한 패키지 식별자·용량·재현 명령을 제공함(`environment-and-emulator.log`).
- **G7 (문서화 및 원격 전달)**: `PASS` — 기존 `REPORT.md` 보존, `REPORT-02.md` 및 `logs/*.log` 4종 작성, `origin/agent/antigravity/AG-01` 푸시 및 `main` 대상 PR 생성 완료.

---

## 10. 중앙 운영 문서 갱신 제안 (`docs/STATUS.md`, `docs/operations/WORK_LOG.md`, `docs/operations/BLOCKERS.md`)

> 본 브랜치에서는 중앙 운영 문서를 직접 수정하지 않으며, 통합 담당 에이전트가 `main` 반영 시 아래 내용을 사용할 수 있도록 제안한다.

1. **`docs/STATUS.md` 갱신 제안**:
   - `AG-01` 상태를 `회차 02 완료 (원격 브랜치 agent/antigravity/AG-01 푸시 및 PR 생성 완료, 52건 스키마·6개 PoC APK·4개 AOD 메모리 통제 비교 APK 원본 로그 영속화 완료; 에뮬레이터 런타임 렌더링은 Wear OS 시스템 이미지 설치 승인 대기 NOT RUN)`으로 갱신.
2. **`docs/operations/WORK_LOG.md` 추가 제안**:
   - `2026-04-20 | AG-01 (R02) | Antigravity | agent/antigravity/AG-01 원격 푸시 및 PR 생성, docs/evidence/AG-01/logs/ 원본 증거 로그 4종 영속화, 공식 문서/XSD/실제 시험 증거 분리, 2x2 통제 변수 비교 시험으로 AOD +810,000 bytes 원인이 DigitalClock 분할이 아닌 AOD 가시 PartText 콜론의 풀스크린 RGBA8888 레이어(450x450x4) 할당임을 규명, Wear OS 에뮬레이터 패키지(system-images;android-36;android-wear-signed;x86_64 등) 요구사항 조사 완료 (REPORT-02.md)`.
3. **`docs/operations/BLOCKERS.md` 갱신 제안**:
   - `BLK-AG01-EMULATOR`: 로컬 Android SDK에 Wear OS 시스템 이미지(`system-images;android-36;android-wear-signed;x86_64`, `system-images;android-37.0;android-wear-signed;x86_64` 등, 2종 약 `6.2 GiB` / 4종 약 `11.6 GiB`, 가용 디스크 `93.88 GiB`)가 설치되어 있지 않음. 사용자 승인 후 7.4절의 `sdkmanager` 및 `avdmanager` 명령을 실행하면 즉시 에뮬레이터 렌더링 및 AOD 전환 캡처 시험 가능.
