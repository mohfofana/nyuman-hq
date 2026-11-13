import { NavLink, Outlet, useLocation } from "react-router-dom";
import { Bell, CalendarDays, FolderOpen, House, LayoutList, MessagesSquare, Search, Users } from "lucide-react";
import { StatusMenu } from "./StatusMenu";

export const NAV = [
  { to: "/accueil", label: "Accueil", icon: House },
  { to: "/discussions", label: "Discussions", icon: MessagesSquare },
  { to: "/agenda", label: "Agenda", icon: CalendarDays },
  { to: "/projets", label: "Projets", icon: LayoutList },
  { to: "/fichiers", label: "Fichiers", icon: FolderOpen },
  { to: "/equipe", label: "Équipe", icon: Users },
];

function NavItem({ to, label, icon: Icon, mobile }: (typeof NAV)[number] & { mobile?: boolean }) {
  return (
    <NavLink to={to} className={({ isActive }) =>
      `group relative flex flex-col items-center gap-1 ${mobile ? "flex-1 py-2" : "w-full py-2.5"} text-[11px] font-medium transition ${
        isActive ? "text-accent" : "text-ink-soft hover:text-ink"}`}>
      {({ isActive }) => (
        <>
          {!mobile && isActive && <span className="absolute left-0 top-2 bottom-2 w-1 rounded-r-full bg-accent" />}
          {mobile && isActive && <span className="absolute left-1/2 top-0 h-1 w-8 -translate-x-1/2 rounded-b-full bg-accent" />}
          <span className={`flex h-9 w-11 items-center justify-center rounded-xl transition ${isActive ? "bg-accent text-white shadow-sm shadow-accent/30" : "group-hover:bg-surface-2"}`}>
            <Icon size={20} strokeWidth={isActive ? 2.2 : 1.8} />
          </span>
          {label}
        </>
      )}
    </NavLink>
  );
}

export function Shell() {
  return (
    <div className="flex h-full flex-col bg-surface">
      <header className="flex h-14 shrink-0 items-center gap-4 bg-gradient-to-r from-accent-bright to-[#E8913A] px-4 text-white">
        <div className="flex items-center gap-2.5">
          <img src="/logo-wordmark.png" alt="Nyuman" className="logo-white h-4" />
          <span className="rounded-md bg-white/20 px-1.5 py-0.5 text-[11px] font-semibold tracking-wide">HQ</span>
        </div>
        <div className="mx-auto hidden w-full max-w-lg items-center gap-2 rounded-xl bg-white px-3.5 py-2 text-sm text-ink-muted shadow-sm ring-1 ring-black/5 sm:flex">
          <Search size={16} className="text-accent" />
          <span className="flex-1">Rechercher des messages, fichiers, personnes</span>
          <kbd className="rounded-md border border-line bg-surface px-1.5 py-0.5 text-[10px] font-medium text-ink-soft">⌘ K</kbd>
        </div>
        <div className="ml-auto flex items-center gap-2 sm:ml-0">
          <button aria-label="Notifications" className="relative flex h-9 w-9 items-center justify-center rounded-full text-white hover:bg-white/15">
            <Bell size={19} />
          </button>
          <StatusMenu />
        </div>
      </header>
      <div className="flex min-h-0 flex-1">
        <nav className="hidden w-[84px] shrink-0 flex-col items-center gap-0.5 border-r border-line bg-white py-3 sm:flex">
          {NAV.map((n) => <NavItem key={n.to} {...n} />)}
        </nav>
        <main className="min-w-0 flex-1 overflow-y-auto pb-20 sm:pb-0">
          <div key={useLocation().pathname} className="page-in h-full"><Outlet /></div>
        </main>
      </div>
      <nav className="fixed inset-x-0 bottom-0 z-20 flex border-t border-line bg-white/95 px-1 pb-[env(safe-area-inset-bottom)] backdrop-blur sm:hidden">
        {NAV.map((n) => <NavItem key={n.to} {...n} mobile />)}
      </nav>
    </div>
  );
}
