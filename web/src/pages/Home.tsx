import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Bell, CalendarPlus, Check, FilePlus2, MessageSquarePlus, Pencil } from "lucide-react";
import { useSession } from "../lib/session";
import { useLive } from "../lib/live";
import { Avatar } from "../components/Avatar";
import { Panel, PresencePill, SoonTag } from "../components/ui";
import { presenceLabel, presenceOf } from "../lib/presence";
import { ActivityRow, NotifButton, useActivity } from "./Activity";
import { useEffect } from "react";
import { meetings, spaceApi, type Meeting, type Space } from "../lib/api";
import { MyPostCard, NoRole, RoleBlocks } from "./space/RoleBlocks";
import { MeetingCard } from "../components/MeetingCard";
import { useTasks } from "./projects/useProjects";
import { dueLabel } from "./projects/meta";

function greeting() {
  const h = new Date().getHours();
  return h < 12 ? "Bonjour" : h < 18 ? "Bon après-midi" : "Bonsoir";
}

function Upcoming() {
  const { subscribe } = useLive();
  const [list, setList] = useState<Meeting[] | null>(null);
  useEffect(() => { meetings.upcoming().then(setList); }, []);
  useEffect(() => subscribe((ev) => { if (String(ev.type).startsWith("meeting.")) meetings.upcoming().then(setList); }), [subscribe]);
  return (
    <Panel title="Mes prochaines réunions" action={<Link to="/agenda" className="inline-flex items-center gap-1 text-sm font-medium text-accent hover:underline">Agenda <ArrowRight size={14} /></Link>}>
      {list && list.length === 0 && (
        <Link to="/agenda?nouvelle=1" className="flex items-center gap-3 rounded-2xl bg-surface p-4 text-sm text-ink-soft hover:bg-surface-2">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-soft text-blue"><CalendarPlus size={18} /></span>
          Aucune réunion prévue. Planifier une réunion →
        </Link>
      )}
      <div className="space-y-2">{list?.slice(0, 3).map((m) => <MeetingCard key={m.id} id={m.id} initial={m} />)}</div>
    </Panel>
  );
}

