"""Login-timing: wait until an expected auth cookie exists before exporting.

Auth cookies often appear only after the POST + redirect chain settles, so a
fixed sleep is unreliable. Poll the adapter until the named cookie is present.
"""
from __future__ import annotations

import time
from typing import Optional

from .adapters.base import Adapter
from .core import NormalizedCookie


class WaitTimeout(RuntimeError):
    pass


def wait_for_cookie(
    adapter: Adapter,
    name: str,
    domain: Optional[str] = None,
    timeout: float = 30.0,
    interval: float = 0.25,
) -> list[NormalizedCookie]:
    """Poll ``adapter.fetch`` until a cookie named ``name`` appears.

    Returns the full cookie set once found; raises WaitTimeout on timeout so
    callers (e.g. agents) can branch on a nonzero exit rather than exporting an
    empty jar.
    """
    deadline = time.monotonic() + timeout
    while True:
        cookies = adapter.fetch(domain=domain)
        if any(c.name == name for c in cookies):
            return cookies
        if time.monotonic() >= deadline:
            raise WaitTimeout(
                "Cookie %r not present within %.0fs%s"
                % (name, timeout, f" for domain {domain}" if domain else "")
            )
        time.sleep(interval)
