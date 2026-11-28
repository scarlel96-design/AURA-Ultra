# CODEX-F03 — 공급망 차단점 확인 결과

2026-11-28 KST · Codex · AUD-R04-05 **OPEN / PARTIAL** · R-21/R-22 · WO-02 · 제품 **NO-GO**. 독립 검수: 대기.
기준 `main` 및 검증 소스: `e8e1af6c2be14acbe47c031066f70463ee1d2295`. 제출 범위: 이 보고서 1개. 제품, Domain, Intelligence, CI, 정책 및 SDK/기기 변경 없음.

## PRE-FLIGHT

기준 SHA를 GitHub Branches API에서 두 번 확인했다. `AGENTS.md`, `README.md`, `docs/{STATUS,MASTER_ARCHITECTURE,REQUIREMENTS,QUALITY_GATES,ROADMAP}.md`와 `SECURITY.md`를 기준 SHA에서 읽었다. `docs/operations/`의 RESUME_PROTOCOL, PROJECT_INVARIANTS, TASK_RECORD_PROTOCOL, VERIFICATION_PROTOCOL, TASK_REPORT_TEMPLATE, GPT_EXECUTION_PLAN, BLOCKERS, WORK_LOG, agent-orders의 배정표 및 CODEX-F03-HANDOFF를 읽었다. WO-02, 통합 결함 등록부 및 개선 계획, F03 R04/R08/R09/R10/R11/R12/R13/R14/R15/R16/R17, PROVENANCE-HANDOFF를 대조했다. 기준 소스는 루트 및 Domain Gradle 설정, 앱 Gradle 파일, wrapper 설정과 실제 CI 워크플로다. R17 검증 스크립트 및 워크플로는 해당 audit SHA에서 별도로 확인했다.

| PR | 상태 | 확인한 HEAD |
|---|---|---|
| #2 | open / HOLD | `fc98c3ad5993e131f733a9444b5849e737a49086` |
| #3 | open / HOLD | `0c4890ea7f69c6145791d17d51b98c97fed45c1d` |
| #5 | open / HOLD | `d847028dc914ebb0acfbf47ff6b83a179d9bf486` |
| #6 | open / HOLD | `68f52ebd1914c7045e34f093fd91516c73af116b` |
| #7 | open / HOLD | `7501dcfe990c7f16123b8fdc44a90baf7354533b` |

기준 SHA 원시 CI: [Bootstrap 46148540826](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46148540826) job 140989799482, [Windows 46148540782](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46148540782) jobs 140989799166 / 140989799397, [문서 46148540783](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46148540783) job 140989799265. 모두 SUCCESS. Linux와 Windows 두 설정에서 각 402개 테스트를 실행했다. 문서 검사기 자체 시험은 7개다. Bootstrap의 공식 WFF 및 네 가지 격리 단계가 SUCCESS다. [Domain 46117540979](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46117540979)는 이전 SHA `b7c8542123901cc49430a35f696a01e21efba915`의 별도 SUCCESS다. 현재 SHA의 신규 Domain 실행으로 계산하지 않았다. 원격 문서·소스·CI 대조는 완료했다. 로컬 clean checkout 및 독립 Gradle 실행 조건은 BLOCKED다.

## 로컬 환경과 원본 아카이브

Windows NT 10.0.26300.0, PowerShell, Git 2.49.0.windows.1, curl 8.23.0, Python 3.14.7, 기본 Java Temurin 21.0.5+11. 기본 JAVA 및 확인한 설치·Gradle toolchain 경로에서 JDK 17을 찾지 못했다. 기존 Gradle 9.3.1 배포 파일과 Android SDK 플랫폼 android-36/36.1/37/37.0을 확인했다. Gradle과 SDK를 실행하거나 설치하지 않았다.

