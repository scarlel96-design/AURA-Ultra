# 차단점 및 불확실성 등록부
OPEN은 미해결, BLOCKED는 외부 조건 필요, RESOLVED는 해결 증거가 있는 상태다. 기록을 삭제하지 않는다. 해결 시 검증 SHA와 증거를 추가한다.

| ID | 상태 / 우선도 | 내용 및 증거 | 해결 조건 | 담당 |
|---|---|---|---|---|
| B-001 | OPEN / P0 | CI 45997124733 및 45998056978: WFF2 APK 실행 코드 검사 FAIL. 실제 ZIP 항목 미확인. WFF3/4 개별 내용 검사도 미확인. | 정확한 항목과 원인 확인, 3 APK 공식 규격 및 내용 검사 PASS, Artifact 확보 | GPT-01 |
| B-002 | BLOCKED / P1 | 현재 채팅 환경에 Android SDK/ADB 및 연결된 워치 없음 | CI로 대체 가능한 검증 수행; 실제 설치·센서·전력 시험은 접근 가능한 환경에서 수행 | GPT / Codex / 사용자 |
| B-003 | OPEN / P1 | WFF5 빌드 비활성. SDK/API, 스키마, 설치된 OS 미확정 | 공식 문서와 호환 도구·기기 증거 확보, 별도 profile 검증 | GPT-02 / 실기기 |
| B-004 | OPEN / P1 | Watch7 크기/펌웨어/OS 및 최신 Samsung 기기 공식 매트릭스 미확인 | 공식 사양 확인, 실제 지원 대상별 기기/OS 기록 | WO-01 / 34 / 35 |
| B-005 | OPEN / P1 | WFF4 Reference, Variant, 숫자 전환, Gyro, 모션 트리거 및 최종 그래픽 품질 미검증 | P03~09의 실제 증거 | GPT-05/06 / Codex |
| B-006 | OPEN / P2 | 실제 KMA API 자격·할당량, Samsung Health 권한/파트너 및 독점 지표, Watch Face Push 조건 미확정 | 공식 조건 확인 및 실제 승인된 환경 시험 | GPT-08/09/11 |
| B-007 | OPEN / P1 | 정식 패키지 ID, 라이선스, 서명/배포 정책 미확정 | ADR 및 필요한 사용자 승인 | WO-29/38 |
| B-008 | OPEN / P2 | 전력/발열/실기기 소재 및 접근성 승인 미확보 | 비교 시험, 영상, 측정 및 사용자 승인 | WO-30~38 |
| B-009 | RESOLVED | CI 45997002132 SDK manager not found (exit 127) | CI 45997124733 SDK 설치·확인 PASS | 수정 544a7010 |

| B-010 | OPEN / P1 | tools/verify_wff.py의 성공 조건이 일반 VALID 포함 여부에 의존한다. 헤더 Validation도 매치되므로 명시적 성공을 검증하지 못할 위험. 실제 두 CI의 성공 로그는 버전별 PASSED를 확인했다. 오판 발생 자체는 미재현. | 공식 validator 결과 형식 확인, 성공·실패·불명확·버전 불일치 회귀 시험, 대상별 명시적 성공 검사 | GPT-01 |

B-001 해결 전 후속 통합 작업을 GO 처리하지 않는다. 독립 테스트·설계·도메인 작업은 RESUME_PROTOCOL의 선행 조건에 따라 진행 가능하다.

## 운영 점검 기록 (2026-11-27)
문서 기준 SHA 951593e4fbbac33f2c675ea5cbbf07edbe22353d, CI 45998609726 (completed/failure): Official WFF validation: success; Build debug APKs: success; Check APK contents: failure; Upload debug APKs: skipped. https://github.com/scarlel96-design/AURA-Ultra/actions/runs/45998609726. 운영 문서 변경 실행이며 제품 코드 변경 없음. B-001/B-010 해결 증거 없음.
신규 제품 차단점 없음. 기존 차단점은 해결되지 않았다. 매 턴 PRE-FLIGHT에서 최신 증거를 다시 확인한다.

## GPT-01 회차 01 수정 후보
B-001: CI 45998909046, job 140505251267에서 DEX build/merge 작업 및 APK FAIL 재확인. 정확한 이전 ZIP 항목은 미확인. Samsung 공식 WFF 가이드의 minify 활성화/resource shrink 비활성화 적용. 검사기는 모든 APK의 정확한 항목과 컴파일된 Manifest를 기록한다. 새 CI 검증 대기.
B-010: 명시적 파일/버전 PASSED 판정, 오류/종료 코드/중복 검사, 정상·실패 fixture 및 실제 잘못된 XML probe 추가. 새 CI 검증 대기. 두 차단점은 OPEN 유지.

- GPT-01 코드 SHA ef9f9c9bbb2020de835926a3bf0e4262b9c89d51, CI 45999371709: completed/success. 실제 최종 로그/Artifact 확인 전 B-001/B-010 OPEN 유지. STATUS의 단계별 결과 참조.
