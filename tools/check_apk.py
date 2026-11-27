"""Inspect each WFF debug APK without changing its signed contents."""
import hashlib
from profile_contract import enabled_profiles, debug_apk, face_source
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "apps/watchface/build/outputs/apk"
NS = "{http://schemas.android.com/apk/res/android}"
BASE_ID = "io.github.scarlel96.aura.watchface"
WFF_PROPERTY = "com.google.wear.watchface.format.version"
REQUIRED_ENTRIES = {"AndroidManifest.xml", "resources.arsc"}


def inspect_entries(names):
    """Return all ZIP payload violations; do not stop at the first entry."""
    errors = []
    missing = REQUIRED_ENTRIES - set(names)
    if missing:
        errors.append("Missing entries: " + ", ".join(sorted(missing)))
    if len(names) != len(set(names)):
        errors.append("Duplicate ZIP entries")
    for name in names:
        lower = name.lower()
        if lower.endswith((".dex", ".so", ".class", ".jar")) or lower.startswith("lib/"):
            errors.append("Executable payload: " + name)
        if name.startswith(("/", "\\")) or "\\" in name or ".." in name.split("/"):
            errors.append("Invalid ZIP path: " + name)
    return errors


def inspect_manifest(xml, profile):
    """Check the compiled APK manifest, not the source manifest."""
    root = ET.fromstring(xml)
    errors = []
    expected_id = BASE_ID + "." + profile["name"]
    if root.tag != "manifest" or root.get("package") != expected_id:
        errors.append("Incorrect package: " + str(root.get("package")))
    sdk = root.find("uses-sdk")
    if sdk is None or sdk.get(NS + "minSdkVersion") != str(profile["minSdk"]):
        errors.append("Incorrect minSdkVersion")
    app = root.find("application")
    if app is None:
        return errors + ["Missing application element"]
    if app.get(NS + "hasCode") != "false":
        errors.append("Missing explicit android:hasCode=false")
    values = [p.get(NS + "value") for p in app.findall("property")
              if p.get(NS + "name") == WFF_PROPERTY]
    if values != [str(profile["version"])]:
        errors.append("Incorrect or duplicate WFF version property: " + str(values))
    for tag in ("activity", "activity-alias", "service", "receiver", "provider"):
        if app.findall(tag):
            errors.append("Executable manifest component: " + tag)
    if any(e.tag.startswith("uses-permission") for e in root):
        errors.append("Unexpected permission in resource-only package")
    if not any(f.get(NS + "name") == "android.hardware.type.watch"
               and f.get(NS + "required", "true") == "true"
               for f in root.findall("uses-feature")):
        errors.append("Missing required watch feature")
    return errors


def inspect_face(archive, expected):
    """Compare the packaged face with the selected source bytes."""
    name = "res/raw/watchface.xml"
    if name not in archive.namelist():
        return ["Missing packaged face"]
    if archive.read(name) != expected:
        return ["Packaged face differs from selected source"]
    return []


def analyzer_path():
    tool = shutil.which("apkanalyzer")
    if tool:
        return tool
    sdk = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if sdk:
        name = "apkanalyzer.bat" if os.name == "nt" else "apkanalyzer"
        candidate = Path(sdk) / "cmdline-tools/latest/bin" / name
        if candidate.is_file():
            return str(candidate)
    raise RuntimeError("Android SDK apkanalyzer not found")


def main():
    enabled = enabled_profiles()
    analyzer = analyzer_path()
    failures = []
    for p in enabled:
        name = p["name"]
        try:
            apk = debug_apk(p)
        except ValueError as exc:
            failures.append(str(exc))
            continue
        print(f"APK {name}: {apk.name}; SHA-256 {hashlib.sha256(apk.read_bytes()).hexdigest()}")
        try:
            with zipfile.ZipFile(apk) as archive:
                entries = archive.namelist()
                print("ZIP entries:\n" + "\n".join(sorted(entries)))
                errors = inspect_entries(entries)
                errors.extend(inspect_face(archive, face_source(p).read_bytes()))
                corrupt = archive.testzip()
                if corrupt:
                    errors.append("Corrupt ZIP entry: " + corrupt)
            result = subprocess.run([analyzer, "manifest", "print", str(apk)],
                                    capture_output=True, text=True, timeout=60, check=False)
            if result.returncode:
                errors.append("apkanalyzer failed: " + result.stderr.strip())
            else:
                print("Compiled manifest:\n" + result.stdout)
                errors.extend(inspect_manifest(result.stdout, p))
        except (OSError, zipfile.BadZipFile, ET.ParseError, subprocess.TimeoutExpired) as exc:
            errors = [f"Inspection failed: {exc}"]
        if errors:
            failures.extend(f"{name}: {error}" for error in errors)
        else:
            print(f"PASS: {name} resource-only package")
    if failures:
        for error in failures:
            print("FAIL: " + error, file=sys.stderr)
        return 1
    print(f"PASS: inspected all {len(enabled)} enabled APKs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
