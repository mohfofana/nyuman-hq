import { X } from "lucide-react";
import type { Channel, Member } from "../../lib/api";
import { useThread } from "./useMessages";
import { MessageItem } from "./MessageItem";
import { MessageList } from "./MessageList";
import { Composer } from "./Composer";
import { TypingLine } from "./TypingLine";
import { channelTitle } from "./format";

export function ThreadPanel({ rootId, channel, members, me, onClose }: {
  rootId: string; channel: Channel; members: Member[]; me: Member; onClose: () => void;
}) {
  const { root, replies } = useThread(rootId);
  return (
    <aside className="slide-in fixed inset-0 z-30 flex flex-col bg-white lg:static lg:z-auto lg:w-[400px] lg:shrink-0 lg:border-l lg:border-line">
      <div className="flex h-16 shrink-0 items-center justify-between border-b border-line px-4">
        <div>
          <div className="font-semibold">Fil de discussion</div>
          <div className="text-xs text-ink-muted">{channel.kind === "channel" ? "#" : ""}{channelTitle(channel, members, me.id)}</div>
        </div>
        <button onClick={onClose} aria-label="Fermer le fil" className="rounded-full p-1.5 text-ink-soft hover:bg-surface"><X size={19} /></button>
      </div>
      {root && (
        <MessageList inThread messages={replies} members={members} me={me}
          header={
            <div className="border-b border-line pb-3">
              <MessageItem m={root} members={members} me={me} compact={false} inThread />
              <div className="mt-3 flex items-center gap-3 px-3 text-xs text-ink-muted">
                {replies.length} réponse{replies.length > 1 ? "s" : ""}<div className="h-px flex-1 bg-line" />
              </div>
            </div>
          } />
      )}
      <div className="shrink-0 px-3 pb-3 sm:px-4">
        <TypingLine channelId={channel.id} parentId={rootId} members={members} />
        <Composer channelId={channel.id} parentId={rootId} members={members} me={me} placeholder="Répondre dans le fil…" autoFocus />
      </div>
    </aside>
  );
}
