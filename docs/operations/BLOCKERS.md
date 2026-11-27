# 차단점 및 불확실성 등록부
OPEN은 미해결, BLOCKED는 외부 조건 필요, RESOLVED는 해결 증거가 있는 상태다. 기록을 삭제하지 않는다. 해결 시 검증 SHA와 증거를 추가한다.

| ID | 상태 / 우선도 | 내용 및 증거 | 해결 조건 | 담당 |
|---|---|---|---|---|
| B-001 | RESOLVED | 과거 WFF2 APK classes.dex 및 AGP 생성 R 클래스 5개 재현, 현행 3 APK 리소스 전용 검사 PASS | CI 46000111676/46000111754; REPORT-02 | GPT-01 |
| B-002 | BLOCKED / P1 | 현재 채팅 환경에 Android SDK/ADB 및 연결된 워치 없음 | CI로 대체 가능한 검증 수행; 실제 설치·센서·전력 시험은 접근 가능한 환경에서 수행 | GPT / Codex / 사용자 |
| B-003 | OPEN / P1 (SDK/빌드 해결) | CI 46002470824 SDK37.0 및 WFF5 Debug APK PASS. WFF5 실제 설치·런타임·전용 기능 미확인 | 실제 기기 및 P12 PoC 증거 | WO-08/35 |
| B-004 | OPEN / P1 | Watch7 크기/펌웨어/OS 및 최신 Samsung 기기 공식 매트릭스 미확인 | 공식 사양 확인, 실제 지원 대상별 기기/OS 기록 | WO-01 / 34 / 35 |
| B-005 | OPEN / P1 | WFF4 Reference, Variant, 숫자 전환, Gyro, 모션 트리거 및 최종 그래픽 품질 미검증 | P03~09의 실제 증거 | GPT-05/06 / Codex |
| B-006 | OPEN / P2 | 실제 KMA API 자격·할당량, Samsung Health 권한/파트너 및 독점 지표, Watch Face Push 조건 미확정 | 공식 조건 확인 및 실제 승인된 환경 시험 | GPT-08/09/11 |
| B-007 | OPEN / P1 | 정식 패키지 ID, 라이선스, 서명/배포 정책 미확정 | ADR 및 필요한 사용자 승인 | WO-29/38 |
| B-008 | OPEN / P2 | 전력/발열/실기기 소재 및 접근성 승인 미확보 | 비교 시험, 영상, 측정 및 사용자 승인 | WO-30~38 |
| B-009 | RESOLVED | CI 45997002132 SDK manager not found (exit 127) | CI 45997124733 SDK 설치·확인 PASS | 수정 544a7010 |

| B-010 | RESOLVED | tools/verify_wff.py의 성공 조건이 일반 VALID 포함 여부에 의존한다. 헤더 Validation도 매치되므로 명시적 성공을 검증하지 못할 위험. 실제 두 CI의 성공 로그는 버전별 PASSED를 확인했다. 오판 발생 자체는 미재현. | 공식 validator 결과 형식 확인, 성공·실패·불명확·버전 불일치 회귀 시험, 대상별 명시적 성공 검사 | GPT-01 |

B-001 해결 확인. 재발 시 관련 통합 작업의 GO를 중단한다. 독립 테스트·설계·도메인 작업은 RESUME_PROTOCOL의 선행 조건에 따라 진행 가능하다.

## 운영 점검 기록 (2026-11-27)
문서 기준 SHA 951593e4fbbac33f2c675ea5cbbf07edbe22353d, CI 45998609726 (completed/failure): Official WFF validation: success; Build debug APKs: success; Check APK contents: failure; Upload debug APKs: skipped. https://github.com/scarlel96-design/AURA-Ultra/actions/runs/45998609726. 운영 문서 변경 실행이며 제품 코드 변경 없음. B-001/B-010 해결 증거 없음.
신규 제품 차단점 없음. 기존 차단점은 해결되지 않았다. 매 턴 PRE-FLIGHT에서 최신 증거를 다시 확인한다.

