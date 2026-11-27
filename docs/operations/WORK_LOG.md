# 누적 개발 이력
이 문서는 시간순 append-only 기록이다. 사실 정정은 새 항목으로 추가한다. 현재 상태의 정본은 ../STATUS.md다.

## 2026-11-27 / 설계 기준선
- 커밋 6f074fbc86c1382a52bfeac57023c1a3f7a7559e: 초기 설계 문서 18개, 요구사항 26개, 38 WO 계획, 8개 테마, 15개 PoC.
- 실제 제품 코드 및 실기기 시험 미실시. 원본 심층 연구 보고서는 저장소에 별도 첨부하지 않음.

## 2026-11-27 / Bootstrap
- 커밋 171fca407653001f085683ee30c20608c8336b31: Gradle Wrapper 8.11.1/JDK17/AGP8.10.1/SDK36, WFF2/3/4 flavor, 기본 WFF XML, 임시 프리뷰, 자동 검증.
- CI 45997002132: Wrapper/구조 PASS, sdkmanager 미설치로 FAIL.
- 커밋 544a7010f4bed515d667bfa6a9bbda1389f5bc92: SDK 설치 action 추가.
- CI 45997124733: SDK/공식 WFF validator/Gradle assemble PASS, WFF2 APK 실행 코드 검사 FAIL, Artifact SKIP. WFF3/4 내용은 검사 중단으로 미확인. B-001 등록.
- 메모리, AOD 품질, 실제 워치 실행은 NOT RUN.

## 2026-11-27 / 세션 독립형 운영
- 기준 부모 SHA 544a7010f4bed515d667bfa6a9bbda1389f5bc92. GPT 선행 개발 목표, 작업 큐, 재개 규칙, 차단점·진행률·인계 정책 및 현재 CI 증거 기록.
- 사용자 승인: "다음 작업"으로 현재 상태를 기반으로 다음 작업을 자율 선택·수행.
- 이번 커밋은 운영 문서만 변경. 앱 코드 및 APK 오류 미수정.
- 다음: GPT-01 / B-001의 정확한 APK 항목 확인 및 원인 수정.

## 2026-11-27 / 운영 및 검증 규정 강화
- 기준 부모 SHA 28f51fd89b08cac0e183bbc6c5dfab98dd0f81fa. 기존 AGENTS, 재개 규정, 품질 게이트, 작업 양식 및 체크포인트를 대조 검토했다.
- 작업별 영속 기록, G0~G7 검증, 요구사항 추적표, 검사기 실패 검출, 구현 후 별도 리뷰, 증거 감사, 보고서 양식을 추가했다.
- CI 45998056978 로그에서 공식 validator PASSED #2/#3/#4, Gradle BUILD SUCCESSFUL, APK 검사 FAIL을 확인했다. B-001 유지. 검증 스크립트의 일반 VALID 포함 조건 위험 B-010 등록. 실제 오판은 미재현.
- 변경 범위: 운영 문서. APK 검사와 validator 스크립트는 미수정. 다음 작업은 GPT-01 유지.
- 증거: docs/evidence/OPS-02/REPORT.md. 최종 저장소 반영은 해당 커밋 이력에서 확인한다.

## 2026-11-27 / 매 턴 PRE-FLIGHT 진입 게이트
- 기준 부모 SHA 951593e4fbbac33f2c675ea5cbbf07edbe22353d. 사용자 요청에 따라 루트 AGENTS.md 최상단에 필수 확인 순서 배치. README와 STATUS 상단에서 연결.
- 매 턴 최신 HEAD 및 필수 문서 확인, 활성 작업·실제 소스·CI 대조, 보고서에 PRE-FLIGHT 판정 기록. 동일 대화 및 재시도에도 적용.
- 문서 기준 SHA 951593e4fbbac33f2c675ea5cbbf07edbe22353d, CI 45998609726 (completed/failure): Official WFF validation: success; Build debug APKs: success; Check APK contents: failure; Upload debug APKs: skipped. https://github.com/scarlel96-design/AURA-Ultra/actions/runs/45998609726. 운영 문서 변경 실행이며 제품 코드 변경 없음. B-001/B-010 해결 증거 없음.
- 운영 규정·기록·검증·보고서 양식 동기화. 제품 코드 변경 없음. 다음 GPT-01/B-001/B-010 유지.
- 증거: docs/evidence/OPS-03/REPORT.md. 커밋 후 실제 등록과 링크 확인.

