import { Bot } from "lucide-react";
import type { Member } from "../lib/api";
import { PRESENCE_COLOR, type Presence } from "../lib/presence";

const SIZES = { sm: "h-8 w-8 text-xs", md: "h-10 w-10 text-sm", lg: "h-16 w-16 text-xl" };

export function initials(name: string) {
  return name.split(/[\s-]+/).filter(Boolean).slice(0, 2).map((p) => p[0]!.toUpperCase()).join("");
}

export function Avatar({ member, presence, size = "md" }: { member: Member; presence?: Presence; size?: keyof typeof SIZES }) {
  return (
    <span className="relative inline-flex shrink-0">
      <span className={`${SIZES[size]} inline-flex items-center justify-center rounded-full bg-surface-2 font-semibold text-ink`}>
        {initials(member.name)}
      </span>
      {member.kind === "agent" && (
        <span title="Agent" className="absolute -left-1 -top-1 inline-flex h-4 w-4 items-center justify-center rounded-full border border-line bg-white text-ink-soft">
          <Bot size={10} />
        </span>
      )}
      {presence && (
        <span className={`absolute -bottom-0.5 -right-0.5 h-3.5 w-3.5 rounded-full border-2 border-white ${PRESENCE_COLOR[presence]}`} />
      )}
    </span>
  );
}
