"""cod-cookie-jar: export cookies.txt (Netscape format) from a browser you control."""
from __future__ import annotations

from .adapters import get_adapter
from .adapters.cdp import CdpAdapter
from .adapters.playwright import PlaywrightAdapter
from .adapters.selenium import SeleniumAdapter
from .core import NormalizedCookie, from_netscape, to_netscape
from .wait import WaitTimeout, wait_for_cookie

__version__ = "0.1.0"

__all__ = [
    "NormalizedCookie",
    "to_netscape",
    "from_netscape",
    "get_adapter",
    "CdpAdapter",
    "PlaywrightAdapter",
    "SeleniumAdapter",
    "wait_for_cookie",
    "WaitTimeout",
    "__version__",
]
