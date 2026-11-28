"""Materialize selected committed build inputs without copying the worktree."""
import os
import re
import stat
import subprocess
from pathlib import Path, PurePosixPath


def git(root, *args):
    return subprocess.check_output(
        ["git", "--no-replace-objects", *args], cwd=root, timeout=60)


def clean_commit(root):
    entries = git(root, "ls-files", "-v", "-z")
    if entries and not entries.endswith(b"\0"):
        raise ValueError("Invalid Git index listing")
    # H is a normal tracked entry. Lowercase tags hide assume-unchanged.
    # S/s identifies skip-worktree. Reject every unsupported tag.
    if any(not item.startswith(b"H ") for item in entries.split(b"\0") if item):
        raise ValueError("Unsupported Git index flags; use a clean full checkout")
    if git(root, "status", "--porcelain", "--untracked-files=no").strip():
        raise ValueError("Tracked worktree changes; commit before bundling")
    commit = git(root, "rev-parse", "HEAD").decode("ascii").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Invalid source commit")
    return commit


def copy_committed_inputs(source, destination, commit, files, directories):
    """Copy regular Git blobs into an exclusively owned, empty directory."""
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Invalid source commit")
    destination = Path(destination)
    info = destination.lstat()
    reparse = getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if not stat.S_ISDIR(info.st_mode) or reparse or any(destination.iterdir()):
        raise ValueError("Destination must be a new empty private directory")
    # The caller must exclusively control this directory throughout the copy.
    # Do not accept preexisting child directories, links, or files.
    raw = git(source, "ls-tree", "-r", "-z", commit, "--", *files, *directories)
    if not raw or not raw.endswith(b"\0"):
        raise ValueError("Missing committed build inputs")
    entries = {}
    folded = set()
    for item in raw[:-1].split(b"\0"):
        header, name = item.split(b"\t", 1)
        mode, kind, oid = header.decode("ascii").split()
        path = name.decode("utf-8")
        parts = path.split("/")
        if (any(part in ("", ".", "..") or "\\" in part or ":" in part for part in parts)
                or PurePosixPath(path).is_absolute()):
            raise ValueError("Invalid committed input path")
        if path not in files and not any(path.startswith(d+"/") for d in directories):
            raise ValueError("Unexpected committed input")
        if mode not in ("100644", "100755") or kind != "blob":
            raise ValueError("Non-regular committed input: " + path)
        if path.casefold() in folded:
            raise ValueError("Duplicate or case-colliding input: " + path)
        folded.add(path.casefold())
        entries[path] = (mode, oid)
    if not set(files) <= set(entries) or any(
            not any(p.startswith(d+"/") for p in entries) for d in directories):
        raise ValueError("Incomplete committed build inputs")
    for path, (mode, oid) in sorted(entries.items()):
        target = Path(destination).joinpath(*path.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(git(source, "cat-file", "blob", oid))
        if os.name != "nt":
            target.chmod(0o755 if mode == "100755" else 0o644)
    return len(entries)
