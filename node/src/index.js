/** cod-cookie-jar (Node port): export cookies.txt from a browser you control. */
export {
  toNetscape,
  fromNetscape,
  toJson,
  fromJson,
  fromWire,
  filterDomain,
  isPartitioned,
  WIRE_VERSION,
} from './core.js';
export { CdpAdapter } from './adapters/cdp.js';

export const VERSION = '0.1.0';

/**
 * Poll an adapter until a cookie of the given name exists, then return the set.
 * Throws on timeout so callers can branch on it.
 */
export async function waitForCookie(
  adapter,
  name,
  { domain = null, timeoutMs = 30000, intervalMs = 250 } = {},
) {
  const deadline = Date.now() + timeoutMs;
  for (;;) {
    const cookies = await adapter.fetch(domain);
    if (cookies.some((c) => c.name === name)) return cookies;
    if (Date.now() >= deadline) {
      throw new Error(
        `Cookie '${name}' not present within ${Math.round(timeoutMs / 1000)}s` +
          (domain ? ` for domain ${domain}` : ''),
      );
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
}
