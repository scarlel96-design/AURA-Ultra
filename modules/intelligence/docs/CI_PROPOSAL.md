# 제안 — intelligence Kotlin 시험 워크플로

이 파일은 실행되지 않는다. 공통 `.github/workflows/bootstrap.yml`은 이번 회차에서 수정하지 않는다. 총괄이 통합할 최소 구성이다.

기존 `bootstrap.yml`은 push와 pull_request마다 WFF 파이프라인을 실행하고 `modules/intelligence` 시험과 `modules/domain` 시험을 실행하지 않는다. 아래 워크플로는 그 파이프라인을 바꾸지 않는다. intelligence 또는 domain 경로가 바뀔 때만 JDK 17로 두 시험을 실행한다. intelligence는 `includeBuild("../domain")`으로 도메인 소스를 치환하므로 도메인 변경도 이 검증에 포함한다.

저장소 루트에서 사람이 같은 검증을 실행하는 명령:

```text
./gradlew -p modules/intelligence test --rerun-tasks --no-daemon
./gradlew -p modules/domain test --rerun-tasks --no-daemon
```

Windows의 비ASCII 경로는 JDK 17 테스트 워커 `@argfile`을 MS949로 읽어 `ClassNotFoundException`이 난다. 로컬 통과 증거는 ASCII worktree에서 만든다. Ubuntu 러너는 그 문제를 재현하지 않으며, 이 제안이 그 제한의 해결은 아니다.

`push`는 `main`에 위 경로가 들어올 때도 같은 시험을 실행한다. pull request만 통과하고 main 푸시가 빠지는 구성을 두지 않는다. 공통 `bootstrap.yml`의 성공은 이 시험의 성공이 아니다.

JUnit XML이 없거나, XML의 `tests`가 0이거나, intelligence가 `TEST-*.xml` 파일 9개·시험 72개·실패 0·오류 0·건너뜀 0이 아니거나, domain이 `TEST-*.xml` 파일 7개·시험 81개·실패 0·오류 0·건너뜀 0이 아니면 그 단계는 실패한다. 집계는 `modules/intelligence/tools/check_junit_xml.py`가 `TEST-*.xml`만 본다. 다른 XML이 있어도 수량을 늘리거나 숨기지 못한다. 72는 회차 04의 52개에 `Round05Test` 7개와 `JunitXmlCheckTest` 13개를 더한 수량이다. 81은 유지한다. 시험을 추가하면 제안의 기대 수량도 함께 올린다. 수량을 낮추는 변경은 시험 미발견을 통과시키지 못한다. 도구는 결과 디렉터리 누락, 결과 파일 누락, 빈 XML, 손상된 XML, 시험 0개, 파일·시험 수 불일치, 실패·오류·건너뜀 은폐, 드러난 실패, 중복 suite·testcase, `--not-before`보다 이른 결과, 헤더 `tests`와 실제 `testcase` 수 불일치를 실패로 끝낸다. 정상 결과는 `OK files=N tests=M`을 찍고 종료 상태 0이다. 공통 워크플로에는 넣지 않는다.

```yaml
name: intelligence-kotlin
on:
  push:
    branches: [main]
    paths:
      - "modules/intelligence/**"
      - "modules/domain/**"
      - ".github/workflows/intelligence-kotlin.yml"
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
      - name: Mark JUnit window
        run: date -u +%Y-%m-%dT%H:%M:%SZ > "$RUNNER_TEMP/junit-not-before.txt"
      - name: Intelligence unit tests
        run: ./gradlew -p modules/intelligence test --rerun-tasks --no-daemon
      - name: Domain regression
        run: ./gradlew -p modules/domain test --rerun-tasks --no-daemon
      - name: Reject missing or short JUnit results
        run: |
          NOT_BEFORE="$(cat "$RUNNER_TEMP/junit-not-before.txt")"
          python3 modules/intelligence/tools/check_junit_xml.py \
            --dir modules/intelligence/build/test-results/test \
            --files 9 --tests 72 --not-before "$NOT_BEFORE"
          python3 modules/intelligence/tools/check_junit_xml.py \
            --dir modules/domain/build/test-results/test \
            --files 7 --tests 81 --not-before "$NOT_BEFORE"
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
