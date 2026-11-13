import { useEffect, useState, type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AlertTriangle, ArrowRight, Bot, Gavel, MessageCircle, PartyPopper, Plus, Sparkles, Store } from "lucide-react";
import { appStatsApi, fmtMinutes, type AppStats, type AppStatsResponse, type MiniTask, type Role, type Space } from "../../lib/api";
import { useSession } from "../../lib/session";
import { Avatar } from "../../components/Avatar";
import { Panel, SoonTag } from "../../components/ui";
import { TrackList, type RowAsk } from "../../components/TrackList";

/** Ce qu'on demande le plus souvent à son agent, prêt à envoyer. Un clic = un réveil (quelques centimes). */
export const AGENT_ASKS: Record<Role, string[]> = {
  dg: ["Relis la dernière décision et dis-moi ce qui cloche",
       "Donne ton avis sur la proposition en cours",
       "Prépare-moi 3 questions pour le point de la semaine"],
  coord: ["Prépare mon point du lundi",
          "Qui est en retard, et sur quoi ?",
          "Liste les décisions en attente"],
  growth: ["Écris un message aux salons inscrits qui n'ont pas eu de réservation",
           "Où en est-on du 12 décembre ?",
           "Propose 3 contenus pour cette semaine"],
  ops: ["Résume les litiges ouverts et ce qu'il faut faire",
        "Quelles échéances arrivent ce mois-ci ?",
        "Relis le dernier contrat et dis-moi les risques"],
  finance: ["Fais le point de trésorerie",
            "Calcule la marge du mois",
            "Prépare les chiffres du prochain comité"],
  tech: ["Où en est le prochain build ?",
         "Qu'est-ce qui bloque côté app en ce moment ?",
         "Résume ce qui a changé cette semaine"],
};

export const ROLE_LABEL: Record<Role, string> = {
  dg: "Direction générale", coord: "Coordination", growth: "Croissance", ops: "Opérations et juridique", finance: "Finance", tech: "Produit et technique",
};

/** Ouvre une discussion avec le message déjà écrit. L'envoi reste à la personne. */
export function useAsk() {
  const navigate = useNavigate();
  return (memberId: string, texte?: string) =>
    navigate(`/discussions?avec=${memberId}${texte ? `&texte=${encodeURIComponent(texte)}` : ""}`);
}

function AskButton({ to, texte, children, tone = "soft" }: {
  to: string; texte: string; children: ReactNode; tone?: "soft" | "ghost";
}) {
  const ask = useAsk();
  return (
    <button onClick={() => ask(to, texte)}
      className={`shrink-0 rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
        tone === "soft" ? "bg-accent-soft text-accent hover:bg-accent hover:text-white"
                        : "text-accent hover:underline"}`}>
      {children}
    </button>
  );
}

/** L'agent qui appuie mon poste : à qui on confie les petites préparations. */
function useMyAgent(space: Space) {
  const { members } = useSession();
  return members.find((m) => m.id === space.agents[0]) ?? null;
}

const more = (to: string, label = "Tout voir") => (
  <Link to={to} className="inline-flex items-center gap-1 text-sm font-medium text-accent hover:underline">{label} <ArrowRight size={14} /></Link>
);

