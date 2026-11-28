# 작업 보고서 — AG-01 / 회차 01

- **상태**: PARTIAL (정적 스키마 52/52 PASS, 격리 Clean APK 6/6 빌드·Manifest·리소스 전용·원본 XML 일치·메모리·Debug 서명 PASS, 로컬 Wear OS 에뮬레이터 및 실기기 런타임 NOT RUN) / 제품 출시 판정: **NO-GO**
- **일자, 작업자, 검토자**: 2026-11-27 / 작업자: Antigravity CLI (`AG-01`) / 검토자: Antigravity CLI (구현 후 별도 자기 재검토 수행; 독립 에이전트·사람 리뷰 아님)
- **기준 브랜치 / HEAD**: `main` @ `fe4e19d7c6e97c043e4f31cb5960bdb430fd507b` (작업 브랜치: `agent/antigravity/AG-01`)
- **PRE-FLIGHT**:
  - 확인한 최신 기준 SHA: `fe4e19d7c6e97c043e4f31cb5960bdb430fd507b` (`docs: assign isolated first tasks to Grok Build and Antigravity CLI [skip ci]`), 직전 코드 검증 SHA: `f284b1bd69a767ef0f7285449fe7c45f05895e53`
  - 실제 읽은 필수 문서 경로: `AGENTS.md`, `README.md`, `docs/STATUS.md`, `docs/MASTER_ARCHITECTURE.md`, `docs/REQUIREMENTS.md`, `docs/QUALITY_GATES.md`, `docs/COMPATIBILITY.md`, `docs/MOTION_SPEC.md`, `docs/DESIGN_SYSTEM.md`, `docs/DATA_INTELLIGENCE.md`, `docs/PERFORMANCE.md`, `docs/REFERENCES.md`, `docs/operations/RESUME_PROTOCOL.md`, `docs/operations/PROJECT_INVARIANTS.md`, `docs/operations/TASK_RECORD_PROTOCOL.md`, `docs/operations/VERIFICATION_PROTOCOL.md`, `docs/operations/TASK_REPORT_TEMPLATE.md`, `docs/operations/GPT_EXECUTION_PLAN.md`, `docs/operations/BLOCKERS.md`, `docs/operations/WORK_LOG.md`, `docs/operations/GPT-03.md`, `docs/operations/agent-orders/README.md`, `docs/operations/agent-orders/AG-01.md`, `docs/evidence/GPT-02/REPORT-02.md`, `docs/evidence/WO-01/REPORT.md`, `docs/evidence/WO-01/API_CAPABILITIES.md`, `docs/evidence/WO-01/TOOLCHAIN.md`, `docs/evidence/WO-01/DEVICE_MATRIX.md`, `docs/evidence/WO-01/SOURCES.md`, `docs/adr/ADR-007.md`
  - 활성 작업 및 차단점: 중앙 활성 작업 `GPT-03 READY` (`GPT-02 GO`), 외부 에이전트 분리 작업 `AG-01 READY` (소유 경로: `tests/compatibility/ag-01/**`, `docs/evidence/AG-01/**`). 차단점 `B-002` (BLOCKED/P1: 실기기/워치 미연결), `B-003` (OPEN/P1: SDK37/빌드 해결, WFF5 전용 기능 및 런타임 미확인), `B-005` (OPEN/P1: WFF4 Reference, Variant, 숫자 전환, Gyro, 모션 트리거 미검증)
  - 관련 CI 대조: CI `46002470824` (코드 SHA `f284b1bd69a767ef0f7285449fe7c45f05895e53`, job `140517331808`, `completed/success`, 40 단위 시험 및 WFF2~5 기본 APK 빌드/스키마/메모리/서명 PASS)
  - 판정: **PRE-FLIGHT PASS** (매 작업 턴마다 최신 HEAD 및 필수 문서를 실제 읽고 대조함)
- **검증 대상 코드 SHA**: 기준 부모 SHA `fe4e19d7c6e97c043e4f31cb5960bdb430fd507b` 위의 `agent/antigravity/AG-01` 브랜치 변경분 (자기 참조 SHA 기록 금지 규정에 따라 커밋 SHA는 Git 이력에서 확인하며, 본 보고서의 모든 파일·APK·XML SHA-256 해시를 아래에 명시함)
- **관련 요구사항 / WO / GPT ID**:
  - 요구사항: `R-02`, `R-06`, `R-07`, `R-08`, `R-17`, `R-18`, `R-20`, `R-22`, `R-23`, `R-25`
  - 초기 PoC 게이트: `P03` (AOD continuity), `P06` (Parallax/Gyro), `P07` (Fluid Digits), `P08` (Reference), `P12` (WFF 5)
  - 연계 작업: `AG-01`, `GPT-05`, `GPT-06`, `WO-05`, `WO-07`, `WO-08` 준비 작업 (선행 WO 미충족 상태 유지)
  - 차단점 연계: `B-002`, `B-003`, `B-005`
- **관련 정본 문서**: `docs/operations/agent-orders/AG-01.md`, `docs/MOTION_SPEC.md`, `docs/COMPATIBILITY.md`, `docs/DESIGN_SYSTEM.md`, `docs/DATA_INTELLIGENCE.md`, `docs/PERFORMANCE.md`, `docs/QUALITY_GATES.md`
- **작업 목표, 포함/제외 범위**:
  - **포함 범위**:
    1. WFF 4 `Variant` 기반 AOD 전환 지원 속성(`duration`, `startOffset`, `interpolation`, `controls`, `angleDirection`) 및 보간 방식의 공식 XSD·검증기 검증
    2. 동일 시간 객체(`<DigitalClock>` + `<TimeText>`)의 위치·크기·색상이 자연스럽게 보간되는 5단계 연속 모션 PoC XML 구현(`poc_wff4_continuity.xml`)
    3. WFF 2·3에서 사용할 수 있는 단일 객체 정적 AOD 대체 샘플 구현(`poc_wff2_static_aod.xml`, `poc_wff3_part_blend_aod.xml`)
    4. WFF 4 `<Reference>`의 공식 지원 데이터 타입, 허용/금지 부모 엘리먼트 및 참조 범위 검증
    5. 합성 컴플리케이션 데이터(`RANGED_VALUE`, `SHORT_TEXT`, `EMPTY`)와 `<Reference>`로 여러 그래픽 요소를 동시 제어하고 데이터 누락 시 `0`이 아닌 `--`로 표시하는 최소 구현체 제작(`poc_wff4_reference_complication.xml`)
    6. WFF 5의 `<Group>` 및 `<ComplicationSlot>` `blendMode` 혼합 기능과 신규 타이포/도형 속성(`Stroke join`, `Font minSize`, `Text lineSpacing`/`verticalAlign`) 검증(`poc_wff5_blend_features.xml`)
    7. 상위 WFF 기능이 하위 규격에 잘못 포함될 때 공식 validator가 거부하는지 7종 negative fixture 및 52건 교차 검증으로 확인
    8. `<Gyro>`, 자리별 숫자 전환(`hh_10`, `hh_1`, `mm_10`, `mm_1`), 이벤트 모션 트리거(`eventTriggerType`, `<Transform><Animation>`)의 공식 조건·메모리 영향·대체 구현 방법 문서화 및 PoC 검증(`poc_wff4_motion_triggers.xml`)
    9. 격리된 임시 작업 공간에서의 6종 PoC APK Clean Build, 리소스 전용 검사, 컴파일된 Manifest 검사, 원본 XML 바이트 일치 검사, 공식 Memory Footprint Evaluator(활성 70 MiB / AOD 7 MiB) 및 Debug APK 서명 검증
  - **제외 범위**:
    - `apps/**`, `tools/**`, `compatibility/**`, `design-system/**`, `assets/**`, `modules/**`, 루트 Gradle 설정, `.github/workflows/**` 및 중앙 운영 문서(`docs/STATUS.md`, `docs/operations/WORK_LOG.md`, `docs/operations/BLOCKERS.md`) 직접 수정 금지
    - 비공개 API, 임의 렌더러 제어, 실행 코드(`.dex`/`.so`/Kotlin/Java) 삽입 금지
    - 사용자 승인 없는 신규 SDK/Wear OS 에뮬레이터 이미지 다운로드 및 실제 사용자 워치 설치/설정 변경 금지
- **선행 조건 및 이전 실패**:
  - `GPT-01` 및 `GPT-02`에서 API 37.0(`platforms;android-37.0`), AGP 9.1.1, Gradle 9.3.1, WFF 2~5 기본 bootstrap APK 빌드 및 CI 검증 기반이 확보됨(`CI 46002470824`).
  - 그러나 WFF 4 `Variant` 전환 속성, `Reference` 교차 요소 제어, WFF 5 `Group`/`ComplicationSlot` `blendMode`, 실제 flavor override(`src/wffN/res/raw/watchface.xml`) 패키징 및 메모리 영향은 미검증 상태(`B-003`, `B-005`).
- **변경 파일 소유권 / 변경 영향**:
  - 소유 경로 `tests/compatibility/ag-01/**` 및 `docs/evidence/AG-01/**` 내부에서만 파일 생성.
  - 기존 제품 APK, 공통 도구 및 CI 워크플로에 대한 부작용(회귀 영향) 0.
- **참조 자료 (정확한 URL·버전·확인일: 2026-11-27)**:
  - Google Watch Face Format 공식 가이드 및 릴리스 노트: `https://developer.android.com/training/wearables/wff`, `https://developer.android.com/training/wearables/wff/release-notes`
  - WFF XML 레퍼런스 (`Variant`, `Reference`, `Transform`, `Animation`, `Gyro`, `Group`, `ComplicationSlot`, `TimeText`, `blendMode`): `https://developer.android.com/reference/wear-os/wff`
  - Google Watch Face 공식 검증 도구 저장소 (Apache-2.0): `https://github.com/google/watchface`
    - Official WFF Validator `1.7.0` (`Maximum Supported Format Version #5`), 고정 JAR SHA-256: `0e2204137fca618264e82f9a053c6c9ec6d4fad08d2b56aa8a57d75c0508a804` 및 JAR 내장 `docs.zip` 공식 WFF 1~5 XSD 스키마
    - Official Memory Footprint Evaluator `1.5.1` (Git hash `b87dde8`), 고정 JAR SHA-256: `503c5f7bc9209ec4d4d4974f973cf66ad6fbb435e8422c310aac5b820f1f991a`
- **가정 / 위험 / 승인 필요 사항**:
  - 스키마 통과 및 격리 APK 빌드/메모리 평가 통과는 실기기 렌더링 품질, 프레임 속도, 배터리 소모 또는 발열 보장을 의미하지 않는다.
  - 로컬 PC에 Wear OS 에뮬레이터용 시스템 이미지(`system-images;android-36;android-wear;x86_64`, `system-images;android-37.0;android-wear;x86_64`) 및 AVD가 설치되어 있지 않으며 연결된 물리 워치도 없다. 지시서의 무승인 다운로드 금지 규칙에 따라 에뮬레이터/실기기 런타임 검증은 `NOT RUN`으로 기록하고 즉시 재현 가능한 명령과 스크립트를 제공한다.