## 2026-11-27 / GPT-01 회차 01 — 초기 패키징 및 검사 강화
- 기준 HEAD 95e51cca23210f930dc3716cb790e791585a7bf0. PRE-FLIGHT: 활성 문서와 요구사항·실제 도구 및 CI 45998909046 확인.
- 삼성 공식 WFF 가이드에 따라 debug/release R8 활성화 및 리소스 축소 비활성화. 이전 APK 항목 미확인으로 원인은 가설 상태.
- WFF 결과 명시적 파일/버전 성공 검증, 실제 invalid XML 검사, 모든 APK ZIP/manifest 검사, 단위 회귀 시험 추가.
- 새 CI 실행 결과 미확인. B-001/B-010 OPEN, GPT-01 NO-GO 유지. evidence/GPT-01/REPORT-01.md 참조.

- 회차 01 코드 SHA ef9f9c9bbb2020de835926a3bf0e4262b9c89d51, CI 45999371709 상태 completed/success 확인. 검증 세부 상태는 STATUS 및 REPORT-01에 저장. 별도 자기 재검토 완료. 제품 GO 미선언. 문서 전용 체크포인트는 실행 중 CI 보존 목적의 [skip ci].

- 최종 CI 45999371709 전체 SUCCESS. 19 단위 시험, WFF2/3/4 정상 및 실패 검출, 3 APK build/내용 검사, Artifact 15197113871 확인. B-010 RESOLVED, B-001 현재 실패 해소(과거 원인 증거 보완 전 OPEN). GPT-01 PARTIAL, WO-01 PARTIAL, 출시 NO-GO. 다음 회차: 과거 실패 격리 재현 및 공식 메모리 평가 통합. 정확한 검증 SHA 및 해시: docs/evidence/GPT-01/REPORT-01.md.

## 2026-11-27 / GPT-01 회차 02
- 기준 HEAD 86f9df3f174f2356959ab04ec4ab6fae0379521e. PRE-FLIGHT 및 이전 CI/Artifact 확인. 공식 memory-footprint release digest, CLI와 소스의 report/byte 단위 확인.
- 기존 70/7 MiB 예산 검증, 실패 검출 단위 시험, debug 서명 검사, 별도 과거 SHA 재현 CI 추가. 제품 XML/Gradle 설정 변경 없음. 새 CI PENDING. REPORT-02 참조.

- 회차 02 코드 98a4f915577cf3175beeca19864a431061673e7b, CI 46000111754 및 46000111676 확인. 원격 소스 자기 재검토 완료. 실제 단계별 상태와 재개 조건은 STATUS 및 REPORT-02에 저장. [skip ci] 문서 체크포인트.

- GPT-01 회차 02 최종: 코드 98a4f915577cf3175beeca19864a431061673e7b, 현행 CI 46000111754 및 과거 재현 CI 46000111676 SUCCESS. 26 PASS/0 FAIL, 메모리 2,371,712 bytes 양 모드 및 3 APK v2 서명 PASS, Artifact 15197747235. 과거 classes.dex/R 클래스 재현으로 B-001 RESOLVED. B-010 RESOLVED 유지. GPT-01 GO(빌드 토대), 1/12 GPT 묶음 완료, WO-01 PARTIAL, 출시 NO-GO. 다음 GPT-02. 증거 REPORT-02.
