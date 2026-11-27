# GPT-06 — Material & Optical independent preparation
Status: PARTIAL. R-05/08/09/10/11/20/22/25, WO-06/11/12/13/16/30 preparation. WO-04/09/10 not GO. P04/05/06 actual device NOT RUN. Preserve Signature layout and premium objective. No WFF XML, renderer API or external agent paths changed.
## R01 material foundation
Use design-system/materials/signature-material-draft.json. Fix a shared upper-left 45-degree light. Generate cropped RGBA PNG swatches for brushed titanium, simulated dark glass and local optical streak at 432/438/480/498. Use integer directional illumination, deterministic horizontal grain, bevel and 4x4 corner coverage. Glass is a baked lens approximation, not actual refraction. The highlight alpha has a bounded envelope. Keep RGB zero at fully transparent pixels. No external assets or libraries. Original artwork is procedural; no third-party material copied.
Draft logical sizes 120x32, 158x52, 80x12. Asset sizes round upward. Limit summed one-copy decoded RGBA to 100000 bytes for these three assets per diameter. This is an incremental draft budget, not official memory evaluation or total runtime memory. AOD selects none; Eco omits the highlight. Actual composition, text contrast, optical quality, density and package memory are not verified. Stored DEFLATE is intentionally unoptimized in R01; later evaluate compressed size. Avoid full-screen textures.
Run python tools/material_foundation.py --check; --manifest; --png 480 glass (redirect binary stdout to a new file outside product paths). No generated binary committed or packaged. Unit tests decode all 12 outputs, verify CRC, dimensions, hashes, corner/alpha, texture distinctions, policy, invalid input and independent process reproduction. Require complete candidate CI before integration. R02 refine titanium/ring geometry, R03 glass composition, R04 optical/spatial, R05 multi-resolution previews/contrast and asset budgets, R06 isolated Signature integration and regression; adjust scope only with evidence. Do not claim GPT-06 complete while required gates pending. User requires explicit stop and report when GPT-06 finishes, before any GPT-07 work; await new direction.
## R05 검증 완료
[REPORT-05-VERIFIED](../evidence/GPT-06/REPORT-05-VERIFIED.md). 통합 c4791149928ce1d90fadc31dcb7af73403e6d02f; CI 46082669709 확인 필요. R05 최소 대비 5.729308:1, 152 SVG, 36 PNG. 실제 제품 리소스 미변경.

## R06 수직 통합 (사용자 승인)
격리된 WFF2~5 실제 APK에 Signature basic 시간·정보와 검증된 유리 패널, 정밀 링을 통합한다. 공식 validator와 memory evaluator, APK 내용·리소스 참조·서명, AOD 장식 숨김, 원본 불변을 검증한다. 정적 fallback 우선. 실시간 Gyro, fluid digits, profile switching은 실제 검증 전 미구현으로 유지한다. 제품 파일 직접 덮어쓰기 및 사용자 기기 설치 금지. 생성/빌드 재현 경로, 정확한 SHA와 실제 아티팩트를 보고한다. GPT-06 준비 종료/소진 시 반드시 사용자에게 보고하고 중단한다. 제품 NO-GO 유지.

[원본 기록](https://github.com/scarlel96-design/AURA-Ultra/blob/c4791149928ce1d90fadc31dcb7af73403e6d02f/docs/operations/GPT-06.md); [archive](../archive/README.md).

R06 후보 e1a5f62abbf20cbaa6d9c741251b96d7a6caddd1; [CI](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46082882539) QUEUED; [실행 보고](https://github.com/scarlel96-design/AURA-Ultra/blob/e1a5f62abbf20cbaa6d9c741251b96d7a6caddd1/docs/evidence/GPT-06/REPORT-06-MATERIAL-APK.md). 기존 검사 단계 보존, 신규 격리 빌드·증거 업로드 단계 추가. 검증 전 통합 금지. 다음 턴 실제 CI 로그, 309 예상 시험, MATERIAL_APK_RESULT 및 네 APK의 메모리/서명/리소스 해시와 artifact 검증. 실패 시 수정·재시험. 현재 제품 NO-GO.

## R06 승격 기준 및 실기기 확인
[실기기 확인 절차와 승격 게이트](SIGNATURE_DEVICE_GATE.md)를 적용한다. 자동 검사 성공은 개발 후보 승인만 의미한다. 실기기 확인/사용자 명시 승인/실제 후보 프리뷰/롤백 및 단일 생성 경로 확보 전 main 제품 리소스 승격 금지. GPT-06 독립 준비 종료 시 미실행 실기기 항목을 명시하고 중단한다.