- **성공 기준 / 롤백 방법**:
  - 성공 기준: 6종 정상 PoC XML 및 7종 negative fixture의 WFF 2~5 공식 스키마 매트릭스(52건) 100% 통과, 격리 임시 워크스페이스에서 6종 PoC APK Clean Build 및 리소스 전용·Manifest·원본 XML 일치·메모리(활성 ≤70 MiB, AOD ≤7 MiB)·Debug v2 서명 100% 통과, 기존 40개 단위 시험 및 신규 AG-01 단위 시험 통과.
  - 롤백 방법: 독립 브랜치 `agent/antigravity/AG-01` 또는 해당 커밋을 삭제/revert하면 `main`에 영향 없이 즉시 롤백된다.

---

## 1. 로컬 환경 조사 결과

| 구분 | 확인 항목 | 실제 확인 값 / 상태 | 비고 |
|---|---|---|---|
| OS | Windows 버전 | Windows 11 `10.0 amd64` | PowerShell / Python 실행 환경 |
| JDK | 기본 Java 런타임 | OpenJDK `21.0.5` (`Temurin-21.0.5+11-LTS`) | `C:\Program Files\Eclipse Adoptium\jdk-21.0.5.11-hotspot` |
| JDK (보조) | Android Studio JBR | OpenJDK `21.0.9` (`build 21.0.9+-14649483-b1163.86`) | `C:\Program Files\Android\Android Studio\jbr` |
| Python | 호스트 스크립트 런타임 | Python `3.14.7` | `unittest` 및 검증 스크립트 실행 |
| Gradle | Gradle Wrapper | Gradle `9.3.1` (Revision `44f4e8d3122ee6e7cbf5a248d7e20b4ca666bda3`) | Wrapper JAR SHA-256 `b3a875dd...42ec13` 일치 |
| AGP | Android Gradle Plugin | `9.1.1` | `compileSdk = 37`, `targetSdk = 37` |
| Android SDK | SDK 경로 (`ANDROID_HOME`) | `C:\Users\scarl\AppData\Local\Android\Sdk` | 로컬 설치 확인 |
| SDK Platforms | 설치된 플랫폼 | `android-36`, `android-36.1`, `android-37`, `android-37.0` (`Pkg.Revision=2`) | `android-37.0/android.jar` 존재 확인 |
| Build Tools | 설치된 빌드 도구 | `36.0.0`, `36.1.0` | `build-tools/36.0.0/apksigner.bat` 확인 |
| Cmdline Tools | 바이너리 검사 도구 | `cmdline-tools/latest/bin/apkanalyzer.bat`, `sdkmanager.bat`, `avdmanager.bat` | 컴파일된 Manifest 검사 사용 |
| WFF Validator | 공식 스키마 검증기 | Version `1.7.0` (Max Format Version `#5`) | SHA-256 `0e2204137fca618264e82f9a053c6c9ec6d4fad08d2b56aa8a57d75c0508a804` |
| Memory Evaluator | 공식 메모리 평가기 | Version `1.5.1`, Git hash `b87dde8` | SHA-256 `503c5f7bc9209ec4d4d4974f973cf66ad6fbb435e8422c310aac5b820f1f991a` |
| System Images | 에뮬레이터 이미지 | `system-images\android-36.1\google_apis_playstore\x86_64` (모바일 전용 1종) | **Wear OS (`android-wear`) 이미지 미설치** |
| AVD / ADB | 에뮬레이터 및 연결 기기 | `emulator -list-avds`: 0개 / `adb devices -l`: 0대 | 격리 Wear OS 에뮬레이터 없음 (`NOT RUN`) |

---

## 2. 구현 및 기술 검증 상세 결과 (구현 범위 1~8)

### 2.1 변경 파일 목록 및 책임

| 파일·모듈 | 변경 및 이유 | 관련 요구사항 | 확인할 영향 |
|---|---|---|---|
| `tests/compatibility/ag-01/fixtures/wff2/poc_wff2_static_aod.xml` | 단일 `DigitalClock`/`TimeText` 정적 AOD 전환 및 날씨 누락 `--` fallback 구현 (WFF 2) | R-02, R-06, R-17, R-18, R-20 | WFF 2~5 스키마 PASS, WFF 2 격리 APK 빌드·메모리 PASS |
| `tests/compatibility/ag-01/fixtures/wff3/poc_wff3_part_blend_aod.xml` | WFF 3 정적 AOD 전환 + `PartDraw`/`PartText` 수준 `blendMode` (`SCREEN`, `SRC_OVER`) 구현 | R-02, R-06, R-20 | WFF 2에서 FAIL(하위 침투 차단), WFF 3~5에서 PASS |
| `tests/compatibility/ag-01/fixtures/wff4/poc_wff4_continuity.xml` | WFF 4 `Variant` 5단계 연속 AOD 전환(`duration`, `startOffset`, 6종 `interpolation`, `controls`, `angleDirection`, 단일 시계 객체 이동·크기 변화) 구현 | R-02, R-06, R-20, P03 | WFF 2/3에서 FAIL, WFF 4/5에서 PASS, 격리 APK 빌드·메모리 PASS |
| `tests/compatibility/ag-01/fixtures/wff4/poc_wff4_reference_complication.xml` | WFF 4 `<Reference>` 단일 소스 발행 및 합성 `ComplicationSlot` 기반 다중 그래픽 요소 동기화 제어 구현 | R-02, R-12, R-17, R-18, R-20, P08 | WFF 2/3에서 FAIL, WFF 4/5에서 PASS, 격리 APK 빌드·메모리 PASS |
| `tests/compatibility/ag-01/fixtures/wff4/poc_wff4_motion_triggers.xml` | `<Gyro>` 시차/반사광, 자리별 `TimeText` (`hh_10`, `hh_1`, `mm_10`, `mm_1`) 컨테이너 모션, 상태 표현식 `<Transform><Animation>` 이벤트 트리거 구현 | R-07, R-08, R-20, P06, P07 | WFF 2/3에서 FAIL, WFF 4/5에서 PASS, 자리별 시계 AOD 메모리 비용 실측 |
| `tests/compatibility/ag-01/fixtures/wff5/poc_wff5_blend_features.xml` | WFF 5 `<Group blendMode>`, `<ComplicationSlot blendMode>`, `<Stroke join>`, `<Font minSize>`, `<Text lineSpacing verticalAlign>` 구현 | R-02, R-20, P12 | WFF 2/3/4에서 FAIL, WFF 5에서 PASS, API 37 격리 APK 빌드·메모리 PASS |
| `tests/compatibility/ag-01/fixtures/negative/neg_*.xml` (7종) | 상위 WFF 기능 하위 규격 침투 및 잘못된 `Variant`/`Reference` 구문 검출용 negative fixture 7종 | R-02, R-22, R-25, G2 | 버전별 공식 validator 거부 및 정확한 `SAXParseException` 검출 확인 |
| `tests/compatibility/ag-01/run_ag01_verification.py` | 52건 스키마 교차 검증, 격리 임시 워크스페이스 6종 APK Clean Build·Manifest·XML·Memory·Signature 검증 및 에뮬레이터 점검 스크립트 | R-02, R-20, R-22, R-25 | 메인 워크스페이스 오염 없이 임시 폴더에서 전체 빌드·검증 수행 |
| `tests/compatibility/ag-01/test_ag01_suite.py` | PoC 구조 불변조건, G2 실패 검출, WFF 2~5 공식 validator 52건 매트릭스 자동 회귀 시험 스위트 | R-02, R-22, G2, G3 | `unittest` 10개 테스트 메서드(내부 52개 validator subTest 포함) 100% PASS |
| `tests/compatibility/ag-01/README.md` | AG-01 PoC 구조 및 재현 명령 안내 문서 | G7 | 독립 실행 및 후속 작업 참조 가능 |
| `docs/evidence/AG-01/REPORT.md` | AG-01 공식 기술 근거, 검증 결과, 실패 분석, 재사용 계약 및 중앙 문서 갱신 제안 보고서 | G0~G7 | 증거 영속 보존 |

---

### 2.2 항목 1 & 2 & 3: WFF 4 `Variant` 기반 AOD 전환 규격, 연속 모션 PoC 및 WFF 2·3 정적 대체

`wff-validator.jar` (v1.7.0) 내장 공식 XSD (`3/common/variant/variantElements.xsd` vs `4/common/variant/variantElements.xsd`)를 대조하여 확인한 공식 규격은 다음과 같다.

| 속성 | 지원 버전 | 타입 및 허용 범위 | 기본값 | 공식 의미 및 플랫폼 제약 |
|---|---|---|---|---|
| `mode` | WFF 1~5 | `"AMBIENT"` (필수) | 없음 | AOD 진입/이탈 시 적용할 상태 모드 |
| `target` | WFF 1~5 | `xs:string` (필수) | 없음 | 부모 엘리먼트의 transformable 속성 (`x`, `y`, `width`, `height`, `scaleX`, `scaleY`, `pivotX`, `pivotY`, `angle`, `alpha`, `tintColor`) |
| `value` | WFF 1~5 | `arithmeticExpressionType` (필수) | 없음 | `AMBIENT` 상태에서의 목표 값 또는 수식 |
| `duration` | **WFF 4~5 전용** | `xs:float` (`0.0` ~ `1.0`) | `"1.0"` | 시스템이 허용하는 전체 AOD 전환 시간 대비 상대 지속 비율 (밀리초 단위가 아님; `0.0`은 즉시 변경, `1.0`은 전체 전환 구간 사용) |
| `startOffset` | **WFF 4~5 전용** | `xs:float` (`0.0` ~ `1.0`) | `"0.0"` | 전체 AOD 전환 시간 대비 시작 지연 비율. **핵심 제약: `duration + startOffset > 1.0`이면 파서가 `startOffset`을 무시함** |
| `interpolation` | **WFF 4~5 전용** | `LINEAR`, `EASE_IN`, `EASE_OUT`, `EASE_IN_OUT`, `OVERSHOOT`, `CUBIC_BEZIER` | `"LINEAR"` | 전환 보간 곡선 (총 6종 열거형만 허용; `SPRING` 등 미지원) |
| `controls` | **WFF 4~5 전용** | `vector4fType` (공백 구분 4개 float) | `"0.5 0.5 0.5 0.5"` | `interpolation="CUBIC_BEZIER"`일 때만 유효한 베지어 제어점 (`x1 y1 x2 y2`) |
| `angleDirection` | **WFF 4~5 전용** | `NONE`, `CLOCKWISE`, `COUNTER_CLOCKWISE` | `"NONE"` | `target="angle"`일 때의 회전 방향 지정 |

