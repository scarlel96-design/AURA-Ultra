# 중간 감사 통합 결함 등록부 — 기준 2026-11-28
상태: OPEN 전부(해결 증거 없음). 기준 main 3dae9dc885ebcd0091f72ee0e63ce64e9c9ada96, GB-02 122d81b05fb0fc56020fb3d03b667545eb6671c3, AG-01 fc98c3ad5993e131f733a9444b5849e737a49086.
[R01](REPORT-R01.md), [R02](REPORT-R02.md), [R03](REPORT-R03.md), [R04](REPORT-R04.md)의 40개 번호를 통합한다. R03-08=R01-04 하나만 중복 제거. R02-10/11은 두 개의 정책 검토다. 39개 = P1 12 + P2 24 + P3 1 + 정책 2. 확인된 P0는 0이며 취약점 부재를 보증하지 않는다. P1은 관련 통합/검증 GO 차단. P2/P3도 해결 또는 명시적 승인된 이관 전 종결하지 않는다. 기존 B-002~008 및 기존 agent AUD ID는 별도 유지한다. 이 등록부의 소유자는 후속 작업 제안이며 배정·실행 승인이 아니다. GB=Grok Build GB-02, DOMAIN=기존 domain 소유권에 따라 별도 승인, AG=Antigravity AG-01, GPT=ChatGPT, USER=사용자/저장소 관리자.
| 감사 ID | 우선도 | 성격 | 담당 | 묶음 | 문제 | 재검증·수용 조건 |
|---|---|---|---|---|---|---|
| AUD-R01-01 | P1 | 운영 통제 | USER | F00 | main 보호/필수 CI 미적용 | 승인된 필수 상태 검사와 직접 쓰기 제한 적용; PR 정책 및 관리자 예외 확인. 현재 보호 OFF를 유지 기록. 설정 권한/승인 필요. |
| AUD-R01-02 | P1 | 검증 결함 | GPT | F01 | Signature 검사기의 6개 결함 미검출 | 6/6 기존 변조 fixture 거부, 정상 XML/PNG 해시 보존, 기하/색/속성/텍스트 전체 비교. |
| AUD-R01-03 | P2 | 검증 결함 | GPT | F01 | Domain JUnit 시험 식별자 미검증 | 무관 클래스/메서드, 중복, 누락, 비정상 nested XML, 실패·SKIP 위조 거부; 필수 81개 시험 식별자 검사. |
| AUD-R01-04 | P2 | 검증 결함 | GPT | F01 | WFF 음성 verdict와 도구 실패 혼동 | R03-08 중복. JVM crash/timeout/잘못된 대상·버전 거부, 정상 스키마 거부만 음성 시험 PASS. |
| AUD-R01-05 | P2 | CI 누락 | GPT | F01 | Domain 검사기 변경 시 CI trigger 누락 | checker/test/wrapper 관련 수정에 workflow 실행; 필수 검사 skip 정책 검토. |
| AUD-R01-06 | P2 | 검증 결함 | GB | G01 | GB JUnit 검증기의 7개 비정상 증거 수용 | 7/7 부정 fixture 거부, 정상 72/81개 원시 XML 및 정확한 클래스·메서드 유지; 미래 시각 허용 오차 명시. |
| AUD-R01-07 | P2 | 공급망 위험 | GPT | F03 | Actions 버전 태그 미고정 | 검토한 공식 release commit SHA 고정, 버전 주석 및 갱신 정책, 동일 CI 회귀. |
| AUD-R02-01 | P1 | 계약 결함 | GB | G01 | 권한 거부/오류/누락 사유 TTL 소실 | 9개 status/TTL 조합에서 원 상태 보존 및 freshness 별도 표현, unusable 숫자 미공개. |
| AUD-R02-02 | P2 | 통합 위험 | GB | G01 | 미래 관측값 허용 | 관측 시각과 예보 유효 구간을 구분, 승인된 출처별 clock skew 정책 및 경계 회귀. 임의 허용치 확정 금지. |
| AUD-R02-03 | P1 | 통합 위험 | GB | G01 | 새 처리 시각에서 오래된 관측 재반영 | source+stream revision/watermark 적용 계약, 80→과거10 방지; timestamp/revision 충돌·재시작·동일 시각 시험. |
| AUD-R02-04 | P1 | 통합 위험 | GB | G01 | 잘못된 정책의 보호 의도 미전달 | 마지막 유효 정책 또는 안전 보호 경로 계약; PolicyRejected와 AOD/reduced 동시 입력에서 보호 유지. 실제 소비자 적용은 C01. |
| AUD-R02-05 | P2 | 검증 결함 | GB | G01 | 비정상 단위 토큰 승인 | 공백/NUL 등 비정상 단위 정책 거부; 정상 합의 토큰 및 검증 경계 유지. |
| AUD-R02-06 | P2 | 극한 경계 | GB | G01 | revision 상한에서 만료된 생략값 유지 | 보관된 TTL/만료 또는 명시 재동기화 계약; 값 만료 시 이전 숫자 미표시, overflow 금지. |
| AUD-R02-07 | P2 | 극한 경계 | GB | G01 | revision 상한 processedAt 갱신 한계 | revision과 delivery sequence/watermark 구분; 같은 revision 보호 전달 및 재정렬 시험; LimitReached 계약 변경 검토. |
| AUD-R02-08 | P2 | 검증 결함 | GB | G01 | 공개 숫자 gate NaN bound 허용 | NaN/Infinity/뒤집힌 min/max 거부, 0·경계 정상 수용. |
| AUD-R02-09 | P2 | 계약 위험 | DOMAIN | D01 | 가변 generic payload 승인 후 변경 가능 | 불변 값 계약 강제 또는 방어 복사; mutable collection 주입 재현 및 primitive 회귀. 통합된 domain 소유권 별도 승인. |
| AUD-R02-10 | POLICY | 정책 검토 | GB | G01 | 충전 중 10→17% 그래픽 제한 해제 | 충전 예외와 그래픽 hysteresis 기준을 문서·시험으로 확정; 실제 제품 임계값 확정은 실측 승인. |
| AUD-R02-11 | POLICY | 정책 검토 | GB | G01 | LOW 대기 중 10→17% 그래픽 제한 해제 | 전환 대기와 즉시 그래픽 보호 간 정책 확정; 반복 경계 입력·급격한 전력 변화 시험. |
| AUD-R02-12 | P2 | 재현성 결함 | GPT | F02 | Windows CRLF로 생성 SVG 바이트 불일치 | 생성 자산/소스의 필요한 LF 규칙 고정; core.autocrlf true/false 및 실제 Windows 전체 316+신규 시험 성공. |
| AUD-R03-01 | P1 | 통합 위험 | GPT | F04 | 역순/동일 tick 보호 요청 미반영 | GB G01과 공통 단조 sequence 및 fail-safe 계약 합의. 오래된 요청이 보호를 해제하지 못하고 새로운 보호를 잃지 않는 host 시험; runtime C01. |
| AUD-R03-02 | P2 | 검증 공백 | GPT | F01 | Fluid Digits 위조 전이 메타데이터 승인 | duration/changed/reason 및 frame/plan 관계 검사, 정상 계획과 경계·위조 fixture 회귀. |
| AUD-R03-03 | P2 | 검증 결함 | AG | A01 | PNG 구조 오류 4종 승인 | 기존 4/4 잘못된 PNG 거부, 지원 subset 명시, 정상 CRC/색상/인덱스 회귀. |
| AUD-R03-04 | P1 | 증거 위험 | AG | A01 | 별도 Lock wallpaper를 active로 오인 | 실제 dumpsys fixture 기반 user/type/section 경계, 불명확하면 UNKNOWN, 합성 오인 fixture 거부. |
| AUD-R03-05 | P1 | 사전검사 결함 | AG | A01 | Manifest 정규식 오인 | namespace-aware XML 구조, 정확한 package/minSdk/property/hasCode/금지 component/permission, APK CRC/서명 계약; 기존 2/2 오류 거부. |
| AUD-R03-06 | P1 | 증거 무결성 | AG | A01 | 파일 경쟁 시 증거 덮어쓰기 | atomic no-clobber 또는 fail-closed, 실제 임시 파일 경쟁 시험에서 기존 증거 보존. |
| AUD-R03-07 | P1 | 검증 결함 | AG | A01 | MP4 컨테이너와 디코딩 대상 불일치 | 검증/디코딩/승격 동일 불변 바이트 및 해시, 실제 ffprobe 정상 12/12와 mismatch 거부. |
| AUD-R03-09 | P1 | 자원 위험 | AG | A01 | MP4 검사 전 과도한 메모리 할당 | 산술/길이/count 상한을 allocation 전에 검사, 366 B fixture 1000/50000/250000 샘플 입력 bounded memory; 고갈 시험 금지. |
| AUD-R03-10 | P2 | 복구 위험 | AG | A01 | install 후 실패가 복구 블록 밖 | 설치 전후 state와 소유권 기록, 모든 실패 단계 mock 및 정리 계약, 기존 사용자 패키지 무단 삭제 금지. |
| AUD-R03-11 | P2 | 증거 위험 | AG | A01 | 캡처 display ID 불일치 | 지원 ID 명시 또는 정확한 binding; unsupported ID fail-closed; 실제 지원 환경 fixture. |
| AUD-R03-12 | P2 | 파일 소유권 위험 | AG | A01 | 고정 원격 영상 경로 삭제 위험 | 고유 실행별 경로 및 소유권 확인, 이전 파일·recorder 실패 시 비소유 파일 보존 mock. |
| AUD-R03-13 | P2 | 복구 증거 위험 | AG | A01 | 종료 직전 상태 재검사 누락 | 복구/정리 끝에 실제 active/interactive 재조회, 오래된 성공 snapshot 거부, 확인과 실제 복원 분리. |
| AUD-R04-01 | P2 | 검증 공백 | GPT | F01 | 소스 Manifest 검사 4종 누락 | 공통 source/compiled 정책, 4/4 부정 fixture 양쪽 거부, 기존 compiled 검사 보존. |
| AUD-R04-02 | P2 | 조건부 경로 위험 | GPT | F02 | 기존 destination symlink 경로 이탈 | 새 private destination 또는 parent no-follow 검증; 외부 sibling 파일 생성 금지, 기존 regular blob 복사 정상. |
| AUD-R04-03 | P2 | 파서 검증 공백 | GPT | F01 | profile JSON 중복 key 허용 | 중복 키 reject, 정상 4 profiles 및 기존 invalid matrix 회귀. |
| AUD-R04-04 | P2 | 출처 검증 한계 | GPT | F02 | assume-unchanged가 실제 수정 숨김 | index flags 거부 또는 신뢰 경계 명시 및 exact blob input 검사; 실제 소스 불일치 검출, 기존 committed-copy 유지. |
| AUD-R04-05 | P1 | 공급망 위험 | GPT | F03 | 전이 의존성 verification/lock 미적용 | 전체 관련 Gradle configurations/AGP/plugins/metadata inventory, 신뢰 원본 checksum·signature 검토 후 strict verification와 lock, 변조 fixture 거부. CVE/license 별도 확인. |
| AUD-R04-06 | P2 | 최소 권한 개선 | GPT | F03 | checkout credential persistence 불필요 | 읽기 전용 workflow persist-credentials:false, 기존 contents:read 유지, 쓰기 권한 확대 금지 및 실제 CI. |
| AUD-R04-07 | P2 | 격리 위험 | GPT | F02 | flavor isolation worktree 복사 | committed blob snapshot으로 일원화, untracked/변조 fixture 거부, 기존 WFF4 stale APK 음성 회귀 유지. |
| AUD-R04-08 | P3 | 문서 개선 | GPT | F04 | ADR-007/BUILD_GUIDE 현재 상태 불일치 | 현행 WFF5 포함, historical baseline 분리, 정식 배포/라이선스 미확정 유지, 문서 경로/예산 검증. |

원본 보고서의 개별 관찰과 시험 실행 결과는 위 링크가 정본이다. 정적 위험은 결함 발생 사실로 과장하지 않는다. 동일 원인 그룹의 작업을 묶되 독립 수용 조건을 제거하지 않는다. 추가 위험은 별도 ID로 등록한다.