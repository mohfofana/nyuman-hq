import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CalendarDays } from "lucide-react";
import { meetings, type Meeting } from "../lib/api";
import { useLive } from "../lib/live";
import { useSession } from "../lib/session";
import { Avatar } from "./Avatar";
import { JoinButton } from "../pages/agenda/MeetingPanel";
import { hm, longDate, relativeStart } from "../pages/agenda/time";

/** Carte d'une réunion, affichée dans une discussion ou sur l'accueil. */
export function MeetingCard({ id, initial }: { id: string; initial?: Meeting }) {
  const { members } = useSession();
  const { subscribe } = useLive();
  const [m, setM] = useState<Meeting | null>(initial ?? null);
  useEffect(() => { if (!initial) meetings.get(id).then(setM).catch(() => setM(null)); }, [id, initial]);
  useEffect(() => subscribe((ev) => { if (ev.meeting?.id === id) setM(ev.meeting); }), [id, subscribe]);
  if (!m) return null;
  const rel = relativeStart(m.start_at, m.end_at);
  return (
    <div className={`my-1 flex max-w-md items-center gap-3 rounded-2xl border bg-white p-3 shadow-sm ${rel.live && !m.cancelled ? "border-online" : "border-line"}`}>
      <Link to={`/agenda?r=${m.id}`} className="flex min-w-0 flex-1 items-center gap-3">
        <span className="flex h-12 w-12 shrink-0 flex-col items-center justify-center rounded-xl bg-blue-soft text-blue">
          <span className="text-[10px] font-bold uppercase leading-none">{new Date(m.start_at).toLocaleDateString("fr-FR", { month: "short" }).replace(".", "")}</span>
          <span className="text-lg font-bold leading-tight">{new Date(m.start_at).getDate()}</span>
        </span>
        <span className="min-w-0">
          <span className={`block truncate text-sm font-semibold ${m.cancelled ? "text-ink-muted line-through" : ""}`}>
            <CalendarDays size={13} className="mr-1 inline text-blue" />{m.title}
          </span>
          <span className="block text-xs text-ink-soft">{m.cancelled ? "Annulée" : rel.live ? "En cours" : `${longDate(m.start_at)} · ${hm(m.start_at)}–${hm(m.end_at)}`}</span>
          <span className="mt-1 flex -space-x-1.5">
            {m.attendees.slice(0, 5).map((a) => { const x = members.find((y) => y.id === a.member_id); return x ? <Avatar key={a.member_id} member={x} size="sm" ring /> : null; })}
          </span>
        </span>
      </Link>
      {!rel.past && <JoinButton m={m} size="sm" />}
    </div>
  );
}
