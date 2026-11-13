import { useEffect, useRef, useState } from "react";
import { LogOut } from "lucide-react";
import { useSession } from "../lib/session";
import { Avatar } from "./Avatar";
import { PRESENCE_COLOR, PRESENCE_LABEL, presenceOf, type Presence } from "../lib/presence";

const CHOICES: { value: Member["manual_status"]; presence: Presence; hint: string }[] = [
  { value: null, presence: "online", hint: "Automatique" },
  { value: "busy", presence: "busy", hint: "Les autres voient que vous êtes pris" },
  { value: "dnd", presence: "dnd", hint: "Les notifications se taisent" },
];
import type { Member } from "../lib/api";

export function StatusMenu() {
  const { me, updateMe, logout } = useSession();
  const [open, setOpen] = useState(false);
  const [msg, setMsg] = useState(me?.status_message ?? "");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const close = (e: MouseEvent) => { if (!ref.current?.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);
  if (!me) return null;
  const presence = presenceOf(me, me);

  return (
    <div ref={ref} className="relative">
      <button onClick={() => setOpen(!open)} aria-label="Mon statut" className="rounded-full">
        <Avatar member={me} presence={presence} size="sm" />
      </button>
      {open && (
        <div className="absolute right-0 top-11 z-30 w-72 rounded-2xl border border-line bg-white p-3 shadow-lg">
          <div className="flex items-center gap-3 px-1 pb-3">
            <Avatar member={me} presence={presence} />
            <div>
              <div className="text-sm font-semibold">{me.name}</div>
              <div className="text-xs text-ink-soft">{PRESENCE_LABEL[presence]}</div>
            </div>
          </div>
          <div className="border-t border-line pt-2">
            {CHOICES.map((c) => (
              <button key={String(c.value)} onClick={() => updateMe({ manual_status: c.value })}
                className={`flex w-full items-center gap-3 rounded-xl px-2 py-2 text-left hover:bg-surface ${me.manual_status === c.value ? "bg-surface" : ""}`}>
                <span className={`h-3 w-3 rounded-full ${PRESENCE_COLOR[c.presence]}`} />
                <span>
                  <span className="block text-sm">{PRESENCE_LABEL[c.presence]}</span>
                  <span className="block text-xs text-ink-muted">{c.hint}</span>
                </span>
              </button>
            ))}
          </div>
          <form className="mt-2 border-t border-line pt-3" onSubmit={(e) => { e.preventDefault(); updateMe({ status_message: msg }); }}>
            <label className="text-xs text-ink-soft">Message d'état</label>
            <input value={msg} onChange={(e) => setMsg(e.target.value)} placeholder="Ex. : en rendez-vous jusqu'à 15 h"
              className="mt-1 w-full rounded-xl border border-line px-3 py-2 text-sm outline-none focus:border-accent" />
          </form>
          <button onClick={logout} className="mt-3 flex w-full items-center gap-2 rounded-xl px-2 py-2 text-sm text-ink-soft hover:bg-surface">
            <LogOut size={16} /> Se déconnecter
          </button>
        </div>
      )}
    </div>
  );
}
