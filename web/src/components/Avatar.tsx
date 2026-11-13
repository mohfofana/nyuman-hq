import { Sparkles } from "lucide-react";
import type { Member } from "../lib/api";
import { PRESENCE_COLOR, type Presence } from "../lib/presence";

const SIZES = {
  sm: { box: "h-8 w-8 text-xs", dot: "h-3 w-3", badge: "h-4 w-4", icon: 9 },
  md: { box: "h-11 w-11 text-sm", dot: "h-3.5 w-3.5", badge: "h-5 w-5", icon: 11 },
  lg: { box: "h-20 w-20 text-2xl", dot: "h-5 w-5", badge: "h-7 w-7", icon: 15 },
};

/** Teintes douces de la palette officielle : chaque membre garde la sienne. */
const TINTS = [
  "bg-[#FBE3CF] text-[#9A4E0A]",
  "bg-[#DCE8F6] text-[#094D92]",
  "bg-[#FFEFC2] text-[#7A5600]",
  "bg-[#DDF0E4] text-[#23704A]",
  "bg-[#ECE4F7] text-[#5B3E8F]",
  "bg-[#FBE1E4] text-[#A33A4A]",
];
export function tintOf(id: string) {
  let h = 0;
  for (const c of id) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return TINTS[h % TINTS.length];
}

export function initials(name: string) {
  return name.split(/[\s-]+/).filter(Boolean).slice(0, 2).map((p) => p[0]!.toUpperCase()).join("");
}

export function Avatar({ member, presence, size = "md", ring }: {
  member: Member; presence?: Presence; size?: keyof typeof SIZES; ring?: boolean;
}) {
  const s = SIZES[size];
  return (
    <span className="relative inline-flex shrink-0">
      <span className={`${s.box} ${tintOf(member.id)} ${ring ? "ring-2 ring-white" : ""} inline-flex items-center justify-center rounded-full font-semibold`}>
        {initials(member.name)}
      </span>
      {member.kind === "agent" && (
        <span title="Agent IA" className={`${s.badge} absolute -right-1 -top-1 inline-flex items-center justify-center rounded-full border-2 border-white bg-blue text-white`}>
          <Sparkles size={s.icon} />
        </span>
      )}
      {presence && (
        <span className={`${s.dot} absolute -bottom-0.5 -right-0.5 rounded-full border-2 border-white ${PRESENCE_COLOR[presence]}`} />
      )}
    </span>
  );
}
