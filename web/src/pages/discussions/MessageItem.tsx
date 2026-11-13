import { useState } from "react";
import { FileText, MessageSquareReply, MoreHorizontal, Pencil, SmilePlus, Trash2 } from "lucide-react";
import { chat, type Member, type Message } from "../../lib/api";
import { Avatar } from "../../components/Avatar";
import { presenceOf } from "../../lib/presence";
import { QUICK, decodeMentions, encodeMentions, fileSize, renderBody, time } from "./format";


export function MessageItem({ m, members, me, compact, onReply, inThread }: {
  m: Message; members: Member[]; me: Member; compact: boolean; onReply?: (m: Message) => void; inThread?: boolean;
}) {
  const author = members.find((x) => x.id === m.author_id);
  const [picker, setPicker] = useState(false);
  const [menu, setMenu] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const mine = m.author_id === me.id;
  if (!author) return null;

  const saveEdit = async () => {
    const body = encodeMentions(draft.trim(), members);
    if (body && body !== m.body) await chat.edit(m.id, body);
    setEditing(false);
  };

  return (
    <div className={`group relative flex gap-3 rounded-xl px-3 transition hover:bg-surface/70 ${compact ? "py-0.5" : "mt-3 pt-2 pb-0.5"}`}
      onMouseLeave={() => { setPicker(false); setMenu(false); }}>
      <div className="w-10 shrink-0">
        {compact ? (
          <span className="invisible block pt-1 text-right text-[10px] text-ink-muted group-hover:visible">{time(m.created_at)}</span>
        ) : <Avatar member={author} presence={presenceOf(author)} />}
      </div>
      <div className="min-w-0 flex-1">
        {!compact && (
          <div className="flex items-baseline gap-2">
            <span className="text-sm font-semibold">{author.name}</span>
            {author.kind === "agent" && <span className="rounded bg-blue-soft px-1 text-[9px] font-bold uppercase text-blue">IA</span>}
            <span className="text-[11px] text-ink-muted">{time(m.created_at)}</span>
          </div>
        )}
        {m.deleted ? (
          <p className="text-sm italic text-ink-muted">Message supprimé</p>
        ) : editing ? (
          <div className="mt-1">
            <textarea autoFocus value={draft} onChange={(e) => setDraft(e.target.value)} rows={Math.min(6, draft.split("\n").length + 1)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); saveEdit(); } if (e.key === "Escape") setEditing(false); }}
              className="w-full resize-none rounded-xl border border-accent bg-white px-3 py-2 text-sm outline-none" />
            <div className="mt-1 text-[11px] text-ink-muted">Entrée pour enregistrer · Échap pour annuler</div>
          </div>
        ) : (
          m.body && (
            <p className="whitespace-pre-wrap break-words text-[14.5px] leading-relaxed">
              {renderBody(m.body, members, me.id)}
              {m.edited_at && <span className="ml-1 text-[11px] text-ink-muted">(modifié)</span>}
            </p>
          )
        )}

        {!m.deleted && m.attachments.length > 0 && (
          <div className="mt-2 flex flex-wrap items-start gap-2">
            {m.attachments.map((a) => a.content_type.startsWith("image/") ? (
              <a key={a.id} href={a.url} target="_blank" rel="noreferrer" className="block w-[min(320px,100%)] overflow-hidden rounded-xl border border-line transition hover:shadow-md">
                <img src={a.url} alt={a.filename} className="block h-auto max-h-64 w-full object-cover" />
              </a>
            ) : (
              <a key={a.id} href={a.url} target="_blank" rel="noreferrer"
                className="flex w-64 items-center gap-3 rounded-xl border border-line bg-white px-3 py-2.5 transition hover:border-accent/40 hover:shadow-sm">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-soft text-blue"><FileText size={20} /></span>
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium">{a.filename}</span>
                  <span className="text-xs text-ink-muted">{fileSize(a.size)}</span>
                </span>
              </a>
            ))}
          </div>
        )}

        {m.reactions.length > 0 && (
          <div className="mt-1.5 flex flex-wrap gap-1">
            {m.reactions.map((r) => {
              const mineR = r.member_ids.includes(me.id);
              const names = r.member_ids.map((id) => members.find((x) => x.id === id)?.name.split(" ")[0]).join(", ");
              return (
                <button key={r.emoji} title={names} onClick={() => chat.react(m.id, r.emoji)}
                  className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs transition ${
                    mineR ? "border-accent/50 bg-accent-soft text-accent" : "border-line bg-white hover:border-ink-muted"}`}>
                  <span className="text-sm leading-none">{r.emoji}</span><span className="font-medium">{r.member_ids.length}</span>
                </button>
              );
            })}
          </div>
        )}

        {!inThread && m.reply_count > 0 && onReply && (
          <button onClick={() => onReply(m)} className="mt-1.5 flex items-center gap-2 rounded-lg py-1 pr-2 text-xs font-semibold text-accent hover:bg-accent-soft">
            <span className="flex -space-x-1.5">
              {m.reply_authors.slice(0, 3).map((id) => { const a = members.find((x) => x.id === id); return a ? <Avatar key={id} member={a} size="sm" ring /> : null; })}
            </span>
            {m.reply_count} réponse{m.reply_count > 1 ? "s" : ""}
            {m.last_reply_at && <span className="font-normal text-ink-muted">· dernière à {time(m.last_reply_at)}</span>}
          </button>
        )}
      </div>

      {!m.deleted && !editing && (
        <div className="absolute -top-3 right-3 z-10 hidden items-center rounded-xl border border-line bg-white p-0.5 shadow-md group-hover:flex">
          {QUICK.slice(0, 3).map((e) => (
            <button key={e} onClick={() => chat.react(m.id, e)} className="rounded-lg px-1.5 py-1 text-base hover:bg-surface">{e}</button>
          ))}
          <div className="relative">
            <button onClick={() => setPicker(!picker)} aria-label="Réagir" className="rounded-lg p-1.5 text-ink-soft hover:bg-surface"><SmilePlus size={17} /></button>
            {picker && (
              <div className="absolute right-0 top-9 grid grid-cols-4 gap-0.5 rounded-xl border border-line bg-white p-1.5 shadow-lg">
                {QUICK.map((e) => <button key={e} onClick={() => { chat.react(m.id, e); setPicker(false); }} className="rounded-lg p-1.5 text-lg hover:bg-surface">{e}</button>)}
              </div>
            )}
          </div>
          {!inThread && onReply && (
            <button onClick={() => onReply(m)} aria-label="Répondre dans un fil" title="Répondre dans un fil" className="rounded-lg p-1.5 text-ink-soft hover:bg-surface"><MessageSquareReply size={17} /></button>
          )}
          {mine && (
            <div className="relative">
              <button onClick={() => setMenu(!menu)} aria-label="Plus" className="rounded-lg p-1.5 text-ink-soft hover:bg-surface"><MoreHorizontal size={17} /></button>
              {menu && (
                <div className="absolute right-0 top-9 w-40 rounded-xl border border-line bg-white p-1 shadow-lg">
                  <button onClick={() => { setDraft(decodeMentions(m.body, members)); setEditing(true); setMenu(false); }}
                    className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-sm hover:bg-surface"><Pencil size={15} /> Modifier</button>
                  <button onClick={() => { if (confirm("Supprimer ce message ?")) chat.remove(m.id); }}
                    className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-sm text-busy hover:bg-[#FDE6E2]"><Trash2 size={15} /> Supprimer</button>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
