import { useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api, ApiError, CATEGORIES, type Category, type DocumentFull, type DocumentInput } from "../api";
import { firstName, formatAgo, formatDateTime } from "../format";
import { useLive, usePresence } from "../live";
import { Avatar } from "../components/Avatar";
import { CategoryChip, categoryLabel } from "./Bibliotheque";

// Le HTML brut est ignoré par ReactMarkdown : un document ne peut pas injecter de script.
function Markdown({ text }: { text: string }) {
  return (
    <div className="prose">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
    </div>
  );
}

function Editor({ doc, onSaved, onCancel }: {
  doc: DocumentFull | null;
  onSaved: (d: DocumentFull) => void;
  onCancel: () => void;
}) {
  const [form, setForm] = useState<DocumentInput>({
    title: doc?.title ?? "",
    category: doc?.category ?? "autre",
    content: doc?.content ?? "",
  });
  const save = useMutation({
    mutationFn: (input: DocumentInput) =>
      doc ? api.updateDocument(doc.id, { ...input, base_version: doc.version }) : api.createDocument(input),
    onSuccess: onSaved,
  });
  const conflict = save.error instanceof ApiError && save.error.status === 409;

  function submit(e: FormEvent) {
    e.preventDefault();
    save.mutate(form);
  }

  return (
    <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <input
        aria-label="Titre du document"
        className="input"
        required
        maxLength={200}
        placeholder="Titre du document"
        value={form.title}
        onChange={(e) => setForm({ ...form, title: e.target.value })}
        style={{ fontSize: 28, fontWeight: 800, minHeight: 64, letterSpacing: "-0.03em" }}
      />
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }} role="group" aria-label="Rayon">
        {CATEGORIES.map((c) => (
          <button key={c.key} type="button" className={form.category === c.key ? "btn small primary" : "btn small"} aria-pressed={form.category === c.key}
            onClick={() => setForm({ ...form, category: c.key as Category })}>
            {c.label}
          </button>
        ))}
      </div>

      <div className="row" style={{ gap: 16 }}>
        <div className="field" style={{ flex: "1 1 400px", minWidth: 0 }}>
          <label htmlFor="doc-content">Texte <span className="soft" style={{ fontWeight: 400 }}>· Markdown : # titre, **gras**, - liste, | tableau |</span></label>
          <textarea id="doc-content" className="textarea" value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} />
        </div>
        <div style={{ flex: "1 1 400px", minWidth: 0, display: "flex", flexDirection: "column", gap: 6 }}>
          <span style={{ fontSize: 13, fontWeight: 650 }}>Aperçu</span>
          <div className="card" style={{ minHeight: 420, padding: 24 }}>
            {form.content.trim() ? <Markdown text={form.content} /> : <p className="soft">L’aperçu s’affiche ici pendant que tu écris.</p>}
          </div>
        </div>
      </div>

      {conflict ? (
        <p className="notice bad" role="alert">
          Quelqu’un a enregistré ce document pendant que tu écrivais. Copie ton texte, recharge la page pour voir sa version, puis refais tes changements.
        </p>
      ) : save.error ? (
        <p className="notice bad" role="alert">{(save.error as ApiError).message}</p>
      ) : null}

      <div className="card" style={{ position: "sticky", bottom: 12, flexDirection: "row", flexWrap: "wrap", alignItems: "center", gap: 10, padding: "12px 16px" }}>
        <button type="submit" className="btn primary" disabled={save.isPending}>
          {doc ? `Enregistrer la version ${doc.version + 1}` : "Créer le document"}
        </button>
        <button type="button" className="btn" onClick={onCancel}>Annuler</button>
        <span className="soft small" style={{ marginLeft: "auto" }}>Rien n’est perdu : chaque version reste dans l’historique.</span>
      </div>
    </form>
  );
}

function History({ doc }: { doc: DocumentFull }) {
  const versions = useQuery({ queryKey: ["versions", doc.id, doc.version], queryFn: () => api.versions(doc.id) });
  const [open, setOpen] = useState<number | null>(null);
  const old = useQuery({
    queryKey: ["version", doc.id, open],
    queryFn: () => api.version(doc.id, open as number),
    enabled: open !== null,
  });

  return (
    <section className="card" aria-labelledby="historique" style={{ gap: 12 }}>
      <h2 id="historique" className="title">Historique</h2>
      <ol className="timeline">
        {(versions.data ?? []).map((v) => (
          <li key={v.version} style={{ position: "relative" }}>
            <button type="button" onClick={() => setOpen(open === v.version ? null : v.version)} aria-expanded={open === v.version}
              style={{
                width: "100%", textAlign: "left", display: "flex", alignItems: "center", gap: 12,
                padding: "8px 8px 8px 0", borderRadius: 12, border: "none", cursor: "pointer",
                background: open === v.version ? "var(--paper)" : "transparent",
              }}>
              <Avatar member={v.author} size={28} ring={v.version === doc.version ? "#bc600d" : undefined} />
              <span style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
                <span style={{ fontSize: 14, fontWeight: 650 }}>Version {v.version}{v.version === doc.version ? " · actuelle" : ""}</span>
                <span className="soft" style={{ fontSize: 12.5 }}>{v.author.name} · {formatDateTime(v.created_at)}</span>
              </span>
            </button>
          </li>
        ))}
      </ol>
      {open !== null && old.data && (
        <div style={{ borderTop: "1px solid var(--line)", paddingTop: 14, display: "flex", flexDirection: "column", gap: 8 }}>
          <span className="eyebrow">Version {old.data.version} · « {old.data.title} »</span>
          <Markdown text={old.data.content} />
        </div>
      )}
    </section>
  );
}

