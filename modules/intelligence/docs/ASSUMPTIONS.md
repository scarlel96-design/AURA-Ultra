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
| GB02-A7 | 신선한 충전 참은 퍼센트가 낮아도 축은 `CHARGING`이다. 그 축만으로 Eco로 내리지 않는다. 확정된 `CHARGING`은 충전 신호가 빠지거나 사용할 수 없으면 신선한 배터리 퍼센트가 있어도 유지한다. 이탈은 신선한 충전 거짓뿐이며, 그때 퍼센트가 없으면 `NORMAL`이고 그 전환은 숫자 0이 아니다. 신선한 거짓과 신선한 퍼센트는 저전력 히스테리시스를 쓴다. 직전 축이 `CHARGING`이면 직전 `LOW`가 아니다. 신선한 낮은 퍼센트의 장식 제한은 A28이다. | `desiredPower` | 충전 중에도 Eco로 내리는 결정 |
| GB02-A8 | 저전력은 `<= powerEnter`에서 들어가고 `>= powerExit`에서 나온다. 그 사이는 직전이 `LOW`일 때만 `LOW`다. | `lowPower` | 실측으로 확정된 임계값 |
| GB02-A9 | 날씨·활동의 `UNKNOWN`은 명세에 있는 축 값이다. 강수 또는 경보가 사용할 수 없고 다른 신선한 날씨 입력이 없으면 `UNKNOWN`이다. 활동 토큰이 `REST`/`ACTIVE`/`EXERCISE`가 아니면 `UNKNOWN`이다. 출퇴근·업무·수면 문구로 활동이나 사용자 모드를 추론하지 않는다. | `desiredWeather`, `parseActivity` | 토큰 어휘 승인 |
| GB02-A10 | 강수는 `>= precipEnter`에서 들어가고 `<= precipExit`에서 나온다. 사이 구간은 직전이 `PRECIP`일 때만 유지한다. 직전 `ALERT`는 직전 `PRECIP`가 아니다. | `precipActive` | 실측으로 확정된 확률 스케일과 임계값 |
| GB02-A11 | 경보 진입만 긴급이다. 디바운스와 최소 유지를 건너뛴다. 경보 해제는 긴급이 아니다. 충전 진입과 신선한 충전 해제만 충전 예외다. | `step` | 해제까지 즉시 반영하는 결정 |
| GB02-A12 | 전원·날씨·활동은 확정 시각과 보류 시작 시각을 축마다 가진다. 다른 축이 반복해서 바뀌어도 기다리는 축의 디바운스와 최소 유지를 다시 시작하지 않는다. `committedAt`은 셋 중 하나라도 확정되면 그 샘플 시각이 되는 마지막 센서 확정 시각이다. `PendingSensors.since`는 아직 기다리는 축의 시작 시각 중 가장 이른 값이다. 우회는 축마다 다르다. 경보 진입은 날씨와 그 샘플의 목표 전원을 바로 확정한다. 전원 결합은 긴급 샘플의 현재 목표 전원을 함께 반영하는 기존 시험 계약을 유지한 검토 결과다. 충전 예외는 전원만 바로 확정한다. 활동은 긴급이나 충전 예외로 디바운스와 최소 유지를 건너뛰지 않는다. 날씨는 충전 예외로 건너뛰지 않는다. 샘플이 생략한 보류 목표는 직전 커밋을 유지한다. | `powerCommittedAt`, `keptSince` | 세 축을 다시 하나의 타이머로 묶는 결정 |
| GB02-A13 | 문서 후보는 최소 유지 60초다. 디바운스 시간은 문서에 없으므로 후보 기본값은 0이다. 둘 다 호출자가 바꿀 수 있다. 음수 시간은 정책을 거절한다. | `PolicyCandidates.documented` | 디바운스 제품 값 |
| GB02-A14 | 밝기·연결·사용자 모드는 대기 없이 반영하고 센서 유지 시각을 재설정하지 않는다. 빠지거나 사용할 수 없으면 직전 값을 유지한다. 첫 스텝 기본은 `DAY`/`ONLINE`/`DEFAULT`다. | `step` | 이 축의 미상 토큰 |
| GB02-A15 | 포커스 우선순위는 `CRITICAL > POWER > EXERCISE > WEATHER > CONTEXT > DECORATIVE`다. `ALERT`만 critical이다. 확정된 `LOW` 또는 신선한 낮은 배터리가 power다. 경보가 있으면 포커스는 `CRITICAL`이고 이유에 `POWER_LOW`를 남긴다. `EXERCISE`가 weather보다 앞이다. 기본이 아닌 사용자 모드, `OFFLINE`, `NIGHT`, `ACTIVE`는 context다. | `focusOf` | 포커스 어휘 승인 |
| GB02-A16 | 품질 후보 이름은 성능 문서의 Balanced, Eco, AOD를 따른다. 항상 표시가 AOD, 그다음 확정된 전원 축 `LOW`만 Eco, 그 외는 Balanced다. 신선한 낮은 배터리는 축이 `LOW`로 확정되기 전에 Eco를 선택하지 않는다. Ultra는 선택하지 않는다. OS 절전 상태, 이 품질 이름, 그래픽 전력 제한은 서로 다르다. | `intentFor` | 프로필 적용 범위 |
| GB02-A17 | `motionAllowed`는 모션 감소, 항상 표시, 확정된 `LOW`에서 거짓이다. `particleEffectsAllowed`는 그때 거짓이고, 신선한 낮은 배터리로 `graphicsPowerLimited`가 참일 때도 거짓이다. 입자는 꺼지고 모션은 켜진 상태가 있다. 저전력이어도 `weatherNumbersKept`와 `timeKept`는 참이다. 이 플래그는 정책을 숨기지 말라는 뜻이다. 이번 샘플의 공개 숫자가 null이면 신선한 숫자가 없다는 뜻이지, 화면의 기존 숫자를 0이나 빈 값으로 지우라는 명령이 아니다. | `IntelligenceIntent` | 표시 계층의 캐시 규칙 |
| GB02-A18 | 관측 순서와 설정 순서는 다르다. `committedAt`은 센서 축을 마지막으로 확정한 시각이다. `processedAt`은 마지막으로 받아들인 입력 시각이다. 관측 역전은 `referenceTime < processedAt`이다. 역전은 센서 축과 두 시각과 보류를 유지하고 숫자를 공개하지 않는다. 모션 감소와 항상 표시는 호출자 설정이다. `referenceTime >= processedAt`인 샘플은 호출 순서대로 그 설정을 교체한다. 같은 시각의 나중 호출도 교체한다. 더 이른 샘플은 저장된 보호를 해제하지 못하고, 아직 없던 보호만 올릴 수 있다. 받아들인 스텝에서는 `committedAt <= processedAt`이다. | `CallerSettings` | 같은 시각의 설정 교체를 금지하는 결정 |
| GB02-A19 | 첫 revision은 1이다. 0으로 만들지 않는다. 축, 포커스, 또는 공개 내용이 바뀔 때만 증가한다. 같은 공개 내용의 반복 샘플은 증가하지 않는다. 의도 revision과 상태 revision은 같다. 이전 revision이 `Long.MAX_VALUE`이면 숫자를 감싸지 않는다. 전해야 할 보호가 없으면 `StepResult.LimitReached(REVISION_EXHAUSTED)`이며 이전 상태 객체를 그대로 돌려주고 `deliveredIntent()`는 null이다. 전해야 할 보호는 모션 감소나 항상 표시가 새로 켜지는 것, 그래픽 전력 제한이 새로 켜지는 것, 사용할 수 없게 된 채널의 기존 공개 숫자를 거두는 것이다. 그때는 같은 revision의 `Advanced`이고 `deliveredIntent()`가 그 의도를 돌려준다. 소비자는 revision이 늘지 않아도 null이 아닌 `deliveredIntent()`를 적용한다. 상한에서는 센서 축과 새 신선한 숫자를 반영하지 않는다. 생략된 채널의 이전 숫자는 유지한다. 축 변경, 새 숫자 교체, 숫자 거두기가 버려지면 이유에 `REVISION_EXHAUSTED`를 더한다. 보호만 켜지고 버린 변경이 없으면 그 이유를 더하지 않는다. 이미 켜진 보호와 이미 켜진 그래픽 전력 제한은 상한에서 끄지 않는다. 상한의 역전은 숫자를 거두지 않는다. | `finish`, `deliveredIntent` | 상한에서 새 revision을 만들거나 보호를 버리는 결정 |
| GB02-A20 | `dataQuality` 집계 규칙은 명세가 미확정이라고 적는다. 이 모듈 후보는 입력이 없으면 `SETTINGS_ONLY`, 들어온 채널이 모두 신선하면 `FRESH`, 아니면 `DEGRADED`다. 생략된 채널은 저하로 세지 않는다. | `gateSample` | 품질 집계 승인 |
| GB02-A21 | 이유 코드 이름은 이 모듈의 후보다. 도메인 초안은 불투명 문자열로만 받는다. 제품 어휘로 중앙 문서에 확정하지 않는다. | `ReasonCode` | 표현 어휘 승인 |
| GB02-A22 | `PresentationIntentDraft.paletteId`는 채우지 않는다. 상황 스냅샷 초안은 만들지 않는다. 도메인 축 문자열을 여기서 얼리지 않기 위해서다. | `toPresentationDraft` | 스냅샷 매핑 WO |
| GB02-A23 | 의존성은 도메인 모듈과 Kotlin 2.4.21 테스트 아티팩트뿐이다. | `build.gradle.kts` | 추가 라이브러리 승인 |
| GB02-A24 | 실기기, 실제 공급원, 그래픽, OS 절전, 배터리 측정은 실행하지 않았다. | 시험 범위 | 기기 연결. B-002 |
| GB02-A25 | 유한한 전원 임계값은 퍼센트 스케일 안이어야 하고, 유한한 강수 임계값은 확률 스케일 안이어야 한다. 비교는 양 끝 포함이다. 스케일 끝점은 허용한다. 유한하지 않은 임계값은 기존의 유한성 메시지만 낸다. 문서 후보 15/20, 70/50은 0 이상 100 이하에서 유효하다. | `PolicyCandidates.issues` | 스케일 밖 임계값을 제품 상수로 승인하는 결정 |
| GB02-A26 | `Instant.plus(Duration)`이 `DateTimeException` 또는 `ArithmeticException`을 던지면 그 유지·디바운스 기한은 경과하지 않은 것이다. 예외는 `step` 밖으로 나가지 않는다. `Duration.ofSeconds(Long.MAX_VALUE)`는 음수가 아니므로 정책으로 받는다. 표현할 수 없는 기한은 확정을 만들지 않는다. 긴급 진입과 충전 예외는 그 기한 없이 확정할 수 있다. | `plusOrNull` | 오버플로를 즉시 확정으로 보는 결정 |
| GB02-A27 | 공통 `.github/workflows`는 이 모듈 시험을 실행하지 않는다. 독립 CI에 넣을 명령, main push 조건, 시험 미발견 차단, JUnit 수량 검사는 [CI_PROPOSAL.md](CI_PROPOSAL.md)에만 둔다. 그 파일은 실행되지 않는다. | 제안 | 총괄의 CI 통합 |
| GB02-A28 | 충전 신호가 없거나 사용할 수 없어도 전원 축은 `CHARGING`으로 남는다. `LOW`가 아닌 새 축 값은 만들지 않는다. 회차 03은 이 유지를 이유로 장식 제한까지 기각했다. 회차 04는 `DATA_INTELLIGENCE.md`의 낮은 배터리 입자 제거를 우선한다. 신선한 낮은 배터리는 축을 바꾸지 않은 채 포커스를 `POWER`로 하고 입자를 끈다. 품질은 `BALANCED`로 남고 모션은 축이 `LOW`로 확정되기 전까지 허용한다. 이유에는 `POWER_LOW`와, 축이 `CHARGING`이면 `POWER_CHARGING`이 함께 있다. 상한 아래의 그래픽 전력 제한은 이번 샘플의 신선한 낮은 배터리이거나 확정 축 `LOW`일 때만 켜진다. 배터리 생략은 보류 중인 저전력 희망을 취소하고 확정 축은 유지한다. 생략이 이전 그래픽 제한을 다음 스텝에 붙잡아 두지 않는다. 상한에서 이미 켜진 그래픽 제한은 끄지 않는다. | `graphicsPowerLimited` | 신선한 낮은 배터리의 장식 제한을 다시 거두거나, 생략된 배터리에 이전 그래픽 제한을 붙잡는 결정 |
| GB02-A29 | `deliveredIntent()`는 한 결과 안에서 적용할 의도만 고른다. 결과가 호출 밖에서 재정렬되면 이전 의도가 최신 보호를 덮어쓸 수 있다. 지원되는 소비자는 호출 순서대로 결과를 받고, null이 아닌 `deliveredIntent()`를 revision이 같아도 적용한다. `Advanced.state.processedAt`이 마지막으로 적용한 시각보다 이르면 그 결과는 버린다. 같은 시각은 호출 순서를 유지한다. 의도 객체에는 `processedAt`이 없다. 순서 필드와 Wear Services·WFF 연결은 넣지 않는다. 이 규칙 없이 재정렬하는 통합은 차단점 GB02-R05-ASYNC다. | `deliveredIntent` | 재정렬을 기계가 거부하도록 순서 필드를 추가하는 결정 |
| GB02-A30 | 공개 `reasonCodes`는 수정할 수 없는 복사본이다. 호출자가 그 목록을 고치면 상태의 `emission`까지 바뀌므로 허용하지 않는다. | `intentFor` | 이유 목록을 호출자가 수정하게 두는 결정 |

도메인 가정 A17의 "FSM은 없다"는 도메인 모듈 안의 문장이다. 이 모듈이 상태 머신을 가진다고 그 문장을 고치지 않는다.
