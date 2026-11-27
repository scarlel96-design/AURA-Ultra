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

JDK 17 테스트 워커는 클래스패스를 `@argfile`로 받는다. Gradle 9.3.1은 그 파일을 UTF-8로 쓴다. 이 기기의 Temurin 17.0.20.1은 `@argfile`을 플랫폼 인코딩 `sun.jnu.encoding=MS949`로 읽는다. 워커 명령의 `-Dfile.encoding=UTF-8`은 argfile을 펼친 뒤에 적용되므로 이 디코딩을 바꾸지 않는다. 경로에 비ASCII 문자가 있으면 클래스 디렉터리 경로가 깨지고 `ClassNotFoundException`이 난다. 클래스 파일은 디스크에 있다. ASCII 경로에서는 두 인코딩이 같은 바이트라 실패하지 않는다.

재현: `C:\Users\scarl\AppData\Local\Temp\코딩-gb01` 접합에서 `IdentityTest` 실행. 워커 argfile의 한글 구간 바이트는 UTF-8 `EC BD 94 EB 94 A9`였다. 같은 JDK로 UTF-8 argfile의 클래스는 찾지 못했고, MS949 argfile의 같은 클래스는 실행됐다.

통과한 시험은 ASCII worktree에서 실행한다. 저장소를 옮기지 않을 때는 ASCII 접합을 쓴다.

```text
cmd /c mklink /J C:\aura-ultra "<저장소 경로>"
C:\aura-ultra\gradlew -p modules/domain test
```

접합은 다른 복사본이 아니다. 작업이 끝나면 접합만 지운다. `rmdir C:\aura-ultra`는 대상을 지우지 않는다. ASCII 경로에서는 추가 절차 없이 저장소 루트의 명령을 사용한다.
