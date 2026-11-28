"""Collect exact artifact and signature evidence without granting trust."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile
import xml.etree.ElementTree as ET

from audit_published_checksums import artifact_path, repositories, allowed_url, RestrictedRedirect
from audit_dependency_review import parse_pom, write_json

INPUTS = {
    "android": "bde7f9ab10ed03882457289e963d90ab6ae8e914b67ec4bf6d68b3d9a9a8fe19",
    "domain": "4b85c4b32d951c09a3ac1b0cc8e110085038d37a3c1673ceca204d563e6202b9",
    "review": "f55f406ad0f9e9ea6f632ae24ab8dd02fd3410c23d8cb8ccb02c3b2563dec815",
    "candidate": "83abe7be0c76b2bf37982676567f0692d80690baacad566d6587c7c0d5415d18",
}
NS = {"v": "https://schema.gradle.org/dependency-verification"}
MAX_ARTIFACT = 128 * 1024 * 1024
MAX_SIGNATURE = 64 * 1024
MAX_NOTICE = 512 * 1024


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def archive(path, expected):
    if sha(path.read_bytes()) != expected:
        raise ValueError("Archive digest mismatch")
    z = zipfile.ZipFile(path)
    if len(z.namelist()) != len(set(z.namelist())) or z.testzip():
        z.close()
        raise ValueError("Invalid archive")
    return z


def inventory(z, source):
    summary = json.loads(z.read("summary.json"))
    raw = z.read("verification-metadata.UNREVIEWED.xml")
    if (summary["sourceCommit"] != source or summary["trust"] != "UNREVIEWED"
            or any(summary["commands"].values()) or sha(raw) != summary["metadata"]["sha256"]):
        raise ValueError("Inventory scope or metadata mismatch")
    rows = {}
    for r in json.loads(z.read("artifacts.json")):
        artifact_path(r)
        key = (r["coordinate"], r["artifact"])
        if key in rows:
            raise ValueError("Duplicate artifact")
        rows[key] = r
    xml = {}
    for c in ET.fromstring(raw).findall("./v:components/v:component", NS):
        coord = ":".join(c.attrib[k] for k in ("group", "name", "version"))
        for a in c.findall("v:artifact", NS):
            k = (coord, a.attrib["name"])
            if k in xml:
                raise ValueError("Duplicate XML artifact")
            xml[k] = [v.attrib["value"] for v in a.findall("v:sha256", NS)]
    if xml != {k: r["sha256"] for k, r in rows.items()}:
        raise ValueError("XML and JSON mismatch")
    return rows


def merge_row(target, key, row):
    if key in target and target[key]["sha256"] != row["sha256"]:
        raise ValueError("Conflicting artifact digests")
    target[key] = row


def read_bytes(url, limit):
    if not allowed_url(url):
        raise ValueError("Unapproved source")
    with urllib.request.build_opener(RestrictedRedirect()).open(url, timeout=12) as response:
        if not allowed_url(response.geturl()):
            raise ValueError("Unapproved final source")
        raw = response.read(limit + 1)
        if not raw or len(raw) > limit:
            raise ValueError("Empty or oversized response")
        return raw, response.geturl()


def notices(raw):
    result = []
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate JAR entries")
        for info in z.infolist():
            name = info.filename.upper()
            leaf = name.rsplit("/", 1)[-1]
            if info.is_dir() or not leaf.startswith(("LICENSE", "NOTICE", "COPYING")):
                continue
            if "/" in name and not name.startswith("META-INF/"):
                continue
            if len(result) >= 40 or info.file_size > MAX_NOTICE:
                raise ValueError("Notice limits exceeded")
            with z.open(info) as f:
                data = f.read(MAX_NOTICE + 1)
            if len(data) > MAX_NOTICE:
                raise ValueError("Oversized notice")
            result.append({"name": info.filename, "bytes": len(data), "sha256": sha(data)})
    return result


def collect(row, output, reader=read_bytes):
    path = artifact_path(row).removesuffix(".sha256")
    expected = row["sha256"][0]
    result = {"coordinate": row["coordinate"], "artifact": row["artifact"],
              "expectedSha256": expected, "trust": "UNREVIEWED", "attempts": [],
              "bytesStatus": "UNAVAILABLE", "signatureStatus": "NOT_CHECKED",
              "licenseStatus": "NOT_CHECKED"}
    for base in repositories(row["coordinate"]):
        url = base + path
        try:
            raw, final = reader(url, MAX_ARTIFACT)
            if not allowed_url(final):
                raise ValueError("Unapproved final source")
        except (OSError, ValueError) as exc:
            result["attempts"].append({"url": url, "error": type(exc).__name__,
                                       "http": getattr(exc, "code", None)})
            continue
        result.update(source=final, actualSha256=sha(raw), bytes=len(raw))
        if result["actualSha256"] != expected:
            result["bytesStatus"] = "MISMATCH"
            return result
        result["bytesStatus"] = "MATCH"
        try:
            sig, sig_url = reader(url + ".asc", MAX_SIGNATURE)
            if not allowed_url(sig_url) or not sig.strip().startswith(b"-----BEGIN PGP SIGNATURE-----"):
                raise ValueError("Unexpected signature response")
            # Preserve the signature, but do not infer signer identity or validity.
            name = sha(sig) + ".asc"
            target = output / name
            # Each worker may see identical signature bytes; exclusive write.
            try:
                with target.open("xb") as f:
                    f.write(sig)
            except FileExistsError:
                pass
            result.update(signatureStatus="PRESENT_UNVERIFIED", signatureSource=sig_url,
                          signatureSha256=sha(sig), signatureFile=name)
        except (OSError, ValueError) as exc:
            result.update(signatureStatus="UNAVAILABLE_OR_INVALID",
                          signatureError=type(exc).__name__, signatureHttp=getattr(exc, "code", None))
        try:
            if row["artifact"].endswith(".pom"):
                declared = parse_pom(raw)
                result.update(licenseStatus="DIRECT_DECLARATION" if declared else "NO_DIRECT_DECLARATION",
                              declarations=declared)
            elif row["artifact"].endswith(".jar"):
                entries = notices(raw)
                result.update(licenseStatus="NOTICE_PRESENT" if entries else "NO_NOTICE_FOUND",
                              notices=entries)
            else:
                result["licenseStatus"] = "NOT_APPLICABLE_TO_FILE"
        except (OSError, ValueError, ET.ParseError, zipfile.BadZipFile, RuntimeError) as exc:
            result.update(licenseStatus="UNKNOWN", licenseError=type(exc).__name__)
        return result
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in INPUTS:
        p.add_argument("--" + key, required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    base, sidecars = {}, {}
    for build in ("android", "domain"):
        with archive(getattr(a, build), INPUTS[build]) as z:
            rows = inventory(z, "e7dd34de38012410d057460b03a74e4c12378d1d")
            report = json.loads(z.read("published-checksums.json"))
            if report["trust"] != "UNREVIEWED":
                raise ValueError("Unexpected trust status")
            checks = {}
            for r in report["artifacts"]:
                k = (r["coordinate"], r["artifact"])
                if k in checks or k not in rows or r["sha256"] != rows[k]["sha256"][0]:
                    raise ValueError("Sidecar identity mismatch")
                if r["trust"] != "UNREVIEWED" or r["status"] not in ("MATCH", "UNAVAILABLE"):
                    raise ValueError("Unexpected sidecar status")
                if r["status"] == "MATCH" and r.get("publishedSha256") != r["sha256"]:
                    raise ValueError("Sidecar checksum mismatch")
                checks[k] = r
            if checks.keys() != rows.keys():
                raise ValueError("Incomplete sidecar evidence")
            for k, r in rows.items():
                merge_row(base, k, r)
                if k in sidecars and sidecars[k] != checks[k]:
                    raise ValueError("Conflicting sidecar evidence")
                sidecars[k] = checks[k]
    with archive(a.review, INPUTS["review"]) as z:
        osv = json.loads(z.read("osv-results.json"))
        licenses = json.loads(z.read("license-results.json"))
    if set(osv) != set(licenses) or set(osv) != {k[0] for k in base}:
        raise ValueError("Review coverage mismatch")
    with archive(a.candidate, INPUTS["candidate"]) as z:
        candidate = inventory(z, "a1158e8b430c5c7aa7eee437b1d70477e4649662")
        candidate_osv = json.loads(z.read("osv-results.json"))
    if not {k[0] for k in candidate} <= set(candidate_osv):
        raise ValueError("Candidate review coverage mismatch")
    queue = {}
    ledger = []
    for k, r in sorted(base.items()):
        ledger.append({"coordinate": k[0], "artifact": k[1], "sha256": r["sha256"][0],
                       "sidecar": sidecars[k]["status"], "license": licenses[k[0]]["status"],
                       "advisoryIds": osv[k[0]].get("ids", []), "trust": "UNREVIEWED"})
        if osv[k[0]]["status"] == "MATCH":
            merge_row(queue, k, r)
    for k, r in candidate.items():
        if candidate_osv[k[0]]["status"] == "MATCH":
            merge_row(queue, k, r)
    if len(ledger) != 664 or len(queue) != 48:
        raise ValueError("Unexpected ledger or priority size")
    a.output.mkdir(parents=True, exist_ok=False)
    write_json(a.output / "baseline-ledger.json", ledger)
    write_json(a.output / "priority-input.json", [queue[k] for k in sorted(queue)])
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda r: collect(r, a.output), [queue[k] for k in sorted(queue)]))
    write_json(a.output / "priority-results.json", results)
    summary = {"trust": "UNREVIEWED", "approval": "BLOCKED", "baseline": len(ledger),
               "priority": len(results), "bytes": dict(Counter(r["bytesStatus"] for r in results)),
               "signatures": dict(Counter(r["signatureStatus"] for r in results)),
               "licenses": dict(Counter(r["licenseStatus"] for r in results)),
               "sourceCommit": __import__("subprocess").check_output(
                   ["git", "rev-parse", "HEAD"], text=True).strip()}
    write_json(a.output / "summary.json", summary)
    print("F03_R13", json.dumps(summary, sort_keys=True), flush=True)
    if any(r["bytesStatus"] != "MATCH" for r in results):
        raise SystemExit("Incomplete byte corroboration; no approval")


if __name__ == "__main__":
    main()
