import { Fragment, useEffect, useLayoutEffect, useRef } from "react";
import type { Member, Message } from "../../lib/api";
import { MessageItem } from "./MessageItem";
import { dayLabel } from "./format";

const GROUP_MS = 5 * 60 * 1000;

export function MessageList({ messages, members, me, onReply, header, hasMore, loadOlder, inThread }: {
  messages: Message[]; members: Member[]; me: Member; onReply?: (m: Message) => void;
  header?: React.ReactNode; hasMore?: boolean; loadOlder?: () => void; inThread?: boolean;
}) {
  const box = useRef<HTMLDivElement>(null);
  const nearBottom = useRef(true);
  const count = useRef(0);

  useLayoutEffect(() => {
    const el = box.current;
    if (!el) return;
    const last = messages[messages.length - 1];
    const grew = messages.length > count.current;
    const appended = grew && count.current > 0 && last && messages[count.current - 1]?.id !== last.id;
    if (count.current === 0 || (appended && (nearBottom.current || last?.author_id === me.id))) el.scrollTop = el.scrollHeight;
    count.current = messages.length;
  }, [messages, me.id]);
  useEffect(() => { count.current = 0; }, [header]);

  return (
    <div ref={box} className="min-h-0 flex-1 overflow-y-auto px-2 pb-4 sm:px-4"
      onScroll={(e) => { const el = e.currentTarget; nearBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 120; }}>
      {hasMore && loadOlder && (
        <div className="py-3 text-center">
          <button onClick={loadOlder} className="rounded-full border border-line bg-white px-3 py-1 text-xs font-medium text-ink-soft hover:border-accent hover:text-accent">Messages plus anciens</button>
        </div>
      )}
      {header}
      {messages.map((m, i) => {
        const prev = messages[i - 1];
        const newDay = !prev || new Date(prev.created_at).toDateString() !== new Date(m.created_at).toDateString();
        const compact = !!prev && !newDay && prev.author_id === m.author_id && !prev.deleted &&
          new Date(m.created_at).getTime() - new Date(prev.created_at).getTime() < GROUP_MS && !prev.reply_count;
        return (
          <Fragment key={m.id}>
            {newDay && !inThread && (
              <div className="sticky top-0 z-[5] my-3 flex items-center gap-3 py-1">
                <div className="h-px flex-1 bg-line" />
                <span className="rounded-full border border-line bg-white px-3 py-0.5 text-[11px] font-semibold text-ink-soft shadow-sm">{dayLabel(m.created_at)}</span>
                <div className="h-px flex-1 bg-line" />
              </div>
            )}
            <MessageItem m={m} members={members} me={me} compact={compact} onReply={onReply} inThread={inThread} />
          </Fragment>
        );
      })}
    </div>
  );
}
