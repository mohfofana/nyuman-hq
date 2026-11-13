import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Check, Moon, Plus, Timer, X } from "lucide-react";
import { fmtMinutes, isoDay, timeApi, type TimeEntry, type TimeSuggestions } from "../lib/api";
import { useLive } from "../lib/live";
import { useSession } from "../lib/session";

export const DURATIONS = [30, 60, 90, 120, 180, 240];

export function dayTitle(day: string): string {
  if (day === isoDay()) return "Aujourd'hui";
  const y = new Date(); y.setDate(y.getDate() - 1);
  if (day === isoDay(y)) return "Hier";
  const s = new Date(day + "T12:00:00").toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "short" });
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/** Les saisies d'un jour + l'ajout rapide : choisir une tâche ou un projet, une durée, et c'est noté. */
export function useDay(day: string) {
  const { subscribe } = useLive();
  const [entries, setEntries] = useState<TimeEntry[] | null>(null);
  const [off, setOff] = useState(false);
  const load = useCallback(() => timeApi.me(day, day).then((r) => { setEntries(r.entries); setOff(r.days_off.includes(day)); }), [day]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => subscribe((ev) => { if (ev.type === "time.updated" && ev.day === day) load(); }), [day, load, subscribe]);
  return { entries, off, load };
}

export function DayEntry({ day, compact, onChange }: { day: string; compact?: boolean; onChange?: () => void }) {
  const { entries, off, load } = useDay(day);
  const [sug, setSug] = useState<TimeSuggestions | null>(null);
  const [pick, setPick] = useState<{ task_id?: string; project_id?: string; label: string } | null>(null);
  const [minutes, setMinutes] = useState<number | null>(null);
  const [note, setNote] = useState("");
  const [adding, setAdding] = useState(false);
  const [busy, setBusy] = useState(false);
  useEffect(() => { timeApi.suggestions(day).then(setSug); }, [day]);

  const done = () => { load(); onChange?.(); };
  const save = async () => {
    if (!pick || !minutes) return;
    setBusy(true);
    try {
      await timeApi.add({ day, task_id: pick.task_id, project_id: pick.project_id, minutes, note: note.trim() });
      setPick(null); setMinutes(null); setNote(""); setAdding(false);
      done();
    } finally { setBusy(false); }
  };

  if (entries === null) return <div className="h-16" />;
  const total = entries.reduce((n, e) => n + e.minutes, 0);
  const showForm = !off && (entries.length === 0 || adding);

  return (
    <div className="space-y-3">
      {entries.length > 0 && (
        <ul className="space-y-1.5">
          {entries.map((e) => (
            <li key={e.id} className="group flex items-center gap-2 rounded-xl bg-surface px-3 py-2 text-sm">
              <span>{e.project_icon}</span>
              <span className="min-w-0 flex-1 truncate">
                <span className="font-medium">{e.task_title ?? e.project_name}</span>
                {e.task_title && <span className="text-ink-muted"> · {e.project_name}</span>}
                {e.note && <span className="block truncate text-xs text-ink-soft">{e.note}</span>}
              </span>
              <span className="shrink-0 font-semibold tabular-nums">{fmtMinutes(e.minutes)}</span>
              <button onClick={async () => { await timeApi.remove(e.id); done(); }} aria-label="Retirer"
                className="rounded-md p-1 text-ink-muted opacity-60 hover:bg-white hover:text-busy group-hover:opacity-100"><X size={14} /></button>
            </li>
          ))}
          <li className="flex items-center justify-between px-1 text-xs text-ink-soft">
            <span className="flex items-center gap-1 text-online"><Check size={13} /> Noté</span>
            <span>Total <b className="text-ink">{fmtMinutes(total)}</b></span>
          </li>
        </ul>
      )}

      {off && (
        <div className="flex items-center justify-between rounded-xl bg-surface px-3 py-2 text-sm text-ink-soft">
          <span className="flex items-center gap-2"><Moon size={15} /> Pas travaillé ce jour-là</span>
          <button onClick={async () => { await timeApi.undoOff(day); done(); }} className="text-xs font-medium text-accent hover:underline">Annuler</button>
        </div>
      )}

      {showForm && sug && (
        <div className="space-y-3">
          <div>
            <p className="mb-1.5 text-xs font-medium text-ink-soft">Sur quoi ?</p>
            <div className="flex flex-wrap gap-1.5">
              {sug.tasks.map((t) => (
                <Chip key={t.id} on={pick?.task_id === t.id} onClick={() => setPick({ task_id: t.id, label: t.title })}>
                  {t.title}<span className="ml-1 text-[11px] opacity-60">{t.project_name}</span>
                </Chip>
              ))}
              {sug.projects.slice(0, compact ? 5 : 10).map((p) => (
                <Chip key={p.id} on={pick?.project_id === p.id} onClick={() => setPick({ project_id: p.id, label: p.name })}>
                  {p.icon} {p.name}
                </Chip>
              ))}
              {sug.tasks.length === 0 && sug.projects.length === 0 && (
                <span className="text-sm text-ink-muted">Aucun projet pour l'instant. <Link to="/projets" className="text-accent hover:underline">Créer un projet</Link></span>
              )}
            </div>
          </div>
          {pick && (
            <div>
              <p className="mb-1.5 text-xs font-medium text-ink-soft">Combien de temps, à peu près ?</p>
              <div className="flex flex-wrap gap-1.5">
                {DURATIONS.map((d) => <Chip key={d} on={minutes === d} onClick={() => setMinutes(d)}>{fmtMinutes(d)}</Chip>)}
              </div>
            </div>
          )}
          {pick && minutes && (
            <div className="flex gap-2">
              <input value={note} onChange={(e) => setNote(e.target.value)} maxLength={300} placeholder="Un mot (facultatif)"
                onKeyDown={(e) => { if (e.key === "Enter") save(); }}
                className="min-w-0 flex-1 rounded-xl border border-line bg-white px-3 py-2 text-sm outline-none focus:border-accent" />
              <button onClick={save} disabled={busy}
                className="shrink-0 rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-accent-hover disabled:opacity-50">Noter</button>
            </div>
          )}
          {entries.length === 0 && !pick && (
            <button onClick={async () => { await timeApi.off(day); done(); }}
              className="flex items-center gap-1.5 text-xs font-medium text-ink-soft hover:text-ink"><Moon size={13} /> Je n'ai pas travaillé ce jour-là</button>
          )}
          {adding && entries.length > 0 && (
            <button onClick={() => { setAdding(false); setPick(null); setMinutes(null); }} className="text-xs text-ink-soft hover:text-ink">Fermer</button>
          )}
        </div>
      )}

      {!off && entries.length > 0 && !adding && (
        <button onClick={() => setAdding(true)} className="flex items-center gap-1 text-xs font-medium text-accent hover:underline"><Plus size={13} /> Ajouter autre chose</button>
      )}
    </div>
  );
}

