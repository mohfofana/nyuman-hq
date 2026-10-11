import type { Status } from "./api";

const nf = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 1 });

/** 486000 → « 486 000 » (espaces fines insécables, comme en français). */
export function formatNumber(value: number): string {
  return nf.format(value);
}

export function formatFcfa(value: number): string {
  return `${formatNumber(Math.round(value))} FCFA`;
}

/** « il y a 2 min », « il y a 3 h », sinon la date courte. */
export function formatAgo(iso: string, now: Date = new Date()): string {
  const then = new Date(iso);
  const minutes = Math.round((now.getTime() - then.getTime()) / 60000);
  if (minutes < 1) return "à l’instant";
  if (minutes < 60) return `il y a ${minutes} min`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `il y a ${hours} h`;
  return then.toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("fr-FR", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatToday(now: Date = new Date()): string {
  const s = now.toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/** « Mohamed Fofana » → « Mohamed » ; une adresse provisoire « mohamed.fofana@… » → « Mohamed ». */
export function firstName(name: string): string {
  const base = name.includes("@") ? name.split("@")[0].split(/[._-]/)[0] : name.split(/\s+/)[0];
  return base ? base.charAt(0).toUpperCase() + base.slice(1) : name;
}

export function greeting(now: Date = new Date()): string {
  const h = now.getHours();
  if (h < 5 || h >= 18) return "Bonsoir";
  if (h < 13) return "Bonjour";
  return "Bon après-midi";
}

/** Numéro de semaine ISO, comme au bureau (« semaine 41 »). */
export function isoWeek(now: Date = new Date()): number {
  const d = new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()));
  const day = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil(((d.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
}

/** « 2026-W42 », la clé de semaine des rapports (même calcul que le serveur). */
export function semaineIso(now: Date = new Date()): string {
  const d = new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()));
  const day = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - day);
  return `${d.getUTCFullYear()}-W${String(isoWeek(now)).padStart(2, "0")}`;
}

/** Couleurs d'avatar : fond clair + texte foncé, contraste vérifié. */
export const AVATAR_COLORS: Record<string, { bg: string; fg: string }> = {
  orange: { bg: "#fbefe3", fg: "#a3530b" },
  bleu: { bg: "#e7eef8", fg: "#2f5f9e" },
  vert: { bg: "#e6f2ec", fg: "#2f6b4f" },
  rouge: { bg: "#fbeae6", fg: "#a8361f" },
  ambre: { bg: "#fbf3dc", fg: "#8a6400" },
  gris: { bg: "#efebe7", fg: "#4f4840" },
};

export function avatarColors(color: string) {
  return AVATAR_COLORS[color] ?? AVATAR_COLORS.gris;
}

/** Couleur du point de statut ; le texte du statut est toujours affiché à côté. */
export function statusDot(status: Status): { color: string; hollow: boolean } {
  switch (status) {
    case "en_ligne":
    case "travaille":
      return { color: "#3e8061", hollow: false };
    case "en_attente":
      return { color: "#c99a1e", hollow: false };
    case "bloque":
      return { color: "#c4432b", hollow: false };
    default:
      return { color: "#9a9086", hollow: true };
  }
}
