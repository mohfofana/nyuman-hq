import { useMemo, useState } from "react";
import { Check, ChevronLeft, ChevronRight } from "lucide-react";
import type { Task, TaskStatus } from "../../lib/api";
import { useSession } from "../../lib/session";
import { Avatar } from "../../components/Avatar";
import { PRIORITY, STATUS, STATUS_ORDER, dueLabel, isoDay } from "./meta";
import { AssigneeSelect, DueInput, NewTask, StatusSelect } from "./TaskParts";

type Props = { tasks: Task[]; projectId: string; onOpen: (t: Task) => void; onPatch: (id: string, d: Partial<Task>) => void };

function DoneBox({ t, onPatch }: { t: Task; onPatch: Props["onPatch"] }) {
  const done = t.status === "done";
  return (
    <button onClick={(e) => { e.stopPropagation(); onPatch(t.id, { status: done ? "todo" : "done" }); }} aria-label={done ? "Rouvrir" : "Terminer"}
      className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition ${done ? "border-online bg-online text-white" : "border-ink-muted/40 hover:border-online hover:bg-[#E3F6EA]"}`}>
      {done && <Check size={12} strokeWidth={3} />}
    </button>
  );
}

/** Vue tableau : une ligne par tâche, tout se modifie sur place. */
export function TaskTable({ tasks, projectId, onOpen, onPatch }: Props) {
  const [showDone, setShowDone] = useState(false);
  const open = tasks.filter((t) => t.status !== "done");
  const done = tasks.filter((t) => t.status === "done");
  const rows = showDone ? [...open, ...done] : open;
  return (
    <div className="overflow-hidden rounded-3xl border border-line bg-white shadow-sm">
      <div className="hidden grid-cols-[1fr_130px_150px_120px_90px] gap-3 border-b border-line bg-surface/60 px-5 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-ink-muted md:grid">
        <span>Tâche</span><span>Statut</span><span>Responsable</span><span>Échéance</span><span>Priorité</span>
      </div>
      {rows.map((t) => {
        const P = PRIORITY[t.priority];
        return (
          <div key={t.id} onClick={() => onOpen(t)}
            className="group grid cursor-pointer grid-cols-1 gap-2 border-b border-line px-5 py-3 transition last:border-0 hover:bg-surface/60 md:grid-cols-[1fr_130px_150px_120px_90px] md:items-center md:gap-3">
            <div className="flex min-w-0 items-center gap-3">
              <DoneBox t={t} onPatch={onPatch} />
              <span className={`truncate text-sm font-medium ${t.status === "done" ? "text-ink-muted line-through" : ""}`}>{t.title}</span>
              {t.description && <span className="hidden text-xs text-ink-muted group-hover:inline">· détails</span>}
            </div>
            <div className="flex flex-wrap items-center gap-2 pl-8 md:contents">
              <div onClick={(e) => e.stopPropagation()}><StatusSelect value={t.status} onChange={(s) => onPatch(t.id, { status: s })} /></div>
              <div onClick={(e) => e.stopPropagation()}><AssigneeSelect value={t.assignee_id} onChange={(id) => onPatch(t.id, { assignee_id: id })} /></div>
              <div onClick={(e) => e.stopPropagation()}><DueInput t={t} onChange={(d) => onPatch(t.id, { due_date: d })} /></div>
              <span className={`inline-flex items-center gap-1 text-xs ${P.cls}`}><P.icon size={13} /> {P.label}</span>
            </div>
          </div>
        );
      })}
      <div className="p-2"><NewTask projectId={projectId} /></div>
      {done.length > 0 && (
        <button onClick={() => setShowDone(!showDone)} className="w-full border-t border-line py-2.5 text-xs font-medium text-ink-soft hover:bg-surface">
          {showDone ? "Masquer" : "Afficher"} les {done.length} tâche{done.length > 1 ? "s" : ""} terminée{done.length > 1 ? "s" : ""}
        </button>
      )}
    </div>
  );
}

function Card({ t, onOpen, onPatch, drag }: { t: Task; onOpen: () => void; onPatch: Props["onPatch"]; drag: boolean }) {
  const { members } = useSession();
  const m = members.find((x) => x.id === t.assignee_id);
  const due = dueLabel(t);
  const P = PRIORITY[t.priority];
  return (
    <div draggable={drag} onDragStart={(e) => { e.dataTransfer.setData("text/task", t.id); e.dataTransfer.effectAllowed = "move"; }}
      onClick={onOpen}
      className="cursor-pointer rounded-2xl border border-line bg-white p-3.5 shadow-[0_1px_2px_rgba(30,26,23,0.05)] transition hover:-translate-y-0.5 hover:shadow-md active:cursor-grabbing">
      <div className="flex items-start gap-2.5">
        <DoneBox t={t} onPatch={onPatch} />
        <span className={`text-sm font-medium leading-snug ${t.status === "done" ? "text-ink-muted line-through" : ""}`}>{t.title}</span>
      </div>
      <div className="mt-3 flex items-center gap-2 pl-7">
        {t.priority !== "normal" && <span className={`inline-flex items-center gap-0.5 text-[11px] font-medium ${P.cls}`}><P.icon size={12} />{P.label}</span>}
        {due && <span className={`text-[11px] ${due.tone}`}>{due.text}</span>}
        <span className="ml-auto">{m && <Avatar member={m} size="sm" />}</span>
      </div>
    </div>
  );
}

/** Vue colonnes (Kanban) : on glisse une carte d'une colonne à l'autre. */
export function TaskBoard({ tasks, projectId, onOpen, onPatch }: Props) {
  const [over, setOver] = useState<TaskStatus | null>(null);
  return (
    <div className="-mx-4 flex snap-x gap-4 overflow-x-auto px-4 pb-4 sm:mx-0 sm:px-0">
      {STATUS_ORDER.map((s) => {
        const col = tasks.filter((t) => t.status === s);
        return (
          <div key={s} onDragOver={(e) => { e.preventDefault(); setOver(s); }} onDragLeave={() => setOver(null)}
            onDrop={(e) => { e.preventDefault(); setOver(null); const id = e.dataTransfer.getData("text/task"); if (id) onPatch(id, { status: s }); }}
            className={`flex w-[78vw] max-w-[300px] shrink-0 snap-start flex-col rounded-3xl p-2.5 transition sm:w-auto sm:max-w-none sm:flex-1 ${over === s ? "bg-accent-soft ring-2 ring-accent/30" : "bg-surface-2/60"}`}>
            <div className="flex items-center gap-2 px-2 pb-2.5 pt-1.5">
              <span className={`h-2.5 w-2.5 rounded-full ${STATUS[s].dot}`} />
              <span className="text-sm font-semibold">{STATUS[s].label}</span>
              <span className="rounded-full bg-white px-2 text-xs font-semibold text-ink-soft">{col.length}</span>
            </div>
            <div className="flex min-h-24 flex-col gap-2">
              {col.map((t) => <Card key={t.id} t={t} drag onOpen={() => onOpen(t)} onPatch={onPatch} />)}
            </div>
            <div className="mt-1.5"><NewTask projectId={projectId} status={s} placeholder="Ajouter" /></div>
          </div>
        );
      })}
    </div>
  );
}

/** Vue calendrier : les tâches posées sur leur échéance. */
export function TaskCalendar({ tasks, onOpen }: Pick<Props, "tasks" | "onOpen">) {
  const [month, setMonth] = useState(() => { const d = new Date(); d.setDate(1); d.setHours(0, 0, 0, 0); return d; });
  const days = useMemo(() => {
    const start = new Date(month);
    start.setDate(1 - ((start.getDay() + 6) % 7));
    return Array.from({ length: 42 }, (_, i) => { const d = new Date(start); d.setDate(start.getDate() + i); return d; });
  }, [month]);
  const today = isoDay(new Date());
  const noDate = tasks.filter((t) => !t.due_date && t.status !== "done").length;
  const shift = (n: number) => { const d = new Date(month); d.setMonth(d.getMonth() + n); setMonth(d); };
  return (
    <div className="overflow-hidden rounded-3xl border border-line bg-white shadow-sm">
      <div className="flex items-center gap-2 border-b border-line px-4 py-3">
        <button onClick={() => shift(-1)} aria-label="Mois précédent" className="rounded-full p-1.5 hover:bg-surface"><ChevronLeft size={18} /></button>
        <span className="min-w-36 text-center font-semibold capitalize">{month.toLocaleDateString("fr-FR", { month: "long", year: "numeric" })}</span>
        <button onClick={() => shift(1)} aria-label="Mois suivant" className="rounded-full p-1.5 hover:bg-surface"><ChevronRight size={18} /></button>
        {noDate > 0 && <span className="ml-auto text-xs text-ink-muted">{noDate} tâche{noDate > 1 ? "s" : ""} sans échéance</span>}
      </div>
      <div className="grid grid-cols-7 border-b border-line text-center text-[11px] font-semibold uppercase tracking-wide text-ink-muted">
        {["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"].map((d) => <div key={d} className="py-2">{d}</div>)}
      </div>
      <div className="grid grid-cols-7">
        {days.map((d, i) => {
          const iso = isoDay(d);
          const items = tasks.filter((t) => t.due_date === iso);
          const inMonth = d.getMonth() === month.getMonth();
          return (
            <div key={i} className={`min-h-24 border-b border-r border-line p-1.5 sm:min-h-28 ${inMonth ? "" : "bg-surface/50"}`}>
              <div className={`mb-1 flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold ${iso === today ? "bg-accent text-white" : inMonth ? "" : "text-ink-muted"}`}>{d.getDate()}</div>
              <div className="space-y-1">
                {items.slice(0, 3).map((t) => (
                  <button key={t.id} onClick={() => onOpen(t)}
                    className={`block w-full truncate rounded-md px-1.5 py-0.5 text-left text-[11px] font-medium ${t.status === "done" ? "bg-[#E3F6EA] text-[#18794A] line-through" : t.due_date! < today ? "bg-[#FDE6E2] text-[#B5321F]" : "bg-accent-soft text-[#7A3E08]"}`}>
                    {t.title}
                  </button>
                ))}
                {items.length > 3 && <div className="px-1 text-[10px] text-ink-muted">+{items.length - 3}</div>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
