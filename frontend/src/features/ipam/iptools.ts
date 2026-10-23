// SPDX-License-Identifier: Apache-2.0
// Pure IP/CIDR helpers for the address grid (§23) and form validation.

export interface Network {
  version: 4 | 6;
  base: bigint;
  masklen: number;
  maxMasklen: number;
}

function parseIpv6(s: string): bigint | null {
  const halves = s.split("::");
  if (halves.length > 2) return null;
  const groupsOf = (part: string): string[] | null => {
    if (part === "") return [];
    const groups = part.split(":");
    const out: string[] = [];
    for (const g of groups) {
      if (g.includes(".")) {
        const v4 = parseIpv4(g);
        if (v4 === null) return null;
        out.push(((v4 >> 16n) & 0xffffn).toString(16), (v4 & 0xffffn).toString(16));
      } else {
        if (!/^[0-9a-fA-F]{1,4}$/.test(g)) return null;
        out.push(g);
      }
    }
    return out;
  };
  const head = groupsOf(halves[0]);
  const tail = halves.length === 2 ? groupsOf(halves[1]) : [];
  if (head === null || tail === null) return null;
  const missing = 8 - head.length - tail.length;
  if (halves.length === 1 ? head.length !== 8 : missing < 1) return null;
  const groups = [...head, ...Array<string>(Math.max(missing, 0)).fill("0"), ...tail];
  if (groups.length !== 8) return null;
  let value = 0n;
  for (const g of groups) value = (value << 16n) | BigInt(parseInt(g, 16));
  return value;
}

function parseIpv4(s: string): bigint | null {
  const parts = s.split(".");
  if (parts.length !== 4) return null;
  let value = 0n;
  for (const part of parts) {
    if (!/^\d{1,3}$/.test(part)) return null;
    const n = Number(part);
    if (n > 255) return null;
    value = (value << 8n) | BigInt(n);
  }
  return value;
}

export function parseIp(raw: string): { version: 4 | 6; value: bigint } | null {
  const s = raw.trim();
  if (s.includes(":")) {
    const value = parseIpv6(s);
    return value === null ? null : { version: 6, value };
  }
  const value = parseIpv4(s);
  return value === null ? null : { version: 4, value };
}

export function parseCidr(raw: string): Network | null {
  const slash = raw.lastIndexOf("/");
  if (slash < 0) return null;
  const ip = parseIp(raw.slice(0, slash));
  if (ip === null) return null;
  const maxMasklen = ip.version === 4 ? 32 : 128;
  const masklen = Number(raw.slice(slash + 1));
  if (!Number.isInteger(masklen) || masklen < 0 || masklen > maxMasklen) return null;
  const all = (1n << BigInt(maxMasklen)) - 1n;
  const mask = masklen === 0 ? 0n : (all << BigInt(maxMasklen - masklen)) & all;
  return { version: ip.version, base: ip.value & mask, masklen, maxMasklen };
}

export function isStrictCidr(raw: string): boolean {
  const slash = raw.lastIndexOf("/");
  if (slash < 0) return false;
  const net = parseCidr(raw);
  const ip = parseIp(raw.slice(0, slash));
  return net !== null && ip !== null && ip.value === net.base;
}

export function formatIp(version: 4 | 6, value: bigint): string {
  if (version === 4) {
    const octets = [24n, 16n, 8n, 0n].map((sh) => ((value >> sh) & 255n).toString());
    return octets.join(".");
  }
  const groups: string[] = [];
  for (let i = 7; i >= 0; i -= 1) groups.push(((value >> BigInt(i * 16)) & 0xffffn).toString(16));
  // RFC 5952: compress the longest run of zero groups (leftmost wins).
  let bestStart = -1;
  let bestLen = 0;
  let runStart = -1;
  groups.forEach((g, i) => {
    if (g === "0") {
      if (runStart < 0) runStart = i;
      if (i - runStart + 1 > bestLen) {
        bestLen = i - runStart + 1;
        bestStart = runStart;
      }
    } else {
      runStart = -1;
    }
  });
  if (bestLen >= 2) {
    const head = groups.slice(0, bestStart).join(":");
    const tail = groups.slice(bestStart + bestLen).join(":");
    return `${head}::${tail}`;
  }
  return groups.join(":");
}

/** Full address list of a CIDR, or null when it exceeds `limit` cells. */
export function enumerateNetwork(cidr: string, limit = 1024): string[] | null {
  const net = parseCidr(cidr);
  if (net === null) return null;
  const size = 1n << BigInt(net.maxMasklen - net.masklen);
  if (size > BigInt(limit)) return null;
  const out: string[] = [];
  for (let i = 0n; i < size; i += 1n) out.push(formatIp(net.version, net.base + i));
  return out;
}
