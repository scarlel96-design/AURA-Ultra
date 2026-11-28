"""Collect remaining baseline bytes and license evidence without granting trust."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess

from audit_provenance_priority import archive, collect, sha
from audit_published_checksums import artifact_path
from audit_dependency_review import write_json

DIGEST = "004cbfb19bb784d6744c6974fc8c0f5d42015078689f16ee8d131003c436e677"
SOURCE = "466fc5f00064b4b1436aebe67a5c8e5168dcac4d"


def identity(row):
    return row["coordinate"], row["artifact"]


def row_from_ledger(row):
    converted = {"coordinate": row["coordinate"], "artifact": row["artifact"],
                 "sha256": [row["sha256"]], "trust": row["trust"]}
    artifact_path(converted)
    return converted


def unique_index(rows):
    index = {identity(row): row for row in rows}
    if len(index) != len(rows):
        raise ValueError("Duplicate artifact identity")
    return index


def select(ledger, priority, prior):
    baseline = unique_index(ledger)
    selected = unique_index(priority)
    results = unique_index(prior)
    if not baseline or selected.keys() != results.keys():
        raise ValueError("Incomplete prior coverage")
    for key, row in baseline.items():
        row_from_ledger(row)
        if row["sidecar"] not in ("MATCH", "UNAVAILABLE"):
            raise ValueError("Unexpected baseline status")
    for key, row in selected.items():
        artifact_path(row)
        prev = results[key]
        if (prev["trust"] != "UNREVIEWED" or prev["bytesStatus"] != "MATCH"
                or prev["expectedSha256"] != row["sha256"][0]
                or prev["actualSha256"] != row["sha256"][0]):
            raise ValueError("Prior byte evidence mismatch")
        if key in baseline and baseline[key]["sha256"] != row["sha256"][0]:
            raise ValueError("Baseline and priority digest differ")
    remaining = [row_from_ledger(row) for key, row in baseline.items()
                 if row["sidecar"] == "UNAVAILABLE" and key not in selected]
    # Group adjacent publisher requests and prioritize executable archives.
    remaining.sort(key=lambda r: (r["coordinate"].split(":")[0],
                                  not r["artifact"].endswith(".jar"), identity(r)))
    return remaining


def reconcile(rows, results):
    expected = unique_index(rows)
    actual = unique_index(results)
    if expected.keys() != actual.keys():
        raise ValueError("Collection coverage mismatch")
    for key, r in actual.items():
        if r["trust"] != "UNREVIEWED" or r["expectedSha256"] != expected[key]["sha256"][0]:
            raise ValueError("Collection trust or digest mismatch")
        if r["bytesStatus"] not in ("MATCH", "MISMATCH", "UNAVAILABLE"):
            raise ValueError("Unexpected byte status")
        if r["bytesStatus"] == "MATCH" and r.get("actualSha256") != r["expectedSha256"]:
            raise ValueError("False byte match")
    return actual


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    with archive(a.input, DIGEST) as z:
        summary = json.loads(z.read("summary.json"))
        if summary["sourceCommit"] != SOURCE or summary["trust"] != "UNREVIEWED":
            raise ValueError("Wrong R13 evidence")
        ledger = json.loads(z.read("baseline-ledger.json"))
        priority = json.loads(z.read("priority-input.json"))
        prior = json.loads(z.read("priority-results.json"))
        for r in prior:
            name = r["signatureFile"]
            if name != r["signatureSha256"] + ".asc" or sha(z.read(name)) != r["signatureSha256"]:
                raise ValueError("Prior signature hash mismatch")
    rows = select(ledger, priority, prior)
    if (len(ledger) != 664 or len(priority) != 48 or len(rows) != 392
            or Counter(r["sidecar"] for r in ledger) != {"MATCH": 234, "UNAVAILABLE": 430}):
        raise ValueError("Unexpected inventory counts")
    a.output.mkdir(parents=True, exist_ok=False)
    write_json(a.output / "remaining-input.json", rows)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda r: collect(r, a.output), rows))
    actual = reconcile(rows, results)
    for r in results:
        if r["signatureStatus"] == "PRESENT_UNVERIFIED":
            name = r["signatureFile"]
            if name != r["signatureSha256"] + ".asc" or sha((a.output / name).read_bytes()) != r["signatureSha256"]:
                raise ValueError("Collected signature hash mismatch")
    write_json(a.output / "remaining-results.json", results)
    groups = defaultdict(list)
    combined = []
    old = unique_index(prior)
    for r in ledger:
        key = identity(r)
        evidence = actual.get(key, old.get(key))
        byte_status = evidence["bytesStatus"] if evidence else "SIDECAR_ONLY"
        combined.append(dict(r, byteRecheck=byte_status,
                             signatureEvidence=evidence["signatureStatus"] if evidence else "NOT_CHECKED",
                             fileLicenseEvidence=evidence["licenseStatus"] if evidence else "NOT_CHECKED"))
        groups[r["coordinate"].split(":")[0]].append(combined[-1])
    write_json(a.output / "combined-ledger.json", combined)
    write_json(a.output / "group-summary.json", {
        g: {"count": len(rs), "byteRecheck": dict(Counter(r["byteRecheck"] for r in rs)),
            "signatureEvidence": dict(Counter(r["signatureEvidence"] for r in rs)),
            "fileLicenseEvidence": dict(Counter(r["fileLicenseEvidence"] for r in rs))}
        for g, rs in sorted(groups.items())})
    report = {"sourceCommit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "inputSha256": DIGEST, "trust": "UNREVIEWED", "approval": "BLOCKED",
              "remaining": len(results), "baseline": len(combined),
              "bytes": dict(Counter(r["bytesStatus"] for r in results)),
              "signatures": dict(Counter(r["signatureStatus"] for r in results)),
              "licenses": dict(Counter(r["licenseStatus"] for r in results)),
              "baselineByteRecheck": dict(Counter(r["byteRecheck"] for r in combined)),
              "baselineSignatureEvidence": dict(Counter(r["signatureEvidence"] for r in combined)),
              "baselineFileLicenseEvidence": dict(Counter(r["fileLicenseEvidence"] for r in combined))}
    write_json(a.output / "summary.json", report)
    print("F03_R16", json.dumps(report, sort_keys=True), flush=True)
    if any(r["bytesStatus"] != "MATCH" for r in results):
        raise SystemExit("Incomplete byte corroboration; no approval")


if __name__ == "__main__":
    main()
