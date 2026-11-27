"""Share build profile selection and artifact paths across host tools."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps/watchface"
API_BY_VERSION = {2: 34, 3: 35, 4: 36, 5: 37}


def validate_profiles(config):
    """Reject missing, duplicate or inconsistent profiles."""
    if config.get("schemaVersion") != 1 or config.get("logicalSize") != 450:
        raise ValueError("Unsupported profile contract")
    profiles = config.get("profiles")
    if not isinstance(profiles, list):
        raise ValueError("Missing profiles")
    seen = set()
    for p in profiles:
        if not isinstance(p, dict):
            raise ValueError("Invalid profile")
        version = p.get("version")
        if type(version) is not int or version not in API_BY_VERSION or version in seen:
            raise ValueError("Invalid or duplicate WFF version")
        seen.add(version)
        if p.get("name") != f"wff{version}" or type(p.get("minSdk")) is not int or p["minSdk"] != API_BY_VERSION[version]:
            raise ValueError("Profile identity or minimum API mismatch")
        if type(p.get("enabled")) is not bool:
            raise ValueError("Enabled must be boolean")
        if not p["enabled"] and not str(p.get("reason", "")).strip():
            raise ValueError("Disabled profile needs a reason")
    if seen != set(API_BY_VERSION):
        raise ValueError("Incomplete WFF profile matrix")
    if not all(p["enabled"] for p in profiles if p["version"] <= 4):
        raise ValueError("Required WFF2/3/4 profile disabled")
    return sorted(profiles, key=lambda p: p["version"])


def load_profiles(root=ROOT):
    return validate_profiles(json.loads((root / "compatibility/profiles.json").read_text(encoding="utf-8")))


def enabled_profiles(root=ROOT):
    return [p for p in load_profiles(root) if p["enabled"]]


def face_source(profile, app=APP):
    """Use the flavor override before the common face."""
    common = app / "src/main/res/raw/watchface.xml"
    override = app / "src" / profile["name"] / "res/raw/watchface.xml"
    if not common.is_file():
        raise ValueError("Missing common face")
    return override if override.is_file() else common


def check_source_sets(profiles, app=APP):
    """Reject untracked watch face overrides until their precedence is supported."""
    allowed = {app / "src/main/res/raw/watchface.xml"}
    allowed.update(app / "src" / p["name"] / "res/raw/watchface.xml" for p in profiles)
    for path in (app / "src").rglob("watchface.xml"):
        if path.is_file() and path not in allowed:
            raise ValueError("Unsupported face source set: " + str(path))


def debug_tasks(profiles):
    return [f":apps:watchface:assemble{p['name'].capitalize()}Debug" for p in profiles]


def debug_apk(profile, app=APP):
    matches = sorted((app / "build/outputs/apk" / profile["name"] / "debug").glob("*.apk"))
    if len(matches) != 1:
        raise ValueError(f"{profile['name']}: expected one debug APK, found {len(matches)}")
    return matches[0]
