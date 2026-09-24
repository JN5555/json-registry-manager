from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


def _run(cwd: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise GitError("git executable not found") from exc
    if result.returncode != 0:
        raise GitError((result.stderr or result.stdout or "unknown git error").strip())
    return result.stdout.rstrip()


def is_repo(cwd: Path) -> bool:
    try:
        return _run(cwd, "rev-parse", "--is-inside-work-tree").strip() == "true"
    except GitError:
        return False


def diff(cwd: Path) -> str:
    return _run(cwd, "diff", "--", ".")


def status_short(cwd: Path) -> str:
    return _run(cwd, "status", "--short")


def commit(cwd: Path, message: str, paths: list[Path] | None = None) -> str:
    if paths:
        _run(cwd, "add", *[str(p) for p in paths])
    else:
        _run(cwd, "add", ".")
    return _run(cwd, "commit", "-m", message)


def push(cwd: Path) -> str:
    return _run(cwd, "push")
