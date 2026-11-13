import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { BellRing, CalendarPlus, X } from "lucide-react";
import type { Meeting } from "../lib/api";
import { useLive } from "../lib/live";
import { useSession } from "../lib/session";
import { JoinButton } from "../pages/agenda/MeetingPanel";
import { hm, relativeStart } from "../pages/agenda/time";

type Toast = { key: string; kind: "reminder" | "invited"; meeting: Meeting; by?: string };

/** Rappels de réunion et invitations, en bas à droite (et notification du navigateur). */
export function Toasts() {
  const { subscribe } = useLive();
  const { members, me } = useSession();
  const [toasts, setToasts] = useState<Toast[]>([]);
  useEffect(() => subscribe((ev) => {
    if (ev.type !== "meeting.reminder" && ev.type !== "meeting.invited") return;
    const kind = ev.type === "meeting.reminder" ? "reminder" : "invited";
    const m: Meeting = ev.meeting;
    setToasts((t) => [...t.filter((x) => x.key !== kind + m.id), { key: kind + m.id, kind, meeting: m, by: ev.by }]);
    if (typeof Notification !== "undefined" && Notification.permission === "granted" && me?.manual_status !== "dnd") {
      const by = members.find((x) => x.id === ev.by)?.name;
      new Notification(kind === "reminder" ? `Réunion ${relativeStart(m.start_at, m.end_at).label.toLowerCase()}` : `${by ?? "On"} vous invite à une réunion`,
        { body: `${m.title} · ${hm(m.start_at)}`, icon: "/logo-mark.png", tag: m.id });
    }
  }), [subscribe, members, me]);
  if (!toasts.length) return null;
  return (
    <div className="fixed bottom-24 right-4 z-[60] flex w-[min(360px,calc(100vw-2rem))] flex-col gap-2 sm:bottom-6">
      {toasts.map((t) => {
        const by = members.find((x) => x.id === t.by);
        return (
          <div key={t.key} className="page-in rounded-2xl border border-line bg-white p-4 shadow-2xl">
            <div className="flex items-start gap-3">
              <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${t.kind === "reminder" ? "bg-accent text-white" : "bg-blue-soft text-blue"}`}>
                {t.kind === "reminder" ? <BellRing size={19} /> : <CalendarPlus size={19} />}
              </span>
              <div className="min-w-0 flex-1">
                <div className="text-xs font-semibold text-ink-muted">
                  {t.kind === "reminder" ? relativeStart(t.meeting.start_at, t.meeting.end_at).label : `${by?.name.split(" ")[0] ?? "Quelqu'un"} vous invite`}
                </div>
                <div className="truncate font-semibold">{t.meeting.title}</div>
                <div className="text-xs text-ink-soft">{hm(t.meeting.start_at)} – {hm(t.meeting.end_at)}</div>
              </div>
              <button onClick={() => setToasts((x) => x.filter((y) => y.key !== t.key))} aria-label="Fermer" className="rounded-full p-1 text-ink-muted hover:bg-surface"><X size={16} /></button>
            </div>
            <div className="mt-3 flex gap-2">
              {t.kind === "reminder" ? <JoinButton m={t.meeting} size="sm" /> : (
                <Link to={`/agenda?r=${t.meeting.id}`} onClick={() => setToasts((x) => x.filter((y) => y.key !== t.key))}
                  className="rounded-full bg-accent px-3 py-1.5 text-xs font-semibold text-white">Voir et répondre</Link>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
