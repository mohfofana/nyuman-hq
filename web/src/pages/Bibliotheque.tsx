import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "motion/react";
import { api, CATEGORIES, type Member } from "../api";
import { formatAgo } from "../format";
import { useLive, usePresence } from "../live";
import { Avatar } from "../components/Avatar";
import { IconPlus, IconSearch } from "../components/Icons";

export function categoryLabel(key: string) {
  return CATEGORIES.find((c) => c.key === key)?.label ?? key;
}

/** Une couleur par rayon, pour reconnaître un document d'un coup d'œil. */
export const CATEGORY_COLORS: Record<string, { bg: string; fg: string }> = {
  cerveau: { bg: "#f7e2cb", fg: "#9c4f0a" },
  contrats: { bg: "#e5e8f7", fg: "#4150a8" },
  finances: { bg: "#e1f0e7", fg: "#2f7a57" },
  "comptes-rendus": { bg: "#faefd3", fg: "#7f5a00" },
  specs: { bg: "#ede3d4", fg: "#5b4d43" },
  pitch: { bg: "#f8e1da", fg: "#a33a22" },
  autre: { bg: "#f6f0e7", fg: "#5b4d43" },
};

export function CategoryChip({ category }: { category: string }) {
  const c = CATEGORY_COLORS[category] ?? CATEGORY_COLORS.autre;
  return <span className="chip" style={{ background: c.bg, color: c.fg }}>{categoryLabel(category)}</span>;
}

function useDebounced<T>(value: T, ms = 250): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = window.setTimeout(() => setV(value), ms);
    return () => window.clearTimeout(t);
  }, [value, ms]);
  return v;
}

export function Bibliotheque() {
  usePresence({ piece: "bibliotheque", label: "parcourt la bibliothèque" });
  const { presences } = useLive();
  const [categorie, setCategorie] = useState<string>("");
  const [q, setQ] = useState("");
  const [archives, setArchives] = useState(false);
  const query = useDebounced(q.trim());

  const docs = useQuery({
    queryKey: ["documents", "", query, archives],
    queryFn: () => api.documents({ q: query || undefined, archives }),
  });
  const members = useQuery({ queryKey: ["membres"], queryFn: api.members });

  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const d of docs.data ?? []) c[d.category] = (c[d.category] ?? 0) + 1;
    return c;
  }, [docs.data]);
  const shown = (docs.data ?? []).filter((d) => !categorie || d.category === categorie);

  const readersOf = (docId: number): Member[] =>
    (members.data ?? []).filter((m) => presences[m.id]?.document_id === docId);

  return (
    <div className="page">
      <header style={{ display: "flex", flexWrap: "wrap", alignItems: "flex-end", justifyContent: "space-between", gap: 16, paddingTop: 8 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <span className="eyebrow">La maison</span>
          <h1 className="display">La bibliothèque</h1>
          <p className="soft" style={{ fontSize: 16, maxWidth: "58ch" }}>
            Contrats, finances, comptes rendus, specs, pitch. Chaque version est gardée, on voit qui a modifié quoi.
          </p>
        </div>
        <Link to="/bibliotheque/nouveau" className="btn primary"><IconPlus /> Nouveau document</Link>
      </header>

      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <div className="search" style={{ maxWidth: 520 }}>
          <IconSearch />
          <label className="visually-hidden" htmlFor="doc-search">Chercher dans la bibliothèque</label>
          <input id="doc-search" className="input" type="search" placeholder="Chercher un titre ou un mot dans les documents" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }} role="group" aria-label="Rayons">
          <button type="button" className={categorie === "" ? "btn small primary" : "btn small"} aria-pressed={categorie === ""} onClick={() => setCategorie("")}>
            Tous · {docs.data?.length ?? 0}
          </button>
          {CATEGORIES.filter((c) => counts[c.key]).map((c) => (
            <button key={c.key} type="button" className={categorie === c.key ? "btn small primary" : "btn small"} aria-pressed={categorie === c.key} onClick={() => setCategorie(c.key)}>
              {c.label} · {counts[c.key]}
            </button>
          ))}
          <button type="button" className={archives ? "btn small brand" : "btn small"} aria-pressed={archives} onClick={() => setArchives(!archives)} style={{ marginLeft: "auto" }}>
            {archives ? "Retour aux documents" : "Corbeille"}
          </button>
        </div>
      </div>

      {docs.isLoading && <p className="soft">Chargement…</p>}
      {docs.data && shown.length === 0 && (
        <div className="card" style={{ alignItems: "flex-start" }}>
          <p className="title">{archives ? "La corbeille est vide." : query ? `Rien ne parle de « ${query} ».` : "Aucun document ici pour l’instant."}</p>
          {!archives && <Link to="/bibliotheque/nouveau" className="btn small">Écrire le premier</Link>}
        </div>
      )}

      <motion.div className="grid-cards" layout>
        <AnimatePresence>
          {shown.map((d) => {
            const readers = readersOf(d.id);
            return (
              <motion.div key={d.id} layout initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, scale: 0.97 }}>
                <Link to={`/bibliotheque/${d.id}`} className="card doc-card" style={{ height: "100%" }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
                    <CategoryChip category={d.category} />
                    {readers.length > 0 && (
                      <span style={{ display: "flex", alignItems: "center", gap: 6 }} className="soft small">
                        {readers.slice(0, 3).map((m) => <Avatar key={m.id} member={m} size={22} ring={presences[m.id]?.editing ? "#bc600d" : "#2f7a57"} />)}
                        {readers.some((m) => presences[m.id]?.editing) ? "en train d’écrire" : "en lecture"}
                      </span>
                    )}
                  </div>
                  <h2 style={{ fontSize: 19, fontWeight: 750, letterSpacing: "-0.02em" }}>{d.title}</h2>
                  {d.excerpt && <p className="doc-excerpt">{d.excerpt}</p>}
                  <div className="doc-foot">
                    <Avatar member={d.updated_by} size={22} />
                    <span>{d.updated_by.name} · {formatAgo(d.updated_at)}</span>
                    <span className="mono" style={{ marginLeft: "auto" }}>v{d.version}</span>
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
