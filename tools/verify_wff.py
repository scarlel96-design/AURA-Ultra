"""Run the official WFF validator against enabled profiles."""
import hashlib
from profile_contract import load_profiles, face_source, check_source_sets
import re
import tempfile
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".aura-tools"
URL = "https://github.com/google/watchface/releases/download/release/wff-validator.jar"
# Official release 460768397, source commit 18d3844 (2026-11-27).
SHA256 = "6ef308dbc306a9187b5b1f4997a662eb57e26ac3650cebbf2ab583cd38bb609e"

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

# The pinned validator exits 0 after schema rejection without stop-on-fail.
REJECTION = re.compile(
    r"^INFO:\s*(?:❌\s*)?FAILED\s*:\s*(.+?) is NOT valid against watch face format version #(\d+)\s*$"
)
HEADER = re.compile(r"^INFO: WFF Validation Application Version 1\.7\.0\. Maximum Supported Format Version #5$")
SCHEMA_REJECTION = "SEVERE: [Line 1:Column 13]: cvc-complex-type.4: Attribute 'width' must appear on element 'WatchFace'."


def require_rejection(returncode, output, face, version):
    """Require the pinned validator's exact negative-control verdict."""
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    verdicts = [match for line in lines if (match := REJECTION.fullmatch(line))]
    if (returncode != 0 or len(verdicts) != 1 or lines.count(SCHEMA_REJECTION) != 1
            or sum(bool(HEADER.fullmatch(line)) for line in lines) > 1
            or any(not (REJECTION.fullmatch(line) or HEADER.fullmatch(line)
                        or line == SCHEMA_REJECTION) for line in lines)):
        raise ValueError("Missing, ambiguous, or abnormal WFF rejection")
    path, actual_version = verdicts[0].groups()
    if Path(path).resolve() != Path(face).resolve() or int(actual_version) != version:
        raise ValueError("WFF rejection does not match requested file or version")


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
    profiles = load_profiles()
    check_source_sets(profiles)
    # Include disabled profiles for schema-only compatibility probes.
    for p in profiles:
        face = face_source(p)
        print(f"SCHEMA_PROFILE {p['name']} enabled={p['enabled']} source={face}", flush=True)
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
        for p in profiles:
            result = run_validator(jar, invalid, p["version"])
            print(result.stdout, end="")
            try:
                require_rejection(result.returncode, result.stdout, invalid, p["version"])
            except ValueError as exc:
                raise SystemExit(f"WFF negative {p['name']}: {exc}") from exc
            print("PASS: real validator rejected invalid XML for " + p["name"])
    print("PASS: explicit WFF verdict and negative probe for every declared profile (disabled profiles: schema only)")

if __name__ == "__main__":
    main()
