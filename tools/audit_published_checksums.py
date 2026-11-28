"""Compare provisional SHA-256 values with published repository sidecars.

A match corroborates the retrieved bytes; it does not prove publisher identity.
Do not promote any generated metadata to a trusted baseline.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

CENTRAL = "https://repo.maven.apache.org/maven2/"
GOOGLE = "https://dl.google.com/dl/android/maven2/"
PORTAL = "https://plugins.gradle.org/m2/"
HOSTS = {"repo.maven.apache.org", "dl.google.com", "maven.google.com",
         "plugins.gradle.org", "plugins-artifacts.gradle.org", "repo1.maven.org"}
PART = re.compile(r"[A-Za-z0-9_+.-]+")
HASH = re.compile(r"[0-9a-fA-F]{64}")


def valid_part(value):
    return isinstance(value, str) and PART.fullmatch(value) and value not in (".", "..")


def artifact_path(row):
    fields = row["coordinate"].split(":")
    if len(fields) != 3 or not all(valid_part(x) for x in fields):
        raise ValueError("Invalid component coordinate")
    group, name, version = fields
    if not all(valid_part(x) for x in group.split(".")):
        raise ValueError("Invalid group path")
    artifact = row["artifact"]
    if not valid_part(artifact):
        raise ValueError("Invalid artifact name")
    if row.get("trust") != "UNREVIEWED":
        raise ValueError("Unexpected inventory trust classification")
    hashes = row["sha256"]
    if len(hashes) != 1 or not HASH.fullmatch(hashes[0]):
        raise ValueError("Require one exact provisional SHA-256")
    return "/".join([*group.split("."), name, version, artifact]) + ".sha256"


def allowed_url(url):
    parsed = urllib.parse.urlsplit(url)
    return (parsed.scheme == "https" and parsed.hostname in HOSTS
            and parsed.username is None and parsed.password is None
            and parsed.port in (None, 443))


class RestrictedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed_url(newurl):
            raise ValueError("Redirect outside approved HTTPS hosts")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def read_sidecar(url, filename):
    if not allowed_url(url):
        raise ValueError("Unapproved repository URL")
    opener = urllib.request.build_opener(RestrictedRedirect())
    with opener.open(url, timeout=8) as response:
        if not allowed_url(response.geturl()):
            raise ValueError("Unapproved final repository URL")
        raw = response.read(513)
        if len(raw) > 512:
            raise ValueError("Oversized checksum response")
        return parse_sidecar(raw, filename), response.geturl()


def parse_sidecar(raw, filename):
    text = raw.decode("ascii").strip()
    if HASH.fullmatch(text):
        return text.lower()
    match = re.fullmatch(r"([0-9a-fA-F]{64})[ \t]+(?:\*)?([A-Za-z0-9_+.-]+)", text)
    if match and match[2] == filename:
        return match[1].lower()
    raise ValueError("Invalid checksum or mismatched filename")


def repositories(coordinate):
    group = coordinate.split(":")[0]
    if group.startswith(("com.android.", "androidx.", "com.google.android.")):
        return (GOOGLE, CENTRAL, PORTAL)
    if group.startswith("org.gradle."):
        return (PORTAL, CENTRAL, GOOGLE)
    return (CENTRAL, GOOGLE, PORTAL)


def corroborate(row, reader=read_sidecar):
    path = artifact_path(row)
    expected = row["sha256"][0].lower()
    attempts = []
    for base in repositories(row["coordinate"]):
        url = base + path
        try:
            published, final = reader(url, row["artifact"])
        except urllib.error.HTTPError as exc:
            attempts.append({"url": url, "status": f"HTTP_{exc.code}"})
            continue
        except (OSError, ValueError) as exc:
            attempts.append({"url": url, "status": type(exc).__name__})
            continue
        return {"coordinate": row["coordinate"], "artifact": row["artifact"],
                "sha256": expected, "publishedSha256": published, "source": final,
                "status": "MATCH" if published == expected else "MISMATCH",
                "attempts": attempts, "trust": "UNREVIEWED"}
    return {"coordinate": row["coordinate"], "artifact": row["artifact"],
            "sha256": expected, "status": "UNAVAILABLE", "attempts": attempts,
            "trust": "UNREVIEWED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = json.loads(args.inventory.read_text(encoding="utf-8"))
    keys = [(r["coordinate"], r["artifact"]) for r in rows]
    if not rows or len(set(keys)) != len(keys):
        raise ValueError("Empty or duplicate artifact inventory")
    for row in rows:
        artifact_path(row)
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(corroborate, rows))
    counts = dict(sorted(Counter(r["status"] for r in results).items()))
    report = {"trust": "UNREVIEWED", "method": "published HTTPS SHA-256 sidecars",
              "counts": counts, "artifacts": results}
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    print("F03_CHECKSUM_RESULT", json.dumps(counts, sort_keys=True), flush=True)
    if counts.get("MISMATCH", 0) or counts.get("UNAVAILABLE", 0):
        raise SystemExit("Unresolved provenance; do not promote metadata")


if __name__ == "__main__":
    main()
