"""Launch a browser you control with Playwright, then export its session as cookies.txt.

This is the end-to-end flow for feeding an authenticated YouTube session to
``yt-dlp`` (e.g. to get past "Sign in to confirm you're not a bot", or to reach
members-only / age-gated content). It drives a browser **you** operate and a
session **you** authenticated — cod-cookie-jar never decrypts an on-disk store.

    pip install -e ".[all]"          # pulls in playwright
    python -m playwright install chromium
    python examples/export_youtube_playwright.py

For gated content you must actually sign in: set ``LOGIN=1`` and a real login
cookie name in ``WAIT_FOR`` below, and log in in the launched window before the
wait times out. An anonymous visitor session (the default here) is enough to
*locate* a video and pull its public storyboard track, but YouTube's PO-token
gate will still refuse a full-resolution download from a datacenter IP unless
the session is signed in.
"""
from __future__ import annotations

import os

from playwright.sync_api import sync_playwright

from cod_cookie_jar import PlaywrightAdapter, to_netscape, wait_for_cookie

URL = os.environ.get("URL", "https://www.youtube.com/")
OUT = os.environ.get("OUT", "cookies.txt")
DOMAIN = os.environ.get("DOMAIN", "youtube.com")
HEADLESS = os.environ.get("HEADLESS", "1") != "0"
WAIT_FOR = os.environ.get("WAIT_FOR")  # e.g. "SID" once you've logged in
# Optional proxy for locked-down / datacenter environments (see README).
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")

launch_args = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    # Some egress proxies reset TLS 1.3 / ECH from headless Chromium; these keep
    # the handshake compatible without ever disabling verification.
    "--disable-quic",
    "--ssl-version-max=tls1.2",
    "--disable-features=EncryptedClientHello",
]

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=HEADLESS,
        args=launch_args,
        proxy={"server": PROXY} if PROXY else None,
    )
    context = browser.new_context(
        locale="en-US",
        # Trust a corporate/agent MITM CA if the environment injects one; harmless otherwise.
        ignore_https_errors=bool(PROXY),
    )
    page = context.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=60_000)

    # Dismiss the EU consent interstitial if present (sets visitor cookies).
    for sel in (
        'button[aria-label*="Accept all"]',
        'button[aria-label*="Accept"]',
        'form[action*="consent"] button',
    ):
        try:
            el = page.query_selector(sel)
            if el:
                el.click(timeout=2_000)
                page.wait_for_timeout(1_200)
                break
        except Exception:
            pass

    if WAIT_FOR:
        print(f"Log in now — waiting up to 120s for the '{WAIT_FOR}' cookie…")
        # Reads through the live context, so HttpOnly login cookies are included.
        cookies = wait_for_cookie(
            PlaywrightAdapter(context=context), WAIT_FOR, domain=DOMAIN, timeout=120
        )
    else:
        page.wait_for_timeout(3_000)  # let visitor cookies settle
        cookies = PlaywrightAdapter(context=context).fetch(domain=DOMAIN)

    browser.close()

with open(OUT, "w", encoding="utf-8") as f:
    f.write(to_netscape(cookies))

print(f"exported {len(cookies)} cookies -> {OUT}")
print("names:", ", ".join(sorted(c.name for c in cookies)))
print("\nNext:  yt-dlp --cookies", OUT, "--js-runtimes deno --remote-components ejs:npm <URL>")
