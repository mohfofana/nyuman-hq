import { useSession } from "../lib/session";
import { Avatar } from "../components/Avatar";

export function Login() {
  const { members, login } = useSession();
  const humans = members.filter((m) => m.kind === "human");
  return (
    <div className="flex min-h-full items-center justify-center bg-surface px-4">
      <div className="w-full max-w-sm rounded-3xl border border-line bg-white p-8 shadow-sm">
        <img src="/logo-mark.png" alt="" className="h-10" />
        <h1 className="mt-5 text-2xl font-semibold">Bienvenue au QG</h1>
        <p className="mt-1 text-sm text-ink-soft">Qui êtes-vous ?</p>
        <div className="mt-6 space-y-2">
          {humans.map((m) => (
            <button key={m.id} onClick={() => login(m.id)}
              className="flex w-full items-center gap-3 rounded-2xl border border-line px-3 py-2.5 text-left transition hover:border-accent hover:bg-accent-soft">
              <Avatar member={m} size="sm" />
              <span>
                <span className="block text-sm font-medium">{m.name}</span>
                <span className="block text-xs text-ink-soft">{m.title}</span>
              </span>
            </button>
          ))}
        </div>
        <p className="mt-6 text-xs text-ink-muted">Version locale : en ligne, on se connectera avec son compte Google.</p>
      </div>
    </div>
  );
}
