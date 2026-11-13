#!/usr/bin/env node
/**
 * Connecteur Claude (MCP) de Nyuman HQ.
 *
 * Les agents (Kodjo, Adjoua, Koffi, Mariam, Kwame…) l'utilisent pour lire et écrire dans HQ
 * comme membres de l'équipe : discussions, mentions, réunions, organigramme, statut.
 *
 * Réglages (variables d'environnement) :
 *   HQ_URL          adresse du serveur HQ (défaut : http://localhost:8030)
 *   HQ_AGENT        identifiant de l'agent (ex. « kodjo »). Sinon : outil hq_je_suis.
 *   HQ_AGENT_TOKEN  clé de l'agent, créée par un head (obligatoire en ligne, inutile en local).
 * La clé n'est jamais affichée ni écrite dans les réponses.
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const BASE = (process.env.HQ_URL || "http://localhost:8030").replace(/\/$/, "");
const TOKEN = process.env.HQ_AGENT_TOKEN || "";
let agent = (process.env.HQ_AGENT || "").trim().toLowerCase();
let membersCache = null;

async function api(method, path, body) {
  if (!agent) throw new Error("Dites d'abord qui vous êtes avec l'outil hq_je_suis (ex. « kodjo »).");
  const headers = { "X-HQ-Agent": agent, "Content-Type": "application/json" };
  if (TOKEN) headers.Authorization = `Bearer ${TOKEN}`;
  const res = await fetch(BASE + path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) throw new Error(`HQ a refusé (${res.status}) : ${data?.detail ?? res.statusText}`);
  return data;
}

async function members() {
  if (!membersCache) membersCache = await api("GET", "/api/members");
  return membersCache;
}
const nameOf = (list, id) => list.find((m) => m.id === id)?.name ?? id;

/** « @Kevin » ou « @Kevin Diakité » → jeton de mention compris par HQ. */
async function encode(text) {
  const list = [...(await members())].sort((a, b) => b.name.length - a.name.length);
  let out = text;
  for (const m of list) {
    out = out.split("@" + m.name).join(`<@${m.id}>`);
    const first = m.name.split(" ")[0];
    out = out.replace(new RegExp(`@${first}(?![\\p{L}-])`, "gu"), `<@${m.id}>`);
  }
  return out;
}
async function decode(body) {
  const list = await members();
  return body
    .replace(/<meeting:([a-f0-9]+)>/g, "[réunion $1]")
    .replace(/<@([a-z0-9_-]+)>/g, (_, id) => "@" + nameOf(list, id));
}

