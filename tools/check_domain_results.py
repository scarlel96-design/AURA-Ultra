"""Validate executed JUnit test evidence, not just the Gradle exit status."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BASELINE = {"DraftContractTest": 12, "FreshnessTest": 11, "IdentityTest": 5,
            "PipelineTest": 5, "RevisionGateTest": 15, "SourceScanTest": 1, "ValidationTest": 32}


def verify(directory):
    counts = {}
    seen = set()
    total = 0
    for path in sorted(directory.glob("TEST-*.xml")):
        root = ET.parse(path).getroot()
        if root.tag != "testsuite" or not root.get("name"):
            raise ValueError("Invalid test suite: " + str(path))
        name = root.get("name")
        if name in counts:
            raise ValueError("Duplicate suite: " + name)
        cases = root.findall("testcase")
        n = int(root.attrib["tests"])
        if n <= 0 or n != len(cases):
            raise ValueError("Invalid test count: " + name)
        if any(int(root.attrib[key]) != 0 for key in ("failures", "errors", "skipped")):
            raise ValueError("Nonpassing suite: " + name)
        for case in cases:
            key = (case.get("classname"), case.get("name"))
            if not all(key) or key in seen or any(case.find(tag) is not None for tag in ("failure", "error", "skipped")):
                raise ValueError("Invalid, duplicate or nonpassing testcase: " + str(key))
            seen.add(key)
        counts[name] = n
        total += n
    prefix = "io.github.scarlel96.aura.domain."
    for name, minimum in BASELINE.items():
        if counts.get(prefix + name, 0) < minimum:
            raise ValueError("Missing baseline tests: " + name)
    return total


if __name__ == "__main__":
    print(f"DOMAIN_RESULT {verify(Path(sys.argv[1]))} PASS / 0 FAIL / 0 ERROR / 0 SKIP")
