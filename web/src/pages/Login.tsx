import { useEffect, useRef, useState, type FormEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, ApiError, type Member } from "../api";

// Bouton « Se connecter avec Google » (Google Identity Services).
declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (options: { client_id: string; callback: (r: { credential: string }) => void }) => void;
          renderButton: (el: HTMLElement, options: Record<string, string | number>) => void;
        };
      };
    };
  }
}

function loadGoogleScript(): Promise<void> {
  if (window.google?.accounts) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Impossible de charger la connexion Google."));
    document.head.appendChild(script);
  });
}

function GoogleButton({ clientId, onLogin, onError }: {
  clientId: string;
  onLogin: (m: Member) => void;
  onError: (msg: string) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    loadGoogleScript()
      .then(() => {
        if (cancelled || !ref.current || !window.google) return;
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: async ({ credential }) => {
            try {
              onLogin(await api.loginGoogle(credential));
            } catch (e) {
              onError(e instanceof ApiError ? e.message : "La connexion a échoué.");
            }
          },
        });
        window.google.accounts.id.renderButton(ref.current, {
          theme: "outline",
          size: "large",
          text: "signin_with",
          shape: "pill",
          locale: "fr",
          width: 320,
        });
      })
      .catch((e: Error) => onError(e.message));
    return () => {
      cancelled = true;
    };
  }, [clientId, onLogin, onError]);

  return <div ref={ref} style={{ minHeight: 44 }} />;
}

/** Connexion par lien envoyé par email : les boîtes @nyuman.app sont chez Netim, pas chez Google. */
function LienForm({ showDevHint }: { showDevHint: boolean }) {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "sent">("idle");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setState("sending");
    try {
      await api.demanderLien(email.trim());
      setState("sent");
    } catch (err) {
      setState("idle");
      setError(err instanceof ApiError ? err.message : "L’envoi a échoué. Réessaie.");
    }
  }

  if (state === "sent") {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <p className="notice good" role="status">
          Si <strong>{email.trim()}</strong> fait partie de la maison, un lien vient de partir. Il marche une seule fois,
          pendant 15 minutes. Pense à regarder dans les spams.
          {showDevHint && <> Sur ce PC, le lien s’affiche dans le journal du serveur.</>}
        </p>
        <button type="button" className="btn" onClick={() => setState("idle")}>Changer d’adresse ou renvoyer</button>
      </div>
    );
  }

  return (
    <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div className="field">
        <label htmlFor="lien-email">Ton adresse Nyuman</label>
        <input
          id="lien-email"
          className="input"
          type="email"
          required
          autoComplete="email"
          placeholder="prenom.nom@nyuman.app"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>
      <button type="submit" className="btn brand" disabled={state === "sending"}>
        {state === "sending" ? "Envoi…" : "Recevoir un lien de connexion"}
      </button>
      {error && <p className="notice bad" role="alert">{error}</p>}
    </form>
  );
}

/** Un petit plan de la maison, dessiné : la promesse de ce qu'on trouve derrière la porte. */
function MiniHouse() {
  return (
    <svg viewBox="0 0 320 190" width="100%" style={{ maxWidth: 420 }} fill="none" aria-hidden="true">
      <g stroke="#cdbfaf" strokeWidth="2.5">
        <rect x="4" y="4" width="312" height="182" rx="6" />
        <path d="M112 4v120M226 4v182M4 124h222M226 92h90" />
      </g>
      <g fontFamily="IBM Plex Mono, monospace" fontSize="8.5" letterSpacing="1" fill="#cdbfaf">
        <text x="12" y="22">BIBLIOTHÈQUE</text>
        <text x="124" y="22">SALON</text>
        <text x="238" y="22">CONSEIL</text>
        <text x="238" y="110">PROJET</text>
        <text x="14" y="142">BUREAUX</text>
      </g>
      <circle cx="150" cy="70" r="13" fill="#f7e2cb" />
      <circle cx="182" cy="78" r="13" fill="#e1f0e7" />
      <rect x="38" y="152" width="26" height="26" rx="8" fill="#e5e8f7" />
      <rect x="76" y="152" width="26" height="26" rx="8" fill="#e5e8f7" />
      <rect x="114" y="152" width="26" height="26" rx="8" fill="#e5e8f7" />
      <circle cx="262" cy="56" r="13" fill="#faefd3" />
      <circle cx="150" cy="70" r="17" stroke="#bc600d" strokeWidth="2.5" />
    </svg>
  );
}

export function Login({ onLogin }: { onLogin: (m: Member) => void }) {
  const config = useQuery({ queryKey: ["auth-config"], queryFn: api.authConfig });
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState("");

  async function devLogin(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      onLogin(await api.loginDev(email.trim()));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "La connexion a échoué.");
    }
  }

  return (
    <div className="login">
      <aside className="login-side">
        <div className="brand" style={{ padding: 0 }}>
          <span className="brand-name">nyuman</span>
          <span className="brand-tag">HQ</span>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>
          <MiniHouse />
          <h1 className="display" style={{ maxWidth: "14ch" }}>La maison où toute l’équipe travaille.</h1>
          <p style={{ color: "var(--cream-2)", fontSize: 17, maxWidth: "44ch" }}>
            Humains et agents, au même niveau, vers un seul objectif. Chacun voit les autres travailler, en direct.
          </p>
        </div>
        <span className="eyebrow" style={{ color: "var(--cream-2)" }}>Abidjan · coiffure, tresses, barbiers, ongles</span>
      </aside>

      <main className="login-main">
        <section style={{ width: "100%", maxWidth: 380, display: "flex", flexDirection: "column", gap: 22 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <h2 style={{ fontSize: 30, fontWeight: 800 }}>Entrer</h2>
            <p className="soft">
              {config.data?.email_login
                ? "Tape ton adresse @nyuman.app : on t’envoie un lien pour entrer, sans mot de passe."
                : "Avec ton compte de l’équipe Nyuman."}
            </p>
          </div>

          {config.data?.email_login && <LienForm showDevHint={config.data.dev_login} />}

          {config.data?.google_client_id && (
            <>
              {config.data.email_login && <div className="login-or">ou</div>}
              <GoogleButton clientId={config.data.google_client_id} onLogin={onLogin} onError={setError} />
            </>
          )}

          {config.data && !config.data.email_login && !config.data.google_client_id && (
            <p className="notice">
              La connexion n’est pas encore réglée sur le serveur : il faut la boîte mail d’envoi (SMTP) ou l’identifiant Google de Nyuman.
            </p>
          )}

          {config.data?.dev_login && (
            <form onSubmit={devLogin} style={{ display: "flex", flexDirection: "column", gap: 12, paddingTop: 20, borderTop: "1px solid var(--line)" }}>
              <div className="field">
                <label htmlFor="dev-email">Connexion de développement <span className="soft" style={{ fontWeight: 400 }}>· sur ce PC seulement</span></label>
                <input id="dev-email" className="input" type="email" required placeholder="ton adresse dans l’équipe" value={email} onChange={(e) => setEmail(e.target.value)} />
              </div>
              <button type="submit" className="btn primary">Entrer dans la maison</button>
            </form>
          )}

          {error && <p className="notice bad" role="alert">{error}</p>}
        </section>
      </main>
    </div>
  );
}