- **허용 부모 엘리먼트 제약**:
  - `<Variant>`는 `Scene`, `Group`, `DigitalClock`, `TimeText`, `AnalogClock`, `HourHand`, `MinuteHand`, `SecondHand`, `ComplicationSlot`, `PartDraw`, `PartText`, `PartImage`, `PartAnimatedImage`에만 직접 배치할 수 있다.
  - `<RoundRectangle>`, `<Arc>`, `<Ellipse>`, `<Fill>`, `<Stroke>`, `<Font>` 등 하위 도형·스타일 엘리먼트는 `<Transform>`과 `<Reference>`는 가질 수 있으나 **`<Variant>`를 직접 자식으로 가질 수 없다**. 따라서 AOD 전환 시 위치·크기·투명도·색상 보간은 반드시 부모 `<Group>`, `<Part*>`, `<DigitalClock>`, `<TimeText>`의 속성을 `target`으로 지정해야 한다.
- **동일 객체 연속 모션 PoC (`poc_wff4_continuity.xml`)**:
  - 기존 bootstrap XML처럼 활성용 `TimeText`와 AOD용 `TimeText` 2개를 교차 페이드(`alpha 255↔0`)하는 대신, **단일 `<DigitalClock>` + 단일 `<TimeText>` 객체**에 `<Variant mode="AMBIENT" target="y" value="166" startOffset="0.00" duration="0.85" interpolation="EASE_IN_OUT"/>`, `target="scaleX" value="0.88"`, `target="scaleY" value="0.88"`, `target="tintColor" value="#FFB7C0C9"`를 부여하여 동일 시간 객체가 이동·축소·감광되도록 구현했다.
  - `MOTION_SPEC.md`의 5단계 활성화/비활성화 구간을 `startOffset + duration <= 1.0` 공식으로 매핑했다:
    - 시간 (`DigitalClock`, 0~85%): `startOffset="0.00" duration="0.85"` (`EASE_IN_OUT`, `CUBIC_BEZIER`)
    - 외곽 링 (`OuterPrecisionRing`, 10~100%): `startOffset="0.10" duration="0.90"` (`CUBIC_BEZIER controls="0.22 1.0 0.36 1.0"`, `EASE_OUT`)
    - 소재 하이라이트 (`MaterialHighlight`, 15~80%): `startOffset="0.15" duration="0.65"` (`EASE_IN_OUT` + `angleDirection="CLOCKWISE"`, `LINEAR`)
    - 정보 패널 (`PrimaryInfoPanel`, 25~90%): `startOffset="0.25" duration="0.65"` (`OVERSHOOT`, `EASE_IN_OUT`, `EASE_OUT`)
    - 보조 정보 (`SecondaryInfoGroup`, 45~100%): `startOffset="0.45" duration="0.55"` (`EASE_IN`)
- **WFF 2·3 정적 AOD 대체 (`poc_wff2_static_aod.xml`, `poc_wff3_part_blend_aod.xml`)**:
  - WFF 2/3에서는 `duration`, `startOffset`, `interpolation` 속성을 제거하고 동일 `<DigitalClock>`의 3속성 `<Variant mode="AMBIENT" target="y|scaleX|scaleY|tintColor" value="..."/>`만 유지하여 동일한 시각적 레이아웃 좌표를 정적 전환으로 재현하고, 장식 그룹은 `<Variant mode="AMBIENT" target="alpha" value="0"/>`로 소등한다.

---

### 2.3 항목 4 & 5: WFF 4 `Reference` 공식 지원 범위 및 합성 컴플리케이션 다중 그래픽 제어

`4/common/reference/referenceElements.xsd` 및 WFF 4 전체 XSD 전수 조사를 통해 확인한 `<Reference>`의 공식 계약은 다음과 같다.

1. **속성 및 데이터 타입**:
   - `name` (`xs:string`, 필수): 문서(`WatchFace`) 전체 범위에서 고유한 식별자. 다른 수식에서 `[REFERENCE.<name>]` 형태로 참조한다.
   - `source` (`xs:string`, 필수): 부모 엘리먼트의 transformable 속성명(예: `x`, `y`, `width`, `height`, `angle`, `alpha`, `scaleX`, `scaleY`, `tintColor`, `color`, `endAngle`, `startAngle`, `thickness` 등).
   - `defaultValue` (`_defaultValueType`, 선택): `argbHexadecimalType` (`#AARRGGBB` 또는 `#RRGGBB`), `xs:integer`, `xs:float`, `xs:double` 중 하나.
2. **허용 부모 엘리먼트(21종) vs 금지 부모 엘리먼트(8종)**:
   - **허용 부모 (21종)**: `Scene`, `Group`, `PartDraw`, `PartText`, `PartImage`, `PartAnimatedImage`, `Arc`, `Ellipse`, `Line`, `Rectangle`, `RoundRectangle`, `Fill`, `Stroke`, `WeightedStroke`, `LinearGradient`, `RadialGradient`, `SweepGradient`, `Font`, `BitmapFont`, `TextCircular`, `InlineImage`, `OutGlow`, `Outline`, `Shadow`.
   - **금지 부모 (8종)**: `DigitalClock`, `TimeText`, `AnalogClock`, `HourHand`, `MinuteHand`, `SecondHand`, `ComplicationSlot`, `Complication`. (이 태그들 바로 아래에 `<Reference>`를 두면 `cvc-complex-type.2.4.a: Invalid content was found starting with element 'Reference'`로 스키마 검증에 실패함).
3. **단일 소스 발행 및 참조 제약**:
   - `<Reference>`는 임의의 JSON이나 외부 객체를 직렬화 없이 전달하는 통로가 아니라, 부모 엘리먼트의 transformable 속성에 `<Transform>`으로 투영된 수치 또는 ARGB 색상을 단일 소스(single-source)로 발행하는 메커니즘이다.
   - 교차 참조 또는 순환 참조(`A ↔ B`)를 구성하면 공식 XSD 명세에 따라 최초 1회만 갱신되고 이후 갱신이 중단된다.
   - **보이지 않는 발행 노드 작성 규칙**: 순수하게 계산값을 발행하기 위한 비가시 노드를 만들 때는 `<PartDraw>`가 아닌 **`<Group alpha="0">`을 사용해야 한다** (`<PartDraw>`는 최소 1개의 `DrawElement` 자식을 필수로 요구하므로 도형 없이 `<Transform>`과 `<Reference>`만 넣으면 스키마 오류가 발생함).
4. **합성 컴플리케이션 다중 그래픽 제어 구현 (`poc_wff4_reference_complication.xml`)**:
   - 장면 레벨 `<Group name="TelemetryReferencePublisher">`에서 `ref_telemetry_ratio` (`source="x"`), `ref_panel_width` (`source="width"`), `ref_status_color` (`source="tintColor"`) 3개 참조를 발행하여 ① 외곽 궤도 `<Arc>`의 `endAngle` 및 `<Stroke>` 색상, ② 중앙 정렬되는 동적 글래스 패널 `<RoundRectangle>`의 `x`/`width` 및 테두리 색상, ③ 상단 브랜드 헤더 `<Font>` 색상, ④ 요약 텍스트 `<Template>` 수치와 색상을 동시에 제어했다.
   - `<ComplicationSlot slotId="1" supportedTypes="RANGED_VALUE SHORT_TEXT EMPTY">` 내부 `<Complication type="RANGED_VALUE">`에서 `[COMPLICATION.RANGED_VALUE_VALUE]`, `[COMPLICATION.RANGED_VALUE_MIN]`, `[COMPLICATION.RANGED_VALUE_MAX]`를 정규화하여 `<Arc>`의 `ref_comp_sweep` (`source="endAngle"`)과 `<Stroke>`의 `ref_comp_color` (`source="color"`)로 발행하고, 이를 진행률 바 `<RoundRectangle>`의 폭/테두리 색상 및 `<PartText>` 라벨 색상이 동시에 참조하도록 구현했다.
   - `SHORT_TEXT` 및 `EMPTY` 상태에서는 `<Condition>`(`textLength([COMPLICATION.TEXT]) > 0`)을 통해 데이터 누락 시 `0`이 아닌 `DATA --` / `NO SOURCE --`로 fallback 표시하여 `R-17`/`R-18`을 준수했다.

---

### 2.4 항목 6 & 7: WFF 5 `Group`/`ComplicationSlot` 혼합 기능 및 상위 기능 하위 침투 검출

`4/` vs `5/` 공식 XSD 전수 비교 및 `poc_wff5_blend_features.xml`, `neg_*.xml` 검증으로 확인한 WFF 5 전용 기능은 다음과 같다.

| WFF 5 신규 기능 | XML 위치 및 속성 | 허용 값 / 타입 | 하위 버전(WFF 2~4) 포함 시 공식 Validator 오류 |
|---|---|---|---|
| 컨테이너 그룹 혼합 모드 | `<Group blendMode="...">` | `blendModeType` (29종: `SCREEN`, `MULTIPLY`, `OVERLAY`, `SOFT_LIGHT`, `SRC_OVER`, `PLUS` 등) | `cvc-complex-type.3.2.2: Attribute 'blendMode' is not allowed to appear in element 'Group'.` |
| 컴플리케이션 슬롯 혼합 모드 | `<ComplicationSlot blendMode="...">` | `blendModeType` (29종) | `cvc-complex-type.3.2.2: Attribute 'blendMode' is not allowed to appear in element 'ComplicationSlot'.` |
| 선 모서리 결합 스타일 | `<Stroke join="...">`, `<WeightedStroke join="...">` | `MITER` (기본), `ROUND`, `BEVEL` | `cvc-complex-type.3.2.2: Attribute 'join' is not allowed to appear in element 'Stroke'.` |
| 자동 크기 최소 글꼴 크기 | `<Font minSize="...">` | `xs:positiveInteger` (기본 `12`) | `cvc-complex-type.3.2.2: Attribute 'minSize' is not allowed to appear in element 'Font'.` |
| 텍스트 줄간격 및 수직 정렬 | `<Text lineSpacing="..." verticalAlign="...">` | `xs:float` (`>= -5.0`), `TOP\|CENTER\|BOTTOM` | `cvc-complex-type.3.2.2: Attribute 'lineSpacing' is not allowed to appear in element 'Text'.` |
| 원형 텍스트 자동 크기 | `<TextCircular isAutoSize="TRUE" verticalAlign="...">` | `booleanType`, `TOP\|CENTER\|BOTTOM` | WFF 4 이하 `TextCircular`에서 `isAutoSize` 미지원 |
| 조건부 하위 설정/슬롯 활성화 | `<ListOption childSettingIds="..." complicationSlotIds="...">` | `stringListType` | WFF 4 이하 `ListOption`에서 해당 속성 미지원 |
| 날씨 소스 오타 수정 (발견) | `sourceType.xsd` (`_weatherSourceEnums`) | WFF 5: `WEATHER.UV_INDEX`, `WEATHER.LAST_UPDATED` | WFF 4 XSD에는 `WEATHER.WEATHER.UV_INDEX`로 중복 접두사 등록됨 |

