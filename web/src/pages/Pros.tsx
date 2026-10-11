import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "motion/react";
import { api, ApiError, type Member, type Pro, type ProAcces, type ProCategorie, type ProContrat, type ProInput } from "../api";
import { usePresence } from "../live";
import { Avatar } from "../components/Avatar";
import { IconClose, IconPlus, IconSearch } from "../components/Icons";

const CATEGORIES: { key: ProCategorie; label: string; tone: string }[] = [
  { key: "fondateur", label: "Fondateur", tone: "brand" },
  { key: "ambassadeur", label: "Ambassadeur", tone: "agent" },
  { key: "partenaire", label: "Partenaire", tone: "good" },
  { key: "prospect", label: "Prospect", tone: "neutral" },
];
const CONTRATS: { key: ProContrat; label: string }[] = [
  { key: "", label: "Pas renseigné" },
  { key: "a_envoyer", label: "À envoyer" },
  { key: "en_attente", label: "En attente" },
  { key: "signe", label: "Signé" },
  { key: "non_requis", label: "Pas nécessaire" },
];
const ACCES: { key: ProAcces; label: string }[] = [
  { key: "", label: "Pas renseigné" },
  { key: "a_envoyer", label: "Lien à envoyer" },
  { key: "envoye", label: "Lien envoyé" },
  { key: "installe", label: "App installée" },
  { key: "actif", label: "Teste l’app" },
];
const categorie = (k: ProCategorie) => CATEGORIES.find((c) => c.key === k) ?? CATEGORIES[3];

function MemberSelect({ id, members, value, onChange }: { id: string; members: Member[]; value: number | null; onChange: (v: number | null) => void }) {
  return (
    <select id={id} className="select" value={value ?? ""} onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}>
      <option value="">Personne</option>
      {members.filter((m) => m.active && m.kind === "humain").map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
    </select>
  );
}

