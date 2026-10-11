import { formatAgo, formatFcfa, formatNumber, statusDot } from "./format";

describe("format", () => {
  it("écrit les nombres à la française", () => {
    // Intl met une espace fine insécable entre les milliers.
    expect(formatNumber(486000).replace(/\s/g, " ")).toBe("486 000");
    expect(formatFcfa(23899.6).replace(/\s/g, " ")).toBe("23 900 FCFA");
  });

  it("dit depuis quand", () => {
    const now = new Date("2026-10-12T10:00:00Z");
    expect(formatAgo("2026-10-12T09:59:40Z", now)).toBe("à l’instant");
    expect(formatAgo("2026-10-12T09:58:00Z", now)).toBe("il y a 2 min");
    expect(formatAgo("2026-10-12T07:00:00Z", now)).toBe("il y a 3 h");
  });

  it("donne un point creux aux absents", () => {
    expect(statusDot("absent").hollow).toBe(true);
    expect(statusDot("bloque")).toEqual({ color: "#c4432b", hollow: false });
  });
});
