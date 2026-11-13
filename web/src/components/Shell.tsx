import { NavLink, Outlet } from "react-router-dom";
import { Bell, CalendarDays, FolderOpen, LayoutList, MessagesSquare, Search, Users } from "lucide-react";
import { StatusMenu } from "./StatusMenu";

export const NAV = [
  { to: "/activite", label: "Activité", icon: Bell },
  { to: "/discussions", label: "Discussions", icon: MessagesSquare },
  { to: "/agenda", label: "Agenda", icon: CalendarDays },
  { to: "/projets", label: "Projets", icon: LayoutList },
  { to: "/fichiers", label: "Fichiers", icon: FolderOpen },
  { to: "/equipe", label: "Équipe", icon: Users },
];

function NavItem({ to, label, icon: Icon, mobile }: (typeof NAV)[number] & { mobile?: boolean }) {
  return (
    <NavLink to={to} className={({ isActive }) =>
      `group flex flex-col items-center gap-1 rounded-xl ${mobile ? "flex-1 py-1.5" : "w-16 py-2"} text-[11px] font-medium transition ${
        isActive ? "text-accent" : "text-ink-soft hover:text-ink"}`}>
      {({ isActive }) => (
        <>
          <span className={`flex h-8 w-10 items-center justify-center rounded-lg ${isActive ? "bg-accent-soft" : "group-hover:bg-surface"}`}>
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
    <div className="flex h-full flex-col">
      <header className="flex h-14 shrink-0 items-center gap-3 border-b border-line px-4">
        <div className="flex items-center gap-2">
          <img src="/logo-mark.png" alt="Nyuman" className="h-7" />
          <span className="text-sm font-semibold">HQ</span>
        </div>
        <div className="mx-auto hidden w-full max-w-md items-center gap-2 rounded-full bg-surface px-4 py-2 text-sm text-ink-muted sm:flex">
          <Search size={16} /> Rechercher
        </div>
        <div className="ml-auto sm:ml-0"><StatusMenu /></div>
      </header>
      <div className="flex min-h-0 flex-1">
        <nav className="hidden w-20 shrink-0 flex-col items-center gap-1 border-r border-line py-3 sm:flex">
          {NAV.map((n) => <NavItem key={n.to} {...n} />)}
        </nav>
        <main className="min-w-0 flex-1 overflow-y-auto pb-20 sm:pb-0">
          <Outlet />
        </main>
      </div>
      <nav className="fixed inset-x-0 bottom-0 z-20 flex border-t border-line bg-white px-1 pb-[env(safe-area-inset-bottom)] sm:hidden">
        {NAV.map((n) => <NavItem key={n.to} {...n} mobile />)}
      </nav>
    </div>
  );
}
