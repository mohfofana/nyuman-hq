import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { chat, type Channel, type Member, type Message, type PresenceSnap } from "./api";
import { setPresenceSnaps } from "./presence";
import { useSession } from "./session";

type Listener = (ev: any) => void;
type Ctx = {
  tick: number;
  channels: Channel[];
  refreshChannels: () => Promise<void>;
  subscribe: (fn: Listener) => () => void;
  sendTyping: (channelId: string, parentId?: string | null) => void;
  typing: Record<string, { member_id: string; parent_id: string | null; until: number }[]>;
  setActiveChannel: (id: string | null) => void;
  notifPermission: NotificationPermission | "unsupported";
  askNotifications: () => Promise<void>;
};

const LiveCtx = createContext<Ctx>(null!);
export const useLive = () => useContext(LiveCtx);

const IDLE_AFTER_MS = 10 * 60 * 1000;

function plain(body: string, members: Member[]) {
  return body.replace(/<@([a-z0-9_-]+)>/g, (_, id) => "@" + (members.find((m) => m.id === id)?.name ?? id));
}

export function LiveProvider({ children }: { children: ReactNode }) {
  const { me, members, patchMember } = useSession();
  const [tick, setTick] = useState(0);
  const [channels, setChannels] = useState<Channel[]>([]);
  const [typing, setTyping] = useState<Ctx["typing"]>({});
  const [notifPermission, setNotif] = useState<Ctx["notifPermission"]>(
    typeof Notification === "undefined" ? "unsupported" : Notification.permission);
  const listeners = useRef(new Set<Listener>());
  const wsRef = useRef<WebSocket | null>(null);
  const snaps = useRef<Record<string, PresenceSnap>>({});
  const active = useRef<string | null>(null);
  const lastTyping = useRef(0);
  const membersRef = useRef(members);
  membersRef.current = members;

  const refreshChannels = useCallback(async () => { setChannels(await chat.channels()); }, []);

  const applySnaps = useCallback((list: PresenceSnap[]) => {
    for (const s of list) snaps.current[s.member_id] = s;
    setPresenceSnaps({ ...snaps.current });
    setTick((t) => t + 1);
  }, []);

  // Connexion temps réel, avec reconnexion automatique.
  useEffect(() => {
    if (!me) return;
    let closed = false;
    let retry = 0;
    let timer: number | undefined;
    const connect = () => {
      const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`);
      wsRef.current = ws;
      ws.onopen = () => { retry = 0; chat.presence().then(applySnaps); refreshChannels(); };
      ws.onmessage = (e) => {
        const ev = JSON.parse(e.data);
        if (ev.type === "presence") applySnaps([ev]);
        else if (ev.type === "member.updated") patchMember(ev.member);
        else if (ev.type === "typing") {
          setTyping((t) => {
            const list = (t[ev.channel_id] ?? []).filter((x) => x.member_id !== ev.member_id && x.until > Date.now());
            return { ...t, [ev.channel_id]: [...list, { member_id: ev.member_id, parent_id: ev.parent_id ?? null, until: Date.now() + 4000 }] };
          });
        } else if (ev.type === "message.new") {
          const m: Message = ev.message;
          setTyping((t) => ({ ...t, [m.channel_id]: (t[m.channel_id] ?? []).filter((x) => x.member_id !== m.author_id) }));
          refreshChannels();
          maybeNotify(m);
        } else if (ev.type === "channel.created") refreshChannels();
        listeners.current.forEach((fn) => fn(ev));
      };
      ws.onclose = () => {
        if (closed) return;
        timer = window.setTimeout(connect, Math.min(1000 * 2 ** retry++, 15000));
      };
    };
    connect();
    return () => { closed = true; clearTimeout(timer); wsRef.current?.close(); };
  }, [me?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  // Présence automatique : « Absent » après 10 minutes sans rien toucher.
  useEffect(() => {
    if (!me) return;
    let idle = false;
    let timer = window.setTimeout(goIdle, IDLE_AFTER_MS);
    function send(type: string) {
      if (wsRef.current?.readyState === WebSocket.OPEN) wsRef.current.send(JSON.stringify({ type }));
    }
    function goIdle() { idle = true; send("idle"); }
    function activity() {
      clearTimeout(timer);
      timer = window.setTimeout(goIdle, IDLE_AFTER_MS);
      if (idle) { idle = false; send("active"); }
    }
    const evs = ["mousemove", "keydown", "pointerdown", "scroll", "focus"];
    evs.forEach((e) => window.addEventListener(e, activity, { passive: true }));
    return () => { clearTimeout(timer); evs.forEach((e) => window.removeEventListener(e, activity)); };
  }, [me?.id]);

  // Le « vu il y a… » et le passage Absent → Hors ligne se recalculent chaque minute.
  useEffect(() => { const i = setInterval(() => setTick((t) => t + 1), 60000); return () => clearInterval(i); }, []);

  // Nombre de non-lus dans le titre de l'onglet.
  useEffect(() => {
    const n = channels.reduce((s, c) => s + (c.kind === "dm" || c.mentions ? c.unread : 0), 0);
    document.title = n ? `(${n}) Nyuman HQ` : "Nyuman HQ";
  }, [channels]);

  function maybeNotify(m: Message) {
    if (!me || m.author_id === me.id) return;
    if (me.manual_status === "dnd") return;
    const ch = channelsRef.current.find((c) => c.id === m.channel_id);
    const forMe = m.body.includes(`<@${me.id}>`) || ch?.kind === "dm" || !ch;
    if (!forMe) return;
    if (!document.hidden && active.current === m.channel_id) return;
    if (typeof Notification === "undefined" || Notification.permission !== "granted") return;
    const author = membersRef.current.find((x) => x.id === m.author_id)?.name ?? "Quelqu'un";
    const n = new Notification(ch?.kind === "channel" ? `${author} dans #${ch.name}` : author, {
      body: plain(m.body, membersRef.current) || "📎 Fichier", icon: "/logo-mark.png", tag: m.channel_id,
    });
    n.onclick = () => { window.focus(); location.assign(`/discussions/${m.channel_id}`); };
  }
  const channelsRef = useRef(channels);
  channelsRef.current = channels;

  const value: Ctx = {
    tick, channels, refreshChannels, typing,
    subscribe: (fn) => { listeners.current.add(fn); return () => listeners.current.delete(fn); },
    sendTyping: (channelId, parentId) => {
      if (Date.now() - lastTyping.current < 2500) return;
      lastTyping.current = Date.now();
      wsRef.current?.readyState === WebSocket.OPEN &&
        wsRef.current.send(JSON.stringify({ type: "typing", channel_id: channelId, parent_id: parentId ?? null }));
    },
    setActiveChannel: (id) => { active.current = id; },
    notifPermission,
    askNotifications: async () => {
      if (typeof Notification === "undefined") return;
      setNotif(await Notification.requestPermission());
    },
  };
  return <LiveCtx.Provider value={value}>{children}</LiveCtx.Provider>;
}