---

### 2.5 항목 8: Gyro, 숫자 전환(Fluid Digits) 및 기타 모션 트리거의 지원 조건과 대체 구현 방법

공식 XSD (`4/common/transform/gyroElements.xsd`, `4/clock/timeText.xsd`, `4/common/simpleTypes/eventTriggerType.xsd`, `4/common/animationElement.xsd`) 및 `poc_wff4_motion_triggers.xml` 격리 APK 메모리 평가를 통해 확인한 기술 조건과 대체 구현 계약은 다음과 같다.

| 모션 항목 | 공식 WFF 지원 조건 및 스키마 제약 | 메모리·성능 영향 (실측) | 하위 버전 / AOD / 모션 감소 대체(Fallback) |
|---|---|---|---|
| **M07/M08 Gyro 반사광·시차 (`<Gyro>`)** | - 부모: `Group`, `PartDraw`, `PartText`, `PartImage`, `PartAnimatedImage` (`DigitalClock`/`TimeText` 직접 배치 불가)<br>- 속성: `x`, `y`, `scaleX`, `scaleY`, `angle`, `alpha` (6종)<br>- 수식 타입: `gyroArithmeticExpressionType` (`ACCELEROMETER_IS_SUPPORTED`, `ACCELEROMETER_X/Y/Z`, `ACCELEROMETER_ANGLE_X/Y/Z/XY`만 허용; 일반 시간/배터리 소스 혼합 불가) | 도형/벡터 레이어에 적용 시 추가 비트맵 메모리 증가 없음 (`2,371,712` bytes 유지). 단, 연속 센서 평가로 인한 런타임 전력 소모는 실기기 측정 필요 | - 핵심 시간 텍스트는 고정하고 배경/하이라이트 `Group`에만 `clamp([ACCELEROMETER_ANGLE_X], -30, 30) * 0.12` (±3.6px) 적용<br>- AOD: 부모 `Group`에 `<Variant mode="AMBIENT" target="alpha" value="0"/>`로 센서 레이어 완전 소등<br>- Eco/모션 감소: `BooleanConfiguration` 또는 정적 좌표로 고정 광택 유지 |
| **M02 숫자 전환 (`Fluid Digits`)** | - `<TimeText>`의 `format` 정규식(`timeFormatType`)은 `hh_10`, `hh_1`, `mm_10`, `mm_1`, `ss_10`, `ss_1` 자리별 포맷을 공식 지원함<br>- 단, `<DigitalClock>`과 `<TimeText>`는 `<Transform>`/`<Animation>`을 직접 자식으로 가질 수 없으므로, 자리별 `<DigitalClock>`을 개별 `<Group>` 컨테이너로 감싸고 부모 `<Group>`에 `<Transform><Animation duration="0.20" interpolation="EASE_OUT" fps="30"/></Transform>` 또는 `<Variant>`를 적용해야 함<br>- 선언형 한계: 이전 숫자 글리프와 새 숫자 글리프를 동시에 유지하며 모핑하는 변수는 없으며, 값 변경 시 컨테이너 위치/스케일/투명도 보간만 가능 | **중요 실측 발견**: 단일 `DigitalClock` (`format="hh:mm"`)의 AOD 메모리는 `2,371,712` bytes (2.26 MiB)인 반면, 4분할 자리별 `DigitalClock` (`hh_10`, `hh_1`, `mm_10`, `mm_1` + 콜론 `PartText`)은 AOD 메모리가 **`3,181,712` bytes (3.03 MiB)**로 **`+810,000` bytes (`450×450×4` RGBA 레이어 1개분)** 증가함 (7 MiB 예산 이내 PASS이나 AOD 여유분 감소) | - 복잡한 멀티 레이어 테마나 Eco/Balanced 프로필에서는 메모리 절약을 위해 단일 `<DigitalClock><TimeText format="hh:mm"/></DigitalClock>`을 기본으로 사용<br>- 자리별 컨테이너 모션은 AOD 메모리 여유가 확인된 테마의 활성 화면에만 제한 적용하거나 AOD에서 단일 시계로 전환 |
| **M05/M09/M13/M14 이벤트 트리거 (`Animation`, `AnimationController`)** | - `PartAnimatedImage` 내부 `AnimationController`의 `play` 속성(`eventTriggerType`)은 **`TAP`, `ON_VISIBLE`, `ON_NEXT_SECOND`, `ON_NEXT_MINUTE`, `ON_NEXT_HOUR` 5종만 존재**함 (`ON_CHARGING`, `ON_GOAL` 같은 전용 트리거 없음)<br>- 따라서 데이터/상태 변화 이벤트 모션은 도형·그룹 속성의 `<Transform target="..." value="조건식"><Animation duration="0.4~0.75" interpolation="EASE_OUT|EASE_IN_OUT" repeat="0"/></Transform>`으로 구현해야 표현식 평가값이 바뀔 때 자동 보간됨 | 벡터/도형(`Arc`, `RoundRectangle`, `Stroke`)의 `<Transform><Animation>`은 추가 프레임 비트맵 없이 `2,371,712` bytes 유지. 반면 480×480 30프레임 비트맵 시퀀스는 약 27.65 MB를 소모하므로 전체 화면 `PartAnimatedImage` 금지 | - 게이지/충전/목표 달성/중요도 변화는 `<Transform><Animation repeat="0"/>` 기반 벡터/색상/크기 보간을 1순위로 사용<br>- 날씨 입자(`M10`) 등 비트맵 애니메이션은 160×160 이하 국소 영역 + `play="ON_VISIBLE"` 1회 재생으로 제한하고 AOD/Eco에서는 `<Condition>` 및 `<Variant alpha="0">`으로 제거 |

---

## 3. 시도한 접근과 실패 원인 (Troubleshooting & Lessons Learned)

1. **실패 1 — 한국어 경로(`코딩 작업`)에서 Windows Java 기본 콘솔 인코딩(CP949)으로 인한 `verify_wff.py` `UnicodeDecodeError`**:
   - **재현 조건**: Windows 한국어 로캘에서 워크스페이스 경로에 한글(`C:\Users\scarl\Desktop\코딩 작업\...`)이 포함된 상태로 `java -jar wff-validator.jar`를 호출하면, Java가 파일 경로가 포함된 `INFO: ✅ PASSED : <경로>` 줄을 CP949(`0xc4 0xda ...`)로 출력하여 Python UTF-8 리더 스레드에서 `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc4`가 발생함.
   - **해결**: Java 실행 시 `-Dfile.encoding=UTF-8 -Dsun.stdout.encoding=UTF-8 -Dsun.stderr.encoding=UTF-8` (또는 `JAVA_TOOL_OPTIONS`)을 명시하여 메인 `tools/verify_wff.py`를 수정하지 않고도 UTF-8 출력을 보장함.
2. **실패 2 — `<PartDraw>`를 도형 자식 없는 순수 `<Reference>` 발행 노드로 사용 시 공식 스키마 검증 실패**:
   - **재현 조건**: `poc_wff4_reference_complication.xml` 및 `poc_wff5_blend_features.xml` 초안에서 화면에 그려지지 않는 단일 소스 계산 노드로 `<PartDraw alpha="0"><Transform .../><Reference .../></PartDraw>`를 배치함.
   - **오류 원문**: `SEVERE: [Line 31:Column 24]: cvc-complex-type.2.4.b: The content of element 'PartDraw' is not complete. One of '{Localization, Variant, Gyro, Launch, ScreenReader, DrawElement}' is expected.`
   - **원인 및 해결**: `4/group/part/draw/partDrawElement.xsd`에서 `<PartDraw>`는 최소 1개 이상의 `DrawElement`(`Arc`, `RoundRectangle` 등) 자식을 필수로 요구한다. 반면 `<Group>`(`4/group/groupElement.xsd`)은 자식 시각 요소 없이 `<Transform>`과 `<Reference>`만 가질 수 있다. 비가시 계산/발행 노드를 `<Group alpha="0">`으로 변경하여 WFF 4 및 WFF 5 공식 스키마 검증을 통과시켰다. 후속 `GPT-05`/`WO-07` 개발 시 비가시 `<Reference>` 허브는 반드시 `<Group>`을 사용해야 한다.
3. **실패 3 — 로컬 격리 Wear OS 에뮬레이터 런타임 시험 미실시 (`NOT RUN`)**:
   - **원인**: 로컬 Android SDK(`C:\Users\scarl\AppData\Local\Android\Sdk`)를 조사한 결과 `emulator.exe`와 `adb.exe`는 설치되어 있으나, `system-images`에는 모바일용 `android-36.1\google_apis_playstore\x86_64`만 존재하고 Wear OS용 시스템 이미지(`android-wear`)와 생성된 AVD가 없다(`emulator -list-avds` 0개, `adb devices -l` 0대).
   - **조치**: AG-01 지시서("새 SDK/에뮬레이터 다운로드, 유료 서비스, 계정 권한 변경 등 추가 환경 조치는 사용자 승인 없이 하지 않는다. 환경이 없으면 NOT RUN, 구체적인 재현 절차와 필요한 환경을 남긴다")를 준수하여 무승인 다운로드를 수행하지 않고 `NOT RUN`으로 기록했으며, 본 보고서 5절 및 `run_ag01_verification.py`에 정확한 AVD 생성·설치·AOD 전환·캡처 재현 명령을 기록했다.

---

## 4. 요구사항 및 검증 추적표