## GPT-01 회차 01 수정 후보
B-001: CI 45998909046, job 140505251267에서 DEX build/merge 작업 및 APK FAIL 재확인. 정확한 이전 ZIP 항목은 미확인. Samsung 공식 WFF 가이드의 minify 활성화/resource shrink 비활성화 적용. 검사기는 모든 APK의 정확한 항목과 컴파일된 Manifest를 기록한다. 새 CI 검증 대기.
B-010: 명시적 파일/버전 PASSED 판정, 오류/종료 코드/중복 검사, 정상·실패 fixture 및 실제 잘못된 XML probe 추가. 새 CI 검증 대기. 두 차단점은 OPEN 유지.

- GPT-01 코드 SHA ef9f9c9bbb2020de835926a3bf0e4262b9c89d51, CI 45999371709: completed/success. 실제 최종 로그/Artifact 확인 전 B-001/B-010 OPEN 유지. STATUS의 단계별 결과 참조.

## GPT-01 회차 01 최종 증거
코드 ef9f9c9bbb2020de835926a3bf0e4262b9c89d51, CI 45999371709: 19 단위 시험 PASS, 공식 WFF 정상 3/3 및 잘못된 XML 명시적 실패 검출 3/3 PASS, 3 APK clean build/내용 검사 PASS, Artifact 15197113871 확보. B-010 해결, B-001 현재 빌드 실패 해소 및 과거 원인 증거만 보완 필요. REPORT-01 최종 결과 참조.

## GPT-01 회차 02 후보
B-001 과거 95e51cc 격리 재현 job 추가. 실행 결과 미확인. B-010 해결 유지. 메모리 및 debug 서명 검사 새 CI 대기. 실제 기기 접근 차단 B-002 유지.

- 회차 02 검증 코드 98a4f915577cf3175beeca19864a431061673e7b, CI 46000111754/46000111676. 메모리·서명·격리 재현 최종 증거 확인 전 B-001 OPEN. B-010 RESOLVED 유지. STATUS 참조.

## GPT-01 회차 02 최종 확인
B-001 RESOLVED: 과거 SHA 격리 재현 classes.dex 및 R 클래스 5개 확인, 현행 3개 APK 검사 PASS. B-010 RESOLVED 유지. 현행 메모리 2,371,712 bytes 활성/AOD, 3 Debug 서명 PASS. CI 46000111754/46000111676 SUCCESS. B-002/003/004/007 등 기존 실기기·WFF5·기기/배포 정책 차단점은 유지. 새 결함 없음.

## GPT-02 회차 01
B-003: 공식 WFF5 공개 및 Wear OS7/API37 확인, AGP9.1.1/Gradle9.3.1 전환 후보. 기존 SDK36 환경 유지. WFF5 schema-only 후보, SDK37 실제 빌드/설치 미확인. B-004: Watch7/8/9/Ultra2 공식 발표 해상도/출시 OS 확인. Ultra 2025 출고 OS 및 실제 설치 OS/기기 시험 미확정. B-007: ADR-007 제안, 정식 정책 승인 필요. B-002 유지. 새 CI 결과 미확인.

- 회차 01 CI 46001149417 in_progress/PENDING. B-003/004/007/002 유지. WFF5 스키마와 API37 toolchain·실기기 시험은 분리한다.

## GPT-02 회차 01 최종
CI 46001149417 SUCCESS, WFF5 스키마 정상 및 예상 실패 검출 PASS. B-003 OPEN: API37 toolchain/실제 WFF5 APK·설치 미확인. B-004 OPEN: 공식 주요 모델 사양 확인, 실제 OS/Ultra2025 출고 OS 미확정. B-007 OPEN: ADR-007 정식 정책 제안 상태. B-002 유지. 기존 B-001/B-010 해결 유지.

GPT-02 회차 02: B-003 API37 전환 후보 격리 검증 중. 스키마 PASS만으로 설치 지원을 주장하지 않는다. B-002/004/007 유지. B-001/010 해결 상태 유지; 회귀 검사 수행 예정.

