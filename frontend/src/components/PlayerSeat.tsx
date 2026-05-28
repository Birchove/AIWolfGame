interface Props {
  playerId: number;
  alive: boolean;
  isSheriff: boolean;
  isSheriffCandidate: boolean;
  isSheriffWithdrawn: boolean;
  role?: string;
  speech?: string;
  demeanorEmojis?: string[];
  isCurrentSpeaker: boolean;
  voteTarget?: number | null;
  isIdiotRevealed: boolean;
}

export function PlayerSeat({
  playerId,
  alive,
  isSheriff,
  isSheriffCandidate,
  isSheriffWithdrawn,
  role,
  speech,
  demeanorEmojis,
  isCurrentSpeaker,
  voteTarget,
  isIdiotRevealed,
}: Props) {
  const classes = [
    "seat",
    alive ? "alive" : "dead",
    isSheriff ? "sheriff" : "",
    isSheriffCandidate ? "sheriff-candidate" : "",
    isSheriffWithdrawn ? "sheriff-withdrawn" : "",
    isCurrentSpeaker ? "speaking" : "",
    isIdiotRevealed ? "idiot-soul" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const emojiLine = demeanorEmojis?.length ? demeanorEmojis.join("") : "";

  return (
    <div className={classes} title={speech}>
      <div className="seat-id">{playerId}</div>
      {isSheriff && (
        <div className="seat-badge sheriff-badge" title="警长">
          🎖
        </div>
      )}
      {isSheriffCandidate && !isSheriff && (
        <div className="seat-badge candidate-badge" title="警上">
          警
        </div>
      )}
      {isSheriffWithdrawn && (
        <div className="seat-badge withdrawn-badge" title="退水">
          退
        </div>
      )}
      {role && <div className="seat-role">{role}</div>}
      {emojiLine && <div className="seat-emojis">{emojiLine}</div>}
      {voteTarget != null && (
        <div className="seat-vote">→{voteTarget}</div>
      )}
      {speech && <div className="seat-speech">{speech.slice(0, 24)}</div>}
    </div>
  );
}
