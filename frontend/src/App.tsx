import { useState } from "react";
import type { ViewMode } from "./types/event";
import { GameSetup } from "./components/GameSetup";
import { RoundTable } from "./components/RoundTable";
import { EventFeed } from "./components/EventFeed";
import { GameSummary } from "./components/GameSummary";
import { ViewModeToggle } from "./components/ViewModeToggle";
import { useSpectatorState } from "./hooks/useSpectatorState";
import { useGameSocket } from "./hooks/useGameSocket";
import { useGameStatus } from "./hooks/useGameStatus";

export default function App() {
  const [gameId, setGameId] = useState<string | null>(null);
  const [view, setView] = useState<ViewMode>("public");
  const { state, applyEvent, reset } = useSpectatorState();
  const gameStatus = useGameStatus(gameId);

  const handleViewChange = (v: ViewMode) => {
    reset();
    setView(v);
  };

  const handleGameStarted = (id: string) => {
    reset();
    setView("public");
    setGameId(id);
  };

  const { connected, error: wsError } = useGameSocket(gameId, view, applyEvent);

  const running =
    gameStatus?.status === "running" ||
    (state.status === "running" && gameStatus?.status !== "complete");
  const failed = gameStatus?.status === "failed";

  return (
    <div className="app">
      {!gameId ? (
        <GameSetup onStarted={handleGameStarted} />
      ) : (
        <>
          <header className="toolbar">
            <span className="game-id">对局 {gameId.slice(0, 8)}…</span>
            <ViewModeToggle view={view} onChange={handleViewChange} />
            <span className={`conn ${connected ? "on" : "off"}`}>
              {connected ? "已连接" : "连接中…"}
            </span>
            {running && state.status !== "complete" && (
              <span className="status-running">对局进行中…</span>
            )}
            {state.status === "complete" && (
              <span className="status-done">已结束</span>
            )}
            {failed && (
              <span className="error" title={gameStatus?.error}>
                对局失败
              </span>
            )}
            <button type="button" onClick={() => setGameId(null)}>
              新局
            </button>
          </header>
          {wsError && <p className="error">{wsError}</p>}
          {failed && gameStatus?.error && (
            <p className="error">{gameStatus.error}</p>
          )}
          <main className="layout">
            <RoundTable state={state} showRoles={view === "god"} />
            <div className="side-panel">
              <EventFeed events={state.events} view={view} />
              {view === "god" && state.dossier && state.status === "complete" && (
                <GameSummary dossier={state.dossier} />
              )}
            </div>
          </main>
        </>
      )}
    </div>
  );
}
