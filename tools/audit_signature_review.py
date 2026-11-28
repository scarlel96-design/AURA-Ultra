"""Verify archived detached signatures. Never grant dependency trust."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import tempfile
import urllib.request
import urllib.parse

from audit_provenance_priority import archive, sha, read_bytes, MAX_ARTIFACT
from audit_published_checksums import artifact_path, CENTRAL
from audit_dependency_review import write_json

DIGEST = "004cbfb19bb784d6744c6974fc8c0f5d42015078689f16ee8d131003c436e677"
SOURCE = "466fc5f00064b4b1436aebe67a5c8e5168dcac4d"
FPR = re.compile(r"(?:[A-F0-9]{40}|[A-F0-9]{64})")
KEYID = re.compile(r"[A-F0-9]{16}")
OFFICIAL = {
    "org.bouncycastle": "https://downloads.bouncycastle.org/java/bc_maven_public_key.asc",
    "org.apache.commons": "https://downloads.apache.org/commons/KEYS",
    "org.apache.httpcomponents": "https://archive.apache.org/dist/httpcomponents/httpclient/KEYS",
}
KOTLIN_PRIMARY = "2FBA29D08D2E25EE84C132C30729A0AFF8999A87"
BAD = {"BADSIG", "ERRSIG", "NO_PUBKEY", "EXPSIG", "EXPKEYSIG", "REVKEYSIG",
       "KEYREVOKED", "SIGEXPIRED", "KEYEXPIRED", "NODATA", "FAILURE", "ERROR"}


def gpg(home, *args):
    return subprocess.run(["gpg", "--no-options", "--homedir", str(home), "--batch",
                           "--no-tty", "--no-auto-key-retrieve", "--no-auto-key-locate",
                           *map(str, args)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=45)


def issuer(text):
    if len(re.findall(r"^:signature packet:", text, re.M)) != 1:
        raise ValueError("Expected exactly one signature packet")
    ids = set(re.findall(r"keyid ([A-F0-9]{16})\b", text))
    fps = set(re.findall(r"issuer fpr v\d+ ([A-F0-9]+)\b", text))
    if len(ids) != 1 or len(fps) > 1:
        raise ValueError("Ambiguous issuer")
    key = next(iter(ids))
    fingerprint = next(iter(fps), None)
    if fingerprint and (not FPR.fullmatch(fingerprint) or not fingerprint.endswith(key)):
        raise ValueError("Inconsistent issuer fingerprint")
    return key, fingerprint


def verdict(returncode, status, keyid, claimed):
    records = [l[len("[GNUPG:] "):].split() for l in status.splitlines()
               if l.startswith("[GNUPG:] ")]
    tags = {r[0] for r in records if r}
    valid = [r for r in records if r and r[0] == "VALIDSIG"]
    if returncode or tags & BAD or len(valid) != 1 or "GOODSIG" not in tags:
        return {"crypto": "NOT_VALIDATED", "statusTags": sorted(tags)}
    v = valid[0]
    if len(v) not in (10, 11):
        raise ValueError("Unexpected VALIDSIG fields")
    signer, primary = v[1], v[-1] if len(v) == 11 else v[1]
    if not FPR.fullmatch(signer) or not FPR.fullmatch(primary):
        raise ValueError("Invalid verified fingerprint")
    if not signer.endswith(keyid) or (claimed and signer != claimed):
        raise ValueError("Verified signer differs from issuer")
    if v[8] not in ("8", "9", "10", "11"):
        return {"crypto": "WEAK_OR_UNKNOWN_HASH", "statusTags": sorted(tags)}
    return {"crypto": "VALID", "signerFingerprint": signer,
            "primaryFingerprint": primary, "statusTags": sorted(tags)}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Key retrieval redirect refused")


def key_bytes(url):
    with urllib.request.build_opener(NoRedirect()).open(url, timeout=12) as response:
        raw = response.read(4 * 1024 * 1024 + 1)
    if not raw or len(raw) > 4 * 1024 * 1024 or b"PRIVATE KEY BLOCK" in raw:
        raise ValueError("Invalid public key data")
    return raw


def key_sources(group, keyid, fingerprint):
    if group in OFFICIAL:
        yield "OFFICIAL_KEY_FILE", OFFICIAL[group]
    if group == "org.jetbrains.kotlin":
        yield "OFFICIAL_FINGERPRINT_LOOKUP", "https://keys.openpgp.org/vks/v1/by-fingerprint/" + KOTLIN_PRIMARY
    if fingerprint:
        yield "DISCOVERY_ONLY", "https://keys.openpgp.org/vks/v1/by-fingerprint/" + fingerprint
    yield "DISCOVERY_ONLY", "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x" + (fingerprint or keyid)


def verify_one(row, evidence, signature, out, cache):
    group = row["coordinate"].split(":")[0]
    result = {"coordinate": row["coordinate"], "artifact": row["artifact"],
              "expectedSha256": row["sha256"][0], "trust": "UNREVIEWED",
              "publisher": "UNCONFIRMED", "crypto": "NOT_RUN", "attempts": []}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sigfile = root / "signature.asc"
        sigfile.write_bytes(signature)
        packet_home = root / "packets"
        packet_home.mkdir(mode=0o700)
        packet = gpg(packet_home, "--list-packets", sigfile)
        try:
            if packet.returncode:
                raise ValueError("Packet parser failed")
            keyid, fingerprint = issuer(packet.stdout)
            result.update(issuerKeyId=keyid, claimedFingerprint=fingerprint)
            url = CENTRAL + artifact_path(row).removesuffix(".sha256")
            raw, final = read_bytes(url, MAX_ARTIFACT)
            result.update(actualSha256=sha(raw), artifactSource=final)
            if sha(raw) != row["sha256"][0]:
                result["crypto"] = "BYTE_MISMATCH"
                return result
            artifact = root / "artifact"
            artifact.write_bytes(raw)
            for i, (kind, source) in enumerate(key_sources(group, keyid, fingerprint)):
                attempt = {"kind": kind, "source": source}
                result["attempts"].append(attempt)
                try:
                    if source not in cache:
                        try:
                            cache[source] = (key_bytes(source), None)
                        except (OSError, ValueError) as exc:
                            cache[source] = (None, type(exc).__name__)
                    key, err = cache[source]
                    if err:
                        attempt["error"] = err
                        continue
                    digest = sha(key)
                    (out / (digest + ".pub")).write_bytes(key)
                    attempt["keySha256"] = digest
                    home = root / ("key" + str(i))
                    home.mkdir(mode=0o700)
                    keyfile = root / "public.key"
                    keyfile.write_bytes(key)
                    imported = gpg(home, "--import-options", "import-clean", "--import", keyfile)
                    if imported.returncode:
                        attempt["error"] = "IMPORT_FAILED"
                        continue
                    verified = gpg(home, "--status-fd", "1", "--verify", sigfile, artifact)
                    attempt.update(verdict(verified.returncode, verified.stdout, keyid, fingerprint))
                    if attempt["crypto"] != "VALID":
                        continue
                    result.update({k: attempt[k] for k in ("crypto", "signerFingerprint", "primaryFingerprint", "statusTags")})
                    result["keySource"] = source
                    result["keySha256"] = digest
                    if kind == "OFFICIAL_KEY_FILE":
                        result["publisher"] = "OFFICIAL_KEY_FILE_MATCH"
                    elif kind == "OFFICIAL_FINGERPRINT_LOOKUP" and result["primaryFingerprint"] == KOTLIN_PRIMARY:
                        result["publisher"] = "OFFICIAL_PRIMARY_FINGERPRINT_MATCH"
                    else:
                        result["publisher"] = "DISCOVERY_ONLY"
                    return result
                except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
                    attempt["error"] = type(exc).__name__
            result["crypto"] = "NOT_VALIDATED"
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            result.update(crypto="UNKNOWN", error=type(exc).__name__)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    with archive(a.input, DIGEST) as z:
        summary = json.loads(z.read("summary.json"))
        if summary["sourceCommit"] != SOURCE or summary["trust"] != "UNREVIEWED":
            raise ValueError("Wrong R13 evidence")
        rows = json.loads(z.read("priority-input.json"))
        evidence = json.loads(z.read("priority-results.json"))
        mapping = {(r["coordinate"], r["artifact"]): r for r in evidence}
        if len(rows) != 48 or len(mapping) != len(evidence) or len(mapping) != 48:
            raise ValueError("Unexpected evidence count")
        items = []
        for row in rows:
            artifact_path(row)
            key = (row["coordinate"], row["artifact"])
            e = mapping.pop(key)
            if (e["expectedSha256"] != row["sha256"][0] or e["actualSha256"] != row["sha256"][0]
                    or e["bytesStatus"] != "MATCH" or e["signatureStatus"] != "PRESENT_UNVERIFIED"
                    or e["trust"] != "UNREVIEWED"):
                raise ValueError("Inconsistent evidence")
            name = e["signatureFile"]
            if not re.fullmatch(r"[0-9a-f]{64}\.asc", name):
                raise ValueError("Invalid signature filename")
            signature = z.read(name)
            if sha(signature) != e["signatureSha256"] or name != sha(signature) + ".asc":
                raise ValueError("Signature hash mismatch")
            items.append((row, e, signature))
        if mapping:
            raise ValueError("Unexpected evidence rows")
    a.output.mkdir(parents=True, exist_ok=False)
    cache = {}
    results = [verify_one(row, e, sig, a.output, cache) for row, e, sig in items]
    write_json(a.output / "signature-results.json", results)
    summary = {"sourceCommit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
               "inputSha256": DIGEST, "trust": "UNREVIEWED", "approval": "BLOCKED",
               "crypto": dict(Counter(r["crypto"] for r in results)),
               "publisher": dict(Counter(r["publisher"] for r in results)), "count": len(results),
               "gpg": subprocess.check_output(["gpg", "--version"], text=True).splitlines()[0]}
    write_json(a.output / "summary.json", summary)
    print("F03_R14", json.dumps(summary, sort_keys=True), flush=True)
    if any(r["crypto"] != "VALID" for r in results):
        raise SystemExit("Incomplete signature validation; no approval")


if __name__ == "__main__":
    main()
