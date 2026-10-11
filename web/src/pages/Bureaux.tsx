import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, type Member, type Objective } from "../api";
import { AGENT_SHEETS, JAMAIS } from "../agents";
import { avatarColors, firstName, formatAgo, formatNumber } from "../format";
import { PIECES, STATUS_COLOR, placeOf } from "../house";
import { useLive, usePresence } from "../live";
import { Avatar } from "../components/Avatar";
import { IconArrow } from "../components/Icons";
import { categoryLabel } from "./Bibliotheque";
import { POLES, PoleChip, leadOf } from "../poles";
import { PoleObjective } from "../components/PoleObjective";
import { RapportCard } from "../components/RapportCard";

function StatusChip({ member }: { member: Member }) {
  const { presences } = useLive();
  const place = placeOf(member, presences[member.id]);
  const tone = place.status === "en_ligne" || place.status === "travaille" ? "good" : place.status === "bloque" ? "bad" : place.status === "en_attente" ? "wait" : "neutral";
  const text = member.kind === "agent" ? member.status_label : place.present ? "Dans la maison" : "Pas là";
  return (
    <span className={`chip ${tone}`}>
      <span aria-hidden="true" style={{ width: 7, height: 7, borderRadius: 999, background: STATUS_COLOR[place.status] }} />
      {text}
    </span>
  );
}

function OfficeCard({ member, isMe }: { member: Member; isMe: boolean }) {
  const { presences } = useLive();
  const place = placeOf(member, presences[member.id]);
  const { bg } = avatarColors(member.color);
  return (
    <Link to={`/bureaux/${member.id}`} className="card office-card">
      <div className="office-band" style={{ background: bg }} aria-hidden="true" />
      <div className="office-body">
        <Avatar member={member} size={60} ring={STATUS_COLOR[place.status]} />
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8, marginTop: 4 }}>
          <h2 style={{ fontSize: 20, fontWeight: 800 }}>{member.name}</h2>
          {member.kind === "agent" && <span className="chip agent">agent</span>}
          {isMe && <span className="chip brand">toi</span>}
        </div>
        <p className="soft small">{member.title || (member.role === "head" ? "Head" : "Membre")}</p>
        {member.pole && <span><PoleChip pole={member.pole} /></span>}
        <p style={{ fontSize: 14 }}>{place.label}</p>
        <span style={{ marginTop: 4 }}><StatusChip member={member} /></span>
      </div>
    </Link>
  );
}

