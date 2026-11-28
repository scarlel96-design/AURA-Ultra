#!/usr/bin/env python3
"""Check one directory of Gradle JUnit XML.

The common GitHub workflow does not run this file. CI_PROPOSAL.md shows the
command a coordinator can add. Exit status is 0 only when the directory
matches the expected file count and test count, with no failures, errors, or
skips.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def parse_time(value: str | None, label: str) -> datetime:
    if value is None or value.strip() == "":
        fail(f"missing timestamp: {label}")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as ex:
        fail(f"unreadable timestamp in {label}: {ex}")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_count(raw: str | None, label: str) -> int:
    try:
        return int(raw if raw is not None else "")
    except ValueError as ex:
        fail(f"bad count for {label}: {ex}")


def require_count(attributes: dict[str, str], name: str, label: str) -> int:
    if name not in attributes:
        fail(f"missing count for {label}: {name}")
    return parse_count(attributes.get(name), f"{label} {name}")


def check_directory(
    directory: Path,
    files_expected: int,
    tests_expected: int,
    not_before: datetime | None,
    not_after: datetime | None,
) -> None:
    if not directory.is_dir():
        fail(f"missing directory: {directory}")
    files = sorted(path for path in directory.glob("TEST-*.xml") if path.is_file())
    if not files:
        fail(f"no JUnit XML: {directory}")
    if len(files) != files_expected:
        fail(f"file count {len(files)} != {files_expected}")
    suite_names: list[str] = []
    seen_cases: set[tuple[str, str]] = set()
    pending_names: list[tuple[str, str]] = []
    tests = failures = errors = skipped = 0
    for path in files:
        raw = path.read_bytes()
        if raw.strip() == b"":
            fail(f"empty XML: {path.name}")
        try:
            root = ET.fromstring(raw)
        except ET.ParseError as ex:
            fail(f"corrupt XML: {path.name}: {ex}")
        if root.tag != "testsuite":
            fail(f"unexpected root <{root.tag}> in {path.name}")
        suite_name = root.attrib.get("name", "")
        if suite_name == "":
            fail(f"missing suite name in {path.name}")
        suite_names.append(suite_name)
        header_tests = require_count(root.attrib, "tests", path.name)
        header_failures = require_count(root.attrib, "failures", path.name)
        header_errors = require_count(root.attrib, "errors", path.name)
        header_skipped = require_count(root.attrib, "skipped", path.name)
        if header_tests <= 0:
            fail(f"discovered no tests in {path.name}")
        direct_cases = [child for child in list(root) if child.tag == "testcase"]
        if len(list(root.iter("testcase"))) != len(direct_cases):
            fail(f"nested testcase in {path.name}")
        cases = direct_cases
        if len(cases) != header_tests:
            fail(f"header tests {header_tests} != testcase count {len(cases)} in {path.name}")
        failure_cases = [case for case in cases if case.find("failure") is not None]
        error_cases = [case for case in cases if case.find("error") is not None]
        skipped_cases = [case for case in cases if case.find("skipped") is not None]
        if header_failures != len(failure_cases):
            fail(f"hidden or mismatched failures in {path.name}")
        if header_errors != len(error_cases):
            fail(f"hidden or mismatched errors in {path.name}")
        if header_skipped != len(skipped_cases):
            fail(f"hidden or mismatched skips in {path.name}")
        if header_failures != 0 or header_errors != 0 or header_skipped != 0:
            fail(f"failed XML in {path.name}: failures={header_failures} errors={header_errors} skipped={header_skipped}")
        for case in cases:
            classname = case.attrib.get("classname")
            method = case.attrib.get("name")
            if classname is None or classname.strip() == "":
                fail(f"missing classname in {path.name}")
            if method is None or method.strip() == "":
                fail(f"missing method in {path.name}")
            if classname != suite_name:
                fail(f"classname does not match suite in {path.name}")
            identity = (classname, method)
            if identity in seen_cases:
                fail(f"duplicate testcase {identity} in {path.name}")
            seen_cases.add(identity)
        if not_before is not None or not_after is not None:
            stamped = parse_time(root.attrib.get("timestamp"), path.name)
            if not_before is not None and stamped < not_before:
                fail(f"stale XML {path.name}: {stamped.isoformat()} < {not_before.isoformat()}")
            if not_after is not None and stamped > not_after:
                fail(f"future XML {path.name}: {stamped.isoformat()} > {not_after.isoformat()}")
        expected_name = f"TEST-{suite_name}.xml"
        if path.name != expected_name:
            pending_names.append((path.name, expected_name))
        tests += header_tests
        failures += header_failures
        errors += header_errors
        skipped += header_skipped
    if len(suite_names) != len(set(suite_names)):
        fail("duplicate suite name")
    for actual, expected in pending_names:
        fail(f"suite filename mismatch: {actual} != {expected}")
    if (tests, failures, errors, skipped) != (tests_expected, 0, 0, 0):
        fail(f"JUnit {(len(files), tests, failures, errors, skipped)} != {(files_expected, tests_expected, 0, 0, 0)}")
    print(f"OK files={len(files)} tests={tests}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True)
    parser.add_argument("--files", type=int, required=True)
    parser.add_argument("--tests", type=int, required=True)
    parser.add_argument("--not-before", default=None)
    parser.add_argument("--not-after", default=None)
    args = parser.parse_args()
    if args.files <= 0 or args.tests <= 0:
        fail("expected file and test counts must be positive")
    not_before = parse_time(args.not_before, "--not-before") if args.not_before else None
    not_after = parse_time(args.not_after, "--not-after") if args.not_after else None
    if not_before is not None and not_after is not None and not_after < not_before:
        fail("--not-after is earlier than --not-before")
    check_directory(Path(args.dir), args.files, args.tests, not_before, not_after)


if __name__ == "__main__":
    main()
