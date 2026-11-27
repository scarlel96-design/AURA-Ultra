# 데이터 계약 및 AURA Intelligence

## 데이터 공급
| 데이터 | 우선 공급원 | 처리 |
|---|---|---|
| 시간/날짜/요일 | WFF | 외부 앱 불필요 |
| 걸음/목표/심박/배터리/충전 | WFF | 최신성·지원 여부 확인 |
| 거리/칼로리/운동 | Health Services | 권한 및 기기 기능 확인 |
| 수면/SpO2 | Health Connect / Samsung Health | 최근 측정 시각 표시 |
| 스트레스/수면 점수/에너지 점수 | Samsung 공식 SDK 검토 | 지원 미확정; 없으면 숨김 |
| 현재 날씨/기온/강수확률/UV | WFF 2+ | 공급 상태 확인 |
| 체감/최고최저/습도/풍속풍향/시간별 예보 | KMA 또는 Open-Meteo | 단위·시간 기준 표준화 |
| 관측/예상/누적 강수량 | KMA 우선 | 종류 구분; 누적 기간 표시 |
| 강수 시작/종료 | 시간별 예보 추정 | 예상 표기; 정밀도 과장 금지 |
| 대기질 | 공식 대기질 API | PM2.5/PM10 구분 |
| 일출/일몰 | 기상 API | 위치 및 시간대 확인 |
| 폰 배터리/연결 | Data Layer | 마지막 갱신 및 연결 상태 |
| 일정/알람 | 시스템 complication | 사용자 공급원 선택 |
| 잔여 배터리 시간 | 통계 모델 후보 | 추정/불확실성 표시 |

Samsung Health Data SDK의 파트너·개발자 모드·지원 데이터 조건을 검증한다. 실시간 생체 데이터나 독점 점수에 대한 접근을 가정하지 않는다.

## 도메인 계약 (설계 의사코드)
```text
Observation<T> {
  value: T?; unit: String; source: SourceId;
  observedAt: Instant?; receivedAt: Instant;
  expiresAt: Instant?; status: VALID|STALE|UNAVAILABLE|DENIED|ERROR;
  kind: OBSERVED|FORECAST|ESTIMATED|SYSTEM;
}
WeatherSnapshot { locationId; issuedAt; validFrom; validTo; probability; observedRain; forecastRain; ... }
ContextSnapshot { weather; activity; power; timeOfDay; connectivity; userMode; dataQuality; }
PresentationIntent { focus; paletteId; quality; motionAllowed; reasonCodes; revision; }
```
값 범위, 단위, 시간대와 출처를 검증한다. 누락을 0으로 바꾸지 않는다. stale 값과 오류를 구분한다. 비동기 수신에서 오래된 revision을 적용하지 않는다.

## 갱신 정책
WFF 시스템 데이터는 시스템 갱신을 따른다. 일반 complication 정기 갱신은 공식 최소 간격(300초)을 준수한다. 이벤트 갱신 요청의 처리 시각은 보장하지 않는다. 날씨 API는 공급원 발표 주기, 할당량, 위치 변화에 맞춰 갱신한다. 초기 제안: 날씨 15~60분, stale 표시는 데이터별 validTo/TTL 기준. 건강 이력은 데이터 공급원 동기화에 따른다. 실패 시 제한된 지수 백오프와 캐시를 사용한다. AOD에서 추가 고빈도 네트워크 및 센서 작업을 피한다.

## 상태 머신
독립 상태 축: power(NORMAL/LOW/CHARGING), weather(NORMAL/PRECIP/ALERT/UNKNOWN), activity(REST/ACTIVE/EXERCISE/UNKNOWN), light(DAY/NIGHT), connectivity(ONLINE/OFFLINE), userMode(DEFAULT/WORK/SLEEP/MANUAL).
우선순위: CRITICAL > POWER > EXERCISE > WEATHER > CONTEXT > DECORATIVE.
시간은 고정한다. 중요 정보만 강조한다. 낮은 배터리에서 날씨 숫자는 유지하고 입자 효과를 제거한다. 실제 OS 절전 상태와 AURA 품질 프로필을 구분한다.
초기 정책 후보: 저전력 진입 15%, 해제 20%; 날씨 강조 진입 확률 70%, 해제 50%; 최소 상태 유지 60초(긴급·충전 예외). 값은 실기기 검증 후 확정한다. 운동/업무/수면 준비 추론에는 명시적 사용자 설정 또는 검증 가능한 신호만 사용한다. 민감한 행동을 추측하지 않는다.

## WFF 전달
공식 complication 타입으로 값을 제공한다. WFF 4 Reference는 지원 필드와 표현식 범위 내에서 그래픽 공유에 활용한다. 고주파 센서 애니메이션은 WFF 자체 데이터로 처리한다. 외부 앱을 프레임 렌더러로 사용하지 않는다. 앱 실패 시 시간/날짜를 유지한다.

## 상세 정보
Wear 상세 UI는 관측/예측/갱신 시각을 표시한다. Mobile Studio는 동의한 설정과 필요한 데이터만 동기화한다. 오프라인 및 권한 거부 상태를 시험한다.
