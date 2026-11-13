import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, type Member } from "./api";

type Ctx = {
  me: Member | null;
  members: Member[];
  loading: boolean;
  login: (id: string) => Promise<void>;
  logout: () => Promise<void>;
  updateMe: (d: Partial<Member>) => Promise<void>;
};

const SessionCtx = createContext<Ctx>(null!);
export const useSession = () => useContext(SessionCtx);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Member | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setMembers(await api.members());
  }, []);

  useEffect(() => {
    Promise.all([api.me().then(setMe).catch(() => setMe(null)), refresh()]).finally(() => setLoading(false));
  }, [refresh]);

  const value: Ctx = {
    me, members, loading,
    login: async (id) => { setMe(await api.devLogin(id)); },
    logout: async () => { await api.logout(); setMe(null); },
    updateMe: async (d) => { setMe(await api.updateMe(d)); await refresh(); },
  };
  return <SessionCtx.Provider value={value}>{children}</SessionCtx.Provider>;
}
