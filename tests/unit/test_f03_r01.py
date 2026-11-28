"""Check the reviewed Actions policy for the repository's canonical workflow style."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PINS = {
    "actions/checkout": "11d5960a326750d5838078e36cf38b85af677262",
    "actions/setup-java": "cf277c60eb25467037889841efdb72551f06f6c3",
    "actions/setup-python": "a26af69be951a213d495a4c3e4e4022e16d87065",
    "actions/upload-artifact": "ea165f8d65b6e75b540449e92b4886f43607fa02",
    "android-actions/setup-android": "138b5fb1cf087fdb4c5f3c621466fe304d0cf2e3",
}
WORKFLOWS = {
    "bootstrap.yml": ["actions/checkout", "actions/setup-java", "actions/setup-python",
                      "android-actions/setup-android", "actions/upload-artifact",
                      "actions/upload-artifact", "actions/upload-artifact"],
    "doc-budget.yml": ["actions/checkout", "actions/setup-python"],
    "domain-kotlin.yml": ["actions/checkout", "actions/setup-java", "actions/setup-python",
                          "actions/upload-artifact"],
    "reproduce-packaging.yml": ["actions/checkout", "actions/setup-java",
                                "actions/setup-python", "android-actions/setup-android"],
    "windows-repro.yml": ["actions/checkout", "actions/setup-python"],
    "f03-inventory.yml": ["actions/checkout", "actions/setup-java", "actions/setup-python",
                          "android-actions/setup-android", "actions/upload-artifact"],
    "f03-review.yml": ["actions/checkout", "actions/setup-java", "actions/setup-python",
                       "android-actions/setup-android", "actions/upload-artifact"],
}


def action_refs(content):
    """Read canonical block-style uses entries; reject unsupported forms."""
    refs = []
    for line in content.splitlines():
        if line.lstrip().startswith("#"):
            continue
        if re.search(r"\buses\s*:", line):
            match = re.fullmatch(r" +(?:- )?uses: ([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([A-Za-z0-9_.-]+)(?: +#.*)?", line)
            if not match:
                raise ValueError("Unsupported uses entry")
            refs.append(match.groups())
    return refs


def check_pins(content, expected):
    refs = action_refs(content)
    if [name for name, _ in refs] != expected:
        raise ValueError("Unexpected action sequence")
    for name, ref in refs:
        if PINS.get(name) != ref or not re.fullmatch(r"[0-9a-f]{40}", ref):
            raise ValueError("Unreviewed action reference: " + name)


def check_credentials(content):
    lines = content.splitlines()
    checkout = [i for i, line in enumerate(lines)
                if re.fullmatch(r" +(?:- )?uses: actions/checkout@[^ ]+(?: +#.*)?", line)]
    if len(checkout) != 1:
        raise ValueError("Expected exactly one checkout")
    index = checkout[0]
    # All current checkouts use a standalone step followed by a with block.
    if not lines[index].startswith("      - uses:"):
        raise ValueError("Unsupported checkout step style")
    end = next((i for i in range(index + 1, len(lines))
                if lines[i].startswith("      - ")), len(lines))
    block = lines[index + 1:end]
    if block.count("        with:") != 1:
        raise ValueError("Missing or duplicate checkout with block")
    if [line for line in block if re.search(r"\bpersist-credentials\s*:", line)] != [
            "          persist-credentials: false"]:
        raise ValueError("Checkout credentials must not persist")
    if sum(bool(re.search(r"\bpersist-credentials\s*:", line)) for line in lines) != 1:
        raise ValueError("Unexpected credential setting")


def check_permissions(content, workflow=None):
    lines = content.splitlines()
    if [line for line in lines if re.search(r"\bpermissions\s*:", line)] != ["permissions:"]:
        raise ValueError("Unexpected permission override")
    index = lines.index("permissions:")
    expected = ["  contents: read"]
    # Only the audit-only archive retrieval workflow needs Actions read access.
    if workflow == "f03-review.yml":
        expected.append("  actions: read")
    end = index + 1 + len(expected)
    if lines[index + 1:end] != expected:
        raise ValueError("Unexpected permission block")
    if end < len(lines) and lines[end].startswith(" "):
        raise ValueError("Unexpected additional permissions")


class ActionPolicyTests(unittest.TestCase):
    def fixture(self):
        return ("permissions:\n  contents: read\njobs:\n  build:\n    steps:\n"
                "      - uses: actions/checkout@" + PINS["actions/checkout"] + " # v4\n"
                "        with:\n          persist-credentials: false\n"
                "      - name: Test\n        run: python --version\n")

    def test_workflow_inventory(self):
        paths = ROOT / ".github/workflows"
        self.assertEqual({p.name for p in paths.iterdir() if p.suffix in (".yml", ".yaml")},
                         set(WORKFLOWS))

    def test_reviewed_action_pins(self):
        for name, expected in WORKFLOWS.items():
            with self.subTest(workflow=name):
                check_pins((ROOT / ".github/workflows" / name).read_text(encoding="utf-8"), expected)

    def test_checkout_credentials_disabled(self):
        for name in WORKFLOWS:
            with self.subTest(workflow=name):
                check_credentials((ROOT / ".github/workflows" / name).read_text(encoding="utf-8"))

    def test_read_only_permissions(self):
        for name in WORKFLOWS:
            with self.subTest(workflow=name):
                check_permissions((ROOT / ".github/workflows" / name).read_text(encoding="utf-8"), name)

    def test_historical_checkout_preserved(self):
        content = (ROOT / ".github/workflows/reproduce-packaging.yml").read_text(encoding="utf-8")
        self.assertIn("          ref: 95e51cca23210f930dc3716cb790e791585a7bf0\n", content)

    def test_policy_accepts_reviewed_fixture(self):
        content = self.fixture()
        check_pins(content, ["actions/checkout"])
        check_credentials(content)
        check_permissions(content)

    def test_mutable_or_unreviewed_reference_rejected(self):
        for ref in ("v4", "main", "0" * 40):
            with self.subTest(ref=ref):
                with self.assertRaises(ValueError):
                    check_pins(self.fixture().replace(PINS["actions/checkout"], ref),
                               ["actions/checkout"])

    def test_missing_or_duplicate_credential_setting_rejected(self):
        content = self.fixture()
        for replacement in ("", "          persist-credentials: true\n",
                            "          persist-credentials: false\n          persist-credentials: false\n"):
            with self.subTest(replacement=replacement):
                with self.assertRaises(ValueError):
                    check_credentials(content.replace("          persist-credentials: false\n", replacement))

    def test_audit_archive_read_is_narrowly_scoped(self):
        base = self.fixture()
        audit = base.replace("contents: read", "contents: read\n  actions: read")
        check_permissions(audit, "f03-review.yml")
        with self.assertRaises(ValueError):
            check_permissions(audit, "bootstrap.yml")
        with self.assertRaises(ValueError):
            check_permissions(base, "f03-review.yml")
        for extra in ("  actions: write", "  actions: read\n  packages: read"):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                check_permissions(base.replace("contents: read", "contents: read\n" + extra),
                                  "f03-review.yml")

    def test_write_permissions_rejected(self):
        for content in (self.fixture().replace("contents: read", "contents: write"),
                        self.fixture().replace("contents: read", "contents: read\n  actions: write"),
                        self.fixture().replace("  build:", "  build:\n    permissions: write-all")):
            with self.assertRaises(ValueError):
                check_permissions(content)


if __name__ == "__main__":
    unittest.main()
