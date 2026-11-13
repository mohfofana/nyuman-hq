import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Gavel, Plus, X } from "lucide-react";
import { proposalsApi, type Proposal } from "../lib/api";
import { useLive } from "../lib/live";
import { ProposalCard } from "../components/ProposalCard";

export function Council() {
  const { subscribe } = useLive();
  const [params, setParams] = useSearchParams();
  const [list, setList] = useState<Proposal[] | null>(null);
  const [tab, setTab] = useState<"open" | "closed">("open");
  const [creating, setCreating] = useState(params.get("nouvelle") === "1");
  const focus = params.get("p");
  const load = useCallback(() => proposalsApi.list(tab).then(setList), [tab]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => subscribe((ev) => { if (ev.type === "proposal.updated") load(); }), [load, subscribe]);
  useEffect(() => {
    if (focus && list) document.getElementById(`p-${focus}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [focus, list]);
  useEffect(() => { if (focus) proposalsApi.get(focus).then((p) => setTab(p.status === "open" ? "open" : "closed")).catch(() => {}); }, [focus]);

  return (
    <div className="mx-auto max-w-3xl px-4 py-6 sm:px-8">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold"><Gavel className="text-blue" size={24} /> Salle du conseil</h1>
          <p className="mt-1 text-sm text-ink-soft">Une proposition, ses chiffres, l'avis de Koffi, puis le vote des responsables.</p>
        </div>
        <button onClick={() => setCreating(true)} className="inline-flex items-center gap-1.5 rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-accent/30 hover:bg-accent-hover">
          <Plus size={16} /> Proposer
        </button>
      </div>
      <div className="mb-4 flex rounded-xl bg-surface-2 p-1 text-sm font-medium sm:inline-flex">
        {([["open", "En cours"], ["closed", "Décidées"]] as const).map(([k, l]) => (
          <button key={k} onClick={() => setTab(k)} className={`flex-1 rounded-lg px-3.5 py-1.5 ${tab === k ? "bg-white shadow-sm" : "text-ink-soft hover:text-ink"}`}>{l}</button>
        ))}
      </div>
      {list && list.length === 0 && (
        <p className="rounded-2xl bg-surface p-5 text-sm text-ink-soft">{tab === "open" ? "Aucune proposition en cours. Une idée qui engage l'équipe ou de l'argent ? Proposez-la." : "Rien de décidé pour l'instant."}</p>
      )}
      <div className="space-y-4">
        {list?.map((p) => (
          <div key={p.id} id={`p-${p.id}`} className={focus === p.id ? "rounded-2xl ring-2 ring-accent/40" : ""}><ProposalCard id={p.id} initial={p} full /></div>
        ))}
      </div>
      {creating && <NewProposal onClose={() => { setCreating(false); if (params.get("nouvelle")) setParams({}); }} onDone={(p) => { setTab("open"); setParams({ p: p.id }); load(); }} />}
    </div>
  );
}

function NewProposal({ onClose, onDone }: { onClose: () => void; onDone: (p: Proposal) => void }) {
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [figures, setFigures] = useState("");
  const [deadline, setDeadline] = useState("");
  const [critic, setCritic] = useState(true);
  const [busy, setBusy] = useState(false);
  const submit = async () => {
    setBusy(true);
    try {
      const p = await proposalsApi.create({ title: title.trim(), body, figures, deadline: deadline || null, ask_critic: critic });
      onDone(p); onClose();
    } finally { setBusy(false); }
  };
  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center bg-black/30 p-0 sm:items-center sm:p-4" onClick={onClose}>
      <div onClick={(e) => e.stopPropagation()} className="slide-in w-full max-w-lg rounded-t-3xl bg-white p-5 shadow-xl sm:rounded-3xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Nouvelle proposition</h2>
          <button onClick={onClose} aria-label="Fermer" className="rounded-lg p-1 text-ink-soft hover:bg-surface"><X size={18} /></button>
        </div>
        <div className="space-y-3 text-sm">
          <input autoFocus value={title} onChange={(e) => setTitle(e.target.value)} maxLength={200} placeholder="Ce qu'on décide, en une phrase"
            className="w-full rounded-xl border border-line px-3 py-2.5 font-medium outline-none focus:border-accent" />
          <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={4} maxLength={10000} placeholder="Pourquoi, et ce que ça change"
            className="w-full resize-none rounded-xl border border-line px-3 py-2 outline-none focus:border-accent" />
          <textarea value={figures} onChange={(e) => setFigures(e.target.value)} rows={2} maxLength={4000} placeholder="Les chiffres : coût, gain, délai"
            className="w-full resize-none rounded-xl border border-line px-3 py-2 outline-none focus:border-accent" />
          <label className="flex items-center justify-between gap-3 text-ink-soft">Réponse souhaitée avant le
            <input type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)} className="rounded-xl border border-line px-3 py-1.5 text-ink outline-none focus:border-accent" />
          </label>
          <label className="flex items-center gap-2 text-ink-soft">
            <input type="checkbox" checked={critic} onChange={(e) => setCritic(e.target.checked)} className="accent-[#BC600D]" />
            Demander l'avis de Koffi (quelques centimes)
          </label>
          <p className="text-xs text-ink-muted">La proposition est annoncée dans #général. Le vote se ferme seul quand tous les responsables ont voté.</p>
        </div>
        <button disabled={title.trim().length < 3 || busy} onClick={submit}
          className="mt-4 w-full rounded-xl bg-accent py-2.5 text-sm font-semibold text-white hover:bg-accent-hover disabled:opacity-40">Soumettre au vote</button>
      </div>
    </div>
  );
}
