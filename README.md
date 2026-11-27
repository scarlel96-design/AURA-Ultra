# AURA Ultra

Galaxy Watch7 이후의 Wear OS 갤럭시 워치를 위한 지능형 프리미엄 워치 페이스 플랫폼.

**상태: 설계 기준선 v1.0 / 초기 빌드 토대 / 출시 NO-GO (2026-11-27)**

AURA는 고급 시계의 금속·유리 소재, 정밀한 데이터 시각화, Apple 디자인의 연속 모션 원리를 독자적인 원형 UI로 통합한다. 화려함은 필수 품질 요구사항이다. 가독성, 안정성, 전력 효율과 함께 검증한다.

## 시작하기
1. [AGENTS.md](AGENTS.md)를 읽는다.
2. [전체 설계도](docs/MASTER_ARCHITECTURE.md)와 [요구사항](docs/REQUIREMENTS.md)을 읽는다.
3. [개발 로드맵](docs/ROADMAP.md)과 [현재 상태](docs/STATUS.md)를 확인한다.
4. [재개 규정](docs/operations/RESUME_PROTOCOL.md)과 [GPT 작업 계획](docs/operations/GPT_EXECUTION_PLAN.md)을 읽는다.
5. STATUS의 활성 작업을 수행한다. 사용자 지시가 '다음 작업'이면 규정에 따라 안전한 작업을 자율 선정한다.

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

워치 페이스는 WFF 리소스 전용 APK다. Wear Services 및 Mobile Studio는 실행 코드를 포함하는 별도 앱이다. 초기 빌드 토대가 추가됐다. 실제 빌드 및 실기기 판정은 CI와 증거 문서에서 확인한다. 본 저장소의 라이선스 및 배포 조건은 아직 확정하지 않았다.

## 초기 빌드 토대
[BUILD_GUIDE.md](docs/BUILD_GUIDE.md) · [WO-01 예비 증거](docs/evidence/WO-01/REPORT.md) · [Bootstrap 증거](docs/evidence/BOOTSTRAP/REPORT.md)
WFF2/3/4 debug variant, Gradle Wrapper, SDK36, 자동 검사 및 CI를 구성했다. WFF5와 프리미엄 그래픽은 후속 PoC 대상이다.

## 세션 독립형 개발 운영
[핵심 요구사항 보존표](docs/operations/PROJECT_INVARIANTS.md) · [차단점](docs/operations/BLOCKERS.md) · [작업 이력](docs/operations/WORK_LOG.md) · [진행률 기준](docs/operations/PROGRESS_MODEL.md) · [인수인계](docs/operations/HANDOFF.md) · [GPT-01](docs/operations/GPT-01.md)
현재 작업과 실제 검증 결과는 STATUS를 참조한다. 이전 대화를 기억하지 않아도 저장소를 읽어 재개할 수 있게 유지한다.
