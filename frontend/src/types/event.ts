import type { PlayerDossier } from "./dossier";

export type ViewMode = "public" | "god";

export interface GameEvent {
  seq: number;
  timestamp: string;
  game_id: string;
  visibility: string;
  type: string;
  phase: string | null;
  round: number | null;
  player_id: number | null;
  payload: Record<string, unknown>;
}

export interface VoteResult {
  eliminated: number | null;
  pk_candidates: number[];
  tied: boolean;
}

export interface SpectatorState {
  roles: Record<number, string> | null;
  alive: Set<number>;
  sheriffId: number | null;
  sheriffCandidates: Set<number>;
  sheriffWithdrawn: Set<number>;
  sheriffElectionStep: string | null;
  phase: string | null;
  round: number | null;
  speeches: Record<number, string>;
  demeanorEmojis: Record<number, string[]>;
  lastSpeakerId: number | null;
  votes: Record<number, number | null>;
  lastVoteResult: VoteResult | null;
  idiotRevealed: Set<number>;
  status: "waiting" | "running" | "complete" | "failed";
  winner: string | null;
  winReason: string | null;
  dossier: PlayerDossier | null;
  events: GameEvent[];
}

export const ALL_PLAYER_IDS = Array.from({ length: 12 }, (_, i) => i + 1);

export function initialSpectatorState(): SpectatorState {
  return {
    roles: null,
    alive: new Set(ALL_PLAYER_IDS),
    sheriffId: null,
    sheriffCandidates: new Set(),
    sheriffWithdrawn: new Set(),
    sheriffElectionStep: null,
    phase: null,
    round: null,
    speeches: {},
    demeanorEmojis: {},
    lastSpeakerId: null,
    votes: {},
    lastVoteResult: null,
    idiotRevealed: new Set(),
    status: "waiting",
    winner: null,
    winReason: null,
    dossier: null,
    events: [],
  };
}
