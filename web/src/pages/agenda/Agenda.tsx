import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { ChevronLeft, ChevronRight, Plus, Video } from "lucide-react";
import { meetings, type Meeting } from "../../lib/api";
import { useSession } from "../../lib/session";
import { useLive } from "../../lib/live";
import { Avatar } from "../../components/Avatar";
import { DAY_END, DAY_START, addDays, hm, longDate, relativeStart, sameDay, startOfWeek } from "./time";
import { JoinButton, MeetingPanel } from "./MeetingPanel";
import { NewMeetingDialog } from "./NewMeetingDialog";

const HOUR_PX = 56;
const DAYS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];

export function useMeetingsRange(start: Date, end: Date) {
  const { subscribe } = useLive();
  const [list, setList] = useState<Meeting[]>([]);
  const load = useCallback(() => meetings.range(start, end).then(setList), [start.getTime(), end.getTime()]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { load(); }, [load]);
  useEffect(() => subscribe((ev) => { if (String(ev.type).startsWith("meeting.")) load(); }), [subscribe, load]);
  return list;
}

/** Répartit les réunions qui se chevauchent en colonnes. */
function lanes(list: Meeting[]) {
  const sorted = [...list].sort((a, b) => a.start_at.localeCompare(b.start_at));
  const out: { m: Meeting; lane: number; lanes: number }[] = [];
  let group: typeof out = [];
  let groupEnd = 0;
  const flush = () => { const n = Math.max(...group.map((g) => g.lane)) + 1; group.forEach((g) => (g.lanes = n)); out.push(...group); group = []; };
  for (const m of sorted) {
    const s = new Date(m.start_at).getTime();
    if (group.length && s >= groupEnd) flush();
    const used = new Set(group.filter((g) => new Date(g.m.end_at).getTime() > s).map((g) => g.lane));
    let lane = 0; while (used.has(lane)) lane++;
    group.push({ m, lane, lanes: 1 });
    groupEnd = Math.max(groupEnd, new Date(m.end_at).getTime());
  }
  if (group.length) flush();
  return out;
}

function EventBlock({ m, lane, lanesN, meId, onOpen }: { m: Meeting; lane: number; lanesN: number; meId: string; onOpen: () => void }) {
  const s = new Date(m.start_at), e = new Date(m.end_at);
  const top = ((s.getHours() + s.getMinutes() / 60) - DAY_START) * HOUR_PX;
  const height = Math.max(22, ((e.getTime() - s.getTime()) / 3600000) * HOUR_PX - 2);
  const mine = m.attendees.some((a) => a.member_id === meId && a.response !== "no");
  const live = relativeStart(m.start_at, m.end_at).live;
  const tone = m.cancelled ? "border-line bg-surface text-ink-muted line-through"
    : live ? "border-online bg-[#E3F6EA] text-[#145C38]"
    : mine ? "border-accent bg-accent-soft text-[#7A3E08]" : "border-blue bg-blue-soft text-blue";
  return (
    <button onClick={onOpen} title={m.title}
      className={`absolute overflow-hidden rounded-lg border-l-[3px] px-2 py-1 text-left text-xs shadow-sm transition hover:z-10 hover:shadow-md ${tone}`}
      style={{ top, height, left: `calc(${(lane / lanesN) * 100}% + 2px)`, width: `calc(${100 / lanesN}% - 4px)` }}>
      <div className="truncate font-semibold">{live && "● "}{m.title}</div>
      {height > 34 && <div className="truncate opacity-80">{hm(m.start_at)} – {hm(m.end_at)}</div>}
    </button>
  );
}

