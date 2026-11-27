"""Prove independent generation and missing/stale output rejection."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from generate_bootstrap import ROOT
from round_layout import SOURCE, generate as geometry
from generate_basic_face import generate as face
from signature_preview import generate as preview


def main():
    expected = geometry() | face() | preview()
    with tempfile.TemporaryDirectory(prefix="aura-layout-repro-") as directory:
        root = Path(directory)
        for name in (SOURCE, "tools/generate_bootstrap.py", "tools/round_layout.py", "tools/generate_basic_face.py", "tools/signature_preview.py"):
            dest = root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dest)
        for tool, files in (("round_layout.py", geometry()), ("generate_basic_face.py", face()), ("signature_preview.py", preview())):
            def call(action, success):
                result = subprocess.run([sys.executable, str(root / "tools" / tool), action], cwd=root,
                                        capture_output=True, timeout=60, check=False)
                if (result.returncode == 0) != success:
                    raise RuntimeError(f"{tool} {action}: {result.stderr!r}")
                if not success and b"Missing or stale generated file" not in result.stderr:
                    raise RuntimeError("Unexpected negative verdict")
                return result.stdout
            call("--check", False)
            first = call("--write", True)
            if call("--check", True) != first:
                raise ValueError("Independent process manifest mismatch")
            for name, data in files.items():
                path = root / name
                if path.read_bytes() != data:
                    raise ValueError("Generated output differs")
                path.write_bytes(b"stale")
                call("--check", False)
                if path.read_bytes() != b"stale":
                    raise ValueError("Check modified source")
                if call("--write", True) != first:
                    raise ValueError("Repair manifest mismatch")
        for name, data in expected.items():
            if (root / name).read_bytes() != data:
                raise ValueError("Restored output mismatch")
    print("PASS: independent geometry/basic face/preview generation, missing/stale rejection and repair")


if __name__ == "__main__":
    main()
