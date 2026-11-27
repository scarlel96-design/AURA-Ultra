# AG-01 WFF 2–5 호환성, 모션 연속성 PoC 및 Wear OS 런타임 안전 검증 스위트

이 디렉터리는 `docs/operations/agent-orders/AG-01.md`, `AG-01-R02.md`, `AG-01-R03.md`, `AG-01-R04.md` 작업지시서에 따라 WFF 2·3·4·5 호환성 PoC, 단일 변수 통제 비교(Ablation) 픽스처, 음성(Negative) 검출 픽스처, 실시간 SDK/AVD 환경 조사기, 안전한 Wear OS 에뮬레이터 런타임 검증 절차를 포함한다.

## 디렉터리 구조

- `fixtures/wff2/poc_wff2_static_aod.xml`: WFF 2 정적 AOD 대체, 단일 `DigitalClock`/`TimeText` 객체 유지, 결측 날씨 데이터 `--` 대체.
- `fixtures/wff3/poc_wff3_part_blend_aod.xml`: WFF 3 정적 AOD 대체 + `PartDraw`/`PartText` 수준 `blendMode`.
- `fixtures/wff4/poc_wff4_continuity.xml`: WFF 4 `<Variant mode="AMBIENT">` 단계적 보간(6종 공식 `interpolation` 전체 포함) 및 단일 시계 연속 모션.
- `fixtures/wff4/poc_wff4_reference_complication.xml`: WFF 4 `<Reference>` 단일 발행자 패턴 및 합성 `<ComplicationSlot>`/`<Complication>` 다중 요소 제어.
- `fixtures/wff4/poc_wff4_motion_triggers.xml`: WFF 4 `<Gyro>`(`sensorSourceType` 전용), 자리별 `TimeText`(`hh_10`, `hh_1`, `mm_10`, `mm_1`) 컨테이너 모션, `<Transform><Animation>`.
- `fixtures/wff5/poc_wff5_blend_features.xml`: WFF 5 `<Group blendMode>`, `<ComplicationSlot blendMode>`, `<Stroke join>`, `<Font minSize>`, `<Text lineSpacing>`.
- `fixtures/ablation/*.xml`: `DigitalClock` 개수(1 vs 4)와 AOD 가시 `<PartText name="ClockColon">`(0 vs 1)을 2×2로 분리한 AOD 메모리 통제 비교 픽스처 4종.
- `fixtures/negative/*.xml`:
  - 기존 7종(회차 01·02 52건 매트릭스 보존용)
  - 회차 03 추가 분리 2종(`neg_wff4_variant_duration_out_of_range.xml`, `neg_wff4_reference_invalid_parent.xml` — `AG01-AUD-02` 단일 결함 분리 검증)
- `run_ag01_verification.py`:
  - 최신 `main` 공식 도구 pin(`wff-validator.jar` SHA-256 `6ef308dbc306a9187b5b1f4997a662eb57e26ac3650cebbf2ab583cd38bb609e`, `memory-footprint.jar` SHA-256 `1ec683365aee86627f0eb502b52fc71f71eff1872776edc5bc6ef7c7b37d28bc`) 검증.
  - 강화된 `require_rejection`: `returncode == 0`, 공식 배너, `0 PASSED`, 정확한 대상 XML 경로 및 WFF 버전의 명시적 `FAILED` 1건, `[Line:Column] SEVERE` 진단 포함 여부 검증.
  - 실시간 `sdkmanager --list`, `avdmanager list device`, `avdmanager list avd`, `emulator -list-avds`, `adb devices -l` 조회·파싱 및 하드코딩 추정 후보(`ESTIMATED_WEAR_IMAGE_CANDIDATES`) 분리 대조, 일반 폰 AVD/물리 기기 제외, `READY`/`NOT RUN`/`UNKNOWN` 엄격 판정.
- `wear_emulator_runtime.py`:
  - 변경 전 로컬 APK(SHA-256, 리소스 전용, 컴파일된 Manifest `package`/`WFF version`/`minSdk`) 및 실행 에뮬레이터(승인된 전용 Wear AVD 이름, `watch` 특성, API 레벨) 사전 검증.
  - `AG01-AUD-04` 수정: 현재 사용자 활성 `mWallpaperComponent=ComponentInfo{<pkg>/<cls>}` 정확 일치 검증(비활성 `previousPackage`, `.other` suffix 충돌, 미확인 WFF 호스트 형식 거부) 및 `Awake+ON` / `Dozing+DOZE|DOZE_SUSPEND` 엄격 판정(`UNKNOWN` display, `Dozing+OFF` 거부).
  - 모든 ADB 명령 종료 코드(`rc==0`)·타임아웃 검증, MP4 `ftyp` 헤더 검증, 최종 `Awake+ON` 복귀 확인 및 `finally` 정리/복구 보장.
- `test_ag01_suite.py`: 25개 단위 테스트 메서드(68건 공식 validator subtests + `AG01-AUD-04` 오판 4종 재현·차단 + 런타임 실패 픽스처 포함).

## 실행 방법

```bash
# 1. AG-01 전체 단위 및 공식 스키마 매트릭스 회귀 테스트 (25 tests, 68 validator subtests)
python -m unittest discover -s tests/compatibility/ag-01 -p "test_*.py" -v

# 2. 최신 공식 도구 pin 기준 전체 검증 및 회차 04 원본 로그 생성
python tests/compatibility/ag-01/run_ag01_verification.py --mode all --logs-dir docs/evidence/AG-01/logs-r04

# 3. 안전한 Wear OS 런타임 검증 실행 계획 출력 (승인 전 무변경 dry-run)
python tests/compatibility/ag-01/wear_emulator_runtime.py --plan-only --serial emulator-5554 --avd-name aura_wear36_round --apk watchface-wff4-debug.apk --package-id io.github.scarlel96.aura.watchface.wff4 --wff-version 4 --out-dir docs/evidence/AG-01/runtime-wff4
```
