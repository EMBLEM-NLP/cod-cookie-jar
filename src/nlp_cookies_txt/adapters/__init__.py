"""Adapter registry."""
from __future__ import annotations

from .base import Adapter, filter_domain

__all__ = ["Adapter", "filter_domain", "get_adapter"]


def get_adapter(name: str, **kwargs) -> Adapter:
    """Instantiate an adapter by name. Imports are lazy so optional deps
    (websocket-client, playwright, selenium) are only required when used."""
    name = name.lower()
    if name == "cdp":
        from .cdp import CdpAdapter

        return CdpAdapter(**kwargs)
    if name == "playwright":
        from .playwright import PlaywrightAdapter

        return PlaywrightAdapter(**kwargs)
    if name == "selenium":
        from .selenium import SeleniumAdapter

        return SeleniumAdapter(**kwargs)
    raise ValueError("Unknown adapter %r (choose: cdp, playwright, selenium)" % name)
