import { useState, type ReactNode } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "motion/react";
import { api, type Member, type Piece } from "../api";
import { formatNumber } from "../format";
import { placeOf } from "../house";
import { useLive } from "../live";
import { Avatar } from "./Avatar";
import { RetourModal } from "./RetourModal";
import {
  IconBibliotheque,
  IconBureau,
  IconClose,
  IconConseil,
  IconLogout,
  IconPros,
  IconProjet,
  IconReglages,
  IconSalon,
} from "./Icons";

/** Les visages des membres présents dans une pièce, à côté de son nom dans le menu. */
function Faces({ members }: { members: Member[] }) {
  if (members.length === 0) return null;
  return (
    <span className="nav-faces" aria-label={`${members.length} ici`}>
      {members.slice(0, 3).map((m) => (
        <Avatar key={m.id} member={m} size={22} onNight />
      ))}
    </span>
  );
}

function NavItem({ to, icon, label, here, badge, badgeLabel = "à trier" }: {
  to: string;
  icon: ReactNode;
  label: string;
  here: Member[];
  badge?: number;
  badgeLabel?: string;
}) {
  return (
    <li>
      <NavLink to={to} end={to === "/"} className={({ isActive }) => (isActive ? "active" : undefined)}>
        {icon}
        {label}
        <Faces members={here} />
        {badge ? <span className="nav-badge" aria-label={`${badge} ${badgeLabel}`}>{badge}</span> : null}
      </NavLink>
    </li>
  );
}

function TopBar() {
  const { connected } = useLive();
  const objective = useQuery({ queryKey: ["objectif"], queryFn: () => api.objective(), refetchInterval: 60_000 });
  const [signaler, setSignaler] = useState(false);
  const o = objective.data;
  return (
    <div className="topbar">
      {signaler && <RetourModal onClose={() => setSignaler(false)} />}
      {o ? (
        <Link to="/" className="topbar-goal" aria-label={`Objectif du trimestre : ${o.title}`}>
          <span className="chip brand" style={{ padding: "3px 10px" }}>{o.quarter}</span>
          <span style={{ fontSize: 13.5, fontWeight: 600 }}>
            {o.current !== null ? `${formatNumber(o.current)} / ${formatNumber(o.target)}` : `Cible ${formatNumber(o.target)}`}
          </span>
          <span className="mini-bar" aria-hidden="true">
            <span style={{ width: `${Math.min(100, Math.round((o.progress ?? 0) * 100))}%` }} />
          </span>
        </Link>
      ) : (
        <span />
      )}
      <span style={{ display: "flex", alignItems: "center", gap: 14, marginLeft: "auto" }}>
        <button type="button" className="btn small" onClick={() => setSignaler(true)}>Signaler un retour</button>
        <span className="live-pill" role="status">
          <span className={connected ? "live-dot on" : "live-dot off"} aria-hidden="true" />
          {connected ? "En direct" : "Reconnexion…"}
        </span>
      </span>
    </div>
  );
}

function Toasts() {
  const { toasts, dismiss } = useLive();
  const members = useQuery({ queryKey: ["membres"], queryFn: api.members });
  const byId = new Map((members.data ?? []).map((m) => [m.id, m]));
  return (
    <div className="toasts" aria-live="polite">
      <AnimatePresence initial={false}>
        {toasts.map((t) => {
          const actor = byId.get(t.actorId);
          return (
            <motion.div
              key={t.id}
              className="toast"
              initial={{ opacity: 0, y: 18, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, x: 40 }}
              transition={{ type: "spring", stiffness: 380, damping: 30 }}
            >
              {actor && <Avatar member={actor} size={30} onNight />}
              <p>
                <b>{actor?.name ?? "Quelqu’un"}</b> {t.text}{" "}
                {t.link && <Link to={t.link} onClick={() => dismiss(t.id)}>Voir</Link>}
              </p>
              <button type="button" onClick={() => dismiss(t.id)} aria-label="Fermer la notification">
                <IconClose />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}

export function Layout({ me }: { me: Member }) {
  const queryClient = useQueryClient();
  const { presences } = useLive();
  const members = useQuery({ queryKey: ["membres"], queryFn: api.members, refetchInterval: 60_000 });
  const retoursEtat = useQuery({ queryKey: ["retours-etat"], queryFn: api.retoursEtat, refetchInterval: 120_000 });
  const decisions = useQuery({ queryKey: ["decisions"], queryFn: api.decisions });
  // Sur le menu : les sujets qui attendent les heads (sur la table, ou à revoir après 30 jours).
  const aTrancher = (decisions.data ?? []).filter((d) => d.statut === "nouveau" || d.a_revoir).length;

  const inPiece = (piece: Piece) =>
    (members.data ?? []).filter((m) => m.active && m.kind === "humain" && placeOf(m, presences[m.id]).piece === piece);

  async function logout() {
    await api.logout();
    queryClient.clear();
    window.location.assign("/");
  }

  return (
    <div className="shell">
      <nav className="rail" aria-label="Les pièces de la maison">
        <div className="brand">
          <span className="brand-name">nyuman</span>
          <span className="brand-tag">HQ</span>
        </div>

        <div className="rail-navs">
          <div className="rail-section">
            <span className="rail-label">La maison</span>
            <ul className="nav">
              <NavItem to="/" icon={<IconSalon />} label="Le salon" here={inPiece("salon")} />
              <NavItem to="/bureaux" icon={<IconBureau />} label="Les bureaux" here={inPiece("bureaux")} />
              <NavItem to="/bibliotheque" icon={<IconBibliotheque />} label="La bibliothèque" here={inPiece("bibliotheque")} />
              <NavItem to="/projet" icon={<IconProjet />} label="Salle de projet" here={inPiece("projet")} badge={retoursEtat.data?.nouveaux} />
              <NavItem to="/conseil" icon={<IconConseil />} label="Salle du conseil" here={inPiece("conseil")} badge={aTrancher || undefined} badgeLabel="à trancher ou à revoir" />
              <NavItem to="/pros" icon={<IconPros />} label="Le panel des pros" here={[]} />
            </ul>
          </div>

          <div className="rail-section">
            <span className="rail-label">L’équipe</span>
            <ul className="nav">
              <NavItem to="/reglages" icon={<IconReglages />} label="Réglages" here={inPiece("entree")} />
            </ul>
          </div>
        </div>

        <div className="rail-me">
          <Avatar member={me} size={36} onNight ring="#2f7a57" />
          <span className="rail-me-text" style={{ minWidth: 0, flex: 1, display: "flex", flexDirection: "column" }}>
            <span style={{ fontSize: 14, fontWeight: 650, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {me.name}
            </span>
            <span style={{ fontSize: 12, color: "var(--cream-2)" }}>{me.role === "head" ? "Head" : "Membre"}</span>
          </span>
          <button type="button" className="icon-btn" onClick={logout} aria-label="Sortir de la maison" title="Sortir">
            <IconLogout />
          </button>
        </div>
      </nav>

      <main className="content">
        <TopBar />
        <Outlet />
      </main>
      <Toasts />
    </div>
  );
}
