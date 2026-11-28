"""Collect exact advisory records and compare the disputed marker POM; no trust promotion."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import urllib.request
import zipfile
from audit_dependency_review import NoRedirect, read_pom, write_json
from audit_published_checksums import CENTRAL, GOOGLE, PORTAL

DIGEST = "f55f406ad0f9e9ea6f632ae24ab8dd02fd3410c23d8cb8ccb02c3b2563dec815"
EXPECTED = "c250047db1cbab6f0d801c44615172892bd3892aa9bc9cc8ef9ecaa4149fda67"
MARKER = "org/jetbrains/kotlin/jvm/org.jetbrains.kotlin.jvm.gradle.plugin/2.4.21/org.jetbrains.kotlin.jvm.gradle.plugin-2.4.21.pom"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def advisory(identifier):
    if not re.fullmatch(r"GHSA-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}", identifier):
        raise ValueError("Unexpected advisory ID")
    url = "https://api.osv.dev/v1/vulns/" + identifier
    try:
        with urllib.request.build_opener(NoRedirect()).open(url, timeout=15) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError("Oversized advisory")
        data = json.loads(raw)
        if data.get("id") != identifier or not isinstance(data.get("affected"), list):
            raise ValueError("Advisory identity/affected mismatch")
        return {"id": identifier, "status": "RETRIEVED", "source": url, "sha256": sha(raw), "record": data}
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        return {"id": identifier, "status": "UNKNOWN", "source": url, "error": type(exc).__name__, "http": getattr(exc, "code", None)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--review", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if sha(a.review.read_bytes()) != DIGEST:
        raise ValueError("Review archive hash mismatch")
    with zipfile.ZipFile(a.review) as z:
        if z.testzip() or len(z.namelist()) != len(set(z.namelist())):
            raise ValueError("Invalid review archive")
        rows = json.loads(z.read("osv-results.json"))
        summary = json.loads(z.read("summary.json"))
        ids = sorted({i for r in rows.values() for i in r.get("ids", [])})
        if len(rows) != 373 or len(ids) != 52 or ids != sorted(summary["advisoryIds"]):
            raise ValueError("Review inventory mismatch")
    a.output.mkdir(parents=True, exist_ok=False)
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(advisory, ids))
    write_json(a.output / "advisories.json", records)
    # Preserve each exact repository response, not just the first match.
    markers = []
    for name, base in (("central", CENTRAL), ("portal", PORTAL), ("google", GOOGLE)):
        url = base + MARKER
        try:
            raw, final = read_pom(url)
            (a.output / (name + ".pom")).write_bytes(raw)
            markers.append({"repository": name, "url": url, "source": final, "sha256": sha(raw),
                            "bytes": len(raw), "status": "MATCH" if sha(raw) == EXPECTED else "MISMATCH"})
        except (OSError, ValueError) as exc:
            markers.append({"repository": name, "url": url, "status": "UNAVAILABLE",
                            "error": type(exc).__name__, "http": getattr(exc, "code", None)})
    write_json(a.output / "marker-results.json", markers)
    write_json(a.output / "component-advisory-map.json", {k: v for k, v in rows.items() if v.get("ids")})
    result = {"advisoriesRetrieved": sum(r["status"] == "RETRIEVED" for r in records),
              "advisoriesExpected": len(ids), "markerResults": markers, "trust": "UNREVIEWED"}
    write_json(a.output / "summary.json", result)
    print("F03_R10", json.dumps(result, sort_keys=True), flush=True)
    # Evidence retrieval is not a security approval.
    if result["advisoriesRetrieved"] != len(ids) or not any(r["status"] == "MATCH" for r in markers):
        raise SystemExit("Incomplete review evidence")


if __name__ == "__main__":
    main()
