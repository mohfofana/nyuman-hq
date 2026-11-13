import { Navigate, Route, Routes } from "react-router-dom";
import { FolderOpen, LayoutList } from "lucide-react";
import { useSession } from "./lib/session";
import { Shell } from "./components/Shell";
import { Login } from "./pages/Login";
import { Home } from "./pages/Home";
import { Team } from "./pages/Team";
import { Preview } from "./pages/Preview";
import { Discussions } from "./pages/discussions/Discussions";
import { Activity } from "./pages/Activity";
import { SearchPage } from "./pages/SearchPage";
import { Agenda } from "./pages/agenda/Agenda";

export default function App() {
  const { me, loading } = useSession();
  if (loading) return null;
  if (!me) return <Login />;
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route path="/accueil" element={<Home />} />
        <Route path="/discussions" element={<Discussions />} />
        <Route path="/discussions/:channelId" element={<Discussions />} />
        <Route path="/activite" element={<Activity />} />
        <Route path="/recherche" element={<SearchPage />} />
        <Route path="/agenda" element={<Agenda />} />
        <Route path="/projets" element={<Preview kind="board" icon={LayoutList} title="Projets" soon="Bientôt" tone="sun"
          text="Le suivi de projet, comme dans Notion."
          bullets={["Pages riches et documents", "Vues tableau, colonnes et calendrier", "Tâches avec responsable et échéance"]} />} />
        <Route path="/fichiers" element={<Preview kind="files" icon={FolderOpen} title="Fichiers" soon="Bientôt" tone="blue"
          text="Tous les fichiers partagés, rangés par canal et par projet."
          bullets={["Aperçu des images et PDF", "Anciennes versions gardées", "Qui a modifié quoi"]} />} />
        <Route path="/equipe" element={<Team />} />
        <Route path="*" element={<Navigate to="/accueil" replace />} />
      </Route>
    </Routes>
  );
}
