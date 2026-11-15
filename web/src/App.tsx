import { useEffect, useState } from "react";

type Ready = { status: string; database?: string };

// Platform shell only: shows whether the API and database are reachable.
// Feature screens are added under src/features/<feature>/.
export function App() {
  const [ready, setReady] = useState<Ready | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/health/ready")
      .then(async (r) => setReady((await r.json()) as Ready))
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "request failed"));
  }, []);

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", margin: "3rem auto", maxWidth: 640 }}>
      <h1>SETHU</h1>
      <p>AICTE cross-bureau complaint monitoring</p>
      <dl>
        <dt>API</dt>
        <dd>{error ? `unreachable (${error})` : ready ? ready.status : "checking..."}</dd>
        <dt>Database</dt>
        <dd>{ready?.database ?? "-"}</dd>
      </dl>
    </main>
  );
}
