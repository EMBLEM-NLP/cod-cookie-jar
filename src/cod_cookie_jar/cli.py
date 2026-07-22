"""Command-line interface for cod-cookie-jar."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from .adapters import get_adapter
from .adapters.base import filter_domain
from .core import to_netscape
from .sinks import write_file, write_stdout
from .wait import WaitTimeout, wait_for_cookie


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cod-cookie-jar",
        description="Export cookies.txt (Netscape format) from a browser you control.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    exp = sub.add_parser("export", help="Export cookies from an automation stack.")
    exp.add_argument(
        "--adapter", default="cdp", choices=["cdp", "playwright", "selenium"]
    )
    exp.add_argument(
        "--endpoint",
        default="http://localhost:9222",
        help="CDP adapter: remote debugging endpoint of YOUR running browser.",
    )
    exp.add_argument(
        "--storage-state", help="Playwright adapter: path to a storage_state JSON."
    )
    exp.add_argument(
        "--domain", action="append", help="Filter to a domain (repeatable)."
    )
    exp.add_argument("--wait-for", help="Poll until a cookie of this name exists.")
    exp.add_argument("--timeout", type=float, default=30.0)
    exp.add_argument(
        "--json",
        action="store_true",
        help="Emit normalized JSON (preserves partitionKey) instead of Netscape.",
    )
    exp.add_argument("--force", action="store_true", help="Allow writing into a git dir.")
    exp.add_argument(
        "-o", "--out", default="-", help="Output path, or '-' for stdout (default)."
    )
    return p


def _make_adapter(args):
    if args.adapter == "cdp":
        return get_adapter("cdp", endpoint=args.endpoint)
    if args.adapter == "playwright":
        if not args.storage_state:
            raise SystemExit(
                "playwright adapter via CLI needs --storage-state "
                "(use the library API to pass a live context)."
            )
        return get_adapter("playwright", storage_state=args.storage_state)
    raise SystemExit(
        "The %r adapter needs a live driver object; use the library API." % args.adapter
    )


def cmd_export(args) -> int:
    adapter = _make_adapter(args)
    # With a single --domain we can let the adapter narrow the fetch. With several,
    # we must fetch everything and filter to the union ourselves, since the adapter
    # fetch takes only one domain.
    multi_domain = bool(args.domain) and len(args.domain) > 1
    fetch_domain = None if multi_domain else (args.domain[0] if args.domain else None)

    try:
        if args.wait_for:
            cookies = wait_for_cookie(
                adapter, args.wait_for, domain=fetch_domain, timeout=args.timeout
            )
        else:
            cookies = adapter.fetch(domain=fetch_domain)
    except WaitTimeout as e:
        print("timeout: %s" % e, file=sys.stderr)
        return 2

    if multi_domain:
        # Union of per-domain matches, reusing the adapters' matching rules so a
        # multi-domain filter behaves exactly like several single-domain fetches.
        seen: set[int] = set()
        union: list = []
        for d in args.domain:
            for c in filter_domain(cookies, d):
                if id(c) not in seen:
                    seen.add(id(c))
                    union.append(c)
        cookies = union

    if args.json:
        text = json.dumps([asdict(c) for c in cookies], indent=2) + "\n"
    else:
        text = to_netscape(cookies)

    if args.out == "-":
        write_stdout(text)
    else:
        write_file(text, args.out, force=args.force)
        print(
            "wrote %d cookies -> %s" % (len(cookies), args.out), file=sys.stderr
        )
    return 0


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "export":
        return cmd_export(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
