import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api, type LiveMessage, type Member, type Presence, type PresenceInput } from "./api";

// La maison en direct : qui est où, ce qu'il fait, et ce qui vient de se passer.
// Un seul flux (Server-Sent Events) par onglet ; le navigateur se reconnecte tout seul en cas de coupure.

export interface Toast {
  id: number;
  actorId: number;
  text: string;
  link: string | null;
}

interface LiveState {
  me: Member;
  connected: boolean;
  presences: Record<number, Presence>;
  toasts: Toast[];
  dismiss: (id: number) => void;
  report: (input: PresenceInput) => void;
}

const LiveContext = createContext<LiveState | null>(null);

const TOAST_MS = 6500;

export function LiveProvider({ me, children }: { me: Member; children: ReactNode }) {
  const queryClient = useQueryClient();
  const [connected, setConnected] = useState(false);
  const [presences, setPresences] = useState<Record<number, Presence>>({});
  const [toasts, setToasts] = useState<Toast[]>([]);
  const lastReport = useRef<PresenceInput | null>(null);

  const dismiss = useCallback((id: number) => setToasts((t) => t.filter((x) => x.id !== id)), []);

  const report = useCallback((input: PresenceInput) => {
    const same = JSON.stringify(input) === JSON.stringify(lastReport.current);
    lastReport.current = input;
    if (!same) api.reportPresence(input).catch(() => undefined);
  }, []);

  useEffect(() => {
    const source = new EventSource("/api/flux", { withCredentials: true });
    source.onopen = () => {
      setConnected(true);
      // Après une reconnexion, le serveur ne sait plus où l'on est : on le lui redit.
      if (lastReport.current) api.reportPresence(lastReport.current).catch(() => undefined);
    };
    source.onerror = () => setConnected(false);
    source.onmessage = (e) => {
      const message = JSON.parse(e.data) as LiveMessage;
      if (message.type === "bonjour") {
        const next: Record<number, Presence> = {};
        for (const [id, p] of Object.entries(message.presences)) next[Number(id)] = p;
        setPresences(next);
      } else if (message.type === "presence") {
        setPresences((prev) => {
          const next = { ...prev };
          if (message.presence) next[message.membre_id] = message.presence;
          else delete next[message.membre_id];
          return next;
        });
      } else if (message.type === "changement") {
        // Un tableau a bougé (tâche déplacée, retour classé…) : on relit seulement ce qui a changé.
        for (const sujet of message.sujets) {
          queryClient.invalidateQueries({ queryKey: [sujet] });
          if (sujet === "retours") queryClient.invalidateQueries({ queryKey: ["retours-etat"] });
        }
      } else if (message.type === "evenement") {
        for (const key of ["evenements", "documents", "document", "versions", "objectif", "objectifs-poles", "membres", "taches", "retours", "retours-etat", "rapports", "decisions", "pros"]) {
          queryClient.invalidateQueries({ queryKey: [key] });
        }
        if (message.actor_id !== me.id) {
          setToasts((t) => [...t.slice(-3), { id: message.id, actorId: message.actor_id, text: message.text, link: message.link }]);
          window.setTimeout(() => dismiss(message.id), TOAST_MS);
        }
      }
    };
    return () => source.close();
  }, [queryClient, me.id, dismiss]);

  const value = useMemo(
    () => ({ me, connected, presences, toasts, dismiss, report }),
    [me, connected, presences, toasts, dismiss, report],
  );
  return <LiveContext.Provider value={value}>{children}</LiveContext.Provider>;
}

export function useLive(): LiveState {
  const ctx = useContext(LiveContext);
  if (!ctx) throw new Error("useLive doit être utilisé dans LiveProvider");
  return ctx;
}

/** Chaque page dit où l'on est et ce qu'on y fait ; les autres le voient sur le plan de la maison. */
export function usePresence(input: PresenceInput | null) {
  const { report } = useLive();
  const key = JSON.stringify(input);
  useEffect(() => {
    if (input) report(input);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, report]);
}
