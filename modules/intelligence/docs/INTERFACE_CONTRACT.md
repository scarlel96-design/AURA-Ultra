# GB-02 인터페이스 계약

상태: 순수 Kotlin 상태 머신. 제품 출시 계약이 아니다. 도메인 타입은 [modules/domain/docs/INTERFACE_CONTRACT.md](../../domain/docs/INTERFACE_CONTRACT.md)를 그대로 사용한다. 가정은 [ASSUMPTIONS.md](ASSUMPTIONS.md)에 있다. 정본 축과 우선순위는 [DATA_INTELLIGENCE.md](../../../docs/DATA_INTELLIGENCE.md)를 따른다.

## 입력

`step(previous, sample, policy)`만 전이를 만든다.

`previous`가 null이면 첫 스텝이다. `sample.referenceTime`은 호출자가 넣는다. 관측 필드는 도메인 `Observation`이거나 null이다. null은 생략이다. 생략은 실패한 관측이 아니다.

`PolicyCandidates.documented()`는 문서 후보 15/20, 70/50, 유지 60초, 디바운스 0, 단위 토큰 `percent`/`percent`/`token`/`flag`, 스케일 0 이상 100 이하를 반환한다. `issues()`가 비어 있지 않으면 `StepResult.PolicyRejected`이고 상태는 만들지 않는다.

## 게이트

각 채널은 `Absent`, `Unusable`, `Fresh` 중 하나다.

`Fresh`가 되려면 `deriveStatus`가 거절·만료 강등이 아니고, 신선도가 `FRESH`이며, 분류가 상태 `VALID`인 읽기이고, 기대 단위 검사가 통과해야 한다. 숫자는 정책 스케일 안이어야 한다. 토큰은 아래 표의 정확한 문자열이어야 한다.

사용할 수 없는 이유는 `STALE`, `UNDECLARED`, `UNAVAILABLE`, `DENIED`, `ERROR`, `REJECTED`, `UNIT_UNCHECKED`, `OUTSIDE_CANDIDATE_SCALE`, `TOKEN_UNCHECKED`로 공개 이유에 연결한다. 값은 공개하지 않는다.

## 축

| 축 | 값 | 반영 |
|---|---|---|
| power | `NORMAL`, `LOW`, `CHARGING` | 디바운스와 최소 유지. 충전 예외는 즉시 |
| weather | `NORMAL`, `PRECIP`, `ALERT`, `UNKNOWN` | 같은 센서 타이머. `ALERT`로 들어갈 때만 긴급 |
| activity | `REST`, `ACTIVE`, `EXERCISE`, `UNKNOWN` | 같은 센서 타이머 |
| light | `DAY`, `NIGHT` | 즉시. 유지 시각을 재설정하지 않음 |
| connectivity | `ONLINE`, `OFFLINE` | 즉시 |
| userMode | `DEFAULT`, `WORK`, `SLEEP`, `MANUAL` | 즉시. 사용자 설정이며 추론하지 않음 |

활동·밝기·연결·사용자 모드의 토큰은 표의 이름과 같아야 한다. 다른 문자열은 확인되지 않은 토큰이다.

## 포커스와 표현

`focusOf` 순서: `ALERT` → `CRITICAL`, `LOW` → `POWER`, `EXERCISE` → `EXERCISE`, `PRECIP` → `WEATHER`, 비기본 사용자 모드 또는 `OFFLINE` 또는 `NIGHT` 또는 `ACTIVE` → `CONTEXT`, 그 외 `DECORATIVE`.

`IntelligenceIntent.toPresentationDraft()`는 도메인 `PresentationIntentDraft`에 포커스 이름, 품질 이름, `motionAllowed`, 이유 이름, revision을 넣는다. `paletteId`는 null이다. revision은 1부터 시작하고 null을 0으로 바꾸지 않는다.

품질 이름 후보는 `BALANCED`, `ECO`, `AOD`다. 모션과 입자 허용은 모션 감소, 항상 표시, 저전력에서 거짓이다. `timeKept`와 `weatherNumbersKept`는 참을 유지한다.

## 하지 않는 일

도메인 소스를 바꾸지 않는다. 상황 스냅샷 초안을 채우지 않는다. 예보를 계산하지 않는다. 민감한 행동을 추정하지 않는다. 시스템 시계와 네트워크와 Android를 쓰지 않는다. 실기기 측정값으로 임계값을 확정하지 않는다.
