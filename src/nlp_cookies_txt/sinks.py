"""Output sinks. Cookies are credential-equivalent, so file output defaults to
mode 0600 and refuses to overwrite into a git-tracked path without --force.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _looks_git_tracked(path: Path) -> bool:
    p = path.resolve().parent
    for parent in [p, *p.parents]:
        if (parent / ".git").exists():
            return True
    return False


def write_file(text: str, path: str, force: bool = False) -> None:
    dest = Path(path)
    if _looks_git_tracked(dest) and not force:
        raise RuntimeError(
            "Refusing to write cookies into a git-tracked directory (%s). "
            "Cookies are credential-equivalent. Use --force to override, and "
            "make sure the file is git-ignored." % dest.parent
        )
    # Create with restrictive perms from the start (avoid a brief 0644 window).
    fd = os.open(str(dest), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)


def write_stdout(text: str) -> None:
    sys.stdout.write(text)


def to_cookiejar(text: str, path: str) -> None:
    """Materialize as a loadable http.cookiejar.MozillaCookieJar (verification helper)."""
    from http.cookiejar import MozillaCookieJar

    write_file(text, path, force=True)
    jar = MozillaCookieJar(path)
    jar.load(ignore_discard=True, ignore_expires=True)
