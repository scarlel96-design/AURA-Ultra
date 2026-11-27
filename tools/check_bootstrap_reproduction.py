"""Check separate-process bootstrap regeneration in an isolated directory."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from generate_bootstrap import ROOT, TOKENS, TEMPLATE, PREVIEW, FACE, PACKAGED_PREVIEW, PALETTE

OUTPUTS = (FACE, PACKAGED_PREVIEW, PALETTE)


def run(root, action, expected):
    result = subprocess.run([sys.executable, str(root / "tools/generate_bootstrap.py"), action],
                            cwd=root, capture_output=True, check=False, timeout=60)
    if result.returncode != expected:
        raise RuntimeError(f"{action}: expected {expected}, got {result.returncode}: {result.stderr!r}")
    return result


def main():
    original = {name: (ROOT / name).read_bytes() for name in OUTPUTS}
    with tempfile.TemporaryDirectory(prefix="aura-reproduce-") as directory:
        root = Path(directory)
        for name in (TOKENS, TEMPLATE, PREVIEW, "tools/generate_bootstrap.py"):
            dest = root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dest)
        missing = run(root, "--check", 1)
        if b"Missing or stale generated file" not in missing.stderr:
            raise RuntimeError("Missing output was not detected")
        first = run(root, "--write", 0).stdout
        for name, data in original.items():
            if (root / name).read_bytes() != data:
                raise RuntimeError("Generated output differs: " + name)
        second = run(root, "--check", 0).stdout
        if first != second:
            raise RuntimeError("Independent process manifest mismatch")
        (root / FACE).write_bytes(b"stale fixture")
        stale = run(root, "--check", 1)
        if b"Missing or stale generated file" not in stale.stderr or (root / FACE).read_bytes() != b"stale fixture":
            raise RuntimeError("Stale output check is not read-only")
        if run(root, "--write", 0).stdout != first:
            raise RuntimeError("Repair manifest mismatch")
        for name, data in original.items():
            if (root / name).read_bytes() != data or (ROOT / name).read_bytes() != data:
                raise RuntimeError("Output changed unexpectedly: " + name)
    print("PASS: independent bootstrap processes, missing/stale rejection, write repair and byte equality")


if __name__ == "__main__":
    main()
