# GB-02 인터페이스 계약

상태: 순수 Kotlin 상태 머신. 제품 출시 계약이 아니다. 도메인 타입은 [modules/domain/docs/INTERFACE_CONTRACT.md](../../domain/docs/INTERFACE_CONTRACT.md)를 그대로 사용한다. 가정은 [ASSUMPTIONS.md](ASSUMPTIONS.md)에 있다. 정본 축과 우선순위는 [DATA_INTELLIGENCE.md](../../../docs/DATA_INTELLIGENCE.md)를 따른다.

## 입력

`step(previous, sample, policy, lastDeliverySequence = 0, lastDeliveryEpoch = 0, openDeliverySession = false)`만 전이를 만든다. 네 번째 인자를 생략하면 결과의 `deliverySequence`는 1이고 `deliveryEpoch`는 0이다. 그 값만으로는 순서가 아니다. 순서를 쓰려면 호출자가 직전 결과의 순서와 epoch를 다시 넣는다. `openDeliverySession`이 참일 때만 epoch가 1 증가하고 순서는 1에서 다시 시작한다. epoch가 `Long.MAX_VALUE`이면 더 열지 않고 감싸지 않는다.

`previous`가 null이면 첫 스텝이다. `sample.referenceTime`은 호출자가 넣는다. 관측 필드는 도메인 `Observation`이거나 null이다. null은 생략이다. 생략은 실패한 관측이 아니다. 상한 아래에서 배터리나 강수를 생략하면 그 공개 숫자는 null이다. null은 0이 아니다.

`PolicyCandidates.documented()`는 문서 후보 15/20, 70/50, 유지 60초, 디바운스 0, 단위 토큰 `percent`/`percent`/`token`/`flag`, 스케일 0 이상 100 이하를 반환한다. `issues()`가 비어 있지 않으면 `StepResult.PolicyRejected`다. `deliveredIntent()`는 null이다. 잘못된 정책을 정상 `Advanced`로 만들지 않고 `issues`를 그대로 둔다. `state`는 이전 상태에 이번 샘플의 모션 감소와 항상 표시만 올린다. 처리 시각과 revision은 바꾸지 않는다. 새 관측 숫자는 받지 않는다. 시계가 역전되지 않았고 보관 TTL이 지났거나 샘플이 `DENIED`/`ERROR`/`UNAVAILABLE`이면 그 공개 숫자를 null로 거두고 철회 커서를 남긴다. 시계 역전은 TTL과 철회를 적용하지 않는다. 첫 입력이면 revision 0이다. `failSafe`는 그 상태의 별도 의도로 데이터 품질 `DEGRADED`, 이유 `POLICY_REJECTED`다. 신뢰할 수 없는 배터리로 새 그래픽 제한을 켜지 않는다. 이미 켜진 제한과 올라간 설정은 유지한다. 다음 스텝에 그 유지를 남기려면 호출자가 `state`를 넘긴다.

`issues()`는 유한하지 않은 임계값, 뒤집힌 구간, 음수 시간, 사용할 수 없는 스케일, 빈 단위를 거절한다. 유한한 전원 임계값이 퍼센트 스케일 밖이거나, 유한한 강수 임계값이 확률 스케일 밖이면 거절한다. 비교는 양 끝 포함이다. 문서 후보 15/20과 70/50은 그 스케일에서 유효하다.

## 게이트

각 채널은 `Absent`, `Unusable`, `Fresh` 중 하나다.

`Fresh`가 되려면 `deriveStatus`가 거절·만료 강등이 아니고, 신선도가 `FRESH`이며, 분류가 상태 `VALID`인 읽기이고, 기대 단위 검사가 통과해야 한다. 숫자는 정책 스케일 안이어야 한다. 토큰은 아래 표의 정확한 문자열이어야 한다.

