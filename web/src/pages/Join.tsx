import { useEffect, useState } from "react";
import { Check, Clock, UserRound } from "lucide-react";
import { joinApi, type JoinMe } from "../lib/api";

/** Première arrivée : Google a confirmé l'adresse, la personne dit qui elle est, un responsable confirme. */
export function Join() {
  const [data, setData] = useState<JoinMe | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  useEffect(() => {
    joinApi.me().then(setData).catch(() => setError("expiré"));
  }, []);

  if (error === "expiré") {
    return (
      <Center title="Votre connexion a expiré">
        <p className="text-sm text-ink-soft">Recommencez : cela ne prend que quelques secondes.</p>
        <a href="/api/auth/google/start" className="mt-5 inline-block rounded-xl bg-accent px-5 py-2.5 text-sm font-semibold text-white hover:bg-accent-hover">
          Se connecter avec Google
        </a>
      </Center>
    );
  }
  if (!data) return null;

  const waiting = data.candidates.find((c) => c.id === data.waiting);
  if (data.waiting) {
    return (
      <Center title="C'est noté, on vous attend">
        <p className="text-sm text-ink-soft">
          Vous vous êtes présenté comme <b className="text-ink">{waiting?.name ?? "membre de l'équipe"}</b>, avec l'adresse{" "}
          <b className="text-ink">{data.email}</b>.
        </p>
        <div className="mt-5 flex items-start gap-3 rounded-2xl bg-surface p-4 text-left text-sm">
          <Clock size={18} className="mt-0.5 shrink-0 text-accent" />
          <span>Un responsable va confirmer que c'est bien vous. Revenez sur cette page une fois que c'est fait : vous entrerez directement.</span>
        </div>
      </Center>
    );
  }

  if (data.candidates.length === 0) {
    return (
      <Center title="Votre adresse n'est pas encore connue">
        <p className="text-sm text-ink-soft">
          <b className="text-ink">{data.email}</b> ne correspond à personne, et toutes les fiches ont déjà leur adresse.
          Demandez à un responsable de vous ajouter.
        </p>
      </Center>
    );
  }

  const choose = async (id: string) => {
    setBusy(id);
    try { setData(await joinApi.join(id)); }
    catch { setError("refus"); }
    finally { setBusy(""); }
  };

  return (
    <Center title="Qui êtes-vous ?">
      <p className="text-sm text-ink-soft">
        Vous arrivez avec <b className="text-ink">{data.email}</b>
        {data.name_seen && <> ({data.name_seen})</>}. Choisissez votre nom : un responsable confirmera.
      </p>
      <div className="mt-5 space-y-2">
        {data.candidates.map((c) => (
          <button key={c.id} onClick={() => choose(c.id)} disabled={!!busy}
            className="group flex w-full items-center gap-3 rounded-2xl border border-line bg-white px-4 py-3 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-accent hover:shadow-md disabled:opacity-50">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent-soft text-accent"><UserRound size={18} /></span>
            <span className="min-w-0 flex-1">
              <span className="block font-medium">{c.name}</span>
              <span className="block truncate text-xs text-ink-soft">{c.title}</span>
            </span>
            {busy === c.id && <Check size={18} className="text-accent" />}
          </button>
        ))}
      </div>
      {error === "refus" && <p className="mt-3 text-sm text-busy">Impossible pour l'instant. Réessayez, ou demandez à un responsable.</p>}
      <p className="mt-4 text-xs text-ink-muted">Vous ne voyez pas votre nom ? Demandez à un responsable de vous ajouter à l'équipe.</p>
    </Center>
  );
}

function Center({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="flex min-h-full items-center justify-center bg-surface px-4 py-10">
      <div className="w-full max-w-md">
        <img src="/logo-wordmark.png" alt="Nyuman" className="mb-6 h-5" />
        <h1 className="text-2xl font-semibold">{title}</h1>
        <div className="mt-2">{children}</div>
      </div>
    </div>
  );
}
