import { useEffect, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "motion/react";
import {
  api,
  ApiError,
  type Decision,
  type DecisionChanges,
  type DecisionInput,
  type DecisionStatut,
  type Member,
  type Pole,
  type Verdict,
  type VoteValeur,
} from "../api";
import { POLES, PoleChip } from "../poles";
import { firstName } from "../format";
import { useLive, usePresence } from "../live";
import { Avatar } from "../components/Avatar";
import { IconClose, IconPlus } from "../components/Icons";

export const STATUTS: { key: DecisionStatut; label: string; tone: string }[] = [
  { key: "nouveau", label: "Sur la table", tone: "brand" },
  { key: "a_initier", label: "À initier", tone: "neutral" },
  { key: "en_cours", label: "En cours", tone: "wait" },
  { key: "valide", label: "Validé", tone: "good" },
  { key: "ajourne", label: "Ajourné", tone: "neutral" },
  { key: "refuse", label: "Refusé", tone: "bad" },
];
const statutOf = (s: DecisionStatut) => STATUTS.find((x) => x.key === s) ?? STATUTS[0];
const VOTES: { key: VoteValeur; label: string; tone: string }[] = [
  { key: "pour", label: "Pour", tone: "good" },
  { key: "contre", label: "Contre", tone: "bad" },
  { key: "abstention", label: "Abstention", tone: "neutral" },
];
const VERDICTS: { key: Verdict; label: string; tone: string }[] = [
  { key: "bonne", label: "C’était la bonne décision", tone: "good" },
  { key: "mitigee", label: "Mitigé", tone: "wait" },
  { key: "mauvaise", label: "Il fallait faire autrement", tone: "bad" },
];

type Onglet = "table" | "route" | "journal";
const ONGLETS: { key: Onglet; label: string; statuts: DecisionStatut[] }[] = [
  { key: "table", label: "Sur la table", statuts: ["nouveau"] },
  { key: "route", label: "En route", statuts: ["a_initier", "en_cours"] },
  { key: "journal", label: "Journal des décisions", statuts: ["valide", "refuse", "ajourne"] },
];

function jour(iso: string | null): string {
  if (!iso) return "";
  const d = iso.length === 10 ? new Date(`${iso}T12:00:00`) : new Date(iso);
  return d.toLocaleDateString("fr-FR", { day: "numeric", month: "long" });
}

function VotesResume({ decision }: { decision: Decision }) {
  if (decision.votes.length === 0) return <span className="soft small">Pas encore de vote</span>;
  const count = (v: VoteValeur) => decision.votes.filter((x) => x.vote === v).length;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
      <span className="faces-row">{decision.votes.map((v) => <Avatar key={v.membre.id} member={v.membre} size={22} />)}</span>
      <span className="small" style={{ fontWeight: 600 }}>
        {[count("pour") && `${count("pour")} pour`, count("contre") && `${count("contre")} contre`, count("abstention") && `${count("abstention")} abst.`]
          .filter(Boolean)
          .join(" · ")}
      </span>
    </span>
  );
}

function DecisionCard({ decision, onOpen }: { decision: Decision; onOpen: () => void }) {
  const s = statutOf(decision.statut);
  return (
    <motion.button layout type="button" className="card decision-card" onClick={onOpen}
      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <span style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
        <span className={`chip ${s.tone}`}>{s.label}</span>
        {decision.a_revoir && <span className="chip brand">à revoir</span>}
        {decision.bilan_verdict && <span className={`chip ${VERDICTS.find((v) => v.key === decision.bilan_verdict)?.tone}`}>bilan fait</span>}
        <span className="mono" style={{ marginLeft: "auto", fontSize: 11.5, color: "var(--ink-2)" }}>{jour(decision.date_demande)}</span>
      </span>
      <span className="decision-title">{decision.titre}</span>
      {(decision.decision || decision.demande) && <span className="decision-excerpt">{decision.decision || decision.demande}</span>}
      <span style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center", marginTop: "auto" }}>
        {(decision.poles_en_charge.length ? decision.poles_en_charge : [decision.pole_concerne]).map((p) => <PoleChip key={p} pole={p} />)}
        <span style={{ marginLeft: "auto" }}><VotesResume decision={decision} /></span>
      </span>
    </motion.button>
  );
}

