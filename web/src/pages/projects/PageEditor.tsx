import { useEffect, useRef, useState } from "react";
import { EditorContent, useEditor, type Editor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import TaskList from "@tiptap/extension-task-list";
import TaskItem from "@tiptap/extension-task-item";
import Placeholder from "@tiptap/extension-placeholder";
import Link from "@tiptap/extension-link";
import Highlight from "@tiptap/extension-highlight";
import { Bold, Heading1, Heading2, Highlighter, Italic, Link2, List, ListChecks, ListOrdered, Minus, Quote, Strikethrough, Undo2 } from "lucide-react";
import { projectsApi, type PageFull } from "../../lib/api";
import { useSession } from "../../lib/session";
import { useLive } from "../../lib/live";
import { Pop } from "./TaskParts";
import { ICONS } from "./meta";

function Btn({ on, label, onClick, children }: { on?: boolean; label: string; onClick: () => void; children: React.ReactNode }) {
  return (
    <button type="button" title={label} aria-label={label} onMouseDown={(e) => e.preventDefault()} onClick={onClick}
      className={`flex h-8 w-8 items-center justify-center rounded-lg transition ${on ? "bg-accent-soft text-accent" : "text-ink-soft hover:bg-surface hover:text-ink"}`}>
      {children}
    </button>
  );
}

function Toolbar({ editor }: { editor: Editor }) {
  const c = () => editor.chain().focus();
  return (
    <div className="sticky top-0 z-10 -mx-2 mb-4 flex flex-wrap items-center gap-0.5 rounded-2xl border border-line bg-white/95 p-1 shadow-sm backdrop-blur">
      <Btn label="Grand titre" on={editor.isActive("heading", { level: 1 })} onClick={() => c().toggleHeading({ level: 1 }).run()}><Heading1 size={17} /></Btn>
      <Btn label="Sous-titre" on={editor.isActive("heading", { level: 2 })} onClick={() => c().toggleHeading({ level: 2 }).run()}><Heading2 size={17} /></Btn>
      <span className="mx-1 h-5 w-px bg-line" />
      <Btn label="Gras" on={editor.isActive("bold")} onClick={() => c().toggleBold().run()}><Bold size={16} /></Btn>
      <Btn label="Italique" on={editor.isActive("italic")} onClick={() => c().toggleItalic().run()}><Italic size={16} /></Btn>
      <Btn label="Barré" on={editor.isActive("strike")} onClick={() => c().toggleStrike().run()}><Strikethrough size={16} /></Btn>
      <Btn label="Surligner" on={editor.isActive("highlight")} onClick={() => c().toggleHighlight().run()}><Highlighter size={16} /></Btn>
      <Btn label="Lien" on={editor.isActive("link")} onClick={() => {
        const url = prompt("Adresse du lien", editor.getAttributes("link").href ?? "https://");
        if (url === null) return;
        url ? c().extendMarkRange("link").setLink({ href: url }).run() : c().unsetLink().run();
      }}><Link2 size={16} /></Btn>
      <span className="mx-1 h-5 w-px bg-line" />
      <Btn label="Liste à puces" on={editor.isActive("bulletList")} onClick={() => c().toggleBulletList().run()}><List size={17} /></Btn>
      <Btn label="Liste numérotée" on={editor.isActive("orderedList")} onClick={() => c().toggleOrderedList().run()}><ListOrdered size={17} /></Btn>
      <Btn label="Cases à cocher" on={editor.isActive("taskList")} onClick={() => c().toggleTaskList().run()}><ListChecks size={17} /></Btn>
      <Btn label="Citation" on={editor.isActive("blockquote")} onClick={() => c().toggleBlockquote().run()}><Quote size={16} /></Btn>
      <Btn label="Séparateur" onClick={() => c().setHorizontalRule().run()}><Minus size={17} /></Btn>
      <span className="ml-auto" />
      <Btn label="Annuler" onClick={() => c().undo().run()}><Undo2 size={16} /></Btn>
    </div>
  );
}

export function PageEditor({ pageId }: { pageId: string }) {
  const [page, setPage] = useState<PageFull | null>(null);
  useEffect(() => {
    let alive = true;
    setPage(null);
    projectsApi.page(pageId).then((p) => { if (alive) setPage(p); });
    return () => { alive = false; };
  }, [pageId]);
  return page ? <EditorBody key={page.id} initial={page} /> : null;
}

function parseDoc(content: string) {
  try { return content ? JSON.parse(content) : ""; } catch { return ""; }
}

/** L'éditeur ne naît qu'une fois la page chargée : son contenu de départ n'entre pas dans « Annuler ». */
function EditorBody({ initial }: { initial: PageFull }) {
  const { members, me } = useSession();
  const { subscribe } = useLive();
  const pageId = initial.id;
  const [page, setPage] = useState<PageFull>(initial);
  const [title, setTitle] = useState(initial.title);
  const [state, setState] = useState<"saved" | "saving" | "idle">("idle");
  const timer = useRef<number | undefined>(undefined);
  const pending = useRef<Partial<PageFull>>({});

  const flush = async () => {
    const d = pending.current;
    pending.current = {};
    if (!Object.keys(d).length) return;
    const saved = await projectsApi.updatePage(pageId, d);
    setPage((p) => ({ ...p, updated_by: saved.updated_by, updated_at: saved.updated_at }));
    setState("saved");
  };
  const save = (d: Partial<PageFull>) => {
    pending.current = { ...pending.current, ...d };
    setState("saving");
    clearTimeout(timer.current);
    timer.current = window.setTimeout(flush, 900);
  };
  useEffect(() => () => { clearTimeout(timer.current); flush(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const editor = useEditor({
    extensions: [
      StarterKit.configure({ heading: { levels: [1, 2, 3] } }),
      TaskList, TaskItem.configure({ nested: true }),
      Link.configure({ openOnClick: true, autolink: true }),
      Highlight,
      Placeholder.configure({ placeholder: "Écrivez ici… Utilisez la barre au-dessus pour les titres, listes et cases à cocher." }),
    ],
    content: parseDoc(initial.content),
    editorProps: { attributes: { class: "hq-prose min-h-[50vh] outline-none" } },
    onUpdate: ({ editor }) => save({ content: JSON.stringify(editor.getJSON()), text: editor.getText() }),
  });

  // Quelqu'un d'autre a modifié la page : on recharge si on n'est pas en train d'écrire (hors « Annuler »).
  useEffect(() => subscribe((ev) => {
    if (ev.type !== "page.updated" || ev.page_id !== pageId || ev.by === me?.id) return;
    if (editor?.isFocused || Object.keys(pending.current).length) return;
    projectsApi.page(pageId).then((p) => {
      setPage(p); setTitle(p.title);
      editor?.chain().setMeta("addToHistory", false).setContent(parseDoc(p.content), false).run();
    });
  }), [subscribe, pageId, editor, me?.id]);

  const who = members.find((m) => m.id === page.updated_by);
  return (
    <div className="mx-auto max-w-3xl px-4 pb-24 pt-6 sm:px-10 sm:pt-10">
      <Pop trigger={(o) => <button onClick={o} className="rounded-xl p-1 text-5xl leading-none transition hover:bg-surface" title="Changer l'icône">{page.icon}</button>}>
        {(close) => <div className="grid grid-cols-8 gap-0.5 p-1">{ICONS.concat(["📄", "📌", "✅", "🗓️", "📞", "🧾", "🎨", "🔒"]).map((i) => (
          <button key={i} onClick={() => { setPage({ ...page, icon: i }); save({ icon: i }); close(); }} className="rounded-lg p-1.5 text-xl hover:bg-surface">{i}</button>
        ))}</div>}
      </Pop>
      <input value={title} onChange={(e) => { setTitle(e.target.value); save({ title: e.target.value }); }} placeholder="Sans titre"
        className="mt-3 w-full bg-transparent text-4xl font-semibold tracking-tight outline-none placeholder:text-ink-muted/60" />
      <div className="mb-6 mt-2 text-xs text-ink-muted">
        {state === "saving" ? "Enregistrement…" : state === "saved" ? "Enregistré ✓" :
          who ? `Modifiée par ${who.name.split(" ")[0]} le ${new Date(page.updated_at).toLocaleDateString("fr-FR", { day: "numeric", month: "long" })} à ${new Date(page.updated_at).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}` : ""}
      </div>
      {editor && <Toolbar editor={editor} />}
      <EditorContent editor={editor} />
    </div>
  );
}
