"""Exercise strict Gradle locking and verification in disposable trees only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

from audit_gradle_inventory import ROOT, run_logged


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(command, cwd, env, output, name):
    return run_logged(command, cwd, env, output / (name + ".log"))


def fixture(wrapper, work, env, output):
    root = work / "fixture"
    root.mkdir()
    repo = root / "repository" / "aura" / "audit" / "demo" / "1.0"
    repo.mkdir(parents=True)
    jar = repo / "demo-1.0.jar"

    def write_jar(payload):
        with zipfile.ZipFile(jar, "w", compression=zipfile.ZIP_STORED) as z:
            z.writestr("payload.txt", payload)

    write_jar("approved synthetic bytes")
    original = jar.read_bytes()
    (repo / "demo-1.0.pom").write_text(
        '<project xmlns="http://maven.apache.org/POM/4.0.0">'
        '<modelVersion>4.0.0</modelVersion><groupId>aura.audit</groupId>'
        '<artifactId>demo</artifactId><version>1.0</version></project>\n',
        encoding="utf-8")
    (root / "settings.gradle").write_text("rootProject.name = 'audit-fixture'\n", encoding="utf-8")
    (root / "build.gradle").write_text(
        "repositories { maven { url = uri('repository') } }\n"
        "configurations { audit }\n"
        "dependencies { audit 'aura.audit:demo:1.0' }\n"
        "dependencyLocking { lockAllConfigurations(); lockMode = LockMode.STRICT }\n"
        "tasks.register('probe') { doLast { configurations.audit.files.each { println(it.name) } } }\n",
        encoding="utf-8")
    cmd = [str(wrapper), "-p", str(root), "--no-daemon", "--console=plain", "--no-build-cache"]
    result = {}
    result["generate"] = run(cmd + ["--write-locks", "--write-verification-metadata", "sha256", "probe"],
                             root, env, output, "fixture-generate")
    lock = root / "gradle.lockfile"
    metadata = root / "gradle/verification-metadata.xml"
    if result["generate"] or not lock.is_file() or not metadata.is_file():
        return result
    result["knownBytesHash"] = sha(original)
    result["knownBytesInMetadata"] = sha(original) in metadata.read_text(encoding="utf-8")
    (output / "fixture-gradle.lockfile").write_bytes(lock.read_bytes())
    (output / "fixture-verification.xml").write_bytes(metadata.read_bytes())
    strict = cmd + ["--dependency-verification=strict", "--refresh-dependencies", "probe"]
    result["positive"] = run(strict, root, env, output, "fixture-positive")
    write_jar("changed synthetic bytes")
    result["tamperExit"] = run(strict, root, env, output, "fixture-tamper")
    log = (output / "fixture-tamper.log").read_text(encoding="utf-8", errors="replace").lower()
    result["tamperRejected"] = (result["tamperExit"] != 0
                               and "dependency verification failed" in log
                               and "demo-1.0.jar" in log)
    jar.write_bytes(original)
    result["restored"] = run(strict, root, env, output, "fixture-restored")
    lock.unlink()
    result["missingLockExit"] = run(strict, root, env, output, "fixture-missing-lock")
    log = (output / "fixture-missing-lock.log").read_text(encoding="utf-8", errors="replace").lower()
    result["missingLockRejected"] = (result["missingLockExit"] != 0
                                    and ("lock state" in log or "lock file" in log))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", choices=("android", "domain"), required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    summary = json.loads((args.inventory / "summary.json").read_text(encoding="utf-8"))
    provisional = (args.inventory / "verification-metadata.UNREVIEWED.xml").read_bytes()
    if (summary["sourceCommit"] != source or summary["build"] != args.build
            or summary["trust"] != "UNREVIEWED" or summary["graph"]["unresolved"]
            or summary["metadata"]["sha256"] != sha(provisional)):
        raise ValueError("Inventory does not match the exact audit build")
    result = {"sourceCommit": source, "build": args.build, "trust": "UNREVIEWED",
              "commands": {}, "lockfiles": [], "fixture": None}
    with tempfile.TemporaryDirectory(prefix="aura-lock-pilot-") as folder:
        temp = Path(folder)
        work = temp / "source"
        work.mkdir()
        archive = temp / "source.tar"
        subprocess.run(["git", "archive", "--format=tar", "-o", str(archive), source],
                       cwd=ROOT, check=True, timeout=60)
        subprocess.run(["tar", "-xf", str(archive), "-C", str(work)], check=True, timeout=60)
        env = dict(os.environ, GRADLE_USER_HOME=str(temp / "gradle-home"))
        graph_dir = output / "lock-graph-parts"
        graph_dir.mkdir()
        env["AURA_INVENTORY_GRAPH_DIR"] = str(graph_dir)
        build = work if args.build == "android" else work / "modules/domain"
        wrapper = work / "gradlew"
        metadata = build / "gradle/verification-metadata.xml"
        if metadata.exists() or list(build.rglob("*.lockfile")):
            raise ValueError("Refuse to overwrite an existing baseline")
        projects = (":", ":apps", ":apps:watchface") if args.build == "android" else (":",)
        graph_tasks = [p.rstrip(":") + ":auraAuditDependencyGraph" for p in projects]
        tasks = ([f":apps:watchface:assembleWff{n}{kind}"
                  for n in (2, 3, 4, 5) for kind in ("Debug", "Release")]
                 if args.build == "android" else ["clean", "test"])
        cmd = [str(wrapper), "-p", str(build), "--no-daemon", "--no-parallel", "--console=plain",
               "--no-build-cache", "-I", str(work / "tools/gradle_lock_pilot.init.gradle"),
               "-I", str(work / "tools/gradle_inventory.init.gradle")]
        result["commands"]["writeLocks"] = run(cmd + ["--write-locks", *graph_tasks, *tasks],
                                                 work, env, output, "write-locks")
        parts = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(graph_dir.glob("*.json"))]
        rows = [r for part in parts for r in part["rows"]]
        keys = [(r["project"], r["scope"], r["configuration"]) for r in rows]
        result["graph"] = {"projects": [p["project"] for p in parts], "configurations": len(rows),
                           "unresolved": sum(bool(r["unresolved"] or r["error"]) for r in rows),
                           "unique": len(keys) == len(set(keys))}
        locks = sorted(build.rglob("*.lockfile"))
        for path in locks:
            relative = path.relative_to(build)
            data = path.read_bytes()
            destination = output / "UNREVIEWED-locks" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            result["lockfiles"].append({"path": relative.as_posix(), "sha256": sha(data),
                                       "bytes": len(data)})
        if (result["commands"]["writeLocks"] == 0 and locks
                and sorted(result["graph"]["projects"]) == sorted(projects)
                and result["graph"]["configurations"] == summary["graph"]["configurations"]
                and result["graph"]["unresolved"] == 0 and result["graph"]["unique"]):
            metadata.parent.mkdir(parents=True, exist_ok=True)
            metadata.write_bytes(provisional)
            # This tests mechanics only against unreviewed bytes in a scratch tree.
            result["commands"]["strictPilot"] = run(
                cmd + ["--dependency-verification=strict", "--rerun-tasks", *graph_tasks, *tasks],
                work, env, output, "strict-pilot")
            result["lockBytesUnchanged"] = all(
                sha((build / row["path"]).read_bytes()) == row["sha256"]
                for row in result["lockfiles"])
        if args.build == "domain":
            result["fixture"] = fixture(wrapper, temp, env, output)
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("F03_LOCK_PILOT_RESULT", json.dumps(result, sort_keys=True), flush=True)
    f = result["fixture"]
    fixture_ok = (args.build != "domain" or f and f.get("knownBytesInMetadata")
                  and f.get("positive") == 0 and f.get("tamperRejected")
                  and f.get("restored") == 0 and f.get("missingLockRejected"))
    if (result["commands"].get("strictPilot") != 0
            or not result.get("lockBytesUnchanged") or not fixture_ok):
        raise SystemExit("Lock pilot incomplete; inspect evidence. Do not promote metadata.")


if __name__ == "__main__":
    main()