| 요구사항 / 완료 기준 | 구현 파일·경로 | 시험 ID | 예상 결과 | 실제 결과 | 증거·SHA | 판정 |
|---|---|---|---|---|---|---|
| **R-02**: WFF 2~5 capability별 빌드 및 스키마 분리 관리 | `tests/compatibility/ag-01/fixtures/wff2..5/*.xml`, `run_ag01_verification.py` | `T-AG01-SCHEMA-POS`, `T-AG01-APK` | 버전별 공식 스키마 PASS 및 격리 APK 6종 clean build PASS | 24/24 교차 검증 PASS, 6/6 격리 APK Clean Build PASS | 4.1~4.3절 표 및 APK/XML SHA-256 | **PASS** (정적/빌드) |
| **R-06 / P03**: WFF 4+ AOD 전환 객체 연속성 및 WFF 2/3 정적 대체 | `poc_wff4_continuity.xml`, `poc_wff2_static_aod.xml`, `poc_wff3_part_blend_aod.xml` | `T-AG01-UNIT-02`, `T-AG01-UNIT-03`, `T-AG01-APK-WFF4-CONT` | 단일 `DigitalClock` 위치·크기·색상 보간, `startOffset+duration<=1.0`, WFF 4/5 PASS & WFF 2/3 대체 PASS | 스키마·구조·격리 APK·메모리(2.26 MiB) 모두 PASS; 실기기/에뮬레이터 영상은 NOT RUN | XML SHA `f70f8ef9...`, APK SHA `cd2732fb...` | **PARTIAL** (스키마/APK PASS, 런타임 영상 NOT RUN) |
| **R-07 / P07**: 숫자 전환 및 이벤트 모션 트리거 지원 조건 확인 | `poc_wff4_motion_triggers.xml` | `T-AG01-UNIT-05`, `T-AG01-APK-WFF4-MOT` | `hh_10`/`hh_1`/`mm_10`/`mm_1` 컨테이너 모션 및 `<Transform><Animation>` 스키마/APK/메모리 PASS | WFF 4/5 스키마 PASS, APK 빌드 및 AOD 메모리(3.03 MiB ≤ 7 MiB) PASS | XML SHA `745df395...`, APK SHA `3dd6808d...` | **PARTIAL** (스키마/APK/메모리 PASS, 런타임 NOT RUN) |
| **R-08 / P06**: 손목 기울기(Gyro) 기반 반사광·시차 조건 확인 | `poc_wff4_motion_triggers.xml` | `T-AG01-UNIT-05`, `T-AG01-APK-WFF4-MOT` | `<Gyro>` `sensorSourceType` 수식 및 AOD 비활성화 스키마/APK PASS | WFF 4/5 스키마 PASS, APK 빌드 및 메모리(2.26 MiB active) PASS | XML SHA `745df395...`, APK SHA `3dd6808d...` | **PARTIAL** (스키마/APK PASS, 센서 실기기 NOT RUN) |
| **R-12 / P08**: WFF 4 `Reference` 및 합성 컴플리케이션 다중 그래픽 제어 | `poc_wff4_reference_complication.xml` | `T-AG01-UNIT-04`, `T-AG01-APK-WFF4-REF` | 단일 소스 `<Reference>` 5개로 도형·패널·색상·텍스트 동시 제어, 스키마/APK/메모리 PASS | WFF 4/5 스키마 PASS, WFF 2/3 거부 PASS, 격리 APK·메모리(2.26 MiB) PASS | XML SHA `e7abd38b...`, APK SHA `713dea16...` | **PARTIAL** (스키마/APK PASS, 런타임 NOT RUN) |
| **R-17 / R-18**: 데이터 누락/오류를 `0`으로 표시하지 않고 기본 시계 유지 | `poc_wff2_static_aod.xml`, `poc_wff4_reference_complication.xml`, `poc_wff5_blend_features.xml` | `T-AG01-UNIT-04` | 날씨/컴플리케이션 누락 시 `WEATHER --`, `DATA --`, `NO SOURCE --` 표시 및 시계 독립 동작 | `<Condition>` 분기 및 `--` fallback 구조/스키마 검증 PASS | XML SHA `2b77582a...`, `e7abd38b...` | **PASS** (설계/스키마) |
| **R-20**: 공식 WFF 메모리 예산(활성 ≤70 MiB, AOD ≤7 MiB) 준수 | 6종 격리 PoC APK 전체 | `T-AG01-MEM-01..06` | `maxActiveBytes <= 73,400,320`, `maxAmbientBytes <= 7,340,032` | 5종 APK 활성/AOD `2,371,712` bytes (2.26 MiB), 1종(4분할 숫자) 활성 `2,371,712` / AOD `3,181,712` bytes (3.03 MiB)로 6/6 PASS | Memory Evaluator 1.5.1 `b87dde8` JSON 리포트 | **PASS** (공식 자산 추정기 기준) |
| **R-22**: 상위 기능 하위 침투 검출 및 검증 재현성 | `fixtures/negative/neg_*.xml` (7종), `test_ag01_suite.py` | `T-AG01-SCHEMA-NEG`, `T-AG01-UNIT-01..10`, `T-BASE-UNIT` | 하위 버전 침투 100% 검출(FAILED), 기존 40 단위 시험 + 신규 10 테스트 PASS | 52/52 스키마 교차 검증 PASS, 기존 40 + 신규 10 단위 시험 PASS | 4.2절 매트릭스 표 | **PASS** |
| **R-23**: 기기/에뮬레이터 설치·렌더링·AOD 전환 확인 | `run_ag01_verification.py --mode emulator` | `T-AG01-EMU-01` | 사용 가능한 격리 Wear OS 에뮬레이터에서 설치·렌더링 확인; 부재 시 NOT RUN 및 재현 절차 기록 | 로컬 Wear OS 시스템 이미지/AVD 부재 확인 → `NOT RUN` 및 재현 명령 기록 | 5절 재현 절차 | **NOT RUN** |
| **R-25**: 리소스 전용 APK(`hasCode=false`), 실행 코드/권한/컴포넌트 0, 원본 XML 일치 | 6종 격리 PoC APK 전체 | `T-AG01-APK-01..06` | `.dex`/`.so`/`.jar` 0개, `hasCode=false`, 권한/컴포넌트 0개, 패키징된 `res/raw/watchface.xml` SHA-256 100% 일치, v2 서명 PASS | 6/6 격리 APK 모두 ZIP/Manifest/XML 바이트 일치/v2 서명 100% PASS | 4.3절 APK 검증 표 | **PASS** |
| **P12**: WFF 5 `Group`/`ComplicationSlot` `blendMode` 및 신규 속성 검증 | `poc_wff5_blend_features.xml` | `T-AG01-UNIT-06`, `T-AG01-APK-WFF5` | WFF 5 스키마 PASS, WFF 2~4 거부 PASS, API 37.0 격리 APK 빌드/메모리/서명 PASS | WFF 5 스키마 PASS, WFF 2~4 `blendMode` 거부 PASS, `wff5` (`minSdk=37`) APK 빌드/메모리/서명 PASS | XML SHA `72b280c1...`, APK SHA `565aa87b...` | **PARTIAL** (스키마/API37 APK PASS, WFF5 기기 런타임 NOT RUN) |

---

## 5. 검증 결과 상세

### 5.1 실행 환경 및 도구 버전 요약

- **명령 실행 위치**: `C:\Users\scarl\Desktop\코딩 작업\AURA-Ultra` (브랜치 `agent/antigravity/AG-01`, 격리 APK 빌드는 `C:\Users\scarl\AppData\Local\Temp\aura-ag01-isolated-*` 임시 디렉터리에서 수행 후 자동 정리)
- **총 자동 시험 수**:
  - 기존 기준선 검사 (`tools/check_foundation.py`): **1 PASS / 0 FAIL**
  - 기존 단위 회귀 시험 (`tests/unit/test_*.py`): **40 PASS / 0 FAIL**
  - AG-01 신규 단위 및 스키마 매트릭스 시험 (`tests/compatibility/ag-01/test_ag01_suite.py`): **10 테스트 메서드 PASS / 0 FAIL** (내부 공식 WFF Validator 교차 검증 **52/52 subTest PASS** 포함)
  - AG-01 격리 Clean APK 빌드 및 5대 패키지 검증 (`run_ag01_verification.py --mode apk`): **6/6 PoC APK PASS / 0 FAIL** (각 APK당 Clean Build + ZIP 리소스 전용 + `apkanalyzer` Manifest + 원본 XML 바이트 일치 + Memory Footprint Evaluator 70/7 MiB + `apksigner` v2 서명 = 36개 세부 검증 항목 전원 PASS)
  - 에뮬레이터 및 실기기 런타임 시험: **NOT RUN** (로컬 Wear OS 시스템 이미지 및 연결 워치 없음)

### 5.2 공식 WFF Validator (v1.7.0) 버전별 스키마 교차 검증 매트릭스 (52/52 PASS)

#### A. 정상 PoC XML 6종 × WFF 버전 #2~#5 교차 검증 (24건)

| PoC ID | 파일 경로 (`tests/compatibility/ag-01/fixtures/...`) | 원본 XML SHA-256 | 최소 버전 | WFF #2 | WFF #3 | WFF #4 | WFF #5 | 판정 |
|---|---|---|---:|---|---|---|---|---|
| `poc_wff2_static_aod` | `wff2/poc_wff2_static_aod.xml` | `2b77582a27a201c96925e631f8d6cd9147d207258b6161613fee063deb62f401` | 2 | **PASSED** | **PASSED** | **PASSED** | **PASSED** | **PASS** (4/4) |
| `poc_wff3_part_blend_aod` | `wff3/poc_wff3_part_blend_aod.xml` | `4914c959de127803753c93609d79ed27e51006416129b6221adc3ce2331c7a5d` | 3 | **FAILED** (예상 거부: `PartDraw@blendMode`) | **PASSED** | **PASSED** | **PASSED** | **PASS** (4/4) |
| `poc_wff4_continuity` | `wff4/poc_wff4_continuity.xml` | `f70f8ef90b3f3418381f1b749c8fd6ef3cb01a88dc5302008f560d045b04c582` | 4 | **FAILED** (예상 거부: `Variant@startOffset`) | **FAILED** (예상 거부: `Variant@startOffset`) | **PASSED** | **PASSED** | **PASS** (4/4) |
| `poc_wff4_reference_complication` | `wff4/poc_wff4_reference_complication.xml` | `e7abd38b9c36efde20c1b40923aeed2a244750e1e0b7a5d77c2c58b4187a6f6d` | 4 | **FAILED** (예상 거부: `Variant@startOffset`) | **FAILED** (예상 거부: `Variant@startOffset`) | **PASSED** | **PASSED** | **PASS** (4/4) |
| `poc_wff4_motion_triggers` | `wff4/poc_wff4_motion_triggers.xml` | `745df3951f3d0333f3baef8e7cc2e405fa6e8cba69ff052510f6a21d7ab507d3` | 4 | **FAILED** (예상 거부: `Variant@startOffset`) | **FAILED** (예상 거부: `Variant@startOffset`) | **PASSED** | **PASSED** | **PASS** (4/4) |
| `poc_wff5_blend_features` | `wff5/poc_wff5_blend_features.xml` | `72b280c1f5579a05460dc5ea18164fae4a3125dd8ef0825034fb013164136f47` | 5 | **FAILED** (예상 거부: `Group@blendMode`) | **FAILED** (예상 거부: `Group@blendMode`) | **FAILED** (예상 거부: `Group@blendMode`) | **PASSED** | **PASS** (4/4) |

