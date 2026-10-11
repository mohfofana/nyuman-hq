import { useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, type Objective, type ObjectiveInput, type ObjectiveMetric, type Pole } from "../api";

export const METRICS: { key: ObjectiveMetric; label: string }[] = [
  { key: "pros_actifs", label: "Pros actifs (chiffre de l’app)" },
  { key: "utilisateurs_inscrits", label: "Utilisateurs inscrits (chiffre de l’app)" },
  { key: "reservations_7j", label: "Réservations payées sur 7 jours (chiffre de l’app)" },
  { key: "acomptes_7j_fcfa", label: "Acomptes sur 7 jours, FCFA (chiffre de l’app)" },
  { key: "revenu_nyuman_7j_fcfa", label: "Revenu Nyuman sur 7 jours, FCFA (chiffre de l’app)" },
  { key: "manuel", label: "Un chiffre que le pôle met à jour à la main" },
];

export function metricLabel(key: ObjectiveMetric): string {
  if (key === "manuel") return "";
  return METRICS.find((m) => m.key === key)?.label.replace(/ \(.*\)$/, "").toLowerCase() ?? key;
}

/** Fixer l'objectif du trimestre : celui de toute la maison, ou celui d'un pôle. */
export function ObjectiveForm({ initial, pole = "", onDone, heading }: {
  initial: Objective | null;
  pole?: Pole;
  onDone: () => void;
  heading: string;
}) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<ObjectiveInput>(
    initial
      ? {
          title: initial.title, quarter: initial.quarter, metric: initial.metric, target: initial.target,
          start_date: initial.start_date, end_date: initial.end_date,
          current_manual: initial.metric === "manuel" ? initial.current : null,
        }
      : { title: "", quarter: "", metric: pole ? "manuel" : "pros_actifs", target: 100, start_date: "", end_date: "", current_manual: 0 },
  );
  const save = useMutation({
    mutationFn: (input: ObjectiveInput) => api.saveObjective(input, pole),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["objectif"] });
      queryClient.invalidateQueries({ queryKey: ["objectifs-poles"] });
      onDone();
    },
  });
  const set = <K extends keyof ObjectiveInput>(key: K, value: ObjectiveInput[K]) => setForm({ ...form, [key]: value });
  const id = pole || "maison";

  function submit(e: FormEvent) {
    e.preventDefault();
    save.mutate(form);
  }

  return (
    <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 14 }} aria-label={heading}>
      <div className="field">
        <label htmlFor={`obj-title-${id}`}>En une phrase</label>
        <input id={`obj-title-${id}`} className="input" required value={form.title}
          placeholder={pole ? "0 bug bloquant avant le lancement" : "100 pros actifs au 31 décembre"}
          onChange={(e) => set("title", e.target.value)} />
      </div>
      <div className="field">
        <label htmlFor={`obj-metric-${id}`}>Chiffre suivi</label>
        <select id={`obj-metric-${id}`} className="select" value={form.metric} onChange={(e) => set("metric", e.target.value as ObjectiveMetric)}>
          {METRICS.map((m) => <option key={m.key} value={m.key}>{m.label}</option>)}
        </select>
      </div>
      <div className="grid-cards" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 150px), 1fr))" }}>
        {form.metric === "manuel" && (
          <div className="field">
            <label htmlFor={`obj-current-${id}`}>Où on en est</label>
            <input id={`obj-current-${id}`} className="input" type="number" min={0} value={form.current_manual ?? 0}
              onChange={(e) => set("current_manual", Number(e.target.value))} />
          </div>
        )}
        <div className="field">
          <label htmlFor={`obj-target-${id}`}>Cible</label>
          <input id={`obj-target-${id}`} className="input" type="number" min={1} required value={form.target}
            onChange={(e) => set("target", Number(e.target.value))} />
        </div>
        <div className="field">
          <label htmlFor={`obj-quarter-${id}`}>Trimestre</label>
          <input id={`obj-quarter-${id}`} className="input" required value={form.quarter} placeholder="T4 2026"
            onChange={(e) => set("quarter", e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor={`obj-start-${id}`}>Début</label>
          <input id={`obj-start-${id}`} className="input" type="date" required value={form.start_date} onChange={(e) => set("start_date", e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor={`obj-end-${id}`}>Fin</label>
          <input id={`obj-end-${id}`} className="input" type="date" required value={form.end_date} onChange={(e) => set("end_date", e.target.value)} />
        </div>
      </div>
      {save.error && <p className="notice bad" role="alert">{(save.error as ApiError).message}</p>}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button type="submit" className="btn primary" disabled={save.isPending}>Enregistrer</button>
        <button type="button" className="btn" onClick={onDone}>Annuler</button>
      </div>
    </form>
  );
}
