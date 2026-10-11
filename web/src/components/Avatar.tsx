import type { MemberRef } from "../api";
import { avatarColors } from "../format";
import { IconSpark } from "./Icons";

// Humains : rond. Agents : carré arrondi avec une étincelle. Même taille, même place : ce sont des collègues.
export function Avatar({
  member,
  size = 32,
  ring,
  onNight = false,
}: {
  member: MemberRef;
  size?: number;
  ring?: string; // couleur de statut autour de l'avatar
  onNight?: boolean;
}) {
  const { bg, fg } = avatarColors(member.color);
  const isAgent = member.kind === "agent";
  const gap = onNight ? "var(--night)" : "var(--card)";
  return (
    <span
      aria-hidden="true"
      className="avatar"
      style={{
        width: size,
        height: size,
        background: bg,
        color: fg,
        fontSize: Math.max(11, Math.round(size * 0.36)),
        borderRadius: isAgent ? Math.round(size * 0.3) : 999,
        boxShadow: ring ? `0 0 0 2.5px ${gap}, 0 0 0 5px ${ring}` : undefined,
      }}
    >
      {member.initials}
      {isAgent && size >= 28 && (
        <span className="avatar-spark" style={{ boxShadow: `0 0 0 2px ${gap}` }}>
          <IconSpark size={9} />
        </span>
      )}
    </span>
  );
}