function PolesPicker({ value, onChange }: { value: Exclude<Pole, "">[]; onChange: (v: Exclude<Pole, "">[]) => void }) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }} role="group" aria-label="Pôles en charge">
      {POLES.map((p) => {
        const on = value.includes(p.key);
        return (
          <button key={p.key} type="button" aria-pressed={on} className="chip-toggle"
            style={on ? { background: p.color.bg, color: p.color.fg, borderColor: p.color.fg } : undefined}
            onClick={() => onChange(on ? value.filter((x) => x !== p.key) : [...value, p.key])}>
            {p.label}
          </button>
        );
      })}
    </div>
  );
}

function TexteSujet({ label, value, editable, placeholder, onSave, rows = 3 }: {
  label: string;
  value: string;
  editable: boolean;
  placeholder: string;
  onSave: (v: string) => void;
  rows?: number;
}) {
  const [draft, setDraft] = useState(value);
  useEffect(() => setDraft(value), [value]);
  const id = `sujet-${label.replace(/\W+/g, "-")}`;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      {editable ? (
        <textarea id={id} className="textarea" rows={rows} style={{ minHeight: rows * 26 }} placeholder={placeholder} value={draft}
          onChange={(e) => setDraft(e.target.value)} onBlur={() => draft !== value && onSave(draft)} />
      ) : value ? (
        <p id={id} style={{ whiteSpace: "pre-wrap", fontSize: 14.5 }}>{value}</p>
      ) : (
        <p id={id} className="soft small">Pas renseigné.</p>
      )}
    </div>
  );
}

