// Accès à l'API de HQ. Toutes les routes sont sous /api ; la session est un cookie httpOnly.

export type Role = "head" | "membre";
export type Kind = "humain" | "agent";
export type Status = "en_ligne" | "travaille" | "en_attente" | "bloque" | "absent" | "en_preparation";

export interface MemberRef {
  id: number;
  name: string;
  kind: Kind;
  initials: string;
  color: string;
}

export type Pole = "direction" | "operations" | "produit" | "croissance" | "";

export interface Member extends MemberRef {
  email: string | null;
  role: Role;
  title: string;
  pole: Pole;
  status: Status;
  status_label: string;
  active: boolean;
}

export interface AuthConfig {
  google_client_id: string | null;
  dev_login: boolean;
  email_login: boolean;
}

export type KpiKey =
  | "utilisateurs_inscrits"
  | "pros_actifs"
  | "reservations_7j"
  | "acomptes_7j_fcfa"
  | "revenu_nyuman_7j_fcfa";

export interface Kpi {
  key: KpiKey;
  label: string;
  value: number;
  unit: "nombre" | "fcfa";
}

export interface Kpis {
  available: boolean;
  reason: string | null;
  updated_at: string | null;
  values: Kpi[];
}

/** Un objectif suit un chiffre de l'app, ou un chiffre tenu à la main par le pôle (« manuel »). */
export type ObjectiveMetric = KpiKey | "manuel";

export interface Objective {
  id: number;
  title: string;
  quarter: string;
  metric: ObjectiveMetric;
  target: number;
  start_date: string;
  end_date: string;
  pole: Pole;
  current: number | null;
  progress: number | null;
  weeks_left: number;
  needed_per_week: number | null;
}

export interface ObjectiveInput {
  title: string;
  quarter: string;
  metric: ObjectiveMetric;
  target: number;
  start_date: string;
  end_date: string;
  current_manual?: number | null;
}

export interface Rapport {
  id: number;
  author_id: number;
  week: string;
  pole: Pole;
  fait: string;
  en_cours: string;
  bloque: string;
  propositions: string;
  created_at: string;
  updated_at: string;
}

export type RapportInput = Pick<Rapport, "fait" | "en_cours" | "bloque" | "propositions">;

export const CATEGORIES = [
  { key: "cerveau", label: "Cerveau commun" },
  { key: "contrats", label: "Contrats" },
  { key: "finances", label: "Finances" },
  { key: "comptes-rendus", label: "Comptes rendus" },
  { key: "specs", label: "Specs" },
  { key: "pitch", label: "Pitch" },
  { key: "autre", label: "Autre" },
] as const;

export type Category = (typeof CATEGORIES)[number]["key"];

export interface DocumentSummary {
  id: number;
  title: string;
  category: Category;
  version: number;
  archived: boolean;
  excerpt: string;
  updated_at: string;
  updated_by: MemberRef;
}

/** Les pièces de la maison : là où chacun se trouve en ce moment. */
export type Piece = "salon" | "bureaux" | "bibliotheque" | "projet" | "conseil" | "entree";

export interface Presence {
  piece: Piece;
  label: string;
  document_id: number | null;
  editing: boolean;
  updated_at: string;
}

export interface PresenceInput {
  piece: Piece;
  label: string;
  document_id?: number | null;
  editing?: boolean;
}

/** Messages du flux en direct (/api/flux). */
export type LiveMessage =
  | { type: "bonjour"; presences: Record<string, Presence> }
  | { type: "presence"; membre_id: number; presence: Presence | null }
  | { type: "evenement"; id: number; actor_id: number; text: string; link: string | null; created_at: string }
  | { type: "changement"; sujets: string[] };

export type TacheStatus = "a_faire" | "en_cours" | "en_attente" | "fait";

export interface Tache {
  id: number;
  title: string;
  description: string;
  status: TacheStatus;
  assignee: MemberRef | null;
  pole: Pole;
  due_date: string | null;
  priority: Priorite;
  objectif_id: number | null;
  position: number;
  source: "humain" | "agent" | "testflight" | "tableau";
  retour_id: number | null;
  created_by: MemberRef;
  created_at: string;
  updated_at: string;
  done_at: string | null;
  etapes: Etape[];
}

