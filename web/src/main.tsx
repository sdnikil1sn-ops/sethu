import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { start } from "./auth";
import "./app.css";

const root = createRoot(document.getElementById("root")!);

// Nothing is rendered until the user is signed in.
start().then(
  () =>
    root.render(
      <StrictMode>
        <App />
      </StrictMode>,
    ),
  (e: unknown) =>
    root.render(
      <main>
        <h1>SETHU</h1>
        <p role="alert">{e instanceof Error ? e.message : "Sign-in failed."}</p>
        <a href="/">Try again</a>
      </main>,
    ),
);
