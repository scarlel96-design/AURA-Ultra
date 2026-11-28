"""Materialize the fixed RV01 Domain and current Intelligence in a fresh CI tree."""
import argparse
import hashlib
import subprocess
from pathlib import Path, PurePosixPath

DOMAIN_COMMIT = "558e18804d08ebd4d79be620962c256e0af07f96"
DOMAIN_TREE = "c51dfeb3fe4e87201f123cd89aceb48b373a0aaf"


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def module_files(repo, commit, module, expected_tree=None):
    if module not in ("modules/domain", "modules/intelligence"):
        raise ValueError("Unapproved module")
    tree = git(repo, "rev-parse", "--verify", f"{commit}:{module}").decode().strip()
    if expected_tree is not None and tree != expected_tree:
        raise ValueError("Wrong module tree")
    files = {}
    for entry in git(repo, "ls-tree", "-r", "-z", commit, "--", module).split(b"\0"):
        if not entry:
            continue
        info, raw_path = entry.split(b"\t", 1)
        mode, kind, oid = info.decode().split()
        path = raw_path.decode("utf-8")
        parts = PurePosixPath(path).parts
        if (mode not in ("100644", "100755") or kind != "blob" or not path.startswith(module + "/")
                or ".." in parts or "\\" in path or ":" in path or path in files):
            raise ValueError("Unsafe module entry")
        files[path] = (mode, oid)
    if not files:
        raise ValueError("Empty module")
    return tree, files


def blob_hash(data):
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def materialize(repo, output, verify_only=False):
    head = git(repo, "rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    pinned = git(repo, "rev-parse", "--verify", DOMAIN_COMMIT + "^{commit}").decode().strip()
    if pinned != DOMAIN_COMMIT:
        raise ValueError("Wrong Domain commit")
    domain_tree, domain = module_files(repo, pinned, "modules/domain", DOMAIN_TREE)
    intel_tree, intel = module_files(repo, head, "modules/intelligence")
    if len(domain) != 26:
        raise ValueError("Wrong Domain file count")
    if not verify_only:
        output.mkdir(parents=True, exist_ok=False)
    for path, (mode, oid) in {**domain, **intel}.items():
        target = output / path
        if not verify_only:
            data = git(repo, "cat-file", "blob", oid)
            if blob_hash(data) != oid:
                raise ValueError("Git blob mismatch")
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(data)
            target.chmod(0o755 if mode == "100755" else 0o644)
        if target.is_symlink() or not target.is_file() or blob_hash(target.read_bytes()) != oid:
            raise ValueError("Composite source mismatch: " + path)
    print(f"RV02_DOMAIN commit={pinned} tree={domain_tree} files={len(domain)}")
    print(f"RV02_INTELLIGENCE commit={head} tree={intel_tree} files={len(intel)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    materialize(args.repo, args.output, args.verify_only)


if __name__ == "__main__":
    main()
