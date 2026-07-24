---
description: Export a spec-correct cookies.txt from a browser you control (curl/yt-dlp/wget ready).
argument-hint: "[--adapter cdp|playwright] [--endpoint URL | --storage-state FILE] [--domain d] [--wait-for NAME] [-o out]"
---

Export a Netscape `cookies.txt` from a browser **the user controls**, using the
bundled `nlp-cookies-txt` tool. Follow the `nlp-cookies-txt` skill for adapter
choice, safety rules (credential-equivalent output, `0600`, refuses git-tracked
paths without `--force`), and post-export verification.

Arguments provided by the user: `$ARGUMENTS`

Do this:

1. Treat the output as a live credential. Only proceed for a session the user
   logged into in a browser they launched — never on-disk stores or someone
   else's profile/account.
2. Run the bundled CLI, passing the user's arguments through. Default the adapter
   to `cdp` and the endpoint to `http://localhost:9222` unless overridden:

   ```bash
   PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python3 -m nlp_cookies_txt.cli export $ARGUMENTS
   ```

   If `$ARGUMENTS` is empty, ask which stack their browser is in (CDP endpoint,
   or a Playwright `--storage-state` JSON file) and where to write the file, then
   run with sensible defaults (`--adapter cdp --endpoint http://localhost:9222
   -o cookies.txt`).
3. If the run reports a missing `websocket-client` (CDP only), tell the user to
   `pip install websocket-client`.
4. After a successful export, confirm the login cookie is present (the HttpOnly
   line begins `#HttpOnly_`) and report the output path. Remind the user to
   delete the file when finished.
