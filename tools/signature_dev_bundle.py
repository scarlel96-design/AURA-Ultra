"""Create and verify a local development bundle from already checked APK bytes."""
import hashlib
import io
import json
import os
import re
import zipfile
from pathlib import Path

PROFILES = ("wff2", "wff3", "wff4", "wff5")
PACKAGE_PREFIX = "io.github.scarlel96.aura.watchface."
MAX_APK = 32 * 1024 * 1024
MAX_FACE = 1024 * 1024
MAX_BUNDLE = 4 * MAX_APK + 2 * MAX_FACE


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate_apk(apk, face):
    if not isinstance(apk, bytes) or not 0 < len(apk) <= MAX_APK:
        raise ValueError("Invalid APK size")
    with zipfile.ZipFile(io.BytesIO(apk)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate APK entry")
        info = archive.getinfo("res/raw/watchface.xml")
        if info.file_size != len(face) or archive.read(info) != face:
            raise ValueError("Candidate APK face mismatch")


def manifest(apks, face, source_sha):
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ValueError("Invalid source commit")
    if set(apks) != set(PROFILES):
        raise ValueError("Incomplete or unexpected profile matrix")
    if not isinstance(face, bytes) or not 0 < len(face) <= MAX_FACE:
        raise ValueError("Invalid face size")
    rows = []
    for version, name in enumerate(PROFILES, 2):
        apk = apks[name]
        validate_apk(apk, face)
        rows.append({"profile": name, "minSdk": version+32,
                     "package": PACKAGE_PREFIX+name, "path": name+".apk",
                     "sha256": sha(apk), "bytes": len(apk)})
    return {"schemaVersion": 1, "kind": "Signature basic development only",
            "sourceCommit": source_sha, "xmlSha256": sha(face),
            "signaturePolicy": "debug; not production-signed",
            "runtimeVerification": "NOT RUN",
            "preview": "bootstrap placeholder; not actual candidate rendering",
            "profiles": rows}


def canonical(data):
    return (json.dumps(data, sort_keys=True, indent=2)+"\n").encode("utf-8")


def build_bundle(apks, face, source_sha):
    expected = manifest(apks, face, source_sha)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as archive:
        items = {"manifest.json": canonical(expected), "watchface.xml": face}
        items.update({name+".apk": apks[name] for name in PROFILES})
        for name, data in sorted(items.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980,1,1,0,0,0))
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)
    result = out.getvalue()
    verify_bundle(result, face, source_sha)
    return result, expected


def verify_bundle(data, face, source_sha):
    """Verify exact payloads and canonical metadata; not an authenticity check."""
    if not isinstance(data, bytes) or len(data) > MAX_BUNDLE:
        raise ValueError("Bundle too large")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        expected_names = {"manifest.json", "watchface.xml"} | {p+".apk" for p in PROFILES}
        if set(archive.namelist()) != expected_names or len(archive.namelist()) != len(expected_names):
            raise ValueError("Unexpected, duplicate or missing bundle entry")
        limits = {"manifest.json": 16384, "watchface.xml": MAX_FACE}
        for info in archive.infolist():
            if info.file_size > limits.get(info.filename, MAX_APK) or info.compress_type != zipfile.ZIP_STORED:
                raise ValueError("Unsupported bundle entry")
        if archive.read("watchface.xml") != face:
            raise ValueError("Bundle XML mismatch")
        apks = {p: archive.read(p+".apk") for p in PROFILES}
        expected = manifest(apks, face, source_sha)
        if archive.read("manifest.json") != canonical(expected):
            raise ValueError("Bundle manifest mismatch")
    return expected


def write_new(path, data):
    """Create a new file, flush it, and compare the persisted bytes."""
    path = Path(path)
    stream = path.open("xb")
    try:
        with stream:
            if stream.write(data) != len(data):
                raise OSError("Short bundle write")
            stream.flush()
            os.fsync(stream.fileno())
        with path.open("rb") as stored:
            actual = stored.read(len(data)+1)
        if actual != data:
            raise ValueError("Stored bundle bytes mismatch")
        return actual
    except BaseException:
        path.unlink()
        raise
