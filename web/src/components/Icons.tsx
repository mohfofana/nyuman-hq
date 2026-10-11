import type { ReactNode } from "react";

function Icon({ children, size = 18 }: { children: ReactNode; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

export const IconSalon = () => (
  <Icon>
    <path d="M3 10.5 12 3l9 7.5V21h-6v-6H9v6H3z" />
  </Icon>
);

export const IconBureau = () => (
  <Icon>
    <rect x="5" y="3" width="14" height="18" rx="1.5" />
    <circle cx="15" cy="12" r="1" />
  </Icon>
);

export const IconBibliotheque = () => (
  <Icon>
    <path d="M4 5h5a3 3 0 0 1 3 3v12a2 2 0 0 0-2-2H4z" />
    <path d="M20 5h-5a3 3 0 0 0-3 3v12a2 2 0 0 1 2-2h6z" />
  </Icon>
);

export const IconProjet = () => (
  <Icon>
    <rect x="3" y="4" width="18" height="16" rx="2" />
    <path d="M9 4v16M15 4v16" />
  </Icon>
);

export const IconConseil = () => (
  <Icon>
    <circle cx="12" cy="12" r="4.5" />
    <circle cx="12" cy="3.5" r="1.5" />
    <circle cx="12" cy="20.5" r="1.5" />
    <circle cx="3.5" cy="12" r="1.5" />
    <circle cx="20.5" cy="12" r="1.5" />
  </Icon>
);

export const IconPros = () => (
  <Icon>
    <circle cx="9" cy="8" r="3.2" />
    <path d="M3.5 19.5c.6-3.2 2.8-5 5.5-5s4.9 1.8 5.5 5" />
    <circle cx="17" cy="9" r="2.4" />
    <path d="M15.8 14.4c2.3.2 4 1.8 4.6 4.6" />
  </Icon>
);

export const IconReglages = () => (
  <Icon>
    <path d="M4 7h10M18 7h2M4 17h4M12 17h8" />
    <circle cx="16" cy="7" r="2" />
    <circle cx="10" cy="17" r="2" />
  </Icon>
);

export const IconSearch = () => (
  <Icon>
    <circle cx="11" cy="11" r="6.5" />
    <path d="m16 16 4.5 4.5" />
  </Icon>
);

export const IconPlus = () => (
  <Icon>
    <path d="M12 5v14M5 12h14" />
  </Icon>
);

export const IconArrow = () => (
  <Icon size={16}>
    <path d="M5 12h14M13 6l6 6-6 6" />
  </Icon>
);

export const IconLogout = () => (
  <Icon>
    <path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3" />
    <path d="M10 8l-4 4 4 4M6 12h10" />
  </Icon>
);

export const IconClose = () => (
  <Icon size={16}>
    <path d="M6 6l12 12M18 6 6 18" />
  </Icon>
);

/** L'étincelle des agents : petite, sur leur avatar, pour qu'on sache toujours à qui l'on parle. */
export const IconSpark = ({ size = 10 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
    <path d="M12 2l2.2 6.6L21 11l-6.8 2.4L12 20l-2.2-6.6L3 11l6.8-2.4z" />
  </svg>
);
