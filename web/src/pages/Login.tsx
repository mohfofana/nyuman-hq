import { useEffect, useState } from "react";
import { ChevronRight, TriangleAlert } from "lucide-react";
import { api } from "../lib/api";
import { useSession } from "../lib/session";

export function Login() {
  const { login } = useSession();
  const [humans, setHumans] = useState<{ id: string; name: string; title: string }[]>([]);
  const [mode, setMode] = useState<{ google: boolean; dev_login: boolean; email: boolean } | null>(null);
  useEffect(() => {
    api.loginStatus().then(async (m) => {
      setMode(m);
      if (m.dev_login) setHumans(await api.profiles().catch(() => []));
    }).catch(() => setMode({ google: false, dev_login: true, email: false }));
  }, []);
  const erreur = new URLSearchParams(window.location.search).get("erreur");

  return (
    <div className="flex min-h-full flex-col bg-surface lg:flex-row">
      <section className="relative flex flex-col justify-between overflow-hidden bg-gradient-to-br from-[#CF6A12] via-accent-bright to-[#EC9A45] px-8 py-10 text-white lg:w-[46%] lg:px-14 lg:py-14">
        <span className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-white/10" />
        <span className="pointer-events-none absolute -bottom-32 -left-16 h-80 w-80 rounded-full bg-sun/25" />
        <img src="/logo-wordmark.png" alt="Nyuman" className="logo-white relative h-6 w-fit" />
        <div className="relative mt-10 lg:mt-0">
          <h1 className="text-3xl font-semibold leading-tight lg:text-5xl">Le QG de<br />l'équipe Nyuman.</h1>
          <p className="mt-4 max-w-sm text-white/85">Discussions, réunions, projets et fichiers, avec toute l'équipe, humains et agents.</p>
          <p className="mt-8 text-xs text-white/75">Humains et agents, au même endroit.</p>
        </div>
      </section>
      <section className="flex flex-1 items-center justify-center px-4 py-10">
        <div className="w-full max-w-sm">
          <h2 className="text-2xl font-semibold">Bonjour 👋</h2>
          <p className="mt-1 text-sm text-ink-soft">
            {mode?.dev_login ? "Qui êtes-vous ?"
              : mode?.email ? "Entrez votre adresse : on vous envoie un lien, sans mot de passe."
              : mode?.google ? "Connectez-vous avec votre compte Google." : "Chargement…"}
          </p>
          {erreur && (
            <p className="mt-4 flex items-start gap-2 rounded-2xl bg-[#FDE6E2] px-3 py-2.5 text-sm text-[#B5321F]">
              <TriangleAlert size={16} className="mt-0.5 shrink-0" /> {erreur}
            </p>
          )}
          {mode?.email && !mode.dev_login && <EmailForm />}
          {mode?.email && mode.google && !mode.dev_login && (
            <div className="my-4 flex items-center gap-3 text-xs text-ink-muted">
              <span className="h-px flex-1 bg-line" /> ou <span className="h-px flex-1 bg-line" />
            </div>
          )}
          {mode?.google && !mode.dev_login && (
            <a href="/api/auth/google/start"
              className="flex w-full items-center justify-center gap-3 rounded-2xl border border-line bg-white px-4 py-3.5 font-medium shadow-sm transition hover:-translate-y-0.5 hover:border-accent hover:shadow-md">
              <GoogleMark /> Continuer avec Google
            </a>
          )}
          {mode?.google && mode.dev_login && <p className="mt-5 text-xs font-medium uppercase tracking-wide text-ink-muted">Ou, en local</p>}
          {mode && !mode.dev_login && !mode.google && !mode.email && (
            <p className="mt-6 rounded-2xl bg-surface p-4 text-sm text-ink-soft">
              La connexion Google n'est pas encore branchée sur ce serveur. Revenez dans un moment.
            </p>
          )}
          <div className={`space-y-2.5 ${mode?.google ? "mt-3" : "mt-6"}`}>
            {humans.map((m) => (
              <button key={m.id} onClick={() => login(m.id)}
                className="group flex w-full items-center gap-3 rounded-2xl border border-line bg-white px-4 py-3 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-accent hover:shadow-md">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent-soft text-sm font-semibold text-accent">
                  {m.name.split(" ").map((w) => w[0]).slice(0, 2).join("")}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block font-medium">{m.name}</span>
                  <span className="block truncate text-xs text-ink-soft">{m.title}</span>
                </span>
                <ChevronRight size={18} className="text-ink-muted transition group-hover:text-accent" />
              </button>
            ))}
          </div>
          <p className="mt-8 text-xs text-ink-muted">
            {mode?.dev_login
              ? "Cliquez sur votre nom pour entrer."
              : "Adresse @nyuman.app ou adresse perso : les deux marchent."}
          </p>
        </div>
      </section>
    </div>
  );
}

/** On tape son adresse, on reçoit un lien : pas de mot de passe à retenir. */
function EmailForm() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(0);
  const [busy, setBusy] = useState(false);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    setBusy(true);
    try { setSent((await api.requestLink(email.trim())).minutes); }
    catch { setSent(-1); }
    finally { setBusy(false); }
  };
  if (sent > 0) {
    return (
      <div className="mt-6 rounded-2xl bg-[#E3F6EA] p-4 text-sm text-[#18794A]">
        <p className="font-medium">Regardez votre boîte mail.</p>
        <p className="mt-1">Si <b>{email.trim()}</b> fait partie de l'équipe, un lien vient d'y être envoyé. Il est valable {sent} minutes.</p>
        <button onClick={() => setSent(0)} className="mt-2 text-xs font-medium underline">Changer d'adresse</button>
      </div>
    );
  }
  return (
    <form onSubmit={submit} className="mt-6 space-y-2">
      <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
        placeholder="prenom@nyuman.app" autoComplete="email"
        className="w-full rounded-2xl border border-line bg-white px-4 py-3 text-[15px] outline-none focus:border-accent" />
      <button disabled={busy}
        className="w-full rounded-2xl bg-accent py-3 text-[15px] font-semibold text-white shadow-sm shadow-accent/30 hover:bg-accent-hover disabled:opacity-50">
        {busy ? "Envoi…" : "Recevoir mon lien"}
      </button>
      {sent === -1 && <p className="text-sm text-busy">L'envoi n'a pas marché. Réessayez dans un moment.</p>}
    </form>
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
