# 차단점 및 불확실성 등록부
현재 항목만 관리한다. 이전 판정·증거 원본: [archive](../archive/README.md). OPEN/BLOCKED는 해결 증거 전 유지한다.

| ID | 상태 / 우선도 | 내용 및 증거 | 해결 조건 | 담당 |
|---|---|---|---|---|
| B-002 | BLOCKED / P1 | 현재 채팅 환경에 Android SDK/ADB 및 연결된 워치 없음 | CI로 대체 가능한 검증 수행; 실제 설치·센서·전력 시험은 접근 가능한 환경에서 수행 | GPT / Codex / 사용자 |
| B-003 | OPEN / P1 (SDK/빌드 해결) | CI 46002470824 SDK37.0 및 WFF5 Debug APK PASS. WFF5 실제 설치·런타임·전용 기능 미확인 | 실제 기기 및 P12 PoC 증거 | WO-08/35 |
| B-004 | OPEN / P1 | Watch7 크기/펌웨어/OS 및 최신 Samsung 기기 공식 매트릭스 미확인 | 공식 사양 확인, 실제 지원 대상별 기기/OS 기록 | WO-01 / 34 / 35 |
| B-005 | OPEN / P1 | WFF4 Reference, Variant, 숫자 전환, Gyro, 모션 트리거 및 최종 그래픽 품질 미검증 | P03~09의 실제 증거 | GPT-05/06 / Codex |
| B-006 | OPEN / P2 | 실제 KMA API 자격·할당량, Samsung Health 권한/파트너 및 독점 지표, Watch Face Push 조건 미확정 | 공식 조건 확인 및 실제 승인된 환경 시험 | GPT-08/09/11 |
| B-007 | OPEN / P1 | 정식 패키지 ID, 라이선스, 서명/배포 정책 미확정 | ADR 및 필요한 사용자 승인 | WO-29/38 |
| B-008 | OPEN / P2 | 전력/발열/실기기 소재 및 접근성 승인 미확보 | 비교 시험, 영상, 측정 및 사용자 승인 | WO-30~38 |

| 추가 항목 | 상태 / 조치 |
|---|---|
| AG01-AUD-01~09 | PR #2 HOLD. R07 사용량 제한, 실제 runtime NOT RUN. 보고서/독립 검토 후 판정. |
| GB02-AUD-05~08 및 revision 보호 | PR #3 HOLD. R04 보완 보고; R05 복합 전이/소비자/CI 제안 검증 후 독립 감사. |
| GB01-E1 | 비ASCII Windows Gradle worker 제한. ASCII worktree 사용. |
| GPT06-D1 | 호스트 링 충돌 해결: CI 46080386050. 실제 소재 승인 미확보. |
| B-011 | 현재 validator/evaluator pin RESOLVED: CI 46056609237. release 변경 시 재확인. |
| B-001/B-009/B-010, GPT04-D1/D2, GPT05-D1/D2/D3 | 이전 호스트 수정 검증 기록은 archive/evidence 참조. 재발 시 재개. |
| R06 | 소재 APK 후보 CI 46082882539 진행 중. 공식 WFF, 패키지, 메모리, 서명 및 실제 렌더링 별도 게이트. |

신규 차단점은 ID, 심각도, 재현, 증거, 담당 및 해결 조건을 기록한다. 과거 세부 이력은 보관소 및 해당 evidence에 연결한다.

OPS-07: 문서 검사 CI와 GitHub 필수 상태 검사 설정 미확인. 후보 검증 전 미통합. 실기기 설치 승인/접근 없음; 기기 검사 NOT RUN.
