# 전체 중간 감사 R01 — 증거 요약
2026-11-28 KST, main 1e5e4b14e0414c66cc38fec582eac2f28c3ad5f7. 실제 main CI 46084484983 job 140790734055 316 PASS/0 FAIL/0 SKIP. doc CI 46084484927 SUCCESS. 실제 소재 artifact 15238137808 114699 B SHA256 6dbd09c5f8d60bdbb16675455a4fc5e6ea66c5fb2167b0d8b857544615837101, 직접 다운로드 및 ZIP/APK SHA/CRC/리소스 일치, 실행 코드 없음. 175x58 RGBA 40600 B, 대비 5.815240, 60개 눈금 서로 다른 위치, 2160/2160 보수적 기하 검사, 공식 메모리 2412312/3181712 B. 실기기 NOT RUN. 
| ID | 등급 | 증거/해결 조건 |
|---|---|---|
| AUD-R01-01 | P1 | main protected=false; required checks off; rulesets=[]; 상세 API 403. 보호 설정 사용자 승인/권한 필요. |
| AUD-R01-02 | P1 | signature_material.check_face에 중복 눈금, 링 숨김, 중앙 침범, Arc 각도, 색상, Template tail 변경 주입 6/6 수용. 실제 APK 정상 별도 확인. 토큰/속성/텍스트 전체 비교 및 음성 회귀. |
| AUD-R01-03 | P2 | check_domain_results.py에 무관한 클래스 81개 시험 주입, 정상 수량으로 승인. 필수 식별자 및 직접 child 검증. |
| AUD-R01-04 | P2 | verify_wff 음성 검증에서 실행 실패와 명시적 schema 거부 구분 부족. 정적 확인. |
| AUD-R01-05 | P2 | domain-kotlin CI paths에 검사기 경로 누락. 설정 확인. |
| AUD-R01-06 | P2 | GB-02 JUnit 검사기 식별자/카운터 검증 부족. R02에서 실제 재현. |
| AUD-R01-07 | P2 | 일부 Actions 버전 태그 이동 가능, commit pin 미고정. 침해 증거 없음. |
GB-02 R05 원본 16 XML 중 10개 115건 확인; R02에서 잔여 검사 및 clean CI 완료. AG R07 원시 로그 38 PASS, 제출 60 schema/6 APK, runtime NOT RUN. PR #2/#3 HOLD. Bootstrap 리소스 아직 초기 상태, 실제 AOD 날짜와 그래픽 승격 미완료. R01 로컬 상세 보고 및 재현 ZIP 사용자에게 제공; R01 당시 호출 한도로 저장소 미기록이므로 이번 문서에 추적 요약 보존. R02 및 R03 후속 감사. 제품 코드 변경 없음.