import { createGame } from "../api/client";
import { useHealth } from "../hooks/useHealth";

interface Props {
  onStarted: (gameId: string) => void;
}

export function GameSetup({ onStarted }: Props) {
  const { health, error } = useHealth();

  async function launch() {
    const id = await createGame(0);
    onStarted(id);
  }

  const llmReady = health?.llm_ready === true;
  const canStart = llmReady && !error;

  return (
    <div className="game-setup">
      <h1>AI 狼人杀观战</h1>
      <p className="hint">DeepSeek LLM 驱动 12 人自动对局，事件流实时更新。</p>

      {error && <p className="error">{error}</p>}

      {health && (
        <div className={`health-banner ${llmReady ? "ok" : "warn"}`}>
          {llmReady ? (
            <span>
              LLM 已就绪 — {health.provider}/{health.model}
            </span>
          ) : health.llm_configured ? (
            <span>LLM 依赖未安装 — 运行 pip install -e &quot;.[spectator]&quot;</span>
          ) : (
            <span>
              未检测到 API Key — 编辑 <code>Config/secrets.yaml</code>
            </span>
          )}
        </div>
      )}

      <button
        type="button"
        disabled={!canStart}
        onClick={() => launch().catch(console.error)}
      >
        开始新对局
      </button>
    </div>
  );
}
