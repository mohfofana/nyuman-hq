import { useCallback, useEffect, useState } from "react";
import { chat, type Message } from "../../lib/api";
import { useLive } from "../../lib/live";

/** Messages d'un canal (sans les réponses de fils), tenus à jour en direct. */
export function useChannelMessages(channelId: string) {
  const { subscribe } = useLive();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [hasMore, setHasMore] = useState(false);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    chat.messages(channelId).then((list) => {
      if (!alive) return;
      setMessages(list); setHasMore(list.length >= 50); setLoading(false);
    });
    return () => { alive = false; };
  }, [channelId]);

  useEffect(() => subscribe((ev) => {
    const m: Message | undefined = ev.message;
    if (!m || m.channel_id !== channelId || m.parent_id) return;
    if (ev.type === "message.new") setMessages((l) => (l.some((x) => x.id === m.id) ? l : [...l, m]));
    if (ev.type === "message.updated") setMessages((l) => l.map((x) => (x.id === m.id ? m : x)));
  }), [channelId, subscribe]);

  const loadOlder = useCallback(async () => {
    if (!messages.length) return;
    const older = await chat.messages(channelId, messages[0].created_at);
    setHasMore(older.length >= 50);
    setMessages((l) => [...older, ...l]);
  }, [channelId, messages]);

  return { messages, loading, hasMore, loadOlder };
}

/** Un fil : message de départ + réponses, en direct. */
export function useThread(rootId: string | null) {
  const { subscribe } = useLive();
  const [root, setRoot] = useState<Message | null>(null);
  const [replies, setReplies] = useState<Message[]>([]);
  useEffect(() => {
    if (!rootId) return;
    setRoot(null); setReplies([]);
    chat.thread(rootId).then((t) => { setRoot(t.root); setReplies(t.replies); });
  }, [rootId]);
  useEffect(() => subscribe((ev) => {
    const m: Message | undefined = ev.message;
    if (!m || !rootId) return;
    if (m.id === rootId) setRoot(m);
    else if (m.parent_id === rootId) {
      if (ev.type === "message.new") setReplies((l) => (l.some((x) => x.id === m.id) ? l : [...l, m]));
      else setReplies((l) => l.map((x) => (x.id === m.id ? m : x)));
    }
  }), [rootId, subscribe]);
  return { root, replies };
}