사용할 수 없는 이유는 `STALE`, `UNDECLARED`, `UNAVAILABLE`, `DENIED`, `ERROR`, `REJECTED`, `UNIT_UNCHECKED`, `OUTSIDE_CANDIDATE_SCALE`, `TOKEN_UNCHECKED`, `FUTURE_OBSERVATION`으로 공개 이유에 연결한다. 그 값은 공개하지 않는다. `DENIED`/`ERROR`/`UNAVAILABLE`은 null TTL이면 `UNDECLARED_IGNORED`를, 만료 TTL이면 `STALE_IGNORED`를 같은 결과에 함께 남긴다. 유효 TTL은 그 상태 사유만 남긴다. 공백·NUL·제어문자 단위와 유한하지 않거나 뒤집힌 `gateDouble` 경계는 값을 공개하지 않는다. `FORECAST`가 아닌 관측의 `observedAt`이 `referenceTime`보다 늦으면 `FUTURE_OBSERVATION`이다. 같은 시각은 허용한다. 허용 오차 상수는 두지 않는다. 이전 공개 숫자가 있으면 그 숫자를 유지하고, 미래 값은 공개하지 않는다. `FORECAST`는 이 검사에서 빼며 관측 커서를 만들거나 바꾸지 않는다. 배터리 예보는 숫자를 공개하지 않고 전원 축과 그래픽 제한을 바꾸지 않는다. 강수 예보는 커서가 없을 때만 숫자를 공개할 수 있고 날씨 축은 바꾸지 않는다. 충전·경보·활동·조도·연결·사용자 모드의 예보와, 그 축 커서보다 이른 관측은 축을 바꾸지 않는다. `DENIED`/`ERROR`/`UNAVAILABLE`은 그 스트림의 철회 커서를 남겨, 그 시각보다 이른 관측이 숫자를 다시 공개하지 못하게 한다. 같은 시각은 호출 순서를 유지한다. 더 높은 호출자 revision은 이른 `observedAt`도 받는다.

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

배터리와 강수의 관측 순서는 `observedAt`, 호출자가 준 revision, 처리 시각, 표시 revision과 따로 둔다. revision을 만들지 않는다. 같은 출처에서 revision이 낮거나, revision이 같고 값이 다르면 첫 숫자를 유지한다. 같은 revision의 같은 값은 중복이다. 더 높은 revision은 `observedAt`이 일러도 받는다. revision이 없으면 `observedAt`이 커서보다 이를 때만 거절한다. 같은 `observedAt`은 기존과 같이 호출 순서의 마지막 값이다. 다른 출처의 더 늦은 `observedAt`은 받을 수 있다. 거절한 과거 값은 이전 숫자와 그래픽 제한을 유지한다. `DENIED`/`ERROR`/`UNAVAILABLE`의 철회 커서는 과거로 내리지 않는다. `observedAt`이 없거나 `referenceTime`보다 뒤면 철회 시각은 `referenceTime`이다. 그 커서가 그대로면 이전 숫자·그래픽·축을 유지하고 이유는 `SUPERSEDED_OBSERVATION`이다. 더 새 철회는 숫자를 null로 거두고 그 시각보다 이른 샘플은 다시 공개하지 않는다. null은 0이 아니다. 다른 출처의 더 이른 철회도 커서를 움직이지 않는다. 더 높은 호출자 revision은 철회 뒤의 이른 `observedAt`도 받는다. 그 우선순위와 철회 경계의 충돌은 D01이며 도메인 계약은 바꾸지 않는다.

모션 감소와 항상 표시는 `CallerSettings`다. 보호 워터마크 `protectionWatermark`는 `processedAt`과 따로 둔다. 기본은 `Instant.EPOCH`다. `referenceTime`이 워터마크보다 이르면 저장된 보호를 해제하지 못하고 없던 보호만 올리며 워터마크는 유지한다. 같거나 늦으면 설정을 호출 순서대로 교체하고 워터마크를 그 `referenceTime`으로 둔다. 잘못된 정책이 보호를 올리면 `processedAt`은 그대로 두고, 그 `referenceTime`이 워터마크보다 이르지 않으면 워터마크만 그 시각이 된다. 그래서 그 시각보다 이른 정상 해제는 최신 보호를 끄지 못한다. 같거나 늦은 정상 해제는 허용한다.

