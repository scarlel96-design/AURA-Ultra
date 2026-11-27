"""Check that built WFF APKs contain resources, not executable payloads."""
import sys
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / "apps/watchface/build/outputs/apk"
for profile in ("wff2", "wff3", "wff4"):
    apks = list((out / profile / "debug").glob("*.apk"))
    if len(apks) != 1:
        sys.exit(f"FAIL: expected one debug APK for {profile}, got {len(apks)}")
    with zipfile.ZipFile(apks[0]) as apk:
        names = apk.namelist()
        if any(n.endswith((".dex", ".so")) or n.startswith("lib/") for n in names):
            sys.exit(f"FAIL: executable payload in {apks[0]}")
        if "AndroidManifest.xml" not in names or "resources.arsc" not in names:
            sys.exit(f"FAIL: missing Android resources in {apks[0]}")
    print(f"PASS: {profile} resource-only package: {apks[0].name}")
