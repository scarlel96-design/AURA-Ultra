# 개발 실행 지침
## 기술 스택
WFF XML / Android Studio / Gradle / Kotlin / Compose for Wear OS / Jetpack Compose / Health Services / Health Connect / Data Layer / DataStore 또는 Room / 검증된 HTTP 클라이언트. 버전은 WO-01~02에서 공식 호환표를 확인하고 고정한다. 미확인 최신 버전을 임의로 선택하지 않는다.
Windows 개발 환경을 포함한다. JDK, Android SDK, platform-tools, 에뮬레이터, 무선 ADB, Gradle Wrapper, 공식 WFF 도구를 기록한다. 시크릿은 환경별 안전한 저장소에서 읽는다.

## 오픈소스 및 제작 자산
| 후보 | 역할 | 정책 |
|---|---|---|
| https://github.com/google/watchface | Validator / Memory Evaluator / Optimizer | 우선 검증 |
| https://github.com/android/wear-os-samples | WFF/Complication/Data Layer 예제 | 공식 참고 |
| https://github.com/android/health-samples | 건강 API 예제 | 공식 참고 |
| https://github.com/garanj/wfp-use-cases | Reference 연동 사례 | 비공식 샘플; 검증 |
| https://github.com/google/horologist | Wear 공통 기능 | 필요 시 |
| https://github.com/rsms/inter | 글꼴 | OFL 조건 확인 |
| https://github.com/google/material-design-icons | 아이콘 | 라이선스·사용 범위 확인 |
| https://github.com/Turtlepaw/clockwork | WFF CLI | 검증 후 |
| https://www.blender.org/ | 광학 소재 사전 렌더링 | 원본 자산 제작 |
| https://inkscape.org/ | 벡터 자산 | 원본 자산 제작 |
| https://developer.samsung.com/watch-face-studio/overview.html | 시안/기기 확인 | 보조 |
| https://developer.android.com/training/wearables/watch-face-designer/export | Figma → WFF | 보조 |

도입 전 URL, release/commit, 라이선스, 의존성, 보안, 호환성, 수정 범위, 도입 사유를 기록한다. 라이선스 검증 전 코드를 복사하지 않는다. Star 수를 품질 증거로 사용하지 않는다. 현재 전수 감사 미실시.

## 파이프라인
Design tokens + 원본 자산 → Asset Compiler(크롭·크기·압축·프레임) → WFF Generator → 버전별 스키마 검사 → Memory Evaluator → 빌드 → 스크린샷/실기기 시험.
생성 자산의 원본, 생성 명령, 도구 버전, 해시를 관리한다. 재현 가능한 빌드를 목표로 한다.
CI에는 포맷·정적 검사·단위 테스트·WFF 검증·메모리·빌드·라이선스 검사를 순차 도입한다. 검증이 실행되지 않은 경우 성공으로 표시하지 않는다.

## 협업
WO 단위 브랜치에서 변경한다. Codex가 통합한다. 병렬 보조 도구는 별도 브랜치와 비중복 파일을 사용한다. 인터페이스를 합의한 뒤 구현한다. PR에 요구사항 ID, 변경 파일, 검증 결과, 위험, 롤백 방법을 포함한다. 자동 병합 또는 릴리스는 별도 승인 없이는 실행하지 않는다.

## GPT 우선 개발 운영
현재 사용자 요구에 따라 채팅 GPT가 가능한 코드·테스트·자동화·문서 작업을 먼저 수행한다. Codex는 실기기 및 복잡한 통합·최종 품질에 집중한다. 작업 선택과 안전한 재개는 operations/RESUME_PROTOCOL.md를 따른다. 세션 종료 전 상태·이력·차단점·증거를 갱신한다.