/** Le haut de l'espace : mon poste et l'agent qui m'appuie. */
export function MyPostCard({ space }: { space: Space }) {
  const { members } = useSession();
  const navigate = useNavigate();
  const agents = space.agents.map((id) => members.find((m) => m.id === id)).filter(Boolean) as typeof members;
  const asks = space.roles.flatMap((r) => AGENT_ASKS[r] ?? []).slice(0, 3);
  const ask = (agentId: string, texte?: string) =>
    navigate(`/discussions?avec=${agentId}${texte ? `&texte=${encodeURIComponent(texte)}` : ""}`);
  return (
    <div className="rounded-2xl bg-white p-4 text-ink shadow-[0_16px_32px_-16px_rgba(188,96,13,0.35)] sm:p-5">
      <div className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Mon poste</div>
      {space.positions.length ? (
        space.positions.map((p) => <div key={p.id} className="mt-1 text-lg font-semibold leading-snug">{p.title}</div>)
      ) : (
        <p className="mt-1 text-sm text-ink-soft">Pas encore de poste dans l'organigramme. <Link to="/equipe" className="text-accent hover:underline">Voir l'équipe</Link></p>
      )}
      {agents.map((a) => (
        <div key={a.id} className="mt-4">
          <button onClick={() => ask(a.id)}
            className="flex w-full items-center gap-3 rounded-xl border border-line px-3 py-2 text-left transition hover:border-accent/40 hover:bg-accent-soft/40">
            <Avatar member={a} size="sm" />
            <span className="min-w-0 flex-1">
              <span className="block text-sm font-semibold">{a.name}, votre agent</span>
              <span className="block truncate text-xs text-ink-soft">{a.title}</span>
            </span>
            <MessageCircle size={16} className="text-accent" />
          </button>
          {a.id === agents[0].id && asks.length > 0 && (
            <div className="mt-2 space-y-1.5">
              {asks.map((t) => (
                <button key={t} onClick={() => ask(a.id, t)}
                  className="flex w-full items-start gap-2 rounded-xl bg-surface px-3 py-2 text-left text-[13px] leading-snug transition hover:bg-accent-soft">
                  <Sparkles size={13} className="mt-0.5 shrink-0 text-accent" /> {t}
                </button>
              ))}
              <p className="pt-0.5 text-[11px] text-ink-muted">Le message s'écrit tout seul : vous relisez avant d'envoyer.</p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function Tile({ label, value, tone = "", sub }: { label: string; value: ReactNode; tone?: string; sub?: ReactNode }) {
  return (
    <div className="rounded-2xl bg-surface px-3.5 py-3">
      <div className="truncate text-[11px] leading-tight text-ink-soft" title={label}>{label}</div>
      <div className={`mt-0.5 text-2xl font-semibold tracking-tight ${tone}`}>{value}</div>
      {sub && <div className="text-[11px] text-ink-muted">{sub}</div>}
    </div>
  );
}

function TaskLine({ t, relance }: { t: MiniTask; relance?: boolean }) {
  const { me, members } = useSession();
  const navigate = useNavigate();
  const who = members.find((m) => m.id === t.assignee_id);
  const today = new Date().toISOString().slice(0, 10);
  const late = !!t.due_date && t.due_date < today;
  const texte = t.due_date
    ? `Bonjour ${who?.name.split(" ")[0] ?? ""}, où en est « ${t.title} » ? C'était pour le ${new Date(t.due_date + "T12:00").toLocaleDateString("fr-FR", { day: "numeric", month: "long" })}.`
    : `Bonjour ${who?.name.split(" ")[0] ?? ""}, où en est « ${t.title} » ?`;
  return (
    <li className="flex items-center gap-2.5 py-2">
      {who ? <Avatar member={who} size="sm" /> : <span className="h-7 w-7 shrink-0 rounded-full border border-dashed border-line" />}
      <Link to={`/projets/${t.project_id}`} className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium hover:text-accent">{t.title}</span>
        <span className="block truncate text-xs text-ink-muted">{t.project_icon} {t.project_name}</span>
      </Link>
      {t.priority === "high" && <span className="rounded-full bg-[#FDE6E2] px-2 py-0.5 text-[10px] font-semibold text-[#B5321F]">Urgent</span>}
      {t.due_date && <span className={`shrink-0 text-xs ${late ? "font-medium text-busy" : "text-ink-soft"}`}>
        {late ? "en retard" : new Date(t.due_date + "T12:00").toLocaleDateString("fr-FR", { weekday: "short", day: "numeric" })}</span>}
      {relance && who && who.id !== me?.id && (
        <button onClick={() => navigate(`/discussions?avec=${who.id}&texte=${encodeURIComponent(texte)}`)}
          className="shrink-0 rounded-lg bg-accent-soft px-2.5 py-1 text-xs font-semibold text-accent hover:bg-accent hover:text-white">
          Relancer
        </button>
      )}
    </li>
  );
}

function VoteBlock({ space }: { space: Space }) {
  const { members } = useSession();
  const list = space.to_vote ?? [];
  return (
    <Panel title="À voter" action={more("/conseil", "Salle du conseil")}>
      {list.length === 0 ? (
        <Link to="/conseil?nouvelle=1" className="flex items-center gap-3 rounded-2xl bg-surface p-4 text-sm text-ink-soft hover:bg-surface-2">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-soft text-blue"><Gavel size={18} /></span>
          Rien à voter. Faire une proposition →
        </Link>
      ) : (
        <ul className="space-y-2">
          {list.map((p) => (
            <li key={p.id}>
              <Link to={`/conseil?p=${p.id}`} className="flex items-center gap-3 rounded-2xl border border-line p-3 transition hover:border-accent/40 hover:bg-surface">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-soft text-blue"><Gavel size={16} /></span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-semibold">{p.title}</span>
                  <span className="block text-xs text-ink-soft">
                    par {members.find((m) => m.id === p.author_id)?.name ?? p.author_id}
                    {p.deadline && ` · avant le ${new Date(p.deadline + "T12:00").toLocaleDateString("fr-FR", { day: "numeric", month: "short" })}`}
                    {p.has_opinion ? " · avis de Koffi donné" : ""}
                  </span>
                </span>
                <span className="rounded-lg bg-accent px-3 py-1.5 text-xs font-semibold text-white">Voter</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

function Departments({ space }: { space: Space }) {
  const { me, members } = useSession();
  return (
    <Panel title="Où en sont les départements" action={more("/projets", "Projets")}>
      <div className="grid gap-2 sm:grid-cols-2">
        {space.departments!.map((d) => {
          const head = members.find((m) => m.id === d.head_id);
          const texte = head && d.late_titles.length
            ? `Bonjour ${head.name.split(" ")[0]}, où en est-on sur ${d.late_titles.map((t) => `« ${t} »`).join(", ")} ? C'est en retard.`
            : "";
          return (
            <div key={d.role} className="rounded-2xl bg-surface px-3.5 py-3">
              <div className="text-sm font-semibold leading-snug">{d.department}</div>
              {head && <div className="truncate text-xs text-ink-muted">{head.name}</div>}
              <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink-soft">
                <span><b className="text-ink">{d.open}</b> en cours</span>
                <span className={d.overdue ? "font-medium text-busy" : ""}><b>{d.overdue}</b> en retard</span>
                <span className="text-[#18794A]"><b>{d.done_week}</b> finies (7 j)</span>
              </div>
              {d.overdue > 0 && head && head.id !== me?.id && (
                <div className="mt-2"><AskButton to={head.id} texte={texte}>Demander à {head.name.split(" ")[0]}</AskButton></div>
              )}
            </div>
          );
        })}
      </div>
      {space.budget_alerts && space.budget_alerts.length > 0 && (
        <ul className="mt-3 space-y-1.5">
          {space.budget_alerts.map((b) => (
            <li key={b.id} className="flex items-center gap-2 rounded-xl bg-[#FFF8E5] px-3 py-2 text-sm">
              <AlertTriangle size={14} className={b.pct >= 100 ? "text-busy" : "text-away"} />
              <span className="min-w-0 flex-1 truncate">{b.icon} {b.name}</span>
              <span className="shrink-0 text-xs font-medium">{fmtMinutes(b.used_minutes)} sur {b.hours_budget} h ({b.pct} %)</span>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

function WeekDue({ space }: { space: Space }) {
  const { members } = useSession();
  const navigate = useNavigate();
  const today = new Date().toISOString().slice(0, 10);
  const all = space.week_due ?? [];
  const late = all.filter((t) => t.due_date && t.due_date < today);
  const soon = all.filter((t) => !late.includes(t));
  return (
    <Panel title="À faire avancer" action={more("/projets")}>
      {all.length === 0 ? <p className="rounded-2xl bg-surface p-4 text-sm text-ink-soft">Rien n'est en retard et rien n'arrive à échéance cette semaine.</p> : (
        <>
          {late.length > 0 && (
            <>
              <h3 className="mb-1 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-busy">
                <AlertTriangle size={12} /> En retard · {late.length}
              </h3>
              <ul className="divide-y divide-line">{late.slice(0, 6).map((t) => <TaskLine key={t.id} t={t} relance />)}</ul>
            </>
          )}
          {soon.length > 0 && (
            <>
              <h3 className={`mb-1 text-xs font-semibold uppercase tracking-wide text-ink-muted ${late.length ? "mt-4" : ""}`}>Cette semaine · {soon.length}</h3>
              <ul className="divide-y divide-line">{soon.slice(0, 6).map((t) => <TaskLine key={t.id} t={t} relance />)}</ul>
            </>
          )}
        </>
      )}
      {space.quiet_projects && space.quiet_projects.length > 0 && (
        <div className="mt-4">
          <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-muted">Rien n'a bougé depuis 14 jours</h3>
          <ul className="divide-y divide-line">
            {space.quiet_projects.map((p) => {
              const owner = members.find((m) => m.id === p.owner_id);
              return (
                <li key={p.id} className="flex items-center gap-2.5 py-2">
                  <Link to={`/projets/${p.id}`} className="min-w-0 flex-1 truncate text-sm font-medium hover:text-accent">{p.icon} {p.name}</Link>
                  {owner && (
                    <button onClick={() => navigate(`/discussions?avec=${owner.id}&texte=${encodeURIComponent(`Bonjour ${owner.name.split(" ")[0]}, où en est le projet « ${p.name} » ? Rien n'a bougé depuis deux semaines.`)}`)}
                      className="shrink-0 rounded-lg bg-accent-soft px-2.5 py-1 text-xs font-semibold text-accent hover:bg-accent hover:text-white">
                      Demander à {owner.name.split(" ")[0]}
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </Panel>
  );
}

function DeptTasks({ space, role }: { space: Space; role: Role }) {
  const agent = useMyAgent(space);
  const d = space.dept?.[role];
  if (!d) return null;
  const action = agent && d.open > 0
    ? <AskButton tone="ghost" to={agent.id}
        texte={`${agent.name}, fais-moi un point court sur « ${d.department} » : ce qui avance, ce qui bloque, et ce que je devrais débloquer en premier.`}>
        Demander un point
      </AskButton>
    : more("/projets");
  return (
    <Panel title={`Tâches · ${d.department}`} action={action}>
      <div className="mb-3 flex gap-2 text-xs">
        <span className="rounded-full bg-surface px-2.5 py-1"><b>{d.open}</b> en cours</span>
        <span className={`rounded-full px-2.5 py-1 ${d.overdue ? "bg-[#FDE6E2] text-[#B5321F]" : "bg-surface"}`}><b>{d.overdue}</b> en retard</span>
      </div>
      {d.urgent.length === 0 ? (
        <p className="rounded-2xl bg-surface p-4 text-sm text-ink-soft">
          Rien d'urgent. {d.open === 0 && <>Créez un projet du département « {d.department} » pour que ses tâches arrivent ici.</>}
        </p>
      ) : <ul className="divide-y divide-line">{d.urgent.map((t) => <TaskLine key={t.id} t={t} relance />)}</ul>}
    </Panel>
  );
}

const F = (n: number) => `${Math.round(n).toLocaleString("fr-FR")} F`;
type Fig = { label: string; value: (s: AppStats) => ReactNode; sub?: (s: AppStats) => ReactNode; alert?: (s: AppStats) => boolean };
const APP_FIGURES: Partial<Record<Role, Fig[]>> = {
  dg: [
    { label: "Salons qui ont travaillé", value: (s) => s.growth.pros_with_completed, sub: (s) => `${s.growth.pros_total} comptes créés` },
    { label: "Réservations payées (30 j)", value: (s) => s.reservations["30d"].paid, sub: (s) => `${s.reservations["30d"].completed} honorées` },
    { label: "Acomptes encaissés (30 j)", value: (s) => F(s.finance["30d"].deposits_fcfa), sub: (s) => `frais ${F(s.finance["30d"].fees_fcfa)}` },
    { label: "Litiges ouverts", value: (s) => s.operations.open_disputes, alert: (s) => s.operations.open_disputes > 0 },
  ],
  growth: [
    { label: "Comptes de coiffeuses créés", value: (s) => s.growth.pros_total, sub: (s) => `+${s.growth.new_pros_7d} en 7 jours` },
    { label: "Comptes non suspendus", value: (s) => s.growth.pros_active },
    { label: "Ont eu une réservation honorée", value: (s) => s.growth.pros_with_completed },
    { label: "Réservations payées (7 j)", value: (s) => s.reservations["7d"].paid, sub: (s) => `${s.reservations["30d"].paid} sur 30 j` },
  ],
  ops: [
    { label: "Litiges ouverts", value: (s) => s.operations.open_disputes, alert: (s) => s.operations.open_disputes > 0,
      sub: (s) => s.operations.oldest_dispute_days != null ? `le plus vieux : ${s.operations.oldest_dispute_days} j` : "aucun" },
    { label: "Retraits bloqués", value: (s) => s.withdrawals.blocked.count, sub: (s) => F(s.withdrawals.blocked.amount_fcfa), alert: (s) => s.withdrawals.blocked.count > 0 },
    { label: "Retraits en attente", value: (s) => s.withdrawals.pending.count, sub: (s) => F(s.withdrawals.pending.amount_fcfa) },
    { label: "Annulations (30 j)", value: (s) => s.reservations["30d"].cancelled },
  ],
  finance: [
    { label: "Acomptes encaissés (30 j)", value: (s) => F(s.finance["30d"].deposits_fcfa), sub: (s) => `${F(s.finance["7d"].deposits_fcfa)} sur 7 j` },
    { label: "Frais gardés (30 j)", value: (s) => F(s.finance["30d"].fees_fcfa), sub: (s) => `${F(s.finance["7d"].fees_fcfa)} sur 7 j` },
    { label: "Retraits en attente", value: (s) => F(s.withdrawals.pending.amount_fcfa), sub: (s) => `${s.withdrawals.pending.count} retraits` },
    { label: "Retraits bloqués", value: (s) => F(s.withdrawals.blocked.amount_fcfa), sub: (s) => `${s.withdrawals.blocked.count} retraits`, alert: (s) => s.withdrawals.blocked.count > 0 },
  ],
};

let statsPromise: Promise<AppStatsResponse> | null = null;
export function useAppStats() {
  const [r, setR] = useState<AppStatsResponse | null>(null);
  useEffect(() => {
    statsPromise ??= appStatsApi.get().finally(() => setTimeout(() => { statsPromise = null; }, 60_000));
    statsPromise.then(setR).catch(() => setR({ available: false }));
  }, []);
  return r;
}

function AppFigures({ role }: { role: Role }) {
  const figs = APP_FIGURES[role];
  const r = useAppStats();
  if (!figs) return null;
  const s = r?.available ? r.stats : undefined;
  return (
    <Panel title="Chiffres de l'app" action={s ? <span className="text-[11px] text-ink-muted">{r?.stale ? "dernier chiffre connu" : "en direct"}</span> : <SoonTag>Bientôt</SoonTag>}>
      <div className="grid grid-cols-2 gap-2">
        {figs.map((f) => (
          <Tile key={f.label} label={f.label} value={s ? f.value(s) : <span className="text-ink-muted">—</span>}
            tone={s && f.alert?.(s) ? "text-busy" : ""} sub={s && f.sub ? f.sub(s) : undefined} />
        ))}
      </div>
      {!s && <p className="mt-2 text-xs text-ink-muted">La route est prête chez Kodjo. Elle s'affichera dès que Kevin aura posé la clé et que Mohamed aura donné son feu vert pour la mettre en ligne.</p>}
    </Panel>
  );
}

function GrowthBlock({ space }: { space: Space }) {
  const agent = useMyAgent(space);
  const s = space.salons ?? {};
  const ask: RowAsk | null = agent && {
    id: agent.id, name: agent.name, label: "Message",
    texte: (t) => `${agent.name}, écris un message court et chaleureux pour « ${t.title} »` +
      (t.contact ? ` (contact : ${t.contact})` : "") + `, actuellement « ${t.stage} ». Objectif : l'amener à sa première réservation.`,
  };
  return (
    <Panel title="Salons à suivre" action={more("/suivi/salon")}>
      <div className="mb-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
        {Object.entries(s).map(([stage, n], i) => (
          <Tile key={stage} label={stage.charAt(0).toUpperCase() + stage.slice(1)} value={n} tone={i === 3 && n ? "text-[#18794A]" : ""} />
        ))}
      </div>
      <TrackList kind="salon" hideDone limit={6} ask={ask} />
    </Panel>
  );
}

function LaunchCard({ days }: { days: number }) {
  const r = useAppStats();
  const worked = r?.available && r.stats ? r.stats.growth.pros_with_completed : null;
  return (
    <Panel>
      <div className="flex items-center gap-4">
        <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-soft text-accent"><PartyPopper size={22} /></span>
        <div>
          <div className="text-sm text-ink-soft">Lancement public le 12 décembre</div>
          <div className="text-2xl font-semibold tracking-tight">{days > 0 ? `J − ${days}` : days === 0 ? "C'est aujourd'hui" : "Lancé"}</div>
        </div>
        <div className="ml-auto text-right">
          <div className="text-sm text-ink-soft">Objectif</div>
          <div className="text-2xl font-semibold tracking-tight">{worked != null ? `${worked} / ` : ""}300 <span className="text-sm font-normal text-ink-soft">pros</span></div>
          {worked != null && <div className="text-[11px] text-ink-muted">salons qui ont honoré une réservation</div>}
        </div>
      </div>
    </Panel>
  );
}

function SimpleTrack({ kind, title, to, space }: {
  kind: "echeance" | "depense"; title: string; to: string; space: Space;
}) {
  const agent = useMyAgent(space);
  const ask: RowAsk | null = agent && {
    id: agent.id, name: agent.name, label: kind === "echeance" ? "Préparer" : "Avis",
    texte: (t) => kind === "echeance"
      ? `${agent.name}, prépare « ${t.title} »` + (t.due_date ? ` (pour le ${t.due_date})` : "") +
        ` : ce qu'il faut faire, dans quel ordre, et ce qu'on risque si on la rate.`
      : `${agent.name}, ton avis sur cette dépense : « ${t.title} »` +
        (t.amount != null ? ` — ${t.amount.toLocaleString("fr-FR")} ${t.currency}` : "") +
        `. Est-ce justifié, et peut-on faire moins cher ?`,
  };
  return (
    <Panel title={title} action={more(to)}>
      <TrackList kind={kind} hideDone limit={5} ask={ask} />
    </Panel>
  );
}

function AiCost({ space }: { space: Space }) {
  if (!space.ai_cost) return null;
  return (
    <Panel>
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-soft text-blue"><Bot size={18} /></span>
        <div className="flex-1">
          <div className="text-sm text-ink-soft">Agents IA ce mois-ci</div>
          <div className="text-xl font-semibold">{space.ai_cost.month_usd.toLocaleString("fr-FR", { minimumFractionDigits: 2 })} $</div>
        </div>
        <div className="text-right text-xs text-ink-soft">{space.ai_cost.replies} réponses</div>
      </div>
    </Panel>
  );
}

/** Les blocs propres au poste, dans l'ordre où la personne en a besoin. */
export function RoleBlocks({ space }: { space: Space }) {
  const r = new Set(space.roles);
  const left: ReactNode[] = [];
  const right: ReactNode[] = [];
  if (space.to_vote) right.push(<VoteBlock key="vote" space={space} />);
  if (r.has("growth")) {
    left.push(<LaunchCard key="launch" days={space.launch_days ?? 0} />, <GrowthBlock key="salons" space={space} />);
  }
  if (r.has("dg") || r.has("coord")) left.push(<Departments key="depts" space={space} />);
  if (r.has("coord")) left.push(<WeekDue key="week" space={space} />);
  if (r.has("ops")) left.push(<SimpleTrack key="ech" kind="echeance" title="Échéances et contrats" to="/suivi/echeance" space={space} />);
  if (space.spend_pending) {
    (r.has("finance") ? left : right).push(<SimpleTrack key="dep" kind="depense" title={`Dépenses à valider${space.spend_pending.count ? ` (${space.spend_pending.count})` : ""}`} to="/suivi/depense" space={space} />);
  }
  for (const role of ["growth", "ops", "finance", "tech"] as Role[]) if (r.has(role)) left.push(<DeptTasks key={`t-${role}`} space={space} role={role} />);
  if (space.ai_cost) right.push(<AiCost key="ai" space={space} />);
  for (const role of ["dg", "growth", "ops", "finance"] as Role[]) if (r.has(role)) right.push(<AppFigures key={`f-${role}`} role={role} />);
  if (!left.length && !right.length) return null;
  return (
    <div className="grid gap-5 lg:grid-cols-[1.4fr_1fr]">
      <div className="space-y-5">{left}</div>
      <div className="space-y-5">{right}</div>
    </div>
  );
}

export function NoRole() {
  return (
    <Link to="/equipe" className="flex items-center gap-3 rounded-2xl border border-dashed border-line bg-white p-4 text-sm text-ink-soft hover:border-accent/40">
      <Store size={18} className="text-accent" /> Votre espace se remplit selon votre poste. Demandez à un responsable de vous placer dans l'organigramme.
      <Plus size={16} className="ml-auto" />
    </Link>
  );
}
