import { useCallback, useReducer } from "react";
import type { GameEvent, SpectatorState } from "../types/event";
import type { PlayerDossier } from "../types/dossier";
import { initialSpectatorState } from "../types/event";

function applyEvent(state: SpectatorState, event: GameEvent): SpectatorState {
  const next: SpectatorState = {
    ...state,
    alive: new Set(state.alive),
    speeches: { ...state.speeches },
    demeanorEmojis: { ...state.demeanorEmojis },
    votes: { ...state.votes },
    idiotRevealed: new Set(state.idiotRevealed),
    sheriffCandidates: new Set(state.sheriffCandidates),
    sheriffWithdrawn: new Set(state.sheriffWithdrawn),
    speechOrder: [...state.speechOrder],
    events: [...state.events, event],
    phase: event.phase ?? state.phase,
    round: event.round ?? state.round,
    status: state.status === "waiting" ? "running" : state.status,
  };

  const p = event.payload;

  switch (event.type) {
    case "game_start": {
      const roles = p.roles as Record<string, string> | undefined;
      if (roles) {
        next.roles = Object.fromEntries(
          Object.entries(roles).map(([k, v]) => [Number(k), v]),
        );
      }
      break;
    }
    case "phase_change":
      next.phase = (p.phase as string) ?? next.phase;
      if (next.phase !== "day_speech") {
        next.speechOrder = [];
      }
      if (next.phase === "day_sheriff" && next.sheriffElectionStep == null) {
        next.sheriffElectionStep = "nominate";
        next.sheriffCandidates = new Set();
        next.sheriffWithdrawn = new Set();
      }
      break;
    case "agent_turn": {
      const pid = event.player_id ?? (p.player_id as number | undefined);
      if (pid != null && event.visibility === "public") {
        if (typeof p.speech === "string") next.speeches[pid] = p.speech;
        if (Array.isArray(p.demeanor_emojis)) {
          next.demeanorEmojis[pid] = p.demeanor_emojis as string[];
        }
        next.lastSpeakerId = pid;
      }
      break;
    }
    case "vote_cast": {
      const voter = p.voter_id as number;
      next.votes[voter] = (p.target_id as number | null) ?? null;
      break;
    }
    case "vote_result":
      next.lastVoteResult = {
        eliminated: (p.eliminated as number | null) ?? null,
        pk_candidates: (p.pk_candidates as number[]) ?? [],
        tied: Boolean(p.tied),
      };
      next.votes = {};
      break;
    case "death": {
      const pid = (p.player_id as number) ?? event.player_id;
      if (pid != null) next.alive.delete(pid);
      break;
    }
    case "sheriff_nominate": {
      const pid = (p.player_id as number) ?? event.player_id;
      if (pid == null) break;
      if (p.running) next.sheriffCandidates.add(pid);
      else {
        next.sheriffCandidates.delete(pid);
        next.sheriffWithdrawn.delete(pid);
      }
      break;
    }
    case "sheriff_nomination_complete": {
      const cands = (p.candidates as number[]) ?? [];
      next.sheriffCandidates = new Set(cands);
      next.sheriffElectionStep = "speech";
      break;
    }
    case "sheriff_withdraw": {
      const pid = (p.player_id as number) ?? event.player_id;
      if (pid != null) {
        next.sheriffCandidates.delete(pid);
        next.sheriffWithdrawn.add(pid);
      }
      break;
    }
    case "sheriff_speech_complete":
      next.sheriffElectionStep = "vote";
      break;
    case "sheriff_vote_result":
      next.sheriffElectionStep = null;
      next.votes = {};
      break;
    case "sheriff_elected":
    case "sheriff_proclaimed":
      next.sheriffId = (p.player_id as number) ?? event.player_id ?? null;
      next.sheriffCandidates = new Set();
      next.sheriffWithdrawn = new Set();
      next.sheriffElectionStep = null;
      break;
    case "sheriff_badge_transferred":
      next.sheriffId = (p.to_id as number) ?? event.player_id ?? null;
      next.sheriffCandidates = new Set();
      next.sheriffWithdrawn = new Set();
      next.sheriffElectionStep = null;
      break;
    case "speech_order_set": {
      const order = (p.order as number[]) ?? [];
      next.speechOrder = order;
      break;
    }
    case "speech_order_pick":
      break;
    case "self_destruct": {
      const pid = (p.player_id as number) ?? event.player_id;
      if (pid != null) next.alive.delete(pid);
      break;
    }
    case "hunter_shoot": {
      const target = p.target_id as number | null;
      if (target != null) next.alive.delete(target);
      break;
    }
    case "idiot_reveal": {
      const pid = (p.player_id as number) ?? event.player_id;
      if (pid != null) next.idiotRevealed.add(pid);
      break;
    }
    case "game_over":
      next.status = "complete";
      next.winner = (p.winner as string | null) ?? null;
      next.winReason = (p.win_reason as string | null) ?? null;
      break;
    case "player_dossier":
      next.dossier = p as unknown as PlayerDossier;
      break;
    default:
      break;
  }

  return next;
}

type Action = { type: "event"; event: GameEvent } | { type: "reset" };

function reducer(state: SpectatorState, action: Action): SpectatorState {
  if (action.type === "reset") return initialSpectatorState();
  return applyEvent(state, action.event);
}

export function useSpectatorState() {
  const [state, dispatch] = useReducer(reducer, undefined, initialSpectatorState);

  const applyEventAction = useCallback((event: GameEvent) => {
    dispatch({ type: "event", event });
  }, []);

  const reset = useCallback(() => {
    dispatch({ type: "reset" });
  }, []);

  return { state, applyEvent: applyEventAction, reset };
}
