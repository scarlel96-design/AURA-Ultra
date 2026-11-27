# AG-01 — WFF 4/5 기능 및 실행 검증 PoC 스위트

이 디렉터리는 작업지시서 [`docs/operations/agent-orders/AG-01.md`](../../../docs/operations/agent-orders/AG-01.md)에 따라 WFF 2~5의 공식 스키마 범위, 연속 AOD 전환(`Variant`), 단일 소스 데이터 참조(`Reference`), 합성 컴플리케이션 다중 그래픽 제어, WFF 5 컨테이너 혼합 모드(`Group`/`ComplicationSlot` `blendMode`), 상위 기능 하위 침투 검출 및 격리된 임시 APK 빌드·메모리·서명 검증을 수행하는 독립 PoC 모듈이다.

## 디렉터리 구성

- `fixtures/wff2/poc_wff2_static_aod.xml`: WFF 2 정적 AOD 대체 구현(단일 `DigitalClock`/`TimeText` 객체의 정적 위치·크기·색상 전환 및 날씨 데이터 누락 시 `--` 표시).
- `fixtures/wff3/poc_wff3_part_blend_aod.xml`: WFF 3 정적 AOD 대체 + `PartDraw`/`PartText` 수준 `blendMode` (`SCREEN`, `SRC_OVER`) 국소 광택 레이어.
- `fixtures/wff4/poc_wff4_continuity.xml`: WFF 4 `Variant` 기반 5단계 연속 AOD 전환 PoC(`startOffset + duration <= 1.0` 규칙, 6종 보간 함수 `LINEAR`, `EASE_IN`, `EASE_OUT`, `EASE_IN_OUT`, `OVERSHOOT`, `CUBIC_BEZIER` + `controls`, `angleDirection="CLOCKWISE"`, 단일 시계 객체 이동·스케일 보간).
- `fixtures/wff4/poc_wff4_reference_complication.xml`: WFF 4 `Reference` 단일 소스 발행 및 합성 `ComplicationSlot`(`RANGED_VALUE`/`SHORT_TEXT`/`EMPTY`) 기반 다중 그래픽 요소(외곽 호, 글래스 패널 폭/위치, 상태 색상, 텍스트 및 `--` fallback) 동기화 제어 PoC.
- `fixtures/wff4/poc_wff4_motion_triggers.xml`: `<Gyro>` 시차/반사광(`sensorSourceType`), 자리별 분리 `TimeText`(`hh_10`, `hh_1`, `mm_10`, `mm_1`) 컨테이너 모션, 상태 표현식 기반 `<Transform><Animation>` 이벤트 트리거 PoC.
- `fixtures/wff5/poc_wff5_blend_features.xml`: WFF 5 `<Group blendMode="SCREEN">`, `<ComplicationSlot blendMode="SCREEN">`, `<Stroke join="ROUND">`, `<Font minSize="14">`, `<Text lineSpacing="1.0" verticalAlign="CENTER" isAutoSize="TRUE">` 통합 PoC.
- `fixtures/negative/neg_*.xml` (7종): 상위 WFF 기능의 하위 규격 침투 및 잘못된 `Variant`/`Reference` 구문 검출 fixture.
- `run_ag01_verification.py`: 공식 WFF Validator(1.7.0) 52건 교차 검증, 격리된 임시 작업 공간 Clean APK 빌드(6종 PoC APK), 리소스 전용·Manifest·원본 XML 일치·Memory Footprint Evaluator(1.5.1, 활성 70 MiB / AOD 7 MiB)·Debug 서명 검증 및 에뮬레이터 환경 점검 러너.
- `test_ag01_suite.py`: 구조적 불변조건, 검증기 실패 검출(G2) 및 공식 WFF 2~5 스키마 매트릭스 단위·통합 회귀 시험.

## 실행 명령

```bash
# 1. AG-01 단위 및 공식 WFF 스키마 매트릭스 회귀 시험 (52건 validator 교차 검증 포함)
python -m unittest discover -s tests/compatibility/ag-01 -p "test_*.py" -v

# 2. AG-01 전체 검증 (스키마 매트릭스 + 격리된 임시 폴더 Clean APK 6종 빌드/Manifest/XML/Memory/Signature + 에뮬레이터 점검)
python tests/compatibility/ag-01/run_ag01_verification.py --mode all
```

상세 검증 결과와 공식 기술 근거는 [`docs/evidence/AG-01/REPORT.md`](../../../docs/evidence/AG-01/REPORT.md)를 참조한다.
