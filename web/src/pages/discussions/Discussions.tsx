import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { ArrowLeft, Hash, Lock, MessageSquarePlus, Plus, Search, Users, Video } from "lucide-react";
import { chat, type Channel, type Member } from "../../lib/api";
import { useSession } from "../../lib/session";
import { useLive } from "../../lib/live";
import { Avatar } from "../../components/Avatar";
import { lastSeenLabel, presenceLabel, presenceOf } from "../../lib/presence";
import { useChannelMessages } from "./useMessages";
import { MessageList } from "./MessageList";
import { Composer } from "./Composer";
import { ThreadPanel } from "./ThreadPanel";
import { TypingLine } from "./TypingLine";
import { NewChannelDialog, NewDmDialog } from "./Dialogs";
import { ChannelSettings, canManageChannels } from "./ChannelSettings";
import { channelTitle } from "./format";

function Unread({ c }: { c: Channel }) {
  if (c.mentions) return <span className="ml-auto rounded-full bg-accent px-1.5 text-[11px] font-bold leading-5 text-white">@{c.mentions}</span>;
  if (c.unread && c.kind === "dm") return <span className="ml-auto min-w-5 rounded-full bg-accent px-1.5 text-center text-[11px] font-bold leading-5 text-white">{c.unread}</span>;
  return null;
}

function ChannelRow({ c, active, members, me }: { c: Channel; active: boolean; members: Member[]; me: Member }) {
  const other = c.kind === "dm" ? members.find((m) => m.id === c.member_ids.find((id) => id !== me.id)) : undefined;
  const group = c.kind === "dm" && c.member_ids.length > 2;
  const bold = c.unread > 0;
  return (
    <Link to={`/discussions/${c.id}`}
      className={`flex items-center gap-2.5 rounded-xl px-2.5 py-1.5 text-sm transition ${active ? "bg-accent-soft font-semibold text-accent" : bold ? "font-semibold text-ink hover:bg-surface" : "text-ink-soft hover:bg-surface hover:text-ink"}`}>
      {c.kind === "channel" ? (
        <span className={`flex h-7 w-7 items-center justify-center rounded-lg ${active ? "bg-white text-accent" : "bg-surface-2"}`}
          title={c.private ? "Canal fermé" : undefined}>
          {c.private ? <Lock size={14} /> : <Hash size={15} />}
        </span>
      ) : other && !group ? (
        <Avatar member={other} presence={presenceOf(other)} size="sm" />
      ) : (
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-soft text-[11px] font-bold text-blue">{c.member_ids.length - 1}</span>
      )}
      <span className="truncate">{channelTitle(c, members, me.id)}</span>
      <Unread c={c} />
    </Link>
  );
}

function Sidebar({ activeId, onNewDm, onNewChannel }: { activeId?: string; onNewDm: () => void; onNewChannel?: () => void }) {
  const { me, members } = useSession();
  const { channels } = useLive();
  const [q, setQ] = useState("");
  if (!me) return null;
  const match = (c: Channel) => channelTitle(c, members, me.id).toLowerCase().includes(q.toLowerCase());
  const chans = channels.filter((c) => c.kind === "channel" && match(c));
  const dms = channels.filter((c) => c.kind === "dm" && match(c))
    .sort((a, b) => (b.last_message_at ?? "").localeCompare(a.last_message_at ?? ""));
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between px-4 pb-2 pt-5">
        <h1 className="text-xl font-semibold tracking-tight">Discussions</h1>
        <button onClick={onNewDm} title="Nouveau message" className="rounded-xl bg-accent p-2 text-white shadow-sm shadow-accent/30 hover:bg-accent-hover"><MessageSquarePlus size={18} /></button>
      </div>
      <div className="px-3 pb-2">
        <div className="flex items-center gap-2 rounded-xl bg-surface px-3 py-2 text-sm focus-within:ring-2 focus-within:ring-accent/20">
          <Search size={15} className="text-ink-muted" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filtrer" className="min-w-0 flex-1 bg-transparent outline-none" />
        </div>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-4">
        <div className="flex items-center justify-between px-2.5 pb-1 pt-3">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Canaux</span>
          {onNewChannel && <button onClick={onNewChannel} title="Nouveau canal" className="rounded-md p-0.5 text-ink-muted hover:bg-surface hover:text-accent"><Plus size={16} /></button>}
        </div>
        {chans.map((c) => <ChannelRow key={c.id} c={c} active={c.id === activeId} members={members} me={me} />)}
        <div className="flex items-center justify-between px-2.5 pb-1 pt-5">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Messages privés</span>
          <button onClick={onNewDm} title="Nouveau message" className="rounded-md p-0.5 text-ink-muted hover:bg-surface hover:text-accent"><Plus size={16} /></button>
        </div>
        {dms.map((c) => <ChannelRow key={c.id} c={c} active={c.id === activeId} members={members} me={me} />)}
        {!dms.length && !q && (
          <button onClick={onNewDm} className="mx-2.5 mt-1 text-left text-xs text-ink-muted hover:text-accent">Écrire à quelqu'un de l'équipe →</button>
        )}
      </div>
    </div>
  );
}

