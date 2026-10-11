import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence, LayoutGroup, motion } from "motion/react";
import type { Member, Piece } from "../api";
import { firstName } from "../format";
import { PIECES, STATUS_COLOR, placeOf, type Place } from "../house";
import { useLive } from "../live";
import { Avatar } from "./Avatar";

// Les meubles, dessinés comme sur un plan d'architecte. Purement décoratifs.
const FURNITURE: Record<Piece, ReactNode> = {
  salon: (
    <svg width="96" height="46" viewBox="0 0 96 46" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <path d="M8 34h80M14 34V18a7 7 0 0 1 7-7h54a7 7 0 0 1 7 7v16M6 34v8M90 34v8M22 25h52" />
      <rect x="34" y="2" width="28" height="5" rx="2.5" />
    </svg>
  ),
  bibliotheque: (
    <svg width="30" height="70" viewBox="0 0 30 70" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <rect x="2" y="2" width="26" height="66" rx="2" />
      <path d="M2 18h26M2 34h26M2 50h26M8 6v10M13 6v10M20 22v10M9 38v10M16 38v10" />
    </svg>
  ),
  conseil: (
    <svg width="64" height="54" viewBox="0 0 64 54" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <ellipse cx="32" cy="27" rx="18" ry="14" />
      <circle cx="32" cy="5" r="3.5" /><circle cx="32" cy="49" r="3.5" /><circle cx="6" cy="27" r="3.5" /><circle cx="58" cy="27" r="3.5" />
    </svg>
  ),
  projet: (
    <svg width="70" height="42" viewBox="0 0 70 42" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <rect x="2" y="2" width="66" height="38" rx="3" />
      <path d="M24 2v38M46 2v38" />
      <rect x="7" y="8" width="12" height="8" /><rect x="29" y="8" width="12" height="8" /><rect x="29" y="20" width="12" height="8" /><rect x="51" y="8" width="12" height="8" />
    </svg>
  ),
  bureaux: (
    <svg width="150" height="30" viewBox="0 0 150 30" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <rect x="2" y="6" width="40" height="20" rx="2" /><rect x="54" y="6" width="40" height="20" rx="2" /><rect x="106" y="6" width="40" height="20" rx="2" />
      <circle cx="22" cy="3" r="2" /><circle cx="74" cy="3" r="2" /><circle cx="126" cy="3" r="2" />
    </svg>
  ),
  entree: (
    <svg width="48" height="34" viewBox="0 0 48 34" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <rect x="2" y="18" width="44" height="14" rx="3" />
      <path d="M10 2v12M10 6h8" />
    </svg>
  ),
};

const DOORS: Record<Piece, "top" | "left" | "right"> = {
  salon: "top",
  bibliotheque: "right",
  conseil: "left",
  projet: "left",
  bureaux: "top",
  entree: "left",
};

function Token({ member, place, isMe }: { member: Member; place: Place; isMe: boolean }) {
  const ring = isMe ? "#bc600d" : STATUS_COLOR[place.status];
  return (
    <motion.div
      layoutId={`membre-${member.id}`}
      initial={{ opacity: 0, scale: 0.6 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.6 }}
      transition={{ type: "spring", stiffness: 260, damping: 26 }}
    >
      <Link
        to={`/bureaux/${member.id}`}
        className={place.present ? "token" : "token dim"}
        aria-label={`${member.name}${member.kind === "agent" ? " (agent)" : ""} : ${place.label}`}
      >
        <Avatar member={member} size={40} ring={ring} />
        <span className="token-name">{isMe ? "toi" : member.kind === "agent" ? member.name : firstName(member.name)}</span>
        <span className="token-bubble" aria-hidden="true">
          <b>{member.name}{member.kind === "agent" ? " · agent" : ""}</b>
          {place.label}
        </span>
      </Link>
    </motion.div>
  );
}

export function HousePlan({ members }: { members: Member[] }) {
  const { presences, me } = useLive();
  const placed = members
    .filter((m) => m.active)
    .map((m) => ({ member: m, place: placeOf(m, presences[m.id]) }));
  const absents = placed.filter((p) => p.place.piece === null);

  return (
    <LayoutGroup>
      <div className="house" role="group" aria-label="Plan de la maison : qui est dans quelle pièce">
        {PIECES.map((piece) => {
          const here = placed.filter((p) => p.place.piece === piece.key);
          const humansHere = here.filter((p) => p.member.kind === "humain").length;
          const mine = presences[me.id]?.piece === piece.key;
          const className = ["room", here.length ? "has-people" : "", mine ? "mine" : "", piece.to ? "" : "closed"]
            .filter(Boolean)
            .join(" ");
          return (
            <section key={piece.key} className={className} style={{ gridArea: piece.area }} aria-label={piece.label}>
              <span className={`room-door ${DOORS[piece.key]}`} aria-hidden="true" />
              <div className="room-head">
                <span className="room-name">
                  {piece.to ? <Link to={piece.to} aria-label={`Aller dans ${piece.label.toLowerCase()}`}>{piece.short}</Link> : piece.short}
                </span>
                <span className="room-count">
                  {piece.to ? (humansHere ? `${humansHere} ici` : "") : "bientôt"}
                </span>
              </div>
              <div className="room-people">
                <AnimatePresence>
                  {here.map(({ member, place }) => (
                    <Token key={member.id} member={member} place={place} isMe={member.id === me.id} />
                  ))}
                </AnimatePresence>
              </div>
              <span className="room-furniture">{FURNITURE[piece.key]}</span>
            </section>
          );
        })}
      </div>
      {absents.length > 0 && (
        <p className="soft small" style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8 }}>
          Pas dans la maison :
          {absents.map(({ member }) => (
            <Link key={member.id} to={`/bureaux/${member.id}`} style={{ display: "inline-flex", alignItems: "center", gap: 6, color: "var(--ink-2)" }}>
              <Avatar member={member} size={22} /> {firstName(member.name)}
            </Link>
          ))}
        </p>
      )}
    </LayoutGroup>
  );
}
