# GB-02 가정과 제약

설계 문서가 정하지 않은 항목은 제품 결정으로 확정하지 않는다. 아래는 이 모듈이 시험 가능한 상태 전이를 만들기 위해 코드에 넣은 후보 규칙이다. `PolicyCandidates.documented()`의 15/20, 70/50, 60초는 문서의 후보를 담은 기본값이다. 제품 상수가 아니다. 호출자가 다른 정책을 넘기면 그 값으로 같은 규칙을 적용한다.

| ID | 규칙 | 코드 | 바꾸기 전에 필요한 것 |
|---|---|---|---|
| GB02-A1 | 패키지는 `io.github.scarlel96.aura.intelligence`다. 배포 applicationId가 아니다. | 소스 패키지 | 모듈 좌표 승인 |
| GB02-A2 | 기준 시각은 `IntelligenceSample.referenceTime`뿐이다. `Instant.now`, Android, 네트워크를 호출하지 않는다. | `step` | 어댑터 WO |
| GB02-A3 | 입력 관측은 도메인의 `deriveStatus`와 `validateObservation`을 통과한 신선 `VALID` 읽기만 값으로 쓴다. 단위는 정책 토큰과 정확히 같을 때만 받는다. 환산하지 않는다. | `gateReading` | 공급원별 단위 표 |
| GB02-A4 | 정책의 퍼센트·확률 스케일을 벗어난 유한 값은 축 숫자로 올리지 않는다. 스케일 자체도 후보이다. | `OUTSIDE_CANDIDATE_SCALE` | 공급원별 범위 |
| GB02-A5 | `STALE`, 만료된 `VALID`, `UNDECLARED`, `UNAVAILABLE`, `DENIED`, `ERROR`, 구조 거절, 비유한 수는 신선한 관측으로 올리지 않는다. 누락을 0으로 만들지 않는다. | `UnusableReason` | 오류 값을 부분 표시하는 계약 |
| GB02-A6 | 전원 축은 `NORMAL`/`LOW`/`CHARGING`만 있다. 명세에 `UNKNOWN`이 없으므로 추가하지 않았다. 사용할 수 없는 배터리는 직전 축을 유지하고, 첫 스텝이면 `NORMAL`이다. 그 숫자는 공개하지 않는다. | `desiredPower` | 전원 미상을 별도 축으로 승인할 때 |
| GB02-A7 | 신선한 충전 참은 퍼센트가 낮아도 `CHARGING`이다. `POWER` 포커스가 아니고 Eco로 내리지 않는다. 신선한 충전 거짓이 충전을 벗어날 때 퍼센트가 없으면 `NORMAL`이며, 그 전환은 숫자 0이 아니다. 사용할 수 없는 충전 플래그는 충전 진입·이탈을 만들지 않는다. | `desiredPower` | 충전 중 저전력 표현을 유지하는 결정 |
| GB02-A8 | 저전력은 `<= powerEnter`에서 들어가고 `>= powerExit`에서 나온다. 그 사이는 직전이 `LOW`일 때만 `LOW`다. | `lowPower` | 실측으로 확정된 임계값 |
| GB02-A9 | 날씨·활동의 `UNKNOWN`은 명세에 있는 축 값이다. 강수 또는 경보가 사용할 수 없고 다른 신선한 날씨 입력이 없으면 `UNKNOWN`이다. 활동 토큰이 `REST`/`ACTIVE`/`EXERCISE`가 아니면 `UNKNOWN`이다. 출퇴근·업무·수면 문구로 활동이나 사용자 모드를 추론하지 않는다. | `desiredWeather`, `parseActivity` | 토큰 어휘 승인 |
| GB02-A10 | 강수는 `>= precipEnter`에서 들어가고 `<= precipExit`에서 나온다. 사이 구간은 직전이 `PRECIP`일 때만 유지한다. 직전 `ALERT`는 직전 `PRECIP`가 아니다. | `precipActive` | 실측으로 확정된 확률 스케일과 임계값 |
| GB02-A11 | 경보 진입만 긴급이다. 디바운스와 최소 유지를 건너뛴다. 경보 해제는 긴급이 아니다. 충전 진입과 신선한 충전 해제만 충전 예외다. | `step` | 해제까지 즉시 반영하는 결정 |
| GB02-A12 | 전원·날씨·활동은 한 시각에 함께 커밋한다. 긴급 또는 충전 예외 샘플은 그 샘플의 현재 목표 센서 축을 함께 반영한다. 보류 중이던 다른 목표를 샘플이 생략하면 직전 커밋을 유지한다. | `commitSensors` | 축별 독립 타이머 |
| GB02-A13 | 문서 후보는 최소 유지 60초다. 디바운스 시간은 문서에 없으므로 후보 기본값은 0이다. 둘 다 호출자가 바꿀 수 있다. 음수 시간은 정책을 거절한다. | `PolicyCandidates.documented` | 디바운스 제품 값 |
| GB02-A14 | 밝기·연결·사용자 모드는 대기 없이 반영하고 센서 유지 시각을 재설정하지 않는다. 빠지거나 사용할 수 없으면 직전 값을 유지한다. 첫 스텝 기본은 `DAY`/`ONLINE`/`DEFAULT`다. | `step` | 이 축의 미상 토큰 |
| GB02-A15 | 포커스 우선순위는 `CRITICAL > POWER > EXERCISE > WEATHER > CONTEXT > DECORATIVE`다. `ALERT`만 critical이다. `LOW`만 power다. `EXERCISE`가 weather보다 앞이다. 기본이 아닌 사용자 모드, `OFFLINE`, `NIGHT`, `ACTIVE`는 context다. | `focusOf` | 포커스 어휘 승인 |
| GB02-A16 | 품질 후보 이름은 성능 문서의 Balanced, Eco, AOD를 따른다. 항상 표시가 AOD, 그다음 저전력이 Eco, 그 외는 Balanced다. Ultra는 선택하지 않는다. OS 절전 상태와 이 품질 이름은 다르다. | `intentFor` | 프로필 적용 범위 |
| GB02-A17 | `motionAllowed`와 `particleEffectsAllowed`는 모션 감소, 항상 표시, 저전력에서 거짓이다. 둘은 항상 같다. 저전력이어도 `weatherNumbersKept`와 `timeKept`는 참이다. 이 플래그는 정책을 숨기지 말라는 뜻이다. 이번 샘플의 공개 숫자가 null이면 신선한 숫자가 없다는 뜻이지, 화면의 기존 숫자를 0이나 빈 값으로 지우라는 명령이 아니다. | `IntelligenceIntent` | 표시 계층의 캐시 규칙 |
| GB02-A18 | 시계 역전은 `referenceTime < committedAt`이다. 같은 시각은 역전이 아니다. 축과 커밋 시각과 보류는 유지하고 숫자는 공개하지 않는다. 샘플의 모션 감소·항상 표시 플래그는 관측이 아니라 호출자 설정으로 적용한다. | `step` | 역전 샘플의 설정 플래그를 무시하는 결정 |
| GB02-A19 | 첫 revision은 1이다. 0으로 만들지 않는다. 축, 포커스, 또는 공개 내용이 바뀔 때만 증가한다. 같은 공개 내용의 반복 샘플은 증가하지 않는다. 의도 revision과 상태 revision은 같다. | `finish` | revision을 샘플마다 올리는 결정 |
| GB02-A20 | `dataQuality` 집계 규칙은 명세가 미확정이라고 적는다. 이 모듈 후보는 입력이 없으면 `SETTINGS_ONLY`, 들어온 채널이 모두 신선하면 `FRESH`, 아니면 `DEGRADED`다. 생략된 채널은 저하로 세지 않는다. | `gateSample` | 품질 집계 승인 |
| GB02-A21 | 이유 코드 이름은 이 모듈의 후보다. 도메인 초안은 불투명 문자열로만 받는다. 제품 어휘로 중앙 문서에 확정하지 않는다. | `ReasonCode` | 표현 어휘 승인 |
| GB02-A22 | `PresentationIntentDraft.paletteId`는 채우지 않는다. 상황 스냅샷 초안은 만들지 않는다. 도메인 축 문자열을 여기서 얼리지 않기 위해서다. | `toPresentationDraft` | 스냅샷 매핑 WO |
| GB02-A23 | 의존성은 도메인 모듈과 Kotlin 2.4.21 테스트 아티팩트뿐이다. | `build.gradle.kts` | 추가 라이브러리 승인 |
| GB02-A24 | 실기기, 실제 공급원, 그래픽, OS 절전, 배터리 측정은 실행하지 않았다. | 시험 범위 | 기기 연결. B-002 |

도메인 가정 A17의 "FSM은 없다"는 도메인 모듈 안의 문장이다. 이 모듈이 상태 머신을 가진다고 그 문장을 고치지 않는다.
