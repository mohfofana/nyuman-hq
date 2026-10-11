import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, type RapportImport } from "../api";

function Rapport({ rapport }: { rapport: RapportImport }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <table className="mini-table">
        <thead>
          <tr><th scope="col">Ce qui sera repris</th><th scope="col">Nouveau</th><th scope="col">Déjà dans HQ</th></tr>
        </thead>
        <tbody>
          {rapport.lignes.map((l) => (
            <tr key={l.contenu}><td>{l.contenu}</td><td className="num">{l.nouveaux}</td><td className="num soft">{l.deja_la}</td></tr>
          ))}
        </tbody>
      </table>
      <details>
        <summary className="small" style={{ cursor: "pointer" }}>Ce que devient chaque onglet</summary>
        <ul className="list-plain small" style={{ gap: 4, paddingTop: 6 }}>
          {Object.entries(rapport.onglets).map(([nom, role]) => <li key={nom}><strong>{nom}</strong> → {role}</li>)}
        </ul>
      </details>
      {rapport.avertissements.length > 0 && (
        <div className="notice small">
          <strong>À vérifier :</strong>
          <ul style={{ margin: "6px 0 0", paddingLeft: 18 }}>
            {rapport.avertissements.map((a) => <li key={a}>{a}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}

/** Reprise du tableau Google de pré-lancement : un aperçu d'abord, puis l'import sur confirmation. */
export function ImportTableau() {
  const queryClient = useQueryClient();
  const [fichier, setFichier] = useState<File | null>(null);
  const apercu = useMutation({ mutationFn: (f: File) => api.importTableau(f, true) });
  const importer = useMutation({
    mutationFn: () => api.importTableau(fichier!, false),
    onSuccess: () => {
      for (const key of ["taches", "decisions", "pros", "documents", "evenements"]) queryClient.invalidateQueries({ queryKey: [key] });
    },
  });
  const nouveaux = apercu.data?.lignes.reduce((n, l) => n + l.nouveaux, 0) ?? 0;
  const error = apercu.error || importer.error;

  return (
    <section className="card" aria-labelledby="reprise" style={{ gap: 12 }}>
      <h2 id="reprise" style={{ fontSize: 18, fontWeight: 700 }}>Reprendre le tableau Google</h2>
      <p className="soft small" style={{ maxWidth: "70ch" }}>
        Dans Google Sheets : <strong>Fichier → Télécharger → Microsoft Excel (.xlsx)</strong>, puis choisis le fichier ici.
        Les tâches et leurs étapes vont dans la salle de projet, les décisions au conseil, les prestataires dans le panel des pros,
        et les autres onglets (modèle financier…) dans la bibliothèque. Rien n’est écrit avant ta confirmation, et relancer ne crée pas de doublon.
      </p>
      <label className="visually-hidden" htmlFor="tableau-fichier">Fichier du tableau (.xlsx)</label>
      <input
        id="tableau-fichier"
        type="file"
        accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        onChange={(e) => {
          const f = e.target.files?.[0] ?? null;
          setFichier(f);
          importer.reset();
          if (f) apercu.mutate(f);
          else apercu.reset();
        }}
      />
      {apercu.isPending && <p className="soft small" role="status">Lecture du tableau…</p>}
      {importer.data ? (
        <>
          <p className="notice good" role="status">C’est repris. Le tableau Google peut maintenant être gardé en lecture seule.</p>
          <Rapport rapport={importer.data} />
        </>
      ) : (
        apercu.data && (
          <>
            <Rapport rapport={apercu.data} />
            <button type="button" className="btn brand" style={{ alignSelf: "flex-start" }} disabled={!nouveaux || importer.isPending}
              onClick={() => importer.mutate()}>
              {nouveaux ? `Reprendre ${nouveaux} élément${nouveaux > 1 ? "s" : ""} dans HQ` : "Tout est déjà dans HQ"}
            </button>
          </>
        )
      )}
      {error && <p className="notice bad" role="alert">{(error as ApiError).message}</p>}
    </section>
  );
}