export type Priorite = "P0" | "P1" | "P2" | "P3" | "";
export type EtapeStatus = "a_faire" | "en_cours" | "fait";

export interface Etape {
  id: number;
  title: string;
  responsable: MemberRef | null;
  livrable: string;
  status: EtapeStatus;
  start_date: string | null;
  due_date: string | null;
  notes: string;
  position: number;
}

export type EtapeChanges = Partial<{
  title: string;
  responsable_id: number | null;
  livrable: string;
  status: EtapeStatus;
  start_date: string | null;
  due_date: string | null;
  notes: string;
  position: number;
}>;

export type DecisionStatut = "nouveau" | "a_initier" | "en_cours" | "valide" | "ajourne" | "refuse";
export type VoteValeur = "pour" | "contre" | "abstention";
export type Verdict = "bonne" | "mitigee" | "mauvaise";

export interface Vote {
  membre: MemberRef;
  vote: VoteValeur;
  commentaire: string;
  updated_at: string;
}

export interface Decision {
  id: number;
  titre: string;
  demande: string;
  pole_concerne: Pole;
  poles_en_charge: Exclude<Pole, "">[];
  objectif: string;
  risques: string;
  decision: string;
  liens: string;
  statut: DecisionStatut;
  date_demande: string | null;
  decided_at: string | null;
  decided_by: MemberRef | null;
  revue_le: string | null;
  a_revoir: boolean;
  bilan: string;
  bilan_verdict: Verdict | "";
  bilan_at: string | null;
  author: MemberRef;
  votes: Vote[];
  created_at: string;
  updated_at: string;
}

export interface DecisionInput {
  titre: string;
  demande?: string;
  pole_concerne?: Pole;
  poles_en_charge?: Exclude<Pole, "">[];
  objectif?: string;
  risques?: string;
  liens?: string;
}

export type DecisionChanges = Partial<DecisionInput & { decision: string; statut: DecisionStatut; date_demande: string }>;

export type ProCategorie = "fondateur" | "ambassadeur" | "partenaire" | "prospect";
export type ProContrat = "" | "a_envoyer" | "en_attente" | "signe" | "non_requis";
export type ProAcces = "" | "a_envoyer" | "envoye" | "installe" | "actif";

export interface Pro {
  id: number;
  numero: number | null;
  categorie: ProCategorie;
  nom: string;
  enseigne: string;
  audience: string;
  telephone: string;
  email: string;
  contrat: ProContrat;
  acces_test: ProAcces;
  notes: string;
  suivi_par: MemberRef | null;
  created_at: string;
  updated_at: string;
}

export type ProInput = {
  nom: string;
  categorie?: ProCategorie;
  enseigne?: string;
  audience?: string;
  telephone?: string;
  email?: string;
  contrat?: ProContrat;
  acces_test?: ProAcces;
  notes?: string;
  suivi_par_id?: number | null;
};

export interface RapportImport {
  apercu: boolean;
  lignes: { contenu: string; nouveaux: number; deja_la: number }[];
  onglets: Record<string, string>;
  avertissements: string[];
}

export interface TacheInput {
  title: string;
  description?: string;
  status?: TacheStatus;
  assignee_id?: number | null;
  pole?: Pole;
  due_date?: string | null;
  priority?: Priorite;
  objectif?: boolean;
}

export type TacheChanges = Partial<{
  title: string;
  description: string;
  status: TacheStatus;
  assignee_id: number | null;
  pole: Pole;
  due_date: string | null;
  priority: Priorite;
  position: number;
  objectif: boolean;
}>;

export type RetourKind = "bug" | "idee" | "remarque";

export interface Retour {
  id: number;
  kind: RetourKind;
  source: "hq" | "testflight";
  comment: string;
  author: MemberRef | null;
  tester_email: string | null;
  espace: "cliente" | "pro" | "";
  device_model: string;
  os_version: string;
  build_version: string;
  captures: number;
  statut: "nouveau" | "en_tache" | "classe";
  tache_id: number | null;
  created_at: string;
}

