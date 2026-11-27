# AURA Ultra

Galaxy Watch7 이후의 Wear OS 갤럭시 워치를 위한 지능형 프리미엄 워치 페이스 플랫폼.

**상태: 설계 기준선 v1.0 / 구현 미착수 / 출시 NO-GO (2026-11-27)**

AURA는 고급 시계의 금속·유리 소재, 정밀한 데이터 시각화, Apple 디자인의 연속 모션 원리를 독자적인 원형 UI로 통합한다. 화려함은 필수 품질 요구사항이다. 가독성, 안정성, 전력 효율과 함께 검증한다.

## 시작하기
1. [AGENTS.md](AGENTS.md)를 읽는다.
2. [전체 설계도](docs/MASTER_ARCHITECTURE.md)와 [요구사항](docs/REQUIREMENTS.md)을 읽는다.
3. [개발 로드맵](docs/ROADMAP.md)과 [현재 상태](docs/STATUS.md)를 확인한다.
4. [WO-01](docs/work-orders/WO-01.md)만 수행한다. 승인 전 후속 WO를 시작하지 않는다.

## 기술 문서
| 문서 | 목적 |
|---|---|
| [디자인 시스템](docs/DESIGN_SYSTEM.md) | 소재, 레이아웃, 테마, 그래픽 품질 |
| [모션 명세](docs/MOTION_SPEC.md) | 시각적 연속성 및 이벤트 모션 |
| [호환성](docs/COMPATIBILITY.md) | WFF 2~5, 기기별 검증, 향후 확장 |
| [데이터 및 지능](docs/DATA_INTELLIGENCE.md) | 건강·기상·상태 머신·데이터 계약 |
| [성능 및 전력](docs/PERFORMANCE.md) | 메모리, 발광 픽셀, 배터리 예산 |
| [보안 및 안정성](docs/SECURITY.md) | 권한·데이터·업데이트·복구 |
| [개발 지침](docs/DEVELOPMENT.md) | 도구, 빌드, 오픈소스, 변경 관리 |
| [품질 검증](docs/QUALITY_GATES.md) | PoC, 시험, 증거, GO/NO-GO |
| [기술 근거](docs/REFERENCES.md) | 공식 문서와 조사 한계 |
| [WO 양식](docs/work-orders/TEMPLATE.md) | 후속 작업 명세 양식 |

워치 페이스는 WFF 리소스 전용 APK다. Wear Services 및 Mobile Studio는 실행 코드를 포함하는 별도 앱이다. 현재 APK와 테스트 결과는 없다. 본 저장소의 라이선스 및 배포 조건은 아직 확정하지 않았다.
