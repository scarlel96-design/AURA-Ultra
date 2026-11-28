# MID-AUDIT — 요구사항 추적표 (R04)
2026-11-28 KST. 기준 main a70cb592a60582ae44ff9f7ad91b4d07009d8c56, AG-01 fc98c3ad5993e131f733a9444b5849e737a49086, GB-02 122d81b05fb0fc56020fb3d03b667545eb6671c3. 정본 REQUIREMENTS.md R-01~26을 빠짐없이 추적한다. 이 표는 구현 및 증거의 범위 검토다. 제품 요구사항 GO 또는 실제 완성도 백분율이 아니다. 분류: A=자동 검증된 개발 기반 또는 격리 후보, H=호스트 모델/PoC, D=설계/데이터 계약, N=실행 구현 미확인. 서로 다른 단계가 공존하면 현재 가장 구체적인 증거와 남은 제한을 함께 적는다. 모든 항목의 출시 필수 조건은 QUALITY_GATES를 유지한다.
| ID | 증거 단계 | 실제 구현/증거 | 미충족 및 다음 담당 |
|---|---|---|---|
| R-01 M | D | COMPATIBILITY.md 및 WO-01 기기 목록 | 설치된 OS/펌웨어 및 실제 기기 확인, Codex/사용자 |
| R-02 M | A | profiles.json, build_profiles.py, verify_wff.py, 4 debug APK | 설치 및 WFF별 실동작, AG/Codex |
| R-03 M | A | generate_basic_face.py 시간/날짜/요일/걸음/목표/HR/배터리/날씨 격리 후보 | 제품 Bootstrap과 후보 분리, 실기기 데이터 및 시각 승인 |
| R-04 M | D | WeatherSnapshotDraft 관측/예측 강수 필드·kind 검사; 후보 강수확률 표시 | 실제 기상 adapter와 관측/예측 단위·유효 구간, GPT-08 |
| R-05 M | A | signature_material.py, titanium_ring/liquid_crystal/optical_depth, 4 정적 소재 APK | 실제 소재와 동적 조명·입체감, 실기기 검증 |
| R-06 C | H | motion_contract/object_paths/coordinator 및 AG WFF4 continuity | P03 실제 전환 영상·재진입·fallback |
| R-07 C | H | fluid_digits, motion_events, AG motion triggers | P07/P09 실제 WFF 이벤트·지원 범위 |
| R-08 C | H | optical_depth 합성 tilt, AG Gyro fixture | P06 실제 센서와 전력 |
| R-09 M | D | DESIGN_SYSTEM 8종 정의, Signature 후보 | 독립 7개 테마 및 전 상태 시각 시험 GPT-10 |
| R-10 M | A | round_layout, signature_preview, motion geometry, 날짜 독립 후보 | 실제 glyph·밝기·잘림·런타임 및 사용자 승인 |
| R-11 M | H | host profiles, reduced motion, visual_quality high contrast; GB 정책 | 실제 품질 전환/접근성, Ultra 품질·palette 계약, 보호 순서 |
| R-12 C | H | GB-02 독립 FSM 72 PASS, domain 81 PASS, 미병합 | 공급원과 PresentationIntent 소비자 연결, 계약 결함 해결 |
| R-13 C | D | DATA_INTELLIGENCE 공급원 설계 및 Observation 계약 | 실제 Health Services/Connect/Samsung 공식 범위 및 권한 GPT-09 |
| R-14 M | D | 후보 기본 기온/날씨/강수확률; 기상 계약 초안 | 체감/최고최저/습도/바람/UV/일출일몰/예보 adapter GPT-08 |
| R-15 C | D | DATA_INTELLIGENCE 대기질/강수시각/누적량 설계 | 실제 공급원과 추정 표시 GPT-08 |
| R-16 C | D | DATA_INTELLIGENCE Data Layer/시스템 complication 설계 | 실제 폰 배터리/일정/알람/잔여시간 GPT-09/11 |
| R-17 M | H | Observation/Validation/Freshness, GB Gate, 후보 weather ERR/-- | TTL 사유 소실, 실제 권한 및 통신 장애 시험 |
| R-18 M | A | 후보 독립 시간/날짜 및 WFF 리소스 전용 구조 | 서비스 장애 주입, 실제 기기 AOD 날짜 확인 |
| R-19 C | D | MASTER_ARCHITECTURE 및 ROADMAP UI 설계 | Wear 상세 화면/Mobile Studio 미구현 GPT-11 |
| R-20 M | A | 공식 메모리 2412312/3181712 B, 4 후보 APK; host pixel checker | 실제 AOD 발광 비율, 전력·발열·전체 테마 |
| R-21 M | D | SECURITY, hasCode=false/allowBackup=false, debug signature; R04 보안 감사 | 실제 전송/저장/권한/업데이트/공급망/서명 정책 |
| R-22 M | A | committed snapshots, generators, CI, artifact hashes | Windows CRLF, dependency locking/verification, CI pins 및 검증기 강화 |
| R-23 M | N | device matrix 존재, 실제 설치 증거 없음 | 지원 주장 전 각 기기/OS 조합 시험 |
| R-24 C | D | Watch Face Push 검토 계획, B-006 | 공식 조건 및 배포 PoC GPT-11/WO-29 |
| R-25 M | A | 실제 APK resource-only 검사 및 공개 WFF/JAR 검증; R04 manifest 대조 | 전체 제품·자산 출처/라이선스·후속 앱 공식 API 감사 |
| R-26 M | H | signature_preview 합성 한영/12·24시간/누락, 조건부 AMPM | 실제 locale/font/단위/긴 문자열, 모든 테마 |
A=8 (02,03,05,10,18,20,22,25); H=7 (06,07,08,11,12,17,26); D=10 (01,04,09,13,14,15,16,19,21,24); N=1 (23). 합계 26. A는 구현 일부 또는 자동 검증 증거일 뿐 요구사항 완료가 아니다. M/C 원본 우선도 유지. WO 0/38 GO, GPT 3/12 GO, 제품 NO-GO. P01~15의 실기기 증거는 아직 승인되지 않았으며 P11 host 시험과 P12 schema/build만 제품 런타임 증거와 분리한다.