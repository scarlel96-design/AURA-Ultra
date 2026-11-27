# GPT 선행 개발 실행 계획
정본 로드맵: ../ROADMAP.md (38 WO). 현재 실행 위치: ../STATUS.md. 운영 규정: RESUME_PROTOCOL.md.
목표는 Codex 투입 전 안전하게 작성·검증할 수 있는 코드, 테스트, 문서를 최대한 확보하는 것이다. 65% 작업량 목표, 조건부 상한 75%는 추정치다. 완료율이나 보장 수치가 아니다.

| GPT ID | WO 연계 | 작업 | 필수 산출물/종료 조건 | 남길 검증 |
|---|---|---|---|---|
| GPT-01 | 01,02,04 | 초기 APK/CI 안정화 | 실패 APK 항목 식별, 공식 리소스 전용 패키징 수정, WFF2/3/4 스키마·빌드·내용 검사·Artifact 확인, 메모리 평가 통합 후보 | 실기기 설치 |
| GPT-02 | 01~04,08 | 버전·환경·모듈 기반 | 도구/기기/API 매트릭스, SDK 및 flavor 정책, 빌드 분리, WFF5 공식 검증 또는 차단 등록, 패키지 ID ADR | WFF5 실기기 |
| GPT-03 | 09,10 | 그래픽 자동 생성 | 토큰 파서, 원본/생성 분리, 결정적 WFF 및 국소 자산 생성, 자산 해시·검증·단위 시험 | 실기기 소재 |
| GPT-04 | 03,04,09,16 | 공통 레이아웃 | 원형 안전 영역, 글꼴·데이터 텍스트, 시각 프리뷰, 날짜·배터리·걸음·심박·날씨 기초 표시, 오류 표시, 스크린샷 검사 | 실제 가독성 |
| GPT-05 | 05,07,14,15 | 연속 모션 PoC | WFF4 Variant, Reference, 변환·숫자·이벤트 트리거 검증, 하위 대체안, 버전별 validator | 실제 전환 영상 |
| GPT-06 | 06,11~16,30 | 소재 및 그래픽 | 원본 금속·유리·광원·깊이 레이어, 지원되는 시차·기상 모션, Signature 초기 구성, 메모리 검사 | 최종 시각 품질·센서 |
| GPT-07 | 17~23 | 도메인 기반 | Kotlin 순수 데이터 계약, FSM·히스테리시스, 품질 정책, TTL, 오류 모델, 캐시 인터페이스 및 단위 시험 | 센서·통합 |
| GPT-08 | 18,19,23 | 기상/강수 | KMA/Open-Meteo adapter, 합성 응답, 단위·시간 정규화, 관측/예측 분리, fallback·백오프·캐시·테스트 | 실제 API 키 및 계정 |
| GPT-09 | 07,17,20~23 | 건강·배터리·컴플리케이션 | 공식 SDK adapter, 권한 상태, provider, Reference 전달 계약, Data Layer 기반, 테스트 | 실제 건강 데이터·기기 |
| GPT-10 | 16,22,24,25,30 | 8개 테마 | 개별 소재/구조/모션/고대비/AOD, 모든 프로필 빌드 및 회귀 | 실제 시각 승인 |
| GPT-11 | 26~29 | Wear 및 Mobile Studio | Compose 상세/설정/프리셋/미리보기 기반, 동기화 계약, 공식 Push 검토, 테스트 | 실제 앱 연결·설치 |
| GPT-12 | 30~38 | 통합 검증 및 인수인계 | CI·회귀·보안/의존성·메모리·진단 자동화, 기기 시험 스크립트·리포트, 남은 문제 인계 | 전력·발열·최종 출시 |

## 순서 및 범위
기본적으로 ID 순서로 진행한다. 단, 앞 작업이 외부 입력에 막히면 의존성이 없는 하위 작업을 먼저 수행한다. 실제 기기 없이 가능한 검증과 기기가 필요한 검증을 분리한다. 누적 목표 비율을 달성하려고 불안정한 코드를 추가하지 않는다.
GPT-01~03 GO(개발 기반). GPT-04 PARTIAL; GPT-05 독립 준비 PARTIAL. GB-01 통합 완료; GB-02 독립 준비 가능. 다음 실행 명세 GPT-04.md를 참조한다. 실제 상태는 STATUS.md가 정본이다.
GPT-02~12는 사전 범위다. 시작 직전에 관련 실제 코드·공식 API·의존성을 확인하여 상세 WO 또는 GPT 작업 명세를 작성한다. 무효화된 과거 계획을 그대로 실행하지 않는다.
사용자가 "다음 작업"이라고 하면 위 표와 STATUS, BLOCKERS에 따라 안전한 작업을 선정한다. 순서 변경은 근거와 선행 조건을 WORK_LOG에 남긴다.


