"""Run the official WFF validator against enabled profiles."""
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".aura-tools"
URL = "https://github.com/google/watchface/releases/download/release/wff-validator.jar"
SHA256 = "0e2204137fca618264e82f9a053c6c9ec6d4fad08d2b56aa8a57d75c0508a804"

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
    for p in profiles:
        if not p["enabled"]:
            continue
        result = subprocess.run(["java", "-jar", str(jar), str(p["version"]), str(face)],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
        print(result.stdout, end="")
        # Require explicit success as well as exit status. Do not accept a silent validator.
        if result.returncode or "FAILED" in result.stdout.upper() or "VALID" not in result.stdout.upper():
            raise SystemExit("WFF validation failed or was inconclusive: " + p["name"])
    print("Official validator completed for enabled profiles. Inspect logs for each verdict.")

if __name__ == "__main__":
    main()
