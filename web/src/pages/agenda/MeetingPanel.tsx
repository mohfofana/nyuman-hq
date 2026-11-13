import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Ban, Check, CircleHelp, Clock, Copy, Hash, Send, Video, X } from "lucide-react";
import { meetings, type Meeting } from "../../lib/api";
import { useSession } from "../../lib/session";
import { useLive } from "../../lib/live";
import { Avatar } from "../../components/Avatar";
import { presenceOf } from "../../lib/presence";
import { hm, longDate, relativeStart } from "./time";

const RESP = {
  yes: { label: "Oui", icon: Check, cls: "bg-[#E3F6EA] text-[#18794A]" },
  maybe: { label: "Peut-être", icon: CircleHelp, cls: "bg-sun-soft text-[#8A6400]" },
  no: { label: "Non", icon: X, cls: "bg-[#FDE6E2] text-[#B5321F]" },
  pending: { label: "Pas répondu", icon: Clock, cls: "bg-surface text-ink-muted" },
} as const;

export function JoinButton({ m, size = "md" }: { m: Meeting; size?: "sm" | "md" }) {
  if (!m.link || m.cancelled) return null;
  const live = relativeStart(m.start_at, m.end_at).live;
  return (
    <a href={m.link} target="_blank" rel="noreferrer" onClick={() => { meetings.join(m.id); }}
      className={`inline-flex items-center justify-center gap-2 rounded-full font-semibold text-white shadow-sm transition ${
        live ? "bg-online shadow-online/30 hover:brightness-95" : "bg-accent shadow-accent/30 hover:bg-accent-hover"} ${
        size === "sm" ? "px-3 py-1.5 text-xs" : "px-5 py-2.5 text-sm"}`}>
      <Video size={size === "sm" ? 14 : 17} /> Rejoindre
    </a>
  );
}