#### B. 상위 기능 하위 침투 및 스키마 위반 검출용 Negative Fixture 7종 × WFF 버전 #2~#5 (28건)

| Negative Fixture ID | 원본 XML SHA-256 | 검증 목적 | WFF #2 | WFF #3 | WFF #4 | WFF #5 | 공식 Validator 검출 오류 원문 (하위/위반 버전) | 판정 |
|---|---|---|---|---|---|---|---|---|
| `neg_wff3_part_blend_in_wff2` | `375b3886074763807ed4d3bc921bfd32452620bb992f407c2e8c8aae57f18638` | WFF 3 `PartDraw@blendMode`의 WFF 2 침투 검출 | **FAILED** (검출 성공) | PASSED | PASSED | PASSED | `SEVERE: [Line 7:Column 79]: cvc-complex-type.3.2.2: Attribute 'blendMode' is not allowed to appear in element 'PartDraw'.` | **PASS** |
| `neg_wff4_variant_transition_in_wff3` | `4f811993d67f5efe55357f487dd1a0e0c2be5972aa9104d6bba72636e4756894` | WFF 4 `Variant` 전환 속성의 WFF 2/3 침투 검출 | **FAILED** (검출 성공) | **FAILED** (검출 성공) | PASSED | PASSED | `SEVERE: [Line 6:Column 124]: cvc-complex-type.3.2.2: Attribute 'startOffset' is not allowed to appear in element 'Variant'.` | **PASS** |
| `neg_wff4_reference_in_wff3` | `d009a0629d018506ca00a1c9478be1daeada5f9e3ee51979235889a917a6dcbd` | WFF 4 `<Reference>` 태그의 WFF 2/3 침투 검출 | **FAILED** (검출 성공) | **FAILED** (검출 성공) | PASSED | PASSED | `SEVERE: [Line 8:Column 72]: cvc-complex-type.2.4.a: Invalid content was found starting with element 'Reference'.` | **PASS** |
| `neg_wff5_group_blend_in_wff4` | `cf17eb33f7e688c9e615409d4e95d3fc85ad20c4208646703f3753b09463e9e9` | WFF 5 `Group@blendMode`의 WFF 2/3/4 침투 검출 | **FAILED** (검출 성공) | **FAILED** (검출 성공) | **FAILED** (검출 성공) | PASSED | `SEVERE: [Line 5:Column 96]: cvc-complex-type.3.2.2: Attribute 'blendMode' is not allowed to appear in element 'Group'.` | **PASS** |
| `neg_wff5_complicationslot_blend_in_wff4` | `d871d14b92c758748ba2b0383ea905264264edb7c42387fd8111fcdbba54c673` | WFF 5 `ComplicationSlot@blendMode`의 WFF 2/3/4 침투 검출 | **FAILED** (검출 성공) | **FAILED** (검출 성공) | **FAILED** (검출 성공) | PASSED | `SEVERE: [Line 6:Column 98]: cvc-complex-type.3.2.2: Attribute 'blendMode' is not allowed to appear in element 'ComplicationSlot'.` | **PASS** |
| `neg_wff5_stroke_join_font_minsize_in_wff4` | `b7854925c66f21b71985276d18fdbb3e73beca61951cdc063a1a1326992e62ff` | WFF 5 `Stroke@join` 및 `Font@minSize`의 WFF 2/3/4 침투 검출 | **FAILED** (검출 성공) | **FAILED** (검출 성공) | **FAILED** (검출 성공) | PASSED | `SEVERE: [Line 9:Column 76]: cvc-complex-type.3.2.2: Attribute 'join' is not allowed to appear in element 'Stroke'.` | **PASS** |
| `neg_wff4_invalid_variant_and_reference_parent` | `1f686be34957a34bccdb14a4a5dc1f2fa76c62f60b8b00a0de4a362b6babf993` | `Variant@duration="1.35"` (>1.0) 및 `DigitalClock` 직속 `Reference` 오류 검출 | **FAILED** (검출 성공) | **FAILED** (검출 성공) | **FAILED** (검출 성공) | **FAILED** (검출 성공) | `SEVERE: [Line 6:Column 125]: cvc-maxInclusive-valid: Value '1.35' is not facet-valid with respect to maxInclusive '1.0E0'` & `Invalid content was found starting with element 'Reference'` | **PASS** |

---

### 5.3 격리된 임시 작업 공간 Clean APK 빌드 및 5대 패키지 검증 결과 (6/6 APK PASS)

각 PoC XML을 격리된 임시 디렉터리(`C:\Users\scarl\AppData\Local\Temp\aura-ag01-isolated-*`)의 flavor override 경로(`apps/watchface/src/wffN/res/raw/watchface.xml`)에 주입하여 Clean Gradle Build(`gradlew.bat --no-daemon --stacktrace clean :apps:watchface:assembleWffNDebug`)를 실행하고 검증한 결과는 다음과 같다.

| PoC ID | 빌드 프로필 (minSdk / WFF) | 생성 APK 파일명 (크기 bytes) | 격리 빌드 APK SHA-256 | 원본 & 패키징 XML SHA-256 일치 (`res/raw/watchface.xml`) | 리소스 전용 & 컴파일 Manifest (`hasCode=false`) | Memory Footprint (`total` / `maxActive` / `maxAmbient` bytes) | Debug v2 서명 (`apksigner`) 및 인증서 SHA-256 | 판정 |
|---|---|---|---|---|---|---:|---|---|
| `poc_wff2_static_aod` | `wff2` (API 34 / WFF 2) | `watchface-wff2-debug.apk` (`73,238` B) | `a7d1235318e7b1c4af82454acccba5be2a500a35d83f0a23c496c81a41d923af` | `2b77582a27a201c96925e631f8d6cd9147d207258b6161613fee063deb62f401` (100% 일치) | PASS (`.dex`/`.so` 0개, 권한/컴포넌트 0개) | `2,371,712` / `2,371,712` (2.26 MiB) / `2,371,712` (2.26 MiB) | PASS (`v2=true`, cert `a3e19480...3b22c442`) | **PASS** |
| `poc_wff3_part_blend_aod` | `wff3` (API 35 / WFF 3) | `watchface-wff3-debug.apk` (`72,910` B) | `7a588ef13ed383c063bff225c08018f927bdc5d624aa470e735eaf981bf2ece5` | `4914c959de127803753c93609d79ed27e51006416129b6221adc3ce2331c7a5d` (100% 일치) | PASS (`.dex`/`.so` 0개, 권한/컴포넌트 0개) | `2,371,712` / `2,371,712` (2.26 MiB) / `2,371,712` (2.26 MiB) | PASS (`v2=true`, cert `a3e19480...3b22c442`) | **PASS** |
| `poc_wff4_continuity` | `wff4` (API 36 / WFF 4) | `watchface-wff4-debug.apk` (`73,574` B) | `cd2732fb26bbf3a6d22f7e459fbaba8ea4047f9b6530051005ce8c135afb8da7` | `f70f8ef90b3f3418381f1b749c8fd6ef3cb01a88dc5302008f560d045b04c582` (100% 일치) | PASS (`.dex`/`.so` 0개, 권한/컴포넌트 0개) | `2,371,712` / `2,371,712` (2.26 MiB) / `2,371,712` (2.26 MiB) | PASS (`v2=true`, cert `a3e19480...3b22c442`) | **PASS** |
| `poc_wff4_reference_complication` | `wff4` (API 36 / WFF 4) | `watchface-wff4-debug.apk` (`74,682` B) | `713dea16b5f9956b0243fcca10babff5feec8e92fd7455a2d0cc301ebee7c2e6` | `e7abd38b9c36efde20c1b40923aeed2a244750e1e0b7a5d77c2c58b4187a6f6d` (100% 일치) | PASS (`.dex`/`.so` 0개, 권한/컴포넌트 0개) | `2,371,712` / `2,371,712` (2.26 MiB) / `2,371,712` (2.26 MiB) | PASS (`v2=true`, cert `a3e19480...3b22c442`) | **PASS** |
| `poc_wff4_motion_triggers` | `wff4` (API 36 / WFF 4) | `watchface-wff4-debug.apk` (`73,738` B) | `3dd6808d06baa48024139ecf6193111d3ceae3baa8be3efe19794c13fa0291e9` | `745df3951f3d0333f3baef8e7cc2e405fa6e8cba69ff052510f6a21d7ab507d3` (100% 일치) | PASS (`.dex`/`.so` 0개, 권한/컴포넌트 0개) | `2,371,712` / `2,371,712` (2.26 MiB) / **`3,181,712` (3.03 MiB)** | PASS (`v2=true`, cert `a3e19480...3b22c442`) | **PASS** |
| `poc_wff5_blend_features` | `wff5` (API 37 / WFF 5) | `watchface-wff5-debug.apk` (`73,650` B) | `565aa87b8a76d33ea592fed384a107c03e5ab31dfbea78fc966e987d5ce32027` | `72b280c1f5579a05460dc5ea18164fae4a3125dd8ef0825034fb013164136f47` (100% 일치) | PASS (`.dex`/`.so` 0개, 권한/컴포넌트 0개) | `2,371,712` / `2,371,712` (2.26 MiB) / `2,371,712` (2.26 MiB) | PASS (`v2=true`, cert `a3e19480...3b22c442`) | **PASS** |

> [!NOTE]
> - 모든 6종 APK는 프로젝트 목표 예산인 활성 `70 MiB` (`73,400,320` bytes) 및 AOD `7 MiB` (`7,340,032` bytes) 이내를 큰 여유로 통과했다.
> - 또한 `src/wffN/res/raw/watchface.xml` flavor override가 공통 `src/main/res/raw/watchface.xml`보다 우선 선택되어 APK 내부 `res/raw/watchface.xml`에 바이트 단위로 100% 동일하게 패키징됨을 격리 빌드로 최초 실증했다 (`GPT-02`에서 이관된 실제 flavor override 빌드 검증 완료).

---

### 5.4 전체 시험 실행 요약표

