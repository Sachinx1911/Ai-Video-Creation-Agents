"use client";

import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";

import { ApiError } from "@/lib/api";

export interface ApiState<T> {
  data: T | undefined;
  error: ApiError | undefined;
  loading: boolean;
  reload: () => void;
}

/**
 * Fetch data from the API on mount (and when `deps` change), optionally polling.
 * Polling pauses while the tab is hidden.
 */
export function useApi<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = [],
  pollMs?: number,
): ApiState<T> {
  const [data, setData] = useState<T>();
  const [error, setError] = useState<ApiError>();
  const fetcherRef = useRef(fetcher);
  useLayoutEffect(() => {
    fetcherRef.current = fetcher;
  });
  const seq = useRef(0);

  const run = useCallback(async () => {
    const id = ++seq.current;
    try {
      const result = await fetcherRef.current();
      if (id === seq.current) {
        setData(result);
        setError(undefined);
      }
    } catch (e) {
      if (id === seq.current) setError(e instanceof ApiError ? e : new ApiError(0, String(e)));
    }
  }, []);

  useEffect(() => {
    void run();
    if (!pollMs) return;
    const t = setInterval(() => {
      if (document.visibilityState === "visible") void run();
    }, pollMs);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, pollMs, run]);

  // Stale-while-revalidate: previous data stays visible while new deps load.
  return { data, error, loading: data === undefined && error === undefined, reload: run };
}