function DecisionDrawer({ decision, me, onClose }: { decision: Decision; me: Member; onClose: () => void }) {
  const queryClient = useQueryClient();
  const isHead = me.role === "head";
  const canEdit = isHead || decision.author.id === me.id;
  const tranche = decision.statut === "valide" || decision.statut === "refuse";
  const myVote = decision.votes.find((v) => v.membre.id === me.id);
  const [titre, setTitre] = useState(decision.titre);
  const [commentaire, setCommentaire] = useState(myVote?.commentaire ?? "");
  const [verdict, setVerdict] = useState<Verdict | null>(null);
  const [bilan, setBilan] = useState("");
  const onSaved = (d: Decision) => queryClient.setQueryData<Decision[]>(["decisions"], (list) => list?.map((x) => (x.id === d.id ? d : x)));
  const update = useMutation({ mutationFn: (c: DecisionChanges) => api.updateDecision(decision.id, c), onSuccess: onSaved });
  const vote = useMutation({ mutationFn: (v: VoteValeur) => api.voteDecision(decision.id, v, commentaire), onSuccess: onSaved });
  const saveBilan = useMutation({ mutationFn: () => api.bilanDecision(decision.id, verdict!, bilan), onSuccess: onSaved });
  const archive = useMutation({
    mutationFn: () => api.archiveDecision(decision.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["decisions"] });
      onClose();
    },
  });
  const error = update.error || vote.error || saveBilan.error || archive.error;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="drawer-wrap" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <motion.aside className="drawer" role="dialog" aria-modal="true" aria-label={`Sujet : ${decision.titre}`}
        initial={{ x: 60, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ type: "spring", stiffness: 360, damping: 34 }}>
        <div className="card-head">
          <span className="eyebrow">Sujet n° {decision.id} · {firstName(decision.author.name)}, {jour(decision.date_demande)}</span>
          <button type="button" className="icon-btn light" onClick={onClose} aria-label="Fermer"><IconClose /></button>
        </div>

        {canEdit ? (
          <input aria-label="Titre du sujet" className="input" value={titre} onChange={(e) => setTitre(e.target.value)}
            onBlur={() => titre.trim() && titre !== decision.titre && update.mutate({ titre })}
            style={{ fontSize: 22, fontWeight: 800, minHeight: 56, letterSpacing: "-0.02em" }} />
        ) : (
          <h2 style={{ fontSize: 22, fontWeight: 800, letterSpacing: "-0.02em" }}>{decision.titre}</h2>
        )}

        {isHead ? (
          <div className="field">
            <span style={{ fontSize: 13, fontWeight: 650 }}>Trancher</span>
            <div className="segmented" role="group" aria-label="Statut du sujet" style={{ alignSelf: "flex-start", flexWrap: "wrap" }}>
              {STATUTS.map((s) => (
                <button key={s.key} type="button" aria-pressed={decision.statut === s.key} onClick={() => update.mutate({ statut: s.key })}>{s.label}</button>
              ))}
            </div>
          </div>
        ) : (
          <span className={`chip ${statutOf(decision.statut).tone}`} style={{ alignSelf: "flex-start" }}>{statutOf(decision.statut).label}</span>
        )}
        {decision.decided_by && decision.decided_at && (
          <p className="soft small">Tranché par {decision.decided_by.name} le {jour(decision.decided_at)}.</p>
        )}

        <TexteSujet label="Décision actée" value={decision.decision} editable={isHead} rows={3}
          placeholder="Ce qui a été décidé, et par qui c’est porté." onSave={(v) => update.mutate({ decision: v })} />
        <TexteSujet label="La demande" value={decision.demande} editable={canEdit} rows={4}
          placeholder="Le sujet en détail : le contexte, la question posée." onSave={(v) => update.mutate({ demande: v })} />
        <TexteSujet label="Quel objectif ça sert, avec quel chiffre" value={decision.objectif} editable={canEdit}
          placeholder="Ex. : sécuriser la marge nette par réservation (100 FCFA)." onSave={(v) => update.mutate({ objectif: v })} />
        <TexteSujet label="Pourquoi ça pourrait échouer" value={decision.risques} editable={canEdit}
          placeholder="Les risques, et ce qu’on ferait à la place." onSave={(v) => update.mutate({ risques: v })} />

        <div className="grid-cards" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 220px), 1fr))" }}>
          <div className="field">
            <label htmlFor="d-concerne">Pôle concerné</label>
            <select id="d-concerne" className="select" value={decision.pole_concerne} disabled={!canEdit}
              onChange={(e) => update.mutate({ pole_concerne: e.target.value as Pole })}>
              <option value="">Tous</option>
              {POLES.map((p) => <option key={p.key} value={p.key}>{p.label}</option>)}
            </select>
          </div>
          <div className="field">
            <span style={{ fontSize: 13, fontWeight: 650 }}>Pôles en charge</span>
            {canEdit ? (
              <PolesPicker value={decision.poles_en_charge} onChange={(v) => update.mutate({ poles_en_charge: v })} />
            ) : (
              <span style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>{decision.poles_en_charge.map((p) => <PoleChip key={p} pole={p} />)}</span>
            )}
          </div>
        </div>
        <TexteSujet label="Liens (Drive, fiches…)" value={decision.liens} editable={canEdit} rows={2}
          placeholder="Une adresse par ligne." onSave={(v) => update.mutate({ liens: v })} />

        <section className="field" aria-label="Votes des heads">
          <span style={{ fontSize: 13, fontWeight: 650 }}>Votes des heads</span>
          {decision.votes.length === 0 && <p className="soft small">Personne n’a encore voté.</p>}
          <ul className="list-plain" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {decision.votes.map((v) => {
              const tone = VOTES.find((x) => x.key === v.vote)?.tone;
              return (
                <li key={v.membre.id} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                  <Avatar member={v.membre} size={26} />
                  <span style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                    <span style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <strong style={{ fontSize: 14 }}>{v.membre.name}</strong>
                      <span className={`chip ${tone}`}>{VOTES.find((x) => x.key === v.vote)?.label}</span>
                    </span>
                    {v.commentaire && <span style={{ fontSize: 14 }}>{v.commentaire}</span>}
                  </span>
                </li>
              );
            })}
          </ul>
          {isHead && !tranche && (
            <div style={{ display: "flex", flexDirection: "column", gap: 8, paddingTop: 6 }}>
              <label className="visually-hidden" htmlFor="d-com">Ton avis</label>
              <input id="d-com" className="input" placeholder="Ton avis en une phrase (facultatif)" value={commentaire} onChange={(e) => setCommentaire(e.target.value)} />
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {VOTES.map((v) => (
                  <button key={v.key} type="button" className={myVote?.vote === v.key ? "btn small primary" : "btn small"}
                    disabled={vote.isPending} onClick={() => vote.mutate(v.key)}>
                    {myVote?.vote === v.key ? `✓ ${v.label}` : v.label}
                  </button>
                ))}
              </div>
            </div>
          )}
          <p className="notice agent small">L’avis du Contradicteur apparaîtra ici quand l’agent sera branché : il relit chaque sujet important, chiffres à l’appui.</p>
        </section>

        {tranche && (
          <section className="field" aria-label="Revue à 30 jours">
            <span style={{ fontSize: 13, fontWeight: 650 }}>Revue à 30 jours : qui avait raison ?</span>
            {decision.bilan_verdict ? (
              <>
                <span className={`chip ${VERDICTS.find((v) => v.key === decision.bilan_verdict)?.tone}`} style={{ alignSelf: "flex-start" }}>
                  {VERDICTS.find((v) => v.key === decision.bilan_verdict)?.label}
                </span>
                {decision.bilan && <p style={{ whiteSpace: "pre-wrap", fontSize: 14.5 }}>{decision.bilan}</p>}
              </>
            ) : (
              <>
                <p className="soft small">
                  {decision.a_revoir ? "Les 30 jours sont passés : c’est le moment du bilan." : `Revue prévue le ${jour(decision.revue_le)}.`}
                </p>
                {isHead && (
                  <>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      {VERDICTS.map((v) => (
                        <button key={v.key} type="button" className={verdict === v.key ? "btn small primary" : "btn small"} onClick={() => setVerdict(v.key)}>{v.label}</button>
                      ))}
                    </div>
                    <textarea aria-label="Bilan" className="textarea" style={{ minHeight: 80 }} placeholder="Ce qu’on a appris, avec les chiffres."
                      value={bilan} onChange={(e) => setBilan(e.target.value)} />
                    <button type="button" className="btn brand" style={{ alignSelf: "flex-start" }} disabled={!verdict || saveBilan.isPending}
                      onClick={() => saveBilan.mutate()}>Enregistrer le bilan</button>
                  </>
                )}
              </>
            )}
          </section>
        )}

        {error && <p className="notice bad" role="alert">{(error as ApiError).message}</p>}
        {canEdit && (
          <button type="button" className="btn" style={{ alignSelf: "flex-start" }} disabled={archive.isPending} onClick={() => archive.mutate()}>
            Retirer du conseil
          </button>
        )}
      </motion.aside>
    </div>
  );
}

