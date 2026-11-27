# AURA Design System — 시각 품질 규격
## 방향
화려함을 장식의 개수가 아닌 소재의 정교함, 계층, 동적 광원, 유기적 움직임으로 구현한다. Apple HIG에서 연속성·가독성 원칙을 참고한다. 원형 디스플레이에 맞는 독자적 자산을 제작한다.

## Signature 플래그십
중앙 시간은 가장 높은 시각 우선순위를 유지한다. 상단 날짜와 배터리, 중하단 날씨·심박 패널, 하단 활동 진행률 및 예상 강수량을 배치한다. 외곽 링은 정밀 눈금과 데이터 진행률로 구성한다. 실제 값과 장식 눈금을 구분한다.

## 공통 토큰 (초기 제안)
450×450 논리 좌표. 중심 (225,225). 모든 요소의 외곽 경계를 원형 안전 영역에서 검사한다.
| 토큰 | 초기값/규칙 |
|---|---|
| time.primary | 직경의 18~24%; 고정폭 숫자 또는 tabular digits |
| text.secondary | 직경의 5~8%; 실기기 가독성 우선 |
| safe.edge | 최소 12~18 논리 단위; 실제 글리프·번인 이동 확인 |
| lighting.origin | 좌상단 30~45°; 소재 간 동일 방향 |
| base | #030508 또는 #000000 |
| text.primary | #F3F7FA |
| text.secondary.color | #A9BACB |
| accent.weather | #79D4F2 |
| accent.activity | #81D7AF |
| accent.heart | #F29AA8 |
| warning | #FFA84D; 색만으로 상태 전달 금지 |
| panel.radius | 원형 화면 및 패널 크기에 비례 |
| touch.target | Wear OS 공식 권장 크기와 원형 영역 준수 |

토큰은 측정 전 목표다. 글꼴 라이선스를 확인하고 한글 fallback을 포함한다. 터치 영역은 충돌하지 않게 설정한다.

## 레이어
L00 OLED Base → L01 Atmosphere → L02 Material → L03 Depth → L04 Precision Ring → L05 Data Visualization → L06 Glass Panel → L07 Typography → L08 Optical Highlight → L09 Motion Effect → L10 Feedback.
정보 위에 광원이 지나갈 때도 대비를 유지한다. 불필요한 전체 화면 투명 비트맵을 피한다.

## 소재 구현
Liquid Crystal: 사전 렌더링 렌즈 이미지, 마스크, 투과/반사 모사, 얇은 테두리, 국소 하이라이트. 진짜 광학 굴절 셰이더가 아니다.
Titanium: 브러시드 메탈, 방사형 결, 미세 가공 표현, 이동하는 좁은 광택.
Atmospheric Light: 시간·날씨에 따른 그라데이션, 색온도 및 국소 입자.
Spatial Depth: 배경·소재·반사광의 이동량 차이. 핵심 텍스트는 고정한다.
WFF 3+ 혼합 모드, WFF 4 색상 변환, WFF 5 확장 혼합 기능을 지원 여부에 따라 사용한다. 하위 버전은 사전 합성 자산으로 유사 품질을 유지한다.

## 테마 8종
| 테마 | 정체성 |
|---|---|
| Signature | Crystal + Titanium + Ultra의 대표 디자인 |
| Titanium | 정밀 금속 결, 기계식 시계 감성 |
| Crystal | 유리 소재, 반사, 깊이감 |
| Ultra | 고밀도 원형 데이터 링 |
| Obsidian | 순수 검정, 얇은 정밀 요소 |
| Chronograph | 아날로그·디지털 하이브리드 |
| Aurora | 환경광 및 오로라 |
| Night Vision | 저휘도 적색, 야간 가독성 |

테마는 색상만 다른 복제본이 아니다. 소재·레이아웃·모션·타이포그래피를 구분한다. Signature의 실기기 품질 승인 후 나머지 테마를 확장한다.

## 검수
각 테마의 AOD/활성/절전/오류/고대비 상태 스크린샷을 수집한다. 작은 화면, 긴 한국어, 12시간제, 최대/최소 숫자 및 터치 영역을 검사한다. 광원 불일치, 밴딩, 픽셀 깨짐, 잘림, 눈부심, 정보 가림, 의미 없는 발광을 결함으로 기록한다. 콘셉트 이미지를 실제 렌더링 증거로 사용하지 않는다.
