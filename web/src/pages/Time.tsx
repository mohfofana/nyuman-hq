import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { AlertTriangle, ChevronLeft, ChevronRight, Lock, Moon, Pencil, Timer } from "lucide-react";
import { api, fmtMinutes, isoDay, projectsApi, timeApi, type MyTime, type TeamTime } from "../lib/api";
import { useLive } from "../lib/live";
import { useSession } from "../lib/session";
import { Avatar } from "../components/Avatar";
import { DayEntry, dayTitle } from "../components/TimeCard";

const WEEKDAYS = ["L", "M", "M", "J", "V", "S", "D"];

function monday(offset: number): Date {
  const d = new Date();
  d.setHours(12, 0, 0, 0);
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7) + offset * 7);
  return d;
}

export function TimePage() {
  const { me } = useSession();
  const [params, setParams] = useSearchParams();
  const tab = params.get("vue") === "equipe" ? "team" : "me";
  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:px-8">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold"><Timer className="text-accent" size={24} /> Temps</h1>
          <p className="mt-1 text-sm text-ink-soft">Chacun dit lui-même où est passé son temps. Personne ne voit les heures de connexion.</p>
        </div>
        <div className="flex rounded-xl bg-surface-2 p-1 text-sm font-medium">
          {([["me", "Ma semaine"], ["team", me?.is_head ? "Équipe et projets" : "Projets"]] as const).map(([k, label]) => (
            <button key={k} onClick={() => setParams(k === "team" ? { vue: "equipe" } : {})}
              className={`rounded-lg px-3.5 py-1.5 transition ${tab === k ? "bg-white text-ink shadow-sm" : "text-ink-soft hover:text-ink"}`}>{label}</button>
          ))}
        </div>
      </div>
      {tab === "me" ? <MyWeek /> : <TeamView />}
    </div>
  );
}

function MyWeek() {
  const { me } = useSession();
  const { subscribe } = useLive();
  const [offset, setOffset] = useState(0);
  const start = useMemo(() => monday(offset), [offset]);
  const days = useMemo(() => Array.from({ length: 7 }, (_, i) => { const d = new Date(start); d.setDate(d.getDate() + i); return isoDay(d); }), [start]);
  const today = isoDay();
  const [sel, setSel] = useState(today);
  const [data, setData] = useState<MyTime | null>(null);
  const load = useCallback(() => timeApi.me(days[0], days[6] > today ? today : days[6]).then(setData), [days, today]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => subscribe((ev) => { if (ev.type === "time.updated") load(); }), [load, subscribe]);
  useEffect(() => { setSel(days.includes(today) ? today : days[4]); }, [days, today]);

  const perDay = (d: string) => data?.entries.filter((e) => e.day === d).reduce((n, e) => n + e.minutes, 0) ?? 0;
  const total = data?.entries.reduce((n, e) => n + e.minutes, 0) ?? 0;
  const byProject = Object.values((data?.entries ?? []).reduce<Record<string, { name: string; icon: string; min: number }>>((acc, e) => {
    acc[e.project_id] ??= { name: e.project_name, icon: e.project_icon, min: 0 };
    acc[e.project_id].min += e.minutes;
    return acc;
  }, {})).sort((a, b) => b.min - a.min);
  const workDays = (me?.work_days ?? "").split(",");

  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_300px]">
      <section className="rounded-2xl border border-line bg-white p-4 shadow-sm sm:p-5">
        <div className="mb-4 flex items-center justify-between">
          <button onClick={() => setOffset(offset - 1)} className="rounded-lg p-1.5 text-ink-soft hover:bg-surface" aria-label="Semaine d'avant"><ChevronLeft size={18} /></button>
          <span className="text-sm font-semibold">
            {offset === 0 ? "Cette semaine" : offset === -1 ? "La semaine dernière" : `Semaine du ${new Date(days[0] + "T12:00").toLocaleDateString("fr-FR", { day: "numeric", month: "long" })}`}
          </span>
          <button onClick={() => setOffset(offset + 1)} disabled={offset >= 0} className="rounded-lg p-1.5 text-ink-soft hover:bg-surface disabled:opacity-30" aria-label="Semaine d'après"><ChevronRight size={18} /></button>
        </div>
        <div className="mb-5 grid grid-cols-7 gap-1.5">
          {days.map((d, i) => {
            const future = d > today, min = perDay(d), off = data?.days_off.includes(d), worked = workDays.includes(String(i + 1));
            return (
              <button key={d} disabled={future} onClick={() => setSel(d)}
                className={`flex flex-col items-center gap-0.5 rounded-xl border py-2 text-xs transition disabled:opacity-35 ${
                  sel === d ? "border-accent bg-accent-soft" : "border-transparent hover:bg-surface"}`}>
                <span className={`font-medium ${worked ? "text-ink" : "text-ink-muted"}`}>{WEEKDAYS[i]}</span>
                <span className={`text-base font-semibold ${d === today ? "text-accent" : ""}`}>{new Date(d + "T12:00").getDate()}</span>
                <span className="h-4 text-[11px] text-ink-soft">{off ? <Moon size={11} className="mt-0.5" /> : min ? fmtMinutes(min) : future ? "" : "·"}</span>
              </button>
            );
          })}
        </div>
        <h2 className="mb-3 text-sm font-semibold">{dayTitle(sel)}</h2>
        <DayEntry key={sel} day={sel} onChange={load} />
      </section>

      <aside className="space-y-5">
        <section className="rounded-2xl border border-line bg-white p-4 shadow-sm">
          <div className="mb-3 flex items-baseline justify-between">
            <h2 className="text-sm font-semibold">Ma semaine</h2>
            <span className="text-lg font-semibold">{fmtMinutes(total)}</span>
          </div>
          {byProject.length === 0 ? <p className="text-sm text-ink-muted">Rien de noté pour l'instant.</p> : (
            <ul className="space-y-2.5">
              {byProject.map((p) => (
                <li key={p.name} className="text-sm">
                  <div className="mb-1 flex justify-between gap-2"><span className="truncate">{p.icon} {p.name}</span><span className="shrink-0 text-ink-soft">{fmtMinutes(p.min)}</span></div>
                  <div className="h-1.5 rounded-full bg-surface-2"><div className="h-full rounded-full bg-accent" style={{ width: `${Math.max(4, (p.min / total) * 100)}%` }} /></div>
                </li>
              ))}
            </ul>
          )}
          <p className="mt-3 flex items-center gap-1.5 text-[11px] text-ink-muted"><Lock size={11} /> Le détail de vos journées n'est visible que par vous et les responsables.</p>
        </section>
        <AskSettings />
      </aside>
    </div>
  );
}

