import { ALL_PLAYER_IDS } from "../types/event";
import type { SpectatorState } from "../types/event";
import { PlayerSeat } from "./PlayerSeat";

interface Props {
  state: SpectatorState;
  showRoles: boolean;
}

export function RoundTable({ state, showRoles }: Props) {
  const inSheriffElection =
    state.sheriffElectionStep != null && state.sheriffId == null;

  return (
    <div className="round-table">
      {ALL_PLAYER_IDS.map((id, index) => {
        const angle = (index / 12) * 2 * Math.PI - Math.PI / 2;
        const x = 50 + 42 * Math.cos(angle);
        const y = 50 + 42 * Math.sin(angle);
        return (
          <div
            key={id}
            className="seat-wrap"
            style={{ left: `${x}%`, top: `${y}%` }}
          >
            <PlayerSeat
              playerId={id}
              alive={state.alive.has(id)}
              isSheriff={state.sheriffId === id}
              isSheriffCandidate={
                inSheriffElection && state.sheriffCandidates.has(id)
              }
              isSheriffWithdrawn={
                inSheriffElection && state.sheriffWithdrawn.has(id)
              }
              role={showRoles ? state.roles?.[id] : undefined}
              speech={state.speeches[id]}
              demeanorEmojis={state.demeanorEmojis[id]}
              isCurrentSpeaker={state.lastSpeakerId === id}
              voteTarget={state.votes[id]}
              isIdiotRevealed={state.idiotRevealed.has(id)}
            />
          </div>
        );
      })}
      <div className="table-center">
        <div>{state.phase ?? "—"}</div>
        <div>第 {state.round ?? "?"} 轮</div>
        {state.sheriffElectionStep && (
          <div className="sheriff-phase">
            竞选·
            {state.sheriffElectionStep === "nominate" && "上警"}
            {state.sheriffElectionStep === "speech" && "警上发言"}
            {state.sheriffElectionStep === "vote" && "警下投票"}
          </div>
        )}
        {inSheriffElection && state.sheriffCandidates.size > 0 && (
          <div className="sheriff-candidates">
            警上: {[...state.sheriffCandidates].sort((a, b) => a - b).join(", ")}
          </div>
        )}
        {state.speechOrder.length > 0 && state.phase === "day_speech" && (
          <div className="speech-order-banner">
            发言序: {state.speechOrder.join(" → ")}
          </div>
        )}
        {state.sheriffId != null && (
          <div className="sheriff-banner">🎖 警长 P{state.sheriffId}</div>
        )}
        {state.status === "complete" && (
          <div className="winner">
            {state.winner} 胜 ({state.winReason})
          </div>
        )}
      </div>
    </div>
  );
}
