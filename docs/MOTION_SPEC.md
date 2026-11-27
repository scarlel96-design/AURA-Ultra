# AURA Continuity & Motion — 명세
모든 모션은 출발 객체와 종료 객체의 시각적 연결을 유지한다. 기존 객체의 위치·크기·색상·투명도를 변경하는 방식을 우선한다. 정교한 모션은 핵심 품질 요구사항이다.

## AOD 연속 모션
WFF 4 Variant의 duration/startOffset은 시스템 전환 시간의 상대 비율이다. 고정 밀리초를 강제하지 않는다. 지원 속성과 보간 함수는 공식 스키마로 검증한다.
| 요소 | 활성화 구간 | 동작 |
|---|---|---|
| 시간 | 0~85% | 동일 객체를 중심에서 활성 위치로 이동; 항상 읽을 수 있게 유지 |
| 외곽 링 | 10~100% | 최소 표시에서 확장 |
| 소재 하이라이트 | 15~80% | 국소 반사광 형성 |
| 정보 패널 | 25~90% | 크기·위치·투명도 보간 |
| 보조 정보 | 45~100% | 안정된 최종 배치로 등장 |

비활성화는 반대 상태로 연결한다. 실제 역재생 동작과 재진입 처리 여부는 실기기 시험으로 확인한다. WFF 2/3에서는 정적 AOD variant와 지원 가능한 전환을 사용한다.

## 이벤트 명세
시간은 초기 설계 목표다. WFF에서 해당 트리거, 중단, 이전 값 보존이 가능한지 PoC로 확인한다.
| ID / 이름 | 시작 → 종료 | 목표 | 후보 구현 / 대체 |
|---|---|---|---|
| M01 Continuity Wake/Sleep | AOD ↔ Active | 시스템 비율 | WFF4 Variant / 정적 상태 |
| M02 Fluid Digits | 이전 숫자 → 새 숫자 | 180~250ms | 자리별 변환·시퀀스 / 즉시 교체 |
| M03 Glass Formation | 최소 패널 → 완성 패널 | 250~550ms | 그룹 변환·마스크 / 단순 fade |
| M04 Liquid Morph | 형상 A → B | 300~600ms | 지원 shape 속성 / scale+crossfade |
| M05 Orbital Flow | 진행률 A → B | 250~450ms | Arc Transform/Animation |
| M06 Precision Sweep | 정적 → 국소 광원 → 정적 | 500~900ms | 작은 이미지 시퀀스 |
| M07 Optical Reflection | 기울기 A → B | 센서 반응 | Gyro / 고정 광택 |
| M08 Spatial Parallax | 레이어 이동 | ±2~6 논리 단위 | Gyro / 정적 깊이 |
| M09 Weather Morph | 기상 상태 A → B | 400~700ms | 조건·리소스 / 정적 아이콘 |
| M10 Atmospheric Motion | 날씨 이벤트 | 짧은 재생 | 국소 PartAnimatedImage |
| M11 Solar Transition | 주간 ↔ 야간 | 분 단위 | 시간·색상 표현식 |
| M12 Heart Pulse | 표시 BPM에 반응 | 짧은 저진폭 | 실제 박동 동기화 아님; 정적 HR 대체 |
| M13 Activity Bloom | 목표 미달 → 달성 | 700~1200ms | 이벤트 1회 / 정적 달성 표시 |
| M14 Energy Flow | 충전 상태 변경 | 600~900ms | 조건부 애니메이션 / 정적 아이콘 |
| M15 Focus Motion | 중요도 변경 | 200~450ms | 색상·투명도 / 고정 강조 |
| M16 Theme Transition | 설정 변경 | 플랫폼 지원 범위 | 시스템 전환 / 즉시 전환 |
| M17 Detail Continuity | 페이스 → 앱 | 시스템 제약 | 동일 디자인 토큰; 앱 내부 shared element |

## 품질
EASE_IN_OUT, EASE_OUT, CUBIC_BEZIER 등 지원 보간을 선택한다. OVERSHOOT는 실제 물리 스프링이 아니다. Compose 앱에서만 물리 스프링과 앱 내부 공유 요소 전환을 검토한다.
모션 감소 시 장식 효과를 제거한다. AOD에서는 지속 애니메이션과 센서 기반 효과를 제거한다. 과도한 반복, 갑작스러운 레이아웃 변경, 읽기 어려운 시간 표시를 금지한다.
각 모션의 지원 API, 트리거, 반복·중단 가능 여부, 메모리, 프레임 영상 및 전력 영향을 증거에 기록한다.
