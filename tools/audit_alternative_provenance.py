"""Collect alternative provenance evidence without approving dependency trust."""
import argparse
import base64
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import zipfile

from audit_provenance_priority import archive, sha, read_bytes, MAX_ARTIFACT
from audit_published_checksums import artifact_path, CENTRAL
from audit_dependency_review import write_json

R13 = "004cbfb19bb784d6744c6974fc8c0f5d42015078689f16ee8d131003c436e677"
R14 = "a51a289088344da0ffd17d7d403372293f9e8f5c2c3bdfefbc0c106bf4536e88"
SOURCE = "be0bd7b2be4c5ff409c47794c24425f371b71c0a"
APACHE = "https://archive.apache.org/dist/httpcomponents/httpclient/binary/httpcomponents-client-4.5.6-bin.zip"
APACHE_SHA512 = "457ccd2bd60d34b8f9b3f7907965840285867b2369dbcf5531c7f552d103a5b758eab431fe4d801ff2ea766104b5077b6bde788be6c800a741f2a409326c99b8"
JDOM = "https://www.jdom.org/dist/binary/archive/jdom-2.0.6.zip"
GOOGLE = "https://android.googlesource.com/platform/frameworks/support/+/e40b1c92b7caf8f4a090cc5ce3a29c273beb4bb4/gradle/verification-metadata.xml?format=TEXT"
JOSE = "https://bitbucket.org/b_c/jose4j/raw/jose4j-0.9.5/pom.xml"
GUAVA_FPR = "BDB5FA4FE719D787FB3D3197F6D4A1D411E9D1AE"
JOSE_FPR = "3051D45031E13516A6E8FAFF280D66A55F5316C5"
NS = {"v": "https://schema.gradle.org/dependency-verification"}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Redirect refused")


def official_bytes(url, limit):
    if url not in (APACHE, APACHE + ".sha512", JDOM, GOOGLE, JOSE):
        raise ValueError("Unapproved official source")
    with urllib.request.build_opener(NoRedirect()).open(url, timeout=20) as r:
        data = r.read(limit + 1)
        if r.geturl() != url or not data or len(data) > limit:
            raise ValueError("Unexpected official response")
        return data


def checksum512(raw, filename):
    text = raw.decode("ascii").strip()
    m = re.fullmatch(r"([a-fA-F0-9]{128})(?:[ \t]+\*?([A-Za-z0-9_.-]+))?", text)
    if not m or (m[2] is not None and m[2] != filename):
        raise ValueError("Invalid SHA-512 sidecar")
    return m[1].lower()


def central512(row, reader=read_bytes):
    url = CENTRAL + artifact_path(row).removesuffix(".sha256")
    r = {"coordinate": row["coordinate"], "artifact": row["artifact"],
         "expectedSha256": row["sha256"][0], "source": url + ".sha512",
         "status": "UNAVAILABLE", "trust": "UNREVIEWED"}
    try:
        side, source = reader(url + ".sha512", 512)
        expected = checksum512(side, row["artifact"])
        raw, artifact_source = reader(url, MAX_ARTIFACT)
        r.update(source=source, artifactSource=artifact_source,
                 publishedSha512=expected, actualSha512=hashlib.sha512(raw).hexdigest(),
                 actualSha256=sha(raw))
        r["status"] = ("SAME_REPOSITORY_MATCH" if r["actualSha512"] == expected
                       and r["actualSha256"] == r["expectedSha256"] else "MISMATCH")
    except (OSError, ValueError) as exc:
        r.update(error=type(exc).__name__, http=getattr(exc, "code", None))
    return r


def member_hashes(raw, filenames):
    result = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or len(names) > 10000:
            raise ValueError("Invalid distribution entry list")
        for name in filenames:
            entries = []
            for info in z.infolist():
                if info.is_dir() or info.filename.rsplit("/", 1)[-1] != name:
                    continue
                if info.file_size > MAX_ARTIFACT:
                    raise ValueError("Oversized distribution member")
                with z.open(info) as f:
                    data = f.read(MAX_ARTIFACT + 1)
                if len(data) > MAX_ARTIFACT:
                    raise ValueError("Oversized member bytes")
                entries.append({"path": info.filename, "sha256": sha(data)})
            result[name] = entries
    return result


def distribution(url, rows, output, expected_sha512=None, reader=official_bytes):
    r = {"source": url, "status": "UNAVAILABLE", "trust": "UNREVIEWED", "members": {}}
    try:
        if expected_sha512:
            side = reader(url + ".sha512", 512)
            published = checksum512(side, url.rsplit("/", 1)[-1])
            if published != expected_sha512:
                raise ValueError("Published distribution digest differs from reviewed value")
        raw = reader(url, MAX_ARTIFACT)
        actual = hashlib.sha512(raw).hexdigest()
        r.update(sha512=actual, sha256=sha(raw), bytes=len(raw),
                 checksumStatus="MATCH" if expected_sha512 == actual else
                 "MISMATCH" if expected_sha512 else "NO_REVIEWED_CHECKSUM")
        if expected_sha512 and actual != expected_sha512:
            r["status"] = "MISMATCH"
            return r
        filenames = [a["artifact"] for a in rows]
        # Some historical JDOM distributions use a different basename.
        aliases = ["jdom-2.0.6.jar"] if url == JDOM else []
        members = member_hashes(raw, filenames + aliases)
        for a in rows:
            entries = members[a["artifact"]]
            if url == JDOM and a["artifact"] == "jdom2-2.0.6.jar":
                entries = entries + members["jdom-2.0.6.jar"]
            r["members"][a["artifact"]] = {"entries": entries, "expectedSha256": a["sha256"][0],
                "status": "ABSENT" if not entries else "EXACT_MATCH" if len(entries) == 1
                and entries[0]["sha256"] == a["sha256"][0] else "DIFFERENT_OR_AMBIGUOUS"}
        r["status"] = "RETRIEVED"
        (output / (sha(raw) + ".zip")).write_bytes(raw)
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as exc:
        r.update(error=type(exc).__name__, http=getattr(exc, "code", None))
    return r


