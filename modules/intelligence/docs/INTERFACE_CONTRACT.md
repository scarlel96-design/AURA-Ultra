# GB-02 인터페이스 계약

상태: 순수 Kotlin 상태 머신. 제품 출시 계약이 아니다. 도메인 타입은 [modules/domain/docs/INTERFACE_CONTRACT.md](../../domain/docs/INTERFACE_CONTRACT.md)를 그대로 사용한다. 가정은 [ASSUMPTIONS.md](ASSUMPTIONS.md)에 있다. 정본 축과 우선순위는 [DATA_INTELLIGENCE.md](../../../docs/DATA_INTELLIGENCE.md)를 따른다.

## 입력

`step(previous, sample, policy)`만 전이를 만든다.

`previous`가 null이면 첫 스텝이다. `sample.referenceTime`은 호출자가 넣는다. 관측 필드는 도메인 `Observation`이거나 null이다. null은 생략이다. 생략은 실패한 관측이 아니다.

`PolicyCandidates.documented()`는 문서 후보 15/20, 70/50, 유지 60초, 디바운스 0, 단위 토큰 `percent`/`percent`/`token`/`flag`, 스케일 0 이상 100 이하를 반환한다. `issues()`가 비어 있지 않으면 `StepResult.PolicyRejected`이고 상태는 만들지 않는다.

`issues()`는 유한하지 않은 임계값, 뒤집힌 구간, 음수 시간, 사용할 수 없는 스케일, 빈 단위를 거절한다. 유한한 전원 임계값이 퍼센트 스케일 밖이거나, 유한한 강수 임계값이 확률 스케일 밖이면 거절한다. 비교는 양 끝 포함이다. 문서 후보 15/20과 70/50은 그 스케일에서 유효하다.

## 게이트

각 채널은 `Absent`, `Unusable`, `Fresh` 중 하나다.

`Fresh`가 되려면 `deriveStatus`가 거절·만료 강등이 아니고, 신선도가 `FRESH`이며, 분류가 상태 `VALID`인 읽기이고, 기대 단위 검사가 통과해야 한다. 숫자는 정책 스케일 안이어야 한다. 토큰은 아래 표의 정확한 문자열이어야 한다.

사용할 수 없는 이유는 `STALE`, `UNDECLARED`, `UNAVAILABLE`, `DENIED`, `ERROR`, `REJECTED`, `UNIT_UNCHECKED`, `OUTSIDE_CANDIDATE_SCALE`, `TOKEN_UNCHECKED`로 공개 이유에 연결한다. 값은 공개하지 않는다.

## 축

| 축 | 값 | 반영 |
|---|---|---|
| power | `NORMAL`, `LOW`, `CHARGING` | 디바운스와 최소 유지는 전원 축의 시각만 사용. 충전 예외는 즉시. 그래픽 전력 제한은 축 확정을 기다리지 않음 |
| weather | `NORMAL`, `PRECIP`, `ALERT`, `UNKNOWN` | 날씨 축의 시각. `ALERT`로 들어갈 때만 긴급 |
| activity | `REST`, `ACTIVE`, `EXERCISE`, `UNKNOWN` | 활동 축의 시각. 긴급과 충전 예외를 물려받지 않음 |
| light | `DAY`, `NIGHT` | 즉시. 유지 시각을 재설정하지 않음 |
| connectivity | `ONLINE`, `OFFLINE` | 즉시 |
| userMode | `DEFAULT`, `WORK`, `SLEEP`, `MANUAL` | 즉시. 사용자 설정이며 추론하지 않음 |

활동·밝기·연결·사용자 모드의 토큰은 표의 이름과 같아야 한다. 다른 문자열은 확인되지 않은 토큰이다.

## 시각과 revision

`MachineState.committedAt`은 전원·날씨·활동 중 하나라도 마지막으로 확정한 시각이다. `powerCommittedAt`, `weatherCommittedAt`, `activityCommittedAt`은 각 축의 확정 시각이다. 보류 시작은 `PendingSensors.powerSince`, `weatherSince`, `activitySince`다. 다른 축이 반복해서 바뀌어도 기다리는 축의 시작 시각과 확정 시각은 다시 시작하지 않는다. `PendingSensors.since`는 아직 기다리는 축의 시작 시각 중 가장 이른 값이다. `processedAt`은 마지막으로 받아들인 `referenceTime`이다. 밝기·연결·사용자 모드만 바뀌어도 `processedAt`은 그 샘플 시각이 되고 센서 확정 시각은 그대로다.

