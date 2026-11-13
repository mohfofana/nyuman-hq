import type { LucideIcon } from "lucide-react";

export function Placeholder({ icon: Icon, title, text }: { icon: LucideIcon; title: string; text: string }) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-6 text-center">
      <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-surface text-ink-soft"><Icon size={26} /></span>
      <h2 className="mt-4 text-lg font-semibold">{title}</h2>
      <p className="mt-1 max-w-sm text-sm text-ink-soft">{text}</p>
    </div>
  );
}