`revision`은 1에서 시작한다. 축, 포커스, 공개 내용이 바뀔 때만 1 증가한다. 이전 값이 `Long.MAX_VALUE`이면 숫자를 감싸지 않는다. 그 상한에서 전해야 할 보호가 없으면 `StepResult.LimitReached`다. `reason`은 `REVISION_EXHAUSTED`이고 `deliveredIntent()`는 null이다. 공개 내용이 그대로이고 시계가 역전되지 않았으며 `referenceTime`이 `processedAt`보다 늦으면 `state`는 같은 revision·숫자·축·보호를 유지한 채 `processedAt`만 그 시각인 복사본이다. 같거나 이른 시각이거나 시계가 역전이면 `state`는 호출자가 넘긴 이전 상태 객체다. 전해야 할 보호가 있으면 같은 revision의 `Advanced`다. 그 보호는 모션 감소나 항상 표시가 새로 켜지는 것, 그래픽 전력 제한이 새로 켜지는 것, 사용할 수 없게 된 채널의 기존 공개 숫자를 거두는 것이다.

소비자는 `StepResult.deliveredIntent()`가 null이 아니면 그 의도를 적용한다. revision이 이전과 같아도 적용한다. `LimitReached`와 `PolicyRejected`는 적용할 의도가 없다. revision이 증가할 때만 초안을 읽는 소비자는 상한의 보호를 놓친다. 그 누락은 시험 전용 소비자 둘을 같은 입력에 넣어 확인한다. Wear Services와 WFF 연결 코드는 없다.

상한의 `Advanced`는 센서 축을 바꾸지 않는다. `resync`가 아니면 새 신선한 숫자로 이전 공개 숫자를 바꾸지 않는다. 생략된 채널은 보관된 `expiresAt`보다 이르면 이전 숫자를 유지한다. `referenceTime`이 그 시각과 같거나 늦고 `resync`가 아니면 그 숫자를 null로 거둔다. `resync`가 참이어도 검증을 통과해 새로 받은 관측만 반영한다. 예보, 철회, 미래 시각, 더 이른 관측, 같은 revision 충돌은 받지 않고 보관 TTL을 늘리지 않는다. 시계 역전은 이 거두기와 재동기화를 하지 않는다. 미래 관측은 상한에서도 이전 숫자를 지우지 않는다. 그 밖의 `Unusable`이고 이전 숫자가 있으면 그 숫자만 null로 거두고 데이터 품질은 `DEGRADED`다. null은 0이 아니다. 축 변경, 새 신선한 숫자 교체, 숫자 거두기가 버려지면 이유에 `REVISION_EXHAUSTED`를 더한다. 모션 감소나 항상 표시만 켜지고 버린 변경이 없으면 그 이유를 더하지 않는다. 이미 켜진 보호와 이미 켜진 그래픽 전력 제한은 상한에서 끄지 않는다. 상한의 역전은 보호가 늘지 않고 숫자를 거둘 근거가 없으면 이전 상태 객체의 `LimitReached`다. 공개 내용이 그대로이고 `referenceTime`만 더 늦으면 `LimitReached`가 `processedAt`을 그 시각으로 기록한다. 그 기록 뒤의 더 이른 `resync`는 시계 역전이라 숫자와 보호를 바꾸지 못한다. 더 늦은 검증된 `resync`는 숫자를 받는다. 이미 켜진 그래픽 제한은 더 높은 배터리를 받아도 상한에서 끄지 않는다.

