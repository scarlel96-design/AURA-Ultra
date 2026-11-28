"""Diagnose exact unresolved artifacts without changing trusted metadata."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import urllib.request
import http.client

from audit_provenance_priority import archive, sha, MAX_ARTIFACT
from audit_published_checksums import artifact_path, CENTRAL, PORTAL, allowed_url, RestrictedRedirect
from audit_dependency_review import write_json

R16 = "86c0fefe4ed174a0d265254811dd78b5e1c1b2c144a30708e8d7f9b8560eee23"
R10 = "490c5d7ce76a024e53ddd0b4553687cd95f874933a94cfe0fdd90dc7f8220096"
SOURCE = "5c1df1f4ccf989354ed09b616ed2d32243383884"
COMPILER_LIMIT = 256 * 1024 * 1024
MARKER_LIMIT = 64 * 1024
CHUNK = 1024 * 1024
TARGETS = {
    ("org.jetbrains.kotlin:kotlin-compiler-embeddable:2.2.10", "kotlin-compiler-embeddable-2.2.10.jar"),
    ("org.jetbrains.kotlin:kotlin-compiler-embeddable:2.4.0", "kotlin-compiler-embeddable-2.4.0.jar"),
    ("org.jetbrains.kotlin.jvm:org.jetbrains.kotlin.jvm.gradle.plugin:2.4.21",
     "org.jetbrains.kotlin.jvm.gradle.plugin-2.4.21.pom"),
}


def consume(response, limit, retain=False, clock=time.monotonic):
    start = clock()
    if response.headers.get("Content-Encoding", "identity").lower() != "identity":
        raise ValueError("Unexpected content encoding")
    lengths = response.headers.get_all("Content-Length") or []
    if len(lengths) > 1 or (lengths and not re.fullmatch(r"[0-9]+", lengths[0])):
        raise ValueError("Invalid content length")
    declared = int(lengths[0]) if lengths else None
    if declared is not None and (declared <= 0 or declared > limit):
        raise ValueError("Content length outside bound")
    digest = hashlib.sha256()
    size = 0
    parts = []
    while True:
        if clock() - start > 120:
            raise TimeoutError("Transfer deadline exceeded")
        chunk = response.read(min(CHUNK, limit - size + 1))
        if not chunk:
            break
        size += len(chunk)
        if size > limit:
            raise ValueError("Stream exceeds bound")
        digest.update(chunk)
        if retain:
            parts.append(chunk)
    if not size or (declared is not None and size != declared):
        raise ValueError("Empty or truncated response")
    return {"bytes": size, "declaredBytes": declared, "sha256": digest.hexdigest()}, b"".join(parts)


def retrieve(url, limit, retain=False):
    if not allowed_url(url):
        raise ValueError("Unapproved repository")
    request = urllib.request.Request(url, headers={"Accept-Encoding": "identity"})
    with urllib.request.build_opener(RestrictedRedirect()).open(request, timeout=20) as response:
        if not allowed_url(response.geturl()) or response.status != 200:
            raise ValueError("Unapproved final source or HTTP status")
        result, body = consume(response, limit, retain)
        result.update(finalSource=response.geturl(), http=response.status)
        return result, body


def attempt(row, base, limit, expected, output, retain=False, reader=retrieve):
    url = base + artifact_path(row).removesuffix(".sha256")
    r = {"source": url, "expectedSha256": expected, "trust": "UNREVIEWED", "status": "UNAVAILABLE"}
    try:
        facts, body = reader(url, limit, retain)
        r.update(facts)
        r["status"] = "MATCH" if facts["sha256"] == expected else "MISMATCH"
        if retain:
            if sha(body) != facts["sha256"]:
                raise ValueError("Retained bytes differ from streamed digest")
            (output / (facts["sha256"] + ".pom")).write_bytes(body)
        r["priorReaderLimitExceeded"] = facts["bytes"] > MAX_ARTIFACT
    except (OSError, ValueError, http.client.HTTPException) as exc:
        r.update(status="UNAVAILABLE", error=type(exc).__name__, reason=str(exc)[:300],
                 http=getattr(exc, "code", None))
    return r


def select(rows, results):
    expected = {(r["coordinate"], r["artifact"]): r for r in rows}
    actual = {(r["coordinate"], r["artifact"]): r for r in results}
    if len(rows) != 392 or len(results) != 392 or len(expected) != 392 or expected.keys() != actual.keys():
        raise ValueError("R16 coverage mismatch")
    adverse = set()
    for key, row in expected.items():
        artifact_path(row)
        prior = actual[key]
        if prior["trust"] != "UNREVIEWED" or prior["expectedSha256"] != row["sha256"][0]:
            raise ValueError("R16 digest or trust mismatch")
        if prior["bytesStatus"] != "MATCH":
            adverse.add(key)
        elif prior["actualSha256"] != row["sha256"][0]:
            raise ValueError("False prior match")
    if adverse != TARGETS:
        raise ValueError("Unexpected unresolved identities")
    return [expected[k] for k in sorted(adverse)]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--r16", required=True, type=Path)
    p.add_argument("--r10", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    with archive(a.r16, R16) as z:
        s = json.loads(z.read("summary.json"))
        if s["sourceCommit"] != SOURCE or s["trust"] != "UNREVIEWED":
            raise ValueError("Wrong R16 evidence")
        rows = select(json.loads(z.read("remaining-input.json")), json.loads(z.read("remaining-results.json")))
    with archive(a.r10, R10) as z:
        historical = {CENTRAL: sha(z.read("central.pom")), PORTAL: sha(z.read("portal.pom"))}
    a.output.mkdir(parents=True, exist_ok=False)
    results = []
    for row in rows:
        expected = row["sha256"][0]
        r = {"coordinate": row["coordinate"], "artifact": row["artifact"],
             "expectedSha256": expected, "trust": "UNREVIEWED"}
        if row["artifact"].endswith(".jar"):
            r["routes"] = [attempt(row, CENTRAL, COMPILER_LIMIT, expected, a.output)]
            r["status"] = r["routes"][0]["status"]
        else:
            if historical[PORTAL] != expected or historical[CENTRAL] == expected:
                raise ValueError("Historical marker hashes do not identify separate routes")
            r["routes"] = [attempt(row, base, MARKER_LIMIT, historical[base], a.output, True)
                           for base in (CENTRAL, PORTAL)]
            r["status"] = ("DISTINCT_ROUTES_MATCH_HISTORY"
                           if all(x["status"] == "MATCH" for x in r["routes"]) else "UNRESOLVED")
            r["originalGradleRoute"] = "UNPROVEN"
        results.append(r)
    write_json(a.output / "exception-results.json", results)
    summary = {"sourceCommit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
               "trust": "UNREVIEWED", "approval": "BLOCKED",
               "results": [{"coordinate": r["coordinate"], "status": r["status"]} for r in results]}
    write_json(a.output / "summary.json", summary)
    print("F03_R17", json.dumps(results, sort_keys=True), flush=True)
    if any(r["status"] not in ("MATCH", "DISTINCT_ROUTES_MATCH_HISTORY") for r in results):
        raise SystemExit("Incomplete route or byte evidence")


if __name__ == "__main__":
    main()
