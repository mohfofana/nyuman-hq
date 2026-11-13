import { useState, type ReactNode } from "react";
import { Check, Hash, Search, X } from "lucide-react";
import { chat, type Member } from "../../lib/api";
import { Avatar } from "../../components/Avatar";
import { presenceOf } from "../../lib/presence";

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-ink/30 p-0 backdrop-blur-[2px] sm:items-center sm:p-4" onClick={onClose}>
      <div className="page-in w-full max-w-md rounded-t-3xl bg-white p-6 shadow-2xl sm:rounded-3xl" onClick={(e) => e.stopPropagation()}>
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button onClick={onClose} aria-label="Fermer" className="rounded-full p-1.5 text-ink-soft hover:bg-surface"><X size={19} /></button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function NewDmDialog({ members, me, onClose, onOpen }: {
  members: Member[]; me: Member; onClose: () => void; onOpen: (id: string) => void;
}) {
  const [q, setQ] = useState("");
  const [picked, setPicked] = useState<string[]>([]);
  const list = members.filter((m) => m.id !== me.id && m.name.toLowerCase().includes(q.toLowerCase()));
  const toggle = (id: string) => setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]));
  return (
    <Modal title="Nouveau message" onClose={onClose}>
      <div className="flex items-center gap-2 rounded-xl border border-line px-3 py-2 focus-within:border-accent">
        <Search size={16} className="text-ink-muted" />
        <input autoFocus value={q} onChange={(e) => setQ(e.target.value)} placeholder="Chercher une personne ou un agent" className="flex-1 text-sm outline-none" />
      </div>
      <div className="mt-3 max-h-80 space-y-0.5 overflow-y-auto">
        {list.map((m) => (
          <button key={m.id} onClick={() => toggle(m.id)}
            className={`flex w-full items-center gap-3 rounded-xl px-2.5 py-2 text-left ${picked.includes(m.id) ? "bg-accent-soft" : "hover:bg-surface"}`}>
            <Avatar member={m} presence={presenceOf(m)} size="sm" />
            <span className="flex-1"><span className="block text-sm font-medium">{m.name}</span><span className="text-xs text-ink-muted">{m.title}</span></span>
            <span className={`flex h-5 w-5 items-center justify-center rounded-full border ${picked.includes(m.id) ? "border-accent bg-accent text-white" : "border-line"}`}>
              {picked.includes(m.id) && <Check size={13} />}
            </span>
          </button>
        ))}
      </div>
      <button disabled={!picked.length} onClick={async () => onOpen((await chat.openDm(picked)).id)}
        className="mt-5 w-full rounded-full bg-accent py-3 text-sm font-semibold text-white shadow-sm shadow-accent/30 hover:bg-accent-hover disabled:bg-surface-2 disabled:text-ink-muted disabled:shadow-none">
        {picked.length > 1 ? `Écrire à ${picked.length} personnes` : "Écrire"}
      </button>
    </Modal>
  );
}

export function NewChannelDialog({ onClose, onOpen }: { onClose: () => void; onOpen: (id: string) => void }) {
  const [name, setName] = useState("");
  const [topic, setTopic] = useState("");
  const [error, setError] = useState("");
  const create = async () => {
    try { onOpen((await chat.createChannel(name, topic)).id); }
    catch (e: any) { setError(e.status === 409 ? "Un canal porte déjà ce nom." : "Création impossible."); }
  };
  return (
    <Modal title="Nouveau canal" onClose={onClose}>
      <label className="text-sm font-medium">Nom</label>
      <div className="mt-1.5 flex items-center gap-2 rounded-xl border border-line px-3 py-2.5 focus-within:border-accent">
        <Hash size={16} className="text-accent" />
        <input autoFocus value={name} onChange={(e) => setName(e.target.value)} placeholder="ex. lancement-12-12" className="flex-1 text-sm outline-none" />
      </div>
      <label className="mt-4 block text-sm font-medium">De quoi parle-t-on ici ? <span className="font-normal text-ink-muted">(facultatif)</span></label>
      <input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="ex. Tout pour le lancement public"
        className="mt-1.5 w-full rounded-xl border border-line px-3 py-2.5 text-sm outline-none focus:border-accent" />
      <p className="mt-3 text-xs text-ink-muted">Toute l'équipe pourra lire et écrire dans ce canal.</p>
      {error && <p className="mt-2 text-sm text-busy">{error}</p>}
      <button disabled={!name.trim()} onClick={create}
        className="mt-5 w-full rounded-full bg-accent py-3 text-sm font-semibold text-white shadow-sm shadow-accent/30 hover:bg-accent-hover disabled:bg-surface-2 disabled:text-ink-muted disabled:shadow-none">
        Créer le canal
      </button>
    </Modal>
  );
}