async function channelId(ref) {
  const r = ref.trim().replace(/^#/, "").toLowerCase();
  const chans = await api("GET", "/api/channels");
  const hit = chans.find((c) => c.id === ref || c.name === r || c.id === r);
  if (!hit) throw new Error(`Canal introuvable : « ${ref} ». Canaux : ${chans.filter((c) => c.kind === "channel").map((c) => "#" + c.name).join(", ")}`);
  return hit.id;
}

async function fmtMessages(msgs) {
  const list = await members();
  const lines = [];
  for (const m of msgs) {
    if (m.deleted) continue;
    const when = new Date(m.created_at).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short", timeZone: "Africa/Abidjan" });
    let line = `[${m.id}] ${when} — ${nameOf(list, m.author_id)} : ${await decode(m.body)}`;
    if (m.attachments?.length) line += ` (📎 ${m.attachments.map((a) => a.filename).join(", ")})`;
    if (m.reply_count) line += ` [${m.reply_count} réponse(s) dans le fil]`;
    if (m.reactions?.length) line += ` ${m.reactions.map((r) => r.emoji + r.member_ids.length).join(" ")}`;
    lines.push(line);
  }
  return lines.join("\n") || "(aucun message)";
}

const ok = (text) => ({ content: [{ type: "text", text }] });
const server = new McpServer({ name: "nyuman-hq", version: "0.1.0" });
const tool = (name, description, inputSchema, run) =>
  server.registerTool(name, { description, inputSchema }, async (args) => {
    try { return ok(await run(args)); }
    catch (e) { return { isError: true, content: [{ type: "text", text: String(e.message || e) }] }; }
  });

tool("hq_je_suis", "Indique quel agent vous êtes dans HQ (kodjo, adjoua, koffi, mariam, kwame…). À appeler une fois en début de session si HQ_AGENT n'est pas réglé.",
  { agent: z.string().describe("identifiant de l'agent, ex. « kodjo »") },
  async ({ agent: a }) => {
    agent = a.trim().toLowerCase();
    membersCache = null;
    const me = await api("GET", "/api/auth/me");
    return `Connecté à HQ en tant que ${me.name} (${me.title}).`;
  });

tool("hq_moi", "Votre fiche dans HQ : nom, rôle, statut, ce que vous faites en ce moment.", {}, async () => {
  const me = await api("GET", "/api/auth/me");
  return JSON.stringify({ id: me.id, nom: me.name, poste: me.title, role: me.role, statut: me.manual_status, en_ce_moment: me.now_doing }, null, 2);
});

tool("hq_statut", "Met à jour votre statut d'agent et ce que vous faites (visible par toute l'équipe sur votre fiche).",
  {
    etat: z.enum(["au_travail", "en_attente", "bloque"]).optional().describe("au_travail, en_attente ou bloque"),
    en_ce_moment: z.string().max(300).optional().describe("une phrase : ce que vous faites maintenant"),
  },
  async ({ etat, en_ce_moment }) => {
    const map = { au_travail: "working", en_attente: "waiting", bloque: "blocked" };
    const body = {};
    if (etat) body.manual_status = map[etat];
    if (en_ce_moment !== undefined) body.now_doing = en_ce_moment;
    const me = await api("PATCH", "/api/members/me", body);
    return `Statut mis à jour : ${etat ?? "inchangé"} · « ${me.now_doing} »`;
  });

tool("hq_equipe", "Liste les membres de l'équipe (humains et agents) avec leur poste.", {}, async () => {
  const list = await members();
  return list.map((m) => `${m.id} — ${m.name} (${m.kind === "agent" ? "agent" : "humain"}) · ${m.title}${m.now_doing ? " · en ce moment : " + m.now_doing : ""}`).join("\n");
});

tool("hq_organigramme", "L'organigramme : les 12 postes, qui les tient et quels agents les appuient.", {}, async () => {
  const org = await api("GET", "/api/org");
  const list = await members();
  return org.positions.map((p) => `${p.id}. ${p.title} (${p.department}) — ${p.holder_ids.map((i) => nameOf(list, i)).join(", ") || "à pourvoir"}${p.support_ids.length ? " · appui : " + p.support_ids.map((i) => nameOf(list, i)).join(", ") : ""}\n   Mission : ${p.mission}`).join("\n");
});

tool("hq_canaux", "Liste vos canaux et discussions privées, avec les non-lus et les mentions.", {}, async () => {
  const list = await members();
  const chans = await api("GET", "/api/channels");
  return chans.map((c) => {
    const title = c.kind === "channel" ? `#${c.name}` : "Privé avec " + c.member_ids.filter((i) => i !== agent).map((i) => nameOf(list, i)).join(", ");
    return `${title} [id ${c.id}] — ${c.unread} non lu(s)${c.mentions ? `, ${c.mentions} mention(s)` : ""}`;
  }).join("\n");
});

tool("hq_lire", "Lit les derniers messages d'un canal (ex. « général », « tech ») ou d'une discussion privée (par son id). Marque comme lu.",
  { canal: z.string().describe("nom du canal (général, tech, finance, opérations…) ou id"), nombre: z.number().int().min(1).max(100).optional() },
  async ({ canal, nombre }) => {
    const id = await channelId(canal);
    const msgs = await api("GET", `/api/channels/${id}/messages`);
    await api("POST", `/api/channels/${id}/read`);
    return fmtMessages(msgs.slice(-(nombre ?? 30)));
  });

tool("hq_lire_fil", "Lit un fil de discussion (le message de départ et ses réponses).",
  { message_id: z.string() },
  async ({ message_id }) => {
    const t = await api("GET", `/api/messages/${message_id}/thread`);
    return (await fmtMessages([t.root])) + "\n— réponses —\n" + (await fmtMessages(t.replies));
  });

tool("hq_ecrire", "Écrit un message dans un canal, ou répond dans un fil (fil_id). Mentionnez avec @Prénom (ex. « @Kevin »). Restez bref et clair, en français simple.",
  { canal: z.string().describe("nom du canal ou id"), texte: z.string().min(1).max(8000), fil_id: z.string().optional().describe("id du message de départ pour répondre dans son fil") },
  async ({ canal, texte, fil_id }) => {
    const id = await channelId(canal);
    const m = await api("POST", `/api/channels/${id}/messages`, { body: await encode(texte), parent_id: fil_id ?? null });
    return `Message envoyé [${m.id}].`;
  });

tool("hq_message_prive", "Envoie un message privé à une ou plusieurs personnes (identifiants : mohamed, kevin, kodjo…).",
  { a: z.array(z.string()).min(1).describe("identifiants des destinataires"), texte: z.string().min(1).max(8000) },
  async ({ a, texte }) => {
    const { id } = await api("POST", "/api/dms", { member_ids: a.map((x) => x.toLowerCase()) });
    const m = await api("POST", `/api/channels/${id}/messages`, { body: await encode(texte) });
    return `Message privé envoyé [${m.id}] dans la discussion ${id}.`;
  });

tool("hq_reagir", "Ajoute (ou retire) une réaction emoji à un message.",
  { message_id: z.string(), emoji: z.string().max(16) },
  async ({ message_id, emoji }) => { await api("POST", `/api/messages/${message_id}/reactions`, { emoji }); return "Réaction enregistrée."; });

tool("hq_activite", "Ce qui vous concerne : les messages où l'on vous mentionne et les réponses dans vos fils. À consulter en début de session.",
  {}, async () => {
    const items = await api("GET", "/api/activity");
    if (!items.length) return "Rien de nouveau pour vous.";
    const list = await members();
    const chans = await api("GET", "/api/channels");
    const lines = [];
    for (const it of items.slice(0, 20)) {
      const m = it.message;
      const ch = chans.find((c) => c.id === m.channel_id);
      const where = ch?.kind === "channel" ? `#${ch.name}` : "privé";
      lines.push(`${it.kind === "mention" ? "@ mention" : "↳ réponse"} · ${where} · ${nameOf(list, m.author_id)} [${m.id}${m.parent_id ? ", fil " + m.parent_id : ""}] : ${await decode(m.body)}`);
    }
    return lines.join("\n");
  });

tool("hq_chercher", "Cherche un mot dans les messages de HQ.", { mot: z.string().min(2) }, async ({ mot }) =>
  fmtMessages(await api("GET", `/api/search?q=${encodeURIComponent(mot)}`)));

tool("hq_reunions", "Vos prochaines réunions (titre, heure, lien, participants).", {}, async () => {
  const list = await members();
  const ms = await api("GET", "/api/meetings/upcoming");
  if (!ms.length) return "Aucune réunion prévue.";
  return ms.map((m) => `${m.title} — ${new Date(m.start_at).toLocaleString("fr-FR", { dateStyle: "full", timeStyle: "short", timeZone: "Africa/Abidjan" })} · ${m.link || "sans lien"} · ${m.attendees.map((a) => nameOf(list, a.member_id) + " (" + a.response + ")").join(", ")} [id ${m.id}]`).join("\n");
});

tool("hq_planifier_reunion", "Planifie une réunion d'équipe avec lien Jitsi et l'annonce dans un canal. Heure d'Abidjan (UTC).",
  {
    titre: z.string().min(1).max(160),
    debut: z.string().describe("date et heure de début, ex. 2026-11-18T10:00 (heure d'Abidjan)"),
    duree_minutes: z.number().int().min(5).max(480),
    participants: z.array(z.string()).describe("identifiants : mohamed, kevin…"),
    canal: z.string().optional().describe("canal où l'annoncer (ex. général)"),
    ordre_du_jour: z.string().optional(),
  },
  async ({ titre, debut, duree_minutes, participants, canal, ordre_du_jour }) => {
    const start = new Date(/Z|[+-]\d\d:?\d\d$/.test(debut) ? debut : debut + "Z");
    if (isNaN(start)) throw new Error("Date de début invalide.");
    const m = await api("POST", "/api/meetings", {
      title: titre, description: ordre_du_jour ?? "", start_at: start.toISOString(),
      end_at: new Date(start.getTime() + duree_minutes * 60000).toISOString(),
      attendee_ids: participants.map((x) => x.toLowerCase()), link_kind: "jitsi",
      channel_id: canal ? await channelId(canal) : null, reminder_minutes: 10,
    });
    return `Réunion planifiée : ${m.title} · ${m.link} [id ${m.id}]`;
  });

// ---------- projets, tâches, pages ----------
const STATUTS = { a_faire: "todo", en_cours: "doing", en_revue: "review", termine: "done" };
const STATUT_FR = Object.fromEntries(Object.entries(STATUTS).map(([k, v]) => [v, k]));

async function projectId(ref) {
  const list = await api("GET", "/api/projects");
  const r = ref.trim().toLowerCase();
  const hit = list.find((p) => p.id === ref || p.name.toLowerCase() === r) || list.find((p) => p.name.toLowerCase().includes(r));
  if (!hit) throw new Error(`Projet introuvable : « ${ref} ». Projets : ${list.map((p) => p.name).join(", ") || "aucun"}`);
  return hit;
}
async function fmtTasks(tasks) {
  const list = await members();
  const projects = await api("GET", "/api/projects");
  return tasks.map((t) => `[${t.id}] ${t.title} — ${STATUT_FR[t.status]} · ${t.assignee_id ? nameOf(list, t.assignee_id) : "personne"}${t.due_date ? " · échéance " + t.due_date : ""}${t.priority === "high" ? " · priorité haute" : ""} · ${projects.find((p) => p.id === t.project_id)?.name ?? ""}`).join("\n") || "(aucune tâche)";
}
/** Texte simple → paragraphes de l'éditeur de pages (une ligne « - » = puce, « [ ] » = case à cocher). */
function toNodes(texte) {
  const nodes = [];
  const para = (t) => ({ type: "paragraph", content: t ? [{ type: "text", text: t }] : [] });
  const push = (listType, item) => {
    const last = nodes[nodes.length - 1];
    if (last?.type === listType) last.content.push(item);
    else nodes.push({ type: listType, content: [item] });
  };
  for (const line of texte.split("\n")) {
    const t = line.trimEnd();
    if (!t) continue;
    const box = t.match(/^\s*\[( |x)\]\s+(.*)$/i);
    const bullet = t.match(/^\s*[-•]\s+(.*)$/);
    const h = t.match(/^(#{1,2})\s+(.*)$/);
    if (box) push("taskList", { type: "taskItem", attrs: { checked: box[1].toLowerCase() === "x" }, content: [para(box[2])] });
    else if (bullet) push("bulletList", { type: "listItem", content: [para(bullet[1])] });
    else if (h) nodes.push({ type: "heading", attrs: { level: h[1].length }, content: [{ type: "text", text: h[2] }] });
    else nodes.push(para(t));
  }
  return nodes;
}

tool("hq_projets", "Liste les projets (façon Notion) avec le nombre de tâches par statut.", {}, async () => {
  const list = await api("GET", "/api/projects");
  return list.map((p) => `${p.icon} ${p.name} [id ${p.id}]${p.department ? " · " + p.department : ""} — ${Object.entries(p.counts).map(([k, v]) => STATUT_FR[k] + " " + v).join(", ") || "aucune tâche"}`).join("\n") || "Aucun projet.";
});

tool("hq_taches", "Liste des tâches : les vôtres par défaut, ou celles d'un projet / d'une personne.",
  { projet: z.string().optional(), personne: z.string().optional().describe("identifiant, ex. kevin ; « moi » par défaut"), statut: z.enum(["a_faire", "en_cours", "en_revue", "termine"]).optional() },
  async ({ projet, personne, statut }) => {
    const params = new URLSearchParams();
    if (projet) params.set("project_id", (await projectId(projet)).id);
    if (personne || !projet) params.set("assignee_id", (personne || agent).toLowerCase());
    if (statut) params.set("status", STATUTS[statut]);
    return fmtTasks(await api("GET", `/api/tasks?${params}`));
  });

tool("hq_creer_tache", "Crée une tâche dans un projet, avec responsable et échéance si besoin.",
  {
    projet: z.string(), titre: z.string().min(1).max(300), responsable: z.string().optional().describe("identifiant, ex. kevin"),
    echeance: z.string().optional().describe("AAAA-MM-JJ"), priorite: z.enum(["basse", "normale", "haute"]).optional(), description: z.string().optional(),
  },
  async ({ projet, titre, responsable, echeance, priorite, description }) => {
    const p = await projectId(projet);
    const t = await api("POST", "/api/tasks", {
      project_id: p.id, title: titre, assignee_id: responsable?.toLowerCase() ?? null, due_date: echeance ?? null,
      priority: { basse: "low", normale: "normal", haute: "high" }[priorite ?? "normale"], description: description ?? "",
    });
    return `Tâche créée [${t.id}] dans ${p.name}.`;
  });

tool("hq_maj_tache", "Met à jour une tâche : statut, responsable, échéance, titre ou description.",
  {
    tache_id: z.string(), statut: z.enum(["a_faire", "en_cours", "en_revue", "termine"]).optional(), responsable: z.string().optional(),
    echeance: z.string().optional().describe("AAAA-MM-JJ, ou « aucune »"), titre: z.string().optional(), description: z.string().optional(),
  },
  async ({ tache_id, statut, responsable, echeance, titre, description }) => {
    const d = {};
    if (statut) d.status = STATUTS[statut];
    if (responsable) d.assignee_id = responsable.toLowerCase() === "personne" ? null : responsable.toLowerCase();
    if (echeance) d.due_date = echeance === "aucune" ? null : echeance;
    if (titre) d.title = titre;
    if (description !== undefined) d.description = description;
    const t = await api("PATCH", `/api/tasks/${tache_id}`, d);
    return `Tâche mise à jour : ${t.title} — ${STATUT_FR[t.status]}.`;
  });

tool("hq_pages", "Liste les pages d'un projet.", { projet: z.string() }, async ({ projet }) => {
  const p = await projectId(projet);
  const pages = await api("GET", `/api/projects/${p.id}/pages`);
  return pages.map((x) => `${x.icon} ${x.title || "Sans titre"} [id ${x.id}]${x.parent_id ? " (sous-page)" : ""}`).join("\n") || "Aucune page.";
});

tool("hq_lire_page", "Lit le texte d'une page de projet.", { page_id: z.string() }, async ({ page_id }) => {
  const p = await api("GET", `/api/pages/${page_id}`);
  const list = await members();
  return `${p.icon} ${p.title || "Sans titre"} (modifiée par ${nameOf(list, p.updated_by)} le ${p.updated_at})\n\n${p.text || "(page vide)"}`;
});

tool("hq_ecrire_page", "Crée une page dans un projet, ou ajoute du texte à la fin d'une page existante. Lignes « - » = puces, « [ ] » = cases à cocher, « # » = titre.",
  { projet: z.string().optional(), page_id: z.string().optional(), titre: z.string().optional(), texte: z.string().min(1) },
  async ({ projet, page_id, titre, texte }) => {
    if (!page_id) {
      if (!projet) throw new Error("Indiquez le projet (pour une nouvelle page) ou page_id (pour ajouter à une page).");
      const p = await projectId(projet);
      const doc = { type: "doc", content: toNodes(texte) };
      const page = await api("POST", `/api/projects/${p.id}/pages`, { title: titre ?? "", content: JSON.stringify(doc), text: texte });
      return `Page créée [${page.id}] dans ${p.name}.`;
    }
    const page = await api("GET", `/api/pages/${page_id}`);
    let doc = { type: "doc", content: [] };
    try { if (page.content) doc = JSON.parse(page.content); } catch { /* page illisible : on repart d'un document vide */ }
    doc.content = [...(doc.content || []), ...toNodes(texte)];
    await api("PATCH", `/api/pages/${page_id}`, { content: JSON.stringify(doc), text: (page.text ? page.text + "\n" : "") + texte, ...(titre ? { title: titre } : {}) });
    return "Texte ajouté à la page.";
  });

await server.connect(new StdioServerTransport());
