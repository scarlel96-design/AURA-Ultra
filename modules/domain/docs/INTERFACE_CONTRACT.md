# GB-01 인터페이스 계약

상태: 구현된 순수 Kotlin 계약과 후속 초안. 제품 출시 계약이 아니다. 정본 이름은 [DATA_INTELLIGENCE.md](../../../docs/DATA_INTELLIGENCE.md)의 의사코드를 유지한다. 가정은 [ASSUMPTIONS.md](ASSUMPTIONS.md)에 있다.

## Observation<T>

| 필드 | 의미 |
|---|---|
| `value` | 측정·예측·추정·시스템 값. 없으면 null. 실제 0과 다르다. |
| `unit` | 호출자가 준 단위 토큰. 값이 있을 때 공백 없는 문자열이 필요하다. |
| `source` | `SourceId`. 불투명 출처. |
| `observedAt` | 출처가 부여한 시각. 예보 유효 시작·종료가 아니다. 없을 수 있다. |
| `receivedAt` | 이 처리 경로가 받은 시각. 필수. |
| `expiresAt` | TTL 시각. 없으면 만료를 선언하지 않은 것이다. |
| `status` | `VALID`, `STALE`, `UNAVAILABLE`, `DENIED`, `ERROR` |
| `kind` | `OBSERVED`, `FORECAST`, `ESTIMATED`, `SYSTEM` |

생성자는 잘못된 조합도 담을 수 있다. 반영 전에 `validateObservation`을 통과해야 한다. 검사 실패 때 입력의 상태와 값을 고치지 않는다.

`classifiedValue()` 결과:

| 결과 | 조건 |
|---|---|
| `Reading(value, VALID 또는 STALE)` | 값이 있고 유한하며 상태가 VALID 또는 STALE |
| `Unavailable` | 상태 UNAVAILABLE, 값 null |
| `Denied` | 상태 DENIED, 값 null |
| `Failed` | 상태 ERROR, 값 null |
| `Inconsistent` | 그 밖의 조합, 또는 유한하지 않은 부동소수 |

## 신선도

`freshnessOf(expiresAt, referenceTime)`와 `deriveStatus(observation, referenceTime)`는 시계를 읽지 않는다.

`EXPIRED_AT_OR_AFTER`: `referenceTime < expiresAt`만 `FRESH`. 같은 시각은 `EXPIRED`. `expiresAt == null`은 `UNDECLARED`.

`deriveStatus`는 구조 검사를 통과한 `VALID`가 만료됐을 때만 상태만 `STALE`인 사본을 만든다. `ERROR`가 만료돼도 `ERROR`로 남고, 신선도 값만 `EXPIRED`로 돌려준다. 신선한 `DENIED`를 `VALID`로 바꾸지 않는다.

## revision

`applyRevision(current, key, revision, incoming, constraints)`:

| 결과 | 조건 | 커서 |
|---|---|---|
| `ACCEPTED` | 커서가 없거나 더 큰 revision이고 검사가 통과 | 새 커서 |
| `DUPLICATE` | revision이 같고 `receivedAt`을 뺀 페이로드가 같음 | 기존 |
| `DUPLICATE_CONFLICT` | revision이 같고 페이로드가 다름 | 기존 |
| `SUPERSEDED_REJECTED` | 더 작은 revision | 기존 |
| `KEY_MISMATCH` | 기존 키와 다름 | 기존 |
| `INVALID_KEY` | subject가 토큰 규칙을 어김 | 기존 또는 null |
| `INVALID_OBSERVATION` | 구조·제약·출처 불일치 | 기존 또는 null |

더 큰 revision의 수신 시각이 이전보다 이르면 수락하고 `receiveTimeInversion`을 true로 둔다.

## 후속 초안

구현 패키지: `io.github.scarlel96.aura.domain.draft`. 동작을 계산하지 않는다.

### WeatherSnapshotDraft

`locationId`, `issuedAt`, `validFrom`, `validTo`, `probability`, `observedRain`, `forecastRain`.

`observedRain.kind`는 `OBSERVED`, `forecastRain.kind`는 `FORECAST`여야 한다. 다르면 `KIND_MISMATCH`이며 kind를 바꾸지 않는다. `probability`의 kind와 스케일은 검사하지 않는다. `validFrom`/`validTo`를 `observedAt`에 복사하지 않는다.

데이터 공급 표의 기온, 습도, 바람, UV, 일출·일몰은 이 초안에 없다. 의사코드의 생략 기호를 임의 필드로 바꾸지 않았다. 후속 계약이 각 값을 `Observation<T>`로 추가한다.

### ContextSnapshotDraft

`weather`, `activity`, `power`, `timeOfDay`, `connectivity`, `userMode`, `dataQuality`.

`weather`만 `WeatherSnapshotDraft`다. 나머지 축은 미확정 문자열이다. null은 축이 없는 상태다. `NORMAL`/`LOW` 같은 FSM 토큰은 열거형으로 넣지 않았다. `dataQuality`를 여러 관측에서 계산하지 않는다.

### PresentationIntentDraft

`focus`, `paletteId`, `quality`, `motionAllowed`, `reasonCodes`, `revision`.

`motionAllowed == null`은 허용이 아니다. `revision == null`은 0이 아니다. 이 타입을 만드는 함수는 없다. 후속 지능 모듈이 `ContextSnapshotDraft`의 관측을 revision 게이트와 `deriveStatus`에 통과시킨 뒤 의도를 만든다. 그 의도의 `revision`도 같은 게이트 규칙을 사용한다.

## 연결 방법

1. Wear/phone 어댑터가 SDK 결과를 `Observation`으로 옮긴다. 이 모듈은 그 SDK를 import하지 않는다.
2. 어댑터는 누락을 null과 `UNAVAILABLE`, 권한 거부를 `DENIED`, 통신 실패를 `ERROR`로 둔다. 실패 숫자를 넣지 않는다.
3. 저장 전 `applyRevision`을 호출한다. 기준 시각은 어댑터의 시계에서 이 함수의 인자로만 들어온다.
4. 표시 전 `deriveStatus`와 `classifiedValue`를 사용한다. WFF 패키지 안에는 이 코드를 넣지 않는다.
5. 루트 `settings.gradle.kts`에 이 모듈을 넣는 변경은 중앙 소유자가 한다. 그 전에 빌드는 [BUILD.md](BUILD.md)의 독립 명령을 사용한다.

## 이 계약에 없는 것

FSM, 히스테리시스, 우선순위, 캐시 저장소, 백오프, Complication 변환, 단위 환산, 실제 기상·건강 요청, 그래픽. 해당 항목은 GPT-07과 WO-17~23의 남은 범위다.
