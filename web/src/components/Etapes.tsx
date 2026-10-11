import { useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, type Etape, type EtapeChanges, type EtapeStatus, type Member, type Tache } from "../api";
import { Avatar } from "./Avatar";

const STATUTS: { key: EtapeStatus; label: string }[] = [
  { key: "a_faire", label: "À faire" },
  { key: "en_cours", label: "En cours" },
  { key: "fait", label: "Fait" },
];

function shortDate(d: string): string {
  return new Date(`${d}T12:00:00`).toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
}

function EtapeRow({ tache, etape, members, onSaved }: {
  tache: Tache;
  etape: Etape;
  members: Member[];
  onSaved: (t: Tache) => void;
}) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState(etape.title);
  const [livrable, setLivrable] = useState(etape.livrable);
  const [notes, setNotes] = useState(etape.notes);
  const update = useMutation({ mutationFn: (c: EtapeChanges) => api.updateEtape(tache.id, etape.id, c), onSuccess: onSaved });
  const archive = useMutation({ mutationFn: () => api.archiveEtape(tache.id, etape.id), onSuccess: onSaved });
  const done = etape.status === "fait";
  const today = new Date().toISOString().slice(0, 10);
  const late = etape.due_date && !done && etape.due_date < today;

  return (
    <li className={open ? "etape open" : "etape"}>
      <div className="etape-line">
        <input
          type="checkbox"
          checked={done}
          aria-label={done ? `Rouvrir « ${etape.title} »` : `Marquer « ${etape.title} » comme fait`}
          onChange={() => update.mutate({ status: done ? "a_faire" : "fait" })}
        />
        <button type="button" className="etape-title" onClick={() => setOpen(!open)} aria-expanded={open}
          style={done ? { textDecoration: "line-through", color: "var(--ink-2)" } : undefined}>
          {etape.title}
        </button>
        {etape.status === "en_cours" && <span className="chip wait">en cours</span>}
        {etape.due_date && <span className={late ? "chip bad" : "chip neutral"}>{shortDate(etape.due_date)}</span>}
        {etape.responsable ? <Avatar member={etape.responsable} size={22} /> : <span className="nobody" title="Pas de responsable" />}
      </div>
      {open && (
        <div className="etape-edit">
          <input aria-label="Titre de l’étape" className="input" value={title} onChange={(e) => setTitle(e.target.value)}
            onBlur={() => title.trim() && title !== etape.title && update.mutate({ title })} />
          <div className="grid-cards" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 150px), 1fr))", gap: 10 }}>
            <div className="field">
              <label htmlFor={`e-resp-${etape.id}`}>Responsable</label>
              <select id={`e-resp-${etape.id}`} className="select" value={etape.responsable?.id ?? ""}
                onChange={(e) => update.mutate({ responsable_id: e.target.value ? Number(e.target.value) : null })}>
                <option value="">Personne</option>
                {members.filter((m) => m.active).map((m) => <option key={m.id} value={m.id}>{m.name}{m.kind === "agent" ? " (agent)" : ""}</option>)}
              </select>
            </div>
            <div className="field">
              <label htmlFor={`e-statut-${etape.id}`}>Statut</label>
              <select id={`e-statut-${etape.id}`} className="select" value={etape.status} onChange={(e) => update.mutate({ status: e.target.value as EtapeStatus })}>
                {STATUTS.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
              </select>
            </div>
            <div className="field">
              <label htmlFor={`e-debut-${etape.id}`}>Début</label>
              <input id={`e-debut-${etape.id}`} className="input" type="date" value={etape.start_date ?? ""}
                onChange={(e) => update.mutate({ start_date: e.target.value || null })} />
            </div>
            <div className="field">
              <label htmlFor={`e-fin-${etape.id}`}>Échéance</label>
              <input id={`e-fin-${etape.id}`} className="input" type="date" value={etape.due_date ?? ""}
                onChange={(e) => update.mutate({ due_date: e.target.value || null })} />
            </div>
          </div>
          <div className="field">
            <label htmlFor={`e-livrable-${etape.id}`}>Livrable attendu</label>
            <input id={`e-livrable-${etape.id}`} className="input" value={livrable} placeholder="Ex. : l’offre en PDF, validée"
              onChange={(e) => setLivrable(e.target.value)} onBlur={() => livrable !== etape.livrable && update.mutate({ livrable })} />
          </div>
          <div className="field">
            <label htmlFor={`e-notes-${etape.id}`}>Blocages, notes, preuves</label>
            <textarea id={`e-notes-${etape.id}`} className="textarea" style={{ minHeight: 70 }} value={notes}
              onChange={(e) => setNotes(e.target.value)} onBlur={() => notes !== etape.notes && update.mutate({ notes })} />
          </div>
          <button type="button" className="link-btn" style={{ alignSelf: "flex-start" }} disabled={archive.isPending} onClick={() => archive.mutate()}>
            Retirer cette étape
          </button>
        </div>
      )}
      {(update.error || archive.error) && <p className="notice bad" role="alert">{((update.error || archive.error) as ApiError).message}</p>}
    </li>
  );
}

/** Les sous-étapes d'une tâche (« 4.1 Finalisation de l'offre »…), avec responsable, livrable et échéance. */
export function Etapes({ tache, members }: { tache: Tache; members: Member[] }) {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const onSaved = (t: Tache) => queryClient.setQueryData<Tache[]>(["taches"], (list) => list?.map((x) => (x.id === t.id ? t : x)));
  const add = useMutation({
    mutationFn: (value: string) => api.addEtape(tache.id, { title: value }),
    onSuccess: (t) => {
      setTitle("");
      onSaved(t);
    },
  });
  const faites = tache.etapes.filter((e) => e.status === "fait").length;

  function submit(e: FormEvent) {
    e.preventDefault();
    if (title.trim()) add.mutate(title.trim());
  }

  return (
    <section className="field" aria-label="Sous-étapes">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
        <span style={{ fontSize: 13, fontWeight: 650 }}>Étapes</span>
        {tache.etapes.length > 0 && <span className="soft small">{faites} sur {tache.etapes.length} faites</span>}
      </div>
      {tache.etapes.length > 0 && (
        <div className="bar" aria-hidden="true"><span style={{ width: `${(faites / tache.etapes.length) * 100}%` }} /></div>
      )}
      <ul className="etapes">
        {tache.etapes.map((e) => <EtapeRow key={e.id} tache={tache} etape={e} members={members} onSaved={onSaved} />)}
      </ul>
      <form onSubmit={submit}>
        <label className="visually-hidden" htmlFor={`new-etape-${tache.id}`}>Nouvelle étape</label>
        <input id={`new-etape-${tache.id}`} className="input" placeholder="Ajouter une étape, puis Entrée" value={title} onChange={(e) => setTitle(e.target.value)} />
      </form>
      {add.error && <p className="notice bad" role="alert">{(add.error as ApiError).message}</p>}
    </section>
  );
}
