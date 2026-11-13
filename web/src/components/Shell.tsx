import { useEffect, useRef, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useLive } from "../lib/live";
import { Bell, CalendarDays, FolderOpen, Gavel, House, LayoutList, MessagesSquare, MoreHorizontal, Search, Timer, Users, X } from "lucide-react";
import { StatusMenu } from "./StatusMenu";
import { Toasts } from "./Toasts";

export const NAV = [
  { to: "/accueil", label: "Mon espace", short: "Espace", icon: House },
  { to: "/discussions", label: "Discussions", icon: MessagesSquare },
  { to: "/agenda", label: "Agenda", icon: CalendarDays },
  { to: "/projets", label: "Projets", icon: LayoutList },
  { to: "/temps", label: "Temps", icon: Timer },
  { to: "/fichiers", label: "Fichiers", icon: FolderOpen },
  { to: "/equipe", label: "Équipe", icon: Users },
];

// Sur téléphone, la barre du bas ne garde que 4 onglets : le reste passe dans « Plus ».
const PHONE_NAV = NAV.slice(0, 4);
const PHONE_MORE = [...NAV.slice(4), { to: "/conseil", label: "Salle du conseil", icon: Gavel }];

function NavItem({ to, label, icon: Icon, mobile, ...rest }: (typeof NAV)[number] & { mobile?: boolean; short?: string }) {
  const { channels } = useLive();
  const badge = to === "/discussions"
    ? channels.reduce((n, c) => n + (c.kind === "dm" ? c.unread : c.mentions), 0)
    : 0;
  const dot = to === "/discussions" && !badge && channels.some((c) => c.unread > 0);
  return (
    <NavLink to={to} className={({ isActive }) =>
      `group relative flex flex-col items-center gap-1 ${mobile ? "flex-1 py-2" : "w-full py-2.5"} text-[11px] font-medium transition ${
        isActive ? "text-accent" : "text-ink-soft hover:text-ink"}`}>
      {({ isActive }) => (
        <>
          {!mobile && isActive && <span className="absolute left-0 top-2 bottom-2 w-1 rounded-r-full bg-accent" />}
          {mobile && isActive && <span className="absolute left-1/2 top-0 h-1 w-8 -translate-x-1/2 rounded-b-full bg-accent" />}
          <span className={`relative flex h-9 w-11 items-center justify-center rounded-xl transition ${isActive ? "bg-accent text-white shadow-sm shadow-accent/30" : "group-hover:bg-surface-2"}`}>
            <Icon size={20} strokeWidth={isActive ? 2.2 : 1.8} />
            {badge > 0 && <span className="absolute -top-0.5 right-1.5 min-w-[18px] rounded-full bg-busy px-1 text-center text-[10px] font-bold leading-[18px] text-white ring-2 ring-white">{badge > 99 ? "99+" : badge}</span>}
            {dot && <span className="absolute right-2.5 top-0.5 h-2 w-2 rounded-full bg-accent ring-2 ring-white" />}
          </span>
          {mobile && rest.short ? rest.short : label}
        </>
      )}
    </NavLink>
  );
}

function SearchBox() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); input.current?.focus(); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  return (
    <form onSubmit={(e) => { e.preventDefault(); if (q.trim()) navigate(`/recherche?q=${encodeURIComponent(q.trim())}`); }}
      className="mx-auto hidden w-full max-w-lg items-center gap-2 rounded-xl bg-white px-3.5 py-2 text-sm shadow-sm ring-1 ring-black/5 focus-within:ring-2 focus-within:ring-white/60 sm:flex">
      <Search size={16} className="text-accent" />
      <input ref={input} value={q} onChange={(e) => setQ(e.target.value)} placeholder="Rechercher des messages, personnes, canaux"
        className="min-w-0 flex-1 bg-transparent text-ink outline-none placeholder:text-ink-muted" />
      <kbd className="rounded-md border border-line bg-surface px-1.5 py-0.5 text-[10px] font-medium text-ink-soft">⌘ K</kbd>
    </form>
  );
}

