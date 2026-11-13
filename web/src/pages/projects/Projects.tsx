import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, CalendarDays, ChevronRight, Columns3, FilePlus2, FileText, Inbox, Plus, Rows3, X } from "lucide-react";
import { projectsApi, type PageMeta, type Project, type Task } from "../../lib/api";
import { useSession } from "../../lib/session";
import { Avatar } from "../../components/Avatar";
import { useOrg } from "../OrgChart";
import { ICONS, STATUS, dueLabel, todayIso } from "./meta";
import { usePages, useProjectList, useTasks } from "./useProjects";
import { AssigneeSelect, NewTask, Pop, TaskDrawer } from "./TaskParts";
import { TaskBoard, TaskCalendar, TaskTable } from "./TaskViews";
import { PageEditor } from "./PageEditor";

function PageTree({ pages, parent, projectId, activeId, depth = 0 }: { pages: PageMeta[]; parent: string | null; projectId: string; activeId?: string; depth?: number }) {
  const kids = pages.filter((p) => p.parent_id === parent);
  return (
    <>
      {kids.map((p) => (
        <div key={p.id}>
          <Link to={`/projets/${projectId}/page/${p.id}`} style={{ paddingLeft: 12 + depth * 14 }}
            className={`flex items-center gap-2 rounded-lg py-1.5 pr-2 text-sm transition ${activeId === p.id ? "bg-accent-soft font-semibold text-accent" : "text-ink-soft hover:bg-surface hover:text-ink"}`}>
            <span>{p.icon}</span><span className="truncate">{p.title || "Sans titre"}</span>
          </Link>
          <PageTree pages={pages} parent={p.id} projectId={projectId} activeId={activeId} depth={depth + 1} />
        </div>
      ))}
    </>
  );
}

function Sidebar({ projects, projectId, pageId, onNewProject }: { projects: Project[]; projectId?: string; pageId?: string; onNewProject: () => void }) {
  const { pages } = usePages(projectId);
  const navigate = useNavigate();
  const addPage = async (parent: string | null = null) => {
    if (!projectId) return;
    const p = await projectsApi.createPage(projectId, { title: "", parent_id: parent });
    navigate(`/projets/${projectId}/page/${p.id}`);
  };
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between px-4 pb-2 pt-5">
        <h1 className="text-xl font-semibold tracking-tight">Projets</h1>
        <button onClick={onNewProject} title="Nouveau projet" className="rounded-xl bg-accent p-2 text-white shadow-sm shadow-accent/30 hover:bg-accent-hover"><Plus size={18} /></button>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-4">
        <Link to="/projets" className={`mb-2 flex items-center gap-2.5 rounded-xl px-2.5 py-2 text-sm font-medium ${!projectId ? "bg-accent-soft text-accent" : "text-ink hover:bg-surface"}`}>
          <span className={`flex h-7 w-7 items-center justify-center rounded-lg ${!projectId ? "bg-white" : "bg-surface-2"}`}><Inbox size={15} /></span> Mes tâches
        </Link>
        <div className="px-2.5 pb-1 pt-3 text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Projets</div>
        {projects.map((p) => {
          const active = p.id === projectId;
          const open = (p.counts.todo ?? 0) + (p.counts.doing ?? 0) + (p.counts.review ?? 0);
          return (
            <div key={p.id}>
              <Link to={`/projets/${p.id}`} className={`flex items-center gap-2.5 rounded-xl px-2.5 py-1.5 text-sm ${active && !pageId ? "bg-accent-soft font-semibold text-accent" : active ? "font-semibold text-ink" : "text-ink-soft hover:bg-surface hover:text-ink"}`}>
                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-surface-2 text-base">{p.icon}</span>
                <span className="flex-1 truncate">{p.name}</span>
                {open > 0 && <span className="text-xs text-ink-muted">{open}</span>}
              </Link>
              {active && (
                <div className="mb-2 ml-4 border-l border-line pl-1">
                  <PageTree pages={pages} parent={null} projectId={p.id} activeId={pageId} />
                  <button onClick={() => addPage()} className="flex w-full items-center gap-2 rounded-lg px-3 py-1.5 text-sm text-ink-muted hover:bg-surface hover:text-accent"><FilePlus2 size={14} /> Nouvelle page</button>
                </div>
              )}
            </div>
          );
        })}
        {!projects.length && <p className="px-2.5 py-2 text-xs text-ink-muted">Aucun projet pour l'instant.</p>}
      </div>
    </div>
  );
}

