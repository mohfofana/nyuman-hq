import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, type Member, type Pole } from "../api";
import { formatNumber } from "../format";
import { poleOf } from "../poles";
import { ObjectiveForm, metricLabel } from "./ObjectiveForm";

/** L'objectif d'un pôle, avec sa jauge. Le head le fixe ; le pôle met à jour son chiffre s'il est suivi à la main. */
export function PoleObjective({ pole, me, compact = false }: { pole: Exclude<Pole, "">; me: Member; compact?: boolean }) {
  const queryClient = useQueryClient();
  const def = poleOf(pole)!;
  const objective = useQuery({ queryKey: ["objectif", pole], queryFn: () => api.objective(pole) });
  const [editing, setEditing] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [value, setValue] = useState<number>(0);
  const o = objective.data;
  const isHead = me.role === "head";
  const canUpdate = !!o && o.metric === "manuel" && (isHead || me.pole === pole);

  const avance = useMutation({
    mutationFn: (v: number) => api.updateAvancement(o!.id, v),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["objectif"] });
      queryClient.invalidateQueries({ queryKey: ["objectifs-poles"] });
      setUpdating(false);
    },
  });

  function submitValue(e: FormEvent) {
    e.preventDefault();
    avance.mutate(value);
  }

  if (editing) {
    return (
      <section className="card" aria-label={`Objectif du pôle ${def.label}`}>
        <h2 className="title">Objectif du pôle {def.label}</h2>
        <ObjectiveForm initial={o ?? null} pole={pole} heading={`Objectif du pôle ${def.label}`} onDone={() => setEditing(false)} />
      </section>
    );
  }

  const pct = Math.min(100, Math.round((o?.progress ?? 0) * 100));
  return (
    <section className="card" aria-label={`Objectif du pôle ${def.label}`} style={{ gap: compact ? 10 : 14 }}>
      <div className="card-head">
        <span className="eyebrow" style={{ color: def.color.fg }}>Objectif du pôle {def.label}{o ? ` · ${o.quarter}` : ""}</span>
        {isHead && (
          <button type="button" className="link-btn" onClick={() => setEditing(true)}>{o ? "Modifier" : "Fixer l’objectif"}</button>
        )}
      </div>
      {!o ? (
        <p className="soft small">{isHead ? "Pas encore d’objectif pour ce pôle." : "Le head du pôle fixera son objectif."}</p>
      ) : (
        <>
          <h3 style={{ fontSize: compact ? 16 : 20, fontWeight: 750 }}>{o.title}</h3>
          <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
            <span className="num" style={{ fontSize: compact ? 26 : 34, fontWeight: 850, letterSpacing: "-0.03em" }}>
              {o.current !== null ? formatNumber(o.current) : "?"}
            </span>
            <span className="soft">/ {formatNumber(o.target)} {metricLabel(o.metric)}</span>
            {o.progress !== null && o.progress >= 1 && <span className="chip good">Atteint</span>}
          </div>
          <div className="bar" role="img" aria-label={`${pct} % de l’objectif du pôle`} style={{ height: 10 }}>
            <span style={{ width: `${pct}%`, background: def.color.fg }} />
          </div>
          {!compact && (
            <p className="soft small">
              {o.weeks_left} semaine{o.weeks_left > 1 ? "s" : ""} restantes
              {o.needed_per_week !== null && o.current !== null && o.current < o.target ? ` · ${formatNumber(o.needed_per_week)} par semaine à tenir` : ""}
              {o.metric === "manuel" ? " · chiffre tenu à la main par le pôle" : " · chiffre en direct de l’app"}
            </p>
          )}
          {canUpdate && !updating && (
            <button type="button" className="btn small" style={{ alignSelf: "flex-start" }} onClick={() => { setValue(o.current ?? 0); setUpdating(true); }}>
              Mettre à jour le chiffre
            </button>
          )}
          {updating && (
            <form onSubmit={submitValue} style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <label className="visually-hidden" htmlFor={`avance-${pole}`}>Nouveau chiffre</label>
              <input id={`avance-${pole}`} className="input" type="number" min={0} style={{ width: 130, minHeight: 38 }} value={value}
                onChange={(e) => setValue(Number(e.target.value))} autoFocus />
              <button type="submit" className="btn small primary" disabled={avance.isPending}>Enregistrer</button>
              <button type="button" className="btn small" onClick={() => setUpdating(false)}>Annuler</button>
            </form>
          )}
          {avance.error && <p className="notice bad">{(avance.error as ApiError).message}</p>}
        </>
      )}
    </section>
  );
}
