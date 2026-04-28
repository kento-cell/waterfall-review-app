import { describe, it, expect } from "vitest";
import { cn, formatBytes, formatDateTime } from "@/lib/utils";

describe("cn", () => {
  it("merges class names", () => {
    expect(cn("a", "b")).toBe("a b");
  });

  it("dedupes tailwind classes", () => {
    expect(cn("p-2", "p-4")).toBe("p-4");
  });
});

describe("formatBytes", () => {
  it("formats bytes", () => {
    expect(formatBytes(512)).toBe("512 B");
  });
  it("formats kilobytes", () => {
    expect(formatBytes(2048)).toBe("2.0 KB");
  });
  it("formats megabytes", () => {
    expect(formatBytes(5 * 1024 * 1024)).toBe("5.00 MB");
  });
});

describe("formatDateTime", () => {
  it("returns - for null", () => {
    expect(formatDateTime(null)).toBe("-");
  });
  it("returns - for undefined", () => {
    expect(formatDateTime(undefined)).toBe("-");
  });
  it("formats valid ISO string (smoke test)", () => {
    const result = formatDateTime("2026-04-28T01:23:45Z");
    expect(result).not.toBe("-");
    expect(typeof result).toBe("string");
  });
});
