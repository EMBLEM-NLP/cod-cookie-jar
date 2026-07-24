---
name: nlp-cookies-txt
description: >-
  Export a spec-correct Netscape cookies.txt from a browser the user controls,
  and hand it to curl, yt-dlp, wget, or Python's http.cookiejar.MozillaCookieJar.
  Use this WHENEVER the user needs cookies from their own logged-in browser
  session — even if they never say "cookies.txt": e.g. "yt-dlp says sign in to
  confirm you're not a bot", "curl/wget needs my auth cookie", "download this
  members-only / age-gated / paywalled video I'm logged into", "export my
  session so a script can act as me", "my scraper keeps getting logged out",
  or "the cookies I exported are missing the login cookie" (the classic
  HttpOnly drop). Also use when a previously exported cookies.txt fails because
  the HttpOnly auth cookie was silently dropped or the #HttpOnly_ prefix is
  missing. This tool talks to a browser the USER launched and a session the USER
  logged into, via sanctioned debugging/automation APIs. Do NOT use it to read,
  decrypt, or extract cookies from an on-disk cookie store, another person's
  browser or profile, or any account the user did not authenticate themselves —
  it deliberately cannot do that, and requests of that shape are out of scope.
---

# nlp-cookies-txt

Produce a **byte-correct Netscape `cookies.txt`** from a browser the user
operates, so downstream tools (`curl`, `yt-dlp`, `wget`, `MozillaCookieJar`)
accept the user's authenticated session. The whole point is *correctness the
common tools get wrong* — especially keeping **HttpOnly** cookies with the
required `#HttpOnly_` domain prefix that strict parsers need. Never
reimplement the serialization; drive this tool.

## Safety and scope — read first

A `cookies.txt` is **credential-equivalent**: treat it like a password. Anyone
holding it can act as the user's session until it expires.

- This works **only** on a browser the user launched and a session the user
  logged into themselves. It reads cookies through debugging/automation APIs the
  user turns on (CDP remote-debugging, Playwright/Selenium drivers) — no on-disk
  decryption, no App-Bound-Encryption bypass, no stealth or anti-bot evasion.
- If the request is to pull cookies from an existing browser profile on disk, a
  browser the user isn't driving, or someone else's account, this tool cannot do
  it and you should not try to work around that — say so plainly.
- The tool writes output `0600` and **refuses a git-tracked path** unless
  `--force` is passed. Do not talk the user into committing a `cookies.txt`; if
  they insist on a tracked path, make sure `.gitignore` covers it (the repo
  already ignores `cookies.txt` / `*.cookies.txt`).

## Running the bundled tool

The plugin ships the Python package, so no install is needed. Invoke the CLI
with the package on `PYTHONPATH`, using the plugin root:

```bash
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python3 -m nlp_cookies_txt.cli export [options]
```

`${CLAUDE_PLUGIN_ROOT}` is set by Claude Code to this plugin's directory. If it
is somehow unset (e.g. running from a clone), substitute the repo root so the
path resolves to `.../nlp-cookies-txt/src`.

Only `websocket-client` is required, and only for the CDP adapter. If a CDP run
fails with a missing-module error, tell the user to `pip install websocket-client`
(or run `pip install -e "${CLAUDE_PLUGIN_ROOT}[cdp]"`).

## Choosing an adapter

Ask which automation stack the user already has a browser open in; default to
CDP because it is stack-agnostic.

| `--adapter` | When to use | How it reads cookies |
|---|---|---|
| `cdp` (default) | Any browser the user launched with `--remote-debugging-port`. Most portable. | `Storage.getCookies` over the browser websocket. |
| `playwright` | A live Playwright context, **or** a saved `storage_state.json`. Works on Firefox too. | `context.cookies()` / `storage_state`. |
| `selenium` | An existing Selenium 4 session. | `Network.getAllCookies` via `execute_cdp_cmd` (avoids `get_cookies()`'s HttpOnly gap). |

Note: `playwright` (live context) and `selenium` need a live driver **object**,
so they run through the library API, not the CLI. From the CLI, the practical
paths are **cdp** (point at a running browser) and **playwright with
`--storage-state`** (a JSON file Playwright saved).

## Common invocations

Start the browser as the user (they do this, not you), log in, then export.

```bash
# 1. user starts their own browser with remote debugging
google-chrome --remote-debugging-port=9222

# 2. export everything to a file (written 0600)
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python3 -m nlp_cookies_txt.cli export \
    --adapter cdp --endpoint http://localhost:9222 -o cookies.txt

# scope to one domain and wait until the auth cookie actually exists first
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python3 -m nlp_cookies_txt.cli export \
    --adapter cdp --endpoint http://localhost:9222 \
    --domain example.com --wait-for SESSIONID --timeout 30 -o cookies.txt

# pipe straight into yt-dlp without ever touching disk
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python3 -m nlp_cookies_txt.cli export \
    --adapter cdp -o - | yt-dlp --cookies /dev/stdin "URL"

# from a saved Playwright storage_state instead of a live browser
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python3 -m nlp_cookies_txt.cli export \
    --adapter playwright --storage-state ./storage_state.json -o cookies.txt
```

Useful flags: `--domain` (repeatable filter), `--wait-for NAME` +
`--timeout SECONDS` (poll until the login cookie appears — great right after a
user logs in), `-o -` (stdout), `--json` (normalized JSON that also preserves
`sameSite`/`partitionKey`, which Netscape can't express), `--force` (allow a
git-tracked output path).

## After exporting

- Confirm the login cookie is present. A quick sanity check the user can trust:
  ```bash
  python3 -c "from http.cookiejar import MozillaCookieJar as J; j=J('cookies.txt'); j.load(ignore_discard=True, ignore_expires=True); print(sorted(c.name for c in j))"
  ```
  The HttpOnly session cookie (line starts `#HttpOnly_`) should show up.
- Remind the user the file is a live credential; delete it when done.

## Library API (when a live Playwright/Selenium object is in play)

```python
from nlp_cookies_txt import CdpAdapter, PlaywrightAdapter, to_netscape, wait_for_cookie

cookies = CdpAdapter("http://localhost:9222").fetch(domain="example.com")
open("cookies.txt", "w").write(to_netscape(cookies))

# live Playwright context you already have
cookies = PlaywrightAdapter(context=context).fetch()
open("cookies.txt", "w").write(to_netscape(cookies))

# wait for login to settle, then export
cookies = wait_for_cookie(CdpAdapter("http://localhost:9222"), "SESSIONID",
                          domain="example.com", timeout=30)
```

Public API lives in `${CLAUDE_PLUGIN_ROOT}/src/nlp_cookies_txt/`; the serializer
and format rules are in `core.py`, the adapters in `adapters/`. Read those only
if the user asks about internals — for normal exports, the CLI above is enough.
