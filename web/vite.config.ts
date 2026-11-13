import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5180,
    // Lien temporaire de test (tunnel Cloudflare). À retirer une fois HQ vraiment en ligne.
    allowedHosts: [".trycloudflare.com"],
    proxy: {
      "/api": "http://localhost:8030",
      "/ws": { target: "ws://localhost:8030", ws: true },
    },
  },
});