function NewProjectDialog({ onClose, onCreated }: { onClose: () => void; onCreated: (p: Project) => void }) {
  const { org } = useOrg();
  const [name, setName] = useState("");
  const [icon, setIcon] = useState("🚀");
  const [dept, setDept] = useState("");
  const [desc, setDesc] = useState("");
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-ink/30 backdrop-blur-[2px] sm:items-center sm:p-4" onClick={onClose}>
      <div className="page-in w-full max-w-md rounded-t-3xl bg-white p-6 shadow-2xl sm:rounded-3xl" onClick={(e) => e.stopPropagation()}>
        <div className="mb-5 flex items-center justify-between"><h2 className="text-lg font-semibold">Nouveau projet</h2>
          <button onClick={onClose} aria-label="Fermer" className="rounded-full p-1.5 text-ink-soft hover:bg-surface"><X size={19} /></button></div>
        <div className="flex items-center gap-3">
          <Pop trigger={(o) => <button onClick={o} className="flex h-12 w-12 items-center justify-center rounded-2xl bg-surface text-2xl hover:bg-surface-2">{icon}</button>}>
            {(close) => <div className="grid grid-cols-8 gap-0.5 p-1">{ICONS.map((i) => <button key={i} onClick={() => { setIcon(i); close(); }} className="rounded-lg p-1.5 text-xl hover:bg-surface">{i}</button>)}</div>}
          </Pop>
          <input autoFocus value={name} onChange={(e) => setName(e.target.value)} placeholder="Nom du projet (ex. Lancement 12/12)"
            className="min-w-0 flex-1 border-b-2 border-line pb-1.5 text-lg font-semibold outline-none focus:border-accent" />
        </div>
        <label className="mt-5 block text-xs font-semibold uppercase tracking-wide text-ink-muted">Département</label>
        <select value={dept} onChange={(e) => setDept(e.target.value)} className="mt-1.5 w-full rounded-xl border border-line bg-white px-3 py-2.5 text-sm outline-none focus:border-accent">
          <option value="">Toute l'entreprise</option>
          {org?.departments.map((d) => <option key={d}>{d}</option>)}
        </select>
        <label className="mt-4 block text-xs font-semibold uppercase tracking-wide text-ink-muted">En une phrase <span className="font-normal normal-case">(facultatif)</span></label>
        <input value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="Ce que ce projet doit permettre"
          className="mt-1.5 w-full rounded-xl border border-line px-3 py-2.5 text-sm outline-none focus:border-accent" />
        <button disabled={!name.trim()} onClick={async () => onCreated(await projectsApi.create({ name, icon, department: dept, description: desc }))}
          className="mt-6 w-full rounded-full bg-accent py-3 text-sm font-semibold text-white shadow-sm shadow-accent/30 hover:bg-accent-hover disabled:bg-surface-2 disabled:text-ink-muted disabled:shadow-none">
          Créer le projet
        </button>
      </div>
    </div>
  );
}

const VIEWS = [
  { id: "table", label: "Tableau", icon: Rows3 },
  { id: "board", label: "Colonnes", icon: Columns3 },
  { id: "calendar", label: "Calendrier", icon: CalendarDays },
] as const;

