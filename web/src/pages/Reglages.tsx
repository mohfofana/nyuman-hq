import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, type Member, type Pole, type Role } from "../api";
import { POLES, PoleChip } from "../poles";
import { Avatar } from "../components/Avatar";
import { ImportTableau } from "../components/ImportTableau";
import { usePresence } from "../live";
import { formatAgo } from "../format";

function PoleSelect({ id, value, onChange, disabled, label }: {
  id: string;
  value: Pole;
  onChange: (p: Pole) => void;
  disabled?: boolean;
  label: string;
}) {
  return (
    <>
      <label className="visually-hidden" htmlFor={id}>{label}</label>
      <select id={id} className="select" style={{ width: "auto", minHeight: 36 }} value={value} disabled={disabled}
        onChange={(e) => onChange(e.target.value as Pole)}>
        <option value="">Sans pôle</option>
        {POLES.map((p) => <option key={p.key} value={p.key}>{p.label}</option>)}
      </select>
    </>
  );
}

function AddMember() {
  const queryClient = useQueryClient();
  const empty = { email: "", name: "", title: "", role: "membre" as Role, pole: "" as Pole };
  const [form, setForm] = useState(empty);
  const add = useMutation({
    mutationFn: api.addMember,
    onSuccess: () => {
      setForm(empty);
      queryClient.invalidateQueries({ queryKey: ["membres"] });
      queryClient.invalidateQueries({ queryKey: ["evenements"] });
    },
  });

  function submit(e: FormEvent) {
    e.preventDefault();
    add.mutate({ ...form, email: form.email.trim().toLowerCase() });
  }

  return (
    <form onSubmit={submit} className="card" aria-labelledby="ajout" style={{ gap: 14 }}>
      <h2 id="ajout" style={{ fontSize: 18, fontWeight: 700 }}>Faire entrer quelqu’un</h2>
      <p className="soft small">Seules les adresses ajoutées ici peuvent se connecter avec Google.</p>
      <div className="grid-cards" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 200px), 1fr))" }}>
        <div className="field">
          <label htmlFor="m-name">Nom</label>
          <input id="m-name" className="input" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <div className="field">
          <label htmlFor="m-email">Adresse Google</label>
          <input id="m-email" className="input" type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </div>
        <div className="field">
          <label htmlFor="m-title">Rôle dans l’équipe</label>
          <input id="m-title" className="input" placeholder="COO, CTO, CGO, chargé de…" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        </div>
        <div className="field">
          <label htmlFor="m-pole">Pôle</label>
          <select id="m-pole" className="select" value={form.pole} onChange={(e) => setForm({ ...form, pole: e.target.value as Pole })}>
            <option value="">Sans pôle</option>
            {POLES.map((p) => <option key={p.key} value={p.key}>{p.label}</option>)}
          </select>
        </div>
        <div className="field">
          <label htmlFor="m-role">Droits</label>
          <select id="m-role" className="select" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as Role })}>
            <option value="membre">Membre</option>
            <option value="head">Head (peut valider et gérer l’équipe)</option>
          </select>
        </div>
      </div>
      {add.error && <p className="notice bad" role="alert">{(add.error as ApiError).message}</p>}
      <button type="submit" className="btn primary" style={{ alignSelf: "flex-start" }} disabled={add.isPending}>Ajouter</button>
    </form>
  );
}

function MemberRow({ member, me }: { member: Member; me: Member }) {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState(member.title);
  const update = useMutation({
    mutationFn: (input: { role?: Role; active?: boolean; pole?: Pole; title?: string }) => api.updateMember(member.id, input),
    onSuccess: (m) => {
      queryClient.invalidateQueries({ queryKey: ["membres"] });
      if (m.id === me.id) queryClient.setQueryData(["me"], m);
    },
  });
  const isMe = member.id === me.id;
  const canEdit = me.role === "head" && member.kind === "humain" && !isMe;
  const canMovePole = isMe || (me.role === "head" && member.active);

  return (
    <li style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "8px 14px", padding: "14px 0", borderTop: "1px solid var(--track)" }}>
      <Avatar member={member} />
      <span style={{ flex: "1 1 220px", minWidth: 0, display: "flex", flexDirection: "column" }}>
        <span style={{ fontWeight: 600 }}>
          {member.name}
          {!member.active && <span className="soft" style={{ fontWeight: 400 }}> · n’a plus accès</span>}
        </span>
        <span className="soft small">
          {member.kind === "agent" ? "Agent" : member.email} {member.title ? `· ${member.title}` : ""}
        </span>
      </span>
      {isMe && (
        <span style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <label className="visually-hidden" htmlFor="my-title">Ton rôle dans l’équipe</label>
          <input id="my-title" className="input" style={{ width: 150, minHeight: 36 }} placeholder="Ton rôle (CEO…)"
            value={title} onChange={(e) => setTitle(e.target.value)} onBlur={() => title !== member.title && update.mutate({ title })} />
        </span>
      )}
      {canMovePole ? (
        <PoleSelect id={`pole-${member.id}`} value={member.pole} disabled={update.isPending}
          label={`Pôle de ${member.name}`} onChange={(pole) => update.mutate({ pole })} />
      ) : (
        <PoleChip pole={member.pole} />
      )}
      {member.kind === "agent" ? (
        <span className="chip neutral">{member.status_label}</span>
      ) : canEdit ? (
        <span style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <label className="visually-hidden" htmlFor={`role-${member.id}`}>Droits de {member.name}</label>
          <select id={`role-${member.id}`} className="select" style={{ width: "auto", minHeight: 36 }}
            value={member.role} disabled={update.isPending}
            onChange={(e) => update.mutate({ role: e.target.value as Role })}>
            <option value="membre">Membre</option>
            <option value="head">Head</option>
          </select>
          <button type="button" className="btn small" disabled={update.isPending}
            onClick={() => update.mutate({ active: !member.active })}>
            {member.active ? "Retirer l’accès" : "Rendre l’accès"}
          </button>
        </span>
      ) : (
        <span className={member.role === "head" ? "chip brand" : "chip neutral"}>{member.role === "head" ? "Head" : "Membre"}</span>
      )}
    </li>
  );
}

