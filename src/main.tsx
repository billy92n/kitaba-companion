import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { VisualReferenceDock } from "./components/VisualReferenceDock";
import { EncyclopediaDock } from "./components/EncyclopediaDock";
import "./player-knowledge-hardening.css";
import "./mvp-theme-hardening.css";
import "./image-fit-hardening.css";
import "./encyclopedia.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode><><App /><VisualReferenceDock /><EncyclopediaDock /></></StrictMode>
);