import type { Member, Piece, Presence, Status } from "./api";

export interface PieceDef {
  key: Piece;
  label: string;
  short: string; // nom court, écrit sur le plan
  to: string | null; // null : pièce pas encore ouverte
  area: string;
}

export const PIECES: PieceDef[] = [
  { key: "salon", label: "Le salon", short: "Salon", to: "/", area: "salon" },
  { key: "bibliotheque", label: "La bibliothèque", short: "Bibliothèque", to: "/bibliotheque", area: "biblio" },
  { key: "conseil", label: "La salle du conseil", short: "Conseil", to: "/conseil", area: "conseil" },
  { key: "projet", label: "La salle de projet", short: "Projet", to: "/projet", area: "projet" },
  { key: "bureaux", label: "Les bureaux", short: "Bureaux", to: "/bureaux", area: "bureaux" },
  { key: "entree", label: "L’entrée", short: "Entrée", to: "/reglages", area: "entree" },
];

export interface Place {
  piece: Piece | null; // null : pas dans la maison
  status: Status;
  label: string;
  present: boolean;
}

/** Où se trouve un membre et ce qu'il fait, à partir de sa présence en direct. */
export function placeOf(member: Member, presence: Presence | undefined): Place {
  if (member.kind === "agent") {
    // Les agents travaillent depuis leur bureau. Tant qu'ils ne tournent pas, ils y attendent, « en préparation ».
    const label =
      member.status === "en_preparation" ? "En préparation · commence à travailler en semaine 3" : member.status_label;
    return { piece: "bureaux", status: member.status, label, present: member.status !== "en_preparation" };
  }
  if (presence) return { piece: presence.piece, status: "en_ligne", label: presence.label, present: true };
  return { piece: null, status: "absent", label: "Pas dans la maison", present: false };
}

export const STATUS_COLOR: Record<Status, string> = {
  en_ligne: "#2f7a57",
  travaille: "#2f7a57",
  en_attente: "#a87405",
  bloque: "#b33a22",
  absent: "#b9aa98",
  en_preparation: "#b9aa98",
};