## GPT-02 회차 02 최종
B-003: SDK 패키지 android-37.0 설치, 네 APK build/스키마/메모리/서명 PASS. 도구 전환 차단 해결. 실제 설치·기능 확인은 남음. B-002/004/007 유지. B-001/010 재발 없음. CI 46002470824, REPORT-02. 첫 CI 46002330942 실패도 보존.

GPT-03 회차 01 후보 CI 46006560829 진행 중. 기존 차단점 유지, 신규 결함 확정 없음. 실제 flavor override 및 독립 생성 프로세스 시험 후속. REPORT-01 참조.

외부 작업 접수: GB-01은 독립 재실행·통합 전 검토 보완 필요. 비ASCII Windows Gradle 테스트 워커 ClassNotFoundException은 환경 제한 GB01-E1, 제품 차단 추가 아님. AG-01 원격 SHA 미확인; push 후 증거 확인. B-002/003/004/005/006/007/008 유지. GPT-03 후보 CI 성공, main 통합 및 재생성/override 시험 남음.

2026-11-28 OPS-05: GB01-D2/D3 수정 코드 및 JUnit 81건 증거 확인. 독립 CI 46056345699 진행. GB01-E1 비ASCII Windows 제한 유지. AG 원격 접근 해소; AG01-AUD-01/02/03의 증거 및 검사기 보완, 실제 Wear runtime NOT RUN. B-002/003/005 유지. 4분할 시계 자체가 아니라 가시 PartText 추가 layer 810000 bytes (공식 평가기 조건). B-001/010 해결 유지. GPT03/GB01 통합 CI 46056345651/46056345699 확인 후 판정.


