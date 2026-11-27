# AG-01 WFF 2–5 호환성, 모션 연속성 PoC 및 Wear OS 런타임 안전 검증 스위트

이 디렉터리는 `docs/operations/agent-orders/AG-01.md` ~ `AG-01-R04.md` 및 회차 05~06 보완 지시(`AG01-AUD-05` ~ `AG01-AUD-09`)에 따라 WFF 2·3·4·5 호환성 PoC, 단일 변수 통제 비교(Ablation) 픽스처, 음성(Negative) 검출 픽스처, 실시간 SDK/AVD 환경 조사기, 안전한 Wear OS 에뮬레이터 런타임 검증 절차를 포함한다.

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
  - 현재 사용자(`mCurrentUserId`) 바인딩 부재 시 타 사용자 fallback 차단(`UNKNOWN`), Active·AOD 캡처 전후 및 최종 복귀 시점의 활성 워치 페이스·화면 상태 6개 체크포인트 검증(`AG01-AUD-08`).
  - `dumpsys power` 및 `dumpsys display`에서 디스플레이 ID별 상태를 명시적으로 대응하고 중복 관측을 타 디스플레이 상태로 오인하지 않으며, 대상 디스플레이(기본 `0`) 미확정 또는 상충 시 `UNKNOWN` 판정(`AG01-AUD-05`).
  - ISO/IEC 15948 PNG 입력 크기·해상도·압축 해제 크기 상한, `zlib.decompressobj()` `eof`/`unused_data`/`unconsumed_tail`, 미지원 인터레이스(`interlace != 0`) 및 비연속 `IDAT`/알 수 없는 critical·APNG 청크 거부(`AG01-AUD-06`).
  - ISO BMFF MP4 박스 구조(`ftyp`, `moov`, `mdat`, `trak/mdia/hdlr(vide)`, `stsd`/`stsz`/`stco|co64`) 검증 및 `ffprobe` 기반 실제 디코딩 프레임 검증(검증 도구 부재 시 `NOT RUN`, `AG01-AUD-07`).
  - 최초 기기 상태 변경 명령부터 단일 `try/finally` 복구 범위 적용, 녹화 프로세스 생성 실패·캡처 실패 복구 및 기존 증거 파일 덮어쓰기 금지(`EvidenceOverwriteError`, `AG01-AUD-09`).
- `test_ag01_suite.py`: 33개 단위 테스트 메서드(기존 28개 + 회차 06 결함 재현 5개, 68건 공식 validator subtests 포함).

## 실행 방법

```bash
# 1. AG-01 전체 단위 및 공식 스키마 매트릭스 회귀 테스트 (33 tests, 68 validator subtests)
python -m unittest discover -s tests/compatibility/ag-01 -p "test_*.py" -v

# 2. 최신 공식 도구 pin 기준 60건 스키마 매트릭스 검증
python tests/compatibility/ag-01/run_ag01_verification.py --mode schema --logs-dir docs/evidence/AG-01/logs-r06
```
