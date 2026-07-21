"""Export cookies.txt via CDP from a browser you launched yourself.

Prereq: start a browser you control with remote debugging, then log in:
    google-chrome --remote-debugging-port=9222
"""
from cod_cookie_jar import CdpAdapter, to_netscape, wait_for_cookie

ENDPOINT = "http://localhost:9222"

adapter = CdpAdapter(ENDPOINT)

# Option A: export immediately
cookies = adapter.fetch(domain="example.com")

# Option B: wait until the auth cookie is actually set (recommended after login)
# cookies = wait_for_cookie(adapter, "SESSIONID", domain="example.com", timeout=30)

with open("cookies.txt", "w", encoding="utf-8") as f:
    f.write(to_netscape(cookies))

print(f"exported {len(cookies)} cookies -> cookies.txt")
