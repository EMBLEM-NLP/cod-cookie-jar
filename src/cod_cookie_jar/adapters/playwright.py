"""Playwright adapter.

Two inputs:
  * a live BrowserContext (``context.cookies()``), or
  * a saved ``storage_state`` JSON file/dict.

Playwright returns HttpOnly cookies on all browsers (including Firefox), so no
CDP is required here.
"""
from __future__ import annotations

import json
from typing import Optional

from ..core import NormalizedCookie
from .base import Adapter, filter_domain


def _normalize(items: list[dict]) -> list[NormalizedCookie]:
    out = []
    for c in items:
        expires = c.get("expires", -1)
        session = expires in (-1, None)
        out.append(
            NormalizedCookie(
                name=c["name"],
                value=c["value"],
                domain=c["domain"],
                path=c.get("path", "/"),
                secure=bool(c.get("secure")),
                http_only=bool(c.get("httpOnly")),
                expires=None if session else float(expires),
                same_site=c.get("sameSite"),
            )
        )
    return out


class PlaywrightAdapter(Adapter):
    def __init__(self, context=None, storage_state=None):
        if context is None and storage_state is None:
            raise ValueError("Provide either a live context or a storage_state.")
        self.context = context
        self.storage_state = storage_state

    def _from_storage_state(self) -> list[dict]:
        state = self.storage_state
        if isinstance(state, str):
            with open(state, "r", encoding="utf-8") as f:
                state = json.load(f)
        return state.get("cookies", [])

    def fetch(self, domain: Optional[str] = None) -> list[NormalizedCookie]:
        if self.context is not None:
            items = self.context.cookies()
        else:
            items = self._from_storage_state()
        return filter_domain(_normalize(items), domain)
