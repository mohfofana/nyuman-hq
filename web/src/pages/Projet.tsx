import { useEffect, useMemo, useState, type DragEvent, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "motion/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api, ApiError, captureUrl, type Member, type Pole, type Priorite, type Retour, type Tache, type TacheChanges, type TacheStatus } from "../api";
import { POLES } from "../poles";
import { firstName, formatAgo, formatDateTime } from "../format";
import { useLive, usePresence } from "../live";
import { Avatar } from "../components/Avatar";
import { IconClose, IconPlus } from "../components/Icons";
import { RetourModal } from "../components/RetourModal";
import { Etapes } from "../components/Etapes";

const COLUMNS: { key: TacheStatus; label: string }[] = [
  { key: "a_faire", label: "À faire" },
  { key: "en_cours", label: "En cours" },
  { key: "en_attente", label: "En attente" },
  { key: "fait", label: "Fait" },
];
const FAIT_VISIBLES = 12;

export const PRIORITES: { key: Exclude<Priorite, "">; label: string; tone: string }[] = [
  { key: "P0", label: "Critique", tone: "bad" },
  { key: "P1", label: "Haute", tone: "brand" },
  { key: "P2", label: "Moyenne", tone: "wait" },
  { key: "P3", label: "Basse", tone: "neutral" },
];
const priorite = (key: Priorite) => PRIORITES.find((p) => p.key === key);

const KIND_LABEL = { bug: "Bug", idee: "Idée", remarque: "Remarque" } as const;
const KIND_TONE = { bug: "bad", idee: "agent", remarque: "wait" } as const;

type Filtre = "tous" | "moi" | "agents" | number;

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

function dueLabel(due: string): string {
  return new Date(`${due}T12:00:00`).toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
}

function AssigneeSelect({ members, value, onChange, id }: {
  members: Member[];
  value: number | null;
  onChange: (v: number | null) => void;
  id: string;
}) {
  const humans = members.filter((m) => m.active && m.kind === "humain");
  const agents = members.filter((m) => m.active && m.kind === "agent");
  return (
    <select id={id} className="select" value={value ?? ""} onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}>
      <option value="">Personne pour l’instant</option>
      <optgroup label="Humains">
        {humans.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
      </optgroup>
      <optgroup label="Agents">
        {agents.map((m) => <option key={m.id} value={m.id}>{m.name} (agent)</option>)}
      </optgroup>
    </select>
  );
}

function TaskCard({ tache, onOpen, onDragStart, onDragEnd, onDragOverCard, dropBefore, dragging }: {
  tache: Tache;
  onOpen: () => void;
  onDragStart: (e: DragEvent) => void;
  onDragEnd: () => void;
  onDragOverCard: (e: DragEvent) => void;
  dropBefore: boolean;
  dragging: boolean;
}) {
  const late = tache.due_date && tache.status !== "fait" && tache.due_date < today();
  const prio = priorite(tache.priority);
  const etapesFaites = tache.etapes.filter((e) => e.status === "fait").length;
  return (
    <motion.button
      layout
      layoutId={`tache-${tache.id}`}
      type="button"
      draggable
      onDragStartCapture={onDragStart}
      onDragEndCapture={onDragEnd}
      onDragOverCapture={onDragOverCard}
      onClick={onOpen}
      className={["task", dragging ? "dragging" : "", dropBefore ? "drop-before" : ""].filter(Boolean).join(" ")}
      transition={{ type: "spring", stiffness: 420, damping: 34 }}
      aria-label={`${tache.title}${tache.assignee ? `, confiée à ${tache.assignee.name}` : ""}`}
    >
      <span className="task-title" style={tache.status === "fait" ? { textDecoration: "line-through", color: "var(--ink-2)" } : undefined}>
        {tache.title}
      </span>
      <span className="task-meta">
        {tache.assignee ? <Avatar member={tache.assignee} size={26} /> : <span className="nobody" title="Personne pour l’instant" />}
        {tache.assignee && <span className="small" style={{ fontWeight: 600 }}>{firstName(tache.assignee.name)}</span>}
        <span style={{ marginLeft: "auto", display: "flex", gap: 6, flexWrap: "wrap", justifyContent: "flex-end" }}>
          {prio && tache.status !== "fait" && <span className={`chip ${prio.tone}`} title={`Priorité ${prio.label.toLowerCase()}`}>{prio.key}</span>}
          {tache.etapes.length > 0 && <span className="chip neutral" title="Étapes faites">{etapesFaites}/{tache.etapes.length}</span>}
          {tache.retour_id && <span className="chip bad">retour</span>}
          {tache.objectif_id && <span className="chip brand">objectif</span>}
          {tache.due_date && <span className={late ? "chip bad" : "chip neutral"}>{late ? "en retard · " : ""}{dueLabel(tache.due_date)}</span>}
        </span>
      </span>
    </motion.button>
  );
}

function RetourCard({ retour, members, highlight }: { retour: Retour; members: Member[]; highlight: boolean }) {
  const queryClient = useQueryClient();
  const [converting, setConverting] = useState(false);
  const [assignee, setAssignee] = useState<number | null>(null);
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["retours"] });
    queryClient.invalidateQueries({ queryKey: ["taches"] });
    queryClient.invalidateQueries({ queryKey: ["retours-etat"] });
  };
  const convert = useMutation({ mutationFn: () => api.convertRetour(retour.id, { assignee_id: assignee }), onSuccess: refresh });
  const classer = useMutation({ mutationFn: () => api.classerRetour(retour.id), onSuccess: refresh });

  return (
    <motion.div layout id={`retour-${retour.id}`} className={highlight ? "retour-card highlight" : "retour-card"}
      initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, x: 30 }}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
        <span className={`chip ${KIND_TONE[retour.kind]}`}>{KIND_LABEL[retour.kind]}</span>
        {retour.espace && <span className="chip on-night">{retour.espace === "cliente" ? "côté clientes" : "côté pros"}</span>}
        {retour.source === "testflight" && <span className="chip on-night">TestFlight</span>}
        <span className="mono" style={{ marginLeft: "auto", fontSize: 11.5, color: "var(--cream-2)" }}>{formatAgo(retour.created_at)}</span>
      </div>
      {retour.comment ? <p>{retour.comment}</p> : <p style={{ color: "var(--cream-2)" }}>Pas de commentaire, voir les captures.</p>}
      {retour.captures > 0 && (
        <div className="retour-thumbs">
          {Array.from({ length: retour.captures }, (_, i) => (
            <a key={i} href={captureUrl(retour.id, i)} target="_blank" rel="noreferrer" aria-label={`Ouvrir la capture ${i + 1}`}>
              <img src={captureUrl(retour.id, i)} alt="" loading="lazy" />
            </a>
          ))}
        </div>
      )}
      <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12.5, color: "var(--cream-2)" }}>
        {retour.author && <Avatar member={retour.author} size={22} onNight />}
        <span>
          {retour.author ? firstName(retour.author.name) : retour.tester_email ?? "Testeur"}
          {(retour.device_model || retour.build_version) && ` · ${[retour.device_model, retour.os_version && `iOS ${retour.os_version}`, retour.build_version && `build ${retour.build_version}`].filter(Boolean).join(", ")}`}
        </span>
      </div>
      {converting ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <label className="visually-hidden" htmlFor={`conv-${retour.id}`}>Confier la tâche à</label>
          <AssigneeSelect id={`conv-${retour.id}`} members={members} value={assignee} onChange={setAssignee} />
          <div className="retour-actions">
            <button type="button" className="btn small on-night" disabled={convert.isPending} onClick={() => convert.mutate()}>Créer la tâche</button>
            <button type="button" className="btn small ghost-night" onClick={() => setConverting(false)}>Annuler</button>
          </div>
        </div>
      ) : (
        <div className="retour-actions">
          <button type="button" className="btn small on-night" onClick={() => setConverting(true)}>En faire une tâche</button>
          <button type="button" className="btn small ghost-night" disabled={classer.isPending} onClick={() => classer.mutate()}>Classer</button>
        </div>
      )}
      {(convert.error || classer.error) && <p className="notice bad">{((convert.error || classer.error) as ApiError).message}</p>}
    </motion.div>
  );
}

