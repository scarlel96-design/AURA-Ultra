"""Build and verify signatures for all enabled debug profiles."""
import os
import subprocess
import sys
from pathlib import Path
from profile_contract import ROOT, enabled_profiles, debug_tasks, debug_apk


def main():
    profiles = enabled_profiles()
    if sys.argv[1:] == ["assemble"]:
        wrapper = ROOT / ("gradlew.bat" if os.name == "nt" else "gradlew")
        subprocess.run([str(wrapper), "--no-daemon", "--stacktrace", "clean", *debug_tasks(profiles)],
                       cwd=ROOT, check=True)
    elif sys.argv[1:] == ["signatures"]:
        sdk = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
        if not sdk:
            raise ValueError("Android SDK path not configured")
        signer = Path(sdk) / "build-tools/35.0.0" / ("apksigner.bat" if os.name == "nt" else "apksigner")
        for p in profiles:
            apk = debug_apk(p)
            print(f"SIGNATURE_PROFILE {p['name']} {apk.name}", flush=True)
            subprocess.run([str(signer), "verify", "--verbose", "--print-certs", str(apk)], check=True)
    else:
        raise SystemExit("Usage: python tools/build_profiles.py assemble|signatures")


if __name__ == "__main__":
    main()
