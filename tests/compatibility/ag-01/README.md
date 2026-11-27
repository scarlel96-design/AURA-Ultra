# AG-01 WFF 2–5 호환성 및 모션 연속성 PoC 검증 스위트

이 디렉터리는 `docs/operations/agent-orders/AG-01.md` 및 `docs/operations/agent-orders/AG-01-R02.md` 작업지시서에 따라 AURA Ultra의 고급 그래픽 및 연속 모션 구현에 필요한 WFF 2·3·4·5 기술 지원 범위와 스키마 제약을 독립적으로 검증하기 위한 PoC XML, 통제 변수 비교(Ablation) XML, 음성(Negative) 검출 픽스처 및 자동화 검증 스크립트를 포함한다.

## 디렉터리 구조

- `fixtures/wff2/poc_wff2_static_aod.xml`: WFF 2 정적 AOD 대체(`duration`/`startOffset`/`interpolation` 미사용), 단일 `DigitalClock`/`TimeText` 객체 유지, 결측 날씨 데이터 `--` 대체.
- `fixtures/wff3/poc_wff3_part_blend_aod.xml`: WFF 3 정적 AOD 대체 + `PartDraw`/`PartText` 수준 `blendMode="SCREEN"` / `"SRC_OVER"`.
- `fixtures/wff4/poc_wff4_continuity.xml`: WFF 4 `<Variant mode="AMBIENT">` 단계적 보간(`duration`, `startOffset`, `startOffset + duration <= 1.0`), 공식 6종 `interpolation`(`LINEAR`, `EASE_IN`, `EASE_OUT`, `EASE_IN_OUT`, `OVERSHOOT`, `CUBIC_BEZIER` + `controls`), `angleDirection="CLOCKWISE"`, 단일 `DigitalClock`/`TimeText` 연속 모션.
- `fixtures/wff4/poc_wff4_reference_complication.xml`: WFF 4 `<Reference>` 단일 발행자(Publisher) 패턴 및 합성 `<ComplicationSlot>`/`<Complication>` 데이터 기반 다중 그래픽 요소 동시 제어.
- `fixtures/wff4/poc_wff4_motion_triggers.xml`: WFF 4 `<Gyro>`(`sensorSourceType` 가속도계 표현식 전용), 공식 자리별 `TimeText` 포맷(`hh_10`, `hh_1`, `mm_10`, `mm_1`) 컨테이너 모션, 상태 표현식 기반 `<Transform><Animation>` 트리거.
- `fixtures/wff5/poc_wff5_blend_features.xml`: WFF 5 `<Group blendMode>` 및 `<ComplicationSlot blendMode>` 합성, `<Stroke join>`, `<Font minSize>`, `<Text lineSpacing>` / `verticalAlign`.
- `fixtures/ablation/*.xml`: 자리별 시계(1개 vs 4개 `DigitalClock`)와 AOD 내 정적 `<PartText name="ClockColon">` 가시 여부(0개 vs 1개)를 2×2로 분리한 AOD 메모리(`+810,000` bytes = `450 × 450 × 4` bytes) 통제 변수 비교 픽스처 4종.
- `fixtures/negative/*.xml`: 상위 WFF 기능이 하위 규격에 잘못 포함되거나 `Variant`/`Reference` 스키마 규칙을 위반하는 경우를 검출하는 7종 음성 픽스처.
- `run_ag01_verification.py`: 공식 `wff-validator.jar` 52건 교차 검증, 격리 임시 디렉터리(`tempfile.TemporaryDirectory`) Clean APK 빌드 6종, 단일 변수 통제 비교 APK 빌드 4종, `apkanalyzer` Manifest 검증, 리소스 전용 ZIP 엔트리 검사, 원본 XML과 APK 내부 `res/raw/watchface.xml` SHA-256 일치 검사, `memory-footprint.jar` 메모리 예산 및 레이어(`--verbose`) 검증, `apksigner` v2 서명 검증, 에뮬레이터 환경 조사 및 원본 로그(`docs/evidence/AG-01/logs/*.log`) 보존 실행기.
- `test_ag01_suite.py`: `unittest` 기반 구조 불변성 및 공식 Validator 매트릭스 자동 회귀 테스트.

## 실행 방법

```bash
# 1. AG-01 단위 및 공식 스키마 매트릭스 테스트 실행
python -m unittest discover -s tests/compatibility/ag-01 -p "test_*.py" -v

# 2. 전체 검증(스키마 52건 + 격리 APK 클린 빌드 6종 + AOD 메모리 통제 비교 4종 + 에뮬레이터 조사) 및 원본 로그 보존
python tests/compatibility/ag-01/run_ag01_verification.py --mode all --logs-dir docs/evidence/AG-01/logs
```
