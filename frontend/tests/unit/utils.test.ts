import { describe, it, expect } from "vitest";
import { formatCurrency, formatDate } from "../../src/lib/utils";

describe("formatCurrency", () => {
  it("formats cents to USD string", () => {
    expect(formatCurrency(1500)).toBe("$15.00");
    expect(formatCurrency(0)).toBe("$0.00");
    expect(formatCurrency(99)).toBe("$0.99");
  });
});

describe("formatDate", () => {
  it("formats date string", () => {
    const result = formatDate("2024-01-15T00:00:00Z");
    expect(result).toContain("Jan");
    expect(result).toContain("15");
    expect(result).toContain("2024");
  });
});
