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
  work_days: string;
  ask_hour: number | null;
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

export type TaskStatus = "todo" | "doing" | "review" | "done";
export type Project = {
  id: string; name: string; icon: string; description: string; department: string; owner_id: string | null;
  created_by: string; archived: boolean; created_at: string; counts: Partial<Record<TaskStatus, number>>;
  hours_budget: number | null;
};
export type PageMeta = {
  id: string; project_id: string; parent_id: string | null; title: string; icon: string; position: number;
  archived: boolean; created_by: string; updated_by: string | null; created_at: string; updated_at: string;
};
export type PageFull = PageMeta & { content: string; text: string };
export type Task = {
  id: string; project_id: string; title: string; description: string; status: TaskStatus; priority: "low" | "normal" | "high";
  assignee_id: string | null; due_date: string | null; page_id: string | null; position: number; archived: boolean;
  created_by: string; updated_by: string | null; created_at: string; updated_at: string; completed_at: string | null;
};

export const projectsApi = {
  list: () => req<Project[]>("/api/projects"),
  create: (d: Partial<Project>) => req<Project>("/api/projects", { method: "POST", body: JSON.stringify(d) }),
  update: (id: string, d: Partial<Project>) => req<Project>(`/api/projects/${id}`, { method: "PATCH", body: JSON.stringify(d) }),
  pages: (id: string) => req<PageMeta[]>(`/api/projects/${id}/pages`),
  createPage: (id: string, d: { title?: string; parent_id?: string | null; icon?: string }) =>
    req<PageFull>(`/api/projects/${id}/pages`, { method: "POST", body: JSON.stringify(d) }),
  page: (id: string) => req<PageFull>(`/api/pages/${id}`),
  updatePage: (id: string, d: Partial<PageFull>) => req<PageFull>(`/api/pages/${id}`, { method: "PATCH", body: JSON.stringify(d) }),
  tasks: (params: Record<string, string>) => req<Task[]>(`/api/tasks?${new URLSearchParams(params)}`),
  createTask: (d: Partial<Task> & { project_id: string; title: string }) =>
    req<Task>("/api/tasks", { method: "POST", body: JSON.stringify(d) }),
  updateTask: (id: string, d: Partial<Task>) => req<Task>(`/api/tasks/${id}`, { method: "PATCH", body: JSON.stringify(d) }),
};

export type AgentRunSummary = {
  enabled: boolean;
  agents: Record<string, { today: number; cap: number; month_cost_usd: number; last_status: string | null; last_at: string | null; last_error: string }>;
};
export const agentsApi = { runs: () => req<AgentRunSummary>("/api/auth/agents/runs") };

// ---------- suivi du temps (déclaré, jamais mesuré) ----------
export type TimeEntry = {
  id: string; member_id: string; day: string; project_id: string; project_name: string; project_icon: string;
  task_id: string | null; task_title: string | null; minutes: number; note: string;
};
export type MyTime = { start: string; end: string; entries: TimeEntry[]; days_off: string[]; work_days: string; ask_hour: number | null };
export type TimeSuggestions = {
  day: string;
  tasks: { id: string; title: string; status: TaskStatus; project_id: string; project_name: string }[];
  projects: { id: string; name: string; icon: string }[];
};
export type TeamTime = {
  start: string; end: string; days: number;
  projects: { id: string; name: string; icon: string; owner_id: string | null; minutes: number; total_minutes: number;
    hours_budget: number | null; budget_pct: number | null; last_day: string | null; inactive: boolean }[];
  people: { member_id: string; minutes: number; projects: Record<string, number> }[] | null;
};
export const timeApi = {
  me: (start?: string, end?: string) => req<MyTime>(`/api/time/me?${new URLSearchParams({ ...(start ? { start } : {}), ...(end ? { end } : {}) })}`),
  suggestions: (day: string) => req<TimeSuggestions>(`/api/time/suggestions?day=${day}`),
  add: (d: { day: string; project_id?: string; task_id?: string; minutes: number; note?: string }) =>
    req<TimeEntry>("/api/time", { method: "POST", body: JSON.stringify(d) }),
  remove: (id: string) => req<void>(`/api/time/${id}`, { method: "DELETE" }),
  off: (day: string) => req<void>("/api/time/off", { method: "POST", body: JSON.stringify({ day }) }),
  undoOff: (day: string) => req<void>(`/api/time/off/${day}`, { method: "DELETE" }),
  team: (days: number) => req<TeamTime>(`/api/time/team?days=${days}`),
};

export function fmtMinutes(min: number): string {
  if (!min) return "0 h";
  const h = Math.floor(min / 60), m = min % 60;
  if (!h) return `${m} min`;
  return m ? `${h} h ${String(m).padStart(2, "0")}` : `${h} h`;
}

/** Jour local au format AAAA-MM-JJ (Abidjan = UTC). */
export const isoDay = (d = new Date()) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
