"""Adapter contract: fetch and normalize; never format."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..core import NormalizedCookie


class Adapter(ABC):
    """An adapter fetches cookies from one automation stack and normalizes them.

    Adapters MUST NOT do any Netscape formatting -- that is the core's job, so
    that every stack yields byte-identical output.
    """

    @abstractmethod
    def fetch(self, domain: Optional[str] = None) -> list[NormalizedCookie]:
        """Return the current cookie set, optionally filtered to ``domain``."""
        raise NotImplementedError


def filter_domain(
    cookies: list[NormalizedCookie], domain: Optional[str]
) -> list[NormalizedCookie]:
    """Keep cookies whose domain matches ``domain`` or a parent of it.

    A cookie for ``.example.com`` matches ``example.com`` and ``app.example.com``.
    """
    if not domain:
        return cookies
    needle = domain.lstrip(".").lower()
    kept = []
    for c in cookies:
        d = c.domain.lstrip(".").lower()
        if needle == d or needle.endswith("." + d) or d.endswith("." + needle):
            kept.append(c)
    return kept
