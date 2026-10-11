import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "motion/react";
import { api, type Kpis, type Member } from "../api";
import { ObjectiveForm, metricLabel } from "../components/ObjectiveForm";
import { firstName, formatAgo, formatNumber, formatToday, greeting, isoWeek } from "../format";
import { placeOf } from "../house";
import { useLive, usePresence } from "../live";
import { Avatar } from "../components/Avatar";
import { HousePlan } from "../components/HousePlan";


function ObjectiveHero({ me }: { me: Member }) {
  const objective = useQuery({ queryKey: ["objectif"], queryFn: () => api.objective(), refetchInterval: 60_000 });
  const [editing, setEditing] = useState(false);
  const o = objective.data;
  const isHead = me.role === "head";

  if (editing) {
    return (
      <section className="card" aria-labelledby="obj-form" style={{ padding: 28 }}>
        <h2 id="obj-form" className="title">L’objectif du trimestre</h2>
        <p className="soft small">Un seul chiffre, commun à tous : humains et agents travaillent pour lui.</p>
        <ObjectiveForm initial={o ?? null} heading="Objectif du trimestre" onDone={() => setEditing(false)} />
      </section>
    );
  }
  if (objective.isLoading) return <section className="card night goal" style={{ minHeight: 220 }} aria-busy="true" />;

  if (!o) {
    return (
      <section className="card night goal" aria-labelledby="objectif">
        <span className="eyebrow" style={{ color: "var(--brand-light)" }}>Objectif du trimestre</span>
        <h2 id="objectif" className="display" style={{ maxWidth: "16ch" }}>Quel chiffre on va chercher ensemble ?</h2>
        <p className="soft">Humains et agents travailleront tous vers lui. Il s’affichera en haut de chaque page.</p>
        {isHead ? (
          <button type="button" className="btn brand" style={{ alignSelf: "flex-start" }} onClick={() => setEditing(true)}>Fixer l’objectif</button>
        ) : (
          <p className="soft small">Un head le fixera.</p>
        )}
      </section>
    );
  }

  const pct = Math.min(100, Math.round((o.progress ?? 0) * 100));
  return (
    <section className="card night goal" aria-labelledby="objectif">
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: "12px 24px", alignItems: "flex-start" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 8, minWidth: 0 }}>
          <span className="eyebrow" style={{ color: "var(--brand-light)" }}>Objectif du trimestre · {o.quarter}</span>
          <h2 id="objectif" style={{ fontSize: "clamp(24px, 3vw, 32px)", fontWeight: 800, maxWidth: "22ch" }}>{o.title}</h2>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {o.progress !== null && o.progress >= 1 && <span className="chip good">Atteint</span>}
          {isHead && <button type="button" className="btn small ghost-night" onClick={() => setEditing(true)}>Modifier</button>}
        </div>
      </div>

      {o.current !== null ? (
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "flex-end", gap: "8px 18px" }}>
          <span className="goal-number num">{formatNumber(o.current)}</span>
          <span style={{ fontSize: 20, fontWeight: 650, color: "var(--cream-2)", paddingBottom: 8 }}>
            / {formatNumber(o.target)} {metricLabel(o.metric)}
          </span>
        </div>
      ) : (
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "flex-end", gap: "8px 18px" }}>
          <span className="goal-number num" style={{ color: "var(--brand-light)" }}>{formatNumber(o.target)}</span>
          <span style={{ fontSize: 20, fontWeight: 650, color: "var(--cream-2)", paddingBottom: 8 }}>
            {metricLabel(o.metric)} visés
          </span>
        </div>
      )}
      <div className={o.current !== null ? "goal-bar" : "goal-bar pending"} role="img" aria-label={o.current !== null ? `${pct} % de l’objectif` : "Chiffre en direct pas encore branché"}>
        <span style={{ width: `${pct}%` }} />
      </div>

      <div className="goal-stats">
        {o.current !== null && o.needed_per_week !== null && o.current < o.target && (
          <div className="goal-stat"><b>{formatNumber(o.needed_per_week)} / semaine</b><span>le rythme à tenir</span></div>
        )}
        <div className="goal-stat"><b>{o.weeks_left} semaine{o.weeks_left > 1 ? "s" : ""}</b><span>avant la fin du trimestre</span></div>
        {o.current !== null ? (
          <div className="goal-stat"><b>{pct} %</b><span>du chemin fait</span></div>
        ) : (
          <div className="goal-stat"><b>Chiffre à brancher</b><span>dès que la base Nyuman est reliée (Réglages)</span></div>
        )}
      </div>
    </section>
  );
}