function ProjectView({ project, projects }: { project: Project; projects: Project[] }) {
  const { me, members } = useSession();
  const { pages } = usePages(project.id);
  const [view, setView] = useState<(typeof VIEWS)[number]["id"]>(() => (localStorage.getItem("hq-view") as any) || "board");
  const [mine, setMine] = useState(false);
  const { tasks, patch } = useTasks({ project_id: project.id });
  const [openId, setOpenId] = useState<string | null>(null);
  const [name, setName] = useState(project.name);
  const [desc, setDesc] = useState(project.description);
  const shown = (tasks ?? []).filter((t) => !mine || t.assignee_id === me?.id);
  const open = tasks?.find((t) => t.id === openId) ?? null;
  const total = tasks?.length ?? 0, done = tasks?.filter((t) => t.status === "done").length ?? 0;
  const pct = total ? Math.round((done / total) * 100) : 0;
  const owner = members.find((m) => m.id === project.owner_id);
  const setV = (v: typeof view) => { setView(v); try { localStorage.setItem("hq-view", v); } catch { /* rien */ } };

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-8 sm:py-8">
      <Link to="/projets" className="mb-3 inline-flex items-center gap-1 text-sm text-ink-soft md:hidden"><ArrowLeft size={16} /> Projets</Link>
      <div className="flex flex-wrap items-start gap-4">
        <Pop trigger={(o) => <button onClick={o} className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-3xl shadow-sm ring-1 ring-line hover:bg-surface">{project.icon}</button>}>
          {(close) => <div className="grid grid-cols-8 gap-0.5 p-1">{ICONS.map((i) => <button key={i} onClick={() => { projectsApi.update(project.id, { icon: i }); close(); }} className="rounded-lg p-1.5 text-xl hover:bg-surface">{i}</button>)}</div>}
        </Pop>
        <div className="min-w-0 flex-1">
          <input value={name} onChange={(e) => setName(e.target.value)} onBlur={() => name.trim() && name !== project.name && projectsApi.update(project.id, { name })}
            className="w-full bg-transparent text-3xl font-semibold tracking-tight outline-none" />
          <input value={desc} onChange={(e) => setDesc(e.target.value)} onBlur={() => desc !== project.description && projectsApi.update(project.id, { description: desc })}
            placeholder="Ajouter une description…" className="mt-1 w-full bg-transparent text-ink-soft outline-none placeholder:text-ink-muted" />
          <div className="mt-3 flex flex-wrap items-center gap-3 text-sm">
            {project.department && <span className="rounded-full bg-surface-2 px-2.5 py-1 text-xs font-medium text-ink-soft">{project.department}</span>}
            <span className="flex items-center gap-1.5 text-xs text-ink-soft">Responsable : <AssigneeSelect value={project.owner_id} onChange={(id) => projectsApi.update(project.id, { owner_id: id })} /></span>
            {total > 0 && (
              <span className="flex items-center gap-2 text-xs text-ink-soft">
                <span className="h-2 w-28 overflow-hidden rounded-full bg-surface-2"><span className="block h-full rounded-full bg-online transition-all" style={{ width: `${pct}%` }} /></span>
                {done}/{total} terminées
              </span>
            )}
            {!owner && null}
          </div>
        </div>
      </div>

      {pages.filter((p) => !p.parent_id).length > 0 && (
        <div className="mt-6 flex flex-wrap gap-2">
          {pages.filter((p) => !p.parent_id).map((p) => (
            <Link key={p.id} to={`/projets/${project.id}/page/${p.id}`} className="flex items-center gap-2 rounded-xl border border-line bg-white px-3 py-2 text-sm shadow-sm transition hover:border-accent/40 hover:shadow-md">
              <span>{p.icon}</span><span className="max-w-48 truncate font-medium">{p.title || "Sans titre"}</span><ChevronRight size={14} className="text-ink-muted" />
            </Link>
          ))}
        </div>
      )}

      <div className="mt-6 flex flex-wrap items-center gap-2">
        <div className="flex rounded-full bg-white p-1 shadow-sm ring-1 ring-line">
          {VIEWS.map(({ id, label, icon: Icon }) => (
            <button key={id} onClick={() => setV(id)} className={`flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-sm font-medium transition ${view === id ? "bg-ink text-white" : "text-ink-soft hover:text-ink"}`}>
              <Icon size={15} /> {label}
            </button>
          ))}
        </div>
        <button onClick={() => setMine(!mine)} className={`rounded-full px-3.5 py-2 text-sm font-medium shadow-sm ring-1 transition ${mine ? "bg-accent-soft text-accent ring-accent/30" : "bg-white text-ink-soft ring-line hover:text-ink"}`}>
          Mes tâches seulement
        </button>
      </div>

      <div className="mt-4">
        {tasks === null ? null : view === "table" ? <TaskTable tasks={shown} projectId={project.id} onOpen={(t) => setOpenId(t.id)} onPatch={patch} />
          : view === "board" ? <TaskBoard tasks={shown} projectId={project.id} onOpen={(t) => setOpenId(t.id)} onPatch={patch} />
          : <TaskCalendar tasks={shown} onOpen={(t) => setOpenId(t.id)} />}
      </div>
      {open && <TaskDrawer task={open} projects={projects} onClose={() => setOpenId(null)} onPatch={(d) => patch(open.id, d)} />}
    </div>
  );
}