export function Reglages({ me }: { me: Member }) {
  usePresence({ piece: "entree", label: "règle la maison" });
  const members = useQuery({ queryKey: ["membres"], queryFn: api.members });
  const config = useQuery({ queryKey: ["auth-config"], queryFn: api.authConfig });
  const kpis = useQuery({ queryKey: ["kpis"], queryFn: api.kpis });
  const retoursEtat = useQuery({ queryKey: ["retours-etat"], queryFn: api.retoursEtat });
  const queryClient = useQueryClient();
  const sync = useMutation({
    mutationFn: api.syncTestflight,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["retours-etat"] }),
  });

  return (
    <div className="page">
      <header style={{ display: "flex", flexDirection: "column", gap: 10, paddingTop: 8 }}>
        <span className="eyebrow">L’entrée</span>
        <h1 className="display">Réglages</h1>
        <p className="soft" style={{ fontSize: 16 }}>L’équipe de la maison, humains et agents, et l’état des branchements.</p>
      </header>

      <section className="card" aria-labelledby="branchements" style={{ gap: 10 }}>
        <h2 id="branchements" style={{ fontSize: 18, fontWeight: 700 }}>Branchements</h2>
        <p style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <span className={config.data?.email_login ? "chip good" : "chip wait"}>
            {config.data?.email_login ? "Branchée" : "À brancher"}
          </span>
          Connexion par lien envoyé par email
          {config.data?.email_login && config.data.dev_login && <span className="soft small">· sur ce PC, le lien s’affiche dans le journal du serveur</span>}
        </p>
        <p style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <span className={config.data?.google_client_id ? "chip good" : "chip neutral"}>
            {config.data?.google_client_id ? "Branchée" : "Facultative"}
          </span>
          Connexion Google
        </p>
        <p style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <span className={kpis.data?.available ? "chip good" : "chip wait"}>
            {kpis.data?.available ? "Branchée" : "À brancher"}
          </span>
          Chiffres de l’app Nyuman
        </p>
        <p style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <span className={retoursEtat.data?.testflight_branche ? "chip good" : "chip neutral"}>
            {retoursEtat.data?.testflight_branche ? "Branché" : "Pas encore utile"}
          </span>
          Import des retours TestFlight
          <span className="soft small">
            {retoursEtat.data?.testflight_branche
              ? retoursEtat.data.derniere_synchro
                ? `· dernier import ${formatAgo(retoursEtat.data.derniere_synchro)}`
                : "· toutes les 15 minutes"
              : "· pour les testeurs externes ; en interne, utilisez « Signaler un retour »"}
          </span>
          {retoursEtat.data?.testflight_branche && (
            <button type="button" className="btn small" disabled={sync.isPending} onClick={() => sync.mutate()}>Importer maintenant</button>
          )}
        </p>
        {sync.data && <p className="soft small">{sync.data.nouveaux} nouveau(x) retour(s) importé(s).</p>}
        {(sync.error || retoursEtat.data?.derniere_erreur) && (
          <p className="notice bad">{sync.error ? (sync.error as ApiError).message : retoursEtat.data?.derniere_erreur}</p>
        )}
        <p className="soft small">
          Les clés se règlent dans les variables d’environnement du serveur, par l’équipe elle-même. Elles ne passent
          jamais par cette page.
        </p>
      </section>

      {me.role === "head" && <AddMember />}
      {me.role === "head" && <ImportTableau />}

      <section className="card" aria-labelledby="equipe" style={{ gap: 4 }}>
        <h2 id="equipe" style={{ fontSize: 18, fontWeight: 700, marginBottom: 6 }}>L’équipe</h2>
        <ul className="list-plain">
          {(members.data ?? []).map((m) => (
            <MemberRow key={m.id} member={m} me={me} />
          ))}
        </ul>
      </section>
    </div>
  );
}
