import type { PlayerDossier } from "../types/dossier";

interface Props {
  dossier: PlayerDossier;
}

export function GameSummary({ dossier }: Props) {
  return (
    <div className="game-summary">
      <h2>全局统计（上帝视角）</h2>
      <p className="summary-meta">
        共 {dossier.round_count} 天 · 胜者 {dossier.winner ?? "—"} (
        {dossier.win_reason ?? "—"})
      </p>
      <div className="summary-grid">
        {dossier.players.map((p) => (
          <details key={p.player_id} className="summary-card">
            <summary>
              P{p.player_id} · {p.role}
              {!p.alive && " · 出局"}
              {p.is_sheriff && " · 警长"}
              {p.in_soul_state && " · 灵魂态"}
              <span className="summary-count"> ({p.speech_count} 次发言)</span>
            </summary>
            <ul className="summary-turns">
              {p.turns.length === 0 && <li>（无记录）</li>}
              {p.turns.map((t, i) => (
                <li key={`${t.phase}-${i}`}>
                  <div className="turn-head">
                    第{t.round}天 · {t.phase}
                    {(t.demeanor_emojis?.length ?? 0) > 0 && (
                      <span className="turn-emojis">
                        {t.demeanor_emojis.join("")}
                      </span>
                    )}
                  </div>
                  {t.speech && <div className="turn-speech">发言: {t.speech}</div>}
                  {t.demeanor && (
                    <div className="turn-demeanor">神态: {t.demeanor}</div>
                  )}
                  {t.reasoning && (
                    <div className="turn-reasoning">心理: {t.reasoning}</div>
                  )}
                  {t.action && (
                    <div className="turn-action">
                      行动: {String((t.action as { type?: string }).type ?? "?")}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </details>
        ))}
      </div>
    </div>
  );
}
