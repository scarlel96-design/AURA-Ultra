# AG-01 WFF 2–5 호환성, 모션 연속성 PoC 및 Wear OS 런타임 안전 검증 스위트

이 디렉터리는 `docs/operations/agent-orders/AG-01.md` ~ `AG-01-R04.md` 및 회차 05 보완 지시에 따라 WFF 2·3·4·5 호환성 PoC, 단일 변수 통제 비교(Ablation) 픽스처, 음성(Negative) 검출 픽스처, 실시간 SDK/AVD 환경 조사기, 안전한 Wear OS 에뮬레이터 런타임 검증 절차를 포함한다.

## 디렉터리 구조

- `fixtures/wff2/poc_wff2_static_aod.xml`: WFF 2 정적 AOD 대체, 단일 `DigitalClock`/`TimeText` 객체 유지, 결측 날씨 데이터 `--` 대체.
- `fixtures/wff3/poc_wff3_part_blend_aod.xml`: WFF 3 정적 AOD 대체 + `PartDraw`/`PartText` 수준 `blendMode`.
- `fixtures/wff4/poc_wff4_continuity.xml`: WFF 4 `<Variant mode="AMBIENT">` 단계적 보간(6종 공식 `interpolation` 전체 포함) 및 단일 시계 연속 모션.
- `fixtures/wff4/poc_wff4_reference_complication.xml`: WFF 4 `<Reference>` 단일 발행자 패턴 및 합성 `<ComplicationSlot>`/`<Complication>` 다중 요소 제어.
- `fixtures/wff4/poc_wff4_motion_triggers.xml`: WFF 4 `<Gyro>`(`sensorSourceType` 전용), 자리별 `TimeText`(`hh_10`, `hh_1`, `mm_10`, `mm_1`) 컨테이너 모션, `<Transform><Animation>`.
- `fixtures/wff5/poc_wff5_blend_features.xml`: WFF 5 `<Group blendMode>`, `<ComplicationSlot blendMode>`, `<Stroke join>`, `<Font minSize>`, `<Text lineSpacing>`.
- `fixtures/ablation/*.xml`: `DigitalClock` 개수(1 vs 4)와 AOD 가시 `<PartText name="ClockColon">`(0 vs 1)을 2×2로 분리한 AOD 메모리 통제 비교 픽스처 4종.
- `fixtures/negative/*.xml`: 기존 7종 + 회차 03 단일 결함 분리 2종(`neg_wff4_variant_duration_out_of_range.xml`, `neg_wff4_reference_invalid_parent.xml`).
- `run_ag01_verification.py`: 최신 `main` 공식 도구 pin(`wff-validator.jar` `6ef308db...`, `memory-footprint.jar` `1ec68336...`) 검증, 엄격한 `require_rejection`, 실시간 SDK/AVD/ADB 조회 및 후보 분리.
- `wear_emulator_runtime.py`:
  - 현재 사용자(`mCurrentUserId`) 바인딩 부재 시 타 사용자 fallback 차단(`UNKNOWN`), 사용자 헤더 유무 불일치·상충 사용자 ID 차단(`UNKNOWN`), 비활성 참조·suffix 충돌·미확인 WFF 호스트 차단.
  - `dumpsys power` 및 `dumpsys display` 전수 스캔으로 복수 디스플레이 상충·상충 `mWakefulness`·비정합 조합(`Awake+DOZE`, `Dozing+ON`) 차단(`UNKNOWN`).
  - ISO/IEC 15948 PNG 전체 구조 및 무결성 검증(`validate_png_bytes`: 8B 시그니처, 전 청크 CRC-32, `IHDR`, `IDAT` zlib 압축 해제 및 스캔라인 길이, `IEND`, trailing bytes 0).
  - 실패 복구 경로의 ADB 종료 코드·타임아웃, 녹화 프로세스 강제 종료·대기(`kill`+`wait`), 최종 `Awake+ON` 복귀 확인, 원격 `rm -f` + `test ! -e` 삭제 확인 및 `RecoveryFailureError` 전파.
- `test_ag01_suite.py`: 28개 단위 테스트 메서드(기존 25개 + 회차 05 결함 재현 3개, 68건 공식 validator subtests 포함).

## 실행 방법

```bash
# 1. AG-01 전체 단위 및 공식 스키마 매트릭스 회귀 테스트 (28 tests, 68 validator subtests)
python -m unittest discover -s tests/compatibility/ag-01 -p "test_*.py" -v

# 2. 최신 공식 도구 pin 기준 60건 스키마 매트릭스 검증
python tests/compatibility/ag-01/run_ag01_verification.py --mode schema --logs-dir docs/evidence/AG-01/logs-r05
```