function ChatView({ channel }: { channel: Channel }) {
  const { me, members } = useSession();
  const { setActiveChannel, subscribe, tick } = useLive();
  const [params, setParams] = useSearchParams();
  const threadId = params.get("fil");
  const { messages, loading, hasMore, loadOlder } = useChannelMessages(channel.id);
  void tick;

  useEffect(() => {
    setActiveChannel(channel.id);
    chat.read(channel.id);
    const off = subscribe((ev) => {
      if (ev.type === "message.new" && ev.message.channel_id === channel.id && !document.hidden) chat.read(channel.id);
    });
    const onVis = () => { if (!document.hidden) chat.read(channel.id); };
    document.addEventListener("visibilitychange", onVis);
    return () => { off(); setActiveChannel(null); document.removeEventListener("visibilitychange", onVis); };
  }, [channel.id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!me) return null;
  const title = channelTitle(channel, members, me.id);
  const others = channel.member_ids.filter((id) => id !== me.id).map((id) => members.find((m) => m.id === id)!).filter(Boolean);
  const solo = channel.kind === "dm" && others.length === 1 ? others[0] : null;
  const openThread = (id: string | null) => {
    const p = new URLSearchParams(params);
    id ? p.set("fil", id) : p.delete("fil");
    setParams(p, { replace: true });
  };

  const [reglages, setReglages] = useState(false);
  // Les visages de l'en-tête : les participants d'un canal fermé, sinon toute l'équipe.
  const dedans = channel.private ? members.filter((m) => channel.member_ids.includes(m.id)) : members;

  const welcome = !hasMore && !loading && (
    <div className="px-3 pb-2 pt-8">
      {solo ? <Avatar member={solo} presence={presenceOf(solo)} size="lg" /> : (
        <span className="flex h-16 w-16 items-center justify-center rounded-2xl bg-accent-soft text-accent">
          {channel.private ? <Lock size={28} /> : <Hash size={30} />}
        </span>
      )}
      <h2 className="mt-3 text-2xl font-semibold tracking-tight">{channel.kind === "channel" ? `Bienvenue dans #${title}` : title}</h2>
      <p className="mt-1 text-sm text-ink-soft">
        {channel.kind === "channel" ? (channel.topic || "Le début de ce canal.") : solo ? `Le début de votre discussion avec ${solo.name}.` : "Le début de votre discussion de groupe."}
      </p>
    </div>
  );

  return (
    <div className="flex min-w-0 flex-1">
      <div className="flex min-w-0 flex-1 flex-col bg-white">
        <header className="flex h-16 shrink-0 items-center gap-3 border-b border-line px-3 sm:px-5">
          <Link to="/discussions" className="rounded-full p-1.5 text-ink-soft hover:bg-surface md:hidden" aria-label="Retour"><ArrowLeft size={20} /></Link>
          {solo ? <Avatar member={solo} presence={presenceOf(solo)} /> : channel.kind === "channel" ? (
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-soft text-accent"><Hash size={20} /></span>
          ) : null}
          <div className="min-w-0 flex-1">
            <div className="truncate font-semibold">{title}</div>
            <div className="truncate text-xs text-ink-muted">
              {solo ? (lastSeenLabel(solo) ? `${presenceLabel(solo, presenceOf(solo))} · ${lastSeenLabel(solo)}` : presenceLabel(solo, presenceOf(solo))) + (solo.status_message ? ` · « ${solo.status_message} »` : "")
                : channel.kind === "channel"
                  ? (channel.private
                      ? `Fermé · ${channel.member_ids.length} participants${channel.topic ? ` · ${channel.topic}` : ""}`
                      : channel.topic || "Toute l'équipe")
                  : `${others.length + 1} membres`}
            </div>
          </div>
          {channel.kind === "channel" && (
            <button onClick={() => setReglages(true)} title="Participants et réglages"
              className="flex items-center gap-1.5 rounded-full border border-line px-3 py-1.5 text-sm font-medium text-ink-soft transition hover:border-accent/40 hover:text-accent">
              <Users size={16} /> <span className="hidden sm:inline">Participants</span>
            </button>
          )}
          {channel.kind === "channel" && (
            <div className="hidden -space-x-2 lg:flex">
              {dedans.slice(0, 5).map((m) => <Avatar key={m.id} member={m} size="sm" ring />)}
              {dedans.length > 5 && <span className="flex h-8 w-8 items-center justify-center rounded-full bg-surface-2 text-[11px] font-semibold ring-2 ring-white">+{dedans.length - 5}</span>}
            </div>
          )}
          <Link to={`/agenda?nouvelle=1&canal=${channel.id}${channel.kind === "dm" ? `&avec=${others.map((o) => o.id).join(",")}` : ""}`}
            title="Planifier une réunion" className="flex items-center gap-1.5 rounded-full border border-line px-3 py-1.5 text-sm font-medium text-ink-soft transition hover:border-blue/40 hover:text-blue">
            <Video size={16} /> <span className="hidden sm:inline">Réunion</span>
          </Link>
        </header>
        {loading ? <div className="flex-1" /> : (
          <MessageList messages={messages} members={members} me={me} onReply={(m) => openThread(m.id)}
            header={welcome} hasMore={hasMore} loadOlder={loadOlder} />
        )}
        <div className="shrink-0 px-3 pb-3 sm:px-5 sm:pb-4">
          <TypingLine channelId={channel.id} members={members} />
          <Composer channelId={channel.id} members={members} me={me}
            placeholder={channel.kind === "channel" ? `Écrire dans #${title}` : `Écrire à ${title}`} />
        </div>
      </div>
      {threadId && <ThreadPanel rootId={threadId} channel={channel} members={members} me={me} onClose={() => openThread(null)} />}
      {reglages && <ChannelSettings channel={channel} onClose={() => setReglages(false)}
        onDeleted={() => { setReglages(false); window.location.href = "/discussions"; }} />}
    </div>
  );
}

export function Discussions() {
  const { me: moi } = useSession();
  const { channelId } = useParams();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { channels, refreshChannels } = useLive();
  const [dialog, setDialog] = useState<"dm" | "channel" | null>(null);
  const channel = useMemo(() => channels.find((c) => c.id === channelId), [channels, channelId]);

  // « Message » depuis une fiche : ouvre (ou crée) la discussion privée, une seule fois.
  const opening = useRef<string | null>(null);
  useEffect(() => {
    const avec = params.get("avec");
    if (!avec || opening.current === avec) return;
    opening.current = avec;
    const texte = params.get("texte");
    chat.openDm([avec]).then(async ({ id }) => {
      await refreshChannels();
      navigate(`/discussions/${id}${texte ? `?texte=${encodeURIComponent(texte)}` : ""}`, { replace: true });
    });
  }, [params]); // eslint-disable-line react-hooks/exhaustive-deps

  // Sur ordinateur, on ouvre « général » par défaut.
  useEffect(() => {
    if (!channelId && !params.get("avec") && window.matchMedia("(min-width: 768px)").matches && channels.length)
      navigate("/discussions/general", { replace: true });
  }, [channelId, channels.length]); // eslint-disable-line react-hooks/exhaustive-deps

  const open = async (id: string) => { setDialog(null); await refreshChannels(); navigate(`/discussions/${id}`); };

  return (
    <div className="flex h-full">
      <div className={`${channelId ? "hidden md:block" : "block"} w-full shrink-0 border-r border-line bg-white md:w-72`}>
        <Sidebar activeId={channelId} onNewDm={() => setDialog("dm")}
          onNewChannel={canManageChannels(moi?.id) ? () => setDialog("channel") : undefined} />
      </div>
      {channel ? <ChatView key={channel.id} channel={channel} /> : <div className="hidden flex-1 md:block" />}
      {dialog === "dm" && <DmDialogWrap onClose={() => setDialog(null)} onOpen={open} />}
      {dialog === "channel" && <NewChannelDialog onClose={() => setDialog(null)} onOpen={open} />}
    </div>
  );
}

function DmDialogWrap({ onClose, onOpen }: { onClose: () => void; onOpen: (id: string) => void }) {
  const { me, members } = useSession();
  if (!me) return null;
  return <NewDmDialog members={members} me={me} onClose={onClose} onOpen={onOpen} />;
}
