import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { CalendarDays, Check, Plus, UserRound, X } from "lucide-react";
import { projectsApi, type Member, type Project, type Task, type TaskStatus } from "../../lib/api";
import { useSession } from "../../lib/session";
import { Avatar } from "../../components/Avatar";
import { PRIORITY, STATUS, STATUS_ORDER, StatusPill, dueLabel } from "./meta";

/** Petit menu déroulant générique, fermé au clic à l'extérieur. */
export function Pop({ trigger, children, align = "left" }: { trigger: (open: () => void) => React.ReactNode; children: (close: () => void) => React.ReactNode; align?: "left" | "right" }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const f = (e: MouseEvent) => { if (!ref.current?.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", f);
    return () => document.removeEventListener("mousedown", f);
  }, [open]);
  return (
    <div ref={ref} className="relative inline-block" onClick={(e) => e.stopPropagation()}>
      {trigger(() => setOpen(!open))}
      {open && <div className={`absolute top-full z-40 mt-1 min-w-48 rounded-xl border border-line bg-white p-1 shadow-xl ${align === "right" ? "right-0" : "left-0"}`}>{children(() => setOpen(false))}</div>}
    </div>
  );
}

export function StatusSelect({ value, onChange }: { value: TaskStatus; onChange: (s: TaskStatus) => void }) {
  return (
    <Pop trigger={(o) => <button onClick={o} className="rounded-full transition hover:brightness-95"><StatusPill s={value} /></button>}>
      {(close) => STATUS_ORDER.map((s) => (
        <button key={s} onClick={() => { onChange(s); close(); }} className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm hover:bg-surface">
          <span className={`h-2 w-2 rounded-full ${STATUS[s].dot}`} /> {STATUS[s].label} {value === s && <Check size={14} className="ml-auto text-accent" />}
        </button>
      ))}
    </Pop>
  );
}

export function AssigneeSelect({ value, onChange, compact }: { value: string | null; onChange: (id: string | null) => void; compact?: boolean }) {
  const { members } = useSession();
  const m = members.find((x) => x.id === value);
  return (
    <Pop trigger={(o) => (
      <button onClick={o} title={m ? m.name : "Choisir un responsable"} className="flex items-center gap-1.5 rounded-full py-0.5 pr-2 text-xs hover:bg-surface">
        {m ? <Avatar member={m} size="sm" /> : <span className="flex h-8 w-8 items-center justify-center rounded-full border border-dashed border-ink-muted/50 text-ink-muted"><UserRound size={14} /></span>}
        {!compact && <span className={m ? "font-medium" : "text-ink-muted"}>{m ? m.name.split(" ")[0] : "Personne"}</span>}
      </button>
    )}>
      {(close) => (
        <div className="max-h-72 overflow-y-auto">
          <button onClick={() => { onChange(null); close(); }} className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-sm text-ink-muted hover:bg-surface"><X size={14} /> Personne</button>
          {members.map((x: Member) => (
            <button key={x.id} onClick={() => { onChange(x.id); close(); }} className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm hover:bg-surface">
              <Avatar member={x} size="sm" /> {x.name} {value === x.id && <Check size={14} className="ml-auto text-accent" />}
            </button>
          ))}
        </div>
      )}
    </Pop>
  );
}

export function DueInput({ t, onChange }: { t: Task; onChange: (d: string | null) => void }) {
  const lbl = dueLabel(t);
  return (
    <label className={`relative inline-flex cursor-pointer items-center gap-1 rounded-lg px-1.5 py-1 text-xs hover:bg-surface ${lbl?.tone ?? "text-ink-muted"}`}>
      <CalendarDays size={13} /> {lbl?.text ?? "Échéance"}
      <input type="date" value={t.due_date ?? ""} onChange={(e) => onChange(e.target.value || null)} className="absolute inset-0 cursor-pointer opacity-0" />
    </label>
  );
}

export function NewTask({ projectId, status = "todo", assignee, placeholder = "Nouvelle tâche…", onCreated }: {
  projectId: string; status?: TaskStatus; assignee?: string; placeholder?: string; onCreated?: () => void;
}) {
  const [title, setTitle] = useState("");
  const [active, setActive] = useState(false);
  const submit = async () => {
    if (!title.trim()) return;
    await projectsApi.createTask({ project_id: projectId, title: title.trim(), status, assignee_id: assignee ?? null });
    setTitle(""); onCreated?.();
  };
  if (!active) return (
    <button onClick={() => setActive(true)} className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-ink-muted transition hover:bg-surface hover:text-accent">
      <Plus size={16} /> {placeholder}
    </button>
  );
  return (
    <form onSubmit={(e) => { e.preventDefault(); submit(); }} className="flex items-center gap-2 rounded-xl border border-accent/50 bg-white px-3 py-1.5 shadow-sm">
      <Plus size={16} className="text-accent" />
      <input autoFocus value={title} onChange={(e) => setTitle(e.target.value)} onBlur={() => { if (!title.trim()) setActive(false); }}
        onKeyDown={(e) => { if (e.key === "Escape") { setTitle(""); setActive(false); } }}
        placeholder="Titre de la tâche, puis Entrée" className="min-w-0 flex-1 bg-transparent py-1 text-sm outline-none" />
    </form>
  );
}

