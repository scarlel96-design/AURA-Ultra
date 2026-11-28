"""Validate fixed Intelligence JUnit inventories; never infer a profile from XML."""
import argparse
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

PREFIX = "io.github.scarlel96.aura.intelligence."
BRANCH = "agent/grok/GB-02-RV02"
INVENTORY = json.loads(Path(__file__).with_name("intelligence_test_inventory.json").read_text(encoding="utf-8"))


def expected_methods(profile):
    if profile not in ("g01", "rv02"):
        raise ValueError("Unknown Intelligence inventory")
    suites = dict(INVENTORY["g01"])
    if profile == "rv02":
        if suites.keys() & INVENTORY["rv02"].keys():
            raise ValueError("Overlapping Intelligence inventories")
        suites.update(INVENTORY["rv02"])
    expected = {PREFIX + name: frozenset(methods) for name, methods in suites.items()}
    count = 108 if profile == "g01" else 124
    if any(len(expected[PREFIX + name]) != len(methods) for name, methods in suites.items()):
        raise ValueError("Duplicate inventory method")
    if sum(map(len, expected.values())) != count:
        raise ValueError("Invalid inventory count")
    return expected


def ci_profile(event, ref, head_ref, head_repo, repository):
    if not repository:
        raise ValueError("Missing repository context")
    if event in ("push", "workflow_dispatch") and ref == "refs/heads/" + BRANCH:
        return "rv02"
    if event == "pull_request" and head_ref == BRANCH and head_repo == repository:
        return "rv02"
    raise ValueError("Unregistered Intelligence CI context")


def verify(directory, profile):
    expected = expected_methods(profile)
    seen = set()
    for path in sorted(directory.glob("*.xml")):
        root = ET.parse(path).getroot()
        suite = root.get("name")
        if root.tag != "testsuite" or suite not in expected or suite in seen:
            raise ValueError("Unknown or duplicate suite")
        if path.name != "TEST-" + suite + ".xml":
            raise ValueError("Suite filename mismatch")
        if root.get("tests") != str(len(expected[suite])) or any(root.get(k) != "0" for k in ("failures", "errors", "skipped")):
            raise ValueError("Invalid or nonpassing suite counters")
        methods = set()
        metadata = set()
        for child in root:
            if child.tag == "testcase":
                method = child.get("name")
                if child.get("classname") != suite or method not in expected[suite] or method in methods or len(child):
                    raise ValueError("Invalid, duplicate or nonpassing testcase")
                methods.add(method)
            else:
                if child.tag not in ("properties", "system-out", "system-err") or child.tag in metadata:
                    raise ValueError("Unexpected suite child")
                metadata.add(child.tag)
                if child.tag == "properties":
                    if any(p.tag != "property" or len(p) for p in child):
                        raise ValueError("Invalid suite properties")
                elif len(child):
                    raise ValueError("Nested log element")
        if methods != expected[suite]:
            raise ValueError("Missing test identity")
        seen.add(suite)
    if seen != set(expected):
        raise ValueError("Missing suite")
    return sum(map(len, expected.values()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--profile", choices=("g01", "rv02"))
    mode.add_argument("--ci", action="store_true")
    args = parser.parse_args()
    profile = args.profile
    if args.ci:
        profile = ci_profile(*(os.environ.get(k, "") for k in (
            "GITHUB_EVENT_NAME", "GITHUB_REF", "GITHUB_HEAD_REF", "RV02_HEAD_REPO", "GITHUB_REPOSITORY")))
    print(f"INTELLIGENCE_INVENTORY {profile}", flush=True)
    print(f"INTELLIGENCE_RESULT {verify(args.directory, profile)} PASS / 0 FAIL / 0 ERROR / 0 SKIP")


if __name__ == "__main__":
    main()
