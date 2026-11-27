# 프로젝트 상태
기준일: 2026-11-27
- 설계 기준선 v1.0: 문서 작성.
- 구현: 초기 빌드 토대만 작성; 제품 기능 개발 미완료.
- 활성 작업: WO-01 (PARTIAL; CI와 공식 환경 확인 진행).
- 다음 작업: WO-02 (WO-01 판정 이후).
- CI 첫 실행: Wrapper 무결성 및 프로젝트 구조 PASS; SDK 도구 미설치 FAIL; 후속 시험 SKIP. 수정 후 재검증 필요.
- 설계 착수: GO. 제품 출시: NO-GO.
- 실제 Watch7 크기, OS, WFF 지원, 신형 기기별 설치 및 실기기 접근: 미확인.
- 최신 SDK/도구 버전, 라이선스, 패키지 ID·배포 방식: 미확정.
- AOD 연속성, Reference 제어, 숫자 morph, Samsung Health 독점 지표, Watch Face Push: PoC 필요.

설계 문서의 기능은 구현 목표다. 완료 증거가 없는 기능을 출시 기능으로 표시하지 않는다.

## Bootstrap implementation (2026-11-27)
- Resource-only Android project and WFF 2/3/4 debug variants created; shared minimal WFF face.
- WO-01 PARTIAL: local Android SDK/Gradle/ADB not available; device and Samsung model matrix verification pending.
- WO-02/04 bootstrap only, no formal completion. WFF5 remains disabled pending confirmed SDK/toolchain.
- CI configured for official validator, APK assembly and payload inspection. Check actual workflow results; no PASS assumed.
- Premium design and motion, external data, services, companion, memory and physical-device tests remain pending.
- Product release NO-GO.