/** Barre du bas du téléphone : 4 onglets + « Plus », qui ouvre le reste en feuille. */
function PhoneNav() {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();
  useEffect(() => { setOpen(false); }, [pathname]);
  const inMore = PHONE_MORE.some((n) => pathname.startsWith(n.to));
  return (
    <>
      {open && (
        <div className="fixed inset-0 z-30 bg-black/30 sm:hidden" onClick={() => setOpen(false)}>
          <div onClick={(e) => e.stopPropagation()}
            className="slide-in absolute inset-x-0 bottom-0 rounded-t-3xl bg-white p-4 pb-[calc(1rem+env(safe-area-inset-bottom))] shadow-xl">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-base font-semibold">Plus</h2>
              <button onClick={() => setOpen(false)} aria-label="Fermer" className="rounded-lg p-1 text-ink-soft hover:bg-surface"><X size={18} /></button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {PHONE_MORE.map(({ to, label, icon: Icon }) => (
                <NavLink key={to} to={to} className={({ isActive }) =>
                  `flex items-center gap-3 rounded-2xl border px-3 py-3 text-sm font-medium transition ${
                    isActive ? "border-accent bg-accent-soft text-accent" : "border-line hover:bg-surface"}`}>
                  <Icon size={19} /> {label}
                </NavLink>
              ))}
            </div>
          </div>
        </div>
      )}
      <nav className="fixed inset-x-0 bottom-0 z-20 flex border-t border-line bg-white/95 px-1 pb-[env(safe-area-inset-bottom)] backdrop-blur sm:hidden">
        {PHONE_NAV.map((n) => <NavItem key={n.to} {...n} mobile />)}
        <button onClick={() => setOpen(true)}
          className={`group relative flex flex-1 flex-col items-center gap-1 py-2 text-[11px] font-medium transition ${inMore ? "text-accent" : "text-ink-soft"}`}>
          {inMore && <span className="absolute left-1/2 top-0 h-1 w-8 -translate-x-1/2 rounded-b-full bg-accent" />}
          <span className={`flex h-9 w-11 items-center justify-center rounded-xl transition ${inMore ? "bg-accent text-white shadow-sm shadow-accent/30" : "group-hover:bg-surface-2"}`}>
            <MoreHorizontal size={20} strokeWidth={inMore ? 2.2 : 1.8} />
          </span>
          Plus
        </button>
      </nav>
    </>
  );
}

export function Shell() {
  const { channels } = useLive();
  const mentionCount = channels.reduce((n, c) => n + c.mentions, 0);
  return (
    <div className="flex h-full flex-col bg-surface">
      <header className="flex h-14 shrink-0 items-center gap-4 bg-gradient-to-r from-accent-bright to-[#E8913A] px-4 text-white">
        <div className="flex items-center gap-2.5">
          <img src="/logo-wordmark.png" alt="Nyuman" className="logo-white h-4" />
          <span className="rounded-md bg-white/20 px-1.5 py-0.5 text-[11px] font-semibold tracking-wide">HQ</span>
        </div>
        <SearchBox />
        <div className="ml-auto flex items-center gap-2 sm:ml-0">
          <Link to="/activite" aria-label="Activité" title="Activité" className="relative flex h-9 w-9 items-center justify-center rounded-full text-white hover:bg-white/15">
            <Bell size={19} />
            {mentionCount > 0 && <span className="absolute right-1 top-1 h-2.5 w-2.5 rounded-full bg-white ring-2 ring-accent-bright" />}
          </Link>
          <StatusMenu />
        </div>
      </header>
      <div className="flex min-h-0 flex-1">
        <nav className="hidden w-[84px] shrink-0 flex-col items-center gap-0.5 border-r border-line bg-white py-3 sm:flex">
          {NAV.map((n) => <NavItem key={n.to} {...n} />)}
        </nav>
        <main className="min-w-0 flex-1 overflow-y-auto pb-20 sm:pb-0">
          <div key={useLocation().pathname.split("/")[1]} className="page-in h-full"><Outlet /></div>
        </main>
      </div>
      <Toasts />
      <PhoneNav />
    </div>
  );
}