관측 순서와 설정 순서는 다르다. 시계 역전은 `referenceTime < processedAt`이다. 축이 그대로인 뒤의 더 이른 입력도 역전이다. 같은 시각은 역전이 아니다. 상한 아래의 역전 결과는 두 시각, 센서 축, 보류를 유지하고 배터리·강수 숫자를 공개하지 않는다. 데이터 품질은 `DEGRADED`다. 역전은 이전 숫자를 거두는 경로가 아니다.

모션 감소와 항상 표시는 `CallerSettings`다. `referenceTime >= processedAt`인 샘플은 그 설정을 호출 순서대로 교체한다. 같은 시각의 나중 호출도 교체한다. 더 이른 샘플은 저장된 보호를 해제하지 못하고, 없던 보호만 올릴 수 있다.

`revision`은 1에서 시작한다. 축, 포커스, 공개 내용이 바뀔 때만 1 증가한다. 이전 값이 `Long.MAX_VALUE`이면 숫자를 감싸지 않는다. 그 상한에서 전해야 할 보호가 없으면 `StepResult.LimitReached`다. `reason`은 `REVISION_EXHAUSTED`이고 `state`는 호출자가 넘긴 이전 상태 객체다. `deliveredIntent()`는 null이다. 전해야 할 보호가 있으면 같은 revision의 `Advanced`다. 그 보호는 모션 감소나 항상 표시가 새로 켜지는 것, 그래픽 전력 제한이 새로 켜지는 것, 사용할 수 없게 된 채널의 기존 공개 숫자를 거두는 것이다.

소비자는 `StepResult.deliveredIntent()`가 null이 아니면 그 의도를 적용한다. revision이 이전과 같아도 적용한다. `LimitReached`와 `PolicyRejected`는 적용할 의도가 없다. revision이 증가할 때만 초안을 읽는 소비자는 상한의 보호를 놓친다. 그 누락은 시험 전용 소비자 둘을 같은 입력에 넣어 확인한다. Wear Services와 WFF 연결 코드는 없다.

상한의 `Advanced`는 센서 축을 바꾸지 않는다. 새 신선한 숫자로 이전 공개 숫자를 바꾸지 않는다. 생략된 채널은 이전 숫자를 유지한다. 배터리나 강수 채널이 `Unusable`이고 이전 숫자가 있으면 그 숫자만 null로 거두고 데이터 품질은 `DEGRADED`다. null은 0이 아니다. 축 변경, 새 신선한 숫자 교체, 숫자 거두기가 버려지면 이유에 `REVISION_EXHAUSTED`를 더한다. 모션 감소나 항상 표시만 켜지고 버린 변경이 없으면 그 이유를 더하지 않는다. 이미 켜진 보호와 이미 켜진 그래픽 전력 제한은 상한에서 끄지 않는다. 상한의 역전은 보호가 늘지 않고 숫자를 거둘 근거가 없으면 이전 상태 객체의 `LimitReached`다.

유지·디바운스 기한은 그 축의 확정 시각 또는 그 축의 보류 시작 시각에 정책을 더한 값이다. 그 덧셈이 시각 범위를 벗어나면 기한은 경과하지 않은 것으로 보고, 예외는 `step` 밖으로 나가지 않는다. `Duration.ofSeconds(Long.MAX_VALUE)`는 음수가 아니므로 받을 수 있다. 경보 진입은 날씨와 그 샘플의 목표 전원을 그 기한 없이 확정한다. 충전 예외는 전원만 그 기한 없이 확정한다. 활동은 그 예외들로 기한을 건너뛰지 않는다. 날씨는 충전 예외로 기한을 건너뛰지 않는다.

확정된 `CHARGING`은 충전 관측이 빠지거나 `Fresh`가 아니면 유지한다. 신선한 충전 거짓만 이탈을 만든다. 그 상태에서 신선한 낮은 배터리가 있어도 축은 `CHARGING`이고 품질은 Eco로 내려가지 않는다. 전원 축에 값을 추가하지 않는다. 신선한 낮은 배터리는 그 축과 별도로 장식과 입자를 제한한다.

## 포커스와 표현

`focusOf` 순서: `ALERT` → `CRITICAL`, 확정된 `LOW` 또는 신선한 낮은 배터리 → `POWER`, `EXERCISE` → `EXERCISE`, `PRECIP` → `WEATHER`, 비기본 사용자 모드 또는 `OFFLINE` 또는 `NIGHT` 또는 `ACTIVE` → `CONTEXT`, 그 외 `DECORATIVE`.