function Chip({ on, onClick, children }: { on: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick}
      className={`max-w-full truncate rounded-full border px-3 py-1.5 text-sm transition ${
        on ? "border-accent bg-accent text-white" : "border-line bg-white text-ink hover:border-accent/40 hover:bg-accent-soft"}`}>
      {children}
    </button>
  );
}

/** La carte que Maeve envoie le soir dans la discussion privée. */
export function TimeCard({ day }: { day: string }) {
  const { me } = useSession();
  if (!me || me.kind !== "human") {
    return <div className="my-1 inline-flex items-center gap-2 rounded-xl bg-surface px-3 py-2 text-sm text-ink-soft"><Timer size={15} /> Question du soir ({dayTitle(day).toLowerCase()})</div>;
  }
  return (
    <div className="my-1 max-w-md rounded-2xl border border-line bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-start gap-3">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-accent-soft text-accent"><Timer size={18} /></span>
        <div>
          <p className="text-sm font-semibold">{dayTitle(day)}, sur quoi avez-vous travaillé ?</p>
          <p className="text-xs text-ink-soft">10 secondes. C'est vous qui le dites : rien n'est mesuré.</p>
        </div>
      </div>
      <DayEntry day={day} compact />
      <Link to="/temps" className="mt-3 block text-xs font-medium text-ink-soft hover:text-accent">Voir ma semaine →</Link>
    </div>
  );
}