function AskSettings() {
  const { me, patchMember } = useSession();
  if (!me) return null;
  const update = async (d: { work_days?: string; ask_hour?: number | null }) => patchMember(await api.updateMe(d as never));
  const days = new Set((me.work_days ?? "").split(",").filter(Boolean));
  const toggle = (n: string) => {
    const next = new Set(days);
    next.has(n) ? next.delete(n) : next.add(n);
    update({ work_days: [...next].sort().join(",") });
  };
  return (
    <section className="rounded-2xl border border-line bg-white p-4 shadow-sm">
      <h2 className="text-sm font-semibold">La question du soir</h2>
      <p className="mb-3 mt-0.5 text-xs text-ink-soft">Maeve vous demande « sur quoi ? » en message privé, seulement les jours où vous travaillez.</p>
      <p className="mb-1.5 text-xs font-medium text-ink-soft">Mes jours</p>
      <div className="mb-3 flex gap-1">
        {WEEKDAYS.map((w, i) => {
          const on = days.has(String(i + 1));
          return <button key={i} onClick={() => toggle(String(i + 1))} aria-pressed={on}
            className={`h-8 w-8 rounded-full text-xs font-semibold transition ${on ? "bg-accent text-white" : "bg-surface text-ink-soft hover:bg-surface-2"}`}>{w}</button>;
        })}
      </div>
      <label className="flex items-center justify-between gap-2 text-xs font-medium text-ink-soft">
        À quelle heure
        <select value={me.ask_hour ?? ""} onChange={(e) => update({ ask_hour: e.target.value === "" ? null : Number(e.target.value) })}
          className="rounded-lg border border-line bg-white px-2 py-1.5 text-sm text-ink outline-none focus:border-accent">
          {[17, 18, 19, 20, 21, 22].map((h) => <option key={h} value={h}>{h} h</option>)}
          <option value="">Jamais</option>
        </select>
      </label>
    </section>
  );
}

