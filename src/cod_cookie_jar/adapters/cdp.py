"""Primary adapter: raw Chrome DevTools Protocol.

Talks to a browser you launched yourself with, e.g.:
    chrome --remote-debugging-port=9222

Uses ``Storage.getCookies`` (the non-deprecated successor to
``Network.getAllCookies``), which returns the full cookie store including
HttpOnly cookies, with no on-disk decryption and no extension loading.

This adapter only reads from a debugging endpoint the operator explicitly
enabled on their own browser. It performs no on-disk access and no bypass of
any browser encryption.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Optional

from ..core import NormalizedCookie
from .base import Adapter, filter_domain


class CdpAdapter(Adapter):
    def __init__(self, endpoint: str = "http://localhost:9222", timeout: float = 10.0):
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout

    def _browser_ws_url(self) -> str:
        with urllib.request.urlopen(
            self.endpoint + "/json/version", timeout=self.timeout
        ) as r:
            info = json.loads(r.read().decode("utf-8"))
        url = info.get("webSocketDebuggerUrl")
        if not url:
            raise RuntimeError(
                "No webSocketDebuggerUrl at %s/json/version -- is the browser "
                "running with --remote-debugging-port?" % self.endpoint
            )
        return url

    def _raw_cookies(self) -> list[dict]:
        try:
            import websocket  # from the 'websocket-client' package
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "The CDP adapter needs 'websocket-client'. "
                "Install with:  pip install cod-cookie-jar[cdp]"
            ) from e

        ws = websocket.create_connection(
            self._browser_ws_url(), timeout=self.timeout
        )
        try:
            ws.send(json.dumps({"id": 1, "method": "Storage.getCookies"}))
            while True:
                msg = json.loads(ws.recv())
                if msg.get("id") == 1:
                    if "error" in msg:
                        raise RuntimeError("CDP error: %s" % msg["error"])
                    return msg["result"]["cookies"]
        finally:
            ws.close()

    def fetch(self, domain: Optional[str] = None) -> list[NormalizedCookie]:
        cookies = []
        for c in self._raw_cookies():
            session = bool(c.get("session")) or c.get("expires", -1) in (-1, None)
            cookies.append(
                NormalizedCookie(
                    name=c["name"],
                    value=c["value"],
                    domain=c["domain"],
                    path=c.get("path", "/"),
                    secure=bool(c.get("secure")),
                    http_only=bool(c.get("httpOnly")),
                    expires=None if session else float(c["expires"]),
                    same_site=c.get("sameSite"),
                    partition_key=(
                        c.get("partitionKey", {}).get("topLevelSite")
                        if isinstance(c.get("partitionKey"), dict)
                        else c.get("partitionKey")
                    ),
                )
            )
        return filter_domain(cookies, domain)
