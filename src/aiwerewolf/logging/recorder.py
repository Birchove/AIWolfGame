"""Append-only event recorder."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from schema.agent import AgentTurnOutput, SelfDestructAction, SpeechOrderAction, VoteAction
from schema.enums import Phase, Role
from schema.events import GameEvent

from aiwerewolf.engine.state import GameState
from aiwerewolf.logging import builder
from aiwerewolf.logging.log import EventLog
from aiwerewolf.logging.storage import append_event, write_event_log
from aiwerewolf.logging.chronicle import write_god_chronicle

if TYPE_CHECKING:
    from aiwerewolf.engine.loop import GameResult


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


class Recorder:
    def __init__(
        self,
        *,
        game_id: str | None = None,
        output_path: Path | None = None,
        on_event: Callable[[GameEvent], None] | None = None,
    ) -> None:
        self.game_id = game_id or str(uuid.uuid4())
        self._log = EventLog(self.game_id)
        self._seq = 0
        self._output_path = output_path
        self._on_event = on_event
        self._last_death_announcements: tuple[int, ...] = ()
        self._last_seer_check_count = 0
        self._seed: int | None = None
        self._god_turns: list[dict] = []

    @property
    def event_log(self) -> EventLog:
        return self._log

    def _append(
        self,
        *,
        visibility: str,
        type: str,
        state: GameState | None = None,
        player_id: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> GameEvent:
        self._seq += 1
        phase = state.phase.value if state else None
        round_num = state.round_number if state else None
        event = GameEvent(
            seq=self._seq,
            timestamp=_utc_now(),
            game_id=self.game_id,
            visibility=visibility,
            type=type,
            phase=phase,
            round=round_num,
            player_id=player_id,
            payload=payload or {},
        )
        self._log.events.append(event)
        if self._output_path is not None and visibility == "god_only":
            append_event(self._output_path, event)
        if self._on_event is not None:
            self._on_event(event)
        return event

    def record_game_start(self, state: GameState, *, seed: int | None) -> None:
        self._seed = seed
        self._god_turns = []
        self._append(
            visibility="god_only",
            type="game_start",
            state=state,
            payload=builder.build_game_start_payload(state, seed=seed),
        )
        self.record_phase_change(state)

    def record_phase_change(self, state: GameState) -> None:
        self._append(
            visibility="public",
            type="phase_change",
            state=state,
            payload={"phase": state.phase.value},
        )

    def record_agent_turn(
        self,
        state: GameState,
        output: AgentTurnOutput,
        *,
        count_as_speech: bool = True,
    ) -> None:
        god_payload = builder.build_agent_turn_god(output, state)
        self._god_turns.append(god_payload)
        self._append(
            visibility="god_only",
            type="agent_turn_full",
            state=state,
            player_id=output.player_id,
            payload=god_payload,
        )
        skip_public = (
            not count_as_speech and isinstance(output.action, SpeechOrderAction)
        )
        public = builder.build_agent_turn_public(output, state)
        if public is not None and not skip_public:
            self._append(
                visibility="public",
                type="agent_turn",
                state=state,
                player_id=output.player_id,
                payload=public,
            )
        if skip_public and isinstance(output.action, SpeechOrderAction):
            action = output.action
            self._append(
                visibility="public",
                type="speech_order_pick",
                state=state,
                player_id=output.player_id,
                payload={
                    "sheriff_id": output.player_id,
                    "side": action.side,
                    "first_speaker_id": action.first_speaker_id,
                    "message": (
                        f"警长指定 P{action.first_speaker_id} 首位发言"
                        if action.first_speaker_id is not None
                        else f"警长指定从锚点向{'右' if action.side == 'right' else '左'}发言"
                    ),
                },
            )
        self._append(
            visibility=f"private:{output.player_id}",
            type="agent_turn",
            state=state,
            player_id=output.player_id,
            payload=builder.build_agent_turn_private(output, state),
        )
        action = output.action
        if isinstance(action, VoteAction) and state.phase in {
            Phase.DAY_VOTE,
            Phase.DAY_PK,
            Phase.DAY_SHERIFF,
        }:
            self._append(
                visibility="public",
                type="vote_cast",
                state=state,
                player_id=output.player_id,
                payload={
                    "voter_id": output.player_id,
                    "target_id": action.target_id,
                },
            )
        if isinstance(action, SelfDestructAction):
            self.record_self_destruct(state, output.player_id)

    def record_wolf_negotiation(self, state: GameState, rounds: list[dict]) -> None:
        if not rounds:
            return
        self._append(
            visibility="god_only",
            type="wolf_negotiation_round",
            state=state,
            payload=builder.build_wolf_negotiation_payload(rounds),
        )

    def record_wolf_consensus(
        self, state: GameState, *, unanimous: bool
    ) -> None:
        self._append(
            visibility="god_only",
            type="wolf_consensus",
            state=state,
            payload=builder.build_wolf_consensus_payload(
                state, unanimous=unanimous
            ),
        )

    def record_witch_night(
        self,
        state: GameState,
        *,
        antidote_used: bool,
        poison_target: int | None,
    ) -> None:
        self._append(
            visibility="god_only",
            type="witch_night",
            state=state,
            payload=builder.build_witch_night_payload(
                antidote_used=antidote_used,
                poison_target=poison_target,
            ),
        )

    def record_seer_check_if_new(self, state: GameState) -> None:
        if len(state.seer_checks) <= self._last_seer_check_count:
            return
        self._last_seer_check_count = len(state.seer_checks)
        payload = builder.build_seer_check_payload(state)
        if payload is None:
            return
        seer = next((p for p in state.players if p.role == Role.SEER), None)
        if seer is None:
            return
        self._append(
            visibility=f"private:{seer.player_id}",
            type="seer_check",
            state=state,
            player_id=seer.player_id,
            payload=payload,
        )
        self._append(
            visibility="god_only",
            type="seer_check",
            state=state,
            player_id=seer.player_id,
            payload=payload,
        )

    def record_night_deaths(
        self, state: GameState, *, player_ids: tuple[int, ...]
    ) -> None:
        """God-only log of deaths resolved at witch phase."""
        for pid in player_ids:
            self._append(
                visibility="god_only",
                type="night_death",
                state=state,
                player_id=pid,
                payload={
                    "player_id": pid,
                    "wolf_kill_target": state.wolf_kill_target,
                },
            )

    def record_death_announcements(self, state: GameState) -> None:
        current = state.death_announcements
        new_ids = [pid for pid in current if pid not in self._last_death_announcements]
        self._last_death_announcements = current
        for pid in new_ids:
            self._append(
                visibility="public",
                type="death",
                state=state,
                player_id=pid,
                payload={"player_id": pid, "announced": True, "cause": "night"},
            )

    def record_sheriff_nominate(
        self, state: GameState, player_id: int, *, running: bool
    ) -> None:
        label = "上警" if running else "警下"
        self._append(
            visibility="public",
            type="sheriff_nominate",
            state=state,
            player_id=player_id,
            payload={
                "player_id": player_id,
                "running": running,
                "message": f"P{player_id} {label}",
            },
        )

    def record_sheriff_nomination_complete(self, state: GameState) -> None:
        self._append(
            visibility="public",
            type="sheriff_nomination_complete",
            state=state,
            payload={
                "candidates": list(state.sheriff_candidates),
                "message": (
                    f"上警玩家: {list(state.sheriff_candidates)}"
                    if state.sheriff_candidates
                    else "无人上警"
                ),
            },
        )

    def record_sheriff_withdraw(self, state: GameState, player_id: int) -> None:
        self._append(
            visibility="public",
            type="sheriff_withdraw",
            state=state,
            player_id=player_id,
            payload={
                "player_id": player_id,
                "message": f"P{player_id} 退水",
                "candidates_remaining": list(state.sheriff_candidates),
            },
        )

    def record_sheriff_speech_complete(self, state: GameState) -> None:
        self._append(
            visibility="public",
            type="sheriff_speech_complete",
            state=state,
            payload={
                "candidates": list(state.sheriff_candidates),
                "withdrawn": list(state.sheriff_withdrawn),
            },
        )

    def record_speech_order_set(
        self, state: GameState, *, order: list[int]
    ) -> None:
        payload = {
            "order": order,
            "side": state.speech_order_side,
            "first_speaker_id": state.speech_first_speaker_id,
            "message": f"发言顺序: {order}",
        }
        self._append(
            visibility="public",
            type="speech_order_set",
            state=state,
            payload=payload,
        )
        self._append(
            visibility="god_only",
            type="speech_order_set",
            state=state,
            payload=payload,
        )

    def record_sheriff_vote_result(
        self, state: GameState, *, votes: tuple
    ) -> None:
        from aiwerewolf.engine.state import VoteRecord

        tally: dict[int, float] = {}
        cast: list[dict] = []
        for v in votes:
            if not isinstance(v, VoteRecord):
                continue
            cast.append({"voter_id": v.voter_id, "target_id": v.target_id})
            if v.target_id is not None:
                tally[v.target_id] = tally.get(v.target_id, 0.0) + v.weight
        payload: dict = {
            "votes": cast,
            "tally": {str(k): val for k, val in tally.items()},
            "sheriff_id": state.sheriff_id,
            "pk_candidates": list(state.pk_candidates),
        }
        if state.sheriff_id is not None:
            payload["message"] = f"P{state.sheriff_id} 当选警长"
        elif state.pk_candidates:
            payload["message"] = f"警长投票平票 PK: {list(state.pk_candidates)}"
        else:
            payload["message"] = "警长投票无结果"
        self._append(
            visibility="public",
            type="sheriff_vote_result",
            state=state,
            payload=payload,
        )
        self._append(
            visibility="god_only",
            type="sheriff_vote_result",
            state=state,
            payload=payload,
        )

    def record_sheriff_elected(self, state: GameState) -> None:
        if state.sheriff_id is None:
            return
        sid = state.sheriff_id
        payload = {
            "player_id": sid,
            "message": f"{sid}号玩家当选为警长，白天投票计 1.5 票",
        }
        self._append(
            visibility="god_only",
            type="sheriff_proclaimed",
            state=state,
            player_id=sid,
            payload=payload,
        )
        self._append(
            visibility="public",
            type="sheriff_elected",
            state=state,
            player_id=sid,
            payload={"player_id": sid, "message": payload["message"]},
        )

    def record_sheriff_badge_transferred(
        self, state: GameState, *, from_id: int
    ) -> None:
        if state.sheriff_id is None:
            return
        payload = {
            "from_id": from_id,
            "to_id": state.sheriff_id,
            "message": f"警徽 P{from_id} → P{state.sheriff_id}",
        }
        self._append(
            visibility="public",
            type="sheriff_badge_transferred",
            state=state,
            player_id=state.sheriff_id,
            payload=payload,
        )

    def record_vote_result(
        self,
        state: GameState,
        *,
        eliminated: int | None,
        pk_candidates: tuple[int, ...] = (),
        tied: bool = False,
    ) -> None:
        self._append(
            visibility="public",
            type="vote_result",
            state=state,
            payload=builder.build_vote_result_payload(
                eliminated=eliminated,
                pk_candidates=pk_candidates,
                tied=tied,
            ),
        )
        if eliminated is not None:
            player = state.player(eliminated)
            if player.role == Role.IDIOT and player.in_soul_state:
                self._append(
                    visibility="public",
                    type="idiot_reveal",
                    state=state,
                    player_id=eliminated,
                    payload={"player_id": eliminated},
                )
            elif not player.alive:
                self._append(
                    visibility="public",
                    type="death",
                    state=state,
                    player_id=eliminated,
                    payload={"player_id": eliminated, "cause": "vote"},
                )

    def record_self_destruct(self, state: GameState, player_id: int) -> None:
        self._append(
            visibility="public",
            type="self_destruct",
            state=state,
            player_id=player_id,
            payload={
                "player_id": player_id,
                "during_election": state.phase
                in {Phase.DAY_SHERIFF, Phase.DAY_PK},
            },
        )

    def record_hunter_shoot(
        self, state: GameState, shooter_id: int, target_id: int | None
    ) -> None:
        self._append(
            visibility="public",
            type="hunter_shoot",
            state=state,
            player_id=shooter_id,
            payload=builder.build_hunter_shoot_payload(shooter_id, target_id),
        )
        if target_id is not None:
            self._append(
                visibility="public",
                type="death",
                state=state,
                player_id=target_id,
                payload={"player_id": target_id, "cause": "hunter_shoot"},
            )

    def record_game_over(self, state: GameState, result: GameResult) -> None:
        self._append(
            visibility="public",
            type="game_over",
            state=state,
            payload=builder.build_game_over_payload(result),
        )
        self._append(
            visibility="god_only",
            type="player_dossier",
            state=state,
            payload=builder.build_player_dossier(
                state, turns=self._god_turns, seed=self._seed
            ),
        )

    def flush(self) -> None:
        if self._output_path is not None:
            write_event_log(self._output_path, self._log, god_only=True)
            write_god_chronicle(self._output_path, self._log)