function TeamView() {
  const { me, members } = useSession();
  const { subscribe } = useLive();
  const [days, setDays] = useState(7);
  const [data, setData] = useState<TeamTime | null>(null);
  const load = useCallback(() => timeApi.team(days).then(setData), [days]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => subscribe((ev) => { if (ev.type === "time.updated" || ev.type === "project.updated") load(); }), [load, subscribe]);
  if (!data) return null;
  const projects = [...data.projects].sort((a, b) => b.minutes - a.minutes || b.total_minutes - a.total_minutes);
  const maxMin = Math.max(1, ...projects.map((p) => p.minutes));
  const name = (pid: string) => data.projects.find((p) => p.id === pid);

  return (
    <div className="space-y-5">
      <div className="flex gap-1.5">
        {[[7, "7 derniers jours"], [30, "30 derniers jours"]].map(([n, l]) => (
          <button key={n} onClick={() => setDays(n as number)}
            className={`rounded-full border px-3 py-1 text-sm ${days === n ? "border-accent bg-accent-soft text-accent" : "border-line bg-white text-ink-soft hover:text-ink"}`}>{l}</button>
        ))}
      </div>

      <section className="rounded-2xl border border-line bg-white shadow-sm">
        <h2 className="border-b border-line px-5 py-3 text-sm font-semibold">Par projet</h2>
        {projects.length === 0 && <p className="px-5 py-6 text-sm text-ink-muted">Aucun projet.</p>}
        <ul className="divide-y divide-line">
          {projects.map((p) => (
            <li key={p.id} className="grid items-center gap-x-4 gap-y-2 px-5 py-3 sm:grid-cols-[minmax(0,1fr)_170px_280px]">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{p.icon} {p.name}
                  {p.inactive && <span className="ml-2 rounded-full bg-surface-2 px-2 py-0.5 text-[11px] font-medium text-ink-soft">Plus rien depuis 14 j</span>}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-1.5 flex-1 rounded-full bg-surface-2"><div className="h-full rounded-full bg-accent" style={{ width: `${(p.minutes / maxMin) * 100}%` }} /></div>
                <span className={`w-14 text-right text-sm tabular-nums ${p.minutes ? "font-semibold" : "text-ink-muted"}`}>{p.minutes ? fmtMinutes(p.minutes) : "—"}</span>
              </div>
              <Budget p={p} canEdit={!!me && (me.is_head || p.owner_id === me.id)} onSaved={load} />
            </li>
          ))}
        </ul>
      </section>

      {data.people && (
        <section className="rounded-2xl border border-line bg-white shadow-sm">
          <div className="flex items-baseline justify-between border-b border-line px-5 py-3">
            <h2 className="text-sm font-semibold">Par personne</h2>
            <span className="flex items-center gap-1 text-[11px] text-ink-muted"><Lock size={11} /> Visible par les responsables seulement</span>
          </div>
          {data.people.length === 0 && <p className="px-5 py-6 text-sm text-ink-muted">Personne n'a encore rien noté sur cette période.</p>}
          <ul className="divide-y divide-line">
            {data.people.map((row) => {
              const m = members.find((x) => x.id === row.member_id);
              return (
                <li key={row.member_id} className="flex flex-wrap items-center gap-3 px-5 py-3">
                  {m && <Avatar member={m} size="sm" />}
                  <span className="w-40 truncate text-sm font-medium">{m?.name ?? row.member_id}</span>
                  <span className="w-16 text-sm font-semibold tabular-nums">{fmtMinutes(row.minutes)}</span>
                  <span className="flex min-w-0 flex-1 flex-wrap gap-1.5">
                    {Object.entries(row.projects).sort((a, b) => b[1] - a[1]).map(([pid, min]) => (
                      <span key={pid} className="rounded-full bg-surface px-2.5 py-0.5 text-xs text-ink-soft">{name(pid)?.icon} {name(pid)?.name ?? "?"} · {fmtMinutes(min)}</span>
                    ))}
                  </span>
                </li>
              );
            })}
          </ul>
        </section>
      )}
    </div>
  );
}

function Budget({ p, canEdit, onSaved }: { p: TeamTime["projects"][number]; canEdit: boolean; onSaved: () => void }) {
  const [edit, setEdit] = useState(false);
  const [val, setVal] = useState(String(p.hours_budget ?? ""));
  const save = async () => {
    await projectsApi.update(p.id, { hours_budget: val.trim() === "" ? null : Math.max(0, Number(val)) });
    setEdit(false); onSaved();
  };
  if (edit) return (
    <form onSubmit={(e) => { e.preventDefault(); save(); }} className="flex items-center gap-1.5 text-sm">
      <input autoFocus type="number" min={0} value={val} onChange={(e) => setVal(e.target.value)} placeholder="ex. 40"
        className="w-20 rounded-lg border border-line px-2 py-1 outline-none focus:border-accent" /> h au total
      <button className="ml-auto rounded-lg bg-accent px-2.5 py-1 text-xs font-semibold text-white">OK</button>
    </form>
  );
  if (!p.hours_budget) return (
    <div className="flex items-center justify-between gap-2 text-xs text-ink-muted">
      <span className="truncate">{p.total_minutes ? `${fmtMinutes(p.total_minutes)} au total · ` : ""}sans budget</span>
      {canEdit && <button onClick={() => setEdit(true)} className="shrink-0 font-medium text-accent hover:underline">Fixer un budget</button>}
    </div>
  );
  const pct = p.budget_pct ?? 0;
  const tone = pct >= 100 ? "bg-busy" : pct >= 80 ? "bg-away" : "bg-online";
  return (
    <div className="text-xs">
      <div className="mb-1 flex items-center justify-between">
        <span className={pct >= 80 ? "flex items-center gap-1 font-medium text-ink" : "text-ink-soft"}>
          {pct >= 80 && <AlertTriangle size={12} className={pct >= 100 ? "text-busy" : "text-away"} />}
          {fmtMinutes(p.total_minutes)} sur {p.hours_budget} h ({pct} %)
        </span>
        {canEdit && <button onClick={() => setEdit(true)} aria-label="Modifier le budget" className="text-ink-muted hover:text-accent"><Pencil size={12} /></button>}
      </div>
      <div className="h-1.5 rounded-full bg-surface-2"><div className={`h-full rounded-full ${tone}`} style={{ width: `${Math.min(100, pct)}%` }} /></div>
    </div>
  );
}
