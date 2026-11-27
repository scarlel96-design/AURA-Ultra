"""Evaluate compiled WFF APK asset memory with the pinned Google tool."""
import hashlib
from profile_contract import enabled_profiles, debug_apk
import json
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".aura-tools"
URL = "https://github.com/google/watchface/releases/download/release/memory-footprint.jar"
SHA256 = "503c5f7bc9209ec4d4d4974f973cf66ad6fbb435e8422c310aac5b820f1f991a"
MIB = 1024 * 1024
LIMITS = {"maxActiveBytes": 70 * MIB, "maxAmbientBytes": 7 * MIB}
FIELDS = {"totalBytes", *LIMITS}


def parse_report(returncode, output):
    """Reject invalid, incomplete, or ambiguous reports."""
    if returncode:
        raise ValueError("Evaluator failed")
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON field: " + key)
            result[key] = value
        return result
    result = json.loads(output, object_pairs_hook=unique_pairs)
    if not isinstance(result, dict) or set(result) != FIELDS:
        raise ValueError("Unexpected memory report fields")
    if any(type(result[k]) is not int or result[k] < 0 for k in FIELDS):
        raise ValueError("Invalid memory byte count")
    return result


def enforce_limits(report):
    for field, limit in LIMITS.items():
        if report[field] > limit:
            raise ValueError(f"{field}: {report[field]} exceeds {limit} bytes")


def get_jar():
    CACHE.mkdir(exist_ok=True)
    jar = CACHE / "memory-footprint.jar"
    if not jar.exists():
        with urllib.request.urlopen(URL, timeout=60) as response:
            data = response.read(64 * MIB + 1)
        if len(data) > 64 * MIB or hashlib.sha256(data).hexdigest() != SHA256:
            raise ValueError("Memory evaluator download digest or size mismatch")
        jar.write_bytes(data)
    if hashlib.sha256(jar.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Memory evaluator digest mismatch")
    return jar


def evaluate(jar, apk, version):
    args = ["java", "-jar", str(jar), "--watch-face", str(apk),
            "--schema-version", str(version), "--apply-v1-offload-limitations", "--report"]
    result = subprocess.run(args, capture_output=True, text=True, timeout=180, check=False)
    print(result.stderr, end="")
    print(result.stdout, end="")
    return parse_report(result.returncode, result.stdout)


def main():
    jar = get_jar()
    subprocess.run(["java", "-jar", str(jar), "--version"], check=True, timeout=30)
    enabled = enabled_profiles()
    for p in enabled:
        apk = debug_apk(p)
        report = evaluate(jar, apk, p["version"])
        print("MEMORY_RESULT " + json.dumps({"profile": p["name"], "apk_sha256": hashlib.sha256(apk.read_bytes()).hexdigest(), **report}, sort_keys=True))
        enforce_limits(report)
        print("PASS: memory budget " + p["name"])
    print(f"PASS: all {len(enabled)} memory reports")


if __name__ == "__main__":
    main()
