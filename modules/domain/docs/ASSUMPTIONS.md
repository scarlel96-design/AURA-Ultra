# GB-01 가정과 제약

설계 문서가 정하지 않은 항목은 제품 결정으로 확정하지 않는다. 아래는 이 모듈이 동작하기 위해 코드에 넣은 규칙이다. 후속 승인으로 바꿀 수 있게 이름과 위치를 고정했다.

| ID | 규칙 | 코드 | 바꾸기 전에 필요한 것 |
|---|---|---|---|
| A1 | `SourceId`는 대소문자를 구분하는 불투명 토큰이다. 목록, 별칭, 공백 제거, 유니코드 정규화는 없다. 제어 문자는 거절한다. | `SourceId.parse` | 승인된 출처 목록. B-006 |
| A2 | 패키지 `io.github.scarlel96.aura.domain`은 기존 소유자 접두를 따른 모듈 패키지다. 배포 applicationId가 아니다. | 소스 패키지 | B-007 |
| A3 | 만료 경계는 `EXPIRED_AT_OR_AFTER` 하나다. `referenceTime < expiresAt`이면 신선하고, 같으면 만료다. | `ExpiryBoundary` | 경계 포함 여부의 제품 승인 |
| A4 | `expiresAt == null`은 무기한도 즉시 만료도 아니다. 결과는 `UNDECLARED`다. | `Freshness.UNDECLARED` | 데이터별 TTL. 15~60분 제안은 적용하지 않았다. |
| A5 | 같은 revision은 먼저 수락한 관측을 유지한다. 페이로드 비교에서 `receivedAt`은 빼며, 나머지 필드가 같으면 `DUPLICATE`, 다르면 `DUPLICATE_CONFLICT`다. | `applyRevision` | 동률 시 마지막 수신 우선 정책이 승인될 때 |
| A6 | revision이 더 크면 수신 시각이 되돌아가도 수락한다. 역전은 `receiveTimeInversion`으로만 알린다. | `RevisionDecision` | 수신 시각을 revision보다 우선하는 정책 |
| A7 | revision은 부호 있는 64비트다. 간격은 허용하고 +1을 요구하지 않는다. 넘침 규칙은 없다. | `RevisionCursor.revision` | 공급원별 revision 정의 |
| A8 | 스트림 키는 `SourceId`와 subject 토큰이다. subject 어휘는 없다. 관측 객체에는 subject 필드를 추가하지 않았다. | `ObservationKey` | 공통 subject 목록 |
| A9 | 미래 시각의 기본 정책은 `UNCHECKED`다. `REJECT_AFTER_REFERENCE`는 호출자가 고를 때만 적용하고, 기준 시각이 없으면 실패한다. | `FutureTimestampPolicy` | 데이터 종류별 미래 시각 허용 |
| A10 | 단위는 정확 일치만 본다. 환산과 별칭 표는 없다. | `IssueCode.UNIT_MISMATCH` | 단위 표준 표 |
| A11 | 건강·기상 값의 기본 범위는 없다. 호출자가 `NumericRange` 또는 `LongBounds`를 전달한다. | `ObservationConstraints` | 지표별 승인 범위 |
| A12 | 유한하지 않은 `Float`/`Double`은 구조적으로 거절하고 읽기 값으로 분류하지 않는다. 제품 범위가 아니다. | `IssueCode.NON_FINITE` | 없음. 측정값으로 쓰지 않는다. |
| A13 | 값이 있는 단위는 공백 문자와 비공백 ISO 제어 문자를 포함하지 않는다. 앞뒤만 보는 검사는 내부 공백과 NUL을 놓친다. 값이 null이면 단위 문자 검사는 하지 않는다. `VALID`/`STALE`은 null이 아닌 값이 필요하고, `UNAVAILABLE`/`DENIED`/`ERROR`는 값이 null이어야 한다. 위반은 거절하고 고치지 않는다. | `IssueCode.UNIT_PADDED`, `UNIT_CONTROL` | 오류에 부분 값을 남기는 계약이 승인될 때 |
| A14 | 파생은 `VALID`가 만료됐을 때만 `STALE` 사본을 만든다. 다른 상태는 올리지 않는다. 입력 객체는 유지한다. | `deriveStatus` | 명시적 STALE을 신선한 VALID로 회복하는 정책 |
| A15 | `observedAt`은 출처 시각이다. 예보 유효 구간은 `WeatherSnapshotDraft.validFrom`/`validTo`만 사용한다. | 초안 타입 | 발행 시각과 관측 시각의 공식 대응 |
| A16 | 오류 문장 필드는 두지 않는다. 상태와 값이 섞이지 않게 하기 위해서다. | `Observation` | 진단 문구 계약 |
| A17 | 날씨·상황·표현 의도는 이름이 있는 필드만 가진 초안이다. 생략 필드는 만들지 않았다. FSM은 없다. | `draft` 패키지 | WO-17~23의 나머지 구현 |
| A18 | 강수확률의 단위와 0~1/퍼센트 스케일은 검사하지 않는다. kind도 강제하지 않는다. | `probability` | 공급원 계약 |
| A19 | `locationId`, `focus`, `paletteId`, `quality`, `reasonCodes`, 상황 축 토큰의 어휘는 없다. 빈 값과 앞뒤 공백만 거절한다. | 초안 검사 | 승인된 어휘 |
| A20 | 이 모듈은 시계, 네트워크, Android SDK, 건강 데이터를 읽지 않는다. 기준 시각은 호출자가 전달한다. | 전체 | 어댑터 WO |
| A21 | 의존성은 Kotlin 2.4.21과 그 테스트 아티팩트뿐이다. | `build.gradle.kts` | 추가 라이브러리 승인 |
| A22 | `expiresAt < observedAt`은 구조 오류다. `expiresAt < receivedAt`은 늦은 수신으로 허용하고 신선도 계산에 맡긴다. | `IssueCode.EXPIRES_BEFORE_OBSERVED` | 없음 |
| A23 | 예보 구간의 `validTo < validFrom`은 역전, 같으면 길이 0으로 초안 검사에서 보고한다. 기상 규칙의 승인이 아니다. | `validateWeatherSnapshotDraft` | 0 길이 구간을 허용하는 결정 |
| A24 | 표시 코드는 `classifiedValue()`를 쓴다. `value ?: 0`으로 읽지 않는다. 이 함수는 단위 문자, 호출자 범위, TTL을 검사하지 않는다. 표시 전에 `validateObservation` 또는 `applyRevision`의 성공과 `deriveStatus`를 확인한다. `Freshness.UNDECLARED`는 `FRESH`가 아니다. | `ClassifiedValue` | 표시 계층 |
| A25 | 정수 범위는 `Byte`, `Short`, `Int`, `Long`에만 적용한다. 표현 가능한 `Long`이 없으면 `RANGE_EMPTY`다. 배타 구간의 인접 정수 `(n, n+1)`과, 배타 하한 `Long.MAX_VALUE`, 배타 상한 `Long.MIN_VALUE`가 포함된다. 부동소수 범위는 `Float`, `Double`에만 적용한다. 다른 형식은 변환하지 않고 `CONSTRAINT_TYPE_MISMATCH`다. 두 범위를 동시에 주면 `CONSTRAINT_CONFLICT`다. | `LongBounds.parse` | 공통 숫자 형식 |
| A26 | `-0.0`은 누락이 아니다. 범위의 `<`/`>`에서는 `0.0`과 같다. `Double.equals`는 부호 비트를 구분하므로 같은 revision에서는 `DUPLICATE_CONFLICT`다. `0.0`으로 바꾸지 않는다. | `samePayload` | 부호 비트를 정규화하는 결정 |
| A27 | `NumericRange`는 인접한 두 `Double` 사이의 열린 구간을 빈 범위로 거절하지 않는다. 예: `(0.0, nextUp(0.0))`. 그 구간에 들어가는 유한 값은 비교에서 나오지 않는다. 정수 범위와 같은 빈 구간 거절로 바꾸지 않았다. | `NumericRange.parse` | 부동소수 빈 구간 정책 |
| A28 | 승인 상태의 값은 null, `Boolean`, `Byte`, `Short`, `Int`, `Long`, `Float`, `Double`, `Char`, `String`만 둔다. 컬렉션, 배열, 사용자 정의 객체는 복사하지 않고 `UNSUPPORTED_PAYLOAD`로 거절한다. `RevisionCursor`는 그 값을 생성하지 못한다. 검증 전 입력 객체는 그대로 반환할 수 있다. | `isStableScalar` | 컬렉션 페이로드의 승인 |

테스트의 `"mm"`, `"percent"`, `"bpm"`, `"fixture"`는 픽스처 토큰이다. 승인된 단위가 아니다.
