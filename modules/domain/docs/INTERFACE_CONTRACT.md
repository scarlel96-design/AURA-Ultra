# GB-01 인터페이스 계약

상태: 구현된 순수 Kotlin 계약과 후속 초안. 제품 출시 계약이 아니다. 정본 이름은 [DATA_INTELLIGENCE.md](../../../docs/DATA_INTELLIGENCE.md)의 의사코드를 유지한다. 가정은 [ASSUMPTIONS.md](ASSUMPTIONS.md)에 있다.

## Observation<T>

| 필드 | 의미 |
|---|---|
| `value` | 측정·예측·추정·시스템 값. 없으면 null. 실제 0과 다르다. |
| `unit` | 호출자가 준 단위 토큰. 값이 있을 때 공백 문자와 ISO 제어 문자가 없는 문자열이 필요하다. 내부 공백도 거절한다. 값이 null이면 이 문자 검사는 하지 않는다. |
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
| `Reading(value, VALID 또는 STALE)` | 지원하는 스칼라 값이 있고, 부동소수면 유한하며, 상태가 VALID 또는 STALE |
| `Unavailable` | 상태 UNAVAILABLE, 값 null |
| `Denied` | 상태 DENIED, 값 null |
| `Failed` | 상태 ERROR, 값 null |
| `Inconsistent` | 그 밖의 조합, 유한하지 않은 부동소수, 또는 지원하지 않는 페이로드 |

지원하는 값은 null, `Boolean`, `Byte`, `Short`, `Int`, `Long`, `Float`, `Double`, `Char`, `String`이다. 컬렉션, 배열, 읽기 전용 컬렉션 인터페이스, 사용자 정의 객체는 지원하지 않는다.

`Observation`과 `StatusDerivation.Rejected`는 검증 전 입력이다. 생성자는 값을 복사하거나 고치지 않는다. `RevisionCursor`, `ClassifiedValue.Reading`, `StatusDerivation.Unchanged`, `StatusDerivation.DegradedToStale`는 승인 상태다. 값이 지원 스칼라가 아니면 생성과 `copy`가 `UnsupportedPayloadException`을 던진다. `validateObservation`은 그 입력을 `UNSUPPORTED_PAYLOAD`로 거절하고, `applyRevision`은 기존 커서를 유지한다. `classifiedValue()`는 `Inconsistent`를 반환한다. `deriveStatus`는 `Rejected`로 입력 객체를 그대로 돌려준다.

유한하지 않은 `Float`와 `Double`은 스칼라다. `validateObservation`은 `NON_FINITE`로 거절하고 `classifiedValue()`는 `Inconsistent`다. `applyRevision`은 그 값을 저장하지 않는다.

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

## 권한 검증

`AuthorityCoordinator`는 관측 revision과 분리된 순수 계약이다. `applyRevision`, `classifiedValue`, `deriveStatus`는 이 상태를 읽지 않는다. 관측 상태 `VALID`, `DENIED`, `ERROR`, `UNAVAILABLE`은 권한을 허가하거나 철회하지 않는다.

scope는 `authority`, `principal`, `category` 불투명 토큰이다. `SourceId`만으로 scope를 만들지 않는다. session과 ticket은 발급한 coordinator 인스턴스에 묶인다. 같은 문자와 같은 번호라도 다른 인스턴스의 ticket은 거절한다. `CheckTicket`과 `AcquisitionCapability`는 data class가 아니고, 호출자가 만든 복제 seal은 허가로 받지 않는다. 공개 `verified = true` 경로는 없다.

신뢰된 확인 결과는 `TrustedCheckResult.GRANTED`, `DENIED`, `FAILED`다. 미발급, 오래된, 다른 인스턴스 ticket은 상태를 바꾸지 않는다. 같은 완료의 반복은 그대로 두고, 같은 ticket의 모순된 반복은 `UNKNOWN`으로 닫는다. 신뢰된 무효화는 이미 `UNKNOWN`이어도 generation을 돌리고 미완료 확인을 취소한다. 검증되지 않은 입력은 어떤 scope도 바꾸지 않는다. 상태가 같고 무효화가 없으면 generation을 유지한다. ticket과 generation이 `Long.MAX_VALUE`를 넘기려 하면 그 scope를 잠그고, 새 coordinator와 새 확인으로만 다시 연다.

획득 capability는 scope, session, generation, 요청 stream에 묶인다. 다른 stream으로 다시 붙이지 않는다. 이전 generation은 재허가 뒤에도 통과하지 않는다. 재허가 이전의 과거 측정값 공개는 이 함수에 없다.

이 타입은 SDK 권한, 동시성, 저장, 소비자 화면 삭제를 증명하지 않는다. 같은 프로세스의 리플렉션을 막지 않는다. `openNearCeiling`은 모듈 내부에서 카운터만 옮기며 `GRANTED`를 만들지 않는다.

## 이 계약에 없는 것

FSM, 히스테리시스, 우선순위, 캐시 저장소, 백오프, Complication 변환, 단위 환산, 실제 기상·건강 요청, 그래픽. 해당 항목은 GPT-07과 WO-17~23의 남은 범위다.
