import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Hash, Search } from "lucide-react";
import { chat, type Message, type PageMeta, type Task } from "../lib/api";
import { useSession } from "../lib/session";
import { useLive } from "../lib/live";
import { Avatar } from "../components/Avatar";
import { presenceOf } from "../lib/presence";
import { channelTitle, dayLabel, decodeMentions, time } from "./discussions/format";

function Highlight({ text, q }: { text: string; q: string }) {
  const i = text.toLowerCase().indexOf(q.toLowerCase());
  if (i < 0 || !q) return <>{text}</>;
  return <>{text.slice(0, i)}<mark className="rounded bg-sun-soft px-0.5 text-ink">{text.slice(i, i + q.length)}</mark>{text.slice(i + q.length)}</>;
}

export function SearchPage() {
  const [params] = useSearchParams();
  const q = params.get("q") ?? "";
  const { me, members } = useSession();
  const { channels } = useLive();
  const [results, setResults] = useState<Message[] | null>(null);
  const [work, setWork] = useState<{ pages: PageMeta[]; tasks: Task[] }>({ pages: [], tasks: [] });
  useEffect(() => {
    setResults(null);
    if (q.trim().length >= 2) {
      chat.search(q).then(setResults);
      fetch(`/api/projects-search?q=${encodeURIComponent(q)}`, { credentials: "include" }).then((r) => r.json()).then(setWork);
    } else setResults([]);
  }, [q]);
  const people = q ? members.filter((m) => m.name.toLowerCase().includes(q.toLowerCase())) : [];
  const chans = q ? channels.filter((c) => c.kind === "channel" && c.name.includes(q.toLowerCase())) : [];
  if (!me) return null;
  return (
    <div className="mx-auto max-w-3xl px-4 py-6 sm:py-8">
      <div className="flex items-center gap-2 text-sm text-ink-muted"><Search size={15} /> Résultats pour</div>
      <h1 className="mt-1 text-3xl font-semibold tracking-tight">« {q} »</h1>
      {(people.length > 0 || chans.length > 0) && (
        <div className="mt-6 flex flex-wrap gap-2">
          {people.map((m) => (
            <Link key={m.id} to={`/discussions?avec=${m.id}`} className="flex items-center gap-2 rounded-full border border-line bg-white py-1 pl-1 pr-3 text-sm shadow-sm hover:border-accent">
              <Avatar member={m} presence={presenceOf(m)} size="sm" /> {m.name}
            </Link>
          ))}
          {chans.map((c) => (
            <Link key={c.id} to={`/discussions/${c.id}`} className="flex items-center gap-1.5 rounded-full border border-line bg-white px-3 py-1.5 text-sm shadow-sm hover:border-accent">
              <Hash size={14} className="text-accent" /> {c.name}
            </Link>
          ))}
        </div>
      )}
      {(work.pages.length > 0 || work.tasks.length > 0) && (
        <>
          <h2 className="mt-8 text-sm font-semibold text-ink-soft">Projets · {work.pages.length + work.tasks.length}</h2>
          <div className="mt-3 space-y-2">
            {work.pages.map((p) => (
              <Link key={p.id} to={`/projets/${p.project_id}/page/${p.id}`} className="flex items-center gap-3 rounded-2xl border border-line bg-white p-4 shadow-sm hover:border-accent/40">
                <span className="text-xl">{p.icon}</span><span className="font-medium"><Highlight text={p.title || "Sans titre"} q={q} /></span><span className="text-xs text-ink-muted">page</span>
              </Link>
            ))}
            {work.tasks.map((t) => (
              <Link key={t.id} to={`/projets/${t.project_id}`} className="flex items-center gap-3 rounded-2xl border border-line bg-white p-4 shadow-sm hover:border-accent/40">
                <span className={`h-2.5 w-2.5 rounded-full ${t.status === "done" ? "bg-online" : "bg-accent"}`} /><span className="font-medium"><Highlight text={t.title} q={q} /></span><span className="text-xs text-ink-muted">tâche</span>
              </Link>
            ))}
          </div>
        </>
      )}
      <h2 className="mt-8 text-sm font-semibold text-ink-soft">Messages{results ? ` · ${results.length}` : ""}</h2>
      <div className="mt-3 space-y-2">
        {results?.length === 0 && <p className="rounded-2xl bg-white p-6 text-center text-sm text-ink-muted shadow-sm">Aucun message ne contient ce mot.</p>}
        {results?.map((m) => {
          const a = members.find((x) => x.id === m.author_id);
          const ch = channels.find((c) => c.id === m.channel_id);
          if (!a) return null;
          return (
            <Link key={m.id} to={`/discussions/${m.channel_id}${m.parent_id ? `?fil=${m.parent_id}` : ""}`}
              className="flex gap-3 rounded-2xl border border-line bg-white p-4 shadow-sm transition hover:border-accent/40 hover:shadow-md">
              <Avatar member={a} size="sm" />
              <div className="min-w-0 flex-1">
                <div className="text-sm"><b className="font-semibold">{a.name}</b>
                  <span className="text-ink-muted"> · {ch ? `${ch.kind === "channel" ? "#" : ""}${channelTitle(ch, members, me.id)}` : ""} · {dayLabel(m.created_at)} {time(m.created_at)}</span>
                </div>
                <p className="mt-1 text-sm text-ink-soft"><Highlight text={decodeMentions(m.body, members)} q={q} /></p>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
