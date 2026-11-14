import { Navigate, Route, Routes } from "react-router-dom";
import { FolderOpen } from "lucide-react";
import { useSession } from "./lib/session";
import { Shell } from "./components/Shell";
import { Login } from "./pages/Login";
import { Join } from "./pages/Join";
import { Home } from "./pages/Home";
import { Team } from "./pages/Team";
import { Preview } from "./pages/Preview";
import { Discussions } from "./pages/discussions/Discussions";
import { Activity } from "./pages/Activity";
import { SearchPage } from "./pages/SearchPage";
import { Agenda } from "./pages/agenda/Agenda";
import { Projects } from "./pages/projects/Projects";
import { TimePage } from "./pages/Time";
import { Council } from "./pages/Council";
import { TrackPage } from "./pages/TrackPage";

export default function App() {
  const { me, loading } = useSession();
  if (loading) return null;
  if (!me) {
    // Arrivé par Google avec une adresse inconnue : il se présente avant d'entrer.
    return window.location.pathname === "/rejoindre" ? <Join /> : <Login />;
  }
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route path="/accueil" element={<Home />} />
        <Route path="/discussions" element={<Discussions />} />
        <Route path="/discussions/:channelId" element={<Discussions />} />
        <Route path="/activite" element={<Activity />} />
        <Route path="/recherche" element={<SearchPage />} />
        <Route path="/agenda" element={<Agenda />} />
        <Route path="/projets" element={<Projects />} />
        <Route path="/projets/:projectId" element={<Projects />} />
        <Route path="/projets/:projectId/page/:pageId" element={<Projects />} />
        <Route path="/conseil" element={<Council />} />
        <Route path="/suivi/:kind" element={<TrackPage />} />
        <Route path="/temps" element={<TimePage />} />
        <Route path="/fichiers" element={<Preview kind="files" icon={FolderOpen} title="Fichiers" soon="Bientôt" tone="blue"
          text="Tous les fichiers partagés, rangés par canal et par projet."
          bullets={["Aperçu des images et PDF", "Anciennes versions gardées", "Qui a modifié quoi"]} />} />
        <Route path="/equipe" element={<Team />} />
        <Route path="*" element={<Navigate to="/accueil" replace />} />
      </Route>
    </Routes>
  );
}