function TaskDrawer({ tache, members, onClose }: { tache: Tache; members: Member[]; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState(tache.title);
  const [description, setDescription] = useState(tache.description);
  const [editingDesc, setEditingDesc] = useState(false);
  const update = useMutation({
    mutationFn: (changes: TacheChanges) => api.updateTache(tache.id, changes),
    onSuccess: (t) => queryClient.setQueryData<Tache[]>(["taches"], (list) => list?.map((x) => (x.id === t.id ? t : x))),
  });
  const archive = useMutation({
    mutationFn: () => api.archiveTache(tache.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["taches"] });
      onClose();
    },
  });

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="drawer-wrap" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <motion.aside
        className="drawer"
        role="dialog"
        aria-modal="true"
        aria-label={`Tâche : ${tache.title}`}
        initial={{ x: 60, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ type: "spring", stiffness: 360, damping: 34 }}
      >
        <div className="card-head">
          <span className="eyebrow">
            Tâche n° {tache.id}{tache.source === "testflight" ? " · TestFlight" : tache.source === "tableau" ? " · reprise du tableau" : ""}
          </span>
          <button type="button" className="icon-btn light" onClick={onClose} aria-label="Fermer"><IconClose /></button>
        </div>

        <input
          aria-label="Titre de la tâche"
          className="input"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onBlur={() => title.trim() && title !== tache.title && update.mutate({ title })}
          style={{ fontSize: 22, fontWeight: 800, minHeight: 56, letterSpacing: "-0.02em" }}
        />

        <div className="segmented" role="group" aria-label="Colonne" style={{ alignSelf: "flex-start", flexWrap: "wrap" }}>
          {COLUMNS.map((c) => (
            <button key={c.key} type="button" aria-pressed={tache.status === c.key} onClick={() => update.mutate({ status: c.key })}>{c.label}</button>
          ))}
        </div>

        <div className="grid-cards" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 200px), 1fr))" }}>
          <div className="field">
            <label htmlFor="t-assignee">Confiée à</label>
            <AssigneeSelect id="t-assignee" members={members} value={tache.assignee?.id ?? null} onChange={(v) => update.mutate({ assignee_id: v })} />
          </div>
          <div className="field">
            <label htmlFor="t-due">Pour le</label>
            <input id="t-due" className="input" type="date" value={tache.due_date ?? ""} onChange={(e) => update.mutate({ due_date: e.target.value || null })} />
          </div>
          <div className="field">
            <label htmlFor="t-prio">Priorité</label>
            <select id="t-prio" className="select" value={tache.priority} onChange={(e) => update.mutate({ priority: e.target.value as Priorite })}>
              <option value="">Pas précisée</option>
              {PRIORITES.map((p) => <option key={p.key} value={p.key}>{p.key} · {p.label}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="t-pole">Pôle</label>
            <select id="t-pole" className="select" value={tache.pole} onChange={(e) => update.mutate({ pole: e.target.value as Pole })}>
              <option value="">Sans pôle</option>
              {POLES.map((p) => <option key={p.key} value={p.key}>{p.label}</option>)}
            </select>
          </div>
        </div>

        <label style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 14 }}>
          <input type="checkbox" checked={tache.objectif_id !== null} onChange={(e) => update.mutate({ objectif: e.target.checked })} />
          Sert l’objectif du trimestre
        </label>

        <Etapes tache={tache} members={members} />

        <div className="field">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 13, fontWeight: 650 }}>Détails</span>
            <button type="button" className="link-btn" onClick={() => {
              if (editingDesc && description !== tache.description) update.mutate({ description });
              setEditingDesc(!editingDesc);
            }}>
              {editingDesc ? "Enregistrer" : "Modifier"}
            </button>
          </div>
          {editingDesc ? (
            <textarea aria-label="Détails de la tâche" className="textarea" style={{ minHeight: 200 }} value={description} onChange={(e) => setDescription(e.target.value)} />
          ) : description.trim() ? (
            <div className="prose" style={{ fontSize: 14.5 }}><ReactMarkdown remarkPlugins={[remarkGfm]}>{description}</ReactMarkdown></div>
          ) : (
            <p className="soft small">Pas encore de détails.</p>
          )}
        </div>

        {update.error && <p className="notice bad" role="alert">{(update.error as ApiError).message}</p>}

        <p className="soft small" style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Avatar member={tache.created_by} size={20} />
          Créée par {tache.created_by.name}, {formatDateTime(tache.created_at)}
          {tache.done_at && ` · terminée ${formatAgo(tache.done_at)}`}
        </p>
        <button type="button" className="btn" style={{ alignSelf: "flex-start" }} disabled={archive.isPending} onClick={() => archive.mutate()}>
          Mettre à la corbeille
        </button>
      </motion.aside>
    </div>
  );
}

