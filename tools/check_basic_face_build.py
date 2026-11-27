"""Build the candidate in a temporary project, without changing the product face."""
import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

from generate_bootstrap import ROOT, FACE, check_outputs, safe_path
from generate_basic_face import OUTPUT, generate
from check_flavor_isolation import FILES, DIRECTORIES, run
from profile_contract import enabled_profiles, debug_apk
from signature_dev_bundle import build_bundle, write_new, sha, verify_bundle
from committed_build_inputs import clean_commit, copy_committed_inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development-bundle", type=Path)
    args = parser.parse_args()
    source_sha = None
    if args.development_bundle is not None:
        if args.development_bundle.exists():
            raise FileExistsError(args.development_bundle)
        source_sha = clean_commit(ROOT)
    original = (ROOT / FACE).read_bytes()
    outputs = generate()
    check_outputs(ROOT, outputs)
    face = outputs[OUTPUT]
    if face == original:
        raise ValueError("Candidate is not distinct")
    with tempfile.TemporaryDirectory(prefix="aura-basic-face-") as directory:
        root = Path(directory)
        if source_sha is not None:
            count = copy_committed_inputs(ROOT, root, source_sha,
                                          FILES + ("apps/watchface/build.gradle.kts",), DIRECTORIES)
            print(f"COMMITTED_INPUTS_RESULT {source_sha} {count}", flush=True)
            run(root, "generate_basic_face.py", "--write")
            run(root, "generate_basic_face.py", "--check")
            if (root / OUTPUT).read_bytes() != face or (root / FACE).read_bytes() != original:
                raise ValueError("Committed input reproduction mismatch")
        else:
            for name in FILES:
                shutil.copy2(ROOT / name, root / name)
            for name in DIRECTORIES:
                shutil.copytree(ROOT / name, root / name, ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copy2(ROOT / "apps/watchface/build.gradle.kts", root / "apps/watchface/build.gradle.kts")
        # Copy only pinned tool JARs. The existing validators verify their digests.
        (root / ".aura-tools").mkdir()
        for name in ("wff-validator.jar", "memory-footprint.jar"):
            path = ".aura-tools/" + name
            shutil.copy2(safe_path(ROOT, path), root / path)
        app = root / "apps/watchface"
        for p in enabled_profiles(root):
            if (app / "src" / p["name"] / "res/raw/watchface.xml").exists():
                raise ValueError("Unexpected product override in candidate fixture")
        (root / FACE).write_bytes(face)
        run(root, "verify_wff.py")
        run(root, "build_profiles.py", "assemble")
        run(root, "check_apk.py")
        run(root, "verify_memory.py")
        run(root, "build_profiles.py", "signatures")
        apks = {}
        for p in enabled_profiles(root):
            apk = debug_apk(p, app)
            with zipfile.ZipFile(apk) as z:
                if z.read("res/raw/watchface.xml") != face:
                    raise ValueError("Candidate APK XML mismatch")
            apks[p["name"]] = apk.read_bytes()
            print("BASIC_APK_RESULT " + json.dumps({"profile": p["name"],
                "xml_sha256": hashlib.sha256(face).hexdigest(),
                "apk_sha256": hashlib.sha256(apk.read_bytes()).hexdigest()}, sort_keys=True))
    if (ROOT / FACE).read_bytes() != original:
        raise ValueError("Product face changed")
    if args.development_bundle is not None:
        if clean_commit(ROOT) != source_sha:
            raise ValueError("Source changed during build")
        data, metadata = build_bundle(apks, face, source_sha)
        stored = write_new(args.development_bundle, data)
        if verify_bundle(stored, face, source_sha) != metadata:
            raise ValueError("Stored development bundle manifest mismatch")
        print("DEV_BUNDLE_RESULT " + json.dumps({"sha256": sha(stored), "bytes": len(stored),
                                               "manifest": metadata, "readbackVerified": True}, sort_keys=True))
    print("PASS: isolated Signature basic candidate, four profiles; product unchanged")


if __name__ == "__main__":
    main()
