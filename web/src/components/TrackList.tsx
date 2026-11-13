import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Archive, Plus } from "lucide-react";
import { TRACK_STAGES, tracksApi, type TrackItem, type TrackKind } from "../lib/api";
import { useLive } from "../lib/live";
import { useSession } from "../lib/session";
import { Avatar } from "./Avatar";

const CONF: Record<TrackKind, { placeholder: string; extra: "contact" | "date" | "amount"; extraLabel: string; done: string[]; empty: string }> = {
  salon: { placeholder: "Nom du salon, quartier", extra: "contact", extraLabel: "Contact (Instagram, WhatsApp…)", done: ["1re réservation"],
    empty: "Ajoutez les salons à amener jusqu'à leur première réservation." },
  echeance: { placeholder: "Ex. : préavis FeexPay, renouvellement contrat Jèko", extra: "date", extraLabel: "Pour le", done: ["réglé"],
    empty: "Contrats, préavis, déclarations : tout ce qui a une date limite." },
  depense: { placeholder: "Ex. : hébergement Railway", extra: "amount", extraLabel: "Montant", done: ["validée", "refusée"],
    empty: "Les dépenses à faire valider arrivent ici." },
};

/** Couleur de l'étape : neutre au départ, orange en cours, vert quand c'est gagné, rouge si refusé. */
function stageTone(kind: TrackKind, stage: string) {
  const stages = TRACK_STAGES[kind];
  if (stage === "refusée") return "bg-[#FDE6E2] text-[#B5321F]";
  if (stage === stages[stages.length - 1] || stage === "validée") return "bg-[#E3F6EA] text-[#18794A]";
  if (stage === stages[0]) return "bg-surface-2 text-ink-soft";
  return "bg-accent-soft text-accent";
}

export function money(amount: number | null, currency: string) {
  if (amount == null) return "";
  return `${amount.toLocaleString("fr-FR")} ${currency === "FCFA" ? "F" : currency}`;
}

export function useTracks(kind: TrackKind) {
  const { subscribe } = useLive();
  const [items, setItems] = useState<TrackItem[] | null>(null);
  const load = useCallback(() => tracksApi.list(kind).then(setItems), [kind]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => subscribe((ev) => { if (ev.type === "track.updated" && ev.kind === kind) load(); }), [kind, load, subscribe]);
  return { items, load };
}

export type RowAsk = { id: string; name: string; label: string; texte: (t: TrackItem) => string };

