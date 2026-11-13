import { Navigate, useParams } from "react-router-dom";
import { CalendarClock, Store, Wallet } from "lucide-react";
import type { TrackKind } from "../lib/api";
import { TrackList } from "../components/TrackList";
import { Panel } from "../components/ui";

export const TRACK_META: Record<TrackKind, { title: string; text: string; icon: typeof Store; tone: string }> = {
  salon: { title: "Salons à suivre", text: "Chaque salon, du premier contact jusqu'à sa première réservation.", icon: Store, tone: "bg-accent-soft text-accent" },
  echeance: { title: "Échéances et contrats", text: "Contrats, préavis, déclarations : tout ce qui a une date limite.", icon: CalendarClock, tone: "bg-blue-soft text-blue" },
  depense: { title: "Dépenses à valider", text: "Chacun demande, un responsable valide ou refuse. Rien n'est payé depuis HQ.", icon: Wallet, tone: "bg-sun-soft text-[#9A6B00]" },
};

export function TrackPage() {
  const { kind } = useParams();
  if (!kind || !(kind in TRACK_META)) return <Navigate to="/accueil" replace />;
  const meta = TRACK_META[kind as TrackKind];
  const Icon = meta.icon;
  return (
    <div className="mx-auto max-w-3xl px-4 py-6 sm:px-8">
      <h1 className="flex items-center gap-2.5 text-2xl font-semibold">
        <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${meta.tone}`}><Icon size={20} /></span>{meta.title}
      </h1>
      <p className="mb-5 mt-1 text-sm text-ink-soft">{meta.text}</p>
      <Panel><TrackList kind={kind as TrackKind} /></Panel>
    </div>
  );
}
