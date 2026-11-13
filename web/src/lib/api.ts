export type Member = {
  id: string;
  name: string;
  kind: "human" | "agent";
  title: string;
  role: string;
  is_head: boolean;
  avatar_tone: string;
  now_doing: string;
  schedule: string;
  manual_status: "busy" | "dnd" | null;
  status_message: string;
};

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw Object.assign(new Error(res.statusText), { status: res.status });
  return res.status === 204 ? (undefined as T) : res.json();
}

export const api = {
  me: () => req<Member>("/api/auth/me"),
  members: () => req<Member[]>("/api/members"),
  devLogin: (member_id: string) =>
    req<Member>("/api/auth/dev-login", { method: "POST", body: JSON.stringify({ member_id }) }),
  logout: () => req<void>("/api/auth/logout", { method: "POST" }),
  updateMe: (data: Partial<Member>) =>
    req<Member>("/api/members/me", { method: "PATCH", body: JSON.stringify(data) }),
};
