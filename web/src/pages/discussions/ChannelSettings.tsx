import { useEffect, useState } from "react";
import { Check, Lock, Pencil, Trash2, Users, X } from "lucide-react";
import { chat, type Channel, type ChannelDetail } from "../../lib/api";
import { useSession } from "../../lib/session";
import { Avatar } from "../../components/Avatar";
import { MemberPicker } from "./Dialogs";

/** Qui peut gérer les canaux. Même liste que côté serveur (Mohamed et Abraham). */
export const CHANNEL_ADMINS = ["mohamed", "abraham"];
export const canManageChannels = (id?: string) => !!id && CHANNEL_ADMINS.includes(id);

/** Réglages d'un canal : participants, nom, suppression. Comme un groupe WhatsApp. */
export function ChannelSettings({ channel, onClose, onDeleted }: {
  channel: Channel; onClose: () => void; onDeleted: () => void;
}) {
  const { me, members } = useSession();
  const [detail, setDetail] = useState<ChannelDetail | null>(null);
  const [ajout, setAjout] = useState<string[] | null>(null);
  const [nom, setNom] = useState<string | null>(null);
  const [sujet, setSujet] = useState<string | null>(null);
  const [confirme, setConfirme] = useState(false);
  const [erreur, setErreur] = useState("");
  const admin = canManageChannels(me?.id);

  useEffect(() => { chat.channelMembers(channel.id).then(setDetail).catch(() => setDetail(null)); }, [channel.id]);
  if (!detail) return null;

  const dedans = members.filter((m) => detail.member_ids.includes(m.id));
  const garde = async (p: Promise<ChannelDetail>) => {
    setErreur("");
    try { setDetail(await p); }
    catch (e: any) { setErreur(e.status === 409 ? "Un canal porte déjà ce nom." : "Impossible pour l'instant."); }
  };

  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center bg-black/30 p-0 sm:items-center sm:p-4" onClick={onClose}>
      <div onClick={(e) => e.stopPropagation()}
        className="slide-in flex max-h-[85vh] w-full max-w-md flex-col rounded-t-3xl bg-white sm:rounded-3xl">
        <div className="flex items-center justify-between border-b border-line p-4">
          <h2 className="flex items-center gap-2 text-lg font-semibold">
            {detail.private && <Lock size={16} className="text-accent" />} #{detail.name}
          </h2>
          <button onClick={onClose} aria-label="Fermer" className="rounded-lg p-1 text-ink-soft hover:bg-surface"><X size={18} /></button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto p-4">
          {/* Nom et sujet */}
          {admin && (
            <div className="mb-4 space-y-2">
              {nom === null ? (
                <button onClick={() => setNom(detail.name)} className="flex items-center gap-1.5 text-sm font-medium text-accent hover:underline">
                  <Pencil size={13} /> Renommer le canal
                </button>
              ) : (
                <form onSubmit={(e) => { e.preventDefault(); garde(chat.updateChannel(detail.id, { name: nom })).then(() => setNom(null)); }}
                  className="flex gap-2">
                  <input autoFocus value={nom} onChange={(e) => setNom(e.target.value)}
                    className="min-w-0 flex-1 rounded-xl border border-line px-3 py-2 text-sm outline-none focus:border-accent" />
                  <button className="rounded-xl bg-accent px-3 py-2 text-sm font-semibold text-white">OK</button>
                  <button type="button" onClick={() => setNom(null)} className="text-sm text-ink-soft">Annuler</button>
                </form>
              )}
              {sujet === null ? (
                <button onClick={() => setSujet(detail.topic)} className="flex items-center gap-1.5 text-sm font-medium text-accent hover:underline">
                  <Pencil size={13} /> {detail.topic ? "Changer le sujet" : "Ajouter un sujet"}
                </button>
              ) : (
                <form onSubmit={(e) => { e.preventDefault(); garde(chat.updateChannel(detail.id, { topic: sujet })).then(() => setSujet(null)); }}
                  className="flex gap-2">
                  <input autoFocus value={sujet} onChange={(e) => setSujet(e.target.value)} placeholder="De quoi parle-t-on ici ?"
                    className="min-w-0 flex-1 rounded-xl border border-line px-3 py-2 text-sm outline-none focus:border-accent" />
                  <button className="rounded-xl bg-accent px-3 py-2 text-sm font-semibold text-white">OK</button>
                  <button type="button" onClick={() => setSujet(null)} className="text-sm text-ink-soft">Annuler</button>
                </form>
              )}
            </div>
          )}

          {/* Participants */}
          {detail.private ? (
            <>
              <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-ink-muted">
                <Users size={13} /> Participants · {dedans.length}
              </h3>
              <ul className="divide-y divide-line">
                {dedans.map((m) => (
                  <li key={m.id} className="group flex items-center gap-2.5 py-2">
                    <Avatar member={m} size="sm" />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-medium">{m.name}</span>
                      <span className="block truncate text-xs text-ink-muted">{m.title}</span>
                    </span>
                    {admin && m.id !== me?.id && (
                      <button onClick={() => garde(chat.removeMember(detail.id, m.id))} title={`Retirer ${m.name}`}
                        className="rounded-lg p-1.5 text-ink-muted opacity-0 hover:bg-surface hover:text-busy group-hover:opacity-100">
                        <X size={15} />
                      </button>
                    )}
                  </li>
                ))}
              </ul>
              {admin && (ajout === null ? (
                <button onClick={() => setAjout([])} className="mt-3 text-sm font-medium text-accent hover:underline">
                  Ajouter quelqu'un
                </button>
              ) : (
                <div className="mt-3 rounded-2xl bg-surface p-3">
                  <MemberPicker members={members} choisis={ajout} onChange={setAjout} exclure={detail.member_ids} />
                  <div className="mt-3 flex gap-2">
                    <button disabled={ajout.length === 0}
                      onClick={() => garde(chat.addMembers(detail.id, ajout)).then(() => setAjout(null))}
                      className="rounded-xl bg-accent px-3.5 py-2 text-sm font-semibold text-white disabled:opacity-40">
                      <Check size={14} className="mr-1 inline" /> Ajouter
                    </button>
                    <button onClick={() => setAjout(null)} className="text-sm text-ink-soft">Annuler</button>
                  </div>
                </div>
              ))}
            </>
          ) : (
            <div className="rounded-2xl bg-surface p-4 text-sm text-ink-soft">
              Ce canal est ouvert : toute l'équipe le voit.
              {admin && (
                <button onClick={() => garde(chat.updateChannel(detail.id, { private: true }))}
                  className="mt-2 block font-medium text-accent hover:underline">
                  Le fermer et choisir les participants
                </button>
              )}
            </div>
          )}

          {erreur && <p className="mt-3 text-sm text-busy">{erreur}</p>}
        </div>

        {admin && (
          <div className="border-t border-line p-4">
            {confirme ? (
              <div className="rounded-2xl bg-[#FDE6E2] p-3 text-sm">
                <p className="font-medium text-[#B5321F]">Supprimer #{detail.name} ?</p>
                <p className="mt-0.5 text-xs text-[#B5321F]">Il disparaîtra pour tout le monde. C'est sans retour.</p>
                <div className="mt-2.5 flex gap-2">
                  <button onClick={async () => { await chat.deleteChannel(detail.id); onDeleted(); }}
                    className="rounded-xl bg-busy px-3.5 py-2 text-sm font-semibold text-white">Supprimer</button>
                  <button onClick={() => setConfirme(false)} className="text-sm text-ink-soft">Annuler</button>
                </div>
              </div>
            ) : (
              <button onClick={() => setConfirme(true)}
                className="flex items-center gap-1.5 text-sm font-medium text-ink-soft hover:text-busy">
                <Trash2 size={14} /> Supprimer ce canal
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