function MyTasksPanel() {
  const { me } = useSession();
  const { tasks, patch } = useTasks(me ? { assignee_id: me.id, status: "todo,doing,review" } : null);
  if (!tasks) return null;
  const sorted = [...tasks].sort((a, b) => (a.due_date ?? "9999").localeCompare(b.due_date ?? "9999"));
  return (
    <Panel title="Mes tâches" action={<Link to="/projets" className="inline-flex items-center gap-1 text-sm font-medium text-accent hover:underline">Tout voir <ArrowRight size={14} /></Link>}>
      {!sorted.length && <p className="rounded-2xl bg-surface p-4 text-sm text-ink-soft">Rien en attente. Les tâches qu'on vous confie arriveront ici.</p>}
      <ul className="divide-y divide-line">
        {sorted.slice(0, 5).map((t) => {
          const due = dueLabel(t);
          return (
            <li key={t.id} className="flex items-center gap-3 py-2.5">
              <button onClick={() => patch(t.id, { status: "done" })} aria-label="Terminer" className="h-5 w-5 shrink-0 rounded-full border-2 border-ink-muted/40 transition hover:border-online hover:bg-[#E3F6EA]" />
              <Link to={`/projets/${t.project_id}`} className="min-w-0 flex-1 truncate text-sm font-medium hover:text-accent">{t.title}</Link>
              {due && <span className={`text-xs ${due.tone}`}>{due.text}</span>}
            </li>
          );
        })}
      </ul>
    </Panel>
  );
}

function TodayCard() {
  const { me, updateMe } = useSession();
  const [editing, setEditing] = useState(!me?.now_doing);
  const [value, setValue] = useState(me?.now_doing ?? "");
  if (!me) return null;
  const save = async () => { await updateMe({ now_doing: value.trim() }); setEditing(false); };
  return (
    <div className="mt-6 rounded-2xl bg-white/80 p-4 shadow-sm ring-1 ring-white backdrop-blur-sm">
      <div className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Ce que je fais aujourd'hui</div>
      {editing ? (
        <form className="mt-2 flex gap-2" onSubmit={(e) => { e.preventDefault(); save(); }}>
          <input autoFocus value={value} onChange={(e) => setValue(e.target.value)} placeholder="Ex. : relire le contrat Jèko"
            className="min-w-0 flex-1 rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink outline-none placeholder:text-ink-muted focus:border-accent" />
          <button className="inline-flex items-center gap-1 rounded-xl bg-accent px-3 text-sm font-semibold text-white shadow-sm shadow-accent/30 hover:bg-accent-hover">
            <Check size={16} /> OK
          </button>
        </form>
      ) : (
        <button onClick={() => setEditing(true)} className="group mt-1 flex items-center gap-2 text-left text-lg font-medium">
          {me.now_doing}
          <Pencil size={14} className="text-ink-muted group-hover:text-accent" />
        </button>
      )}
      <div className="mt-2 text-xs text-ink-muted">Visible sur votre fiche par toute l'équipe.</div>
    </div>
  );
}

const SHORTCUTS = [
  { icon: MessageSquarePlus, label: "Ouvrir les discussions", to: "/discussions", tone: "bg-accent-soft text-accent", ready: true },
  { icon: CalendarPlus, label: "Planifier une réunion", to: "/agenda?nouvelle=1", tone: "bg-blue-soft text-blue", ready: true },
  { icon: FilePlus2, label: "Ouvrir les projets", to: "/projets", tone: "bg-sun-soft text-[#9A6B00]", ready: true },
];

function useSpace() {
  const { subscribe } = useLive();
  const [space, setSpace] = useState<Space | null>(null);
  useEffect(() => { spaceApi.get().then(setSpace); }, []);
  useEffect(() => subscribe((ev) => {
    if (["proposal.updated", "track.updated", "task.updated", "task.assigned", "project.updated", "time.updated"].includes(ev.type)) spaceApi.get().then(setSpace);
  }), [subscribe]);
  return space;
}

export function Home() {
  const { me, members } = useSession();
  useLive();
  const activity = useActivity();
  const space = useSpace();
  if (!me) return null;
  const date = new Date().toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" });
  const others = members.filter((m) => m.id !== me.id);

  return (
    <div className="mx-auto max-w-6xl space-y-5 px-4 py-6 sm:px-8 sm:py-8">
      <section className="relative overflow-hidden rounded-[28px] bg-gradient-to-br from-[#FFF6EC] via-[#FDEBD8] to-[#FFE3BD] p-6 ring-1 ring-[#F5DCC0] sm:p-8">
        <span className="pointer-events-none absolute -right-16 -top-20 h-64 w-64 rounded-full bg-white/50" />
        <span className="pointer-events-none absolute -bottom-24 right-24 h-56 w-56 rounded-full bg-sun/30" />
        <div className="relative grid gap-6 lg:grid-cols-[1.4fr_1fr] lg:items-end">
          <div>
            <div className="text-sm font-medium text-accent">{date.charAt(0).toUpperCase() + date.slice(1)}</div>
            <h1 className="mt-1 text-3xl font-semibold tracking-tight sm:text-4xl">{greeting()}, {me.name.split(" ")[0]} 👋</h1>
            <div className="mt-3"><PresencePill p={presenceOf(me, me)} /></div>
            <TodayCard />
          </div>
          {space ? <MyPostCard space={space} /> : <div />}
        </div>
      </section>

      {space && (space.roles.length || space.to_vote ? <RoleBlocks space={space} /> : me.kind === "human" && <NoRole />)}

      <div className="grid gap-5 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-5">
        <MyTasksPanel />
        <Panel title="L'équipe en ce moment" action={<Link to="/equipe" className="inline-flex items-center gap-1 text-sm font-medium text-accent hover:underline">Tout voir <ArrowRight size={14} /></Link>}>
          <ul className="divide-y divide-line">
            {others.map((m) => (
              <li key={m.id} className="flex items-center gap-3 py-2.5">
                <Avatar member={m} presence={presenceOf(m, me)} size="sm" />
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium">{m.name} <span className="hidden font-normal text-ink-muted sm:inline">· {m.title}</span></div>
                  <div className={`truncate text-xs ${m.now_doing ? "text-ink-soft" : "text-ink-muted"}`}>{m.now_doing || "Rien d'indiqué"}</div>
                </div>
                <PresencePill p={presenceOf(m, me)} label={presenceLabel(m, presenceOf(m, me))} />
              </li>
            ))}
          </ul>
        </Panel>
        </div>

        <div className="space-y-5">
          <Upcoming />
          <Panel title="Raccourcis">
            <div className="grid gap-2">
              {SHORTCUTS.map(({ icon: Icon, label, to, tone, ready }: any) => (
                <Link key={label} to={to} className="group flex items-center gap-3 rounded-2xl border border-line px-3 py-2.5 transition hover:border-accent/40 hover:bg-surface">
                  <span className={`flex h-9 w-9 items-center justify-center rounded-xl ${tone}`}><Icon size={18} /></span>
                  <span className="flex-1 text-sm font-medium">{label}</span>
                  {!ready && <SoonTag />}
                </Link>
              ))}
            </div>
          </Panel>
          <Panel title="Activité" action={<Link to="/activite" className="inline-flex items-center gap-1 text-sm font-medium text-accent hover:underline">Tout voir <ArrowRight size={14} /></Link>}>
            <NotifButton />
            {activity && activity.length > 0 ? (
              <div className="-mx-2 mt-1">{activity.slice(0, 4).map((it) => <ActivityRow key={it.message.id} item={it} members={members} />)}</div>
            ) : (
              <div className="mt-2 flex items-center gap-3 rounded-2xl bg-surface p-4">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-sun-soft text-[#9A6B00]"><Bell size={18} /></span>
                <p className="text-sm text-ink-soft">Vos mentions et réponses apparaîtront ici.</p>
              </div>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
