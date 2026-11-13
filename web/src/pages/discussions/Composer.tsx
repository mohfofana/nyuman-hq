import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { FileText, Loader2, Paperclip, SendHorizontal, Smile, X } from "lucide-react";
import { chat, type Attachment, type Member } from "../../lib/api";
import { useLive } from "../../lib/live";
import { Avatar } from "../../components/Avatar";
import { QUICK, encodeMentions, fileSize } from "./format";

export function Composer({ channelId, parentId, members, me, placeholder, autoFocus }: {
  channelId: string; parentId?: string | null; members: Member[]; me: Member; placeholder: string; autoFocus?: boolean;
}) {
  const { sendTyping } = useLive();
  const [params] = useSearchParams();
  // Un bouton d'ailleurs peut proposer un message tout prêt : /discussions/<id>?texte=…
  const prefill = params.get("texte") ?? "";
  const [text, setText] = useState(prefill);
  const [files, setFiles] = useState<Attachment[]>([]);
  const [uploading, setUploading] = useState(0);
  const [error, setError] = useState("");
  const [query, setQuery] = useState<string | null>(null);
  const [sel, setSel] = useState(0);
  const [emoji, setEmoji] = useState(false);
  const [drag, setDrag] = useState(false);
  const ta = useRef<HTMLTextAreaElement>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  // En changeant de discussion, on repart d'une zone vide — ou du message proposé s'il y en a un.
  useEffect(() => { setText(prefill); setFiles([]); setError(""); }, [channelId, parentId, prefill]);
  useEffect(() => {
    const el = ta.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, [text]);

  const suggestions = query === null ? [] : members
    .filter((m) => m.id !== me.id && m.name.toLowerCase().includes(query.toLowerCase())).slice(0, 6);

  const onChange = (v: string) => {
    setText(v);
    if (v.trim()) sendTyping(channelId, parentId);
    const caret = ta.current?.selectionStart ?? v.length;
    const match = v.slice(0, caret).match(/(?:^|\s)@([\p{L}\p{N}-]*)$/u);
    setQuery(match ? match[1] : null);
    setSel(0);
  };

  const pick = (m: Member) => {
    const el = ta.current!;
    const caret = el.selectionStart;
    const before = text.slice(0, caret).replace(/@([\p{L}\p{N}-]*)$/u, `@${m.name} `);
    const next = before + text.slice(caret);
    setText(next);
    setQuery(null);
    requestAnimationFrame(() => { el.focus(); el.setSelectionRange(before.length, before.length); });
  };

  const upload = async (list: FileList | File[]) => {
    setError("");
    for (const f of Array.from(list).slice(0, 10)) {
      setUploading((n) => n + 1);
      try { const a = await chat.upload(f); setFiles((x) => [...x, a]); }
      catch (e: any) { setError(e.message || "Envoi impossible"); }
      finally { setUploading((n) => n - 1); }
    }
  };

  const send = async () => {
    const body = encodeMentions(text.trim(), members);
    if ((!body && !files.length) || uploading) return;
    setText(""); setFiles([]);
    try { await chat.send(channelId, body, parentId, files.map((f) => f.id)); }
    catch { setError("Le message n'est pas parti. Réessayez."); setText(text); }
  };

  return (
    <div className={`relative rounded-2xl border bg-white shadow-sm transition ${drag ? "border-accent ring-4 ring-accent/10" : "border-line focus-within:border-accent/60 focus-within:shadow-md"}`}
      onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)}
      onDrop={(e) => { e.preventDefault(); setDrag(false); upload(e.dataTransfer.files); }}>
      {suggestions.length > 0 && (
        <div className="absolute bottom-full left-2 mb-2 w-72 overflow-hidden rounded-2xl border border-line bg-white py-1 shadow-xl">
          <div className="px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Mentionner</div>
          {suggestions.map((m, i) => (
            <button key={m.id} onMouseDown={(e) => { e.preventDefault(); pick(m); }}
              className={`flex w-full items-center gap-2.5 px-3 py-2 text-left ${i === sel ? "bg-accent-soft" : "hover:bg-surface"}`}>
              <Avatar member={m} size="sm" />
              <span className="text-sm font-medium">{m.name}</span>
              <span className="truncate text-xs text-ink-muted">{m.title}</span>
            </button>
          ))}
        </div>
      )}
      {(files.length > 0 || uploading > 0) && (
        <div className="flex flex-wrap gap-2 border-b border-line p-2.5">
          {files.map((f) => (
            <span key={f.id} className="relative flex items-center gap-2 rounded-xl border border-line bg-surface py-1.5 pl-1.5 pr-7 text-xs">
              {f.content_type.startsWith("image/")
                ? <img src={f.url} alt="" className="h-9 w-9 rounded-lg object-cover" />
                : <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-soft text-blue"><FileText size={16} /></span>}
              <span><span className="block max-w-36 truncate font-medium">{f.filename}</span><span className="text-ink-muted">{fileSize(f.size)}</span></span>
              <button onClick={() => setFiles((x) => x.filter((y) => y.id !== f.id))} aria-label="Retirer" className="absolute right-1.5 top-1.5 rounded-full p-0.5 text-ink-muted hover:bg-white hover:text-ink"><X size={13} /></button>
            </span>
          ))}
          {uploading > 0 && <span className="flex items-center gap-2 px-2 text-xs text-ink-soft"><Loader2 size={14} className="animate-spin" /> Envoi…</span>}
        </div>
      )}
      <div className="flex items-end gap-1 p-2">
        <button onClick={() => fileInput.current?.click()} aria-label="Joindre un fichier" title="Joindre un fichier"
          className="rounded-xl p-2 text-ink-soft hover:bg-surface hover:text-accent"><Paperclip size={19} /></button>
        <input ref={fileInput} type="file" multiple hidden onChange={(e) => { e.target.files && upload(e.target.files); e.target.value = ""; }} />
        <textarea ref={ta} autoFocus={autoFocus} rows={1} value={text} placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
          onPaste={(e) => { if (e.clipboardData.files.length) { e.preventDefault(); upload(e.clipboardData.files); } }}
          onKeyDown={(e) => {
            if (suggestions.length) {
              if (e.key === "ArrowDown") { e.preventDefault(); setSel((s) => (s + 1) % suggestions.length); return; }
              if (e.key === "ArrowUp") { e.preventDefault(); setSel((s) => (s - 1 + suggestions.length) % suggestions.length); return; }
              if (e.key === "Enter" || e.key === "Tab") { e.preventDefault(); pick(suggestions[sel]); return; }
              if (e.key === "Escape") { setQuery(null); return; }
            }
            if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
          }}
          className="max-h-[200px] min-w-0 flex-1 resize-none bg-transparent px-1 py-2 text-[14.5px] outline-none placeholder:text-ink-muted" />
        <div className="relative">
          <button onClick={() => setEmoji(!emoji)} aria-label="Emoji" className="rounded-xl p-2 text-ink-soft hover:bg-surface hover:text-accent"><Smile size={19} /></button>
          {emoji && (
            <div className="absolute bottom-11 right-0 grid grid-cols-4 gap-0.5 rounded-xl border border-line bg-white p-1.5 shadow-lg">
              {QUICK.map((e) => <button key={e} onClick={() => { setText((t) => t + e); setEmoji(false); ta.current?.focus(); }} className="rounded-lg p-1.5 text-lg hover:bg-surface">{e}</button>)}
            </div>
          )}
        </div>
        <button onClick={send} disabled={(!text.trim() && !files.length) || uploading > 0} aria-label="Envoyer"
          className="rounded-xl bg-accent p-2.5 text-white shadow-sm shadow-accent/30 transition hover:bg-accent-hover disabled:bg-surface-2 disabled:text-ink-muted disabled:shadow-none">
          <SendHorizontal size={18} />
        </button>
      </div>
      {error && <div className="px-3 pb-2 text-xs text-busy">{error}</div>}
    </div>
  );
}
