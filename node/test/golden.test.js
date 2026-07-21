/**
 * Runs the Node serializer against the SHARED golden fixtures.
 * The same files drive the Python suite (tests/test_golden_fixtures.py), so a
 * divergence between the two ports fails here or there.
 *
 * Run:  node --test
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

import { toNetscape, toJson, fromJson, fromWire, isPartitioned } from '../src/core.js';

const here = dirname(fileURLToPath(import.meta.url));
const fixtureDir = join(here, '..', '..', 'fixtures', 'golden');
const files = readdirSync(fixtureDir).filter((f) => f.endsWith('.json')).sort();

function load(name) {
  return JSON.parse(readFileSync(join(fixtureDir, name), 'utf-8'));
}

test('fixtures exist', () => {
  assert.ok(files.length > 0, `no fixtures in ${fixtureDir}`);
});

for (const file of files) {
  const c = load(file);
  const cookies = c.cookies.map(fromWire);

  test(`golden netscape: ${c.name}`, () => {
    assert.equal(toNetscape(cookies), c.expectedNetscape, c.description);
  });

  test(`wire roundtrip: ${c.name}`, () => {
    const again = fromJson(toJson(cookies));
    assert.equal(again.length, cookies.length);
    for (let i = 0; i < cookies.length; i++) {
      assert.deepEqual(again[i], cookies[i]);
    }
  });
}

test('CHIPS partitionKey survives JSON but not Netscape', () => {
  const c = load('chips_partitioned_flattened.json');
  const cookies = c.cookies.map(fromWire);
  assert.equal(cookies[0].partitionKey, 'https://top.example');
  assert.ok(isPartitioned(cookies[0]));
  assert.match(toJson(cookies), /partitionKey/);
  assert.doesNotMatch(toNetscape(cookies), /top\.example/);
});