| 시험 ID | 필수/선택 | 종류 | 명령·대상 버전 | 기대 결과 | 실제 결과 | 판정 | 로그·증거 |
|---|---|---|---|---|---|---|---|
| `T-BASE-INV` | 필수 | 정적 불변조건 | `python tools/check_foundation.py` | 기존 저장소 불변조건 PASS | `PASS: resource-only manifest, XML structure, AOD invariant, preview, flavor matrix, tokens` | **PASS** | 콘솔 출력 (exit 0) |
| `T-BASE-UNIT` | 필수 | 단위 회귀 | `python -m unittest discover -s tests/unit -p "test_*.py" -v` | 기존 40개 단위 시험 전부 PASS | `Ran 40 tests in 0.037s - OK` (40 PASS / 0 FAIL) | **PASS** | 콘솔 출력 (exit 0) |
| `T-AG01-UNIT` | 필수 | 단위·도구·스키마 매트릭스 | `python -m unittest discover -s tests/compatibility/ag-01 -p "test_*.py" -v` | 10개 테스트 메서드 및 52개 공식 validator subTest 전부 PASS | `Ran 10 tests - OK` (10 PASS / 0 FAIL, 52 validator subTests PASS) | **PASS** | `test_ag01_suite.py` |
| `T-AG01-SCHEMA` | 필수 | 공식 WFF Validator 1.7.0 | `python tests/compatibility/ag-01/run_ag01_verification.py --mode schema` | 정상 PoC 6종×4버전(24건) 및 negative 7종×4버전(28건) = 52건 모두 기대 판정 일치 | 52/52 기대 판정(`PASS_EXPECTED_VALID` / `PASS_EXPECTED_REJECTED_ON_LOWER_VERSION` / `PASS_DETECTED_INVALID`) 일치 | **PASS** | 5.2절 매트릭스 표 |
| `T-AG01-APK` | 필수 | 격리 APK Clean Build·Manifest·XML·Memory·Signature | `python tests/compatibility/ag-01/run_ag01_verification.py --mode apk` | 격리 임시 폴더에서 6종 PoC APK clean build, 리소스 전용, Manifest, XML 일치, 70/7 MiB 예산, v2 서명 PASS | 6/6 PoC APK 전 항목 PASS (`BUILD SUCCESSFUL`) | **PASS** | 5.3절 APK 검증 표 |
| `T-AG01-EMU` | 필수(환경 조건부) | 격리 Wear OS 에뮬레이터 런타임 | `python tests/compatibility/ag-01/run_ag01_verification.py --mode emulator` | 사용 가능한 격리 에뮬레이터가 있으면 설치·렌더링·AOD 시험, 없으면 `NOT RUN` 및 재현 방법 기록 | 로컬 Wear OS 시스템 이미지(`android-wear`) 및 AVD 부재 확인 → `NOT RUN` 기록 | **NOT RUN** | 6절 에뮬레이터 재현 절차 |
| `T-AG01-DEVICE` | 선택(승인 조건부) | 실제 사용자 워치 설치·모션·전력 | `adb devices -l` (읽기 전용 확인만 수행) | 연결된 기기 확인; 승인 없는 설치/설정 변경 금지 | 연결된 워치 0대 (`List of devices attached` 비어 있음) → `NOT RUN` | **NOT RUN** | `adb devices -l` (exit 0) |

---

## 6. 격리 Wear OS 에뮬레이터 및 실기기 런타임 미실시 사유와 정확한 재현 절차

### 6.1 미실시(`NOT RUN`) 사유
1. `C:\Users\scarl\AppData\Local\Android\Sdk\system-images`에 모바일/폴더블용 `android-36.1\google_apis_playstore\x86_64`만 설치되어 있으며, Wear OS 에뮬레이터용 시스템 이미지(`android-wear`)가 설치되어 있지 않다.
2. `emulator.exe -list-avds` 결과 생성된 AVD가 0개이며, `adb.exe devices -l` 결과 연결된 에뮬레이터 또는 물리 워치가 0대다.
3. 작업지시서 `AG-01.md` 5항(*"새 SDK/에뮬레이터 다운로드, 유료 서비스, 계정 권한 변경 등 추가 환경 조치는 사용자 승인 없이 하지 않는다. 환경이 없으면 NOT RUN, 구체적인 재현 절차와 필요한 환경을 남긴다"*)을 엄격히 준수하여 임의의 대용량 시스템 이미지 다운로드를 수행하지 않았다.

### 6.2 필요한 환경 및 정확한 재현 명령
사용자가 Wear OS 시스템 이미지 설치를 승인하거나 해당 이미지가 설치된 환경에서는 아래 명령으로 AG-01의 6종 PoC APK 빌드부터 격리 에뮬레이터 설치, 워치 페이스 활성화, AOD 전환, 스크린샷/연속 모션 화면 녹화까지 즉시 재현할 수 있다.

```powershell
# 1. 필요한 Wear OS 6 (API 36, WFF 4) 및 Wear OS 7 (API 37.0, WFF 5) 시스템 이미지 설치 (사용자 승인 후 실행)
C:\Users\scarl\AppData\Local\Android\Sdk\cmdline-tools\latest\bin\sdkmanager.bat `
  "system-images;android-36;android-wear;x86_64" `
  "system-images;android-37.0;android-wear;x86_64"

# 2. 격리된 원형 Wear OS AVD 생성 (454x454 / 480x480 원형 프로필)
C:\Users\scarl\AppData\Local\Android\Sdk\cmdline-tools\latest\bin\avdmanager.bat create avd `
  -n aura_ag01_wear36_round `
  -k "system-images;android-36;android-wear;x86_64" `
  -d wearos_large_round

# 3. 격리 에뮬레이터 부팅 (스냅샷 저장 비활성화)
Start-Process C:\Users\scarl\AppData\Local\Android\Sdk\emulator\emulator.exe `
  -ArgumentList "-avd aura_ag01_wear36_round -no-snapshot -no-boot-anim"

# 4. 부팅 완료 및 기기 속성 확인
adb wait-for-device
adb shell getprop ro.product.model
adb shell getprop ro.build.version.sdk
adb shell wm size

# 5. AG-01 격리 APK 빌드 및 설치·AOD 전환·연속 모션 녹화
python tests/compatibility/ag-01/run_ag01_verification.py --mode all
# (임시 빌드 폴더에서 생성된 watchface-wff4-debug.apk 설치 후)
adb install -r watchface-wff4-debug.apk
adb exec-out screencap -p > docs/evidence/AG-01/active_wff4.png
# 연속 모션 녹화 시작 (백그라운드) 후 AOD 진입(KEYCODE_SLEEP) 및 복귀(KEYCODE_WAKEUP)
adb shell screenrecord --time-limit 8 /sdcard/ag01_aod_transition.mp4
adb shell input keyevent KEYCODE_SLEEP
adb exec-out screencap -p > docs/evidence/AG-01/ambient_wff4.png
adb shell input keyevent KEYCODE_WAKEUP
adb pull /sdcard/ag01_aod_transition.mp4 docs/evidence/AG-01/ag01_aod_transition.mp4
```

---

## 7. 구현 후 별도 검토 (G5 Self-Review)

- **검토 유형**: 구현 단계와 분리된 별도 자기 재검토 (독립 에이전트 또는 사람의 리뷰가 아님)
- **검토 대상**: `git status` 및 `tests/compatibility/ag-01/**` 전체 파일, `AG-01.md` 지시서, `MOTION_SPEC.md`, `COMPATIBILITY.md`, `DATA_INTELLIGENCE.md`, `PERFORMANCE.md`, 공식 WFF 2~5 XSD 스키마

| 결함 ID | 심각도 | 위치·재현 | 증거 | 수정/이관 | 재검증 |
|---|---|---|---|---|---|
| `AG01-REV-01` | P1 (수정 완료) | `poc_wff4_reference_complication.xml`, `poc_wff5_blend_features.xml`: 비가시 `<Reference>` 발행 노드에 자식 도형 없는 `<PartDraw>`를 사용하여 `cvc-complex-type.2.4.b` 스키마 검증 실패 | `wff-validator.jar` 실행 시 `The content of element 'PartDraw' is not complete` 출력 | 비가시 계산/발행 노드를 `<Group alpha="0">`으로 변경하여 도형 자식 강제 제약을 해소하고 기술 규칙으로 문서화 | `run_ag01_verification.py --mode all` 및 52/52 스키마 검증 **PASS** |
| `AG01-REV-02` | P2 (수정 완료) | `poc_wff4_motion_triggers.xml` 11행 `<Group name=" ActiveDecoration"` 속성값 선행 공백 및 `test_ag01_suite.py` 메서드명 오타 | 파일 원문 대조에서 발견 | 선행 공백 제거 및 메서드명 수정 | 단위 테스트 10/10 **PASS** |
| `AG01-REV-03` | P2 (보완 완료) | `test_ag01_suite.py`: `startOffset + duration > 1.0` 범위 초과 및 금지된 부모(`DigitalClock`) 아래 `<Reference>` 배치를 구조 검사기가 검출하는 G2 회귀 테스트 보강 필요 | G5 코드 리뷰 중 테스트 커버리지 점검 | `test_detects_variant_window_overflow_and_invalid_reference_parent` 테스트를 추가하여 negative fixture 7의 구조적 위반 검출을 이중 검증 | `unittest` 10/10 **PASS** |

---

## 8. 종료 게이트 (G0 ~ G7) 판정

| 게이트 | 결과 | 증거 또는 미적용 사유 |
|---|---|---|
| **G0 사전 검증** | **PASS** | 매 작업 턴 PRE-FLIGHT 수행, 기준 HEAD `fe4e19d7c6e97c043e4f31cb5960bdb430fd507b` 및 모든 필수 운영·설계 문서, 직전 CI `46002470824` 확인 완료 |
| **G1 구현/요구사항** | **PASS** | AG-01 구현 범위 1~8번 전체 구현 및 요구사항(`R-02/06/07/08/12/17/18/20/22/23/25`, `P03/06/07/08/12`) 추적표 연결 완료 |
| **G2 검증 도구** | **PASS** | 공식 WFF Validator 1.7.0의 버전별 실패 검출(7종 negative fixture + 상위 PoC 하위 버전 교차 거부 총 28+10=38건 거부 확인) 및 `require_rejection` 단위 회귀 시험 통과 |
| **G3 시험/회귀** | **PASS** | 기존 `check_foundation.py` PASS, 기존 단위 시험 40/40 PASS, 신규 AG-01 시험 10/10 (52 validator subTests) PASS, 격리 Clean APK 6/6 빌드·검증 PASS |
| **G4 분야별 검증** | **PARTIAL** | WFF 정적 스키마(52/52), 격리 APK 리소스 전용·Manifest·원본 XML 일치·공식 메모리 추정(70/7 MiB)·Debug 서명(6/6) 모두 PASS. 로컬 Wear OS 에뮬레이터 및 실기기 렌더링·센서·전력 측정은 환경 부재로 `NOT RUN` |
| **G5 별도 재검토** | **PASS** | 별도 자기 재검토를 통해 `AG01-REV-01..03` 3건을 식별·수정하고 전체 테스트 및 격리 APK 빌드를 재실행하여 통과 확인 (독립 에이전트 리뷰 아님 명시) |
| **G6 증거 및 판정** | **PASS** | 기준 SHA, 6종 원본 PoC XML SHA-256, 7종 negative XML SHA-256, 6종 격리 APK SHA-256, 바이트 단위 메모리 리포트 및 인증서 SHA-256 일치 확인 |
| **G7 문서/재개** | **PASS** | `docs/evidence/AG-01/REPORT.md` 및 `tests/compatibility/ag-01/README.md` 작성, 중앙 `STATUS`/`WORK_LOG`/`BLOCKERS` 갱신 제안 포함, 독립 브랜치 `agent/antigravity/AG-01` 반영 |

