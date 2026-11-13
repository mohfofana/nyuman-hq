import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { SessionProvider } from "./lib/session";
import { LiveProvider } from "./lib/live";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <SessionProvider><LiveProvider><App /></LiveProvider></SessionProvider>
    </BrowserRouter>
  </StrictMode>,
);
