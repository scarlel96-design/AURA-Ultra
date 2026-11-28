# 전체 중간 감사 R02 — Domain 및 Intelligence
2026-11-28 KST. main 1e5e4b14e0414c66cc38fec582eac2f28c3ad5f7, GB-02 122d81b05fb0fc56020fb3d03b667545eb6671c3, AG-01 fc98c3ad5993e131f733a9444b5849e737a49086. PRE-FLIGHT: 최신 AGENTS/STATUS/RESUME/INVARIANTS/TASK_RECORD/VERIFICATION/TEMPLATE/GPT_EXECUTION_PLAN/BLOCKERS/WORK_LOG/agent-orders/README/architecture/requirements/quality/roadmap/DATA_INTELLIGENCE/SECURITY/GPT-06 및 종료 증거, GB/domain 인터페이스/가정/소스/시험/로그 확인. R-04/11/12/17/18/21/22; WO-17~23. 감사만 수행. 제품/외부 브랜치 수정 없음.
GB-02 R05 이전 확인 10 XML에 잔여 6개/38개 시험 추가 검사, 전체 16 XML/153건 식별자·개수·오류 표시 일치. GB HEAD 변경은 보고서와 Windows 로그뿐. 해당 로그 315 PASS/1 ERROR, generated palette.svg CRLF.
[격리 감사 코드](https://github.com/scarlel96-design/AURA-Ultra/tree/d49e01409abbae74f98fc6a79a93e16b6723c555/tests/audit/R02/MidAuditR02.kt). 감사 브랜치에 workflow, test, plan 3개 경로만 추가. 최초 CI 46086528253 실패(HEAD^ shallow checkout); fetch-depth 0 및 고정 base 비교로 수정, 기존 소스/시험 무변경. [CI](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46086659055) job 140797694591 SUCCESS, wrapper digest OK, Gradle 9.3.1/JDK17/Kotlin 2.4.21. Domain clean 81 PASS(52s), Intelligence clean 72 PASS(24s), 신규 9개 정상 실행(18s; 정상 대조 3, 위험 관찰 6). [Artifact](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46086659055/artifacts/15239207748) ID 15239207748, 13504 B, SHA256 a6bb222efbe185ae5e589ded0981106b953f87154b18d2ad8e4b3091b8c96f82. 직접 다운로드, ZIP CRC, 17 XML(7/81+9/72+1/9) 클래스·메서드·개수 일치, 0 FAIL/ERROR/SKIP. 성공한 관찰 시험이 동작 승인이라는 뜻은 아니다.
| ID | 분류 | 실제 결과 및 해결 조건 |
|---|---|---|
| AUD-R02-01 | P1 계약 결함 | DENIED/ERROR/UNAVAILABLE 각각 null TTL→UNDECLARED, expired→STALE, valid TTL만 원래 상태. 9개 중 6개 사유 소실, 값은 미공개. R-17 오류 상태 및 TTL 별도 유지. |
| AUD-R02-02 | P2 통합 위험 | referenceTime 1초에 미래 20초 관측 Fresh(70). 도메인 opt-in 미래 거부 정상. 출처별 허용 오차 및 발행/예보 시각 계약. |
| AUD-R02-03 | P1 통합 위험 | 최신 관측 80→나중 처리된 과거 관측 10, LOW 전환. applyRevision 자체 정상. 스트림별 출처/revision 및 처리 순서 보장. |
| AUD-R02-04 | P1 통합 위험 | 잘못된 정책 + AOD/감소 true→PolicyRejected, deliveredIntent null. 기존 계약대로; 소비자 안전 보호 및 마지막 유효 정책 필요. |
| AUD-R02-05 | P2 검증 결함 | 앞뒤 공백/내부 공백/NUL 단위 설정 모두 issues=[]/Advanced. 정책 자체 검사 강화. |
| AUD-R02-06 | P2 극한 경계 | Long.MAX_VALUE, 만료된 생략 채널 80/90 유지. TTL 보존 또는 재동기화. 현 생략 보존 계약의 한계. |
| AUD-R02-07 | P2 극한 경계 | 상한 t100 LimitReached, processedAt t0 유지. 전달 sequence 및 watermark 계약. |
| AUD-R02-08 | P2 검증 결함 | 공개 gateDouble NaN min/max→Fresh(999). 정상 step 정책 검증과 구분. 직접 함수 인자 검증. |
| AUD-R02-09 | P2 계약 위험 | generic List 승인 후 호출자 변조 [1]→[1,2]. 불변 값/복사 계약. 기존 primitive 데이터 결함 증거 없음. |
| AUD-R02-10/11 | 정책 재검토 | 충전/LOW 확정 대기에서 10→17%에 그래픽 제한 해제. 현 정책대로, 확정 LOW hysteresis 별개. |
| AUD-R02-12 | P2 재현성 결함 | exact .gitattributes blob 821a2452e77fe42e947db1aec86f1c42475346c6 및 palette blob 602a6a9601920f30ecb87d2bd4d2ae8430d564c6. 임시 Git core.autocrlf=true에서 1309→1329 B, 20 CRLF, 원본 불일치. 생성 경로 LF 규칙 실험은 원본 유지. 실제 Windows 전체 수정/재검증 NOT RUN. |
AUD-R01-06 실제 원본 checker blob 99fa3716c09e11a3770d7e8e02eb48359e0671e9. 정상/명시적 실패/이전 시각 대조 3/3 맞음. missing classname, empty method, unrelated class/method, missing counters, wrong suite filename, nested testcase, future timestamp 7/7 수용. 미래 상한은 추가 제안. 기존 시험 결과 조작 증거 없음. 로컬 재현 코드/로그 ZIP 사용자 제공.
기존 100000 전이 시험 단언 확인: 시간/우선순위/revision/유한성/모션/AOD 보호. 신규 조합을 모두 보증하지 않음. 같은 processedAt 소비자는 호출 순서 보장 필요(기존 GB02-R05-ASYNC). 정상 대조: 실제 0, exact TTL boundary, NaN reject, critical priority, old AOD protection, domain revision reject/duplicate, opt-in timestamp gate PASS. 
G0 읽기 검증, G1 계약 및 G2 검사기 결함 확인, G3 실제 신규/기존 CI 실행, G4 데이터 경계 결과, G5 GB 코드 별도 검토 및 자기 재검토 구분, G6 artifact 대조, G7 본 문서/중앙 기록. 전체 감사 PARTIAL, 출시 NO-GO, 두 외부 PR HOLD. 실기기/실제 공급원/서비스 연결 미실행. 다음 R03 그래픽/모션/AG-01 소스 및 검증기 감사. GPT-07 착수 금지. 감사 브랜치 병합 금지. 수정 작업은 전체 감사 후 소유권에 맞춰 계획.