import { useEffect, useState } from "react";
import { ChevronRight, TriangleAlert } from "lucide-react";
import { api } from "../lib/api";
import { useSession } from "../lib/session";
import { Avatar } from "../components/Avatar";

export function Login() {
  const { members, login } = useSession();
  const [mode, setMode] = useState<{ google: boolean; dev_login: boolean } | null>(null);
  useEffect(() => { api.loginStatus().then(setMode).catch(() => setMode({ google: false, dev_login: true })); }, []);
  const erreur = new URLSearchParams(window.location.search).get("erreur");
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
          <p className="mt-1 text-sm text-ink-soft">{mode?.google ? "Connectez-vous avec votre compte Google." : "Qui êtes-vous ?"}</p>
          {erreur && (
            <p className="mt-4 flex items-start gap-2 rounded-2xl bg-[#FDE6E2] px-3 py-2.5 text-sm text-[#B5321F]">
              <TriangleAlert size={16} className="mt-0.5 shrink-0" /> {erreur}
            </p>
          )}
          {mode?.google && (
            <a href="/api/auth/google/start"
              className="mt-6 flex w-full items-center justify-center gap-3 rounded-2xl border border-line bg-white px-4 py-3.5 font-medium shadow-sm transition hover:-translate-y-0.5 hover:border-accent hover:shadow-md">
              <GoogleMark /> Continuer avec Google
            </a>
          )}
          {mode?.google && mode.dev_login && <p className="mt-5 text-xs font-medium uppercase tracking-wide text-ink-muted">Ou, en local</p>}
          <div className={`space-y-2.5 ${mode?.google ? "mt-3" : "mt-6"}`}>
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
          <p className="mt-8 text-xs text-ink-muted">
            {mode?.google ? "Seules les adresses de l'équipe peuvent entrer." : "Version locale. En ligne, on se connectera avec son compte Google."}
          </p>
        </div>
      </section>
    </div>
  );
}

/** Le logo Google, tel qu'ils demandent de l'afficher. */
function GoogleMark() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9 3.6l6.7-6.7C35.6 2.6 30.2.5 24 .5 14.6.5 6.5 5.9 2.6 13.8l7.8 6.1C12.3 13.9 17.7 9.5 24 9.5z" />
      <path fill="#4285F4" d="M46.6 24.6c0-1.7-.2-3.3-.5-4.9H24v9.3h12.7c-.6 3-2.3 5.5-4.8 7.2l7.5 5.8c4.4-4 6.9-10 6.9-17.4z" />
      <path fill="#FBBC05" d="M10.4 28.4a14.5 14.5 0 0 1 0-8.8l-7.8-6.1a23.5 23.5 0 0 0 0 21l7.8-6.1z" />
      <path fill="#34A853" d="M24 47.5c6.2 0 11.5-2 15.3-5.6l-7.5-5.8c-2.1 1.4-4.8 2.2-7.8 2.2-6.3 0-11.7-4.4-13.6-10.4l-7.8 6.1C6.5 42.1 14.6 47.5 24 47.5z" />
    </svg>
  );
}
