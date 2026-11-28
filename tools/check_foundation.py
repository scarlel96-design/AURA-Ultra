"""Check project invariants. This is not the official WFF validator."""
import json
from check_apk import resource_manifest_errors
from profile_contract import load_profiles, check_source_sets, face_source
import re
import sys
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps/watchface"
RES = APP / "src/main/res"
NS = "{http://schemas.android.com/apk/res/android}"

def require(ok, message):
    if not ok:
        raise ValueError(message)

def check():
    manifest = ET.parse(APP / "src/main/AndroidManifest.xml").getroot()
    errors = resource_manifest_errors(manifest, "$"+"{wffVersion}")
    require(not errors, "; ".join(errors))
    require(not any(p.suffix in (".kt", ".java", ".dex", ".so") for p in (APP / "src").rglob("*") if p.is_file()), "Executable source or binary in WFF")
    face = ET.parse(RES / "raw/watchface.xml").getroot()
    require(face.tag == "WatchFace" and (face.get("width"), face.get("height")) == ("450","450"), "Invalid root or canvas")
    require(len(face.findall("Scene")) == 1, "Expected one Scene")
    require(len(face.findall(".//TimeText")) == 2, "Expected active and ambient time")
    require(any(v.get("mode") == "AMBIENT" and v.get("target") == "alpha" and v.get("value") == "0" for v in face.findall(".//Group/Variant")), "Missing decoration suppression")
    require(all(t.get("hourFormat") == "SYNC_TO_DEVICE" for t in face.findall(".//TimeText")), "Clock must respect device format")
    info = ET.parse(RES / "xml/watch_face_info.xml").getroot()
    require(info.find("Preview").get("value") == "@drawable/preview", "Missing preview metadata")
    png = (RES / "drawable-nodpi/preview.png").read_bytes()
    require(png[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", png[16:24]) == (450,450), "Invalid preview header/dimensions")
    profiles = load_profiles()
    check_source_sets(profiles)
    gradle = (APP / "build.gradle.kts").read_text(encoding="utf-8")
    expected_names = {p["name"] for p in profiles if p["enabled"]}
    actual_names = set(re.findall(r'create\("([^"]+)"\)', gradle))
    require(actual_names == expected_names, "Unexpected Gradle profile matrix")
    compile_match = re.search(r'\bcompileSdk\s*=\s*(\d+)', gradle)
    require(compile_match is not None, "Missing compileSdk")
    for p in profiles:
        match = re.search(r'create\("' + p["name"] + r'"\)\s*\{([^}]*)\}', gradle)
        if p["enabled"]:
            require(match and f'minSdk = {p["minSdk"]}' in match[1] and f'["wffVersion"] = "{p["version"]}"' in match[1], "Gradle/profile mismatch: " + p["name"])
            require(int(compile_match[1]) >= p["minSdk"], "compileSdk below profile minimum")
            require(f'applicationIdSuffix = ".{p["name"]}"' in match[1], "Application ID suffix mismatch")
            resolved = ET.parse(face_source(p)).getroot()
            require(resolved.tag == "WatchFace" and (resolved.get("width"), resolved.get("height")) == ("450", "450"), "Invalid resolved face canvas")
            require(len(resolved.findall("Scene")) == 1 and len(resolved.findall(".//TimeText")) == 2, "Missing scene or time")
            require(all(t.get("hourFormat") == "SYNC_TO_DEVICE" for t in resolved.findall(".//TimeText")), "Clock format mismatch")
            require(any(v.get("mode") == "AMBIENT" and v.get("target") == "alpha" and v.get("value") == "0" for v in resolved.findall(".//Group/Variant")), "Missing AOD decoration suppression")
        else:
            require(match is None, "Unapproved profile enabled")
    tokens = json.loads((ROOT / "design-system/tokens/bootstrap.json").read_text(encoding="utf-8"))
    require(tokens["size"] == int(face.get("width")), "Canvas token mismatch")
    for name, color in tokens["colors"].items():
        require(color in (RES / "raw/watchface.xml").read_text(encoding="utf-8"), "Unused bootstrap color: " + name)
    for name, (x,y,w,h) in tokens["layout"].items():
        require(x >= 0 and y >= 0 and x+w <= 450 and y+h <= 450, "Bounds: " + name)
    print("PASS: resource-only manifest, XML structure, AOD invariant, preview, flavor matrix, tokens")
    print("NOT RUN: official WFF schema, renderer, memory, battery, device compatibility")

if __name__ == "__main__":
    try:
        check()
    except (ValueError, OSError, ET.ParseError, AttributeError, KeyError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
