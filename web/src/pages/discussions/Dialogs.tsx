import { useState, type ReactNode } from "react";
import { Check, Hash, Search, X } from "lucide-react";
import { chat, type Member } from "../../lib/api";
import { Avatar } from "../../components/Avatar";
import { useSession } from "../../lib/session";
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
  const { me, members } = useSession();
  const [name, setName] = useState("");
  const [topic, setTopic] = useState("");
  const [ferme, setFerme] = useState(true);
  const [choisis, setChoisis] = useState<string[]>([]);
  const [error, setError] = useState("");
  const create = async () => {
    try { onOpen((await chat.createChannel({ name, topic, private: ferme, member_ids: choisis })).id); }
    catch (e: any) {
      setError(e.status === 409 ? "Un canal porte déjà ce nom."
        : e.status === 403 ? "Seuls Mohamed et Abraham créent les canaux." : "Création impossible.");
    }
  };
  const autres = members.filter((m) => m.id !== me?.id);
  return (
    <Modal title="Nouveau canal" onClose={onClose}>
      <label className="text-sm font-medium">Nom</label>
      <div className="mt-1.5 flex items-center gap-2 rounded-xl border border-line px-3 py-2.5 focus-within:border-accent">
        <Hash size={16} className="text-accent" />
        <input autoFocus value={name} onChange={(e) => setName(e.target.value)} placeholder="ex. croissance" className="flex-1 text-sm outline-none" />
      </div>
      <label className="mt-4 block text-sm font-medium">De quoi parle-t-on ici ? <span className="font-normal text-ink-muted">(facultatif)</span></label>
      <input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="ex. Salons, contenus, lancement"
        className="mt-1.5 w-full rounded-xl border border-line px-3 py-2.5 text-sm outline-none focus:border-accent" />

      <div className="mt-4 flex rounded-xl bg-surface-2 p-1 text-sm font-medium">
        {([[true, "Participants choisis"], [false, "Toute l'équipe"]] as const).map(([v, l]) => (
          <button key={l} onClick={() => setFerme(v)}
            className={`flex-1 rounded-lg px-3 py-1.5 transition ${ferme === v ? "bg-white shadow-sm" : "text-ink-soft hover:text-ink"}`}>{l}</button>
        ))}
      </div>

      {ferme ? (
        <>
          <p className="mt-3 text-xs text-ink-muted">Seuls les choisis verront ce canal. Vous en faites partie d'office.</p>
          <MemberPicker members={autres} choisis={choisis} onChange={setChoisis} />
        </>
      ) : (
        <p className="mt-3 text-xs text-ink-muted">Les onze personnes et les agents verront ce canal.</p>
      )}

      {error && <p className="mt-2 text-sm text-busy">{error}</p>}
      <button disabled={!name.trim()} onClick={create}
        className="mt-5 w-full rounded-full bg-accent py-3 text-sm font-semibold text-white shadow-sm shadow-accent/30 hover:bg-accent-hover disabled:bg-surface-2 disabled:text-ink-muted disabled:shadow-none">
        Créer le canal
      </button>
    </Modal>
  );
}

/** Cocher des participants : les personnes puis les agents, dans la même liste. */
export function MemberPicker({ members, choisis, onChange, exclure = [] }: {
  members: Member[]; choisis: string[]; onChange: (ids: string[]) => void; exclure?: string[];
}) {
  const libres = members.filter((m) => !exclure.includes(m.id));
  const basculer = (id: string) =>
    onChange(choisis.includes(id) ? choisis.filter((x) => x !== id) : [...choisis, id]);
  const bloc = (titre: string, liste: Member[]) => liste.length === 0 ? null : (
    <div className="mt-2">
      <div className="px-1 pb-1 text-[11px] font-semibold uppercase tracking-wide text-ink-muted">{titre}</div>
      <div className="flex flex-wrap gap-1.5">
        {liste.map((m) => {
          const on = choisis.includes(m.id);
          return (
            <button key={m.id} onClick={() => basculer(m.id)}
              className={`flex items-center gap-2 rounded-full border py-1 pl-1 pr-3 text-sm transition ${
                on ? "border-accent bg-accent-soft text-accent" : "border-line hover:bg-surface"}`}>
              <Avatar member={m} size="sm" />
              {m.name.split(" ")[0]}
              {on && <Check size={13} />}
            </button>
          );
        })}
      </div>
    </div>
  );
  return (
    <div className="mt-1 max-h-56 overflow-y-auto">
      {bloc("Personnes", libres.filter((m) => m.kind === "human"))}
      {bloc("Agents", libres.filter((m) => m.kind === "agent"))}
    </div>
  );
}
