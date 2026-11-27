# 제안 — domain Kotlin 시험 워크플로

이 파일은 실행되지 않는다. 공통 `.github/workflows`는 이번 회차에서 수정하지 않는다. 총괄이 통합할 최소 구성이다.

기존 `bootstrap.yml`은 push와 pull_request마다 WFF 파이프라인을 실행하고 `modules/domain` 시험을 실행하지 않는다. 아래 워크플로는 그 파이프라인을 바꾸지 않고, 도메인 경로가 바뀔 때만 JDK 17로 `modules/domain` 시험을 실행한다.

```yaml
name: domain-kotlin
on:
  pull_request:
    paths:
      - "modules/domain/**"
      - ".github/workflows/domain-kotlin.yml"
  workflow_dispatch:
permissions:
  contents: read
concurrency:
  group: domain-kotlin-${{ github.ref }}
  cancel-in-progress: true
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "17"
      - name: Verify Gradle wrapper
        run: echo "b3a875ddc1f044746e1b1a55f645584505f4a10438c1afea9f15e92a7c42ec13  gradle/wrapper/gradle-wrapper.jar" | sha256sum -c -
      - name: Domain unit tests
        run: ./gradlew -p modules/domain test --rerun-tasks --no-daemon
      - name: Upload JUnit XML
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: domain-junit-xml
          path: modules/domain/build/test-results/test/*.xml
          if-no-files-found: error
```

Wrapper 해시는 저장소의 `gradle/wrapper/gradle-wrapper.jar`와 기존 bootstrap 단계가 사용하는 값이다. 통합 시 그 해시가 바뀌었으면 같은 값으로 맞춘다. Ubuntu 러너의 경로는 ASCII라서 Windows 비ASCII 경로의 테스트 워커 문제를 재현하지 않는다. 이 제안은 그 환경 제한의 해결이 아니다.
