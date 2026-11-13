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
  manual_status: "busy" | "dnd" | "working" | "waiting" | "blocked" | null;
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

export type Channel = {
  id: string;
  kind: "channel" | "dm";
  name: string;
  topic: string;
  member_ids: string[];
  unread: number;
  mentions: number;
  last_message_at: string | null;
};

export type Attachment = { id: string; filename: string; content_type: string; size: number; url: string };

export type Message = {
  id: string;
  channel_id: string;
  author_id: string;
  parent_id: string | null;
  body: string;
  deleted: boolean;
  created_at: string;
  edited_at: string | null;
  reactions: { emoji: string; member_ids: string[] }[];
  attachments: Attachment[];
  reply_count: number;
  last_reply_at: string | null;
  reply_authors: string[];
};

export type ActivityItem = { kind: "mention" | "reply"; message: Message };

export type PresenceSnap = { member_id: string; connected: boolean; idle: boolean; in_meeting?: boolean; last_seen: string | null };

export const chat = {
  channels: () => req<Channel[]>("/api/channels"),
  createChannel: (name: string, topic: string) =>
    req<{ id: string }>("/api/channels", { method: "POST", body: JSON.stringify({ name, topic }) }),
  openDm: (member_ids: string[]) => req<{ id: string }>("/api/dms", { method: "POST", body: JSON.stringify({ member_ids }) }),
  read: (id: string) => req<void>(`/api/channels/${id}/read`, { method: "POST" }),
  messages: (id: string, before?: string) =>
    req<Message[]>(`/api/channels/${id}/messages${before ? `?before=${encodeURIComponent(before)}` : ""}`),
  thread: (id: string) => req<{ root: Message; replies: Message[] }>(`/api/messages/${id}/thread`),
  send: (channelId: string, body: string, parent_id?: string | null, attachment_ids: string[] = []) =>
    req<Message>(`/api/channels/${channelId}/messages`, {
      method: "POST", body: JSON.stringify({ body, parent_id: parent_id ?? null, attachment_ids }),
    }),
  edit: (id: string, body: string) => req<Message>(`/api/messages/${id}`, { method: "PATCH", body: JSON.stringify({ body }) }),
  remove: (id: string) => req<Message>(`/api/messages/${id}`, { method: "DELETE" }),
  react: (id: string, emoji: string) =>
    req<Message>(`/api/messages/${id}/reactions`, { method: "POST", body: JSON.stringify({ emoji }) }),
  search: (q: string) => req<Message[]>(`/api/search?q=${encodeURIComponent(q)}`),
  activity: () => req<ActivityItem[]>("/api/activity"),
  presence: () => req<PresenceSnap[]>("/api/presence"),
  upload: async (file: File): Promise<Attachment> => {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch("/api/uploads", { method: "POST", body: fd, credentials: "include" });
    if (!res.ok) throw Object.assign(new Error((await res.json().catch(() => ({}))).detail ?? res.statusText), { status: res.status });
    return res.json();
  },
};

export type Meeting = {
  id: string;
  title: string;
  description: string;
  start_at: string;
  end_at: string;
  organizer_id: string;
  link_kind: "jitsi" | "meet" | "none";
  link: string;
  channel_id: string | null;
  reminder_minutes: number;
  cancelled: boolean;
  notes: string;
  notes_by: string | null;
  notes_at: string | null;
  attendees: { member_id: string; response: "pending" | "yes" | "maybe" | "no"; joined: boolean }[];
};

export type MeetingInput = {
  title: string; description: string; start_at: string; end_at: string; attendee_ids: string[];
  link_kind: string; channel_id: string | null; reminder_minutes: number;
};

export const meetings = {
  config: () => req<{ google_meet: boolean; jitsi: boolean }>("/api/meetings/config"),
  range: (start: Date, end: Date) =>
    req<Meeting[]>(`/api/meetings?start=${encodeURIComponent(start.toISOString())}&end=${encodeURIComponent(end.toISOString())}`),
  upcoming: () => req<Meeting[]>("/api/meetings/upcoming"),
  get: (id: string) => req<Meeting>(`/api/meetings/${id}`),
  create: (d: MeetingInput) => req<Meeting>("/api/meetings", { method: "POST", body: JSON.stringify(d) }),
  update: (id: string, d: Partial<MeetingInput>) => req<Meeting>(`/api/meetings/${id}`, { method: "PATCH", body: JSON.stringify(d) }),
  cancel: (id: string) => req<Meeting>(`/api/meetings/${id}/cancel`, { method: "POST" }),
  respond: (id: string, response: string) =>
    req<Meeting>(`/api/meetings/${id}/respond`, { method: "POST", body: JSON.stringify({ response }) }),
  join: (id: string) => req<{ link: string }>(`/api/meetings/${id}/join`, { method: "POST" }),
  saveNotes: (id: string, notes: string) =>
    req<Meeting>(`/api/meetings/${id}/notes`, { method: "PUT", body: JSON.stringify({ notes }) }),
  publishNotes: (id: string) => req<{ channel_id: string }>(`/api/meetings/${id}/notes/publish`, { method: "POST" }),
};

export type Position = {
  id: number; title: string; department: string; reports_to: number | null;
  mission: string; hours: string; holder_ids: string[]; support_ids: string[];
};
export type Org = { departments: string[]; positions: Position[] };

export const orgApi = {
  get: () => req<Org>("/api/org"),
  set: (id: number, holder_ids: string[], support_ids: string[]) =>
    req<Org>(`/api/org/positions/${id}`, { method: "PUT", body: JSON.stringify({ holder_ids, support_ids }) }),
};