/** La jauge d'un pôle, en petit, dans l'organigramme. */
function MiniGauge({ objective, color }: { objective: Objective; color: string }) {
  const pct = Math.min(100, Math.round((objective.progress ?? 0) * 100));
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, background: "var(--paper)", borderRadius: 12, padding: "10px 12px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 8, fontSize: 13 }}>
        <span style={{ fontWeight: 650, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{objective.title}</span>
        <span className="num soft" style={{ whiteSpace: "nowrap" }}>
          {objective.current !== null ? formatNumber(objective.current) : "?"} / {formatNumber(objective.target)}
        </span>
      </div>
      <div className="bar" role="img" aria-label={`${pct} % de l’objectif du pôle`} style={{ height: 7 }}>
        <span style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

/** Une ligne de l'organigramme : un humain ou un agent, avec ce qu'il fait en ce moment. */
function Seat({ member, isMe, lead, rapport }: { member: Member; isMe: boolean; lead?: string; rapport?: boolean }) {
  const { presences } = useLive();
  const place = placeOf(member, presences[member.id]);
  return (
    <Link to={`/bureaux/${member.id}`} className="seat">
      <Avatar member={member} size={lead ? 48 : 38} ring={STATUS_COLOR[place.status]} />
      <span style={{ minWidth: 0, display: "flex", flexDirection: "column", gap: 1 }}>
        <span style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 6 }}>
          <b style={{ fontSize: lead ? 16 : 14.5, fontWeight: 750 }}>{member.name}</b>
          {lead && <span className="chip brand" style={{ padding: "1px 8px" }}>{lead}</span>}
          {member.kind === "agent" && <span className="chip agent" style={{ padding: "1px 8px" }}>agent</span>}
          {isMe && <span className="chip neutral" style={{ padding: "1px 8px" }}>toi</span>}
          {member.kind === "humain" && rapport !== undefined && (
            <span className={rapport ? "chip good" : "chip wait"} style={{ padding: "1px 8px" }}>
              {rapport ? "rapport publié" : "rapport à venir"}
            </span>
          )}
        </span>
        <span className="soft" style={{ fontSize: 12.5, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {member.title ? `${member.title} · ` : ""}{place.label}
        </span>
      </span>
    </Link>
  );
}

export function Bureaux() {
  usePresence({ piece: "bureaux", label: "passe dans les bureaux" });
  const { me } = useLive();
  const members = useQuery({ queryKey: ["membres"], queryFn: api.members });
  const [vue, setVue] = useState<"organigramme" | "bureaux">("organigramme");
  const objectives = useQuery({ queryKey: ["objectifs-poles"], queryFn: api.poleObjectives });
  const semaine = useQuery({ queryKey: ["rapports", "semaine"], queryFn: api.rapportsSemaine });
  const active = (members.data ?? []).filter((m) => m.active);
  const published = new Set((semaine.data?.rapports ?? []).map((r) => r.author_id));
  const hasRapport = (m: Member) => (m.kind === "humain" ? published.has(m.id) : undefined);

  const direction = POLES[0];
  const ceo = leadOf("direction", active);
  const poles = POLES.slice(1);
  const transversaux = active.filter((m) => m.kind === "agent" && !m.pole);
  const sansPole = active.filter((m) => m.kind === "humain" && !m.pole);
  const team = (pole: string, lead?: Member) =>
    active.filter((m) => m.pole === pole && m.id !== lead?.id).sort((a, b) => (a.kind === b.kind ? 0 : a.kind === "humain" ? -1 : 1));

  return (
    <div className="page">
      <header style={{ display: "flex", flexWrap: "wrap", alignItems: "flex-end", justifyContent: "space-between", gap: 16, paddingTop: 8 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <span className="eyebrow">La maison</span>
          <h1 className="display">Les bureaux</h1>
          <p className="soft" style={{ fontSize: 16, maxWidth: "62ch" }}>
            Le CEO, et trois heads qui dirigent chacun un pôle et lui rendent compte. Humains et agents, chacun à sa place.
          </p>
        </div>
        <div className="segmented" role="group" aria-label="Affichage">
          <button type="button" aria-pressed={vue === "organigramme"} onClick={() => setVue("organigramme")}>Organigramme</button>
          <button type="button" aria-pressed={vue === "bureaux"} onClick={() => setVue("bureaux")}>Tous les bureaux</button>
        </div>
      </header>

      {vue === "bureaux" ? (
        <div className="grid-cards">
          {active.map((m) => <OfficeCard key={m.id} member={m} isMe={m.id === me.id} />)}
        </div>
      ) : (
        <div className="org">
          <section className="card org-top" aria-label={direction.label}>
            <span className="eyebrow" style={{ color: direction.color.fg }}>{direction.label}</span>
            {ceo ? <Seat member={ceo} isMe={ceo.id === me.id} lead={direction.lead} rapport={hasRapport(ceo)} /> : (
              <p className="soft small">Le CEO n’est pas encore rangé ici : dans Réglages, mets ton pôle sur « Direction » et ton rôle sur « CEO ».</p>
            )}
            {team("direction", ceo).map((m) => <Seat key={m.id} member={m} isMe={m.id === me.id} />)}
          </section>

          <div className="org-link" aria-hidden="true"><span>rendent compte au CEO</span></div>

          <div className="org-poles">
            {poles.map((p) => {
              const lead = leadOf(p.key, active);
              const members = team(p.key, lead);
              return (
                <section key={p.key} className="card org-pole" aria-label={p.label}>
                  <div className="card-head">
                    <h2 style={{ fontSize: 18, fontWeight: 800 }}>{p.label}</h2>
                    <span className="chip" style={{ background: p.color.bg, color: p.color.fg }}>{p.lead}</span>
                  </div>
                  {objectives.data?.[p.key] ? (
                    <MiniGauge objective={objectives.data[p.key]!} color={p.color.fg} />
                  ) : (
                    <p className="soft small">Pas encore d’objectif pour ce pôle.</p>
                  )}
                  {lead ? <Seat member={lead} isMe={lead.id === me.id} lead={p.lead} rapport={hasRapport(lead)} /> : (
                    <p className="soft small">Head à faire entrer dans Réglages ({p.lead}).</p>
                  )}
                  {members.length > 0 && <div className="org-divider" />}
                  {members.map((m) => <Seat key={m.id} member={m} isMe={m.id === me.id} rapport={hasRapport(m)} />)}
                  {members.length === 0 && lead && <p className="soft small">Pas encore d’équipe ni d’agent dans ce pôle.</p>}
                </section>
              );
            })}
          </div>

          {(transversaux.length > 0 || sansPole.length > 0) && (
            <div className="org-poles" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 300px), 1fr))" }}>
              {transversaux.length > 0 && (
                <section className="card org-pole" aria-label="Pour toute la maison">
                  <h2 style={{ fontSize: 16, fontWeight: 800 }}>Pour toute la maison</h2>
                  {transversaux.map((m) => <Seat key={m.id} member={m} isMe={m.id === me.id} />)}
                </section>
              )}
              {sansPole.length > 0 && (
                <section className="card org-pole" aria-label="Pas encore rangés">
                  <h2 style={{ fontSize: 16, fontWeight: 800 }}>Pas encore rangés dans un pôle</h2>
                  {sansPole.map((m) => <Seat key={m.id} member={m} isMe={m.id === me.id} />)}
                  <Link to="/reglages" className="small">Ranger dans Réglages</Link>
                </section>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function Bureau() {
  const id = Number(useParams().id);
  const { me, presences } = useLive();
  const members = useQuery({ queryKey: ["membres"], queryFn: api.members });
  const member = (members.data ?? []).find((m) => m.id === id);
  usePresence({ piece: "bureaux", label: member ? (member.id === me.id ? "est dans son bureau" : `passe voir ${firstName(member.name)}`) : "passe dans les bureaux" });

  const events = useQuery({ queryKey: ["evenements", "acteur", id], queryFn: () => api.events(id), enabled: !!member });
  const taches = useQuery({ queryKey: ["taches", "membre", id], queryFn: () => api.taches(id), enabled: !!member });
  const documents = useQuery({ queryKey: ["documents", "", "", false], queryFn: () => api.documents({}), enabled: !!member });

  if (members.isLoading) return <div className="page"><p className="soft">Chargement…</p></div>;
  if (!member) {
    return (
      <div className="page">
        <p className="notice bad">Ce bureau n’existe pas.</p>
        <Link to="/bureaux">Retour aux bureaux</Link>
      </div>
    );
  }

  const place = placeOf(member, presences[member.id]);
  const room = PIECES.find((p) => p.key === place.piece);
  const sheet = member.kind === "agent" ? AGENT_SHEETS[member.name] : undefined;
  const touched = (documents.data ?? []).filter((d) => d.updated_by.id === member.id).slice(0, 6);

  return (
    <div className="page">
      <span className="soft small"><Link to="/bureaux" style={{ color: "var(--ink-2)" }}>Les bureaux</Link> › {member.name}</span>

      <section className="card" style={{ padding: 30, flexDirection: "row", flexWrap: "wrap", alignItems: "center", gap: 24 }}>
        <Avatar member={member} size={92} ring={STATUS_COLOR[place.status]} />
        <div style={{ flex: "1 1 320px", minWidth: 0, display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 10 }}>
            <h1 className="display" style={{ fontSize: "clamp(30px, 4vw, 44px)" }}>{member.name}</h1>
            {member.kind === "agent" ? <span className="chip agent">agent</span> : <span className={member.role === "head" ? "chip brand" : "chip neutral"}>{member.role === "head" ? "Head" : "Membre"}</span>}
            <PoleChip pole={member.pole} />
            <StatusChip member={member} />
          </div>
          {member.title && <p className="soft" style={{ fontSize: 16 }}>{member.title}</p>}
          <p style={{ fontSize: 16 }}>
            <b>En ce moment :</b> {place.label}
            {room && place.present && member.kind === "humain" && <> · <span className="soft">{room.label.toLowerCase()}</span></>}
          </p>
        </div>
      </section>

      {member.pole && <PoleObjective pole={member.pole} me={me} />}
      <RapportCard member={member} me={me} />

      {sheet && (
        <section className="card" aria-labelledby="fiche" style={{ gap: 18 }}>
          <div className="card-head">
            <h2 id="fiche" className="title">Sa fiche de poste</h2>
            <span className="chip neutral">{sheet.modele} · budget {sheet.budget} $ / mois</span>
          </div>
          {member.status === "en_preparation" && (
            <p className="notice agent">
              {member.name} fait déjà partie de l’équipe, mais ne travaille pas encore : les agents se mettent au travail en semaine 3, dès que la clé Anthropic de Nyuman est entrée par l’équipe.
            </p>
          )}
          <div className="grid-cards" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 240px), 1fr))" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span className="eyebrow" style={{ color: "var(--good)" }}>Seul</span>
              <p>{sheet.seul}</p>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span className="eyebrow" style={{ color: "var(--wait)" }}>Avec un oui d’un head</span>
              <p>{sheet.avecOui}</p>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span className="eyebrow" style={{ color: "var(--bad)" }}>Jamais</span>
              <p>{JAMAIS}</p>
            </div>
          </div>
          <p className="soft small">Travaille pour : {sheet.pourQui}.</p>
        </section>
      )}

      <section className="card" aria-labelledby="ses-taches" style={{ gap: 6 }}>
        <div className="card-head">
          <h2 id="ses-taches" className="title">Ses tâches</h2>
          <Link to="/projet" className="small">Salle de projet</Link>
        </div>
        {taches.data && taches.data.filter((t) => t.status !== "fait").length === 0 && (
          <p className="soft" style={{ padding: "8px 0" }}>
            Aucune tâche ouverte{member.kind === "agent" ? ". Tu peux lui en confier une dans la salle de projet." : "."}
          </p>
        )}
        <ul className="list-plain">
          {(taches.data ?? []).filter((t) => t.status !== "fait").map((t) => (
            <li key={t.id} className="feed-item">
              <Link to={`/projet?tache=${t.id}`} style={{ flex: 1, minWidth: 0, color: "var(--ink)", textDecoration: "none", fontWeight: 600 }}>{t.title}</Link>
              {t.due_date && <span className="chip neutral">{new Date(`${t.due_date}T12:00:00`).toLocaleDateString("fr-FR", { day: "numeric", month: "short" })}</span>}
              <span className={t.status === "en_cours" ? "chip good" : t.status === "en_attente" ? "chip wait" : "chip neutral"}>
                {t.status === "en_cours" ? "en cours" : t.status === "en_attente" ? "en attente" : "à faire"}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <div className="row">
        <section className="card col-main" aria-labelledby="actions" style={{ gap: 6 }}>
          <h2 id="actions" className="title">Ses dernières actions</h2>
          {events.data && events.data.length === 0 && <p className="soft" style={{ padding: "14px 0" }}>Rien encore.</p>}
          <ul className="list-plain">
            {(events.data ?? []).map((ev) => (
              <li key={ev.id} className="feed-item">
                <p className="feed-text">{ev.link ? <Link to={ev.link}>{ev.text}</Link> : ev.text}</p>
                <span className="feed-time">{formatAgo(ev.created_at)}</span>
              </li>
            ))}
          </ul>
        </section>
        <section className="card col-side" aria-labelledby="docs" style={{ gap: 6 }}>
          <h2 id="docs" className="title">Ses documents</h2>
          {documents.data && touched.length === 0 && <p className="soft" style={{ padding: "14px 0" }}>Aucun document modifié.</p>}
          <ul className="list-plain">
            {touched.map((d) => (
              <li key={d.id} className="feed-item">
                <Link to={`/bibliotheque/${d.id}`} style={{ display: "flex", flexDirection: "column", gap: 2, color: "var(--ink)", textDecoration: "none", flex: 1 }}>
                  <b style={{ fontWeight: 650 }}>{d.title}</b>
                  <span className="soft small">{categoryLabel(d.category)} · {formatAgo(d.updated_at)}</span>
                </Link>
                <IconArrow />
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