표시 revision과 `deliverySequence`는 다르다. 같은 epoch에서 순서는 `lastDeliverySequence + 1`이고 `Long.MAX_VALUE`에서 멈추며 감싸지 않는다. 음수 순서는 1로 바꾸되 epoch를 열지 않는다. 그 1은 이미 더 큰 순서를 적용한 소비자를 지나지 못한다. 후보 소비자는 같은 epoch에서 마지막으로 적용한 순서보다 큰 값만 전체를 적용한다. 순서와 epoch가 모두 상한이면 보호를 강화하는 요청만 적용하고 해제는 적용하지 않는다. 더 이전 epoch는 버린다. `openDeliverySession`으로 연 더 큰 epoch만 새 워터마크이며, 그때는 해제도 적용한다. 세션을 열지 않은 더 큰 epoch는 적용하지 않는다. 양쪽 순서를 0으로 되돌리는 것만으로는 재시작이 아니다. 이 필드를 무시하는 소비자는 회차 05의 호출 순서 계약을 유지한다. 합의 전 후보는 [PROTECTION_DELIVERY_CONTRACT.md](PROTECTION_DELIVERY_CONTRACT.md)다.

유지·디바운스 기한은 그 축의 확정 시각 또는 그 축의 보류 시작 시각에 정책을 더한 값이다. 그 덧셈이 시각 범위를 벗어나면 기한은 경과하지 않은 것으로 보고, 예외는 `step` 밖으로 나가지 않는다. `Duration.ofSeconds(Long.MAX_VALUE)`는 음수가 아니므로 받을 수 있다. 경보 진입은 날씨와 그 샘플의 목표 전원을 그 기한 없이 확정한다. 충전 예외는 전원만 그 기한 없이 확정한다. 활동은 그 예외들로 기한을 건너뛰지 않는다. 날씨는 충전 예외로 기한을 건너뛰지 않는다.

확정된 `CHARGING`은 충전 관측이 빠지거나 `Fresh`가 아니면 유지한다. 신선한 충전 거짓만 이탈을 만든다. 그 상태에서 신선한 낮은 배터리가 있어도 축은 `CHARGING`이고 품질은 Eco로 내려가지 않는다. 전원 축에 값을 추가하지 않는다. 신선한 낮은 배터리는 그 축과 별도로 장식과 입자를 제한한다.

## 포커스와 표현

`focusOf` 순서: `ALERT` → `CRITICAL`, 확정된 `LOW` 또는 신선한 낮은 배터리 → `POWER`, `EXERCISE` → `EXERCISE`, `PRECIP` → `WEATHER`, 비기본 사용자 모드 또는 `OFFLINE` 또는 `NIGHT` 또는 `ACTIVE` → `CONTEXT`, 그 외 `DECORATIVE`.

그래픽 전력 제한은 배터리 채널이 `Fresh`이고 값이 `powerEnter` 이하일 때 바로 켜진다. 디바운스와 최소 유지를 기다리지 않는다. `powerExit` 이상이면 끈다. 그 사이이고 이전 그래픽 제한이 켜져 있으면 전원 축이 `LOW`가 아니어도 유지한다. 충전과 저전력 확정 대기도 같다. 후보 15/20을 그대로 쓰며 새 제품 임계값으로 승격하지 않는다. 포커스가 `CRITICAL`이면 이유는 `WEATHER_ALERT`와 `POWER_LOW`다. 품질은 확정된 `LOW`일 때만 `ECO`다. 모션은 확정된 `LOW`, 모션 감소, 항상 표시에서만 꺼진다. 입자는 그때 꺼지고, 그래픽 전력 제한이 켜져도 꺼진다. `graphicsPowerLimited`는 그 제한이거나 확정된 `LOW`다. 상한 아래에서 배터리 생략과 사용할 수 없는 배터리는 이번 샘플의 그래픽 제한을 켜지 않고, 이전 제한을 붙잡아 두지 않는다. 상한에서 이미 켜진 제한은 끄지 않는다.

