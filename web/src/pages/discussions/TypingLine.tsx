import { useEffect, useState } from "react";
import type { Member } from "../../lib/api";
import { useLive } from "../../lib/live";

export function TypingLine({ channelId, parentId = null, members }: { channelId: string; parentId?: string | null; members: Member[] }) {
  const { typing } = useLive();
  const [, force] = useState(0);
  useEffect(() => { const i = setInterval(() => force((x) => x + 1), 1000); return () => clearInterval(i); }, []);
  const who = (typing[channelId] ?? []).filter((t) => t.until > Date.now() && (t.parent_id ?? null) === parentId)
    .map((t) => members.find((m) => m.id === t.member_id)?.name.split(" ")[0]).filter(Boolean);
  return (
    <div className="flex h-6 items-center gap-2 px-2 text-xs text-ink-soft">
      {who.length > 0 && (
        <>
          <span className="flex gap-0.5">
            {[0, 1, 2].map((i) => <span key={i} className="h-1.5 w-1.5 animate-bounce rounded-full bg-accent" style={{ animationDelay: `${i * 0.15}s` }} />)}
          </span>
          <span><b className="font-semibold">{who.join(", ")}</b> {who.length > 1 ? "écrivent" : "écrit"}…</span>
        </>
      )}
    </div>
  );
}
