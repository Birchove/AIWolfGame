import { useEffect, useState } from "react";
import { fetchGameStatus, type GameStatus } from "../api/client";

export function useGameStatus(gameId: string | null, pollMs = 2000) {
  const [status, setStatus] = useState<GameStatus | null>(null);

  useEffect(() => {
    if (!gameId) {
      setStatus(null);
      return;
    }

    let cancelled = false;

    async function poll() {
      try {
        const s = await fetchGameStatus(gameId!);
        if (!cancelled) setStatus(s);
      } catch {
        if (!cancelled) setStatus(null);
      }
    }

    poll();
    const id = setInterval(poll, pollMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [gameId, pollMs]);

  return status;
}