`IntelligenceIntent.toPresentationDraft()`는 도메인 `PresentationIntentDraft`에 포커스 이름, 품질 이름, `motionAllowed`, 이유 이름, revision을 넣는다. `paletteId`는 null이다. 도메인 초안은 `reasonCodes`를 생략할 수 있는 목록으로 선언한다. 이 모듈은 이유 이름을 항상 넣는다. 도메인 초안에는 입자 필드가 없으므로 그래픽 제한의 초안 표시는 포커스 이름 `POWER`와 이유 `POWER_LOW`다. `particleEffectsAllowed`는 `IntelligenceIntent`에 남긴다. revision은 1부터 시작하고 null을 0으로 바꾸지 않는다. 상한에서 소비자가 적용할 초안은 `deliveredIntent().toPresentationDraft()`다.

품질 이름 후보는 `BALANCED`, `ECO`, `AOD`다. `timeKept`와 `weatherNumbersKept`는 참을 유지한다. `reasonCodes`는 수정할 수 없는 복사본이다.

## 초기 상태

`previous`가 null이면 첫 스텝이다. revision은 1이고 보류는 없다. `committedAt`, 축별 확정 시각, `processedAt`은 그 샘플의 `referenceTime`이다. 축은 그 샘플의 목표값이고, 설정은 그 샘플의 모션 감소와 항상 표시다.

## 소비자 순서

`deliveredIntent()`는 한 결과 안의 의도를 고른다. 결과가 호출 밖에서 재정렬되면 이전 의도가 최신 보호를 덮어쓸 수 있다. 회차 05 소비자는 `step` 결과를 호출 순서대로 받고, null이 아닌 `deliveredIntent()`를 revision이 같아도 적용한다. `Advanced.state.processedAt`이 마지막으로 적용한 시각보다 이르면 그 결과는 버린다. 같은 시각은 호출 순서를 유지한다. 의도 객체에는 `processedAt`이 없다. 이 규칙만 쓰는 통합은 차단점 GB02-R05-ASYNC로 남는다. 회차 07의 `deliverySequence`는 후보이다. 필드를 무시하면 회차 05 계약이 그대로다.

## 실제 공급원

호출자가 `referenceTime`을 넣는다. 기계는 시스템 시계를 읽지 않는다. 관측은 도메인 `Observation`으로 들어오고, null은 생략이며 실패한 관측이 아니다. 공개 숫자 null을 0으로 그리지 않는다. `particleEffectsAllowed`는 도메인 초안에 없으므로 초안만 보는 렌더러는 입자 제한을 놓친다. 포커스 이름 `POWER`와 이유 `POWER_LOW`를 함께 본다. 제품 임계값과 플랫폼 지원 범위는 이 계약이 확정하지 않는다.

## 구현하지 않은 기능

Wear Services, WFF 렌더링, 실제 공급원 연결, 실기기, 배터리 측정, 예보 계산, 행동 추론, 상황 스냅샷, 팔레트, OS 절전 연동, 공통 GitHub Actions 적용. 도메인 `Observation`에는 revision이 없다. 스트림 revision은 이 모듈의 선택 필드이며 도메인 `applyRevision`을 호출하지 않는다. 출처가 바뀌면 도메인은 `KEY_MISMATCH`다. 그 변경 제안은 D01이다.

## 총괄 CI

공통 `bootstrap.yml`은 수정하지 않는다. 총괄이 [CI_PROPOSAL.md](CI_PROPOSAL.md)의 워크플로를 별도로 추가한다. 검증 도구는 `modules/intelligence/tools/check_junit_xml.py`다. 기대 수량은 intelligence `TEST-*.xml` 13개·시험 108개, domain 7개·시험 81개다. 108은 회차 08의 99개에 `Round08CloseoutTest` 9개를 더한 수량이다. 99는 회차 07의 93개에 `Round08Test` 6개를 더한 수량이다. 93은 회차 06의 82개에 `Round07Test` 11개를 더한 수량이다. 수량을 낮추지 않는다. 검사기는 직접 자식 `testcase`, suite와 같은 classname, 비어 있지 않은 메서드, `TEST-{suite}.xml` 파일명, 네 카운터의 존재, `--not-before`/`--not-after` 창을 본다. 공통 JUnit 워크플로는 수정하지 않는다.

