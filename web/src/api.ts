import { useCallback, useEffect, useState } from "react";
import { accessToken } from "./auth";

export async function api<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: {
      Authorization: `Bearer ${await accessToken()}`,
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    // The API explains refusals in `detail` ("only the bureau holding this case can act on it").
    const detail = await response.json().then(
      (b: { detail?: unknown }) => (typeof b.detail === "string" ? b.detail : null),
      () => null,
    );
    throw new Error(detail ? `${detail[0].toUpperCase()}${detail.slice(1)}.` : `The request failed (${response.status}).`);
  }
  return (await response.json()) as T;
}

/** Load data for a screen. `reload` fetches again; a newer request wins over an older one. */
export function useLoad<T>(path: string) {
  const [state, setState] = useState<{ data?: T; error?: string }>({});
  const [version, setVersion] = useState(0);
  useEffect(() => {
    let current = true;
    api<T>(path).then(
      (data) => current && setState({ data }),
      (e: unknown) => current && setState({ error: e instanceof Error ? e.message : "The request failed." }),
    );
    return () => {
      current = false;
    };
  }, [path, version]);
  const reload = useCallback(() => setVersion((v) => v + 1), []);
  return { ...state, reload };
}
