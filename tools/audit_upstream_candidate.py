"""Evaluate an upstream AGP/Gradle pair in a disposable source tree.

Never approve generated metadata, modify the checkout, or force transitive versions.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

from audit_gradle_inventory import run_logged, summarize_metadata
from audit_dependency_review import load_inventory, osv_query, request_osv, write_json

ROOT = Path(__file__).resolve().parents[1]
AGP = "9.5.1"
GRADLE = "9.6.1"
DIST_SHA = "9c0f7faeeb306cb14e4279a3e084ca6b596894089a0638e68a07c945a32c9e14"
OLD_DIST_SHA = "b266d5ff6b90eada6dc3b20cb090e3731302e553a27c5d3e4df1f0d76beaff06"
WRAPPER_SHA = "b3a875ddc1f044746e1b1a55f645584505f4a10438c1afea9f15e92a7c42ec13"
PROJECTS = {":", ":apps", ":apps:watchface"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("Unexpected version anchor: " + old)
    return text.replace(old, new, 1)


def patch_candidate(work):
    plugin = work / "build.gradle.kts"
    props = work / "gradle/wrapper/gradle-wrapper.properties"
    wrapper = work / "gradle/wrapper/gradle-wrapper.jar"
    if sha(wrapper.read_bytes()) != WRAPPER_SHA:
        raise ValueError("Original wrapper JAR hash mismatch")
    if (work / "gradle/verification-metadata.xml").exists():
        raise ValueError("Refuse to replace existing trust metadata")
    before = {p.relative_to(work).as_posix(): sha(p.read_bytes()) for p in (plugin, props)}
    plugin_text = replace_once(plugin.read_text(encoding="utf-8"), 
                               'id("com.android.application") version "9.1.1"',
                               'id("com.android.application") version "' + AGP + '"')
    prop_text = replace_once(props.read_text(encoding="utf-8"), "gradle-9.3.1-bin.zip",
                             "gradle-" + GRADLE + "-bin.zip")
    prop_text = replace_once(prop_text, "distributionSha256Sum=" + OLD_DIST_SHA,
                             "distributionSha256Sum=" + DIST_SHA)
    plugin.write_text(plugin_text, encoding="utf-8", newline="\n")
    props.write_text(prop_text, encoding="utf-8", newline="\n")
    return {p.relative_to(work).as_posix(): {"before": before[p.relative_to(work).as_posix()],
             "after": sha(p.read_bytes()), "content": p.read_text(encoding="utf-8")} for p in (plugin, props)}


def graph_index(parts):
    if len(parts) != len(PROJECTS) or {p["project"] for p in parts} != PROJECTS:
        raise ValueError("Missing/duplicate project graph")
    result = {}
    for part in parts:
        for row in part["rows"]:
            key = (row["project"], row["scope"], row["configuration"])
            if (key in result or row["project"] != part["project"]
                    or row["scope"] not in {"project", "buildscript"}
                    or row["error"] or row["unresolved"]):
                raise ValueError("Invalid or unresolved graph row")
            modules = row["modules"]
            if len(modules) != len(set(modules)):
                raise ValueError("Duplicate graph module")
            if any(len(m.split(":")) != 3 or not all(m.split(":")) for m in modules):
                raise ValueError("Invalid module coordinate")
            result[key] = row
    if not result or (":", "buildscript", "classpath") not in result:
        raise ValueError("Missing root classpath")
    return result


def scan(coords, query=request_osv):
    results = {}
    for offset in range(0, len(coords), 50):
        batch = coords[offset:offset+50]
        try:
            results.update(osv_query(batch, query))
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            results.update({c: {"status": "UNKNOWN", "error": type(exc).__name__} for c in batch})
    return results


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    baseline_rows, baseline_graph = load_inventory(args.baseline, "android")
    with zipfile.ZipFile(args.baseline) as z:
        old_rows = json.loads(z.read("graph.json"))
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    result = {"sourceCommit": source, "candidate": {"agp": AGP, "gradle": GRADLE},
              "trust": "UNREVIEWED", "commands": {}, "graph": None, "metadata": None, "osv": None}
    try:
        with tempfile.TemporaryDirectory(prefix="aura-upstream-pilot-") as folder:
            temp = Path(folder)
            work = temp / "source"
            work.mkdir()
            archive = temp / "source.tar"
            subprocess.run(["git", "archive", "--format=tar", "-o", str(archive), source],
                           cwd=ROOT, check=True, timeout=60)
            subprocess.run(["tar", "-xf", str(archive), "-C", str(work)], check=True, timeout=60)
            result["scratchChanges"] = patch_candidate(work)
            write_json(output / "scratch-changes.json", result["scratchChanges"])
            env = dict(os.environ)
            # No archive retrieval token is passed to the build process.
            for key in ("GH_TOKEN", "GITHUB_TOKEN", "ACTIONS_RUNTIME_TOKEN"):
                env.pop(key, None)
            env["GRADLE_USER_HOME"] = str(temp / "gradle-home")
            parts_dir = output / "graph-parts"
            parts_dir.mkdir()
            env["AURA_INVENTORY_GRAPH_DIR"] = str(parts_dir)
            cmd = [str(work / "gradlew"), "-p", str(work), "--no-daemon", "--console=plain", "--no-build-cache"]
            result["commands"]["version"] = run_logged(cmd + ["--version"], work, env, output / "version.log")
            if result["commands"]["version"]:
                raise ValueError("Candidate Gradle bootstrap failed")
            result["commands"]["graph"] = run_logged(cmd + ["--no-parallel", "-I",
                str(work / "tools/gradle_inventory.init.gradle"), ":auraAuditDependencyGraph",
                ":apps:auraAuditDependencyGraph", ":apps:watchface:auraAuditDependencyGraph"],
                work, env, output / "graph.log")
            if result["commands"]["graph"]:
                raise ValueError("Candidate graph command failed")
            parts = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(parts_dir.glob("*.json"))]
            index = graph_index(parts)
            rows = list(index.values())
            modules = {m for r in rows for m in r["modules"]}
            if "com.android.tools.build:gradle:" + AGP not in modules:
                raise ValueError("Candidate AGP missing from graph")
            write_json(output / "graph.json", rows)
            old_keys = {(r["project"], r["scope"], r["configuration"]) for r in old_rows}
            result["graph"] = {"configurations": len(rows), "modules": len(modules),
                               "addedConfigurations": sorted(set(index) - old_keys),
                               "removedConfigurations": sorted(old_keys - set(index)),
                               "addedModules": sorted(modules - baseline_graph),
                               "removedModules": sorted(baseline_graph - modules)}
            tasks = [f":apps:watchface:assembleWff{n}{kind}" for n in (2, 3, 4, 5) for kind in ("Debug", "Release")]
            result["commands"]["metadata"] = run_logged(cmd + ["--write-verification-metadata", "sha256", *tasks],
                                                        work, env, output / "metadata-build.log")
            metadata = work / "gradle/verification-metadata.xml"
            coords = set(modules)
            if metadata.is_file():
                raw = metadata.read_bytes()
                (output / "verification-metadata.UNREVIEWED.xml").write_bytes(raw)
                artifacts = summarize_metadata(metadata)
                write_json(output / "artifacts.json", artifacts)
                coords.update(r["coordinate"] for r in artifacts)
                result["metadata"] = {"sha256": sha(raw), "artifacts": len(artifacts),
                                      "components": len({r["coordinate"] for r in artifacts})}
                metadata.unlink()
            old_coords = {r["coordinate"] for r in baseline_rows}
            results = scan(sorted(coords))
            write_json(output / "osv-results.json", results)
            result["osv"] = {"counts": dict(Counter(r["status"] for r in results.values())),
                             "ids": sorted({i for r in results.values() for i in r.get("ids", [])}),
                             "newCoordinates": sorted(coords - old_coords),
                             "removedCoordinates": sorted(old_coords - coords)}
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        result["error"] = str(exc)
    finally:
        write_json(output / "summary.json", result)
        print("F03_R11", json.dumps(result, sort_keys=True), flush=True)
    if (result.get("error") or any(result["commands"].values()) or not result["metadata"]
            or not result["graph"] or not result["osv"]
            or result["osv"]["counts"].get("UNKNOWN") or result["osv"]["counts"].get("MATCH")):
        raise SystemExit("Candidate incomplete or adverse; do not promote")


if __name__ == "__main__":
    main()
