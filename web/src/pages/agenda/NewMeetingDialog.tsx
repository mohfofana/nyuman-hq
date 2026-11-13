import { useEffect, useState } from "react";
import { Bell, CalendarDays, Check, Hash, Lock, Users, Video, X } from "lucide-react";
import { meetings, type Meeting } from "../../lib/api";
import { useSession } from "../../lib/session";
import { useLive } from "../../lib/live";
import { Avatar } from "../../components/Avatar";
import { channelTitle } from "../discussions/format";

const DURATIONS = [15, 30, 45, 60, 90];
const REMINDERS = [{ v: 5, l: "5 min avant" }, { v: 10, l: "10 min avant" }, { v: 15, l: "15 min avant" }, { v: 30, l: "30 min avant" }, { v: 60, l: "1 h avant" }];

function nextSlot() {
  const d = new Date();
  d.setMinutes(d.getMinutes() < 30 ? 30 : 60, 0, 0);
  return d;
}
const pad = (n: number) => String(n).padStart(2, "0");
const dateValue = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const timeValue = (d: Date) => `${pad(d.getHours())}:${pad(d.getMinutes())}`;

export function NewMeetingDialog({ initial, onClose, onCreated }: {
  initial: { attendees?: string[]; channelId?: string | null; start?: Date };
  onClose: () => void; onCreated: (m: Meeting) => void;
}) {
  const { me, members } = useSession();
  const { channels } = useLive();
  const start0 = initial.start ?? nextSlot();
  const [title, setTitle] = useState("");
  const [date, setDate] = useState(dateValue(start0));
  const [time, setTime] = useState(timeValue(start0));
  const [duration, setDuration] = useState(30);
  const [attendees, setAttendees] = useState<string[]>((initial.attendees ?? []).filter((id) => id !== me?.id));
  const [kind, setKind] = useState<"jitsi" | "meet">("jitsi");
  const [meetReady, setMeetReady] = useState(false);
  const [channelId, setChannelId] = useState<string>(initial.channelId ?? "");
  const [reminder, setReminder] = useState(10);
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => { meetings.config().then((c) => setMeetReady(c.google_meet)); }, []);
  if (!me) return null;
  const others = members.filter((m) => m.id !== me.id);
  const toggle = (id: string) => setAttendees((a) => (a.includes(id) ? a.filter((x) => x !== id) : [...a, id]));
  const all = attendees.length === others.length;

  const submit = async () => {
    setError("");
    const start = new Date(`${date}T${time}`);
    if (isNaN(start.getTime())) return setError("Date ou heure invalide.");
    setBusy(true);
    try {
      const m = await meetings.create({
        title: title.trim(), description, start_at: start.toISOString(),
        end_at: new Date(start.getTime() + duration * 60000).toISOString(),
        attendee_ids: attendees, link_kind: kind, channel_id: channelId || null, reminder_minutes: reminder,
      });
      onCreated(m);
    } catch (e: any) { setError(e.message || "Création impossible."); }
    finally { setBusy(false); }
  };

  const label = "text-xs font-semibold uppercase tracking-wide text-ink-muted";
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-ink/30 backdrop-blur-[2px] sm:items-center sm:p-4" onClick={onClose}>
      <div className="page-in flex max-h-[92vh] w-full max-w-xl flex-col rounded-t-3xl bg-white shadow-2xl sm:rounded-3xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-line px-6 py-4">
          <h2 className="flex items-center gap-2 text-lg font-semibold"><span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-soft text-blue"><CalendarDays size={17} /></span> Nouvelle réunion</h2>
          <button onClick={onClose} aria-label="Fermer" className="rounded-full p-1.5 text-ink-soft hover:bg-surface"><X size={19} /></button>
        </div>
        <div className="space-y-5 overflow-y-auto px-6 py-5">
          <input autoFocus value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Titre de la réunion"
            className="w-full border-b-2 border-line pb-2 text-xl font-semibold outline-none placeholder:text-ink-muted focus:border-accent" />

          <div className="grid grid-cols-2 gap-3">
            <label className="block"><span className={label}>Jour</span>
              <input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="mt-1.5 w-full rounded-xl border border-line px-3 py-2.5 text-sm outline-none focus:border-accent" /></label>
            <label className="block"><span className={label}>Heure</span>
              <input type="time" step={900} value={time} onChange={(e) => setTime(e.target.value)} className="mt-1.5 w-full rounded-xl border border-line px-3 py-2.5 text-sm outline-none focus:border-accent" /></label>
          </div>
          <div>
            <span className={label}>Durée</span>
            <div className="mt-1.5 flex flex-wrap gap-2">
              {DURATIONS.map((d) => (
                <button key={d} onClick={() => setDuration(d)}
                  className={`rounded-full px-3.5 py-1.5 text-sm font-medium transition ${duration === d ? "bg-accent text-white shadow-sm shadow-accent/30" : "bg-surface text-ink-soft hover:bg-surface-2"}`}>
                  {d < 60 ? `${d} min` : d === 60 ? "1 h" : "1 h 30"}
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between">
              <span className={label}>Participants</span>
              <button onClick={() => setAttendees(all ? [] : others.map((m) => m.id))} className="flex items-center gap-1 text-xs font-semibold text-accent hover:underline">
                <Users size={13} /> {all ? "Retirer tout le monde" : "Toute l'équipe"}
              </button>
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              {others.map((m) => {
                const on = attendees.includes(m.id);
                return (
                  <button key={m.id} onClick={() => toggle(m.id)}
                    className={`flex items-center gap-2 rounded-full border py-1 pl-1 pr-3 text-sm transition ${on ? "border-accent bg-accent-soft font-medium text-accent" : "border-line hover:border-ink-muted"}`}>
                    <Avatar member={m} size="sm" />{m.name.split(" ")[0]}{on && <Check size={14} />}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <span className={label}>Visio</span>
            <div className="mt-1.5 grid grid-cols-2 gap-2">
              <button onClick={() => setKind("jitsi")}
                className={`rounded-2xl border p-3 text-left transition ${kind === "jitsi" ? "border-accent bg-accent-soft/60 ring-2 ring-accent/15" : "border-line hover:bg-surface"}`}>
                <div className="flex items-center gap-2 text-sm font-semibold"><Video size={16} className="text-blue" /> Jitsi</div>
                <div className="mt-0.5 text-xs text-ink-soft">Gratuit, lien créé tout de suite</div>
              </button>
              <button disabled={!meetReady} onClick={() => setKind("meet")}
                className={`rounded-2xl border p-3 text-left transition disabled:cursor-not-allowed ${kind === "meet" ? "border-accent bg-accent-soft/60" : "border-line"} ${meetReady ? "hover:bg-surface" : "opacity-60"}`}>
                <div className="flex items-center gap-2 text-sm font-semibold">{meetReady ? <Video size={16} className="text-online" /> : <Lock size={15} />} Google Meet</div>
                <div className="mt-0.5 text-xs text-ink-soft">{meetReady ? "Avec le compte Google de l'équipe" : "Bientôt : à brancher par Kevin"}</div>
              </button>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block"><span className={label}><Hash size={11} className="mr-1 inline" />Annoncer dans</span>
              <select value={channelId} onChange={(e) => setChannelId(e.target.value)} className="mt-1.5 w-full rounded-xl border border-line bg-white px-3 py-2.5 text-sm outline-none focus:border-accent">
                <option value="">Ne pas annoncer</option>
                {channels.map((c) => <option key={c.id} value={c.id}>{c.kind === "channel" ? "#" : "💬 "}{channelTitle(c, members, me.id)}</option>)}
              </select></label>
            <label className="block"><span className={label}><Bell size={11} className="mr-1 inline" />Rappel</span>
              <select value={reminder} onChange={(e) => setReminder(+e.target.value)} className="mt-1.5 w-full rounded-xl border border-line bg-white px-3 py-2.5 text-sm outline-none focus:border-accent">
                {REMINDERS.map((r) => <option key={r.v} value={r.v}>{r.l}</option>)}
              </select></label>
          </div>

          <label className="block"><span className={label}>Ordre du jour <span className="font-normal normal-case">(facultatif)</span></span>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} placeholder="Les points à aborder"
              className="mt-1.5 w-full resize-none rounded-xl border border-line px-3 py-2.5 text-sm outline-none focus:border-accent" /></label>
          {error && <p className="text-sm text-busy">{error}</p>}
        </div>
        <div className="flex items-center justify-end gap-2 border-t border-line px-6 py-4">
          <button onClick={onClose} className="rounded-full px-4 py-2.5 text-sm font-medium text-ink-soft hover:bg-surface">Annuler</button>
          <button disabled={!title.trim() || busy} onClick={submit}
            className="rounded-full bg-accent px-6 py-2.5 text-sm font-semibold text-white shadow-sm shadow-accent/30 hover:bg-accent-hover disabled:bg-surface-2 disabled:text-ink-muted disabled:shadow-none">
            Planifier
          </button>
        </div>
      </div>
    </div>
  );
}