def xml_root(raw):
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("DTD/entity refused")
    return ET.fromstring(raw)


def guava_binding(raw):
    root = xml_root(base64.b64decode(raw, validate=False))
    if root.tag != "{https://schema.gradle.org/dependency-verification}verification-metadata":
        raise ValueError("Unexpected Google verification document")
    for k in root.findall("./v:configuration/v:trusted-keys/v:trusted-key", NS):
        if k.get("id") == GUAVA_FPR and (k.get("group") == "com.google.guava" or
                any(t.get("group") == "com.google.guava" for t in k.findall("v:trusting", NS))):
            return "GOOGLE_CONSUMER_KEY_BINDING"
    return "NOT_FOUND"


def jose_binding(raw):
    root = xml_root(raw)
    ns = {"p": "http://maven.apache.org/POM/4.0.0"}
    if root.tag != "{http://maven.apache.org/POM/4.0.0}project":
        raise ValueError("Unexpected POM")
    found = [n.text.strip().upper() for plugin in root.findall(".//p:plugin", ns)
             if plugin.findtext("p:artifactId", "", ns) == "maven-gpg-plugin"
             for n in plugin.findall(".//p:keyname", ns) if n.text]
    return "RELEASE_SOURCE_KEYNAME_MATCH" if JOSE_FPR in found else "NOT_FOUND"


def binding(url, parser, out):
    r = {"source": url, "status": "UNAVAILABLE", "trust": "UNREVIEWED"}
    try:
        raw = official_bytes(url, 4 * 1024 * 1024)
        r.update(sha256=sha(raw), status=parser(raw))
        (out / (sha(raw) + ".txt")).write_bytes(raw)
    except (OSError, ValueError, ET.ParseError) as exc:
        r.update(error=type(exc).__name__, http=getattr(exc, "code", None))
    return r


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--r13", type=Path, required=True)
    p.add_argument("--r14", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    with archive(a.r13, R13) as z:
        rows = json.loads(z.read("priority-input.json"))
    with archive(a.r14, R14) as z:
        summary = json.loads(z.read("summary.json"))
        prev = json.loads(z.read("signature-results.json"))
    if summary["sourceCommit"] != SOURCE or summary["trust"] != "UNREVIEWED":
        raise ValueError("Wrong R14 evidence")
    index = {(r["coordinate"], r["artifact"]): r for r in prev}
    if len(rows) != 48 or len(index) != len(prev) or len(index) != 48:
        raise ValueError("Unexpected priority inventory")
    weak = []
    for row in rows:
        artifact_path(row)
        prior = index.pop((row["coordinate"], row["artifact"]))
        if prior["expectedSha256"] != row["sha256"][0] or prior["actualSha256"] != row["sha256"][0]:
            raise ValueError("R14 identity mismatch")
        if row["coordinate"].split(":")[0] in ("io.netty", "org.apache.httpcomponents", "org.jdom"):
            if prior["crypto"] != "NOT_VALIDATED":
                raise ValueError("Unexpected weak signature scope")
            weak.append(row)
    if index or len(weak) != 28:
        raise ValueError("Incomplete priority scope")
    a.output.mkdir(parents=True, exist_ok=False)
    with ThreadPoolExecutor(max_workers=4) as pool:
        checks = list(pool.map(central512, weak))
    write_json(a.output / "sha512-results.json", checks)
    distributions = [
        distribution(APACHE, [r for r in weak if r["coordinate"].startswith("org.apache.httpcomponents:")], a.output, APACHE_SHA512),
        distribution(JDOM, [r for r in weak if r["coordinate"].startswith("org.jdom:")], a.output),
    ]
    write_json(a.output / "distribution-results.json", distributions)
    bindings = {"guava": binding(GOOGLE, guava_binding, a.output),
                "jose4j": binding(JOSE, jose_binding, a.output)}
    write_json(a.output / "binding-results.json", bindings)
    result = {"sourceCommit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "trust": "UNREVIEWED", "approval": "BLOCKED",
              "sha512": dict(Counter(r["status"] for r in checks)),
              "distributions": [{k: v for k, v in d.items() if k != "members"} for d in distributions],
              "bindings": {k: v["status"] for k, v in bindings.items()}}
    write_json(a.output / "summary.json", result)
    print("F03_R15", json.dumps(result, sort_keys=True), flush=True)
    # Collection success is not a trust approval. Any mismatch remains adverse.
    if any(r["status"] == "MISMATCH" for r in checks + distributions):
        raise SystemExit("Alternative evidence mismatch; no approval")


if __name__ == "__main__":
    main()