function ProDrawer({ pro, members, onClose }: { pro: Pro | null; members: Member[]; onClose: () => void }) {
  const queryClient = useQueryClient();
  const creating = pro === null;
  const [form, setForm] = useState<ProInput>(() => ({
    nom: pro?.nom ?? "",
    categorie: pro?.categorie ?? "partenaire",
    enseigne: pro?.enseigne ?? "",
    audience: pro?.audience ?? "",
    telephone: pro?.telephone ?? "",
    email: pro?.email ?? "",
    contrat: pro?.contrat ?? "",
    acces_test: pro?.acces_test ?? "a_envoyer",
    notes: pro?.notes ?? "",
    suivi_par_id: pro?.suivi_par?.id ?? null,
  }));
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["pros"] });
  const save = useMutation({
    mutationFn: () => (creating ? api.createPro(form) : api.updatePro(pro.id, form)),
    onSuccess: () => {
      refresh();
      onClose();
    },
  });
  const archive = useMutation({
    mutationFn: () => api.archivePro(pro!.id),
    onSuccess: () => {
      refresh();
      onClose();
    },
  });
  const set = <K extends keyof ProInput>(key: K, value: ProInput[K]) => setForm((f) => ({ ...f, [key]: value }));

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  function submit(e: FormEvent) {
    e.preventDefault();
    if (form.nom.trim()) save.mutate();
  }

  return (
    <div className="drawer-wrap" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <motion.form className="drawer" onSubmit={submit} aria-label={creating ? "Ajouter une pro" : `Fiche : ${pro.enseigne || pro.nom}`}
        initial={{ x: 60, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ type: "spring", stiffness: 360, damping: 34 }}>
        <div className="card-head">
          <span className="eyebrow">{creating ? "Nouvelle fiche" : `Fiche${pro.numero ? ` n° ${pro.numero}` : ""}`}</span>
          <button type="button" className="icon-btn light" onClick={onClose} aria-label="Fermer"><IconClose /></button>
        </div>
        <div className="grid-cards" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 220px), 1fr))", gap: 12 }}>
          <div className="field">
            <label htmlFor="p-enseigne">Salon ou nom d’utilisateur</label>
            <input id="p-enseigne" className="input" maxLength={120} value={form.enseigne} onChange={(e) => set("enseigne", e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="p-nom">Nom et prénoms</label>
            <input id="p-nom" className="input" required maxLength={120} value={form.nom} onChange={(e) => set("nom", e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="p-cat">Catégorie</label>
            <select id="p-cat" className="select" value={form.categorie} onChange={(e) => set("categorie", e.target.value as ProCategorie)}>
              {CATEGORIES.map((c) => <option key={c.key} value={c.key}>{c.label}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="p-audience">Audience</label>
            <input id="p-audience" className="input" maxLength={40} placeholder="Ex. : 10K - 30K" value={form.audience} onChange={(e) => set("audience", e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="p-tel">Téléphone</label>
            <input id="p-tel" className="input" type="tel" maxLength={40} value={form.telephone} onChange={(e) => set("telephone", e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="p-mail">Email pour l’accès aux tests</label>
            <input id="p-mail" className="input" type="email" maxLength={254} value={form.email} onChange={(e) => set("email", e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="p-contrat">Contrat / NDA</label>
            <select id="p-contrat" className="select" value={form.contrat} onChange={(e) => set("contrat", e.target.value as ProContrat)}>
              {CONTRATS.map((c) => <option key={c.key} value={c.key}>{c.label}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="p-acces">Accès aux tests</label>
            <select id="p-acces" className="select" value={form.acces_test} onChange={(e) => set("acces_test", e.target.value as ProAcces)}>
              {ACCES.map((a) => <option key={a.key} value={a.key}>{a.label}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="p-suivi">Suivie par</label>
            <MemberSelect id="p-suivi" members={members} value={form.suivi_par_id ?? null} onChange={(v) => set("suivi_par_id", v)} />
          </div>
        </div>
        <div className="field">
          <label htmlFor="p-notes">Notes</label>
          <textarea id="p-notes" className="textarea" style={{ minHeight: 90 }} value={form.notes} onChange={(e) => set("notes", e.target.value)} />
        </div>
        {(save.error || archive.error) && <p className="notice bad" role="alert">{((save.error || archive.error) as ApiError).message}</p>}
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button type="submit" className="btn brand" disabled={save.isPending}>{creating ? "Ajouter au panel" : "Enregistrer"}</button>
          {!creating && <button type="button" className="btn" disabled={archive.isPending} onClick={() => archive.mutate()}>Retirer du panel</button>}
        </div>
      </motion.form>
    </div>
  );
}

export function Pros() {
  usePresence({ piece: "bureaux", label: "regarde le panel des pros" });
  const queryClient = useQueryClient();
  const [params, setParams] = useSearchParams();
  const pros = useQuery({ queryKey: ["pros"], queryFn: api.pros });
  const members = useQuery({ queryKey: ["membres"], queryFn: api.members });
  const [cat, setCat] = useState<ProCategorie | "tous">("tous");
  const [acces, setAcces] = useState<ProAcces | "tous">("tous");
  const [q, setQ] = useState("");
  const [creating, setCreating] = useState(false);
  const all = pros.data ?? [];
  const memberList = members.data ?? [];
  const selectedId = Number(params.get("fiche")) || null;
  const selected = all.find((p) => p.id === selectedId) ?? null;

  const update = useMutation({
    mutationFn: ({ id, changes }: { id: number; changes: Partial<ProInput> }) => api.updatePro(id, changes),
    onSuccess: (p) => queryClient.setQueryData<Pro[]>(["pros"], (list) => list?.map((x) => (x.id === p.id ? p : x))),
  });

  const visibles = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return all
      .filter((p) => cat === "tous" || p.categorie === cat)
      .filter((p) => acces === "tous" || p.acces_test === acces)
      .filter((p) => !needle || [p.nom, p.enseigne, p.email, p.telephone].some((v) => v.toLowerCase().includes(needle)));
  }, [all, cat, acces, q]);

  function open(id: number | null) {
    const next = new URLSearchParams(params);
    if (id) next.set("fiche", String(id));
    else next.delete("fiche");
    setParams(next, { replace: true });
  }

  const count = (f: (p: Pro) => boolean) => all.filter(f).length;
  const envoyes = count((p) => ["envoye", "installe", "actif"].includes(p.acces_test));

  return (
    <div className="page" style={{ maxWidth: 1400 }}>
      <header style={{ display: "flex", flexWrap: "wrap", alignItems: "flex-end", justifyContent: "space-between", gap: 16, paddingTop: 8 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <span className="eyebrow">La maison</span>
          <h1 className="display">Le panel des pros</h1>
          <p className="soft" style={{ fontSize: 16, maxWidth: "64ch" }}>
            Les salons, coiffeuses et barbiers avec qui Nyuman démarre les tests : fondateurs, ambassadeurs, partenaires. On suit ici les contrats et les accès à l’app.
          </p>
        </div>
        <button type="button" className="btn brand" onClick={() => setCreating(true)}><IconPlus /> Ajouter une pro</button>
      </header>

      <p className="notice small" role="note">
        Données personnelles (téléphones, emails) : visibles seulement par l’équipe connectée. Ne pas les copier ailleurs. Aucun agent n’y a accès sans votre accord.
      </p>

      <div className="grid-cards" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 200px), 1fr))" }}>
        <div className="card kpi"><span className="eyebrow">Dans le panel</span><span className="kpi-value">{all.length}</span></div>
        <div className="card kpi"><span className="eyebrow">Fondateurs</span><span className="kpi-value">{count((p) => p.categorie === "fondateur")}</span></div>
        <div className="card kpi">
          <span className="eyebrow">Accès envoyés</span>
          <span className="kpi-value">{envoyes}<span className="kpi-unit"> sur {all.length}</span></span>
        </div>
        <div className="card kpi">
          <span className="eyebrow">Contrats signés</span>
          <span className="kpi-value">{count((p) => p.contrat === "signe")}<span className="kpi-unit"> · {count((p) => p.contrat === "en_attente")} en attente</span></span>
        </div>
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 10 }}>
        <div className="segmented" role="group" aria-label="Catégorie" style={{ flexWrap: "wrap" }}>
          <button type="button" aria-pressed={cat === "tous"} onClick={() => setCat("tous")}>Toutes · {all.length}</button>
          {CATEGORIES.filter((c) => all.some((p) => p.categorie === c.key)).map((c) => (
            <button key={c.key} type="button" aria-pressed={cat === c.key} onClick={() => setCat(c.key)}>
              {c.label}s · {count((p) => p.categorie === c.key)}
            </button>
          ))}
        </div>
        <label className="visually-hidden" htmlFor="pros-acces">Accès aux tests</label>
        <select id="pros-acces" className="select" style={{ width: "auto", minHeight: 40 }} value={acces} onChange={(e) => setAcces(e.target.value as ProAcces | "tous")}>
          <option value="tous">Tous les accès</option>
          {ACCES.map((a) => <option key={a.key} value={a.key}>{a.label}</option>)}
        </select>
        <div className="search" style={{ flex: "1 1 220px", maxWidth: 360 }}>
          <IconSearch />
          <label className="visually-hidden" htmlFor="pros-q">Chercher</label>
          <input id="pros-q" className="input" placeholder="Chercher un nom, un salon…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
      </div>

      <div className="pros-table-wrap">
        <table className="pros-table">
          <thead>
            <tr>
              <th scope="col">Pro</th>
              <th scope="col">Catégorie</th>
              <th scope="col">Audience</th>
              <th scope="col">Contact</th>
              <th scope="col">Contrat / NDA</th>
              <th scope="col">Accès aux tests</th>
              <th scope="col">Suivie par</th>
            </tr>
          </thead>
          <tbody>
            {visibles.map((p) => (
              <tr key={p.id}>
                <td>
                  <button type="button" className="pro-name" onClick={() => open(p.id)}>
                    <strong>{p.enseigne || p.nom}</strong>
                    {p.enseigne && <span className="soft small">{p.nom}</span>}
                  </button>
                </td>
                <td><span className={`chip ${categorie(p.categorie).tone}`}>{categorie(p.categorie).label}</span></td>
                <td className="mono small">{p.audience || "—"}</td>
                <td className="small">
                  <span style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                    {p.telephone && <a href={`tel:${p.telephone.replace(/\s/g, "")}`}>{p.telephone}</a>}
                    {p.email && <a href={`mailto:${p.email}`}>{p.email}</a>}
                    {!p.telephone && !p.email && <span className="soft">—</span>}
                  </span>
                </td>
                <td>
                  <label className="visually-hidden" htmlFor={`contrat-${p.id}`}>Contrat de {p.enseigne || p.nom}</label>
                  <select id={`contrat-${p.id}`} className="select compact" value={p.contrat}
                    onChange={(e) => update.mutate({ id: p.id, changes: { contrat: e.target.value as ProContrat } })}>
                    {CONTRATS.map((c) => <option key={c.key} value={c.key}>{c.label}</option>)}
                  </select>
                </td>
                <td>
                  <label className="visually-hidden" htmlFor={`acces-${p.id}`}>Accès aux tests de {p.enseigne || p.nom}</label>
                  <select id={`acces-${p.id}`} className={`select compact acces-${p.acces_test || "vide"}`} value={p.acces_test}
                    onChange={(e) => update.mutate({ id: p.id, changes: { acces_test: e.target.value as ProAcces } })}>
                    {ACCES.map((a) => <option key={a.key} value={a.key}>{a.label}</option>)}
                  </select>
                </td>
                <td>{p.suivi_par ? <Avatar member={p.suivi_par} size={26} /> : <span className="nobody" title="Personne" />}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {pros.data && visibles.length === 0 && (
          <p className="soft" style={{ padding: 16 }}>
            {all.length === 0 ? "Le panel est vide. Ajoute une pro, ou reprends le tableau Google depuis les réglages." : "Personne ne correspond à ces filtres."}
          </p>
        )}
      </div>
      {update.error && <p className="notice bad" role="alert">{(update.error as ApiError).message}</p>}

      {(selected || creating) && (
        <ProDrawer key={selected?.id ?? "nouveau"} pro={creating ? null : selected} members={memberList}
          onClose={() => { setCreating(false); open(null); }} />
      )}
    </div>
  );
}
