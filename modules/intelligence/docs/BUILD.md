# aura-intelligence 독립 빌드

이 디렉터리는 루트 `settings.gradle.kts`에 포함되지 않는다. 루트 설정, Android 플러그인, Wear 앱, `modules/domain` 소스를 수정하지 않고 순수 JVM으로 컴파일한다. 도메인 계약은 `includeBuild("../domain")`으로 같은 소스 트리를 치환한다. 좌표는 `io.github.scarlel96.aura:aura-domain`이다.

## 명령

저장소 루트에서 기존 Wrapper를 사용한다.

```text
.\gradlew -p modules/intelligence test
.\gradlew -p modules/intelligence dependencies --configuration testRuntimeClasspath
.\gradlew -p modules/domain test
python modules/intelligence/tools/check_junit_xml.py --dir modules/intelligence/build/test-results/test --files 13 --tests 108 --not-before <start> --not-after <end>
python modules/intelligence/tools/check_junit_xml.py --dir modules/domain/build/test-results/test --files 7 --tests 81 --not-before <start> --not-after <end>
```

`check_junit_xml.py`는 표준 라이브러리만 쓴다. 공통 GitHub Actions에는 연결되어 있지 않다. `--not-before`보다 이른 XML과 `--not-after`보다 늦은 XML을 거절한다. 창은 호출자가 준다. 시험이 끝난 디렉터리에만 실행한다. 직접 자식이 아닌 `testcase`, 빈 classname·메서드, suite와 다른 classname, `TEST-{suite}.xml`이 아닌 파일명, 빠진 카운터도 거절한다.

`-p`는 시작 디렉터리를 `modules/intelligence`로 두고 이 디렉터리의 `settings.gradle.kts`를 읽는다. 루트 프로젝트 `:apps:watchface`는 구성되지 않는다. 도메인 회귀는 기존 `modules/domain` 빌드를 그대로 실행한다.

독립 CI에 넣을 명령과 워크플로 초안은 [CI_PROPOSAL.md](CI_PROPOSAL.md)에 있다. 그 파일은 실행되지 않고, 공통 `.github/workflows`는 바꾸지 않는다.

## 고정 버전

| 도구 | 버전 | 역할 |
|---|---|---|
| Gradle Wrapper | 9.3.1 | 저장소 루트 Wrapper. 이 모듈은 Wrapper를 복제하지 않는다. |
| Kotlin Gradle Plugin / stdlib | 2.4.21 | 컴파일러와 표준 라이브러리 |
| kotlin-test-junit5 | 2.4.21 | 테스트 실행 |
| JUnit Jupiter / Platform | 5.10.1 / 1.10.1 | kotlin-test가 가져온다 |
| 바이트코드 | JVM 17 | Kotlin `jvmTarget`과 Java toolchain |
| 컴파일·테스트 JVM | 17 | Foojay toolchain resolver 1.0.0 |

조회일 2026-11-28. Kotlin 2.4.21, https://kotlinlang.org/docs/releases.html, Apache-2.0, https://github.com/JetBrains/kotlin/blob/v2.4.21/license/LICENSE.txt. JUnit 5는 EPL-2.0, https://junit.org/junit5/. opentest4j 1.3.0. JetBrains annotations 13.0, Apache-2.0. Gradle Wrapper 9.3.1, Apache-2.0. Foojay 1.0.0, Apache-2.0, https://github.com/gradle/foojay-toolchains.

저장소는 `mavenCentral`과 Gradle Plugin Portal만 사용한다. Android SDK, 네트워크 클라이언트, 건강 데이터 라이브러리는 의존성에 없다. 실행 경로는 호출자가 넣은 `Observation`만 본다.

생성물 `modules/intelligence/build`와 `.gradle`은 저장소 무시 규칙에 해당하며 커밋하지 않는다.

## Windows 경로

JDK 17 테스트 워커는 클래스패스를 `@argfile`로 받는다. Gradle 9.3.1은 그 파일을 UTF-8로 쓴다. Temurin 17.0.20.1은 `@argfile`을 `sun.jnu.encoding=MS949`로 읽는다. 명령의 `-Dfile.encoding=UTF-8`은 argfile을 펼친 뒤에 적용된다. 비ASCII 경로에서는 `ClassNotFoundException`이 난다. GB-01에서 확인한 절차와 같다. 이 모듈의 통과 시험은 ASCII worktree에서 실행한다.

통과 명령의 예:

```text
C:\Users\scarl\AppData\Local\Temp\aura-gb02-wt\gradlew -p modules/intelligence clean test --rerun-tasks
```
