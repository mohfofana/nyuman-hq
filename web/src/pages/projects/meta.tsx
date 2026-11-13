import { ArrowDown, ArrowUp, Minus } from "lucide-react";
import type { Task, TaskStatus } from "../../lib/api";

export const STATUS: Record<TaskStatus, { label: string; dot: string; pill: string }> = {
  todo: { label: "À faire", dot: "bg-offline", pill: "bg-surface-2 text-ink-soft" },
  doing: { label: "En cours", dot: "bg-blue", pill: "bg-blue-soft text-blue" },
  review: { label: "En revue", dot: "bg-away", pill: "bg-sun-soft text-[#8A6400]" },
  done: { label: "Terminé", dot: "bg-online", pill: "bg-[#E3F6EA] text-[#18794A]" },
};
export const STATUS_ORDER: TaskStatus[] = ["todo", "doing", "review", "done"];

export const PRIORITY = {
  high: { label: "Haute", icon: ArrowUp, cls: "text-busy" },
  normal: { label: "Normale", icon: Minus, cls: "text-ink-muted" },
  low: { label: "Basse", icon: ArrowDown, cls: "text-blue" },
} as const;

export const ICONS = ["📁", "🚀", "💰", "📣", "🤝", "⚖️", "📱", "🛠️", "🎯", "📊", "🗂️", "✂️", "💇🏾‍♀️", "🎉", "📝", "💡"];

export function StatusPill({ s }: { s: TaskStatus }) {
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-[11px] font-semibold ${STATUS[s].pill}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${STATUS[s].dot}`} />{STATUS[s].label}
    </span>
  );
}

const pad = (n: number) => String(n).padStart(2, "0");
export const isoDay = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
export const todayIso = () => isoDay(new Date());

export function dueLabel(t: Task): { text: string; tone: string } | null {
  if (!t.due_date) return null;
  const today = todayIso();
  const tomorrow = isoDay(new Date(Date.now() + 86400000));
  const d = new Date(t.due_date + "T00:00:00");
  const late = t.status !== "done" && t.due_date < today;
  const text = t.due_date === today ? "Aujourd'hui" : t.due_date === tomorrow ? "Demain"
    : d.toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
  return { text, tone: late ? "text-busy font-semibold" : t.due_date === today && t.status !== "done" ? "text-accent font-semibold" : "text-ink-soft" };
}