export function Projet() {
  const { me, presences } = useLive();
  const queryClient = useQueryClient();
  const [params, setParams] = useSearchParams();
  const taches = useQuery({ queryKey: ["taches"], queryFn: () => api.taches() });
  const retours = useQuery({ queryKey: ["retours"], queryFn: () => api.retours("nouveau") });
  const members = useQuery({ queryKey: ["membres"], queryFn: api.members });
  const [filtre, setFiltre] = useState<Filtre>("tous");
  const [pole, setPole] = useState<Pole | "tous">("tous");
  const [newTitle, setNewTitle] = useState("");
  const [draggingId, setDraggingId] = useState<number | null>(null);
  const [overColumn, setOverColumn] = useState<TacheStatus | null>(null);
  const [dropBeforeId, setDropBeforeId] = useState<number | null>(null);
  const [showAllDone, setShowAllDone] = useState(false);
  const [signaler, setSignaler] = useState(false);

  const selectedId = Number(params.get("tache")) || null;
  const highlightRetour = Number(params.get("retour")) || null;
  const all = taches.data ?? [];
  const selected = all.find((t) => t.id === selectedId) ?? null;
  usePresence({ piece: "projet", label: selected ? `travaille sur « ${selected.title} »` : "regarde la salle de projet" });

  useEffect(() => {
    if (highlightRetour) document.getElementById(`retour-${highlightRetour}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [highlightRetour, retours.data]);

  const memberList = members.data ?? [];
  const visible = useMemo(
    () =>
      all
        .filter((t) => pole === "tous" || t.pole === pole)
        .filter((t) =>
          filtre === "tous" ? true : filtre === "moi" ? t.assignee?.id === me.id : filtre === "agents" ? t.assignee?.kind === "agent" : t.assignee?.id === filtre,
        ),
    [all, filtre, pole, me.id],
  );
  const byColumn = (status: TacheStatus) => {
    const list = visible.filter((t) => t.status === status);
    return status === "fait"
      ? list.sort((a, b) => (b.done_at ?? "").localeCompare(a.done_at ?? ""))
      : list.sort((a, b) => a.position - b.position);
  };

  const create = useMutation({
    mutationFn: (title: string) =>
      api.createTache({
        title,
        assignee_id: typeof filtre === "number" ? filtre : filtre === "moi" ? me.id : null,
        pole: pole === "tous" ? "" : pole,
      }),
    onSuccess: () => {
      setNewTitle("");
      queryClient.invalidateQueries({ queryKey: ["taches"] });
    },
  });

  function open(id: number | null) {
    const next = new URLSearchParams(params);
    if (id) next.set("tache", String(id));
    else next.delete("tache");
    setParams(next, { replace: true });
  }

  function move(id: number, status: TacheStatus, beforeId: number | null) {
    const column = byColumn(status).filter((t) => t.id !== id);
    let position: number;
    const index = beforeId ? column.findIndex((t) => t.id === beforeId) : -1;
    if (index === -1) position = (column.at(-1)?.position ?? 0) + 1;
    else if (index === 0) position = column[0].position - 1;
    else position = (column[index - 1].position + column[index].position) / 2;

    // On déplace tout de suite à l'écran ; le serveur confirme, et les autres écrans suivent en direct.
    queryClient.setQueryData<Tache[]>(["taches"], (list) => list?.map((t) => (t.id === id ? { ...t, status, position } : t)));
    api.updateTache(id, { status, position }).catch(() => queryClient.invalidateQueries({ queryKey: ["taches"] }));
  }

  function onDrop(e: DragEvent, status: TacheStatus) {
    e.preventDefault();
    const id = Number(e.dataTransfer.getData("text/plain"));
    if (id) move(id, status, dropBeforeId);
    setDraggingId(null);
    setOverColumn(null);
    setDropBeforeId(null);
  }

  function submitNew(e: FormEvent) {
    e.preventDefault();
    if (newTitle.trim()) create.mutate(newTitle.trim());
  }

  const filterPeople = memberList.filter((m) => m.active && all.some((t) => t.assignee?.id === m.id));
  const nouveaux = retours.data ?? [];

  return (
    <div className="page" style={{ maxWidth: 1600 }}>
      <header style={{ display: "flex", flexWrap: "wrap", alignItems: "flex-end", justifyContent: "space-between", gap: 16, paddingTop: 8 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <span className="eyebrow">La maison</span>
          <h1 className="display">La salle de projet</h1>
          <p className="soft" style={{ fontSize: 16, maxWidth: "62ch" }}>
            Les tâches de toute l’équipe, humains et agents, vers l’objectif du trimestre. Glisse une carte pour la changer de colonne.
          </p>
        </div>
        <button type="button" className="btn brand" onClick={() => setSignaler(true)}>Signaler un retour sur l’app</button>
      </header>

      <div className="segmented" role="group" aria-label="Pôle" style={{ alignSelf: "flex-start", flexWrap: "wrap" }}>
        <button type="button" aria-pressed={pole === "tous"} onClick={() => setPole("tous")}>Tous les pôles</button>
        {POLES.map((p) => (
          <button key={p.key} type="button" aria-pressed={pole === p.key} onClick={() => setPole(p.key)}>
            {p.label} · {all.filter((t) => t.pole === p.key && t.status !== "fait").length}
          </button>
        ))}
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 10 }}>
        <div className="segmented" role="group" aria-label="Filtrer les tâches">
          {(["tous", "moi", "agents"] as const).map((f) => (
            <button key={f} type="button" aria-pressed={filtre === f} onClick={() => setFiltre(f)}>
              {f === "tous" ? "Tout le monde" : f === "moi" ? "Mes tâches" : "Les agents"}
            </button>
          ))}
        </div>
        {filterPeople.filter((m) => m.id !== me.id).map((m) => (
          <button key={m.id} type="button" className={filtre === m.id ? "btn small primary" : "btn small"} aria-pressed={filtre === m.id}
            onClick={() => setFiltre(filtre === m.id ? "tous" : m.id)} style={{ paddingLeft: 6 }}>
            <Avatar member={m} size={24} /> {firstName(m.name)}
          </button>
        ))}
      </div>

      <div className="board">
        <section className="column inbox" aria-label="Retours sur l’app à trier">
          <div className="column-head">
            <span className="column-title">Retours à trier</span>
            <span className="column-count">{nouveaux.length}</span>
          </div>
          <button type="button" className="btn small on-night" onClick={() => setSignaler(true)}><IconPlus /> Signaler</button>
          <AnimatePresence>
            {nouveaux.map((r) => <RetourCard key={r.id} retour={r} members={memberList} highlight={r.id === highlightRetour} />)}
          </AnimatePresence>
          {retours.data && nouveaux.length === 0 && (
            <p style={{ fontSize: 13.5, color: "var(--cream-2)", padding: "4px 2px" }}>
              Rien à trier. Bugs, idées et captures des testeurs arrivent ici, au lieu de WhatsApp.
            </p>
          )}
        </section>

        {COLUMNS.map((col) => {
          const cards = byColumn(col.key);
          const shown = col.key === "fait" && !showAllDone ? cards.slice(0, FAIT_VISIBLES) : cards;
          const workingHere = memberList.filter((m) => presences[m.id]?.piece === "projet" && m.id !== me.id);
          return (
            <section
              key={col.key}
              className={overColumn === col.key ? "column over" : "column"}
              aria-label={col.label}
              onDragOver={(e) => { e.preventDefault(); setOverColumn(col.key); }}
              onDragLeave={(e) => { if (!e.currentTarget.contains(e.relatedTarget as Node)) setOverColumn(null); }}
              onDrop={(e) => onDrop(e, col.key)}
            >
              <div className="column-head">
                <span className="column-title">{col.label}</span>
                <span className="column-count">{cards.length}</span>
              </div>
              {col.key === "a_faire" && (
                <form className="quick-add" onSubmit={submitNew}>
                  <label className="visually-hidden" htmlFor="new-task">Nouvelle tâche</label>
                  <input id="new-task" className="input" placeholder="Nouvelle tâche, puis Entrée" value={newTitle} onChange={(e) => setNewTitle(e.target.value)} />
                </form>
              )}
              {shown.map((t) => (
                <TaskCard
                  key={t.id}
                  tache={t}
                  onOpen={() => open(t.id)}
                  dragging={draggingId === t.id}
                  dropBefore={dropBeforeId === t.id && draggingId !== t.id}
                  onDragStart={(e) => { e.dataTransfer.setData("text/plain", String(t.id)); e.dataTransfer.effectAllowed = "move"; setDraggingId(t.id); }}
                  onDragEnd={() => { setDraggingId(null); setOverColumn(null); setDropBeforeId(null); }}
                  onDragOverCard={() => setDropBeforeId(t.id)}
                />
              ))}
              {col.key === "fait" && cards.length > FAIT_VISIBLES && (
                <button type="button" className="link-btn" onClick={() => setShowAllDone(!showAllDone)}>
                  {showAllDone ? "Voir moins" : `Voir les ${cards.length - FAIT_VISIBLES} autres`}
                </button>
              )}
              {cards.length === 0 && col.key !== "a_faire" && <p className="soft small" style={{ padding: "4px 2px" }}>Rien ici.</p>}
              {col.key === "en_cours" && workingHere.length > 0 && (
                <p className="soft small" style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  {workingHere.slice(0, 3).map((m) => <Avatar key={m.id} member={m} size={20} />)} aussi dans la salle
                </p>
              )}
            </section>
          );
        })}
      </div>

      {all.length === 0 && taches.data && (
        <p className="soft">
          Aucune tâche pour l’instant. Écris la première dans « À faire », ou transforme un retour en tâche.{" "}
          <Link to="/bureaux">Les agents</Link> pourront aussi en recevoir.
        </p>
      )}

      {selected && <TaskDrawer key={selected.id} tache={selected} members={memberList} onClose={() => open(null)} />}
      {signaler && <RetourModal onClose={() => setSignaler(false)} />}
    </div>
  );
}