function NouveauSujet({ onClose, onCreated }: { onClose: () => void; onCreated: (d: Decision) => void }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<Required<DecisionInput>>({
    titre: "", demande: "", objectif: "", risques: "", liens: "", pole_concerne: "", poles_en_charge: [],
  });
  const create = useMutation({
    mutationFn: () => api.createDecision(form),
    onSuccess: (d) => {
      queryClient.invalidateQueries({ queryKey: ["decisions"] });
      onCreated(d);
    },
  });
  const set = <K extends keyof DecisionInput>(key: K, value: DecisionInput[K]) => setForm((f) => ({ ...f, [key]: value }));

  function submit(e: FormEvent) {
    e.preventDefault();
    if (form.titre.trim()) create.mutate();
  }

  return (
    <div className="drawer-wrap" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <motion.form className="drawer" onSubmit={submit} aria-label="Mettre un sujet au conseil"
        initial={{ x: 60, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ type: "spring", stiffness: 360, damping: 34 }}>
        <div className="card-head">
          <span className="eyebrow">Nouveau sujet au conseil</span>
          <button type="button" className="icon-btn light" onClick={onClose} aria-label="Fermer"><IconClose /></button>
        </div>
        <p className="soft small">Chaque sujet dit quel objectif il sert, avec quel chiffre, et pourquoi il pourrait échouer. Les heads votent, puis tranchent.</p>
        <div className="field">
          <label htmlFor="n-titre">Le sujet</label>
          <input id="n-titre" className="input" required maxLength={200} placeholder="Ex. : Commission Wave, pro ou Nyuman ?" value={form.titre}
            onChange={(e) => set("titre", e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="n-demande">La demande</label>
          <textarea id="n-demande" className="textarea" style={{ minHeight: 100 }} value={form.demande} onChange={(e) => set("demande", e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="n-objectif">Quel objectif ça sert, avec quel chiffre</label>
          <textarea id="n-objectif" className="textarea" style={{ minHeight: 60 }} value={form.objectif} onChange={(e) => set("objectif", e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="n-risques">Pourquoi ça pourrait échouer</label>
          <textarea id="n-risques" className="textarea" style={{ minHeight: 60 }} value={form.risques} onChange={(e) => set("risques", e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="n-concerne">Pôle concerné</label>
          <select id="n-concerne" className="select" value={form.pole_concerne} onChange={(e) => set("pole_concerne", e.target.value as Pole)}>
            <option value="">Tous</option>
            {POLES.map((p) => <option key={p.key} value={p.key}>{p.label}</option>)}
          </select>
        </div>
        <div className="field">
          <span style={{ fontSize: 13, fontWeight: 650 }}>Pôles en charge</span>
          <PolesPicker value={form.poles_en_charge} onChange={(v) => set("poles_en_charge", v)} />
        </div>
        <div className="field">
          <label htmlFor="n-liens">Liens (Drive, fiches…)</label>
          <textarea id="n-liens" className="textarea" style={{ minHeight: 50 }} value={form.liens} onChange={(e) => set("liens", e.target.value)} />
        </div>
        {create.error && <p className="notice bad" role="alert">{(create.error as ApiError).message}</p>}
        <button type="submit" className="btn brand" style={{ alignSelf: "flex-start" }} disabled={create.isPending}>Mettre au conseil</button>
      </motion.form>
    </div>
  );
}

export function Conseil() {
  const { me } = useLive();
  const [params, setParams] = useSearchParams();
  const decisions = useQuery({ queryKey: ["decisions"], queryFn: api.decisions });
  const [onglet, setOnglet] = useState<Onglet>("table");
  const [nouveau, setNouveau] = useState(false);
  const all = decisions.data ?? [];
  const selectedId = Number(params.get("sujet")) || null;
  const selected = all.find((d) => d.id === selectedId) ?? null;
  const aRevoir = all.filter((d) => d.a_revoir);
  usePresence({ piece: "conseil", label: selected ? `lit « ${selected.titre} »` : "est dans la salle du conseil" });

  function open(id: number | null) {
    const next = new URLSearchParams(params);
    if (id) next.set("sujet", String(id));
    else next.delete("sujet");
    setParams(next, { replace: true });
  }

  const courant = ONGLETS.find((o) => o.key === onglet)!;
  const visibles = all.filter((d) => courant.statuts.includes(d.statut));

  return (
    <div className="page">
      <header style={{ display: "flex", flexWrap: "wrap", alignItems: "flex-end", justifyContent: "space-between", gap: 16, paddingTop: 8 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <span className="eyebrow">La maison</span>
          <h1 className="display">La salle du conseil</h1>
          <p className="soft" style={{ fontSize: 16, maxWidth: "64ch" }}>
            Les sujets à trancher, les votes des heads, et le journal des décisions, revu à 30 jours : qui avait raison ?
          </p>
        </div>
        <button type="button" className="btn brand" onClick={() => setNouveau(true)}><IconPlus /> Mettre un sujet au conseil</button>
      </header>

      {aRevoir.length > 0 && (
        <div className="notice" role="status" style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
          <strong>{aRevoir.length === 1 ? "1 décision à revoir" : `${aRevoir.length} décisions à revoir`} : 30 jours ont passé.</strong>
          {aRevoir.map((d) => <button key={d.id} type="button" className="btn small" onClick={() => open(d.id)}>{d.titre}</button>)}
        </div>
      )}

      <div className="segmented" role="group" aria-label="Sujets" style={{ alignSelf: "flex-start", flexWrap: "wrap" }}>
        {ONGLETS.map((o) => (
          <button key={o.key} type="button" aria-pressed={onglet === o.key} onClick={() => setOnglet(o.key)}>
            {o.label} · {all.filter((d) => o.statuts.includes(d.statut)).length}
          </button>
        ))}
      </div>

      <div className="conseil-layout">
        <div className="grid-cards" style={{ alignContent: "start" }}>
          {visibles.map((d) => <DecisionCard key={d.id} decision={d} onOpen={() => open(d.id)} />)}
          {decisions.data && visibles.length === 0 && (
            <p className="soft">
              {onglet === "table" ? "Rien sur la table. Un sujet à trancher ? Mets-le au conseil." : onglet === "route" ? "Aucun sujet en cours d’exécution." : "Le journal est vide pour l’instant."}
            </p>
          )}
        </div>
        <aside style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <section className="card night" aria-labelledby="validation" style={{ gap: 10 }}>
            <h2 id="validation" style={{ fontSize: 17, fontWeight: 700 }}>File de validation</h2>
            <p style={{ color: "var(--cream-2)", fontSize: 14 }}>
              Vide pour l’instant. Quand les agents travailleront, tout ce qu’ils veulent faire à l’extérieur (un message, une publication, une dépense) attendra ici un « oui » humain.
            </p>
          </section>
          <section className="card" aria-labelledby="rythme" style={{ gap: 8 }}>
            <h2 id="rythme" style={{ fontSize: 17, fontWeight: 700 }}>Le rythme du conseil</h2>
            <ul className="list-plain" style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 14 }}>
              <li><strong>Lundi</strong> : chacun publie son rapport et 3 propositions.</li>
              <li><strong>Mardi</strong> : le Contradicteur relit les sujets.</li>
              <li><strong>Mercredi</strong> : réunion de 30 minutes, les heads tranchent.</li>
              <li><strong>À 30 jours</strong> : bilan de chaque décision.</li>
            </ul>
          </section>
        </aside>
      </div>

      {selected && <DecisionDrawer key={selected.id} decision={selected} me={me} onClose={() => open(null)} />}
      {nouveau && <NouveauSujet onClose={() => setNouveau(false)} onCreated={(d) => { setNouveau(false); setOnglet("table"); open(d.id); }} />}
    </div>
  );
}
