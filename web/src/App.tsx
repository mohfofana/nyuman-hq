import { Navigate, Route, Routes } from "react-router-dom";
import { Bell, CalendarDays, FolderOpen, LayoutList, MessagesSquare } from "lucide-react";
import { useSession } from "./lib/session";
import { Shell } from "./components/Shell";
import { Login } from "./pages/Login";
import { Team } from "./pages/Team";
import { Placeholder } from "./pages/Placeholder";

export default function App() {
  const { me, loading } = useSession();
  if (loading) return null;
  if (!me) return <Login />;
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route path="/activite" element={<Placeholder icon={Bell} title="Rien de nouveau" text="Les mentions, réponses et réactions qui vous concernent apparaîtront ici." />} />
        <Route path="/discussions" element={<Placeholder icon={MessagesSquare} title="Discussions" text="Canaux et messages privés : c'est la prochaine étape." />} />
        <Route path="/agenda" element={<Placeholder icon={CalendarDays} title="Agenda" text="Réunions avec lien Meet, échéances et rappels : arrive après la messagerie." />} />
        <Route path="/projets" element={<Placeholder icon={LayoutList} title="Projets" text="Pages, tâches et tableaux façon Notion : arrive ensuite." />} />
        <Route path="/fichiers" element={<Placeholder icon={FolderOpen} title="Fichiers" text="Les fichiers partagés dans les canaux et les projets seront rangés ici." />} />
        <Route path="/equipe" element={<Team />} />
        <Route path="*" element={<Navigate to="/discussions" replace />} />
      </Route>
    </Routes>
  );
}
