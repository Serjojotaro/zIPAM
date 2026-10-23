// SPDX-License-Identifier: Apache-2.0
import { describe, expect, it } from "vitest";
import { enumerateNetwork, formatIp, isStrictCidr, parseCidr, parseIp } from "./iptools";

describe("parseIp", () => {
  it("parses IPv4", () => {
    expect(parseIp("10.0.0.1")).toEqual({ version: 4, value: 167772161n });
    expect(parseIp("255.255.255.255")).toEqual({ version: 4, value: 4294967295n });
  });

  it("rejects invalid IPv4", () => {
    expect(parseIp("10.0.0.256")).toBeNull();
    expect(parseIp("10.0.0")).toBeNull();
    expect(parseIp("abc")).toBeNull();
  });

  it("parses compressed IPv6", () => {
    expect(parseIp("::1")).toEqual({ version: 6, value: 1n });
    expect(parseIp("fe80::1")?.value).toEqual((0xfe80n << 112n) + 1n);
  });

  it("parses IPv4-embedded IPv6", () => {
    expect(parseIp("::ffff:1.2.3.4")?.value).toEqual((0xffffn << 32n) | 0x01020304n);
  });

  it("rejects invalid IPv6", () => {
    expect(parseIp("fe80:::1")).toBeNull();
    expect(parseIp("1:2:3:4:5:6:7:8:9")).toBeNull();
  });
});

describe("parseCidr / isStrictCidr", () => {
  it("masks host bits", () => {
    expect(parseCidr("10.0.0.1/24")?.base).toEqual(167772160n);
  });

  it("rejects bad masklen", () => {
    expect(parseCidr("10.0.0.0/33")).toBeNull();
    expect(parseCidr("10.0.0.0")).toBeNull();
  });

  it("detects strict CIDRs", () => {
    expect(isStrictCidr("10.0.0.0/24")).toBe(true);
    expect(isStrictCidr("10.0.0.1/24")).toBe(false);
    expect(isStrictCidr("fe80::/64")).toBe(true);
    expect(isStrictCidr("fe80::1/64")).toBe(false);
  });
});

describe("formatIp", () => {
  it("compresses the longest zero run (RFC 5952)", () => {
    expect(formatIp(6, (0xfe80n << 112n) + 1n)).toBe("fe80::1");
    expect(formatIp(6, 0n)).toBe("::");
  });

  it("formats IPv4", () => {
    expect(formatIp(4, 167772161n)).toBe("10.0.0.1");
  });
});

describe("enumerateNetwork", () => {
  it("lists a small IPv4 network", () => {
    expect(enumerateNetwork("10.0.0.0/30")).toEqual([
      "10.0.0.0",
      "10.0.0.1",
      "10.0.0.2",
      "10.0.0.3",
    ]);
  });

  it("returns null above the limit", () => {
    expect(enumerateNetwork("10.0.0.0/21")).toBeNull();
    expect(enumerateNetwork("10.0.0.0/24")?.length).toBe(256);
  });

  it("lists a small IPv6 network", () => {
    expect(enumerateNetwork("fe80::/126")).toEqual(["fe80::", "fe80::1", "fe80::2", "fe80::3"]);
  });
});