- `git -c credential.interactive=never ls-remote https://github.com/scarlel96-design/AURA-Ultra.git refs/heads/main` → `Could not resolve host: github.com`, exit 128. 로컬 작업 폴더에는 Git checkout이 없었다.
- `curl.exe -q --silent --show-error --head --connect-timeout 5 --max-time 10 URL`로 Gradle 캐시를 사용하지 않고 네트워크를 확인했다. `github.com`, `repo.maven.apache.org`, `plugins.gradle.org`, `dl.google.com`에서 각각 exit 6 / HTTP 000을 받았다. HTTP 000은 HTTP 응답을 받지 못했다는 의미다. TLS, 리디렉션 및 원격 바이트를 관측하지 못했다.
- `Get-ChildItem`으로 `$env:USERPROFILE\.gradle\caches\modules-2\files-2.1\org.jetbrains.kotlin\kotlin-compiler-embeddable`을 읽었다. 버전 디렉터리는 2.4.20과 2.4.21이었다. 2.2.10/2.4.0은 이 캐시에 없었다. 기존 캐시의 파일을 바꾸지 않았다.
- GitHub 연결에서 아래 원본 아카이브의 다운로드 참조를 받았다. Actions API의 크기와 SHA-256은 당시 기록과 일치했다. 참조의 호스트 `sdmntpraustraliaeast.oaiusercontent.com`에 대한 HEAD는 exit 6 / HTTP 000이었다. 로컬 원본 ZIP의 바이트, CRC 및 행 재추출은 **NOT RUN**이다. 아카이브 메타데이터와 기존 원시 CI 증거를 재사용했다.

| 원본 아카이브 | API 크기(B) | API SHA-256 |
|---|---:|---|
| [15243421432](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46095415032/artifacts/15243421432) | 108387 | `bde7f9ab10ed03882457289e963d90ab6ae8e914b67ec4bf6d68b3d9a9a8fe19` |
| [15243241825](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46095415032/artifacts/15243241825) | 25425 | `4b85c4b32d951c09a3ac1b0cc8e110085038d37a3c1673ceca204d563e6202b9` |
| [15249229410](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46112122206/artifacts/15249229410) | 2546 | `734667209c5cd9d666d5e58c65abcd14e3c6ef04e46bf2a8d3a4239637261c5c` |
| [15248144979](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46108927818/artifacts/15248144979) | 54330 | `83abe7be0c76b2bf37982676567f0692d80690baacad566d6587c7c0d5415d18` |

R04 두 원본의 검증 소스는 `e7dd34de38012410d057460b03a74e4c12378d1d`다. 별도 보고서 [R16](REPORT-R16.md)과 원시 [R17 job 140877748686](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46112122206/job/140877748686)의 해시 행을 비교에 사용했다.

## 두 compiler JAR의 공식 출처

GitHub 연결에서 `GET /repos/JetBrains/kotlin/releases/tags/vVERSION`을 읽었다. 정확한 `kotlin-compiler-embeddable` 릴리스 자산의 ID, 크기, SHA-256이 R16/R17의 인벤토리 해시와 각각 일치했다. JetBrains의 두 릴리스 자산 목록에서도 같은 다이제스트를 확인했다.