## 하지 않는 일

도메인 소스를 바꾸지 않는다. 상황 스냅샷 초안을 채우지 않는다. 예보를 계산하지 않는다. 민감한 행동을 추정하지 않는다. 시스템 시계와 네트워크와 Android를 쓰지 않는다. 실기기 측정값으로 임계값을 확정하지 않는다. Wear·WFF 연결로 재정렬을 대신 막지 않는다. `deliverySequence`는 총괄 합의 전의 후보이고, 회차 05 호출 순서 소비자를 제거하지 않는다.

## 보호 수신 경계

`ProtectedBoundary`는 `step` 밖에 있는 순수 후보다. 기계 상태, `deliveredIntent`, 전달 epoch, AOD, 그래픽 제한, 정책 임계값을 바꾸지 않는다. 설정된 합성 scope와 stream만 받는다. 수신은 `AuthorityCoordinator.permits`가 기대 scope와 기대 요청을 모두 통과할 때만 capability와 그 관측 인스턴스를 한 슬롯에 묶는다. 최종 `read`와 `commit`이 같은 검사를 다시 한다. 공개 타입을 직접 구현한 기록, 다른 scope로의 재부착, 이전 generation의 지연 결과는 공개하지 않는다.

스트림 `ERROR`와 `UNAVAILABLE`은 그 슬롯만 지우고 순서 울타리를 올린다. 권한 generation은 바꾸지 않는다. 권한 무효화는 coordinator generation을 돌리고 그 scope의 슬롯을 비운다. 재허가 뒤에도 이전 기록은 공개되지 않는다. 재허가 이전 이력 공개 함수는 없다. 누락 값을 0으로 바꾸지 않는다. `FORECAST`와 TTL 만료는 권한 상태가 아니다. 슬롯은 설정한 stream마다 하나다. capability 목록은 쌓지 않는다. 순서가 `Long.MAX_VALUE`를 넘기려 하면 잠그고 감싸지 않는다.

이 경계의 시험은 등록된 Intelligence 108개에 포함되지 않는다. 108개의 식별자와 기대는 유지한다. 공통 검사기 등록 전에 이 수량을 등록된 수량으로 말하지 않는다.

나중 F04·C01·GPT-07이 실제 경로를 연결할 때 비워야 하는 필드는 다음과 같다. 이번 후보는 그 경로를 구현하지 않는다.

| 필드 | 이유 |
|---|---|
| `ObservationMemory`의 보호 스트림 커서와 만료 시각 | 철회 뒤 이전 측정이 남으면 지연 재생이 된다 |
| `Emission.publishedBatteryPercent`, `publishedPrecipitation`, `reasonCodes` | 파생 숫자가 권한과 따로 공개된다 |
| `IntelligenceIntent`의 같은 공개 숫자·이유·revision | `deliveredIntent()`가 null이어도 철회가 전달돼야 한다 |
| `PendingSensors`와 축 확정 시각 | 보류 목표가 철회된 입력을 확정할 수 있다 |
| `MachineState.focus`와 `revision` | 파생 포커스를 권한 증거로 보면 안 된다 |
| `CallerSettings`, AOD, 모션 감소, 그래픽 전력 제한 | 보호 설정은 데이터 철회와 함께 끄지 않는다 |

직렬화한 envelope는 발급 표식을 잃으므로 권한 증거가 아니다. `commit`을 권한 무효화와 겹치지 않게 호출하는 일은 어댑터의 compare-and-commit 의무다. 이 모듈은 그 동시성을 증명하지 않는다.
