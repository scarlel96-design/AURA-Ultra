"""Run the official WFF validator against enabled profiles."""
import hashlib
import json
import re
import tempfile
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".aura-tools"
URL = "https://github.com/google/watchface/releases/download/release/wff-validator.jar"
SHA256 = "0e2204137fca618264e82f9a053c6c9ec6d4fad08d2b56aa8a57d75c0508a804"

PASS = re.compile(
    r"^INFO:\s*(?:✅\s*)?PASSED\s*:\s*(.+?) is valid against watch face format version #(\d+)\s*$"
)
FAILURE = re.compile(r"\b(?:FAILED|ERROR|SEVERE)\b", re.IGNORECASE)

def require_pass(returncode, output, face, version):
    """Require one explicit verdict for the requested file and version."""
    verdicts = [match for line in output.splitlines() if (match := PASS.fullmatch(line))]
    if returncode != 0 or FAILURE.search(output) or len(verdicts) != 1:
        raise ValueError("Missing, ambiguous, or failed WFF verdict")
    path, actual_version = verdicts[0].groups()
    if Path(path).resolve() != Path(face).resolve() or int(actual_version) != version:
        raise ValueError("WFF verdict does not match requested file or version")

def run_validator(jar, face, version):
    return subprocess.run(
        ["java", "-jar", str(jar), str(version), str(face)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        timeout=120, check=False,
    )

def main():
    CACHE.mkdir(exist_ok=True)
    jar = CACHE / "wff-validator.jar"
    if not jar.exists():
        with urllib.request.urlopen(URL, timeout=60) as response:
            data = response.read(100 * 1024 * 1024 + 1)
        if len(data) > 100 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != SHA256:
            raise SystemExit("Validator download size or digest mismatch. Review the official release before updating the pin.")
        jar.write_bytes(data)
    if hashlib.sha256(jar.read_bytes()).hexdigest() != SHA256:
        raise SystemExit("Validator digest mismatch.")
    face = ROOT / "apps/watchface/src/main/res/raw/watchface.xml"
    profiles = json.loads((ROOT / "compatibility/profiles.json").read_text(encoding="utf-8"))["profiles"]
    enabled = [p for p in profiles if p["enabled"]]
    if not enabled or len({p["version"] for p in enabled}) != len(enabled):
        raise SystemExit("Missing or duplicate enabled WFF versions")
    for p in enabled:
        result = run_validator(jar, face, p["version"])
        print(result.stdout, end="")
        try:
            require_pass(result.returncode, result.stdout, face, p["version"])
        except ValueError as exc:
            raise SystemExit(f"WFF {p['name']}: {exc}") from exc
    # Exercise the real validator with well-formed but schema-invalid XML.
    with tempfile.TemporaryDirectory(prefix="aura-wff-negative-") as directory:
        invalid = Path(directory) / "invalid.xml"
        invalid.write_text("<WatchFace/>", encoding="utf-8")
        for p in enabled:
            result = run_validator(jar, invalid, p["version"])
            print(result.stdout, end="")
            if any(PASS.fullmatch(line) for line in result.stdout.splitlines()):
                raise SystemExit("Invalid WFF fixture unexpectedly passed: " + p["name"])
            if result.returncode == 0 and not FAILURE.search(result.stdout):
                raise SystemExit("Inconclusive negative validator test: " + p["name"])
            print("PASS: real validator rejected invalid XML for " + p["name"])
    print("PASS: explicit WFF verdict and negative probe for every enabled profile")

if __name__ == "__main__":
    main()
