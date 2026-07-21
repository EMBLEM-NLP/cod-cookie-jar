/**
 * CDP adapter for the Node port.
 *
 * Talks to a browser YOU launched with --remote-debugging-port=9222, using
 * Storage.getCookies over the browser websocket. No dependencies: Node 18+ has
 * a global WebSocket and global fetch.
 *
 * Reads only from a debugging endpoint the operator explicitly enabled on their
 * own browser. No on-disk access, no encryption bypass.
 */
import { filterDomain } from './core.js';

async function browserWsUrl(endpoint, timeoutMs) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(endpoint.replace(/\/$/, '') + '/json/version', {
      signal: ctrl.signal,
    });
    const info = await res.json();
    if (!info.webSocketDebuggerUrl) {
      throw new Error(
        `No webSocketDebuggerUrl at ${endpoint}/json/version -- is the browser ` +
          'running with --remote-debugging-port?',
      );
    }
    return info.webSocketDebuggerUrl;
  } finally {
    clearTimeout(t);
  }
}

function rawCookies(wsUrl, timeoutMs) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    const timer = setTimeout(() => {
      ws.close();
      reject(new Error('CDP timeout'));
    }, timeoutMs);

    ws.addEventListener('open', () => {
      ws.send(JSON.stringify({ id: 1, method: 'Storage.getCookies' }));
    });
    ws.addEventListener('message', (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id === 1) {
        clearTimeout(timer);
        ws.close();
        if (msg.error) reject(new Error('CDP error: ' + JSON.stringify(msg.error)));
        else resolve(msg.result.cookies);
      }
    });
    ws.addEventListener('error', (e) => {
      clearTimeout(timer);
      reject(new Error('WebSocket error: ' + (e.message || 'connection failed')));
    });
  });
}

export class CdpAdapter {
  constructor(endpoint = 'http://localhost:9222', timeoutMs = 10000) {
    this.endpoint = endpoint;
    this.timeoutMs = timeoutMs;
  }

  async fetch(domain = null) {
    const wsUrl = await browserWsUrl(this.endpoint, this.timeoutMs);
    const raw = await rawCookies(wsUrl, this.timeoutMs);
    const cookies = raw.map((c) => {
      const session = Boolean(c.session) || c.expires === undefined || c.expires < 0;
      let partitionKey = null;
      if (c.partitionKey) {
        partitionKey =
          typeof c.partitionKey === 'object'
            ? c.partitionKey.topLevelSite
            : c.partitionKey;
      }
      return {
        name: c.name,
        value: c.value,
        domain: c.domain,
        path: c.path || '/',
        secure: Boolean(c.secure),
        httpOnly: Boolean(c.httpOnly),
        expires: session ? null : Number(c.expires),
        hostOnly: null,
        sameSite: c.sameSite ?? null,
        partitionKey,
      };
    });
    return filterDomain(cookies, domain);
  }
}
