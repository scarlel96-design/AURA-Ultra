# aura-domain 독립 빌드

이 디렉터리는 루트 `settings.gradle.kts`에 포함되지 않는다. 루트 설정, Android 플러그인, Wear 앱을 수정하지 않고 순수 JVM으로 컴파일한다.

## 명령

저장소 루트에서 기존 Wrapper를 사용한다.

```text
.\gradlew -p modules/domain test
.\gradlew -p modules/domain dependencies --configuration testCompileClasspath
```

`-p`는 시작 디렉터리를 `modules/domain`으로 두고 이 디렉터리의 `settings.gradle.kts`를 읽는다. 루트 프로젝트 `:apps:watchface`는 구성되지 않는다.

## 고정 버전

| 도구 | 버전 | 역할 |
|---|---|---|
| Gradle Wrapper | 9.3.1 | 저장소 루트 Wrapper. 이 모듈은 Wrapper를 복제하지 않는다. |
| Kotlin Gradle Plugin / stdlib | 2.4.21 | 컴파일러와 표준 라이브러리 |
| kotlin-test-junit5 | 2.4.21 | 테스트 실행 |
| 바이트코드 | JVM 17 | Kotlin `jvmTarget`과 Java toolchain |
| 컴파일·테스트 JVM | 17 | Foojay toolchain resolver 1.0.0 |

조회일 2026-11-27. Kotlin 안정 버전 근거: https://kotlinlang.org/docs/releases.html (Latest Kotlin version 2.4.21). 라이선스: Kotlin Apache-2.0, https://github.com/JetBrains/kotlin/blob/v2.4.21/license/LICENSE.txt. JUnit 5는 kotlin-test-junit5가 가져오며 Eclipse Public License 2.0, https://junit.org/junit5/. Gradle 9.3.1은 Apache-2.0.

저장소는 `mavenCentral`과 Gradle Plugin Portal만 사용한다. Android SDK, Google Maven, 네트워크 클라이언트, 건강 데이터 라이브러리는 의존성에 없다. JDK 17 도구 사슬은 `org.gradle.toolchains.foojay-resolver-convention` 1.0.0, Apache-2.0, https://github.com/gradle/foojay-toolchains 를 사용한다.

첫 실행은 플러그인 다운로드가 필요하다. 이후 동일 Wrapper와 동일 버전으로 다시 실행한다. 생성물 `modules/domain/build`와 `.gradle`은 저장소 무시 규칙에 해당하며 커밋하지 않는다.

## Windows 경로

저장소 경로에 비ASCII 문자가 있으면 이 환경의 Gradle 테스트 워커가 테스트 클래스를 읽지 못하고 `ClassNotFoundException`으로 실패했다. JDK 17과 JDK 21 모두 같은 실패였다. 소스와 빌드 파일은 저장소에 두고, ASCII 경로의 디렉터리 접합에서 같은 명령을 실행한다.

```text
cmd /c mklink /J C:\aura-ultra "<저장소 경로>"
C:\aura-ultra\gradlew -p modules/domain test
```

접합은 다른 복사본이 아니다. ASCII 경로에서는 추가 절차 없이 저장소 루트의 명령을 사용한다.
