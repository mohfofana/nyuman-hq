import type { LucideIcon } from "lucide-react";

const Bar = ({ w, className = "" }: { w: string; className?: string }) => (
  <div className={`h-2.5 rounded-full bg-surface-2 ${className}`} style={{ width: w }} />
);

function Chat() {
  return (
    <div className="grid h-full grid-cols-[220px_1fr] gap-0 overflow-hidden rounded-2xl border border-line bg-white">
      <div className="space-y-3 border-r border-line p-4">
        {["70%", "55%", "80%", "45%", "65%"].map((w, i) => (
          <div key={i} className={`flex items-center gap-2 rounded-lg p-1.5 ${i === 0 ? "bg-accent-soft" : ""}`}>
            <div className={`h-6 w-6 rounded-md ${i === 0 ? "bg-accent/30" : "bg-surface-2"}`} /><Bar w={w} />
          </div>
        ))}
      </div>
      <div className="flex flex-col justify-end space-y-4 p-5">
        {[["60%", false], ["40%", true], ["70%", false], ["35%", true]].map(([w, mine], i) => (
          <div key={i} className={`flex items-end gap-2 ${mine ? "justify-end" : ""}`}>
            {!mine && <div className="h-7 w-7 rounded-full bg-surface-2" />}
            <div className={`rounded-2xl px-4 py-3 ${mine ? "bg-accent-soft" : "bg-surface"}`} style={{ width: w as string }}><Bar w="80%" className={mine ? "bg-accent/20" : ""} /></div>
          </div>
        ))}
        <div className="h-11 rounded-xl border border-line" />
      </div>
    </div>
  );
}

function Calendar() {
  return (
    <div className="h-full overflow-hidden rounded-2xl border border-line bg-white p-4">
      <div className="grid grid-cols-5 gap-3">
        {Array.from({ length: 5 }).map((_, d) => (
          <div key={d} className="space-y-2">
            <Bar w="50%" />
            <div className="h-64 rounded-xl bg-surface p-2">
              {d % 2 === 0 && <div className="mt-6 h-14 rounded-lg border-l-4 border-blue bg-blue-soft" />}
              {d === 1 && <div className="mt-20 h-10 rounded-lg border-l-4 border-accent bg-accent-soft" />}
              {d === 3 && <div className="mt-12 h-16 rounded-lg border-l-4 border-sun bg-sun-soft" />}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Board() {
  const cols = [["bg-surface-2", 3], ["bg-sun", 2], ["bg-online", 2]] as const;
  return (
    <div className="grid h-full grid-cols-3 gap-4">
      {cols.map(([dot, n], c) => (
        <div key={c} className="space-y-3 rounded-2xl bg-white p-3 ring-1 ring-line">
          <div className="flex items-center gap-2"><span className={`h-2.5 w-2.5 rounded-full ${dot}`} /><Bar w="40%" /></div>
          {Array.from({ length: n }).map((_, i) => (
            <div key={i} className="space-y-2 rounded-xl border border-line p-3">
              <Bar w="85%" /><Bar w="55%" />
              <div className="flex justify-between pt-1"><div className="h-5 w-5 rounded-full bg-surface-2" /><Bar w="25%" /></div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function Files() {
  const tones = ["bg-accent-soft", "bg-blue-soft", "bg-sun-soft", "bg-[#E3F6EA]"];
  return (
    <div className="grid h-full grid-cols-2 gap-4 sm:grid-cols-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="rounded-2xl bg-white p-3 ring-1 ring-line">
          <div className={`h-24 rounded-xl ${tones[i % 4]}`} />
          <Bar w="75%" className="mt-3" /><Bar w="45%" className="mt-2" />
        </div>
      ))}
    </div>
  );
}

const KINDS = { chat: Chat, calendar: Calendar, board: Board, files: Files };
const TONES = { orange: "bg-accent text-white", blue: "bg-blue text-white", sun: "bg-sun text-ink" };

export function Preview({ kind, icon: Icon, title, text, bullets, soon, tone = "orange" }: {
  kind: keyof typeof KINDS; icon: LucideIcon; title: string; text: string; bullets: string[]; soon: string; tone?: keyof typeof TONES;
}) {
  const Mock = KINDS[kind];
  return (
    <div className="relative h-full min-h-[560px] overflow-hidden p-4 sm:p-8">
      <div className="pointer-events-none h-full [mask-image:linear-gradient(to_bottom,black_55%,transparent)]" aria-hidden><Mock /></div>
      <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-b from-surface/0 via-surface/45 to-surface/95 px-4">
        <div className="w-full max-w-md rounded-3xl border border-line bg-white p-7 shadow-[0_24px_48px_-24px_rgba(30,26,23,0.3)]">
          <div className="flex items-center justify-between">
            <span className={`flex h-12 w-12 items-center justify-center rounded-2xl shadow-sm ${TONES[tone]}`}><Icon size={24} /></span>
            <span className="rounded-full bg-accent-soft px-3 py-1 text-xs font-semibold text-accent">{soon}</span>
          </div>
          <h2 className="mt-5 text-2xl font-semibold tracking-tight">{title}</h2>
          <p className="mt-1.5 text-sm leading-relaxed text-ink-soft">{text}</p>
          <ul className="mt-5 space-y-2">
            {bullets.map((b) => (
              <li key={b} className="flex items-center gap-2.5 text-sm">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-accent-soft text-[11px] font-bold text-accent">✓</span>{b}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
