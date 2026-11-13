import type { Member, PresenceSnap } from "./api";

export type Presence = "online" | "away" | "meeting" | "busy" | "dnd" | "offline";

export const PRESENCE_LABEL: Record<Presence, string> = {
  online: "Disponible",
  away: "Absent",
  meeting: "En réunion",
  busy: "Occupé",
  dnd: "Ne pas déranger",
  offline: "Hors ligne",
};

export const PRESENCE_COLOR: Record<Presence, string> = {
  online: "bg-online",
  away: "bg-away",
  meeting: "bg-busy",
  busy: "bg-busy",
  dnd: "bg-busy",
  offline: "bg-offline",
};

/** Après la fermeture de HQ, on reste « Absent » quelques minutes avant « Hors ligne ». */
const AWAY_AFTER_LEAVE_MS = 5 * 60 * 1000;

let snaps: Record<string, PresenceSnap> = {};
export function setPresenceSnaps(next: Record<string, PresenceSnap>) { snaps = next; }

export function presenceOf(m: Member, _me?: Member | null): Presence {
  const s = snaps[m.id];
  let auto: Presence = "offline";
  if (s?.connected) auto = s.idle ? "away" : "online";
  else if (s?.last_seen && Date.now() - new Date(s.last_seen).getTime() < AWAY_AFTER_LEAVE_MS) auto = "away";
  if (m.manual_status === "dnd" && auto !== "offline") return "dnd";
  if (s?.in_meeting) return "meeting";
  if (m.manual_status && auto !== "offline") return m.manual_status;
  return auto;
}

export function lastSeenLabel(m: Member): string | null {
  const s = snaps[m.id];
  if (!s || s.connected || !s.last_seen) return null;
  const min = Math.round((Date.now() - new Date(s.last_seen).getTime()) / 60000);
  if (min < 1) return "vu à l'instant";
  if (min < 60) return `vu il y a ${min} min`;
  const h = Math.round(min / 60);
  if (h < 24) return `vu il y a ${h} h`;
  return `vu le ${new Date(s.last_seen).toLocaleDateString("fr-FR", { day: "numeric", month: "short" })}`;
}