function WeekGrid({ week, list, meId, onOpen, onSlot }: {
  week: Date; list: Meeting[]; meId: string; onOpen: (m: Meeting) => void; onSlot: (d: Date) => void;
}) {
  const days = Array.from({ length: 7 }, (_, i) => addDays(week, i));
  const hours = Array.from({ length: DAY_END - DAY_START }, (_, i) => DAY_START + i);
  const now = new Date();
  const nowTop = ((now.getHours() + now.getMinutes() / 60) - DAY_START) * HOUR_PX;
  return (
    <div className="overflow-hidden rounded-3xl border border-line bg-white shadow-sm">
      <div className="grid grid-cols-[56px_repeat(7,1fr)] border-b border-line">
        <div />
        {days.map((d, i) => {
          const today = sameDay(d, now);
          return (
            <div key={i} className="py-3 text-center">
              <div className={`text-[11px] font-semibold uppercase tracking-wide ${today ? "text-accent" : "text-ink-muted"}`}>{DAYS[i]}</div>
              <div className={`mx-auto mt-1 flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold ${today ? "bg-accent text-white shadow-sm shadow-accent/30" : ""}`}>{d.getDate()}</div>
            </div>
          );
        })}
      </div>
      <div ref={(el) => { if (el && !el.dataset.scrolled) { el.dataset.scrolled = "1"; el.scrollTop = Math.max(0, nowTop - 2 * HOUR_PX); } }}
        className="max-h-[calc(100vh-260px)] overflow-y-auto">
        <div className="relative grid grid-cols-[56px_repeat(7,1fr)]" style={{ height: hours.length * HOUR_PX }}>
          <div className="relative">
            {hours.map((h) => <div key={h} className="absolute right-2 -translate-y-1/2 text-[11px] text-ink-muted" style={{ top: (h - DAY_START) * HOUR_PX }}>{h > DAY_START ? `${h}h` : ""}</div>)}
          </div>
          {days.map((d, i) => {
            const items = lanes(list.filter((m) => sameDay(new Date(m.start_at), d)));
            const today = sameDay(d, now);
            return (
              <div key={i} className={`relative border-l border-line ${today ? "bg-accent-soft/25" : ""}`}>
                {hours.map((h) => (
                  <button key={h} aria-label={`Planifier ${longDate(d)} à ${h}h`}
                    onClick={() => { const x = new Date(d); x.setHours(h, 0, 0, 0); onSlot(x); }}
                    className="absolute inset-x-0 border-t border-line/70 transition hover:bg-surface/80" style={{ top: (h - DAY_START) * HOUR_PX, height: HOUR_PX }} />
                ))}
                {items.map(({ m, lane, lanes: n }) => <EventBlock key={m.id} m={m} lane={lane} lanesN={n} meId={meId} onOpen={() => onOpen(m)} />)}
                {today && nowTop > 0 && nowTop < hours.length * HOUR_PX && (
                  <div className="pointer-events-none absolute inset-x-0 z-20" style={{ top: nowTop }}>
                    <div className="relative h-0.5 bg-busy"><span className="absolute -left-1 -top-1 h-2.5 w-2.5 rounded-full bg-busy" /></div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function DayList({ week, list, onOpen }: { week: Date; list: Meeting[]; onOpen: (m: Meeting) => void }) {
  const { members } = useSession();
  const [day, setDay] = useState(() => { const t = new Date(); return t >= week && t < addDays(week, 7) ? t : week; });
  const items = list.filter((m) => sameDay(new Date(m.start_at), day)).sort((a, b) => a.start_at.localeCompare(b.start_at));
  return (
    <div>
      <div className="grid grid-cols-7 gap-1 rounded-2xl bg-white p-1.5 shadow-sm ring-1 ring-line">
        {Array.from({ length: 7 }, (_, i) => addDays(week, i)).map((d, i) => {
          const on = sameDay(d, day), has = list.some((m) => sameDay(new Date(m.start_at), d) && !m.cancelled);
          return (
            <button key={i} onClick={() => setDay(d)} className={`rounded-xl py-2 text-center transition ${on ? "bg-accent text-white" : "hover:bg-surface"}`}>
              <div className={`text-[10px] font-semibold uppercase ${on ? "text-white/80" : "text-ink-muted"}`}>{DAYS[i]}</div>
              <div className="text-sm font-semibold">{d.getDate()}</div>
              <div className={`mx-auto mt-0.5 h-1 w-1 rounded-full ${has ? (on ? "bg-white" : "bg-accent") : "bg-transparent"}`} />
            </button>
          );
        })}
      </div>
      <h2 className="mt-5 text-sm font-semibold text-ink-soft">{longDate(day)}</h2>
      <div className="mt-2 space-y-2">
        {items.length === 0 && <p className="rounded-2xl bg-white p-6 text-center text-sm text-ink-muted shadow-sm">Aucune réunion ce jour-là.</p>}
        {items.map((m) => {
          const live = relativeStart(m.start_at, m.end_at).live;
          return (
            <div key={m.id} onClick={() => onOpen(m)} className={`flex cursor-pointer gap-3 rounded-2xl border bg-white p-4 shadow-sm ${live ? "border-online" : "border-line"}`}>
              <div className="w-12 shrink-0 text-sm"><div className="font-semibold">{hm(m.start_at)}</div><div className="text-xs text-ink-muted">{hm(m.end_at)}</div></div>
              <div className={`w-1 shrink-0 rounded-full ${m.cancelled ? "bg-line" : live ? "bg-online" : "bg-accent"}`} />
              <div className="min-w-0 flex-1">
                <div className={`font-semibold ${m.cancelled ? "text-ink-muted line-through" : ""}`}>{m.title}</div>
                <div className="mt-1.5 flex -space-x-1.5">
                  {m.attendees.slice(0, 6).map((a) => { const x = members.find((y) => y.id === a.member_id); return x ? <Avatar key={a.member_id} member={x} size="sm" ring /> : null; })}
                </div>
              </div>
              <div onClick={(e) => e.stopPropagation()} className="self-center"><JoinButton m={m} size="sm" /></div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function Agenda() {
  const { me } = useSession();
  const [params, setParams] = useSearchParams();
  const [week, setWeek] = useState(() => startOfWeek(new Date()));
  const [scope, setScope] = useState<"mine" | "all">("all");
  const [slot, setSlot] = useState<Date | undefined>();
  const end = useMemo(() => addDays(week, 7), [week]);
  const all = useMeetingsRange(week, end);
  const openId = params.get("r");
  const open = all.find((m) => m.id === openId) ?? null;
  const [fetched, setFetched] = useState<Meeting | null>(null);
  useEffect(() => { if (openId && !open) meetings.get(openId).then(setFetched).catch(() => setFetched(null)); }, [openId, open]);
  if (!me) return null;
  const list = scope === "mine" ? all.filter((m) => m.attendees.some((a) => a.member_id === me.id && a.response !== "no")) : all;
  const creating = params.get("nouvelle") === "1";
  const setParam = (k: string, v: string | null) => { const p = new URLSearchParams(params); v ? p.set(k, v) : p.delete(k); if (k === "nouvelle" && !v) { p.delete("avec"); p.delete("canal"); } setParams(p, { replace: true }); };
  const label = `${week.toLocaleDateString("fr-FR", { day: "numeric", month: "long" })} – ${addDays(week, 6).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" })}`;
  const panel = open ?? (fetched?.id === openId ? fetched : null);

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-8 sm:py-8">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="mr-auto text-3xl font-semibold tracking-tight">Agenda</h1>
        <div className="flex rounded-full bg-white p-1 shadow-sm ring-1 ring-line">
          {([["all", "Toute l'équipe"], ["mine", "Mes réunions"]] as const).map(([v, l]) => (
            <button key={v} onClick={() => setScope(v)} className={`rounded-full px-3.5 py-1.5 text-sm font-medium transition ${scope === v ? "bg-ink text-white" : "text-ink-soft hover:text-ink"}`}>{l}</button>
          ))}
        </div>
        <button onClick={() => { setSlot(undefined); setParam("nouvelle", "1"); }}
          className="inline-flex items-center gap-2 rounded-full bg-accent px-4 py-2.5 text-sm font-semibold text-white shadow-sm shadow-accent/30 hover:bg-accent-hover">
          <Plus size={17} /> Nouvelle réunion
        </button>
      </div>
      <div className="mt-4 flex items-center gap-2">
        <button onClick={() => setWeek(addDays(week, -7))} aria-label="Semaine précédente" className="rounded-full bg-white p-2 shadow-sm ring-1 ring-line hover:bg-surface"><ChevronLeft size={18} /></button>
        <button onClick={() => setWeek(startOfWeek(new Date()))} className="rounded-full bg-white px-3.5 py-2 text-sm font-medium shadow-sm ring-1 ring-line hover:bg-surface">Aujourd'hui</button>
        <button onClick={() => setWeek(addDays(week, 7))} aria-label="Semaine suivante" className="rounded-full bg-white p-2 shadow-sm ring-1 ring-line hover:bg-surface"><ChevronRight size={18} /></button>
        <span className="ml-2 text-sm font-medium text-ink-soft">{label}</span>
      </div>
      <div className="mt-5 hidden md:block">
        <WeekGrid week={week} list={list} meId={me.id} onOpen={(m) => setParam("r", m.id)} onSlot={(d) => { setSlot(d); setParam("nouvelle", "1"); }} />
      </div>
      <div className="mt-5 md:hidden"><DayList week={week} list={list} onOpen={(m) => setParam("r", m.id)} /></div>
      {!list.length && (
        <div className="mt-4 hidden items-center gap-3 rounded-2xl bg-blue-soft/60 p-4 text-sm text-blue md:flex">
          <Video size={18} /> Aucune réunion cette semaine. Cliquez sur un créneau de l'agenda pour en planifier une.
        </div>
      )}
      {panel && <MeetingPanel meeting={panel} onClose={() => setParam("r", null)} />}
      {creating && (
        <NewMeetingDialog
          initial={{ attendees: params.get("avec")?.split(",").filter(Boolean), channelId: params.get("canal"), start: slot }}
          onClose={() => setParam("nouvelle", null)}
          onCreated={(m) => { const p = new URLSearchParams(); p.set("r", m.id); setParams(p, { replace: true }); setWeek(startOfWeek(new Date(m.start_at))); }} />
      )}
    </div>
  );
}