## GPT-05 R01 — independent M01 motion preparation (2026-11-28 KST)
- Main 78879e9eda866da779c8bd558bfb8db56fcf8b4f, [combined CI 46070824245](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46070824245), job 140747074767, IN_PROGRESS at latest check. Host regression, layout/asset reproduction, invariants, official WFF validation, baseline APK assemble/content/memory/signature steps SUCCESS; isolated flavor/Signature and artifacts pending at observation. Do not mark GPT-04 complete. Candidate R11 CI 46070098373 verified previously. GPT-04 remains PARTIAL pending combined evidence and actual rendering/adoption.
- Independent GPT-05 candidate bb0712fefb982e7a8c0893b9707d3eaa4ad9fb12, branch gpt-05-motion-contract, [CI 46071034201](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46071034201) queued when checked. Five changed paths: design-system/motion/m01-draft.json, tools/motion_contract.py, tests/unit/test_motion_contract.py, docs/operations/GPT-05.md, docs/evidence/GPT-05/REPORT-01.md. No product, AG/GB or workflow changes. R-06/07/10/11/20/22/25, WO-05/07/14/15 preparation only. Preserve five documented M01 windows. Host rational smoothstep, panel/secondary inset expansion and alpha, fixed core reserved regions, round geometry projection, exact reverse positions, static lower-profile/reduced-motion fallback. 13 new test methods (expected 176 total). Planned 4004 geometry checks and 1001 reverse comparisons; actual results pending. CLI MOTION_RESULT is not yet a dedicated CI step; discovered unit test asserts audit counts. No runtime/WFF easing equivalence, derivative continuity, glyph/conditional marker rendering, ring/material geometry, actual center-to-active time movement, frame rate, lit pixels or power claim. Fixed core draft is a documented R01 assumption, not a replacement for MOTION_SPEC or final design. No new dependency. G0 PASS, G1 implemented, G2/G3/G4/G6 pending, G5 self-review, G7 remote refs/diff/records. Preserve existing blockers including B-005, AG01-AUD-04 follow-up and GB-02 integration hold. GPT-04/GPT-05 PARTIAL, GPT 3/12, WO GO 0/38, release NO-GO. Next verify both runs, exact SHA, all required steps/logs, 13 new methods, 176 full host, APK/bundle hash matching, and input count (candidate adds two tracked build-input paths); integrate only after success. Actual AVD/device work NOT RUN; no download/install/distribution.


## GPT-06 R01 — material foundation checkpoint
- GPT-05 R07 integrated e430ef26bc3b9f281c94c67927bc2698d380b01b, exact two tested blobs verified, combined CI 46075293496 IN_PROGRESS at observation. New candidate 66364c51b69d597d1640bb23a8a88c8a058ba7bd, branch gpt-06-material-foundation, CI 46075399378 IN_PROGRESS. Five changed paths: design-system/materials/signature-material-draft.json, tools/material_foundation.py, tests/unit/test_material_foundation.py, docs/operations/GPT-06.md, docs/evidence/GPT-06/REPORT-01.md. Confirmed 12 test methods, expected 258 host tests, actual execution pending. 12 cropped RGBA PNGs at four diameters, deterministic integer grain and illumination, rounded mask, dark glass approximation, bounded optical highlight. Per-diameter one-copy RGBA draft allocation <=100000 bytes, no selected material assets in AOD. No product packaging, live optics, actual visual acceptance, official material memory measurement, sensor or power claims. New procedural assets require no external dependencies. G2/G3/G4/G6 PENDING, G5 self-review, G7 records. Next check exact R07 integration and R01 candidate CI (246/258 host), MATERIAL_RESULT 12 assets with hashes and budgets, all previous gates; integrate only on full success. GPT-04/05/06 PARTIAL; GPT 3/12, WO GO 0/38, release NO-GO. AG R06 submission remains HOLD pending independent review; GB HOLD unchanged.
- User stop gate: after GPT-06 is complete, report results and stop before GPT-07. No automatic GPT-07 start until further user instruction. This applies to all subsequent resume turns; report remaining external verification if GPT-06 cannot reach GO. 
