"""Runs the Python serializer against the SHARED golden fixtures.

The same fixture files are consumed by the Node suite (node/test/golden.test.js),
so a divergence between the two ports fails here or there.
"""
import json
import pathlib

import pytest

from nlp_cookies_txt.core import from_json, from_wire, to_json, to_netscape

FIXTURE_DIR = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "golden"
FIXTURES = sorted(FIXTURE_DIR.glob("*.json"))


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_fixtures_exist():
    assert FIXTURES, f"no fixtures found in {FIXTURE_DIR}"


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_golden_netscape(path):
    case = _load(path)
    cookies = [from_wire(d) for d in case["cookies"]]
    assert to_netscape(cookies) == case["expectedNetscape"], case["description"]


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_wire_roundtrip_preserves_everything(path):
    """JSON wire format must survive a round trip, including CHIPS partitionKey."""
    case = _load(path)
    cookies = [from_wire(d) for d in case["cookies"]]
    again = from_json(to_json(cookies))
    assert len(again) == len(cookies)
    for a, b in zip(cookies, again):
        assert a == b


def test_chips_partition_key_survives_json_but_not_netscape():
    case = _load(FIXTURE_DIR / "chips_partitioned_flattened.json")
    cookies = [from_wire(d) for d in case["cookies"]]
    assert cookies[0].partition_key == "https://top.example"
    # JSON preserves it...
    assert "partitionKey" in to_json(cookies)
    # ...Netscape cannot express it.
    assert "top.example" not in to_netscape(cookies)