export interface RetoursEtat {
  nouveaux: number;
  testflight_branche: boolean;
  derniere_synchro: string | null;
  derniere_erreur: string | null;
}

export const captureUrl = (retourId: number, index: number) => `/api/retours/${retourId}/captures/${index}`;

export interface DocumentFull extends DocumentSummary {
  content: string;
  created_at: string;
  created_by: MemberRef;
}

export interface DocumentInput {
  title: string;
  category: Category;
  content: string;
}

export interface DocumentVersion {
  version: number;
  title: string;
  author: MemberRef;
  created_at: string;
}

export interface DocumentVersionFull extends DocumentVersion {
  content: string;
}

export interface HqEvent {
  id: number;
  actor: MemberRef;
  text: string;
  link: string | null;
  created_at: string;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method,
    credentials: "include",
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = data && typeof data.detail === "string" ? data.detail : "Le serveur n’a pas répondu comme prévu.";
    throw new ApiError(res.status, detail);
  }
  return data as T;
}

export const api = {
  authConfig: () => request<AuthConfig>("GET", "/auth/config"),
  me: () => request<Member>("GET", "/auth/me"),
  loginGoogle: (credential: string) => request<Member>("POST", "/auth/google", { credential }),
  loginDev: (email: string) => request<Member>("POST", "/auth/dev", { email }),
  demanderLien: (email: string) => request<void>("POST", "/auth/lien", { email }),
  validerLien: (jeton: string) => request<Member>("POST", "/auth/lien/valider", { jeton }),
  logout: () => request<void>("POST", "/auth/logout"),

  members: () => request<Member[]>("GET", "/membres"),
  addMember: (input: { email: string; name: string; title: string; role: Role; pole: Pole }) =>
    request<Member>("POST", "/membres", input),
  updateMember: (id: number, input: { role?: Role; title?: string; active?: boolean; pole?: Pole }) =>
    request<Member>("PATCH", `/membres/${id}`, input),

  kpis: () => request<Kpis>("GET", "/kpis"),
  objective: (pole: Pole = "") => request<Objective | null>("GET", `/objectifs/courant${pole ? `?pole=${pole}` : ""}`),
  saveObjective: (input: ObjectiveInput, pole: Pole = "") =>
    request<Objective>("PUT", `/objectifs/courant${pole ? `?pole=${pole}` : ""}`, input),
  poleObjectives: () => request<Partial<Record<Pole, Objective>>>("GET", "/objectifs/poles"),
  updateAvancement: (id: number, value: number) => request<Objective>("PATCH", `/objectifs/${id}/avancement`, { value }),

  rapports: (auteur: number) => request<Rapport[]>("GET", `/rapports?auteur=${auteur}`),
  rapportsSemaine: () => request<{ week: string; rapports: Rapport[] }>("GET", "/rapports/semaine"),
  publishRapport: (input: RapportInput) => request<Rapport>("PUT", "/rapports/moi", input),

  documents: (params: { categorie?: string; q?: string; archives?: boolean }) => {
    const qs = new URLSearchParams();
    if (params.categorie) qs.set("categorie", params.categorie);
    if (params.q) qs.set("q", params.q);
    if (params.archives) qs.set("archives", "true");
    const s = qs.toString();
    return request<DocumentSummary[]>("GET", `/documents${s ? `?${s}` : ""}`);
  },
  document: (id: number) => request<DocumentFull>("GET", `/documents/${id}`),
  createDocument: (input: DocumentInput) => request<DocumentFull>("POST", "/documents", input),
  updateDocument: (id: number, input: DocumentInput & { base_version: number }) =>
    request<DocumentFull>("PUT", `/documents/${id}`, input),
  archiveDocument: (id: number) => request<DocumentFull>("POST", `/documents/${id}/archiver`),
  restoreDocument: (id: number) => request<DocumentFull>("POST", `/documents/${id}/restaurer`),
  versions: (id: number) => request<DocumentVersion[]>("GET", `/documents/${id}/versions`),
  version: (id: number, version: number) =>
    request<DocumentVersionFull>("GET", `/documents/${id}/versions/${version}`),

  events: (acteur?: number) => request<HqEvent[]>("GET", `/evenements${acteur ? `?acteur=${acteur}&limit=50` : ""}`),
  reportPresence: (input: PresenceInput) => request<void>("POST", "/presence", input),

  taches: (assignee?: number) => request<Tache[]>("GET", `/taches${assignee ? `?assignee=${assignee}` : ""}`),
  createTache: (input: TacheInput) => request<Tache>("POST", "/taches", input),
  updateTache: (id: number, changes: TacheChanges) => request<Tache>("PATCH", `/taches/${id}`, changes),
  archiveTache: (id: number) => request<Tache>("POST", `/taches/${id}/archiver`),
  addEtape: (tacheId: number, input: EtapeChanges & { title: string }) => request<Tache>("POST", `/taches/${tacheId}/etapes`, input),
  updateEtape: (tacheId: number, etapeId: number, changes: EtapeChanges) =>
    request<Tache>("PATCH", `/taches/${tacheId}/etapes/${etapeId}`, changes),
  archiveEtape: (tacheId: number, etapeId: number) => request<Tache>("POST", `/taches/${tacheId}/etapes/${etapeId}/archiver`),

  decisions: () => request<Decision[]>("GET", "/decisions"),
  createDecision: (input: DecisionInput) => request<Decision>("POST", "/decisions", input),
  updateDecision: (id: number, changes: DecisionChanges) => request<Decision>("PATCH", `/decisions/${id}`, changes),
  voteDecision: (id: number, vote: VoteValeur, commentaire: string) =>
    request<Decision>("PUT", `/decisions/${id}/vote`, { vote, commentaire }),
  bilanDecision: (id: number, verdict: Verdict, bilan: string) => request<Decision>("PUT", `/decisions/${id}/bilan`, { verdict, bilan }),
  archiveDecision: (id: number) => request<Decision>("POST", `/decisions/${id}/archiver`),

  pros: () => request<Pro[]>("GET", "/pros"),
  createPro: (input: ProInput) => request<Pro>("POST", "/pros", input),
  updatePro: (id: number, changes: Partial<ProInput>) => request<Pro>("PATCH", `/pros/${id}`, changes),
  archivePro: (id: number) => request<Pro>("POST", `/pros/${id}/archiver`),

  importTableau: async (fichier: File, apercu: boolean): Promise<RapportImport> => {
    const form = new FormData();
    form.append("fichier", fichier);
    const res = await fetch(`/api/import/tableau?apercu=${apercu}`, { method: "POST", credentials: "include", body: form });
    const data = await res.json().catch(() => null);
    if (!res.ok) throw new ApiError(res.status, data && typeof data.detail === "string" ? data.detail : "La reprise a échoué.");
    return data as RapportImport;
  },

  retours: (statut: "nouveau" | "en_tache" | "classe" | "tous" = "nouveau") => request<Retour[]>("GET", `/retours?statut=${statut}`),
  retoursEtat: () => request<RetoursEtat>("GET", "/retours/etat"),
  createRetour: async (form: FormData): Promise<Retour> => {
    // Envoi en multipart (texte + images) : le navigateur fixe lui-même l'en-tête Content-Type.
    const res = await fetch("/api/retours", { method: "POST", credentials: "include", body: form });
    const data = await res.json().catch(() => null);
    if (!res.ok) throw new ApiError(res.status, data && typeof data.detail === "string" ? data.detail : "L’envoi a échoué.");
    return data as Retour;
  },
  convertRetour: (id: number, input: { title?: string; assignee_id?: number | null }) => request<Tache>("POST", `/retours/${id}/tache`, input),
  classerRetour: (id: number) => request<Retour>("POST", `/retours/${id}/classer`),
  syncTestflight: () => request<{ nouveaux: number }>("POST", "/retours/synchroniser"),
};
