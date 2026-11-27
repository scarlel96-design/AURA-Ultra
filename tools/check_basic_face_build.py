"""Build the candidate in a temporary project, without changing the product face."""
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

from generate_bootstrap import ROOT, FACE, check_outputs
from generate_basic_face import OUTPUT, generate
from check_flavor_isolation import FILES, DIRECTORIES, run
from profile_contract import enabled_profiles, debug_apk


def main():
    original = (ROOT / FACE).read_bytes()
    outputs = generate()
    check_outputs(ROOT, outputs)
    face = outputs[OUTPUT]
    if face == original:
        raise ValueError("Candidate is not distinct")
    with tempfile.TemporaryDirectory(prefix="aura-basic-face-") as directory:
        root = Path(directory)
        for name in FILES:
            shutil.copy2(ROOT / name, root / name)
        for name in DIRECTORIES:
            shutil.copytree(ROOT / name, root / name, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy2(ROOT / "apps/watchface/build.gradle.kts", root / "apps/watchface/build.gradle.kts")
        shutil.copytree(ROOT / ".aura-tools", root / ".aura-tools")
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
        for p in enabled_profiles(root):
            apk = debug_apk(p, app)
            with zipfile.ZipFile(apk) as z:
                if z.read("res/raw/watchface.xml") != face:
                    raise ValueError("Candidate APK XML mismatch")
            print("BASIC_APK_RESULT " + json.dumps({"profile": p["name"],
                "xml_sha256": hashlib.sha256(face).hexdigest(),
                "apk_sha256": hashlib.sha256(apk.read_bytes()).hexdigest()}, sort_keys=True))
    if (ROOT / FACE).read_bytes() != original:
        raise ValueError("Product face changed")
    print("PASS: isolated Signature basic candidate, four profiles; product unchanged")


if __name__ == "__main__":
    main()
