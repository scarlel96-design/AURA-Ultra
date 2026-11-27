# 제안 — intelligence Kotlin 시험 워크플로

이 파일은 실행되지 않는다. 공통 `.github/workflows/bootstrap.yml`은 이번 회차에서 수정하지 않는다. 총괄이 통합할 최소 구성이다.

기존 `bootstrap.yml`은 push와 pull_request마다 WFF 파이프라인을 실행하고 `modules/intelligence` 시험과 `modules/domain` 시험을 실행하지 않는다. 아래 워크플로는 그 파이프라인을 바꾸지 않는다. intelligence 또는 domain 경로가 바뀔 때만 JDK 17로 두 시험을 실행한다. intelligence는 `includeBuild("../domain")`으로 도메인 소스를 치환하므로 도메인 변경도 이 검증에 포함한다.

저장소 루트에서 사람이 같은 검증을 실행하는 명령:

```text
./gradlew -p modules/intelligence test --rerun-tasks --no-daemon
./gradlew -p modules/domain test --rerun-tasks --no-daemon
```

Windows의 비ASCII 경로는 JDK 17 테스트 워커 `@argfile`을 MS949로 읽어 `ClassNotFoundException`이 난다. 로컬 통과 증거는 ASCII worktree에서 만든다. Ubuntu 러너는 그 문제를 재현하지 않으며, 이 제안이 그 제한의 해결은 아니다.

```yaml
name: intelligence-kotlin
on:
  pull_request:
    paths:
      - "modules/intelligence/**"
      - "modules/domain/**"
      - ".github/workflows/intelligence-kotlin.yml"
  workflow_dispatch:
permissions:
  contents: read
concurrency:
  group: intelligence-kotlin-${{ github.ref }}
  cancel-in-progress: true
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "17"
      - name: Verify Gradle wrapper
        run: echo "b3a875ddc1f044746e1b1a55f645584505f4a10438c1afea9f15e92a7c42ec13  gradle/wrapper/gradle-wrapper.jar" | sha256sum -c -
      - name: Intelligence unit tests
        run: ./gradlew -p modules/intelligence test --rerun-tasks --no-daemon
      - name: Domain regression
        run: ./gradlew -p modules/domain test --rerun-tasks --no-daemon
      - name: Upload JUnit XML
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: intelligence-junit-xml
          path: |
            modules/intelligence/build/test-results/test/*.xml
            modules/domain/build/test-results/test/*.xml
          if-no-files-found: error
```

Wrapper 해시는 저장소의 `gradle/wrapper/gradle-wrapper.jar`와 기존 bootstrap 단계가 사용하는 값이다. 통합 시 그 해시가 바뀌었으면 같은 값으로 맞춘다. 루트 `settings.gradle.kts`에는 이 모듈을 넣지 않는다.
