export interface HealthStatus {
  status: string;
  llm_ready: boolean;
  llm_configured: boolean;
  agents_installed: boolean;
  agents_error: string;
  provider: string;
  model: string;
  base_url: string | null;
}

export interface GameStatus {
  game_id: string;
  status: string;
  event_count: number;
  winner?: string;
  error?: string;
}

const API_BASE = "";

export async function fetchHealth(): Promise<HealthStatus> {
  const resp = await fetch(`${API_BASE}/health`);
  if (!resp.ok) throw new Error("API unavailable");
  return resp.json();
}

export async function createGame(seed: number): Promise<string> {
  const resp = await fetch(`${API_BASE}/games`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seed }),
  });
  if (!resp.ok) {
    let detail = await resp.text();
    try {
      const j = JSON.parse(detail) as { detail?: string };
      detail = j.detail ?? detail;
    } catch {
      /* keep raw */
    }
    throw new Error(detail || "Failed to create game");
  }
  const data = (await resp.json()) as { game_id: string };
  return data.game_id;
}

export function wsUrl(gameId: string, view: "public" | "god"): string {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;
  return `${proto}//${host}/ws/games/${gameId}?view=${view}`;
}

export async function fetchGameStatus(gameId: string): Promise<GameStatus> {
  const resp = await fetch(`${API_BASE}/games/${gameId}`);
  if (!resp.ok) throw new Error("Game not found");
  return resp.json();
}