export function NewDocument() {
  usePresence({ piece: "bibliotheque", label: "écrit un nouveau document" });
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  return (
    <div className="page">
      <span className="soft small"><Link to="/bibliotheque" style={{ color: "var(--ink-2)" }}>La bibliothèque</Link> › Nouveau</span>
      <Editor
        doc={null}
        onCancel={() => navigate("/bibliotheque")}
        onSaved={(d) => {
          queryClient.invalidateQueries({ queryKey: ["documents"] });
          navigate(`/bibliotheque/${d.id}`);
        }}
      />
    </div>
  );
}

export function DocumentPage() {
  const id = Number(useParams().id);
  const queryClient = useQueryClient();
  const { me, presences } = useLive();
  const doc = useQuery({ queryKey: ["document", id], queryFn: () => api.document(id) });
  const members = useQuery({ queryKey: ["membres"], queryFn: api.members });
  const [editing, setEditing] = useState(false);

  const title = doc.data?.title;
  usePresence(title ? { piece: "bibliotheque", label: `${editing ? "modifie" : "lit"} « ${title} »`, document_id: id, editing } : null);

  const refresh = (d: DocumentFull) => {
    queryClient.setQueryData(["document", id], d);
    queryClient.invalidateQueries({ queryKey: ["documents"] });
  };
  const archive = useMutation({ mutationFn: () => api.archiveDocument(id), onSuccess: refresh });
  const restore = useMutation({ mutationFn: () => api.restoreDocument(id), onSuccess: refresh });

  const others = (members.data ?? []).filter((m) => m.id !== me.id && presences[m.id]?.document_id === id);
  const othersEditing = others.filter((m) => presences[m.id]?.editing);

  if (doc.isLoading) return <div className="page"><p className="soft">Chargement…</p></div>;
  if (doc.error || !doc.data) {
    return (
      <div className="page">
        <p className="notice bad">{doc.error instanceof ApiError ? doc.error.message : "Document introuvable."}</p>
        <Link to="/bibliotheque">Retour à la bibliothèque</Link>
      </div>
    );
  }
  const d = doc.data;

  const presenceBar = others.length > 0 && (
    <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 10 }}>
      <span className="soft small">Ici en ce moment :</span>
      {others.map((m) => (
        <span key={m.id} style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 13.5 }}>
          <Avatar member={m} size={26} ring={presences[m.id]?.editing ? "#bc600d" : "#2f7a57"} />
          {firstName(m.name)} <span className="soft">{presences[m.id]?.editing ? "écrit" : "lit"}</span>
        </span>
      ))}
    </div>
  );
  const editWarning = othersEditing.length > 0 && (
    <p className="notice" role="status">
      {othersEditing.map((m) => firstName(m.name)).join(" et ")} {othersEditing.length > 1 ? "sont" : "est"} en train de modifier ce document.
      Attends {othersEditing.length > 1 ? "qu’ils aient" : "qu’il ait"} enregistré pour ne pas vous marcher dessus.
    </p>
  );

  return (
    <div className="page">
      <span className="soft small"><Link to="/bibliotheque" style={{ color: "var(--ink-2)" }}>La bibliothèque</Link> › {categoryLabel(d.category)}</span>
      {editing ? (
        <>
          {editWarning}
          <Editor doc={d} onCancel={() => setEditing(false)} onSaved={(nd) => { refresh(nd); setEditing(false); }} />
        </>
      ) : (
        <div className="row">
          <div className="col-main">
            <header style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
                <CategoryChip category={d.category} />
                {d.archived && <span className="chip wait">Dans la corbeille</span>}
              </div>
              <h1 className="display" style={{ fontSize: "clamp(30px, 4vw, 46px)" }}>{d.title}</h1>
              <span className="soft small" style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Avatar member={d.updated_by} size={24} />
                Version {d.version}, modifiée par {d.updated_by.name} {formatAgo(d.updated_at)}
              </span>
              {presenceBar}
              {editWarning}
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {!d.archived && <button type="button" className="btn primary" onClick={() => setEditing(true)}>Modifier</button>}
                {d.archived ? (
                  <button type="button" className="btn" onClick={() => restore.mutate()} disabled={restore.isPending}>Restaurer</button>
                ) : (
                  <button type="button" className="btn" onClick={() => archive.mutate()} disabled={archive.isPending}>Mettre à la corbeille</button>
                )}
              </div>
            </header>
            <article className="card" style={{ padding: "32px clamp(20px, 4vw, 44px)" }}>
              {d.content.trim() ? <Markdown text={d.content} /> : <p className="soft">Ce document est vide.</p>}
            </article>
          </div>
          <div className="col-side" style={{ flexBasis: 300 }}>
            <History doc={d} />
          </div>
        </div>
      )}
    </div>
  );
}
