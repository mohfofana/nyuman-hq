import type { LucideIcon } from "lucide-react";

const TONES = {
  orange: "bg-accent-soft text-accent",
  blue: "bg-blue-soft text-blue",
  sun: "bg-sun-soft text-[#9A6B00]",
};

export function Placeholder({ icon: Icon, title, text, tone = "orange", soon }: {
  icon: LucideIcon; title: string; text: string; tone?: keyof typeof TONES; soon?: string;
}) {
  return (
    <div className="flex h-full items-center justify-center px-6">
      <div className="w-full max-w-md rounded-3xl border border-line bg-white p-8 text-center shadow-sm">
        <span className={`mx-auto flex h-16 w-16 items-center justify-center rounded-2xl ${TONES[tone]}`}><Icon size={30} /></span>
        <h2 className="mt-5 text-xl font-semibold">{title}</h2>
        <p className="mt-2 text-sm leading-relaxed text-ink-soft">{text}</p>
        {soon && <span className="mt-5 inline-block rounded-full bg-surface px-3 py-1 text-xs font-medium text-ink-soft">{soon}</span>}
      </div>
    </div>
  );
}
