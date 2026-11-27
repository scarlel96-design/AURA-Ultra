# 기술 근거 및 재검증 목록
기준선은 2026-11-27의 AURA Ultra 심층 연구 및 독립 조사, 이후 통합 설계에 근거한다. 원본 연구 보고서는 저장소에 아직 첨부하지 않았다. 다음 공식 문서에서 정확한 버전·태그·정책을 재확인한다. 외부 링크는 구현 검증 결과가 아니다.

| 자료 | 검증 대상 |
|---|---|
| https://developer.android.com/training/wearables/wff | WFF 버전, XML, 선언형 제약 |
| https://developer.android.com/reference/wear-os/wff | Transform, Animation, Variant, Reference, Gyro, data sources, mask/blend |
| https://github.com/google/watchface | validator, evaluator, optimizer |
| https://developer.android.com/training/wearables/complications | 타입, 갱신, 권한 |
| https://developer.android.com/training/wearables/data | Data Layer |
| https://developer.android.com/health-and-fitness/guides/health-services | Health Services |
| https://developer.android.com/health-and-fitness/guides/health-connect | Health Connect |
| https://developer.samsung.com/health/data/overview.html | Samsung SDK, 파트너 조건 |
| https://developer.samsung.com/watch-face-studio/overview.html | WFS 기능 |
| https://developer.samsung.com/remote-test-lab | 원격 기기 |
| https://www.samsung.com/sec/watches/ | 국내 공식 기기 사양·지원 |
| https://developer.apple.com/design/human-interface-guidelines/ | 디자인·모션·가독성 |
| https://developer.android.com/develop/ui/compose/animation/shared-elements | 앱 내부 shared element |
| https://developer.android.com/develop/ui/views/graphics/agsl | AGSL; WFF 내부 사용 아님 |
| https://www.data.go.kr/data/15084084/openapi.do | 기상청 단기예보 |
| https://open-meteo.com/en/docs | 대체 기상 예보·약관 |

WO-01에서 출처별 접속일, 정확한 문서 링크, 근거 요약, 적용 버전, 확인/미확인 상태를 기록한다. 최신 신형 기기명 및 사양을 삼성 공식 문서로 확인한다. WFF 5 지원 상태, 메모리 기준, 발광 픽셀, Watch Face Push와 Samsung Health의 배포 요건을 재검증한다. 연구 문서의 예제 코드는 빌드 완료 코드가 아니다. Apple의 비공개 렌더링 기술을 확인된 구현으로 단정하지 않는다.
