import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, type Member, type Rapport, type RapportInput } from "../api";
import { firstName, formatAgo, semaineIso } from "../format";

const SECTIONS: { key: keyof RapportInput; label: string; hint: string; tone?: string }[] = [
  { key: "fait", label: "Fait cette semaine", hint: "Ce qui est terminé, avec un chiffre si possible" },
  { key: "en_cours", label: "En cours", hint: "Ce qui avance, et où on en est" },
  { key: "bloque", label: "Bloqué", hint: "Ce qui coince, et ce qu’il faudrait pour débloquer", tone: "var(--bad)" },
  { key: "propositions", label: "3 propositions", hint: "Une par ligne : l’objectif servi, le chiffre visé", tone: "var(--brand-ink)" },
];

function numeroSemaine(week: string): string {
  return `semaine ${Number(week.split("W")[1])}`;
}

function Lines({ text }: { text: string }) {
  const lines = text.split("\n").map((l) => l.replace(/^[-•*]\s*/, "").trim()).filter(Boolean);
  if (lines.length === 0) return <p className="soft small">Rien.</p>;
  return (
    <ul style={{ margin: 0, paddingLeft: 18, display: "flex", flexDirection: "column", gap: 4, fontSize: 14.5 }}>
      {lines.map((l, i) => <li key={i}>{l}</li>)}
    </ul>
  );
}

function RapportView({ rapport }: { rapport: Rapport }) {
  return (
    <div className="grid-cards" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 230px), 1fr))" }}>
      {SECTIONS.map((s) => (
        <div key={s.key} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <span className="eyebrow" style={s.tone ? { color: s.tone } : undefined}>{s.label}</span>
          <Lines text={rapport[s.key]} />
        </div>
      ))}
    </div>
  );
}

/** Le rapport de la semaine : chacun publie le sien ; les autres le lisent dans son bureau. */
export function RapportCard({ member, me }: { member: Member; me: Member }) {
  const queryClient = useQueryClient();
  const rapports = useQuery({ queryKey: ["rapports", member.id], queryFn: () => api.rapports(member.id), enabled: member.kind === "humain" });
  const week = semaineIso();
  const current = rapports.data?.find((r) => r.week === week);
  const previous = (rapports.data ?? []).filter((r) => r.week !== week);
  const isMe = member.id === me.id;
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<RapportInput>({ fait: "", en_cours: "", bloque: "", propositions: "" });

  useEffect(() => {
    if (current) setForm({ fait: current.fait, en_cours: current.en_cours, bloque: current.bloque, propositions: current.propositions });
  }, [current]);

  const publish = useMutation({
    mutationFn: api.publishRapport,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rapports"] });
      setEditing(false);
    },
  });

  function submit(e: FormEvent) {
    e.preventDefault();
    publish.mutate(form);
  }

  if (member.kind === "agent") {
    return (
      <section className="card" id="rapport" aria-label="Rapport de la semaine">
        <h2 className="title">Rapport de la semaine</h2>
        <p className="notice agent">{member.name} publiera son rapport et ses 3 propositions chaque lundi, dès qu’il se mettra au travail (semaine 3).</p>
      </section>
    );
  }

  const showForm = isMe && (editing || !current);
  return (
    <section className="card" id="rapport" aria-label="Rapport de la semaine" style={{ gap: 16 }}>
      <div className="card-head">
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <h2 className="title">Rapport de la {numeroSemaine(week)}</h2>
          <span className="soft small">
            {current ? `Publié ${formatAgo(current.created_at)}${current.updated_at !== current.created_at ? `, complété ${formatAgo(current.updated_at)}` : ""}` : "À publier le lundi, pour la réunion du mercredi"}
          </span>
        </div>
        {current ? <span className="chip good">Publié</span> : <span className="chip wait">Pas encore</span>}
      </div>

      {showForm ? (
        <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {SECTIONS.map((s) => (
            <div key={s.key} className="field">
              <label htmlFor={`rapport-${s.key}`} style={s.tone ? { color: s.tone } : undefined}>{s.label}</label>
              <textarea id={`rapport-${s.key}`} className="textarea" style={{ minHeight: 80, fontFamily: "var(--font)", fontSize: 14.5 }}
                placeholder={s.hint} value={form[s.key]} onChange={(e) => setForm({ ...form, [s.key]: e.target.value })} />
            </div>
          ))}
          {publish.error && <p className="notice bad" role="alert">{(publish.error as ApiError).message}</p>}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button type="submit" className="btn primary" disabled={publish.isPending}>{current ? "Mettre à jour" : "Publier mon rapport"}</button>
            {current && <button type="button" className="btn" onClick={() => setEditing(false)}>Annuler</button>}
          </div>
        </form>
      ) : current ? (
        <>
          <RapportView rapport={current} />
          {isMe && <button type="button" className="btn small" style={{ alignSelf: "flex-start" }} onClick={() => setEditing(true)}>Compléter</button>}
        </>
      ) : (
        <p className="soft">{firstName(member.name)} n’a pas encore publié son rapport cette semaine.</p>
      )}

      {previous.length > 0 && (
        <details className="details">
          <summary>Les semaines d’avant ({previous.length})</summary>
          <div style={{ display: "flex", flexDirection: "column", gap: 18, marginTop: 14 }}>
            {previous.map((r) => (
              <div key={r.id} style={{ display: "flex", flexDirection: "column", gap: 10, paddingTop: 12, borderTop: "1px solid var(--line)" }}>
                <span className="eyebrow">{numeroSemaine(r.week)}</span>
                <RapportView rapport={r} />
              </div>
            ))}
          </div>
        </details>
      )}
    </section>
  );
}
