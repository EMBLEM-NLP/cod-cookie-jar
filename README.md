# cod-cookie-jar

Export a spec-correct **`cookies.txt`** (Netscape format) from **a browser you control**, from whatever automation stack you already use.

Given a browser you drive and a session **you** logged into, it produces a `cookies.txt` consumable by `curl`, `yt-dlp`, `wget`, and Python's `http.cookiejar.MozillaCookieJar` — via each browser's own sanctioned APIs. No on-disk decryption, no stealth.

## Why it exists
- `Selenium.get_cookies()` and `document.cookie` drop **HttpOnly** cookies; this doesn't.
- The popular "Get cookies.txt LOCALLY" extension omits the `#HttpOnly_` prefix, so strict parsers silently drop HttpOnly auth cookies; this emits it correctly.
- One correct serializer, thin adapters, byte-identical output across stacks.

## Scope

**This tool assumes a browser you operate and a session you authenticated.** It reads cookies through debugging/automation APIs you enable yourself.

**Non-goals (deliberately out of scope):**
- No on-disk cookie-store decryption / App-Bound-Encryption bypass.
- No anti-bot / stealth / detection-evasion.
- No extracting cookies from profiles, browsers, or accounts you don't operate.

Cookie files are **credential-equivalent** — treat `cookies.txt` like a password. File output is written `0600` and refuses a git-tracked path without `--force`.

## Install
```bash
pip install -e ".[cdp]"      # CDP adapter (recommended, stack-agnostic)
pip install -e ".[all]"      # + playwright + selenium adapters
pip install -e ".[dev]"      # + pytest
```

## Quickstart (CDP — recommended)
Launch a browser **you control** with remote debugging, log in, then:
```bash
# 1. start Chrome yourself
google-chrome --remote-debugging-port=9222

# 2. export after you've logged in
cod-cookie-jar export --adapter cdp --endpoint http://localhost:9222 -o cookies.txt

# only one domain, and wait until the auth cookie exists first
cod-cookie-jar export --adapter cdp --endpoint http://localhost:9222 \
    --domain example.com --wait-for SESSIONID --timeout 30 -o cookies.txt

# pipe straight into yt-dlp
cod-cookie-jar export --adapter cdp -o - | yt-dlp --cookies /dev/stdin URL
```

## Library API
```python
from cod_cookie_jar import CdpAdapter, PlaywrightAdapter, to_netscape, wait_for_cookie

# CDP
cookies = CdpAdapter("http://localhost:9222").fetch(domain="example.com")
open("cookies.txt", "w").write(to_netscape(cookies))

# Playwright live context
cookies = PlaywrightAdapter(context=context).fetch()
open("cookies.txt", "w").write(to_netscape(cookies))

# Wait for login to settle, then export
adapter = CdpAdapter("http://localhost:9222")
cookies = wait_for_cookie(adapter, "SESSIONID", domain="example.com", timeout=30)
```

## Adapters
| Adapter | Source | HttpOnly | Notes |
|---|---|---|---|
| `cdp` | `Storage.getCookies` over the browser websocket | yes | Primary; any browser you launch with `--remote-debugging-port`. |
| `playwright` | `context.cookies()` / `storage_state` | yes | Works on Firefox too; accepts a saved storage_state. |
| `selenium` | Selenium 4 `execute_cdp_cmd("Network.getAllCookies")` | yes | Avoids `get_cookies()`'s HttpOnly gap. |

## Output format
Seven tab-separated fields per line: `domain`, `includeSubdomains`, `path`, `secure`, `expiry`, `name`, `value`. HttpOnly cookies carry a `#HttpOnly_` prefix on the domain field; session cookies use expiry `0`.

## Testing
```bash
pytest                       # golden-file serializer suite is the core guarantee
```