| 버전·JetBrains 공식 자산 | 자산 ID | 크기(B) | 릴리스 자산 SHA-256 |
|---|---:|---:|---|
| [kotlin-compiler-embeddable-2.2.10.jar](https://github.com/JetBrains/kotlin/releases/download/v2.2.10/kotlin-compiler-embeddable-2.2.10.jar) · [릴리스 목록](https://github.com/JetBrains/kotlin/releases/expanded_assets/v2.2.10) | 598652892 | 56259401 | `79628fd5d64b4692a62f98962baab00e9076a37e2cffd6ace33cd0b7be7d1cdf` |
| [kotlin-compiler-embeddable-2.4.0.jar](https://github.com/JetBrains/kotlin/releases/download/v2.4.0/kotlin-compiler-embeddable-2.4.0.jar) · [릴리스 목록](https://github.com/JetBrains/kotlin/releases/expanded_assets/v2.4.0) | 587835542 | 60351320 | `c2b25e8c1c93ec416ba4327f5e31eaec0f0c8847241b9353e294b8db9dce564f` |

공식 자산 메타데이터와 감사 기준의 일치는 확인했다. 원본 JAR의 로컬 다운로드·해시·서명 검증은 **NOT RUN**이다. 위 직접 릴리스 URL은 독립 확인된 출처다. R17의 Maven 요청이 그 정확한 URL로 이동했는지는 확인되지 않았다. R17에서 두 Central 주소 모두 `Redirect refused; host=github.com`으로 끝났다. 이번 정확한 URL HEAD에서도 DNS 단계에서 중단됐다. 따라서 R17의 662/664 기존 바이트/sidecar 교차 근거 집계와 승인 0건을 유지한다.

실행: 각 아래 URL에 `curl.exe -q --silent --show-error --head --connect-timeout 5 --max-time 10 --output NUL --write-out 'http=%{http_code} bytes=%{size_download} redirects=%{num_redirects}\n' $url`. 루프의 각 curl 상태를 기록했다.

```text
curl: (6) Could not resolve host: repo.maven.apache.org
http=000 bytes=0 redirects=0
url=https://repo.maven.apache.org/maven2/org/jetbrains/kotlin/kotlin-compiler-embeddable/2.2.10/kotlin-compiler-embeddable-2.2.10.jar exit=6
curl: (6) Could not resolve host: repo.maven.apache.org
http=000 bytes=0 redirects=0
url=https://repo.maven.apache.org/maven2/org/jetbrains/kotlin/kotlin-compiler-embeddable/2.4.0/kotlin-compiler-embeddable-2.4.0.jar exit=6
curl: (6) Could not resolve host: github.com
http=000 bytes=0 redirects=0
url=https://github.com/JetBrains/kotlin/releases/download/v2.2.10/kotlin-compiler-embeddable-2.2.10.jar exit=6
curl: (6) Could not resolve host: github.com
http=000 bytes=0 redirects=0
url=https://github.com/JetBrains/kotlin/releases/download/v2.4.0/kotlin-compiler-embeddable-2.4.0.jar exit=6
```

## Kotlin JVM marker POM의 경로

`org.jetbrains.kotlin.jvm:org.jetbrains.kotlin.jvm.gradle.plugin:2.4.21`. 로컬 Gradle URL 캐시의 한 직렬화 레코드에 Plugin Portal URL과 정확한 673 B 캐시 파일이 함께 있었다. 파일 SHA-256은 R17의 Portal 값과 같다. [Gradle 저장 형식](https://github.com/gradle/gradle/blob/v9.3.1/platforms/software/dependency-management/src/main/java/org/gradle/internal/resource/cached/DefaultCachedExternalResourceIndex.java)은 같은 값 레코드에 캐시 파일과 원격 메타데이터 URI를 기록한다. [Gradle 캐시 접근 소스](https://github.com/gradle/gradle/blob/v9.3.1/platforms/software/dependency-management/src/main/java/org/gradle/internal/resource/transfer/DefaultCacheAwareExternalResourceAccessor.java)에는 원격 체크섬이 맞으면 기존 파일을 재사용하는 경로도 있다.

판정: **이 Windows 캐시의 리소스 출처는 Plugin Portal**. `cached_at`은 캐시 기록 시각이다. `recorded_content_length=-1`은 길이 미기록이며, 673 B는 실제 파일 측정값이다. 이 기록만으로 실제 HTTP 전송 또는 R04/R08의 별도 CI에서 사용한 경로를 확정하지 않는다. Domain 소스는 Plugin Portal을 Central보다 먼저 선언한다. 이전 CI 경로는 그 실행의 원본 전송 로그 또는 캐시 인덱스가 필요하다. R17의 Central POM은 1376 B / `8e08073d123182e69c07d24c6dca7b98cc53a37707a73a6af7be88e38218b42b`였다. 두 경로의 해시를 별개로 보존한다.

```text
index_sha256=d258a0c73dbc46af7672e5b75e692a00537c23f30c3c05609641575bc73409be value_offset=1672793
metadata=https://plugins.gradle.org/m2/org/jetbrains/kotlin/jvm/org.jetbrains.kotlin.jvm.gradle.plugin/2.4.21/org.jetbrains.kotlin.jvm.gradle.plugin-2.4.21.pom recorded_content_length=-1
cached_at_utc=2026-11-27T13:30:21.202000+00:00
last_modified_utc=2026-10-08T09:03:53+00:00
file_bytes=673 sha256=c250047db1cbab6f0d801c44615172892bd3892aa9bc9cc8ef9ecaa4149fda67
missing_file_flag and changed_origin: rejected (2/2)
```

실행 명령은 PowerShell의 `@'<줄바꿈>아래 Python 코드<줄바꿈>'@ | python -`이다. 최종 exit 0. 변경된 출처와 캐시 파일 플래그 누락은 메모리에서만 시험했다. 첫 시도는 Gradle의 길이 미기록 값을 가변 정수로 읽다가 실패했다(exit 1). 최종 명령은 Gradle의 9바이트 Kryo 값을 부호 있는 정수로 해석한다.

```python
from pathlib import Path
from datetime import datetime, timezone
import hashlib, os, struct
r = Path(os.environ["USERPROFILE"]) / ".gradle/caches/modules-2"
raw = (r / "metadata-2.107/resource-at-url.bin").read_bytes()
name = "org.jetbrains.kotlin.jvm.gradle.plugin-2.4.21.pom"
maven = "org/jetbrains/kotlin/jvm/org.jetbrains.kotlin.jvm.gradle.plugin/2.4.21/"
rel = ("files-2.1/org.jetbrains.kotlin.jvm/org.jetbrains.kotlin.jvm.gradle.plugin/"
       "2.4.21/44b18b0df1c28548f1f4d32ec6a0277afdcc70db/" + name)
url = "https://plugins.gradle.org/m2/" + maven + name
def var(buf, i, count=5):
    n = 0
    for j in range(count):
        b = buf[i]
        i += 1
        if count == 9 and j == 8:
            return n | b << 56, i
        n |= (b & 127) << (j * 7)
        if b < 128:
            return n, i
    raise ValueError("invalid length")
def string(buf, i):
    b = buf[i]
    i += 1
    if not b & 128:
        raise ValueError("expected Kryo length-prefixed string")
    n = b & 63
    if b & 64:
        high, i = var(buf, i)
        n |= high << 6
    if n < 1:
        raise ValueError("empty string")
    return buf[i:i+n-1].decode("ascii"), i+n-1
def read(buf, i):
    if buf[i] != 1:
        raise ValueError("cached file absent")
    f, i = string(buf, i+1)
    ts = struct.unpack_from(">q", buf, i)[0]
    i += 8
    if buf[i] != 1:
        raise ValueError("metadata absent")
    uri, i = string(buf, i+1)
    if buf[i] != 1:
        raise ValueError("last-modified absent")
    modified = struct.unpack_from(">q", buf, i+1)[0]
    typ, i = string(buf, i+9)
    size, i = var(buf, i, 9)
    if f != rel or uri != url or not typ.startswith("application/xml"):
        raise ValueError("unexpected path, origin, or content type")
    return ts, modified, uri, size - (1 << 64) if size >> 63 else size
if raw.count(rel.encode()) != 1 or raw.count(url.encode()) != 1:
    raise SystemExit("ambiguous cache record")
ix = raw.index(rel.encode()) - 3
ts, modified, uri, size = read(raw, ix)
pom = (r / rel).read_bytes()
expected = "c250047db1cbab6f0d801c44615172892bd3892aa9bc9cc8ef9ecaa4149fda67"
if len(pom) != 673 or hashlib.sha256(pom).hexdigest() != expected:
    raise SystemExit("POM bytes mismatch")
print("index_sha256="+hashlib.sha256(raw).hexdigest(), "value_offset="+str(ix))
print("metadata="+uri, "recorded_content_length="+str(size))
print("cached_at_utc="+datetime.fromtimestamp(ts/1000, timezone.utc).isoformat())
print("last_modified_utc="+datetime.fromtimestamp(modified/1000, timezone.utc).isoformat())
print("file_bytes="+str(len(pom)), "sha256="+expected)
for altered in (raw[:ix]+b"\0"+raw[ix+1:],
                raw.replace(url.encode(), url.replace("plugins", "example").encode(), 1)):
    try:
        read(altered, ix)
    except ValueError:
        continue
    raise SystemExit("negative accepted")
print("missing_file_flag and changed_origin: rejected (2/2)")
```

## 배포자 신뢰 및 검증 누락

- R14에서 강한 서명 18/48을 검증했다. 공식 키와 대조한 것은 12개다. Kotlin은 [공식 지문](https://kotlinlang.org/docs/security.html) `2FBA29D08D2E25EE84C132C30729A0AFF8999A87`을 현재 다시 확인했다. Bouncy Castle과 Commons는 기존 R14 지문 및 공식 [BC Maven 키](https://www.bouncycastle.org/download/bouncy-castle-java/)와 [Apache KEYS](https://downloads.apache.org/commons/KEYS) 경로를 유지한다. 후보 릴리스에서 키 교체·폐기와 서명 시점의 배포 권한을 별도로 확인한다.
- Guava 6개는 발견한 키와 AndroidX 소비자 설정의 일치다. Google/Guava 배포자 지문 또는 정확한 배포 다이제스트가 아직 필요하다. R15의 Apache 공식 배포 ZIP은 HttpClient JAR 1개를 강한 다이제스트로 뒷받침한다. 나머지 Netty/HttpClient/JDOM2의 약한 서명 행마다 공식 강한 다이제스트 또는 유효한 강한 서명을 찾는다. jose4j의 태그 POM 일치는 JAR 서명 검증이 아니다. jose4j 2개는 공식 키 또는 강한 배포 다이제스트가 필요하다.
- R16 기준 425개에 서명 파일이 존재한다. 원래 우선 행의 SHA-1 서명 28개와 jose4j 키 미확보 2개는 별도 집계다. R16에서 찾지 못한 서명 6개는 `javax.inject:javax.inject:1` JAR/POM, `net.sf.kxml:kxml2:2.3.0` JAR/POM, Foojay marker POM 1.0.0 및 `org.sonatype.oss:oss-parent:7` POM이다. 정확한 파일 단위의 신뢰 근거와 독립 검토 전까지 승인 0을 유지한다.
- R09의 373개 component / 664개 artifact는 잠정 build inventory다. 라이선스 결과는 직접 선언 237, 직접 선언 없음 74, 고정 POM 없음 61, marker 경로에 따른 POM 불일치 1이다. 상속 POM, JAR/AAR의 LICENSE·NOTICE, 재배포 의무, 빌드 전용 및 APK 포함 여부를 각각 확인한다. 이름이나 선언만으로 의무 충족을 판정하지 않는다.
- 잠정 CycloneDX 1.6은 release SBOM이 아니다. 후보의 실제 WFF2–5 배포 APK 목록과 배포 리소스를 대조한다. buildscript/설정 플러그인, detached, Lint, UTP, 단위/연결 테스트, Gradle 배포 및 SDK 도구는 별도 범위로 기록한다. 현재 `main`의 추적 트리에서 `verification-metadata.xml` 및 dependency lockfile을 찾지 못했다. 독립 Intelligence composite 범위를 Android/Domain 결과로 추정하지 않는다.

## R12 잔여 9건의 해결 경로

원시 [R12 job 140867872652](https://github.com/scarlel96-design/AURA-Ultra/actions/runs/46108927818/job/140867872652), audit `a1158e8b430c5c7aa7eee437b1d70477e4649662`: AGP 9.5.3/Gradle 9.6.1 후보의 assemble 8개 및 lint 8개가 성공했다. OSV 대상 197개에서 8개 component가 9개 ID에 해당했다. 최종 게이트는 exit 1이다. 이 표는 그 후보의 패치 하한이며, main의 전체 권고 수가 아니다.

| R12 영향 좌표 | 권고 ID | 수정 하한 및 적용 지점 |
|---|---|---|
| `com.google.guava:guava:33.4.0-jre` | [GHSA-xxph-c9ww-hj94](https://github.com/advisories/GHSA-xxph-c9ww-hj94) | 33.7.2 계열의 JRE 변형을 포함하는 AGP/Lint 검사 |
| `org.apache.commons:commons-lang3:3.16.0` | [GHSA-j288-q9x7-2f5v](https://github.com/advisories/GHSA-j288-q9x7-2f5v) | 3.18.0 이상을 사용하는 AGP/Lint 검사 |
| `org.apache.httpcomponents:httpclient:4.5.6` | [GHSA-7r82-7xv7-xcpj](https://github.com/advisories/GHSA-7r82-7xv7-xcpj) | 4.x 하한 4.5.13. Lint 실제 classpath에서 검사 |
| `org.bitbucket.b_c:jose4j:0.9.5` | [GHSA-3677-xxcr-wjqv](https://github.com/advisories/GHSA-3677-xxcr-wjqv) | 0.9.6 이상을 사용하는 AGP classpath 검사 |
| `org.bouncycastle:bcpkix-jdk18on:1.80.2` | [GHSA-wg6q-6289-32hp](https://github.com/advisories/GHSA-wg6q-6289-32hp) | 1.84. 채택 후보는 BC 계열 전체를 맞춘다 |
| `org.bouncycastle:bcprov-jdk18on:1.80.2` | [GHSA-9pwp-9qqc-pr26](https://github.com/advisories/GHSA-9pwp-9qqc-pr26) (Critical) | 1.85. AGP/Lint의 bcprov, bcpkix, bcutil, BOM을 함께 검사 |
| 같은 bcprov | [GHSA-qp49-qgx5-5m26](https://github.com/advisories/GHSA-qp49-qgx5-5m26) | 1.85. 같은 계열 검사로 두 건을 확인 |
| `org.jdom:jdom2:2.0.6` | [GHSA-2363-cqg2-863c](https://github.com/advisories/GHSA-2363-cqg2-863c) | 2.0.6.1 이상을 사용하는 AGP classpath 검사 |
| `org.jetbrains.kotlin:kotlin-gradle-plugin:2.2.10` | [GHSA-r937-wjx7-w2jp](https://github.com/advisories/GHSA-r937-wjx7-w2jp) | 권고 하한 2.4.20-Beta1. 검증 후보는 호환되는 안정 KGP 2.4.20 이상 |

[Google 공개 표](https://developer.android.com/reference/tools/gradle-api)에서 9.5.3은 안정, 9.6.0-alpha07은 프리뷰다. [AGP 9.6 변경](https://developer.android.com/build/releases/agp-9-6-0-release-notes)은 기본 KGP를 2.4.20으로 올린다. 이는 KGP 1건의 상류 해결 경로다. 같은 변경이 다른 8건을 해결했다는 근거는 없다. Google은 [지원되는 KGP 명시](https://developer.android.com/build/migrate-to-built-in-kotlin#choose-a-kotlin-gradle-plugin-version)를 문서화했다. [JetBrains 호환표](https://kotlinlang.org/docs/gradle-configure-project.html)는 KGP 2.4.20–2.4.21의 완전 지원 범위를 AGP 8.5.2–9.3.1 및 Gradle 7.6.3–9.7.0으로 제시한다. 따라서 승인 후 현행 AGP 9.1.1/Gradle 9.3.1과 안정 KGP 조합을 별도 비교할 수 있다. 9.5.3에 같은 KGP를 강제하지 않는다. 상류가 패치된 AGP/Lint 조합을 게시하면 메타데이터 diff로 바뀐 좌표를 먼저 확인한다. 새 후보의 그래프·빌드·OSV·직접 APK 증거를 그때 한 번 수집한다. 동일 후보 재실행과 임의 force/exclude는 하지 않았다.

## Strict 적용 조건 및 종료

1. 정확한 JAR·POM·module 다이제스트 또는 공식 키와 강한 서명을 파일별로 승인받는다. 동적 버전과 자동 신뢰 추가를 배제한다.
2. 모든 실제 진입점에서 해석 그래프를 기록한다. project와 buildscript lock을 별도로 적용한다. settings·plugin·detached 구성은 잠금 가능 여부를 개별 확인한다. 미적용 경로의 버전과 아티팩트는 명시적으로 검증한다.
3. 검토한 metadata와 lock만 커밋 입력에 추가한다. 격리된 호출자가 SHA와 경로를 검증하게 한다. 누락, 변조, dirty/숨김 인덱스 및 lock 상태 오류를 실패로 처리한다.
4. 소유자와 사용자의 별도 승인 후 새 Gradle 사용자 홈과 JDK 17을 사용한다. WFF2–5 Debug/Release, 격리 flavor/basic/no-bundle/material, Lint 및 Domain clean test를 수행한다. APK 직접 검사, validator, 서명, 메모리와 SBOM을 대조한다. 연결 테스트는 승인된 환경에서 별도로 수행한다.
5. 배포자·권고·라이선스·SBOM·격리 입력을 독립 검수한다. 검수 후 적용된 정확한 SHA에서 main 회귀를 검증한다.

[Gradle 검증](https://docs.gradle.org/current/userguide/dependency_verification.html) / [Gradle 잠금](https://docs.gradle.org/current/userguide/dependency_locking.html). 기존 R08은 197 configs와 6개 lock의 격리 파일럿이었다. 파일럿의 변조 및 lock 누락 거부 증거를 재사용했다. 제품 적용 검증은 NOT RUN이다.

| 게이트 | 이 회차 판정 | 근거 |
|---|---|---|
| G0 | PARTIAL | 정본/CI/PR PRE-FLIGHT 대조 완료. 로컬 독립 실행 조건 BLOCKED |
| G1 | PARTIAL | 제품 변경 없음. 공식 두 자산 메타데이터와 로컬 marker 경로 확인. 원본 바이트 검증 미완료 |
| G2 | PASS (좁은 범위) | 로컬 캐시 읽기 1건, 메모리 내 오류 2건 거부. 기존 정책 시험 기준 유지 |
| G3 | 기준 CI SUCCESS / 로컬 NOT RUN | 기준 402×3 및 문서 7. 새 Gradle/OSV/실기기 실행 없음. R12/R17 기존 adverse 게이트 FAIL 유지 |
| G4 | PARTIAL | 공식 JAR 자산 해시 및 로컬 marker 해시 일치. 신뢰 승인, 라이선스, release SBOM 및 full graph 미완료 |
| G5 | 자기 재검토 | 보고서와 기준 SHA, 레코드, 원시 CI 대조. GPT 독립 검수 대기 |
| G6 | PARTIAL | 원본 ZIP API 크기/해시 및 기존 로그 대조. 로컬 ZIP CRC, JAR 바이트, 원래 CI 전송 경로 미확인 |
| G7 | 보고서 제출 | 별도 증거 브랜치에 이 문서만 제출 대상으로 삼았다. 중앙 문서 갱신은 총괄에 위임 |

재개 첫 명령: `git -c credential.interactive=never ls-remote https://github.com/scarlel96-design/AURA-Ultra.git refs/heads/main`. 다음 환경에서는 exit 0과 정확한 main SHA를 확인한다. 기존 캐시와 독립된 네트워크에서 공식 릴리스 URL의 홉을 검토한다. 승인 범위의 홉에서만 지정 크기·SHA-256을 검사한다. 원본 ZIP 두 개의 CRC와 인벤토리 행을 확인한다. 과거 CI의 marker 경로는 그 실행의 증거가 있을 때만 확정한다. DNS 실패가 반복되면 전체 재수집 없이 중단한다.

중앙 기록 갱신 제안: CODEX-F03 제한 검토 종료, GitHub 공식 해시 2/2 및 로컬 marker Portal 경로 확보, 원본 배포 검증 및 채택 BLOCKED. F03 PARTIAL, 개발 감사 14/16, 제품 NO-GO, 기존 PR HOLD 유지. F04/C01/GPT-07 미착수. 이 문서의 롤백은 증거 브랜치의 단일 문서 커밋을 되돌리는 것으로 충분하다.