export function TrackList({ kind, limit, hideDone, ask }: {
  kind: TrackKind; limit?: number; hideDone?: boolean; ask?: RowAsk | null;
}) {
  const { me, members } = useSession();
  const navigate = useNavigate();
  const { items, load } = useTracks(kind);
  const conf = CONF[kind];
  const [title, setTitle] = useState("");
  const [extra, setExtra] = useState("");
  const [currency, setCurrency] = useState("FCFA");
  const [error, setError] = useState("");
  if (!items || !me) return null;

  const add = async () => {
    if (!title.trim()) return;
    await tracksApi.add({
      kind, title: title.trim(),
      ...(conf.extra === "contact" ? { contact: extra } : {}),
      ...(conf.extra === "date" && extra ? { due_date: extra } : {}),
      ...(conf.extra === "amount" && extra ? { amount: Number(extra), currency } : {}),
    });
    setTitle(""); setExtra(""); load();
  };
  const setStage = async (t: TrackItem, stage: string) => {
    setError("");
    try { await tracksApi.update(t.id, { stage }); load(); }
    catch (e: any) { setError(e.status === 403 ? "Seul un responsable valide ou refuse une dépense." : "Impossible pour l'instant."); }
  };
  const shown = items.filter((t) => !hideDone || !conf.done.includes(t.stage));
  const today = new Date().toISOString().slice(0, 10);

  return (
    <div className="space-y-2">
      {shown.length === 0 && <p className="rounded-2xl bg-surface p-3 text-sm text-ink-soft">{conf.empty}</p>}
      <ul className="divide-y divide-line">
        {shown.slice(0, limit ?? 100).map((t) => {
          const owner = members.find((m) => m.id === t.owner_id);
          const late = t.due_date && t.due_date < today && !conf.done.includes(t.stage);
          return (
            <li key={t.id} className="group flex items-center gap-2.5 py-2">
              {owner && <Avatar member={owner} size="sm" />}
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium">{t.title}</div>
                <div className="truncate text-xs text-ink-soft">
                  {[t.contact, t.amount != null ? money(t.amount, t.currency) : "",
                    t.due_date ? `pour le ${new Date(t.due_date + "T12:00").toLocaleDateString("fr-FR", { day: "numeric", month: "short" })}` : ""]
                    .filter(Boolean).join(" · ")}
                  {late && <span className="ml-1 font-medium text-busy">en retard</span>}
                </div>
              </div>
              <select value={t.stage} onChange={(e) => setStage(t, e.target.value)}
                className={`shrink-0 cursor-pointer rounded-full border-0 py-1 pl-2.5 pr-6 text-xs font-medium outline-none ${stageTone(kind, t.stage)}`}>
                {TRACK_STAGES[kind].map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
              {ask && (
                <button onClick={() => navigate(`/discussions?avec=${ask.id}&texte=${encodeURIComponent(ask.texte(t))}`)}
                  title={`Demander à ${ask.name}`}
                  className="shrink-0 rounded-lg bg-accent-soft px-2.5 py-1 text-xs font-semibold text-accent transition hover:bg-accent hover:text-white">
                  {ask.label}
                </button>
              )}
              <button onClick={async () => { await tracksApi.update(t.id, { archived: true }); load(); }} title="Ranger" aria-label="Ranger"
                className="rounded-md p-1 text-ink-muted opacity-0 hover:bg-surface hover:text-ink group-hover:opacity-100"><Archive size={14} /></button>
            </li>
          );
        })}
      </ul>
      {limit && shown.length > limit && <p className="text-xs text-ink-muted">+ {shown.length - limit} autres</p>}
      {error && <p className="text-xs text-busy">{error}</p>}
      <form onSubmit={(e) => { e.preventDefault(); add(); }} className="flex flex-wrap gap-2 pt-1">
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder={conf.placeholder} maxLength={200}
          className="min-w-[160px] flex-[2] rounded-xl border border-line bg-white px-3 py-2 text-sm outline-none focus:border-accent" />
        {title.trim() && conf.extra === "contact" && (
          <input value={extra} onChange={(e) => setExtra(e.target.value)} placeholder={conf.extraLabel} maxLength={160}
            className="min-w-[140px] flex-1 rounded-xl border border-line bg-white px-3 py-2 text-sm outline-none focus:border-accent" />
        )}
        {title.trim() && conf.extra === "date" && (
          <input type="date" value={extra} onChange={(e) => setExtra(e.target.value)} aria-label={conf.extraLabel}
            className="rounded-xl border border-line bg-white px-3 py-2 text-sm outline-none focus:border-accent" />
        )}
        {title.trim() && conf.extra === "amount" && (
          <span className="flex gap-1">
            <input type="number" min={0} value={extra} onChange={(e) => setExtra(e.target.value)} placeholder="Montant"
              className="w-28 rounded-xl border border-line bg-white px-3 py-2 text-sm outline-none focus:border-accent" />
            <select value={currency} onChange={(e) => setCurrency(e.target.value)} className="rounded-xl border border-line bg-white px-2 text-sm">
              <option>FCFA</option><option>USD</option><option>EUR</option>
            </select>
          </span>
        )}
        <button disabled={!title.trim()} className="inline-flex items-center gap-1 rounded-xl bg-accent px-3 py-2 text-sm font-semibold text-white hover:bg-accent-hover disabled:opacity-40">
          <Plus size={15} /> Ajouter
        </button>
      </form>
    </div>
  );
}
