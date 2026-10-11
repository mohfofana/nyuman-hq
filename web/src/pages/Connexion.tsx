import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError, type Member } from "../api";

// En développement, React lance les effets deux fois : le lien ne doit être validé qu'une fois.
const validations = new Map<string, Promise<Member>>();

/** Page ouverte par le lien reçu par email (/connexion#jeton=…). */
export function Connexion({ onLogin }: { onLogin: (m: Member) => void }) {
  const navigate = useNavigate();
  const [jeton] = useState(() => new URLSearchParams(window.location.hash.slice(1)).get("jeton"));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Le jeton quitte tout de suite la barre d'adresse et l'historique du navigateur.
    if (window.location.hash) window.history.replaceState(null, "", "/connexion");
    if (!jeton) {
      navigate("/", { replace: true });
      return;
    }
    let validation = validations.get(jeton);
    if (!validation) {
      validation = api.validerLien(jeton);
      validations.set(jeton, validation);
    }
    let active = true;
    validation
      .then((m) => {
        if (!active) return;
        onLogin(m);
        navigate("/", { replace: true });
      })
      .catch((e) => {
        if (active) setError(e instanceof ApiError ? e.message : "La connexion a échoué.");
      });
    return () => {
      active = false;
    };
  }, [jeton, navigate, onLogin]);

  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "var(--night)", color: "var(--cream)", padding: 24 }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 22, maxWidth: 380, textAlign: "center" }}>
        <div className="brand" style={{ padding: 0 }}>
          <span className="brand-name">nyuman</span>
          <span className="brand-tag">HQ</span>
        </div>
        {error ? (
          <>
            <p className="notice bad" role="alert">{error}</p>
            <button type="button" className="btn on-night" onClick={() => navigate("/", { replace: true })}>
              Recevoir un nouveau lien
            </button>
          </>
        ) : (
          <p role="status" style={{ color: "var(--cream-2)" }}>On ouvre la porte…</p>
        )}
      </div>
    </div>
  );
}
