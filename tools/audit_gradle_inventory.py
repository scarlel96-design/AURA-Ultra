"""Collect provisional Gradle evidence. Do not install a trust baseline."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {"v": "https://schema.gradle.org/dependency-verification"}


def run_logged(command, cwd, env, path):
    with path.open("wb") as log:
        result = subprocess.run(command, cwd=cwd, env=env, stdout=log,
                                stderr=subprocess.STDOUT, timeout=1200)
    print(f"INVENTORY_COMMAND {path.name} exit={result.returncode}", flush=True)
    return result.returncode


def summarize_metadata(path):
    root = ET.parse(path).getroot()
    if root.tag != "{" + NS["v"] + "}verification-metadata":
        raise ValueError("Unexpected verification metadata namespace")
    rows = []
    for component in root.findall("./v:components/v:component", NS):
        coordinate = ":".join(component.attrib[k] for k in ("group", "name", "version"))
        for artifact in component.findall("v:artifact", NS):
            hashes = sorted({x.attrib["value"] for x in artifact.findall("v:sha256", NS)})
            rows.append({"coordinate": coordinate, "artifact": artifact.attrib["name"],
                         "sha256": hashes, "trust": "UNREVIEWED"})
    if not rows or any(not row["sha256"] for row in rows):
        raise ValueError("Empty or incomplete provisional checksum inventory")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", choices=("android", "domain"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                     text=True).strip()
    result = {"sourceCommit": source, "build": args.build, "trust": "UNREVIEWED",
              "commands": {}, "metadata": None, "graph": None}
    with tempfile.TemporaryDirectory(prefix="aura-inventory-") as folder:
        temp = Path(folder)
        work = temp / "source"
        work.mkdir()
        archive = temp / "source.tar"
        subprocess.run(["git", "archive", "--format=tar", "-o", str(archive), source],
                       cwd=ROOT, check=True, timeout=60)
        subprocess.run(["tar", "-xf", str(archive), "-C", str(work)],
                       check=True, timeout=60)
        env = dict(os.environ)
        env["GRADLE_USER_HOME"] = str(temp / "gradle-home")
        graph_dir = output / "graph-parts"
        graph_dir.mkdir()
        env["AURA_INVENTORY_GRAPH_DIR"] = str(graph_dir)
        build = work if args.build == "android" else work / "modules/domain"
        metadata = build / "gradle/verification-metadata.xml"
        if metadata.exists():
            raise ValueError("Refuse to overwrite an existing trust baseline")
        command = [str(work / "gradlew"), "-p", str(build), "--no-daemon",
                   "--console=plain", "--no-build-cache"]
        tasks = ([f":apps:watchface:assembleWff{n}{kind}"
                  for n in (2, 3, 4, 5) for kind in ("Debug", "Release")]
                 if args.build == "android" else ["clean", "test"])
        result["commands"]["metadata"] = run_logged(
            command + ["--write-verification-metadata", "sha256", *tasks],
            work, env, output / "metadata-build.log")
        if metadata.exists():
            data = metadata.read_bytes()
            (output / "verification-metadata.UNREVIEWED.xml").write_bytes(data)
            rows = summarize_metadata(metadata)
            (output / "artifacts.json").write_text(
                json.dumps(rows, indent=2) + "\n", encoding="utf-8")
            result["metadata"] = {"sha256": hashlib.sha256(data).hexdigest(),
                                  "artifacts": len(rows),
                                  "components": len({r["coordinate"] for r in rows})}
            # Never use generated values as approved metadata.
            metadata.unlink()
        projects = (":", ":apps", ":apps:watchface") if args.build == "android" else (":",)
        graph_tasks = [p.rstrip(":") + ":auraAuditDependencyGraph" for p in projects]
        result["commands"]["graph"] = run_logged(
            command + ["--no-parallel", "-I", str(work / "tools/gradle_inventory.init.gradle"),
                       *graph_tasks], work, env, output / "graph.log")
        parts = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(graph_dir.glob("*.json"))]
        actual_projects = [p["project"] for p in parts]
        rows = [r for part in parts for r in part["rows"]]
        keys = [(r["project"], r["scope"], r["configuration"]) for r in rows]
        if (sorted(actual_projects) == sorted(projects) and len(keys) == len(set(keys))
                and all(r["project"] == part["project"] for part in parts for r in part["rows"])):
            (output / "graph.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
            result["graph"] = {"configurations": len(rows),
                               "unresolved": sum(bool(r["unresolved"] or r["error"]) for r in rows),
                               "modules": len({m for r in rows for m in r["modules"]}),
                               "projects": actual_projects}
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n",
                                         encoding="utf-8")
    print(json.dumps(result, sort_keys=True), flush=True)
    if any(result["commands"].values()) or not result["metadata"] or not result["graph"]:
        raise SystemExit("Inventory incomplete; inspect the uploaded evidence")
    if result["graph"]["unresolved"]:
        raise SystemExit("Unresolved configurations require review")


if __name__ == "__main__":
    main()