export function MeetingPanel({ meeting, onClose }: { meeting: Meeting; onClose: () => void }) {
  const { me, members } = useSession();
  const { channels } = useLive();
  const navigate = useNavigate();
  const [notes, setNotes] = useState(meeting.notes);
  const [saved, setSaved] = useState<"idle" | "saving" | "saved">("idle");
  const [copied, setCopied] = useState(false);
  const timer = useRef<number | undefined>(undefined);
  useEffect(() => { setNotes(meeting.notes); }, [meeting.id]); // eslint-disable-line react-hooks/exhaustive-deps
  if (!me) return null;
  const organizer = members.find((x) => x.id === meeting.organizer_id);
  const mine = meeting.attendees.find((a) => a.member_id === me.id);
  const rel = relativeStart(meeting.start_at, meeting.end_at);
  const channel = channels.find((c) => c.id === meeting.channel_id);
  const isOrganizer = meeting.organizer_id === me.id;

  const onNotes = (v: string) => {
    setNotes(v); setSaved("saving");
    clearTimeout(timer.current);
    timer.current = window.setTimeout(async () => { await meetings.saveNotes(meeting.id, v); setSaved("saved"); }, 800);
  };

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-ink/30 backdrop-blur-[3px]" onClick={onClose}>
      <aside className="slide-in flex h-full w-full max-w-lg flex-col overflow-y-auto bg-white shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className={`relative px-6 pb-5 pt-6 ${meeting.cancelled ? "bg-surface" : "bg-gradient-to-br from-[#E9F0FA] to-[#F7FAFE]"}`}>
          <button onClick={onClose} aria-label="Fermer" className="absolute right-4 top-4 rounded-full bg-white/80 p-1.5 text-ink hover:bg-white"><X size={18} /></button>
          <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold ${
            meeting.cancelled ? "bg-[#FDE6E2] text-[#B5321F]" : rel.live ? "bg-online text-white" : "bg-white text-blue"}`}>
            {rel.live && !meeting.cancelled && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-white" />}
            {meeting.cancelled ? "Annulée" : rel.label}
          </span>
          <h2 className={`mt-3 text-2xl font-semibold tracking-tight ${meeting.cancelled ? "text-ink-muted line-through" : ""}`}>{meeting.title}</h2>
          <div className="mt-1 text-sm text-ink-soft">{longDate(meeting.start_at)} · {hm(meeting.start_at)} – {hm(meeting.end_at)}</div>
          {organizer && <div className="mt-1 text-xs text-ink-muted">Organisée par {organizer.name}</div>}
          {!meeting.cancelled && meeting.link && (
            <div className="mt-5 flex flex-wrap items-center gap-2">
              <JoinButton m={meeting} />
              <button onClick={async () => { await navigator.clipboard.writeText(meeting.link); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
                className="inline-flex items-center gap-1.5 rounded-full border border-line bg-white px-4 py-2.5 text-sm font-medium hover:border-blue/40">
                {copied ? <Check size={15} className="text-online" /> : <Copy size={15} />} {copied ? "Copié" : "Copier le lien"}
              </button>
              <span className="text-xs text-ink-muted">{meeting.link_kind === "jitsi" ? "Visio Jitsi" : "Google Meet"}</span>
            </div>
          )}
        </div>

        <div className="space-y-6 px-6 py-6">
          {!meeting.cancelled && (
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Vous venez ?</div>
              <div className="mt-2 grid grid-cols-3 gap-2">
                {(["yes", "maybe", "no"] as const).map((r) => {
                  const R = RESP[r];
                  const on = mine?.response === r;
                  return (
                    <button key={r} onClick={() => meetings.respond(meeting.id, r)}
                      className={`flex items-center justify-center gap-1.5 rounded-xl border py-2 text-sm font-medium transition ${on ? `${R.cls} border-transparent` : "border-line hover:bg-surface"}`}>
                      <R.icon size={15} /> {R.label}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          <div>
            <div className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Participants · {meeting.attendees.length}</div>
            <ul className="mt-2 space-y-1">
              {meeting.attendees.map((a) => {
                const m = members.find((x) => x.id === a.member_id);
                if (!m) return null;
                const R = RESP[a.response];
                return (
                  <li key={a.member_id} className="flex items-center gap-3 rounded-xl px-1 py-1.5">
                    <Avatar member={m} presence={presenceOf(m)} size="sm" />
                    <span className="flex-1 text-sm font-medium">{m.name}{a.member_id === meeting.organizer_id && <span className="font-normal text-ink-muted"> · organisateur</span>}</span>
                    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${R.cls}`}><R.icon size={12} /> {R.label}</span>
                  </li>
                );
              })}
            </ul>
          </div>

          {meeting.description && (
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Ordre du jour</div>
              <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed">{meeting.description}</p>
            </div>
          )}

          {channel && (
            <button onClick={() => navigate(`/discussions/${channel.id}`)} className="flex items-center gap-2 text-sm text-ink-soft hover:text-accent">
              <Hash size={15} /> Annoncée dans {channel.kind === "channel" ? `#${channel.name}` : "une discussion privée"}
            </button>
          )}

          <div>
            <div className="flex items-center justify-between">
              <div className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Compte rendu</div>
              <span className="text-[11px] text-ink-muted">{saved === "saving" ? "Enregistrement…" : saved === "saved" ? "Enregistré ✓" : ""}</span>
            </div>
            <textarea value={notes} onChange={(e) => onNotes(e.target.value)} rows={7}
              placeholder={"Décisions, qui fait quoi, prochaines étapes…\nTout le monde peut l'écrire pendant ou après la réunion."}
              className="mt-2 w-full resize-y rounded-2xl border border-line bg-surface/50 px-4 py-3 text-sm leading-relaxed outline-none focus:border-accent focus:bg-white" />
            <button disabled={!notes.trim() || saved === "saving"}
              onClick={async () => { const r = await meetings.publishNotes(meeting.id); navigate(`/discussions/${r.channel_id}`); }}
              className="mt-2 inline-flex items-center gap-2 rounded-full border border-line px-4 py-2 text-sm font-medium hover:border-accent hover:text-accent disabled:opacity-40">
              <Send size={15} /> Publier dans {channel?.kind === "channel" ? `#${channel.name}` : channel ? "la discussion" : "#général"}
            </button>
          </div>

          {isOrganizer && !meeting.cancelled && (
            <button onClick={() => { if (confirm("Annuler cette réunion pour tout le monde ?")) meetings.cancel(meeting.id); }}
              className="inline-flex items-center gap-2 text-sm font-medium text-busy hover:underline">
              <Ban size={15} /> Annuler la réunion
            </button>
          )}
        </div>
      </aside>
    </div>
  );
}
