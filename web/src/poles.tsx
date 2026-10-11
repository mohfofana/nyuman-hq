import type { Member, Pole } from "./api";

// L'organisation de Nyuman : le CEO, et trois heads qui dirigent chacun un pôle et lui rendent compte.
export interface PoleDef {
  key: Exclude<Pole, "">;
  label: string;
  lead: string; // rôle de la personne qui dirige le pôle
  color: { bg: string; fg: string };
}

export const POLES: PoleDef[] = [
  { key: "direction", label: "Direction", lead: "CEO", color: { bg: "#f7e2cb", fg: "#9c4f0a" } },
  { key: "operations", label: "Opérations", lead: "COO", color: { bg: "#e1f0e7", fg: "#2f7a57" } },
  { key: "produit", label: "Produit", lead: "CTO", color: { bg: "#e5e8f7", fg: "#4150a8" } },
  { key: "croissance", label: "Croissance et marketing", lead: "CGO", color: { bg: "#f8e1da", fg: "#a33a22" } },
];

export function poleOf(key: Pole | undefined) {
  return POLES.find((p) => p.key === key);
}

/** Le head qui dirige un pôle (le premier head humain rangé dans ce pôle). */
export function leadOf(pole: Pole, members: Member[]): Member | undefined {
  return members.find((m) => m.active && m.kind === "humain" && m.role === "head" && m.pole === pole);
}

export function PoleChip({ pole }: { pole: Pole }) {
  const p = poleOf(pole);
  if (!p) return null;
  return <span className="chip" style={{ background: p.color.bg, color: p.color.fg }}>{p.label}</span>;
}
