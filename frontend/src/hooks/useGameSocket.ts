import { useEffect, useRef, useState } from "react";
import type { GameEvent, ViewMode } from "../types/event";
import { wsUrl } from "../api/client";

export function useGameSocket(
  gameId: string | null,
  view: ViewMode,
  onEvent: (event: GameEvent) => void,
) {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    if (!gameId) {
      setConnected(false);
      return;
    }

    setError(null);
    const url = wsUrl(gameId, view);
    const ws = new WebSocket(url);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setError("WebSocket connection failed");
    ws.onmessage = (msg) => {
      try {
        const event = JSON.parse(msg.data as string) as GameEvent;
        onEventRef.current(event);
      } catch {
        setError("Invalid event JSON");
      }
    };

    return () => ws.close();
  }, [gameId, view]);

  return { connected, error };
}
