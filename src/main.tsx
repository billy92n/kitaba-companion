import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { VisualReferenceDock } from "./components/VisualReferenceDock";
import "./player-knowledge-hardening.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode><><App /><VisualReferenceDock /></></StrictMode>
);
