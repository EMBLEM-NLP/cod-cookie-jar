"""Selenium 4 adapter.

IMPORTANT: ``driver.get_cookies()`` does not reliably return HttpOnly cookies,
so this adapter uses ``execute_cdp_cmd("Network.getAllCookies")`` instead, which
returns the full store including HttpOnly.
"""
from __future__ import annotations

from typing import Optional

from ..core import NormalizedCookie
from .base import Adapter, filter_domain


class SeleniumAdapter(Adapter):
    def __init__(self, driver):
        self.driver = driver

    def fetch(self, domain: Optional[str] = None) -> list[NormalizedCookie]:
        result = self.driver.execute_cdp_cmd("Network.getAllCookies", {})
        out = []
        for c in result.get("cookies", []):
            session = bool(c.get("session")) or c.get("expires", -1) in (-1, None)
            out.append(
                NormalizedCookie(
                    name=c["name"],
                    value=c["value"],
                    domain=c["domain"],
                    path=c.get("path", "/"),
                    secure=bool(c.get("secure")),
                    http_only=bool(c.get("httpOnly")),
                    expires=None if session else float(c["expires"]),
                    same_site=c.get("sameSite"),
                )
            )
        return filter_domain(out, domain)
