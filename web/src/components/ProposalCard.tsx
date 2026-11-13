import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Gavel, MessageSquareWarning } from "lucide-react";
import { proposalsApi, type Proposal, type VoteChoice } from "../lib/api";
import { useLive } from "../lib/live";
import { useSession } from "../lib/session";
import { Avatar } from "./Avatar";

const STATUS: Record<Proposal["status"], { label: string; cls: string }> = {
  open: { label: "Vote en cours", cls: "bg-accent-soft text-accent" },
  adopted: { label: "Adoptée", cls: "bg-[#E3F6EA] text-[#18794A]" },
  rejected: { label: "Rejetée", cls: "bg-[#FDE6E2] text-[#B5321F]" },
  withdrawn: { label: "Retirée", cls: "bg-surface-2 text-ink-soft" },
};
/** Mise en forme légère des textes des agents : **gras** et listes « - ». */
function Rich({ text, className = "" }: { text: string; className?: string }) {
  const inline = (line: string) => line.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? <b key={i}>{part.slice(2, -2)}</b> : part);
  return (
    <div className={`space-y-1 ${className}`}>
      {text.split("\n").filter((l, i, a) => l.trim() || (i > 0 && a[i - 1].trim())).map((l, i) => {
        const t = l.trim();
        if (!t) return <div key={i} className="h-1" />;
        if (/^[-•*] /.test(t)) return <div key={i} className="flex gap-2 pl-1"><span className="text-ink-muted">•</span><span>{inline(t.slice(2))}</span></div>;
        return <p key={i}>{inline(t)}</p>;
      })}
    </div>
  );
}

const CHOICE_LABEL: Record<VoteChoice, string> = { pour: "Pour", contre: "Contre", abstention: "Abstention" };

export function useProposal(id: string, initial?: Proposal) {
  const { subscribe } = useLive();
  const [p, setP] = useState<Proposal | null>(initial ?? null);
  useEffect(() => { if (!initial) proposalsApi.get(id).then(setP).catch(() => setP(null)); }, [id, initial]);
  useEffect(() => { if (initial) setP(initial); }, [initial]);
  useEffect(() => subscribe((ev) => { if (ev.type === "proposal.updated" && ev.proposal.id === id) setP(ev.proposal); }), [id, subscribe]);
  return [p, setP] as const;
}

