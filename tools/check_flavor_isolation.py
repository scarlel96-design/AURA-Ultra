"""Test generated flavor precedence and stale APK detection in an isolated project."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from generate_bootstrap import ROOT, FACE, TOKENS, TEMPLATE, parse_tokens, render_face, safe_path
from profile_contract import enabled_profiles, face_source, check_source_sets, debug_apk
from committed_build_inputs import clean_commit, copy_committed_inputs

OVERRIDE = "apps/watchface/src/wff4/res/raw/watchface.xml"
FILES = ("settings.gradle.kts", "build.gradle.kts", "gradle.properties", "gradlew", "gradlew.bat")
DIRECTORIES = ("gradle", "compatibility", "tools", "assets", "design-system", "apps/watchface/src")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def make_override(root):
    tokens = json.loads((root / TOKENS).read_bytes())
    # Change one existing color; do not introduce a new WFF feature.
    original = tokens["colors"]["accent"]
    tokens["colors"]["accent"] = "#FFFFA84D" if original != "#FFFFA84D" else "#FF79D4F2"
    checked = parse_tokens(json.dumps(tokens))
    generated = render_face((root / TEMPLATE).read_text(encoding="utf-8"), checked)
    if generated == (root / FACE).read_bytes():
        raise ValueError("Override must differ from common face")
    return generated


def run(root, tool, *args, expected=0, timeout=600):
    result = subprocess.run([sys.executable, str(root / "tools" / tool), *args],
                            cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace",
                            timeout=timeout, check=False)
    print(result.stdout, end="", flush=True)
    if result.returncode != expected:
        raise RuntimeError(f"{tool}: expected exit {expected}, got {result.returncode}")
    return result.stdout


def verify_matrix(root, common, override):
    profiles = enabled_profiles(root)
    if [p["name"] for p in profiles] != ["wff2", "wff3", "wff4", "wff5"]:
        raise ValueError("Expected all four enabled profiles")
    app = root / "apps/watchface"
    check_source_sets(profiles, app)
    for p in profiles:
        name = p["name"]
        expected = override if name == "wff4" else common
        expected_path = root / (OVERRIDE if name == "wff4" else FACE)
        if face_source(p, app) != expected_path:
            raise ValueError("Wrong selected source: " + name)
        apk = debug_apk(p, app)
        with zipfile.ZipFile(apk) as archive:
            actual = archive.read("res/raw/watchface.xml")
        if actual != expected:
            raise ValueError("Incorrect packaged face: " + name)
        print("FLAVOR_RESULT " + json.dumps({"profile": name, "source": expected_path.relative_to(root).as_posix(),
                                            "source_sha256": digest(expected), "packaged_sha256": digest(actual),
                                            "apk_sha256": digest(apk.read_bytes())}, sort_keys=True), flush=True)


def require_mismatch(output):
    expected = "FAIL: wff4: Packaged face differs from selected source"
    failures = [line.strip() for line in output.splitlines() if line.startswith("FAIL:")]
    if failures != [expected]:
        raise ValueError("Wrong failure target or unrelated APK failure")
    for name in ("wff2", "wff3", "wff5"):
        if f"PASS: {name} resource-only package" not in output.splitlines():
            raise ValueError("Missing unaffected profile PASS: " + name)


def main():
    source = clean_commit(ROOT)
    common = (ROOT / FACE).read_bytes()
    if (ROOT / OVERRIDE).exists():
        raise ValueError("Test requires the original common-only bootstrap")
    with tempfile.TemporaryDirectory(prefix="aura-flavor-") as directory:
        root = Path(directory)
        count = copy_committed_inputs(ROOT, root, source,
                                      FILES + ("apps/watchface/build.gradle.kts",), DIRECTORIES)
        if (root / FACE).read_bytes() != common or (root / OVERRIDE).exists():
            raise ValueError("Committed flavor input mismatch")
        print(f"FLAVOR_COMMITTED_INPUTS {source} {count}", flush=True)
        # Reuse only the two named JARs. Their wrappers verify pinned digests.
        (root / ".aura-tools").mkdir()
        for name in ("wff-validator.jar", "memory-footprint.jar"):
            path = ".aura-tools/" + name
            shutil.copy2(safe_path(ROOT, path), root / path)
        run(root, "generate_bootstrap.py", "--check")
        override = make_override(root)
        path = root / OVERRIDE
        path.parent.mkdir(parents=True)
        path.write_bytes(override)
        run(root, "verify_wff.py")
        run(root, "build_profiles.py", "assemble")
        run(root, "check_apk.py")
        verify_matrix(root, common, override)
        run(root, "verify_memory.py")
        run(root, "build_profiles.py", "signatures")
        # Change only the expected source; the signed APK remains untouched.
        path.write_bytes(common)
        require_mismatch(run(root, "check_apk.py", expected=1))
        path.write_bytes(override)
        run(root, "check_apk.py")
        verify_matrix(root, common, override)
        if (root / FACE).read_bytes() != common:
            raise ValueError("Common face changed inside the isolated project")
    if clean_commit(ROOT) != source or (ROOT / FACE).read_bytes() != common or (ROOT / OVERRIDE).exists():
        raise ValueError("Product source changed")
    print("PASS: generated WFF4 override isolated; all four APKs verified; stale source rejected; product unchanged")


if __name__ == "__main__":
    main()
