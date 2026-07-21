#!/usr/bin/env node
/**
 * cod-cookie-jar CLI (Node port).
 * Export cookies.txt (Netscape) or JSON from a browser you control via CDP.
 */
import { writeFileSync, existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

import { CdpAdapter, toNetscape, toJson, waitForCookie } from './index.js';

function parseArgs(argv) {
  const args = {
    adapter: 'cdp',
    endpoint: 'http://localhost:9222',
    domain: null,
    waitFor: null,
    timeout: 30,
    json: false,
    force: false,
    out: '-',
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === '--adapter') args.adapter = next();
    else if (a === '--endpoint') args.endpoint = next();
    else if (a === '--domain') args.domain = next();
    else if (a === '--wait-for') args.waitFor = next();
    else if (a === '--timeout') args.timeout = Number(next());
    else if (a === '--json') args.json = true;
    else if (a === '--force') args.force = true;
    else if (a === '-o' || a === '--out') args.out = next();
  }
  return args;
}

function looksGitTracked(path) {
  let dir = dirname(resolve(path));
  for (;;) {
    if (existsSync(resolve(dir, '.git'))) return true;
    const parent = dirname(dir);
    if (parent === dir) return false;
    dir = parent;
  }
}

async function main() {
  const argv = process.argv.slice(2);
  if (argv[0] !== 'export') {
    console.error('usage: cod-cookie-jar export [--adapter cdp] [--endpoint URL] ...');
    process.exit(1);
  }
  const args = parseArgs(argv.slice(1));

  if (args.adapter !== 'cdp') {
    console.error(`The '${args.adapter}' adapter needs a live driver; use the library API.`);
    process.exit(1);
  }
  const adapter = new CdpAdapter(args.endpoint, args.timeout * 1000);

  let cookies;
  try {
    if (args.waitFor) {
      cookies = await waitForCookie(adapter, args.waitFor, {
        domain: args.domain,
        timeoutMs: args.timeout * 1000,
      });
    } else {
      cookies = await adapter.fetch(args.domain);
    }
  } catch (e) {
    console.error('error: ' + e.message);
    process.exit(2);
  }

  const text = args.json ? toJson(cookies) : toNetscape(cookies);

  if (args.out === '-') {
    process.stdout.write(text);
  } else {
    if (looksGitTracked(args.out) && !args.force) {
      console.error(
        'Refusing to write cookies into a git-tracked directory. Cookies are ' +
          'credential-equivalent. Use --force and make sure the file is git-ignored.',
      );
      process.exit(1);
    }
    writeFileSync(args.out, text, { mode: 0o600 });
    console.error(`wrote ${cookies.length} cookies -> ${args.out}`);
  }
}

main();
