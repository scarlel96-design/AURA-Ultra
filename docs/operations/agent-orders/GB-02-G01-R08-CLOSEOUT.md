# GB-02 G01 R08-CLOSEOUT — 최종 인계 전 경계 검증
2026-11-28 KST. R08의 제한된 보완이다. 새 R09가 아니다. 사용자 전달용. PR #3 HOLD. 제품 NO-GO.
기준 main 210f65e62bed919d4e6851ab1fb9a3e30c9146b8; GB HEAD f8dc433dd93b2c5febd0b6496e1fd729a5e09a26; 구현 671e999d668811ee402042e692bda7293bba24d2; CI head 1f6d9605b59670a3489a0a76746c857e7fc7cf99. 최신 main/PR HEAD 및 AGENTS PRE-FLIGHT를 다시 확인한다. R08 지시서와 REPORT-08, 총괄 검토, Machine.kt, Round07/08Test, 계약을 읽는다. 소유권이 충돌하지 않는 문서 변경만 GB 브랜치에 병합한다.
## 범위
modules/intelligence/**, docs/evidence/GB-02/**만 변경한다. Domain, 공통 tools/CI/Gradle, WFF, 중앙 문서 및 AG 경로는 수정하지 않는다. 기존 99 Intelligence, 81 Domain, 100000회 seeded 전이 및 JUnit 7종 부정 시험을 보존한다. 신규 기능 금지.
## P1 — 재현 우선 (정적 검토 가설)
A. 철회 커서 단조성: Machine.kt revokedCursor, decideNumber의 permission loss, orderChannel의 permission loss 및 ceilingCursor. t10 정상→t20 DENIED→늦게 전달된 t12 DENIED/ERROR/UNAVAILABLE→t15 유효 값. 처리 시각은 계속 증가시킨다. 최신 철회 이후의 오래된 숫자나 축이 재수용되는지 검사한다. 배터리·강수·충전 및 다른 축의 커서를 확인한다. 더 늦은 정상 입력은 허용한다. 철회 자체를 무시하지 않는다. 커서를 과거로 내리지 않는다. 누락/미래 시각, source A/B, 낮거나 높은 caller revision도 검사한다. revision 우선 규칙과 철회 보안 경계가 충돌하면 D01/총괄 승인 후보로 명시하고 임의로 Domain 계약을 바꾸지 않는다.
B. 잘못된 정책의 보호 watermark: t10 정상→t30 PolicyRejected에서 AOD/모션 보호 강화→t20 정상 정책 해제. 전달 순서는 증가시킨다. retainedAfterRejectedPolicy가 processedAt을 유지하는 점을 검증한다. 오래된 해제로 최신 보호가 해제되거나 폐기한 숫자가 다시 공개되는지 확인한다. 정상적으로 t40에서 해제가 가능한 대조를 둔다. 기존 legacy 계약/표시 revision을 불필요하게 변경하지 않는다. 필요하면 별도 보호/관측 watermark를 제안한다.
C. 표시 revision 상한: t10 상태 revision=Long.MAX_VALUE→t100 LimitReached(공개 변경 없음)→t50 resync 유효 관측. 이전 상태를 그대로 반환하는 경로 때문에 처리 시각 역전 검사가 우회되는지 확인한다. t100 이후의 새 resync, TTL 동시 만료, 권한 철회 및 기존 보호 유지도 대조한다. R07/R08 시험을 약화하지 않는다. 상한에서 revision을 감싸지 않는다.
## 전달 계약 최종 대조
세 축을 독립 검사한다. 새로운 세션 시작 결과보다 후속 보호 결과가 먼저 도착하는 경우, 이전 세션 지연 해제, 신뢰된 세션 성립 및 epoch 상한 fail-safe를 문서/시험과 대조한다. 실제 caller/consumer의 세션 동기화와 재전송은 F04/C01 인계 조건으로 기록한다. 실기기와 제품 소비자를 구현하지 않는다. 승인되지 않은 임계값 15/20,70/50,60초를 확정하지 않는다.
## 시험과 종료
각 가설은 수정 전 독립 fixture로 실행한다. 재현된 결함만 최소 수정한다. 재현 불가/계약 충돌은 원본 결과와 이유를 기록한다. JDK17 ASCII worktree, clean test --no-daemon --no-build-cache; offline 여부 명시. 99+신규/81, 100000회, JUnit 7종, 원시 XML/로그, 정확한 코드/증거 SHA, G0~G7, 발생한 CI 결과를 제출한다. 공통 Bootstrap과 Intelligence 전용 CI를 구분한다. 로컬 Python3.14.7 palette/PNG 2건은 GPT 담당이다.
REPORT-08-CLOSEOUT.md와 PR #3만 갱신한다. 최종 인계 표에 해결/미재현/외부 차단을 분리한다. D01, F04, C01, 전용 CI, 실측 정책, 실기기와 epoch 상한을 승인 전까지 PARTIAL/OPEN으로 둔다. 추가 R09, GB-03, GPT-07에 착수하지 않는다. main 병합, 강제 푸시 금지. PR #3 HOLD 유지. 사용자 및 총괄 검토를 기다린다.
