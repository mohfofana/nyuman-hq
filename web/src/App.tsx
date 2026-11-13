import { Navigate, Route, Routes } from "react-router-dom";
import { CalendarDays, FolderOpen, LayoutList, MessagesSquare } from "lucide-react";
import { useSession } from "./lib/session";
import { Shell } from "./components/Shell";
import { Login } from "./pages/Login";
import { Home } from "./pages/Home";
import { Team } from "./pages/Team";
import { Preview } from "./pages/Preview";

export default function App() {
  const { me, loading } = useSession();
  if (loading) return null;
  if (!me) return <Login />;
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route path="/accueil" element={<Home />} />
        <Route path="/discussions" element={<Preview kind="chat" icon={MessagesSquare} title="Discussions" soon="Prochaine étape"
          text="Toute l'équipe au même endroit, humains et agents."
          bullets={["Canaux par sujet et messages privés", "Fils, mentions @ et réactions", "Fichiers, images et recherche"]} />} />
        <Route path="/agenda" element={<Preview kind="calendar" icon={CalendarDays} title="Agenda" soon="Après la messagerie" tone="blue"
          text="Les réunions et échéances de toute l'équipe."
          bullets={["Lien Google Meet créé tout seul", "Rappel avant chaque réunion", "Synchronisé avec Google Agenda"]} />} />
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
