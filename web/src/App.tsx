import { useCallback } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, type Member } from "./api";
import { LiveProvider } from "./live";
import { Layout } from "./components/Layout";
import { Login } from "./pages/Login";
import { Connexion } from "./pages/Connexion";
import { Salon } from "./pages/Salon";
import { Bibliotheque } from "./pages/Bibliotheque";
import { DocumentPage, NewDocument } from "./pages/Document";
import { Bureau, Bureaux } from "./pages/Bureaux";
import { Reglages } from "./pages/Reglages";
import { Projet } from "./pages/Projet";
import { Conseil } from "./pages/Conseil";
import { Pros } from "./pages/Pros";

export function App() {
  const queryClient = useQueryClient();
  // Arrivée par le lien reçu par email : on valide le lien avant de demander « qui est connecté ? ».
  const surLien = useLocation().pathname === "/connexion";
  const me = useQuery({
    enabled: !surLien,
    queryKey: ["me"],
    queryFn: async () => {
      try {
        return await api.me();
      } catch (e) {
        if (e instanceof ApiError && e.status === 401) return null;
        throw e;
      }
    },
  });
  const onLogin = useCallback((m: Member) => queryClient.setQueryData(["me"], m), [queryClient]);

  if (surLien) return <Connexion onLogin={onLogin} />;
  if (me.isLoading) {
    return (
      <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "var(--night)", color: "var(--cream)" }} role="status">
        <div className="brand" style={{ padding: 0 }}>
          <span className="brand-name">nyuman</span>
          <span className="brand-tag">HQ</span>
          <span className="visually-hidden">On ouvre la porte…</span>
        </div>
      </div>
    );
  }
  if (me.error) {
    return (
      <div style={{ padding: 32 }}>
        <p className="notice bad">Le serveur de HQ ne répond pas. Réessaie dans un instant.</p>
      </div>
    );
  }
  if (!me.data) return <Login onLogin={onLogin} />;

  const user = me.data;
  return (
    <LiveProvider me={user}>
      <Routes>
        <Route element={<Layout me={user} />}>
          <Route index element={<Salon me={user} />} />
          <Route path="bureaux" element={<Bureaux />} />
          <Route path="bureaux/:id" element={<Bureau />} />
          <Route path="projet" element={<Projet />} />
          <Route path="conseil" element={<Conseil />} />
          <Route path="pros" element={<Pros />} />
          <Route path="bibliotheque" element={<Bibliotheque />} />
          <Route path="bibliotheque/nouveau" element={<NewDocument />} />
          <Route path="bibliotheque/:id" element={<DocumentPage />} />
          <Route path="reglages" element={<Reglages me={user} />} />
          <Route path="*" element={<div className="page"><p className="soft">Cette pièce n’existe pas.</p></div>} />
        </Route>
      </Routes>
    </LiveProvider>
  );
}
