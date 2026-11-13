import { ChevronRight } from "lucide-react";
import { useSession } from "../lib/session";
import { Avatar } from "../components/Avatar";

export function Login() {
  const { members, login } = useSession();
  const humans = members.filter((m) => m.kind === "human");
  const agents = members.filter((m) => m.kind === "agent");
  return (
    <div className="flex min-h-full flex-col bg-surface lg:flex-row">
      <section className="relative flex flex-col justify-between overflow-hidden bg-gradient-to-br from-[#CF6A12] via-accent-bright to-[#EC9A45] px-8 py-10 text-white lg:w-[46%] lg:px-14 lg:py-14">
        <span className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-white/10" />
        <span className="pointer-events-none absolute -bottom-32 -left-16 h-80 w-80 rounded-full bg-sun/25" />
        <img src="/logo-wordmark.png" alt="Nyuman" className="logo-white relative h-6 w-fit" />
        <div className="relative mt-10 lg:mt-0">
          <h1 className="text-3xl font-semibold leading-tight lg:text-5xl">Le QG de<br />l'équipe Nyuman.</h1>
          <p className="mt-4 max-w-sm text-white/85">Discussions, réunions, projets et fichiers, avec toute l'équipe, humains et agents.</p>
          <div className="mt-8 flex -space-x-2">
            {agents.map((m) => <Avatar key={m.id} member={m} size="sm" ring />)}
          </div>
          <p className="mt-2 text-xs text-white/75">{agents.length} agents travaillent déjà ici.</p>
        </div>
      </section>
      <section className="flex flex-1 items-center justify-center px-4 py-10">
        <div className="w-full max-w-sm">
          <h2 className="text-2xl font-semibold">Bonjour 👋</h2>
          <p className="mt-1 text-sm text-ink-soft">Qui êtes-vous ?</p>
          <div className="mt-6 space-y-2.5">
            {humans.map((m) => (
              <button key={m.id} onClick={() => login(m.id)}
                className="group flex w-full items-center gap-3 rounded-2xl border border-line bg-white px-4 py-3 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-accent hover:shadow-md">
                <Avatar member={m} />
                <span className="min-w-0 flex-1">
                  <span className="block font-medium">{m.name}</span>
                  <span className="block truncate text-xs text-ink-soft">{m.title}</span>
                </span>
                <ChevronRight size={18} className="text-ink-muted transition group-hover:text-accent" />
              </button>
            ))}
          </div>
          <p className="mt-8 text-xs text-ink-muted">Version locale. En ligne, on se connectera avec son compte Google.</p>
        </div>
      </section>
    </div>
  );
}
