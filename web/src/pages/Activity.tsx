import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AtSign, BellRing, MessageSquareReply } from "lucide-react";
import { chat, type ActivityItem, type Member } from "../lib/api";
import { useSession } from "../lib/session";
import { useLive } from "../lib/live";
import { Avatar } from "../components/Avatar";
import { decodeMentions, time, dayLabel, channelTitle } from "./discussions/format";

export function useActivity() {
  const { me } = useSession();
  const { subscribe } = useLive();
  const [items, setItems] = useState<ActivityItem[] | null>(null);
  useEffect(() => { chat.activity().then(setItems); }, []);
  useEffect(() => subscribe((ev) => {
    if (ev.type === "message.new" && me && ev.message.author_id !== me.id) chat.activity().then(setItems);
  }), [subscribe, me]);
  return items;
}

export function ActivityRow({ item, members }: { item: ActivityItem; members: Member[] }) {
  const { me } = useSession();
  const { channels } = useLive();
  const m = item.message;
  const author = members.find((x) => x.id === m.author_id);
  const ch = channels.find((c) => c.id === m.channel_id);
  if (!author || !me) return null;
  const href = `/discussions/${m.channel_id}${m.parent_id ? `?fil=${m.parent_id}` : ""}`;
  return (
    <Link to={href} className="flex gap-3 rounded-2xl p-3 transition hover:bg-surface">
      <span className="relative">
        <Avatar member={author} size="sm" />
        <span className={`absolute -bottom-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full ring-2 ring-white ${item.kind === "mention" ? "bg-accent text-white" : "bg-blue text-white"}`}>
          {item.kind === "mention" ? <AtSign size={10} /> : <MessageSquareReply size={9} />}
        </span>
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-sm">
          <b className="font-semibold">{author.name.split(" ")[0]}</b>{" "}
          {item.kind === "mention" ? "vous a mentionné" : "a répondu dans un fil"}
          {ch && <span className="text-ink-muted"> · {ch.kind === "channel" ? "#" : ""}{channelTitle(ch, members, me.id)}</span>}
        </span>
        <span className="mt-0.5 line-clamp-2 block text-sm text-ink-soft">{decodeMentions(m.body, members) || "📎 Fichier"}</span>
      </span>
      <span className="shrink-0 text-[11px] text-ink-muted">{dayLabel(m.created_at) === "Aujourd'hui" ? time(m.created_at) : dayLabel(m.created_at)}</span>
    </Link>
  );
}

export function NotifButton() {
  const { notifPermission, askNotifications } = useLive();
  if (notifPermission === "granted" || notifPermission === "unsupported") return null;
  return (
    <button onClick={askNotifications} className="flex w-full items-center gap-3 rounded-2xl border border-dashed border-accent/40 bg-accent-soft/60 p-3 text-left text-sm transition hover:bg-accent-soft">
      <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent text-white"><BellRing size={17} /></span>
      <span><b className="font-semibold">Activer les notifications</b><span className="block text-xs text-ink-soft">Pour être prévenu des messages privés et des mentions.</span></span>
    </button>
  );
}

export function Activity() {
  const { members } = useSession();
  const items = useActivity();
  return (
    <div className="mx-auto max-w-2xl px-4 py-6 sm:py-8">
      <h1 className="text-3xl font-semibold tracking-tight">Activité</h1>
      <p className="mt-1 text-ink-soft">Les mentions et réponses qui vous concernent.</p>
      <div className="mt-5"><NotifButton /></div>
      <div className="mt-4 rounded-3xl border border-line bg-white p-2 shadow-sm">
        {items === null ? null : items.length === 0
          ? <p className="p-6 text-center text-sm text-ink-muted">Rien pour l'instant. Quand quelqu'un vous mentionne avec @, ça apparaît ici.</p>
          : items.map((it) => <ActivityRow key={it.message.id} item={it} members={members} />)}
      </div>
    </div>
  );
}