그래픽 전력 제한은 배터리 채널이 `Fresh`이고 저전력 히스테리시스가 참일 때 바로 켜진다. 디바운스와 최소 유지를 기다리지 않는다. 포커스가 `CRITICAL`이면 이유는 `WEATHER_ALERT`와 `POWER_LOW`다. 품질은 확정된 `LOW`일 때만 `ECO`다. 모션은 확정된 `LOW`, 모션 감소, 항상 표시에서만 꺼진다. 입자는 그때 꺼지고, 그래픽 전력 제한이 켜져도 꺼진다. `graphicsPowerLimited`는 그 제한이거나 확정된 `LOW`다. 상한 아래에서 배터리 생략은 이번 샘플의 그래픽 제한을 켜지 않는다. 확정 축이 `LOW`가 아니면 이전 스텝의 그래픽 제한은 다음 의도로 넘어가지 않는다. 상한에서 이미 켜진 제한은 끄지 않는다.

`IntelligenceIntent.toPresentationDraft()`는 도메인 `PresentationIntentDraft`에 포커스 이름, 품질 이름, `motionAllowed`, 이유 이름, revision을 넣는다. `paletteId`는 null이다. 도메인 초안은 `reasonCodes`를 생략할 수 있는 목록으로 선언한다. 이 모듈은 이유 이름을 항상 넣는다. 도메인 초안에는 입자 필드가 없으므로 그래픽 제한의 초안 표시는 포커스 이름 `POWER`와 이유 `POWER_LOW`다. `particleEffectsAllowed`는 `IntelligenceIntent`에 남긴다. revision은 1부터 시작하고 null을 0으로 바꾸지 않는다. 상한에서 소비자가 적용할 초안은 `deliveredIntent().toPresentationDraft()`다.

품질 이름 후보는 `BALANCED`, `ECO`, `AOD`다. `timeKept`와 `weatherNumbersKept`는 참을 유지한다. `reasonCodes`는 수정할 수 없는 복사본이다.

## 초기 상태

`previous`가 null이면 첫 스텝이다. revision은 1이고 보류는 없다. `committedAt`, 축별 확정 시각, `processedAt`은 그 샘플의 `referenceTime`이다. 축은 그 샘플의 목표값이고, 설정은 그 샘플의 모션 감소와 항상 표시다.

## 소비자 순서

`deliveredIntent()`는 한 결과 안의 의도를 고른다. 결과가 호출 밖에서 재정렬되면 이전 의도가 최신 보호를 덮어쓸 수 있다. 지원되는 소비자는 `step` 결과를 호출 순서대로 받고, null이 아닌 `deliveredIntent()`를 revision이 같아도 적용한다. `Advanced.state.processedAt`이 마지막으로 적용한 시각보다 이르면 그 결과는 버린다. 같은 시각은 호출 순서를 유지한다. 의도 객체에는 `processedAt`이 없다. 이 규칙 없이 결과를 재정렬하는 통합은 차단점 GB02-R05-ASYNC다. 순서 필드는 추가하지 않는다.

## 실제 공급원

호출자가 `referenceTime`을 넣는다. 기계는 시스템 시계를 읽지 않는다. 관측은 도메인 `Observation`으로 들어오고, null은 생략이며 실패한 관측이 아니다. 공개 숫자 null을 0으로 그리지 않는다. `particleEffectsAllowed`는 도메인 초안에 없으므로 초안만 보는 렌더러는 입자 제한을 놓친다. 포커스 이름 `POWER`와 이유 `POWER_LOW`를 함께 본다. 제품 임계값과 플랫폼 지원 범위는 이 계약이 확정하지 않는다.

## 구현하지 않은 기능

Wear Services, WFF 렌더링, 실제 공급원 연결, 실기기, 배터리 측정, 예보, 행동 추론, 상황 스냅샷, 팔레트, OS 절전 연동, 공통 GitHub Actions 적용.

## 총괄 CI

공통 `bootstrap.yml`은 수정하지 않는다. 총괄이 [CI_PROPOSAL.md](CI_PROPOSAL.md)의 워크플로를 별도로 추가한다. 검증 도구는 `modules/intelligence/tools/check_junit_xml.py`다. 기대 수량은 intelligence `TEST-*.xml` 9개·시험 72개, domain 7개·시험 81개다. 수량을 낮추지 않는다.

## 하지 않는 일

도메인 소스를 바꾸지 않는다. 상황 스냅샷 초안을 채우지 않는다. 예보를 계산하지 않는다. 민감한 행동을 추정하지 않는다. 시스템 시계와 네트워크와 Android를 쓰지 않는다. 실기기 측정값으로 임계값을 확정하지 않는다. 순서 필드나 Wear·WFF 연결로 재정렬을 대신 막지 않는다.
