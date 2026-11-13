import type { Member } from "./api";

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

/** La présence automatique (temps réel) arrive à l'étape 3 ; d'ici là, on se base sur le statut manuel. */
export function presenceOf(m: Member, me?: Member | null): Presence {
  if (m.manual_status) return m.manual_status;
  if (me && m.id === me.id) return "online";
  return "offline";
}
