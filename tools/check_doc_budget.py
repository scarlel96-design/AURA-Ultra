"""Enforce byte limits for active operating documents, not historical evidence."""
import json
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIMITS = {
    "AGENTS.md": 8 * 1024,
    "docs/STATUS.md": 8 * 1024,
    "docs/operations/WORK_LOG.md": 10 * 1024,
    "docs/operations/BLOCKERS.md": 8 * 1024,
    "docs/operations/agent-orders/README.md": 5 * 1024,
    "docs/operations/GPT_EXECUTION_PLAN.md": 10 * 1024,
    **{f"docs/operations/GPT-{n:02}.md": 10 * 1024 for n in range(1, 7)},
}


def check(root=ROOT):
    records, errors = {}, []
    for name, limit in sorted(LIMITS.items()):
        path = root / name
        try:
            # Reject symlinks in the entire relative path.
            for parent in path.relative_to(root).parents:
                if not stat.S_ISDIR((root / parent).lstat().st_mode):
                    raise ValueError("Non-directory parent")
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("Not a regular file")
            size = info.st_size
            if size == 0 or size > limit:
                raise ValueError(f"{size} bytes; expected 1..{limit}")
            records[name] = {"bytes": size, "limit": limit}
        except (OSError, ValueError) as exc:
            errors.append(f"{name}: {exc}")
    # Apply the same limit to future GPT execution specifications.
    folder = root / "docs/operations"
    if folder.is_dir() and not folder.is_symlink():
        for path in sorted(folder.glob("GPT-[0-9][0-9].md")):
            name = path.relative_to(root).as_posix()
            if name in LIMITS:
                continue
            try:
                info = path.lstat()
                limit = 10 * 1024
                if not stat.S_ISREG(info.st_mode) or not 1 <= info.st_size <= limit:
                    raise ValueError("Invalid file or byte limit")
                records[name] = {"bytes": info.st_size, "limit": limit}
            except (OSError, ValueError) as exc:
                errors.append(f"{name}: {exc}")
    if errors:
        raise ValueError("\n".join(errors))
    return records


def main():
    try:
        print("DOC_BUDGET_RESULT " + json.dumps(check(), sort_keys=True))
    except ValueError as exc:
        print("FAIL: " + str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