function Section({ title, tone, tasks, projects, onOpen, onPatch }: {
  title: string; tone: string; tasks: Task[]; projects: Project[]; onOpen: (t: Task) => void; onPatch: (id: string, d: Partial<Task>) => void;
}) {
  if (!tasks.length) return null;
  return (
    <div className="mt-6">
      <h2 className={`mb-2 text-sm font-semibold ${tone}`}>{title} · {tasks.length}</h2>
      <div className="overflow-hidden rounded-2xl border border-line bg-white shadow-sm">
        {tasks.map((t) => {
          const p = projects.find((x) => x.id === t.project_id);
          const due = dueLabel(t);
          return (
            <div key={t.id} onClick={() => onOpen(t)} className="flex cursor-pointer items-center gap-3 border-b border-line px-4 py-3 last:border-0 hover:bg-surface/60">
              <button onClick={(e) => { e.stopPropagation(); onPatch(t.id, { status: t.status === "done" ? "todo" : "done" }); }}
                className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 ${t.status === "done" ? "border-online bg-online text-white" : "border-ink-muted/40 hover:border-online"}`}>
                {t.status === "done" && <span className="text-[10px]">✓</span>}
              </button>
              <span className={`min-w-0 flex-1 truncate text-sm font-medium ${t.status === "done" ? "text-ink-muted line-through" : ""}`}>{t.title}</span>
              <span className="hidden text-xs text-ink-muted sm:inline">{p?.icon} {p?.name}</span>
              <span className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-semibold ${STATUS[t.status].pill}`}>{STATUS[t.status].label}</span>
              {due && <span className={`w-20 text-right text-xs ${due.tone}`}>{due.text}</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MyTasks({ projects }: { projects: Project[] }) {
  const { me } = useSession();
  const { tasks, patch } = useTasks(me ? { assignee_id: me.id } : null);
  const [openId, setOpenId] = useState<string | null>(null);
  const groups = useMemo(() => {
    const today = todayIso();
    const week = new Date(); week.setDate(week.getDate() + 7);
    const wk = week.toISOString().slice(0, 10);
    const open = (tasks ?? []).filter((t) => t.status !== "done");
    return {
      late: open.filter((t) => t.due_date && t.due_date < today),
      today: open.filter((t) => t.due_date === today),
      week: open.filter((t) => t.due_date && t.due_date > today && t.due_date <= wk),
      later: open.filter((t) => t.due_date && t.due_date > wk),
      none: open.filter((t) => !t.due_date),
      done: (tasks ?? []).filter((t) => t.status === "done" && t.completed_at && Date.now() - new Date(t.completed_at).getTime() < 7 * 86400000),
    };
  }, [tasks]);
  if (!me) return null;
  const open = tasks?.find((t) => t.id === openId) ?? null;
  const firstProject = projects[0];
  const s = { projects, onOpen: (t: Task) => setOpenId(t.id), onPatch: patch };
  const nothing = tasks && !tasks.filter((t) => t.status !== "done").length;
  return (
    <div className="mx-auto max-w-4xl px-4 py-6 sm:px-8 sm:py-8">
      <div className="flex items-center gap-3">
        <Avatar member={me} size="md" />
        <div><h1 className="text-3xl font-semibold tracking-tight">Mes tâches</h1><p className="text-sm text-ink-soft">Tout ce qui vous est confié, tous projets confondus.</p></div>
      </div>
      {firstProject && <div className="mt-5"><NewTask projectId={firstProject.id} assignee={me.id} placeholder={`Nouvelle tâche pour moi (dans ${firstProject.icon} ${firstProject.name})`} /></div>}
      {nothing && <div className="mt-6 rounded-2xl bg-[#E3F6EA] p-5 text-sm text-[#18794A]">🎉 Rien en attente pour vous. Les tâches qu'on vous confie apparaîtront ici.</div>}
      <Section title="En retard" tone="text-busy" tasks={groups.late} {...s} />
      <Section title="Aujourd'hui" tone="text-accent" tasks={groups.today} {...s} />
      <Section title="Cette semaine" tone="text-ink" tasks={groups.week} {...s} />
      <Section title="Plus tard" tone="text-ink-soft" tasks={groups.later} {...s} />
      <Section title="Sans échéance" tone="text-ink-soft" tasks={groups.none} {...s} />
      <Section title="Terminé cette semaine" tone="text-online" tasks={groups.done} {...s} />
      {open && <TaskDrawer task={open} projects={projects} onClose={() => setOpenId(null)} onPatch={(d) => patch(open.id, d)} />}
    </div>
  );
}

export function Projects() {
  const { projectId, pageId } = useParams();
  const navigate = useNavigate();
  const { projects } = useProjectList();
  const [creating, setCreating] = useState(false);
  if (!projects) return null;
  const project = projects.find((p) => p.id === projectId);
  return (
    <div className="flex h-full">
      <div className="hidden w-72 shrink-0 border-r border-line bg-white md:block">
        <Sidebar projects={projects} projectId={projectId} pageId={pageId} onNewProject={() => setCreating(true)} />
      </div>
      <div className="min-w-0 flex-1 overflow-y-auto">
        {!projectId && (
          <div className="md:hidden">
            <div className="flex gap-2 overflow-x-auto px-4 pt-4">
              {projects.map((p) => <Link key={p.id} to={`/projets/${p.id}`} className="flex shrink-0 items-center gap-2 rounded-full bg-white px-3 py-2 text-sm font-medium shadow-sm ring-1 ring-line">{p.icon} {p.name}</Link>)}
              <button onClick={() => setCreating(true)} className="flex shrink-0 items-center gap-1 rounded-full bg-accent px-3 py-2 text-sm font-semibold text-white"><Plus size={15} /> Projet</button>
            </div>
          </div>
        )}
        {pageId ? (
          <div>
            {project && <Link to={`/projets/${project.id}`} className="ml-4 mt-4 inline-flex items-center gap-1.5 text-sm text-ink-soft hover:text-accent sm:ml-10"><ArrowLeft size={15} /> {project.icon} {project.name}</Link>}
            <PageEditor key={pageId} pageId={pageId} />
          </div>
        ) : project ? <ProjectView key={project.id} project={project} projects={projects} />
          : projectId ? null
          : projects.length ? <MyTasks projects={projects} /> : (
            <div className="flex h-full items-center justify-center px-6 text-center">
              <div className="max-w-sm">
                <span className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-accent-soft text-accent"><FileText size={28} /></span>
                <h2 className="mt-4 text-xl font-semibold">Premier projet</h2>
                <p className="mt-1 text-sm text-ink-soft">Un projet rassemble ses pages (notes, plans, comptes rendus) et ses tâches.</p>
                <button onClick={() => setCreating(true)} className="mt-5 rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-white shadow-sm shadow-accent/30 hover:bg-accent-hover">Créer un projet</button>
              </div>
            </div>
          )}
      </div>
      {creating && <NewProjectDialog onClose={() => setCreating(false)} onCreated={(p) => { setCreating(false); navigate(`/projets/${p.id}`); }} />}
    </div>
  );
}
