import { useEffect, useState } from "react";
import { fetchHealth, type HealthStatus } from "../api/client";

export function useHealth() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchHealth()
      .then((h) => {
        if (!cancelled) {
          setHealth(h);
          setError(null);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError("无法连接后端 — 请先运行 python -m aiwerewolf.api.server");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { health, error };
}
