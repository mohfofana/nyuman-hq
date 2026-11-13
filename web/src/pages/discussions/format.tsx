import type { ReactNode } from "react";
import type { Channel, Member } from "../../lib/api";
import { MeetingCard } from "../../components/MeetingCard";
import { TimeCard } from "../../components/TimeCard";
import { ProposalCard } from "../../components/ProposalCard";

const TOKEN = /(<@[a-z0-9_-]+>|<meeting:[a-f0-9]+>|<proposal:[a-f0-9]+>|<temps:\d{4}-\d{2}-\d{2}>|https?:\/\/[^\s<]+)/g;

/** Affiche le texte d'un message : mentions en pastille, liens cliquables. */
export function renderBody(body: string, members: Member[], meId?: string): ReactNode[] {
  return body.split(TOKEN).map((part, i) => {
    const meeting = part.match(/^<meeting:([a-f0-9]+)>$/);
    if (meeting) return <MeetingCard key={i} id={meeting[1]} />;
    const prop = part.match(/^<proposal:([a-f0-9]+)>$/);
    if (prop) return <ProposalCard key={i} id={prop[1]} />;
    const temps = part.match(/^<temps:(\d{4}-\d{2}-\d{2})>$/);
    if (temps) return <TimeCard key={i} day={temps[1]} />;
    const mention = part.match(/^<@([a-z0-9_-]+)>$/);
    if (mention) {
      const m = members.find((x) => x.id === mention[1]);
      const mine = mention[1] === meId;
      return (
        <span key={i} className={`rounded-md px-1 py-0.5 font-medium ${mine ? "bg-accent text-white" : "bg-accent-soft text-accent"}`}>
          @{m?.name ?? mention[1]}
        </span>
      );
    }
    if (/^https?:\/\//.test(part))
      return <a key={i} href={part} target="_blank" rel="noreferrer" className="text-blue underline decoration-blue/30 hover:decoration-blue">{part}</a>;
    return part;
  });
}

/** « @Kevin » tapé dans la zone de texte → jeton <@kevin> envoyé au serveur. */
export function encodeMentions(text: string, members: Member[]): string {
  const sorted = [...members].sort((a, b) => b.name.length - a.name.length);
  let out = text;
  for (const m of sorted) out = out.split("@" + m.name).join(`<@${m.id}>`);
  return out;
}

export function decodeMentions(body: string, members: Member[]): string {
  return body.replace(/<meeting:[a-f0-9]+>/g, "📅 Réunion").replace(/<temps:[\d-]+>/g, "⏱️ Votre journée, sur quoi ?").replace(/<proposal:[a-f0-9]+>/g, "⚖️ Proposition au vote").replace(/<@([a-z0-9_-]+)>/g, (_, id) => "@" + (members.find((m) => m.id === id)?.name ?? id));
}

export function channelTitle(ch: Channel, members: Member[], meId?: string): string {
  if (ch.kind === "channel") return ch.name;
  const others = ch.member_ids.filter((id) => id !== meId);
  return others.map((id) => members.find((m) => m.id === id)?.name.split(" ")[0] ?? id).join(", ") || "Vous";
}

export const time = (iso: string) => new Date(iso).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });

export function dayLabel(iso: string): string {
  const d = new Date(iso);
  const today = new Date();
  const y = new Date(); y.setDate(today.getDate() - 1);
  if (d.toDateString() === today.toDateString()) return "Aujourd'hui";
  if (d.toDateString() === y.toDateString()) return "Hier";
  const s = d.toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" });
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function fileSize(n: number) {
  if (n < 1024) return `${n} o`;
  if (n < 1024 * 1024) return `${Math.round(n / 1024)} Ko`;
  return `${(n / 1024 / 1024).toFixed(1).replace(".", ",")} Mo`;
}

export const QUICK = ["👍", "❤️", "😂", "🎉", "✅", "🙏", "👀", "🔥"];