## OPS-05 독립 CI 최종 및 공식 도구 갱신 후보
- 통합 코드 c6ae81217641dda75b7b3e3fbc0063fd11469c6c: Kotlin CI [46056345699](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46056345699), job 140699646163, SUCCESS. 로그 JDK17 Eclipse Temurin, BUILD SUCCESSFUL in 50s, DOMAIN_RESULT 81 PASS / 0 FAIL / 0 ERROR / 0 SKIP. Artifact [15226378043](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46056345699/artifacts/15226378043), 5180 bytes, digest sha256:a3fec194673e455f63b3a12103ea24c00b20d294ab6a227b6628644d47c5320f, expired=false. 메타데이터 확인, 재다운로드/재해시 미실시. GB-01 독립 CI PASS; main 통합은 아래 공통 게이트 실패로 보류.
- Bootstrap [46056345651](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46056345651), job 140699646086, FAILURE. 독립 프로세스 --write/--check/missing/stale/repair/byte equality PASS, host 68 PASS/0 FAIL, SDK PASS. 공식 validator 단계 'Validator download size or digest mismatch. Review the official release before updating the pin.' exit 1. 이후 schema/build/APK/memory/signature/Artifact SKIP. 실제 스키마 위반으로 판정하지 않는다.
- B-011 OPEN/P0: 공식 Google watchface 가변 release 태그에서 JAR 두 개 교체. 공식 [release](https://github.com/google/watchface/releases/tag/release) ID 460768397 published 2026-11-27T15:21:34Z, tag commit 18d3844de1729f0c5128f59cfa359b0e34b66612. [PR 118](https://github.com/google/watchface/pull/118)의 XML DOM parser 설정 통합 변경 파일 및 핵심 diff 확인. validator asset 800984124 SHA256 6ef308dbc306a9187b5b1f4997a662eb57e26ac3650cebbf2ab583cd38bb609e; memory asset 800984064 SHA256 1ec683365aee86627f0eb502b52fc71f71eff1872776edc5bc6ef7c7b37d28bc. 이전 공식 pin과 다름. 공식 release API 메타데이터를 확인했으며 독립 바이너리/소스 재현은 하지 않았다. 정확한 해시 검증을 유지한 새 pin 후보 0cec62250a2dc05cd02773f6969726867946fe4f를 integration/gpt03-gb01에만 반영. 기존 main과 에이전트 증거의 이전 pin은 보존. 도구 실행 버전, 출력, 정상/실패 schema 및 4 APK/메모리/서명 전체 성공 전 병합 금지.
- 신규 후보 CI: AURA Bootstrap 46056609237 in_progress/PENDING. 최종 원본 로그 미확인. Kotlin 소스는 c6ae812와 동일; 새 SHA에서 도메인 재실행 여부 구분. AG-01-R03은 현재 자기 브랜치의 고정 도구를 사용하며 새 도구 전환은 중앙 승인 이후. B-011 해결은 후보 전체 게이트 및 SHA 대조 후 판정. GPT-03 PARTIAL/GB-01 독립 CI PASS/AG-01 PARTIAL, 정식 WO 0/38, 출시 NO-GO.

B-011 RESOLVED(현재 도구 버전): CI 46056609237 공식 validator 및 evaluator 신규 pin, 4 APK 전체 PASS. 가변 release에 따른 재발 가능성은 남는다. 이전 실패 로그 유지. GB01-E1 및 AG01-AUD 항목 유지. 실제 Wear OS runtime 미실시.

GPT-03 회차 02: B-011 현재 pin 해결 유지, main GB01 독립 CI 81 PASS 재확인. 격리 flavor 후보 CI 46059190750 및 main CI 46059108841 진행/최종 확인 대기. 향후 실제 제품 override 도입 전 현재 common-only fixture를 일반화한다. B-002/003/004/005/006/007/008 및 GB01-E1 유지. AG-01 소유권 유지, PR #2 미병합.

GPT-03 회차 03: CI 46059190750 SUCCESS, 격리 source precedence 및 stale APK 검출·복원 PASS. B-011 해결 유지. 기존 실기기/외부 데이터/정식 배포 차단 유지. 제품 override 확장 전 fixture 일반화.

GPT-04 회차 01: 정적 원형 기하 4화면 PASS; 후보 전체 CI 46059943214 최종 확인 대기. 신규 확정 제품 결함 없음. 실제 글리프/렌더링/해상도 검증은 B-002/004/008 유지. GB-02/AG-01 변경 없음.

GPT-04 회차 01 전체 CI 성공; 기하 후보 통합 승인. 기존 실기기·글리프·공급원 차단 유지.

GPT-04 회차 02: 124/124 합성 호스트 글꼴 조합 fit; 기기 font/실제 표시 및 locale·native HR/날씨 runtime 미실시, 기존 B-002/004/006/008 유지. 후보 전체 CI 46060479503 최종 확인 대기. AG/GB 소유권 및 기존 main 제품 유지.

OPS-06: GPT04-D1 OPEN/P0 후보 Group name 필수 속성 누락(46060479503), 수정 374dec9 재검증 CI 46062170635. AG01-AUD-04 OPEN/P1 runtime package/display 오판 4종 분리 함수 재현. AG 원격 환경 0 Wear AVD, 실제 실행 NOT RUN. AG 기존 pin CI 실패; main pin 해결 유지. GB-01 통합 완료, GB-02 READY.

GPT04-D1 RESOLVED: CI 46062170635 SUCCESS, 100 host and 12 APK PASS. Runtime/locale/glyph/AOD pixel verification still pending. No product or external owner edits.

GPT04-D2 OPEN/P0(후보 검증): 초기 프리뷰 46064026867 실패, percent regex 수정 82fef7c, CI 46064080195 재검증 중. 실제 기기/AMPM/글꼴 검증 미실시 유지. GPT04-D1 해결 유지. 외부 소유권 및 기존 product 변경 없음.

GPT04-D2 RESOLVED: CI 46064080195 SUCCESS, 120 host/12 APK and 40 synthetic preview outputs. Runtime blockers unchanged. Official IS_24_HOUR_MODE WFF1 identified, marker implementation pending.

GPT-04 R05: 공식 12/24시간 설정 표현식 확인 및 조건부 AM/PM 후보 구현. 4해상도 기하 PASS. 전체 CI 46065067806 최종 확인 대기. 실제 렌더링/글리프/발광/설정 변경 시험 미실시. GPT04-D1/D2 해결 유지. 외부 소유 경로 변경 없음.


## GPT-04 회차 06 — R05 최종 검증 및 통합 (2026-11-28 KST)
기준 main 50937487e790323daf947d5a6b10b912302d635c; 검증 후보 2fe3551d3279630a86571df3b6f6eee499027ee5. [main CI 46064940883](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46064940883) job 140727869837 SUCCESS (120 host); [candidate CI 46065067806](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46065067806) job 140728287603 SUCCESS (129 host, 0 FAIL). 양쪽 12 APK clean build, WFF2~5 정상/오류 fixture, APK contents/memory/signature, 40 SVG + manifest 독립 재생성 41/41 hash 일치. Candidate manifest 4a7a643654cd4e46374a3c0ce80e18547abb6c954bc7c4f03a62fbc7c170cdcd; XML 4bbe6db1a6a215538ea8e0d37509c35132845ad845a0fb42efb78c19f8f11313; Signature 4 profiles active 2371712 B / ambient 3181712 B. Asset estimator only. Evidence artifact 15229529952, digest sha256:6c2cf13d76b122b62a887d2d35fc4ba588eae2c38a8958303609c5edef4044b3; bootstrap artifact 15230945190, digest sha256:9c26e96b97f6f391ea6d23095e428619230ea8adb0a31794d4f9d627833a6111. Both unexpired; download/re-hash NOT RUN. Reviewed actual candidate diff and main divergence (only central documents), preserve R05 report checkpoint on main. Integrate nine validated generator/layout/test/document paths; product apps/watchface and GB/AG owner paths unchanged. New integrated SHA CI pending. GPT-04 PARTIAL, GPT 3/12, WO GO 0/38, release NO-GO. Runtime locale/setting/actual glyph/lit pixels/power NOT RUN. Next: confirm integrated CI, prepare host-only screenshot validation with strict dimension/black background/ambient lit-pixel metrics and negative fixtures, then isolated development package. Do not change AG runtime tools or production face; do not install on user watch.


## GPT-04 회차 07 — 스크린샷 검사 후보 (2026-11-28 KST)
- 기준 main fec5b13b8691dfc1f3cbfd94408a1f713ec6c2d8. 통합 CI [46067172820](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46067172820), job 140735204703 SUCCESS. 129 host PASS, 12 APK PASS, preview 41/41 hash match, candidate XML 4bbe6db1a6a215538ea8e0d37509c35132845ad845a0fb42efb78c19f8f11313. Signature active/ambient 2371712/3181712 B. Artifact 15231112855 sha256:b4f8502f1d2659c26516c2c06dc6051eaae6aae57bbe638aa5cc82598708f690; 15231047867 sha256:729b0abfd73ddd86202b9bb32cacc4e2ecdc4f145c6dddc75967deb10505cf9a; unexpired, download NOT RUN.
- New candidate 582d74a6d4314a5d4991359b81be38bd821de72c, branch gpt-04-screenshot, [CI 46067778673](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46067778673) PENDING as last queried. Four added paths: tools/check_signature_capture.py, tests/unit/test_signature_capture.py, docs/SIGNATURE_CAPTURE.md, docs/evidence/GPT-04/REPORT-07.md. No existing test or product resource modifications. Remote branch and file list verified. 14 new unittest methods confirmed by source inspection, expected total 143; execution results not yet verified. No new dependency. Basic-only opaque RGB/RGBA PNG bounded decoder; strict original size, circle, expected region occupancy, 12/24 mode, nonblack AOD ratio <=10% using circular pixel centers. This is a project proxy, not official AOD or OLED power validation. Capture mode is supplied by operator, region occupancy is not readable text or proof of runtime provenance. Actual capture and candidate package NOT RUN/not implemented. Separate self-review: scope and code paths checked, no external agent changes; no independent reviewer. Candidate must pass full CI and negative fixtures before integration; G2/G3/G4/G6 candidate pending. GPT-04 PARTIAL, GPT 3/12, WO GO 0/38, release NO-GO. Existing runtime blockers unchanged. Next: fetch run 46067778673 job logs, verify actual host count and failure detection, resolve failure first, then integrate verified tools and prepare isolated debug evidence package. Do not distribute or install candidate APK.


## GPT-04 회차 08 — 개발용 로컬 번들 후보 (2026-11-28 KST)
- 기준 main 827a4739c3dddb9ebcb4194ef0b2cccb745d4238. R07 CI [46067778673](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46067778673), job 140737269974: in_progress, regression/SDK/schema/build/APK/memory/signature/flavor steps success 확인. 최종 Signature/Artifact 로그 및 실제 시험 개수 미확인. R07 통합 보류. 기존 기준 129 host/12 APK PASS 유지.
- 독립 준비 후보 6cbef46ec2723d609793e2f12900de423c763482, branch gpt-04-dev-package, [CI 46068112540](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46068112540) in_progress. 기존 main에서 분기하여 R07 미검증 변경에 의존하지 않는다. 실제 변경 6개: tools/signature_dev_bundle.py, tests/unit/test_signature_dev_bundle.py, tools/check_basic_face_build.py, .github/workflows/bootstrap.yml, docs/ASSET_GENERATION.md, docs/evidence/GPT-04/REPORT-08.md. 원격 브랜치/파일 목록/실제 변경 재확인. No product/AG/GB owner change. Existing test gates preserved; optional local bundle generation after all candidate APK gates. Four APK bytes and XML + canonical manifest, profile, minSdk, package IDs, source commit, hashes, byte sizes; bounded zip entry verification, missing/duplicate/tamper/no-overwrite tests. Eight added methods, expected 137 tests on independent package branch; combined 151 expected only after both branches merge and tests execute. No runtime or artifact publication. CI runner temporary output only. Existing package IDs may replace installed bootstrap; preview remains placeholder. No install. No new dependency. G0 PASS; G1 candidate; G2/G3/G4/G6 candidate pending; G5 self-review, not independent; G7 remote confirmation. GPT-04 PARTIAL, GPT 3/12, WO GO 0/38, release NO-GO. Existing B-002/003 runtime/004/005/006/007/008 unchanged. Next: query 46067778673 and 46068112540, read raw logs and artifacts; verify R07 host count and R08 DEV_BUNDLE_RESULT profile/hash/commit matches BASIC_APK_RESULT. Fix failures before integration; merge verified candidate paths only and rerun combined CI. No user-watch install or production release.


## GPT-04 회차 09 — R07/R08 최종 검증 및 통합 (2026-11-28 KST)
- Main 기준 1203bce34264bdbc8994f78cd8e247ceba92c3d6; R07 582d74a6d4314a5d4991359b81be38bd821de72c, [CI 46067778673](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46067778673) job 140737269974 SUCCESS, 143 host PASS (14 new), R08 6cbef46ec2723d609793e2f12900de423c763482, [CI 46068112540](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46068112540) job 140738250045 SUCCESS, 137 host PASS (8 new). Both 0 FAIL/0 SKIP, 12 APK clean builds, official WFF2~5 schema and negative fixtures, APK contents, memory and signatures, 40 preview outputs + manifest hash match 41/41. XML 4bbe6db1a6a215538ea8e0d37509c35132845ad845a0fb42efb78c19f8f11313; Signature four profiles active 2371712 B / ambient 3181712 B, asset estimate only.
- R08 DEV_BUNDLE_RESULT: 311014 bytes, SHA256 742c568aa3af7c86bc41643f7fa22bc8e53205469b4d5a5c88b0a725eef82f83; sourceCommit exactly 6cbef46ec2723d609793e2f12900de423c763482; XML exact; WFF2/3/4/5 manifest SHA256 matches BASIC_APK_RESULT and MEMORY_RESULT 4/4. WFF2 73458 B 0d2b6e594447a0f066d8520c8094e6b0d15d9cba008a35151b4c452249ca9890; WFF3 73458 B 659b9dd5b29c1f7f85e5cdb596a66122c33c8a527b83404285d8298c2aca5176; WFF4 73458 B cc29e995f94ec60034d350330c0e0cf56610ef552752449bbbe7d048a4437708; WFF5 73454 B 094d85884ba4b8c32d87dc56af2ebca8c1574773dbeac972cb04219389dd0024. minSdk 34/35/36/37, expected package IDs. Local bundle temporary only; separate download and rehash NOT RUN. Uploaded baseline/layout artifacts: R07 15231617312 sha256:312cf7d1fe84a760ce61d24f6c2750d11daa28d8a97b3fc5be828804ff3d6d6d and 15231418198 sha256:e118c187c17dd3b4cbb7185e95e18d59aa40d9022c1eadde36526c852fdd49ae; R08 15231204149 sha256:bec4bd8673cd4039e1e70447bc39b397e26c40a7107a440e94c9f4b351b85b50 and 15231243937 sha256:25f45844eea0bde1f2b22f403de8a848b17a2c8636873d4b8e007fbfb56c4e41; unexpired, download NOT RUN.
- Separate self-review of exact candidate diffs and main divergence: only central docs/report changes on main. Integrate eight verified blob paths, preserve full R07/R08 reports. No product XML, AG/GB owner path, external dependency or release changes. G0 PASS; G1/G2/G3/G4/G6 candidate static/build PASS; G5 self-review only; G7 verify ref and paths. Combined CI expected 151 tests, PENDING until new head logs. Existing warnings: debug minify and Node20 actions forced to Node24, no failure. Local bundle provenance limited to tracked Git worktree; untracked/ignored inputs may affect local build; hash/manifest consistency is not authentication. Use clean checkout for provenance; follow-up P2 review local input isolation and read-back verification, do not claim tamper-proof package. Actual device, locale, glyphs, AOD pixels, power, runtime NOT RUN. GPT-04 PARTIAL, GPT 3/12, WO GO 0/38, release NO-GO. Next: verify combined CI, review local input isolation; separate device-only GPT-04 gates and start independent GPT-05 preparation only after safe entry conditions. No install/distribution.


## GPT-04 회차 10 — 입력 격리 및 저장 무결성 보완 (2026-11-28 KST)
- Main a79faec6ff5ef5008b23992a540c2de4162a4091, [CI 46068687912](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46068687912), job 140740121653 SUCCESS. 151 host PASS (22 new), 0 FAIL/SKIP, 12 clean APK builds, WFF2~5 schema and negative fixtures, contents/memory/signatures PASS, 40 SVG + manifest 41/41 independent hashes. Signature XML 4bbe6db1a6a215538ea8e0d37509c35132845ad845a0fb42efb78c19f8f11313, all four profiles 2371712/3181712 B active/ambient (asset estimate). Bundle 311014 B SHA256 914760d23771b176ee9bf1e1a44f225b48cd0ba09aa78a1dbca3f0bf389ee66d; sourceCommit matches main; BASIC_APK_RESULT, MEMORY_RESULT and manifest 4/4 hashes match: wff2 e06acd7484a58f82e9fc8b2050ea604faa38176f47a48e1abdca3f34df5c6f88, wff3 7c910eaa59316a88e10885983f077f5581e7ddd36c07d8c8c3a6bd23deef5a4f, wff4 5112cda7d5426a3f0cfe4319e7035c8c7f273135435f845d841ec84606b47e44, wff5 98d3808580789ecea330cd4710efaf13f742f178ceecbec6f7cc9c022b157bc6. Artifact 15231748192 sha256:11123064368835aba22e0cd88a7deeef6f9505d77fc9ed025d6df51d7a4a98b5; 15231718243 sha256:f78f1198504248736bb0e09b4b0e9646e4f42084e1d902a2828ffb557a66a0bf; unexpired, download NOT RUN.
- R10-D1/D2 P2 candidate 4a7d097b645aaca87937eb6ff33d0c3a6a2104fb, branch gpt-04-bundle-hardening, [CI 46069370084](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46069370084) PENDING as last observed. Seven changed paths: tools/committed_build_inputs.py, tools/check_basic_face_build.py, tools/signature_dev_bundle.py, tests/unit/test_committed_build_inputs.py, tests/unit/test_signature_dev_bundle.py, docs/ASSET_GENERATION.md, docs/evidence/GPT-04/REPORT-10.md. Git blob snapshot for bundle mode only, explicit regular modes and input completeness, reject symlinks/gitlinks/case collisions, regenerate candidate from committed inputs and compare exact bytes; only pinned validator JARs copied. Flush/fsync, reopen, byte compare, stored manifest verification, no overwrite. Seven Git fixtures and three write/readback fixtures; expected 161 host total; actual new test results not yet verified. No external dependency, production/AG/GB changes or CI gate removal. Source and remote branch checked; G5 self-review, not independent. G0 PASS; G1 candidate; G2/G3/G4/G6 PENDING; G7 remote confirmation. Local build is not hermetic: SDK, environment, Gradle caches, Python and signing remain trusted external inputs. No-bundle legacy worktree copy unchanged. Private output directory required. Node20 and setup-java v4 deprecation warning remains, separate migration after official version review. Existing runtime blockers remain. GPT-04 PARTIAL, GPT 3/12, WO GO 0/38, release NO-GO. Next: inspect 46069370084 job logs, 161 host results, COMMITTED_INPUTS_RESULT exact SHA/positive count, DEV_BUNDLE_RESULT readbackVerified true and hash match 4/4; resolve failures before integration; then finalize host-only GPT-04 scope and separate GPT-05 preparation from actual device/AG evidence. No installation/distribution.


## GPT-04 회차 11 — Git fixture 실패 수정 (2026-11-28 KST)
- R10 candidate 4a7d097b645aaca87937eb6ff33d0c3a6a2104fb, CI [46069370084](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46069370084) job 140742441699 FAILURE: 161 tests, 154 PASS / 7 ERROR / 0 SKIP; all seven errors at clean_commit during fixture setup. Three new readback tests PASS. Subsequent SDK/build/schema/APK/memory/signature/artifact SKIP. Main verified baseline a79faec6ff5ef5008b23992a540c2de4162a4091 CI 46068687912 SUCCESS 151 host/12 APK unchanged.
- R11-D1 P0 candidate failure reproduced on Linux 6.18.57 x86_64, Git 2.47.3, Python 3.13.5: index-only --chmod=+x leaves file 100644, status ' M gradlew', diff mode 100755 => 100644. chmod +x restores clean state. Correct fixture only: set POSIX mode before add, Windows fixture core.filemode=false, fixture-local core.autocrlf=false, LF bytes, explicit clean assertion, two staged mutation rejection tests. No production helper or existing assertions weakened. Targeted nine tests PASS in 0.445s. Local helper Git blob c77e98077f49bbd61a62413810a967df0b516de4, corrected test blob 3d617fe4be2792e7013128a6c8b43f9ba5185709 matches remote. Windows NOT RUN.
- Candidate 716f554139a44148ad6fe496690e9b4e6b5bcabc, branch gpt-04-bundle-hardening, [CI 46070098373](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46070098373) IN_PROGRESS at last query. Two changed paths versus failed candidate: tests/unit/test_committed_build_inputs.py and docs/evidence/GPT-04/REPORT-11.md. Expected full host count 163, actual full result PENDING. G0 PASS, G1/G2 targeted PASS, G3/G4/G6 full candidate PENDING, G5 self-review, G7 ref/records. No forced update, external dependency, product or AG/GB changes. R10-D1/D2 and R11-D1 unresolved until full CI. Next: check candidate run exact SHA, full host count, 12 APK, 41/41 preview hashes, COMMITTED_INPUTS_RESULT exact SHA/count, DEV_BUNDLE_RESULT readbackVerified true and all 4 APK hashes; integrate only if all required gates pass. GPT-04 PARTIAL; 3/12 GPT, WO GO 0/38, release NO-GO. Runtime NOT RUN.
