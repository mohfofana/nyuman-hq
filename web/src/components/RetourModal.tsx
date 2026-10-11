import { useEffect, useRef, useState, type ClipboardEvent, type DragEvent, type FormEvent } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { motion } from "motion/react";
import { api, ApiError, type RetourKind } from "../api";
import { IconClose } from "./Icons";

const MAX_FILES = 6;
const MAX_BYTES = 8 * 1024 * 1024;
const DETAILS_KEY = "hq-retour-appareil";

const KINDS: { key: RetourKind; label: string; hint: string }[] = [
  { key: "bug", label: "Bug", hint: "quelque chose ne marche pas" },
  { key: "idee", label: "Idée", hint: "ce serait mieux si…" },
  { key: "remarque", label: "Remarque", hint: "un détail, un ressenti" },
];

interface Details {
  device_model: string;
  os_version: string;
  build_version: string;
}

function loadDetails(): Details {
  try {
    const raw = localStorage.getItem(DETAILS_KEY);
    if (raw) return { device_model: "", os_version: "", build_version: "", ...JSON.parse(raw) };
  } catch {
    /* stockage indisponible : on repart de zéro */
  }
  return { device_model: "", os_version: "", build_version: "" };
}

function saveDetails(d: Details) {
  try {
    localStorage.setItem(DETAILS_KEY, JSON.stringify(d));
  } catch {
    /* rien de grave */
  }
}

/** « Signaler un retour » : remplace les captures envoyées une à une sur WhatsApp. */
export function RetourModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [kind, setKind] = useState<RetourKind>("bug");
  const [espace, setEspace] = useState<"cliente" | "pro" | "">("");
  const [comment, setComment] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [details, setDetails] = useState<Details>(loadDetails);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const urls = files.map((f) => URL.createObjectURL(f));
    setPreviews(urls);
    return () => urls.forEach((u) => URL.revokeObjectURL(u));
  }, [files]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  function addFiles(list: FileList | File[]) {
    const images = Array.from(list).filter((f) => f.type.startsWith("image/"));
    if (images.some((f) => f.size > MAX_BYTES)) setError("Une capture dépasse 8 Mo.");
    const ok = images.filter((f) => f.size <= MAX_BYTES);
    setFiles((prev) => [...prev, ...ok].slice(0, MAX_FILES));
  }

  function onPaste(e: ClipboardEvent) {
    const pasted = Array.from(e.clipboardData.items)
      .filter((i) => i.type.startsWith("image/"))
      .map((i) => i.getAsFile())
      .filter((f): f is File => f !== null);
    if (pasted.length) {
      e.preventDefault();
      addFiles(pasted);
    }
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    addFiles(e.dataTransfer.files);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!comment.trim() && files.length === 0) {
      setError("Écris ce qui se passe ou ajoute au moins une capture.");
      return;
    }
    setError(null);
    setSending(true);
    const form = new FormData();
    form.append("kind", kind);
    form.append("comment", comment);
    form.append("espace", espace);
    form.append("device_model", details.device_model);
    form.append("os_version", details.os_version);
    form.append("build_version", details.build_version);
    files.forEach((f) => form.append("captures", f, f.name || "capture.png"));
    try {
      await api.createRetour(form);
      saveDetails(details);
      queryClient.invalidateQueries({ queryKey: ["retours"] });
      queryClient.invalidateQueries({ queryKey: ["retours-etat"] });
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "L’envoi a échoué.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <motion.form
        className="card modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="retour-titre"
        onSubmit={submit}
        onPaste={onPaste}
        initial={{ opacity: 0, y: 24, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ type: "spring", stiffness: 380, damping: 32 }}
      >
        <div className="card-head">
          <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <h2 id="retour-titre" className="title">Signaler un retour sur l’app</h2>
            <span className="soft small">Toute l’équipe le voit tout de suite, et il peut devenir une tâche en un clic.</span>
          </div>
          <button type="button" className="icon-btn light" onClick={onClose} aria-label="Fermer"><IconClose /></button>
        </div>

        <div className="kind-pick" role="group" aria-label="Type de retour">
          {KINDS.map((k) => (
            <button key={k.key} type="button" aria-pressed={kind === k.key} onClick={() => setKind(k.key)} className={`kind-btn ${k.key}`}>
              <b>{k.label}</b>
              <span>{k.hint}</span>
            </button>
          ))}
        </div>

        <div className="field">
          <span style={{ fontSize: 13, fontWeight: 650 }} id="espace-label">Côté de l’app</span>
          <div className="segmented" role="group" aria-labelledby="espace-label" style={{ alignSelf: "flex-start" }}>
            {([["cliente", "Clientes"], ["pro", "Pros"], ["", "Les deux"]] as const).map(([v, l]) => (
              <button key={v} type="button" aria-pressed={espace === v} onClick={() => setEspace(v)}>{l}</button>
            ))}
          </div>
        </div>

        <div className="field">
          <label htmlFor="retour-comment">Ce qui se passe</label>
          <textarea
            id="retour-comment"
            className="textarea"
            style={{ minHeight: 110, fontFamily: "var(--font)", fontSize: 15 }}
            autoFocus
            placeholder="Ce que tu faisais, ce qui s’est passé, ce que tu attendais…"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />
        </div>

        <div
          className={dragging ? "dropzone over" : "dropzone"}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          {files.length > 0 && (
            <div className="thumbs">
              {previews.map((src, i) => (
                <div key={src} className="thumb">
                  <img src={src} alt={`Capture ${i + 1}`} />
                  <button type="button" aria-label={`Retirer la capture ${i + 1}`} onClick={() => setFiles(files.filter((_, j) => j !== i))}>
                    <IconClose />
                  </button>
                </div>
              ))}
            </div>
          )}
          {files.length < MAX_FILES && (
            <p className="soft small">
              Glisse tes captures ici, colle-les (Ctrl+V) ou{" "}
              <button type="button" className="link-btn" onClick={() => inputRef.current?.click()}>choisis-les</button>
              {" "}· {MAX_FILES} au maximum
            </p>
          )}
          <input ref={inputRef} type="file" accept="image/*" multiple hidden onChange={(e) => e.target.files && addFiles(e.target.files)} />
        </div>

        <details className="details">
          <summary>Appareil et version de l’app <span className="soft">(gardés pour la prochaine fois)</span></summary>
          <div className="grid-cards" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 140px), 1fr))", marginTop: 10 }}>
            <div className="field">
              <label htmlFor="r-device">Téléphone</label>
              <input id="r-device" className="input" placeholder="iPhone 13" value={details.device_model} onChange={(e) => setDetails({ ...details, device_model: e.target.value })} />
            </div>
            <div className="field">
              <label htmlFor="r-os">iOS</label>
              <input id="r-os" className="input" placeholder="18.1" value={details.os_version} onChange={(e) => setDetails({ ...details, os_version: e.target.value })} />
            </div>
            <div className="field">
              <label htmlFor="r-build">Build</label>
              <input id="r-build" className="input" placeholder="14" value={details.build_version} onChange={(e) => setDetails({ ...details, build_version: e.target.value })} />
            </div>
          </div>
        </details>

        {error && <p className="notice bad" role="alert">{error}</p>}
        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", flexWrap: "wrap" }}>
          <button type="button" className="btn" onClick={onClose}>Annuler</button>
          <button type="submit" className="btn primary" disabled={sending}>{sending ? "Envoi…" : "Envoyer à l’équipe"}</button>
        </div>
      </motion.form>
    </div>
  );
}
