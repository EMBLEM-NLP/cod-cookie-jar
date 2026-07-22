"""CLI multi-domain filtering.

Regression guard: `--domain` was doubly broken — only the first domain was
fetched, and the follow-up filter was neutralized by a stray `or True`, so
`--domain a --domain b` silently returned only `a`'s cookies. A multi-domain
export must return the *union* of the requested domains, using the same
parent/subdomain matching as a single-domain fetch.
"""
import json

from cod_cookie_jar.cli import main

# Three unrelated domains plus one subdomain to exercise parent/child matching.
COOKIES = [
    {"name": "a", "value": "1", "domain": "alpha.com", "path": "/", "expires": 1893456000},
    {"name": "b", "value": "2", "domain": "beta.com", "path": "/", "expires": 1893456000},
    {"name": "g", "value": "3", "domain": "gamma.com", "path": "/", "expires": 1893456000},
    {"name": "s", "value": "4", "domain": ".app.alpha.com", "path": "/", "expires": 1893456000},
]


def _state(tmp_path):
    p = tmp_path / "state.json"
    p.write_text(json.dumps({"cookies": COOKIES}), encoding="utf-8")
    return str(p)


def _names(tmp_path, capsys, *domains):
    args = ["export", "--adapter", "playwright", "--storage-state", _state(tmp_path)]
    for d in domains:
        args += ["--domain", d]
    args += ["-o", "-"]
    rc = main(args)
    assert rc == 0
    out = capsys.readouterr().out
    # Data rows are tab-separated; header/comment lines contain no tabs.
    return {line.split("\t")[5] for line in out.splitlines() if "\t" in line}


def test_multi_domain_returns_union(tmp_path, capsys):
    # alpha + beta -> both (and alpha's .app.alpha.com child), gamma excluded.
    # This is the union case the old `or True` code broke.
    assert _names(tmp_path, capsys, "alpha.com", "beta.com") == {"a", "b", "s"}


def test_multi_domain_excludes_unrequested(tmp_path, capsys):
    assert "g" not in _names(tmp_path, capsys, "alpha.com", "beta.com")


def test_multi_domain_matches_subdomains_like_single(tmp_path, capsys):
    # A parent-domain request must also pull the .app.alpha.com child, matching
    # filter_domain's single-domain semantics.
    assert _names(tmp_path, capsys, "alpha.com") == {"a", "s"}


def test_single_domain_still_narrows(tmp_path, capsys):
    assert _names(tmp_path, capsys, "beta.com") == {"b"}


def test_no_domain_returns_all(tmp_path, capsys):
    assert _names(tmp_path, capsys) == {"a", "b", "g", "s"}