- **최종 작업 판정 및 이유**: **PARTIAL** (AG-01의 모든 코드·PoC XML·스키마·격리 APK 빌드·메모리·서명 검증은 100% 성공했으나, 로컬 환경에 Wear OS 에뮬레이터 시스템 이미지 및 물리 워치가 없어 런타임 렌더링·AOD 전환 영상 시험이 `NOT RUN`이므로 `VERIFICATION_PROTOCOL.md` 및 `AG-01.md`에 따라 `PARTIAL`로 판정함).
- **제품 출시 판정(별도)**: **NO-GO** (초기 PoC 및 개발 기반 단계; 실기기·전력·전체 테마 미구현).
- **미해결 장애 / 이관 및 해결 조건**:
  - `B-002` (BLOCKED/P1): 실기기 또는 Wear OS 에뮬레이터 시스템 이미지가 준비된 환경에서 6절의 재현 명령으로 `watchface-wff4-debug.apk` 및 `watchface-wff5-debug.apk` 설치·렌더링·AOD 전환 영상을 확보해야 함.
  - `B-003` (OPEN/P1): WFF 5 전용 기능(`Group`/`ComplicationSlot` `blendMode`, `Stroke join`, `Font minSize`, `Text lineSpacing`/`verticalAlign`)의 공식 스키마 및 API 37.0 격리 APK 빌드·메모리·서명 통과까지 확인 완료. 실제 Wear OS 7(API 37) 기기/에뮬레이터 런타임 렌더링만 남음.
  - `B-005` (OPEN/P1): WFF 4 `Variant` 전환 속성·보간, `<Reference>` 단일 소스 다중 그래픽 제어, `<Gyro>`, 자리별 `TimeText` 및 `<Transform><Animation>`의 공식 스키마·격리 APK 빌드·메모리 평가 증거 확보 완료. 실기기 시각/모션 영상 확인만 남음.
- **다음 작업 ID, 읽을 문서, 첫 행동·명령, 기대 결과**:
  - 다음 연계 작업: `GPT-03` (공통 토큰 기반 결정적 WFF·그래픽 자산 생성 자동화) 및 이후 `GPT-05` / `WO-05` / `WO-07` / `WO-08` (본 AG-01 PoC의 `Variant`, `Reference`, `Group`/`ComplicationSlot` `blendMode` 계약을 생성기 템플릿에 통합).
  - 읽을 문서: `AGENTS.md` → `docs/STATUS.md` → `docs/evidence/AG-01/REPORT.md` → `tests/compatibility/ag-01/README.md`.
  - 첫 행동·명령:
    ```bash
    python -m unittest discover -s tests/compatibility/ag-01 -p "test_*.py" -v
    python tests/compatibility/ag-01/run_ag01_verification.py --mode all
    ```
  - 기대 결과: 10개 단위/매트릭스 시험(52건 공식 validator 교차 검증) `OK`, 6종 격리 PoC APK Clean Build·Manifest·XML·Memory·Signature `PASS`.

---

## 9. 중앙 운영 문서(`STATUS.md`, `WORK_LOG.md`, `BLOCKERS.md`, `agent-orders/README.md`) 갱신 제안

외부 에이전트 작업 통제 규정(`AGENTS.md` 43행 및 `docs/operations/agent-orders/README.md`)에 따라 중앙 운영 문서는 직접 수정하지 않고 총괄 담당자가 병합 후 반영할 수 있도록 아래 갱신 제안을 제출한다.

### 9.1 `docs/STATUS.md` 추가 제안

```markdown
## AG-01 (Antigravity CLI) — WFF 4/5 기능 및 격리 APK 실행 검증 PoC 결과
기준 main SHA `fe4e19d7c6e97c043e4f31cb5960bdb430fd507b`, 브랜치 `agent/antigravity/AG-01`. 상세 증거: `docs/evidence/AG-01/REPORT.md`.
- 공식 WFF Validator 1.7.0 내장 XSD(WFF 1~5) 및 실행 검증을 통해 WFF 4 `Variant` 전환(`duration`, `startOffset`, 6종 `interpolation`, `controls`, `angleDirection`, `startOffset + duration <= 1.0` 규칙), WFF 4 `<Reference>` 허용 부모 21종/금지 부모 8종 및 합성 `ComplicationSlot` 다중 그래픽 제어, WFF 5 `<Group>`/`<ComplicationSlot>` `blendMode` 및 `Stroke join`/`Font minSize`/`Text lineSpacing`, `<Gyro>` 및 자리별 `TimeText`(`hh_10`, `hh_1`, `mm_10`, `mm_1`) 조건을 검증했다.
- 정상 PoC XML 6종 × 4버전(24건) 및 상위 기능 하위 침투 검출용 negative fixture 7종 × 4버전(28건) = 총 52건 공식 validator 교차 검증 100% PASS (`test_ag01_suite.py` 10 tests OK). 기존 40 단위 시험 및 `check_foundation.py` 회귀 PASS.
- 격리된 임시 작업 공간에서 flavor override(`src/wffN/res/raw/watchface.xml`)로 6종 PoC Debug APK를 Clean Build하고 리소스 전용(`hasCode=false`, `.dex` 0개), 컴파일된 Manifest, 원본 XML 바이트 일치, 공식 Memory Footprint Evaluator 1.5.1(단일 시계 PoC 5종 활성/AOD `2,371,712` bytes; 4분할 자리별 시계 PoC 활성 `2,371,712` / AOD `3,181,712` bytes로 70/7 MiB 예산 이내), `apksigner` v2 서명을 6/6 PASS로 확인했다.
- 로컬 Android SDK에 Wear OS 에뮬레이터 시스템 이미지(`android-wear`)와 연결된 워치가 없어 에뮬레이터/실기기 런타임 시험은 무승인 다운로드 금지 규정에 따라 `NOT RUN`으로 기록하고 재현 명령을 제공했다. 판정: AG-01 PARTIAL (정적 스키마·격리 APK·메모리·서명 PASS, 런타임 NOT RUN), 제품 출시 NO-GO 유지.
```

### 9.2 `docs/operations/WORK_LOG.md` 추가 제안

```markdown
## 2026-11-27 / AG-01 — WFF 4/5 연속 모션·Reference·혼합 모드 PoC 및 격리 APK 검증
- 기준 부모 SHA `fe4e19d7c6e97c043e4f31cb5960bdb430fd507b`, 브랜치 `agent/antigravity/AG-01`. PRE-FLIGHT 수행 완료.
- `tests/compatibility/ag-01/`에 WFF 2 정적 AOD 대체(`poc_wff2_static_aod.xml`), WFF 3 부품 혼합 모드(`poc_wff3_part_blend_aod.xml`), WFF 4 5단계 연속 AOD 전환(`poc_wff4_continuity.xml`), WFF 4 Reference 및 합성 컴플리케이션 다중 그래픽 제어(`poc_wff4_reference_complication.xml`), Gyro·자리별 숫자·이벤트 애니메이션 트리거(`poc_wff4_motion_triggers.xml`), WFF 5 Group/ComplicationSlot 혼합 모드(`poc_wff5_blend_features.xml`) 등 6종 정상 PoC와 7종 negative fixture, 자동 검증 스크립트(`run_ag01_verification.py`, `test_ag01_suite.py`)를 구현했다.
- 공식 WFF Validator 1.7.0 52/52 교차 검증 PASS, 격리 임시 워크스페이스 6/6 Clean APK 빌드·Manifest·리소스 전용·원본 XML 바이트 일치·Memory Footprint Evaluator 1.5.1(70/7 MiB 예산)·Debug v2 서명 PASS. 자리별 4분할 `DigitalClock` 구성이 단일 `DigitalClock` 대비 AOD 오프로드 메모리를 `+810,000` bytes (`2,371,712` → `3,181,712` bytes) 증가시키는 정량 근거를 확보했다.
- 로컬 Wear OS 에뮬레이터 이미지 및 연결 워치 부재로 런타임 시험은 `NOT RUN`. AG-01 PARTIAL, 제품 출시 NO-GO. 증거: `docs/evidence/AG-01/REPORT.md`.
```

### 9.3 `docs/operations/BLOCKERS.md` 갱신 제안

```markdown
- **B-002 (BLOCKED / P1 유지)**: 로컬 PC에 Android SDK(`platforms;android-37.0`, `build-tools;36.0.0`, `adb`, `emulator`)가 설치되어 있음을 확인했으나, Wear OS 에뮬레이터 시스템 이미지(`android-wear`)와 연결된 물리 워치가 없다(`adb devices -l` 0대, `emulator -list-avds` 0개). 에뮬레이터 시스템 이미지 설치 승인 또는 실기기 연결 필요.
- **B-003 (OPEN / P1 부분 해소)**: AG-01에서 WFF 5 전용 기능(`<Group blendMode>`, `<ComplicationSlot blendMode>`, `<Stroke join>`, `<Font minSize>`, `<Text lineSpacing verticalAlign>`)을 포함한 `poc_wff5_blend_features.xml`의 WFF 5 공식 스키마 통과, WFF 2~4 하위 침투 거부, API 37.0 격리 Clean APK 빌드(`565aa87b...`)·원본 XML 일치·메모리(`2,371,712` bytes)·v2 서명 검증까지 PASS 확인. 실제 Wear OS 7 기기/에뮬레이터 런타임 렌더링 확인 전까지 OPEN 유지.
- **B-005 (OPEN / P1 부분 해소)**: AG-01에서 WFF 4 `Variant` 전환 속성/보간(`poc_wff4_continuity.xml`), `<Reference>` 단일 소스 다중 그래픽 제어(`poc_wff4_reference_complication.xml`), `<Gyro>`·자리별 `TimeText`·`<Transform><Animation>`(`poc_wff4_motion_triggers.xml`)의 공식 스키마, 하위 버전 침투 거부, 격리 APK 빌드 및 메모리 예산(2.26 MiB / 3.03 MiB) 검증 PASS. 실기기/에뮬레이터 전환 영상 및 최종 그래픽 품질 확인 전까지 OPEN 유지.
```

### 9.4 `docs/operations/agent-orders/README.md` 상태 갱신 제안

- `Antigravity CLI` (`AG-01`) 상태를 `READY` → `PARTIAL (스키마 52/52·격리 APK 6/6·메모리·서명 PASS, 에뮬레이터/실기기 NOT RUN; docs/evidence/AG-01/REPORT.md)`로 갱신 제안.
