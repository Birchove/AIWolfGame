import { useEffect, useRef } from "react";
import type { GameEvent, ViewMode } from "../types/event";

const TYPE_LABEL: Record<string, string> = {
  phase_change: "阶段",
  agent_turn: "发言",
  death: "死亡",
  vote_cast: "投票",
  vote_result: "票型",
  sheriff_nominate: "上警",
  sheriff_nomination_complete: "上警汇总",
  sheriff_withdraw: "退水",
  sheriff_speech_complete: "警上发言完",
  sheriff_vote_result: "警长票型",
  sheriff_elected: "警长",
  sheriff_proclaimed: "警长公示",
  sheriff_badge_transferred: "移交警徽",
  speech_order_pick: "警长定序",
  speech_order_set: "发言顺序",
  self_destruct: "自爆",
  hunter_shoot: "猎人",
  idiot_reveal: "白痴",
  game_over: "结束",
  wolf_consensus: "狼刀",
  witch_night: "女巫",
  seer_check: "验人",
  night_death: "夜死",
};

function formatEvent(e: GameEvent): string {
  const p = e.payload;
  switch (e.type) {
    case "agent_turn":
      return `P${e.player_id}: ${(p.speech as string) || "(无发言)"}`;
    case "vote_cast":
      return `P${p.voter_id} → P${p.target_id ?? "弃票"}`;
    case "vote_result":
      if (p.tied) return `平票 PK: ${(p.pk_candidates as number[])?.join(", ")}`;
      return p.eliminated ? `出局 P${p.eliminated}` : "平安日";
    case "death":
      return `P${p.player_id} 死亡`;
    case "phase_change":
      return String(p.phase);
    case "game_over":
      return `胜者 ${p.winner} (${p.win_reason})`;
    case "sheriff_nominate":
      return p.message as string;
    case "sheriff_nomination_complete":
      return (p.message as string) || `上警: ${(p.candidates as number[])?.join(", ")}`;
    case "sheriff_withdraw":
      return (p.message as string) || `P${p.player_id} 退水`;
    case "sheriff_vote_result": {
      const tally = p.tally as Record<string, number> | undefined;
      const tallyStr = tally
        ? Object.entries(tally)
            .map(([k, v]) => `P${k}:${v}`)
            .join(" ")
        : "";
      return ((p.message as string) || "警长投票") + (tallyStr ? ` [${tallyStr}]` : "");
    }
    case "sheriff_elected":
    case "sheriff_proclaimed":
      return (p.message as string) || `P${p.player_id} 当选警长`;
    case "sheriff_badge_transferred":
      return (p.message as string) || `警徽 P${p.from_id} → P${p.to_id}`;
    case "speech_order_pick":
      return (p.message as string) || "警长指定发言顺序";
    case "speech_order_set":
      return (p.message as string) || `顺序 ${(p.order as number[])?.join("→")}`;
    case "self_destruct":
      return `P${p.player_id} 自爆`;
    case "hunter_shoot":
      return `猎人 P${p.shooter_id} → P${p.target_id ?? "不开枪"}`;
    case "wolf_consensus": {
      const t = p.target_id as number | null;
      return t != null ? `刀口 P${t}` : "空刀";
    }
    case "seer_check":
      return `验 P${p.target_id}: ${p.is_wolf ? "狼" : "好人"}`;
    default:
      return JSON.stringify(p).slice(0, 80);
  }
}

const HIDDEN_IN_FEED = new Set(["player_dossier", "agent_turn_full", "game_start", "wolf_negotiation_round"]);

interface Props {
  events: GameEvent[];
  view: ViewMode;
}

export function EventFeed({ events, view }: Props) {
  const listRef = useRef<HTMLUListElement>(null);

  const visible = events.filter((e) => {
    if (HIDDEN_IN_FEED.has(e.type)) return false;
    if (view === "public" && e.visibility !== "public") return false;
    if (e.type === "agent_turn" && e.visibility !== "public") return false;
    return true;
  });

  useEffect(() => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [visible.length]);

  return (
    <div className="event-feed">
      <h2>事件流 ({visible.length})</h2>
      <ul ref={listRef}>
        {visible.map((e) => (
          <li key={e.seq} className={`evt evt-${e.type}`}>
            <span className="evt-seq">#{e.seq}</span>
            <span className="evt-type">{TYPE_LABEL[e.type] ?? e.type}</span>
            <span className="evt-body">{formatEvent(e)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