/** Une proposition : texte, chiffres, avis de Koffi, puis le vote des responsables. */
export function ProposalCard({ id, initial, full }: { id: string; initial?: Proposal; full?: boolean }) {
  const { me, members } = useSession();
  const [p, setP] = useProposal(id, initial);
  const [comment, setComment] = useState("");
  const [open, setOpen] = useState(!!full);
  if (!p || !me) return null;
  const name = (mid: string) => members.find((m) => m.id === mid)?.name ?? mid;
  const author = members.find((m) => m.id === p.author_id);
  const mine = p.votes.find((v) => v.member_id === me.id);
  const canVote = me.kind === "human" && me.is_head && p.status === "open";
  const total = p.voters.length || 1;
  const st = STATUS[p.status];
  const vote = async (c: VoteChoice) => setP(await proposalsApi.vote(p.id, c, comment.trim()));

  return (
    <div className={`my-1 rounded-2xl border bg-white p-4 shadow-sm ${full ? "border-line" : "max-w-lg border-line"}`}>
      <div className="flex items-start gap-3">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-soft text-blue"><Gavel size={18} /></span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${st.cls}`}>{st.label}</span>
            {p.deadline && p.status === "open" && <span className="text-[11px] text-ink-muted">avant le {new Date(p.deadline + "T12:00").toLocaleDateString("fr-FR", { day: "numeric", month: "short" })}</span>}
          </div>
          <Link to={`/conseil?p=${p.id}`} className="mt-1 block font-semibold leading-snug hover:text-accent">{p.title}</Link>
          <p className="text-xs text-ink-soft">Proposée par {author?.name ?? p.author_id}</p>
        </div>
      </div>

      {(open || full) && (p.body || p.figures) && (
        <div className="mt-3 space-y-2 text-sm">
          {p.body && <Rich text={p.body} className="text-ink" />}
          {p.figures && <p className="whitespace-pre-wrap rounded-xl bg-surface px-3 py-2 text-ink"><span className="mr-1 text-xs font-semibold text-ink-soft">Chiffres</span>{p.figures}</p>}
        </div>
      )}
      {!open && !full && (p.body || p.figures) && <button onClick={() => setOpen(true)} className="mt-2 text-xs font-medium text-accent hover:underline">Lire la proposition</button>}

      <div className={`mt-3 rounded-xl border px-3 py-2 text-sm ${p.opinion ? "border-[#F5DCC0] bg-[#FFF8F0]" : "border-dashed border-line text-ink-muted"}`}>
        <div className="mb-0.5 flex items-center gap-1.5 text-xs font-semibold text-ink-soft"><MessageSquareWarning size={13} /> Avis de Koffi, contradicteur</div>
        {p.opinion ? (open || full ? <Rich text={p.opinion} className="text-ink" /> : <p className="line-clamp-3 text-ink">{p.opinion.replace(/\*\*/g, "")}</p>) : <p className="text-xs">En attente de son avis.</p>}
      </div>

      <div className="mt-3">
        <div className="flex h-2 overflow-hidden rounded-full bg-surface-2">
          <div className="bg-online" style={{ width: `${(p.tally.pour / total) * 100}%` }} />
          <div className="bg-busy" style={{ width: `${(p.tally.contre / total) * 100}%` }} />
          <div className="bg-offline" style={{ width: `${(p.tally.abstention / total) * 100}%` }} />
        </div>
        <div className="mt-1.5 flex flex-wrap items-center justify-between gap-2 text-xs text-ink-soft">
          <span>Pour {p.tally.pour} · Contre {p.tally.contre} · Abstention {p.tally.abstention} · {p.votes.length}/{p.voters.length} ont voté</span>
          <span className="flex -space-x-1.5">
            {p.voters.map((v) => { const m = members.find((x) => x.id === v); const has = p.votes.some((x) => x.member_id === v);
              return m ? <span key={v} className={has ? "" : "opacity-30"} title={`${m.name}${has ? " a voté" : " n'a pas encore voté"}`}><Avatar member={m} size="sm" ring /></span> : null; })}
          </span>
        </div>
        {(open || full) && p.votes.some((v) => v.comment) && (
          <ul className="mt-2 space-y-1 text-xs">
            {p.votes.filter((v) => v.comment).map((v) => <li key={v.member_id}><b>{name(v.member_id)}</b> ({CHOICE_LABEL[v.choice].toLowerCase()}) : {v.comment}</li>)}
          </ul>
        )}
      </div>

      {canVote && (
        <div className="mt-3 border-t border-line pt-3">
          {mine && <p className="mb-2 text-xs text-ink-soft">Vous avez voté <b>{CHOICE_LABEL[mine.choice].toLowerCase()}</b>. Vous pouvez changer tant que le vote est ouvert.</p>}
          <input value={comment} onChange={(e) => setComment(e.target.value)} maxLength={500} placeholder="Un mot pour expliquer (facultatif)"
            className="mb-2 w-full rounded-xl border border-line px-3 py-2 text-sm outline-none focus:border-accent" />
          <div className="flex flex-wrap gap-2">
            {(["pour", "contre", "abstention"] as VoteChoice[]).map((c) => (
              <button key={c} onClick={() => vote(c)}
                className={`rounded-xl px-4 py-2 text-sm font-semibold transition ${mine?.choice === c
                  ? c === "pour" ? "bg-online text-white" : c === "contre" ? "bg-busy text-white" : "bg-ink-soft text-white"
                  : "border border-line bg-white hover:bg-surface"}`}>{CHOICE_LABEL[c]}</button>
            ))}
            {full && <button onClick={async () => setP(await proposalsApi.close(p.id))} className="ml-auto text-xs font-medium text-ink-soft hover:text-ink">Clore le vote</button>}
          </div>
        </div>
      )}
      {full && p.status === "open" && p.author_id === me.id && (
        <button onClick={async () => setP(await proposalsApi.withdraw(p.id))} className="mt-2 text-xs text-ink-muted hover:text-busy">Retirer ma proposition</button>
      )}
    </div>
  );
}
