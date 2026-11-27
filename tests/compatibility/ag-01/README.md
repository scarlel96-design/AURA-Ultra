# AG-01 WFF 2–5 호환성, 모션 연속성 PoC 및 Wear OS 런타임 안전 검증 스위트

이 디렉터리는 `docs/operations/agent-orders/AG-01.md`, `AG-01-R02.md`, `AG-01-R03.md` 작업지시서에 따라 WFF 2·3·4·5 호환성 PoC, 단일 변수 통제 비교(Ablation) 픽스처, 음성(Negative) 검출 픽스처, 실시간 SDK/AVD 환경 조사기, 안전한 Wear OS 에뮬레이터 런타임 검증 절차를 포함한다.

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
  - 강화된 `require_rejection`: `returncode == 0`, 공식 배너, `0 PASSED`, 정확한 대상 XML 경로 및 WFF 버전의 명시적 `FAILED` 1건, `[Line:Column] SEVERE` 진단 포함 여부 검증.
  - 실시간 `sdkmanager --list`, `avdmanager list device`, `avdmanager list avd`, `emulator -list-avds`, `adb devices -l` 조회·파싱 및 하드코딩 추정 후보(`ESTIMATED_WEAR_IMAGE_CANDIDATES`) 분리 대조, 일반 폰 AVD/물리 기기 제외, `READY`/`NOT RUN`/`UNKNOWN` 엄격 판정.
- `wear_emulator_runtime.py`: 실제 Wear OS AVD만 대상으로 하는 안전한 설치, 워치 페이스 선택 확인(`dumpsys wallpaper`), Active/AOD 상태 확인(`dumpsys power`/`display`), 전환 영상 녹화(`screenrecord`) 및 스크린샷 캡처 절차(`--force` 금지, `-s <emulator-serial>` 강제, 물리 기기 및 폰 AVD 차단).
- `test_ag01_suite.py`: 구조 불변성, 강화된 `require_rejection` 실패 탐지, 에뮬레이터 환경 파싱/오류/분리, 런타임 안전장치, 그리고 68건 공식 validator subtests를 검증하는 자동 회귀 테스트 스위트.

## 실행 방법

```bash
# 1. AG-01 전체 단위 및 공식 스키마 매트릭스 회귀 테스트 (68 validator subtests 포함)
python -m unittest discover -s tests/compatibility/ag-01 -p "test_*.py" -v

# 2. 엄격한 60건 스키마 매트릭스 및 실시간 에뮬레이터 환경 조사 로그 생성 (회차 03 새 로그 경로)
python tests/compatibility/ag-01/run_ag01_verification.py --mode schema --logs-dir docs/evidence/AG-01/logs-r03
python tests/compatibility/ag-01/run_ag01_verification.py --mode emulator --logs-dir docs/evidence/AG-01/logs-r03

# 3. 안전한 Wear OS 런타임 검증 실행 계획 출력 (승인 전 무변경 dry-run)
python tests/compatibility/ag-01/wear_emulator_runtime.py --plan-only --serial emulator-5554 --apk watchface-wff4-debug.apk --package-id io.github.scarlel96.aura.watchface.wff4 --wff-version 4 --out-dir docs/evidence/AG-01/runtime-wff4
```
