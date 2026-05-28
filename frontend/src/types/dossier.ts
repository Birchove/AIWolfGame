export interface PlayerTurn {
  player_id: number;
  role: string;
  phase: string;
  round: number;
  speech: string;
  demeanor: string;
  demeanor_emojis: string[];
  reasoning: string;
  action: Record<string, unknown>;
}

export interface PlayerDossierEntry {
  player_id: number;
  role: string;
  alive: boolean;
  is_sheriff: boolean;
  in_soul_state: boolean;
  speech_count: number;
  turns: PlayerTurn[];
}

export interface PlayerDossier {
  seed: number | null;
  winner: string | null;
  win_reason: string | null;
  round_count: number;
  players: PlayerDossierEntry[];
}
