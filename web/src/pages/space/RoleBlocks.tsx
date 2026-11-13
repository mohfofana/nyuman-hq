import type { ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AlertTriangle, ArrowRight, Bot, Gavel, MessageCircle, PartyPopper, Plus, Store } from "lucide-react";
import { chat, fmtMinutes, type MiniTask, type Role, type Space } from "../../lib/api";
import { useSession } from "../../lib/session";
import { Avatar } from "../../components/Avatar";
import { Panel, SoonTag } from "../../components/ui";
import { TrackList } from "../../components/TrackList";

export const ROLE_LABEL: Record<Role, string> = {
  dg: "Direction générale", coord: "Coordination", growth: "Croissance", ops: "Opérations et juridique", finance: "Finance", tech: "Produit et technique",
};

const more = (to: string, label = "Tout voir") => (
  <Link to={to} className="inline-flex items-center gap-1 text-sm font-medium text-accent hover:underline">{label} <ArrowRight size={14} /></Link>
);

/** Le haut de l'espace : mon poste et l'agent qui m'appuie. */
export function MyPostCard({ space }: { space: Space }) {
  const { members } = useSession();
  const navigate = useNavigate();
  const agents = space.agents.map((id) => members.find((m) => m.id === id)).filter(Boolean) as typeof members;
  const ask = async (id: string) => { const r = await chat.openDm([id]); navigate(`/discussions/${r.id}`); };
  return (
    <div className="rounded-2xl bg-white p-5 text-ink shadow-[0_16px_32px_-16px_rgba(188,96,13,0.35)]">
      <div className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Mon poste</div>
      {space.positions.length ? (
        space.positions.map((p) => <div key={p.id} className="mt-1 text-lg font-semibold leading-snug">{p.title}</div>)
      ) : (
        <p className="mt-1 text-sm text-ink-soft">Pas encore de poste dans l'organigramme. <Link to="/equipe" className="text-accent hover:underline">Voir l'équipe</Link></p>
      )}
      {agents.length > 0 && (
        <div className="mt-4 space-y-2">
          {agents.map((a) => (
            <button key={a.id} onClick={() => ask(a.id)}
              className="flex w-full items-center gap-3 rounded-xl border border-line px-3 py-2 text-left transition hover:border-accent/40 hover:bg-accent-soft/40">
              <Avatar member={a} size="sm" />
              <span className="min-w-0 flex-1">
                <span className="block text-sm font-semibold">Demander à {a.name}</span>
                <span className="block truncate text-xs text-ink-soft">{a.title}</span>
              </span>
              <MessageCircle size={16} className="text-accent" />
            </button>
          ))}
        </div>
      )}
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

function TaskLine({ t }: { t: MiniTask }) {
  const { members } = useSession();
  const who = members.find((m) => m.id === t.assignee_id);
  const today = new Date().toISOString().slice(0, 10);
  const late = t.due_date && t.due_date < today;
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
  return (
    <Panel title="Où en sont les départements" action={more("/projets", "Projets")}>
      <div className="grid gap-2 sm:grid-cols-2">
        {space.departments!.map((d) => (
          <div key={d.role} className="rounded-2xl bg-surface px-3.5 py-3">
            <div className="text-sm font-semibold">{d.department}</div>
            <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-xs text-ink-soft">
              <span><b className="text-ink">{d.open}</b> en cours</span>
              <span className={d.overdue ? "font-medium text-busy" : ""}><b>{d.overdue}</b> en retard</span>
              <span className="text-[#18794A]"><b>{d.done_week}</b> finies (7 j)</span>
            </div>
          </div>
        ))}
      </div>
      {space.budget_alerts && space.budget_alerts.length > 0 && (
        <ul className="mt-3 space-y-1.5">
          {space.budget_alerts.map((b) => (
            <li key={b.id} className="flex items-center gap-2 rounded-xl bg-[#FFF8E5] px-3 py-2 text-sm">
              <AlertTriangle size={14} className={b.pct >= 100 ? "text-busy" : "text-away"} />
              <span className="flex-1 truncate">{b.icon} {b.name}</span>
              <span className="text-xs font-medium">{fmtMinutes(b.used_minutes)} sur {b.hours_budget} h ({b.pct} %)</span>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

function WeekDue({ space }: { space: Space }) {
  const list = space.week_due ?? [];
  return (
    <Panel title="Échéances des 7 prochains jours (toute l'équipe)" action={more("/projets")}>
      {list.length === 0 ? <p className="rounded-2xl bg-surface p-4 text-sm text-ink-soft">Aucune échéance cette semaine.</p>
        : <ul className="divide-y divide-line">{list.slice(0, 8).map((t) => <TaskLine key={t.id} t={t} />)}</ul>}
      {space.quiet_projects && space.quiet_projects.length > 0 && (
        <p className="mt-3 rounded-xl bg-surface px-3 py-2 text-xs text-ink-soft">
          Rien n'a bougé depuis 14 jours : {space.quiet_projects.map((p) => `${p.icon} ${p.name}`).join(", ")}.
        </p>
      )}
    </Panel>
  );
}

function DeptTasks({ space, role }: { space: Space; role: Role }) {
  const d = space.dept?.[role];
  if (!d) return null;
  return (
    <Panel title={`Tâches · ${d.department}`} action={more("/projets")}>
      <div className="mb-3 flex gap-2 text-xs">
        <span className="rounded-full bg-surface px-2.5 py-1"><b>{d.open}</b> en cours</span>
        <span className={`rounded-full px-2.5 py-1 ${d.overdue ? "bg-[#FDE6E2] text-[#B5321F]" : "bg-surface"}`}><b>{d.overdue}</b> en retard</span>
      </div>
      {d.urgent.length === 0 ? (
        <p className="rounded-2xl bg-surface p-4 text-sm text-ink-soft">
          Rien d'urgent. {d.open === 0 && <>Créez un projet du département « {d.department} » pour que ses tâches arrivent ici.</>}
        </p>
      ) : <ul className="divide-y divide-line">{d.urgent.map((t) => <TaskLine key={t.id} t={t} />)}</ul>}
    </Panel>
  );
}

const APP_FIGURES: Partial<Record<Role, string[]>> = {
  dg: ["Pros actives", "Réservations (30 j)", "Acomptes encaissés (30 j)", "Litiges ouverts"],
  growth: ["Pros inscrites", "Pros actives", "Avec une 1re réservation", "Nouvelles (7 j)"],
  ops: ["Litiges ouverts", "Retraits bloqués", "Retraits en attente", "Plus vieux litige"],
  finance: ["Acomptes encaissés (30 j)", "Frais (30 j)", "Retraits en attente", "Retraits bloqués"],
  tech: ["Version en ligne", "Dernier déploiement"],
};

function AppFigures({ role }: { role: Role }) {
  const names = APP_FIGURES[role];
  if (!names) return null;
  return (
    <Panel title="Chiffres de l'app" action={<SoonTag>Bientôt</SoonTag>}>
      <div className="grid grid-cols-2 gap-2">
        {names.map((n) => <Tile key={n} label={n} value={<span className="text-ink-muted">—</span>} />)}
      </div>
      <p className="mt-2 text-xs text-ink-muted">En direct de l'app dès que Kodjo aura ouvert l'accès en lecture seule (demandé le 13/11).</p>
    </Panel>
  );
}

function GrowthBlock({ space }: { space: Space }) {
  const s = space.salons ?? {};
  return (
    <Panel title="Salons à suivre" action={more("/suivi/salon")}>
      <div className="mb-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
        {Object.entries(s).map(([stage, n], i) => (
          <Tile key={stage} label={stage.charAt(0).toUpperCase() + stage.slice(1)} value={n} tone={i === 3 && n ? "text-[#18794A]" : ""} />
        ))}
      </div>
      <TrackList kind="salon" hideDone limit={6} />
    </Panel>
  );
}

function LaunchCard({ days }: { days: number }) {
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
          <div className="text-2xl font-semibold tracking-tight">300 <span className="text-sm font-normal text-ink-soft">pros</span></div>
        </div>
      </div>
    </Panel>
  );
}

function SimpleTrack({ kind, title, to }: { kind: "echeance" | "depense"; title: string; to: string }) {
  return (
    <Panel title={title} action={more(to)}>
      <TrackList kind={kind} hideDone limit={5} />
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
  if (r.has("ops")) left.push(<SimpleTrack key="ech" kind="echeance" title="Échéances et contrats" to="/suivi/echeance" />);
  if (space.spend_pending) {
    (r.has("finance") ? left : right).push(<SimpleTrack key="dep" kind="depense" title={`Dépenses à valider${space.spend_pending.count ? ` (${space.spend_pending.count})` : ""}`} to="/suivi/depense" />);
  }
  for (const role of ["growth", "ops", "finance", "tech"] as Role[]) if (r.has(role)) left.push(<DeptTasks key={`t-${role}`} space={space} role={role} />);
  if (space.ai_cost) right.push(<AiCost key="ai" space={space} />);
  for (const role of ["dg", "growth", "ops", "finance", "tech"] as Role[]) if (r.has(role)) right.push(<AppFigures key={`f-${role}`} role={role} />);
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