const STATUS_LABEL = { a_faire: "à faire", en_cours: "en cours", en_attente: "en attente", fait: "fait" } as const;

/** Ce que j'ai à faire : les tâches ouvertes qui me sont confiées. */
function MesTaches({ me }: { me: Member }) {
  const taches = useQuery({ queryKey: ["taches", "moi", me.id], queryFn: () => api.taches(me.id) });
  const open = (taches.data ?? []).filter((t) => t.status !== "fait").slice(0, 5);
  return (
    <section className="card" aria-labelledby="mes-taches" style={{ gap: 8 }}>
      <div className="card-head">
        <h2 id="mes-taches" className="title">Tes tâches</h2>
        <Link to="/projet" className="small">Salle de projet</Link>
      </div>
      {taches.data && open.length === 0 && <p className="soft small">Rien ne t’attend. Prends une tâche dans la salle de projet.</p>}
      <ul className="list-plain">
        {open.map((t) => (
          <li key={t.id} className="feed-item">
            <Link to={`/projet?tache=${t.id}`} style={{ flex: 1, minWidth: 0, color: "var(--ink)", textDecoration: "none", fontWeight: 600, fontSize: 14.5 }}>
              {t.title}
            </Link>
            <span className={t.status === "en_cours" ? "chip good" : t.status === "en_attente" ? "chip wait" : "chip neutral"}>{STATUS_LABEL[t.status]}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

type FeedFilter = "tout" | "humains" | "agents";

function Feed() {
  const events = useQuery({ queryKey: ["evenements"], queryFn: () => api.events(), refetchInterval: 120_000 });
  const [filter, setFilter] = useState<FeedFilter>("tout");
  const items = (events.data ?? []).filter(
    (e) => filter === "tout" || (filter === "agents" ? e.actor.kind === "agent" : e.actor.kind === "humain"),
  );

  return (
    <section className="card" aria-labelledby="fil" style={{ gap: 6, flex: 1 }}>
      <div className="card-head">
        <h2 id="fil" className="title">Le fil</h2>
        <div className="segmented" role="group" aria-label="Filtrer le fil">
          {(["tout", "humains", "agents"] as FeedFilter[]).map((f) => (
            <button key={f} type="button" aria-pressed={filter === f} onClick={() => setFilter(f)}>
              {f === "tout" ? "Tout" : f === "humains" ? "Humains" : "Agents"}
            </button>
          ))}
        </div>
      </div>
      {events.data && items.length === 0 && (
        <p className="soft" style={{ padding: "18px 0" }}>
          {filter === "agents" ? "Les agents n’ont encore rien fait : ils commencent en semaine 3." : "Rien pour l’instant. Chaque action de l’équipe apparaîtra ici, en direct."}
        </p>
      )}
      <ul className="list-plain" style={{ maxHeight: 520, overflowY: "auto" }}>
        <AnimatePresence initial={false}>
          {items.map((ev) => (
            <motion.li
              key={ev.id}
              className="feed-item"
              layout
              initial={{ opacity: 0, y: -10, backgroundColor: "rgba(247,226,203,0.9)" }}
              animate={{ opacity: 1, y: 0, backgroundColor: "rgba(247,226,203,0)" }}
              transition={{ duration: 0.6 }}
            >
              <Avatar member={ev.actor} size={34} />
              <p className="feed-text">
                <b>{ev.actor.name}</b> {ev.link ? <Link to={ev.link}>{ev.text}</Link> : ev.text}
              </p>
              <span className="feed-time">{formatAgo(ev.created_at)}</span>
            </motion.li>
          ))}
        </AnimatePresence>
      </ul>
    </section>
  );
}

function KpiStrip({ kpis }: { kpis: Kpis | undefined }) {
  return (
    <section aria-labelledby="kpi" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div className="card-head">
        <h2 id="kpi" className="title">L’app Nyuman</h2>
        {kpis?.available && kpis.updated_at && <span className="soft small">Mis à jour {formatAgo(kpis.updated_at)}</span>}
      </div>
      {kpis && !kpis.available ? (
        <div className="card" style={{ flexDirection: "row", flexWrap: "wrap", alignItems: "center", gap: 16 }}>
          <span className="chip wait">À brancher</span>
          <p style={{ flex: "1 1 320px" }} className="soft">{kpis.reason}</p>
          <Link to="/reglages" className="btn small">Voir les branchements</Link>
        </div>
      ) : (
        <div className="grid-cards" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 200px), 1fr))" }}>
          {(kpis?.values ?? []).map((k) => (
            <div key={k.key} className="card kpi">
              <span className="soft small">{k.label}</span>
              <span className="kpi-value">
                {formatNumber(k.unit === "fcfa" ? Math.round(k.value) : k.value)}
                {k.unit === "fcfa" && <span className="kpi-unit"> FCFA</span>}
              </span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

const RYTHME = [
  { day: "Lundi", text: "Rapports et 3 propositions par agent" },
  { day: "Mardi", text: "Le Contradicteur relit tout" },
  { day: "Mercredi", text: "Réunion des heads, 30 min" },
  { day: "Jeudi", text: "Exécution" },
  { day: "Vendredi", text: "Exécution et bilan" },
];

function Week() {
  const today = new Date().getDay() - 1; // 0 = lundi
  return (
    <section aria-labelledby="semaine" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <h2 id="semaine" className="title">Le rythme de la semaine</h2>
      <ol className="week list-plain" style={{ display: "grid" }}>
        {RYTHME.map((r, i) => (
          <li key={r.day} className={i === today ? "week-day today" : "week-day"}>
            <span className="eyebrow">{r.day}{i === today ? " · aujourd’hui" : ""}</span>
            <span style={{ fontSize: 14, fontWeight: 600 }}>{r.text}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}

export function Salon({ me }: { me: Member }) {
  usePresence({ piece: "salon", label: "est dans le salon" });
  const { presences } = useLive();
  const kpis = useQuery({ queryKey: ["kpis"], queryFn: api.kpis, refetchInterval: 60_000 });
  const members = useQuery({ queryKey: ["membres"], queryFn: api.members, refetchInterval: 60_000 });

  const all = (members.data ?? []).filter((m) => m.active);
  const humansIn = all.filter((m) => m.kind === "humain" && placeOf(m, presences[m.id]).present).length;
  const agents = all.filter((m) => m.kind === "agent");
  const agentsWorking = agents.filter((m) => m.status !== "en_preparation").length;

  return (
    <div className="page">
      <header style={{ display: "flex", flexDirection: "column", gap: 10, paddingTop: 8 }}>
        <span className="eyebrow">{formatToday()} · semaine {isoWeek()}</span>
        <h1 className="display">{greeting()}, {firstName(me.name)}.</h1>
        <p className="soft" style={{ fontSize: 16 }}>
          {humansIn} humain{humansIn > 1 ? "s" : ""} dans la maison
          {agents.length > 0 && (agentsWorking > 0 ? `, ${agentsWorking} agent${agentsWorking > 1 ? "s" : ""} au travail` : `, ${agents.length} agents en préparation`)}.
        </p>
      </header>

      <ObjectiveHero me={me} />

      <div className="row">
        <section className="card col-main" aria-labelledby="maison" style={{ gap: 14 }}>
          <div className="card-head">
            <h2 id="maison" className="title">La maison, en ce moment</h2>
            <span className="soft small">Passe la souris sur quelqu’un pour voir ce qu’il fait</span>
          </div>
          <HousePlan members={members.data ?? []} />
        </section>
        <div className="col-side">
          <MesTaches me={me} />
          <Feed />
        </div>
      </div>

      <KpiStrip kpis={kpis.data} />
      <Week />
    </div>
  );
}