export function TaskDrawer({ task, projects, onClose, onPatch }: {
  task: Task; projects: Project[]; onClose: () => void; onPatch: (d: Partial<Task>) => void;
}) {
  const { members } = useSession();
  const [title, setTitle] = useState(task.title);
  const [desc, setDesc] = useState(task.description);
  useEffect(() => { setTitle(task.title); setDesc(task.description); }, [task.id]); // eslint-disable-line react-hooks/exhaustive-deps
  const project = projects.find((p) => p.id === task.project_id);
  const by = members.find((m) => m.id === task.created_by);
  const upd = members.find((m) => m.id === task.updated_by);
  const row = "flex items-center gap-3 py-2.5";
  const lab = "w-28 shrink-0 text-xs font-semibold uppercase tracking-wide text-ink-muted";
  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-ink/30 backdrop-blur-[3px]" onClick={onClose}>
      <aside className="slide-in flex h-full w-full max-w-lg flex-col overflow-y-auto bg-white shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-line px-6 py-4">
          {project && <Link to={`/projets/${project.id}`} onClick={onClose} className="text-sm text-ink-soft hover:text-accent">{project.icon} {project.name}</Link>}
          <button onClick={onClose} aria-label="Fermer" className="rounded-full p-1.5 text-ink-soft hover:bg-surface"><X size={18} /></button>
        </div>
        <div className="px-6 py-5">
          <div className="flex items-start gap-3">
            <button onClick={() => onPatch({ status: task.status === "done" ? "todo" : "done" })} aria-label="Terminer"
              className={`mt-1.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 transition ${task.status === "done" ? "border-online bg-online text-white" : "border-ink-muted/40 hover:border-online"}`}>
              {task.status === "done" && <Check size={14} strokeWidth={3} />}
            </button>
            <textarea value={title} rows={1} onChange={(e) => setTitle(e.target.value)} onBlur={() => title.trim() && title !== task.title && onPatch({ title: title.trim() })}
              className={`w-full resize-none bg-transparent text-2xl font-semibold leading-snug tracking-tight outline-none [field-sizing:content] ${task.status === "done" ? "text-ink-muted line-through" : ""}`} />
          </div>
          <div className="mt-5 divide-y divide-line">
            <div className={row}><span className={lab}>Statut</span><StatusSelect value={task.status} onChange={(s) => onPatch({ status: s })} /></div>
            <div className={row}><span className={lab}>Responsable</span><AssigneeSelect value={task.assignee_id} onChange={(id) => onPatch({ assignee_id: id })} /></div>
            <div className={row}><span className={lab}>Échéance</span><DueInput t={task} onChange={(d) => onPatch({ due_date: d })} />
              {task.due_date && <button onClick={() => onPatch({ due_date: null })} className="text-xs text-ink-muted hover:text-busy">Retirer</button>}</div>
            <div className={row}><span className={lab}>Priorité</span>
              <div className="flex gap-1">
                {(["low", "normal", "high"] as const).map((p) => {
                  const P = PRIORITY[p];
                  return <button key={p} onClick={() => onPatch({ priority: p })} className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${task.priority === p ? "bg-ink text-white" : "bg-surface text-ink-soft hover:bg-surface-2"}`}><P.icon size={12} /> {P.label}</button>;
                })}
              </div>
            </div>
            <div className={row}><span className={lab}>Projet</span>
              <select value={task.project_id} onChange={(e) => onPatch({ project_id: e.target.value })} className="rounded-lg border border-line bg-white px-2 py-1.5 text-sm outline-none focus:border-accent">
                {projects.map((p) => <option key={p.id} value={p.id}>{p.icon} {p.name}</option>)}
              </select>
            </div>
          </div>
          <div className="mt-5 text-xs font-semibold uppercase tracking-wide text-ink-muted">Description</div>
          <textarea value={desc} onChange={(e) => setDesc(e.target.value)} onBlur={() => desc !== task.description && onPatch({ description: desc })} rows={6}
            placeholder="Ce qu'il faut faire, les liens utiles, ce qui compte pour dire que c'est fini…"
            className="mt-2 w-full resize-y rounded-2xl border border-line bg-surface/50 px-4 py-3 text-sm leading-relaxed outline-none focus:border-accent focus:bg-white" />
          <p className="mt-4 text-xs text-ink-muted">
            Créée par {by?.name ?? "?"} le {new Date(task.created_at).toLocaleDateString("fr-FR", { day: "numeric", month: "long" })}
            {upd && ` · modifiée par ${upd.name.split(" ")[0]} le ${new Date(task.updated_at).toLocaleDateString("fr-FR", { day: "numeric", month: "long" })} à ${new Date(task.updated_at).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}`}
          </p>
          <button onClick={() => { if (confirm("Mettre cette tâche à la corbeille ?")) { onPatch({ archived: true }); onClose(); } }}
            className="mt-6 text-sm font-medium text-busy hover:underline">Mettre à la corbeille</button>
        </div>
      </aside>
    </div>
  );
}
