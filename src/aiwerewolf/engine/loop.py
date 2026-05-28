"""Full game loop — drives phases with Agent team."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from schema.agent import AgentTurnOutput, HunterShootAction, SelfDestructAction, WitchPoisonAction, WitchSaveAction, WolfKillAction
from schema.config import AppConfig
from schema.enums import Camp, Phase, Role, WinReason

if TYPE_CHECKING:
    from aiwerewolf.agents.base import Agent
    from aiwerewolf.logging.recorder import Recorder
from aiwerewolf.engine.day import resolve_day_vote, resolve_pk_vote, resolve_sheriff_election, resolve_sheriff_pk
from aiwerewolf.engine.night import (
    check_hunter_status,
    collect_death_announcements,
    confirm_idiot,
    resolve_witch,
    resolve_wolf_kill,
)
from aiwerewolf.engine.rules import apply_win_if_any, next_phase
from aiwerewolf.engine.setup import create_game
from aiwerewolf.engine.state import GameState
from aiwerewolf.engine.speech import append_speech
from aiwerewolf.protocol.dispatch import apply_action
from aiwerewolf.protocol.visibility import Visibility

_MAX_STEPS = 5000
_WOLF_NEGOTIATION_ROUNDS = 5


@dataclass(frozen=True, slots=True)
class GameResult:
    state: GameState
    round_count: int
    winner: Camp | None
    win_reason: WinReason | None


class GameLoop:
    def __init__(
        self,
        agents: dict[int, Agent],
        *,
        max_rounds: int = 30,
        recorder: Recorder | None = None,
        cfg: AppConfig | None = None,
    ) -> None:
        self._agents = agents
        self._max_rounds = max_rounds
        self._recorder = recorder
        self._cfg = cfg

    def run(self, *, seed: int | None = None) -> GameResult:
        state = create_game(seed=seed)
        if self._cfg is not None:
            from aiwerewolf.agents.model_assign import bind_agents_for_game

            bind_agents_for_game(
                self._agents, state, self._cfg, seed=seed if seed is not None else 0
            )
        state = next_phase(state)
        if self._recorder is not None:
            self._recorder.record_game_start(state, seed=seed)
        steps = 0

        while state.phase != Phase.GAME_OVER and steps < _MAX_STEPS:
            state = self._drive_phase(state)
            state = apply_win_if_any(state, max_rounds=self._max_rounds)
            steps += 1

        if state.phase != Phase.GAME_OVER:
            state = apply_win_if_any(state, max_rounds=self._max_rounds)

        result = GameResult(
            state=state,
            round_count=state.round_number,
            winner=state.winner,
            win_reason=state.win_reason,
        )
        if self._recorder is not None:
            self._recorder.record_game_over(state, result)
            self._recorder.flush()
        return result

    def _drive_phase(self, state: GameState) -> GameState:
        if state.self_destruct_today:
            nxt = next_phase(state)
            self._record_phase(nxt)
            return nxt

        phase = state.phase
        if phase == Phase.NIGHT_WOLF:
            return self._night_wolf(state)
        if phase == Phase.NIGHT_WITCH:
            return self._night_witch(state)
        if phase == Phase.NIGHT_SEER:
            return self._single_role_phase(state, Role.SEER)
        if phase == Phase.NIGHT_HUNTER:
            return self._single_role_phase(state, Role.HUNTER)
        if phase == Phase.NIGHT_IDIOT:
            return self._single_role_phase(state, Role.IDIOT)
        if phase == Phase.DAY_SHERIFF:
            return self._day_sheriff(state)
        if phase in {Phase.DAY_ANNOUNCE, Phase.DAY_SPEECH}:
            return self._day_speeches(state)
        if phase == Phase.DAY_VOTE:
            return self._day_vote(state)
        if phase == Phase.DAY_PK:
            return self._day_pk(state)
        nxt = next_phase(state)
        self._record_phase(nxt)
        return nxt

    def _record_phase(self, state: GameState) -> None:
        if self._recorder is not None:
            self._recorder.record_phase_change(state)

    def _finish_phase(self, state: GameState) -> GameState:
        nxt = next_phase(state)
        self._record_phase(nxt)
        return nxt

    def _night_wolf(self, state: GameState) -> GameState:
        state = replace(state, wolf_kill_target=None)
        target, negotiation_log, unanimous = self._resolve_wolf_consensus(state)
        if self._recorder is not None:
            self._recorder.record_wolf_negotiation(state, negotiation_log)
        if target is not None:
            try:
                state = resolve_wolf_kill(state, target)
            except ValueError:
                target = None
        if target is None:
            state = replace(state, wolf_kill_target=None)
        if self._recorder is not None:
            self._recorder.record_wolf_consensus(state, unanimous=unanimous)
        state = replace(
            state, wolf_negotiation_round=0, wolf_negotiation_votes=()
        )
        return self._finish_phase(state)

    def _valid_wolf_targets(self, state: GameState) -> set[int]:
        wolf_ids = {p.player_id for p in state.living_wolves()}
        return {
            p.player_id
            for p in state.living_players()
            if p.player_id not in wolf_ids
        }

    def _sanitize_wolf_vote(
        self, state: GameState, target: int | None
    ) -> int | None:
        if target is None:
            return None
        if target not in self._valid_wolf_targets(state):
            return None
        return target

    def _resolve_wolf_consensus(
        self, state: GameState
    ) -> tuple[int | None, list[dict], bool]:
        wolves = list(state.living_wolves())
        negotiation_log: list[dict] = []
        if not wolves:
            return None, negotiation_log, False
        votes: list[int | None] = []
        unanimous = False
        for round_idx in range(_WOLF_NEGOTIATION_ROUNDS):
            state = replace(
                state,
                wolf_negotiation_round=round_idx + 1,
                wolf_negotiation_votes=(),
            )
            round_votes: list[tuple[int, int | None]] = []
            votes: list[int | None] = []
            round_discussions: list[dict] = []
            for w in wolves:
                state, output = self._act(state, w.player_id)
                target: int | None = None
                if isinstance(output.action, WolfKillAction):
                    target = self._sanitize_wolf_vote(state, output.action.target_id)
                    votes.append(target)
                round_votes.append((w.player_id, target))
                round_discussions.append(
                    {
                        "wolf_id": w.player_id,
                        "target_id": target,
                        "speech": output.speech,
                        "demeanor_emojis": list(output.demeanor_emojis or []),
                    }
                )
            state = replace(state, wolf_negotiation_votes=tuple(round_votes))
            negotiation_log.append(
                {
                    "round": round_idx + 1,
                    "discussions": round_discussions,
                    "votes": [
                        {"wolf_id": wid, "target_id": tgt}
                        for wid, tgt in round_votes
                    ],
                }
            )
            if (
                len(votes) == len(wolves)
                and votes
                and all(v == votes[0] for v in votes)
            ):
                unanimous = True
                return votes[0], negotiation_log, unanimous
        if not votes:
            return None, negotiation_log, False
        counts: dict[int | None, int] = {}
        for v in votes:
            counts[v] = counts.get(v, 0) + 1
        top_count = max(counts.values())
        leaders = [t for t, c in counts.items() if c == top_count]
        if len(leaders) == 1 and leaders[0] is not None:
            return leaders[0], negotiation_log, False
        return None, negotiation_log, False

    def _night_witch(self, state: GameState) -> GameState:
        witch = self._find_alive_role(state, Role.WITCH)
        use_antidote = False
        poison_target: int | None = None
        alive_before = {p.player_id for p in state.living_players()}
        if witch is not None:
            state, output = self._act(state, witch.player_id)
            action = output.action
            if isinstance(action, WitchSaveAction) and action.use_antidote:
                use_antidote = True
            elif isinstance(action, WitchPoisonAction):
                poison_target = action.target_id
        try:
            state = resolve_witch(
                state, use_antidote=use_antidote, poison_target=poison_target
            )
        except ValueError:
            use_antidote = False
            poison_target = None
            state = resolve_witch(state)
        night_dead = tuple(
            sorted(
                pid
                for pid in alive_before
                if not state.player(pid).alive
            )
        )
        if self._recorder is not None:
            self._recorder.record_witch_night(
                state,
                antidote_used=use_antidote,
                poison_target=poison_target,
            )
            self._recorder.record_night_deaths(state, player_ids=night_dead)
        state = check_hunter_status(state)
        state = self._handle_hunter_shoot(state)
        return self._finish_phase(state)

    def _single_role_phase(self, state: GameState, role: Role) -> GameState:
        player = self._find_alive_role(state, role)
        if player is not None:
            state, output = self._act(state, player.player_id)
            state = self._try_apply(state, output)
        elif role == Role.HUNTER:
            state = check_hunter_status(state)
        elif role == Role.IDIOT:
            state = confirm_idiot(state)
        if role == Role.IDIOT:
            state = collect_death_announcements(state)
            if self._recorder is not None:
                self._recorder.record_death_announcements(state)
        if role == Role.SEER:
            if self._recorder is not None:
                self._recorder.record_seer_check_if_new(state)
        return self._finish_phase(state)

    def _day_sheriff(self, state: GameState) -> GameState:
        from dataclasses import replace

        from schema.agent import PassAction, SheriffRunAction, SheriffWithdrawAction

        from aiwerewolf.engine.sheriff_election import (
            sheriff_speech_order,
            sheriff_voter_ids,
        )

        if state.sheriff_election_forbidden:
            return self._finish_phase(state)

        skip_nominate = bool(
            state.sheriff_election_retry and state.sheriff_candidates
        )

        if not skip_nominate:
            state = replace(state, sheriff_election_step="nominate")
            for pid in self._living_ids(state):
                before = set(state.sheriff_candidates)
                state, output = self._act(state, pid)
                state = self._try_apply(state, output)
                if self._recorder is not None:
                    self._record_sheriff_nominate_turn(
                        state, output, before_candidates=before
                    )
                if state.self_destruct_today or state.phase == Phase.GAME_OVER:
                    return (
                        self._finish_phase(state)
                        if state.phase != Phase.GAME_OVER
                        else state
                    )
            if self._recorder is not None:
                self._recorder.record_sheriff_nomination_complete(state)
        else:
            state = replace(state, sheriff_election_retry=False)

        if not state.sheriff_candidates:
            state = replace(state, sheriff_election_step="nominate")
            return self._finish_phase(state)

        living_cands = tuple(
            pid
            for pid in state.sheriff_candidates
            if state.player(pid).alive
        )
        state = replace(state, sheriff_candidates=living_cands, sheriff_election_step="speech")
        for pid in sheriff_speech_order(state):
            if pid not in state.sheriff_candidates:
                continue
            state, output = self._act(state, pid)
            state = self._try_apply(state, output)
            if (
                self._recorder is not None
                and isinstance(output.action, SheriffWithdrawAction)
            ):
                self._recorder.record_sheriff_withdraw(state, pid)
            if state.self_destruct_today or state.phase == Phase.GAME_OVER:
                return (
                    self._finish_phase(state)
                    if state.phase != Phase.GAME_OVER
                    else state
                )
        if self._recorder is not None:
            self._recorder.record_sheriff_speech_complete(state)

        state = replace(state, sheriff_election_step="vote")
        for pid in sheriff_voter_ids(state):
            state, output = self._act(state, pid)
            state = self._try_apply(state, output)
            if state.self_destruct_today or state.phase == Phase.GAME_OVER:
                return (
                    self._finish_phase(state)
                    if state.phase != Phase.GAME_OVER
                    else state
                )

        votes_snapshot = state.day_votes
        state = resolve_sheriff_election(state)
        if self._recorder is not None:
            self._recorder.record_sheriff_vote_result(state, votes=votes_snapshot)
            if state.sheriff_id is not None:
                self._recorder.record_sheriff_elected(state)
            elif state.phase == Phase.DAY_PK:
                self._recorder.record_vote_result(
                    state,
                    eliminated=None,
                    pk_candidates=state.pk_candidates,
                    tied=True,
                )
        state = replace(state, sheriff_election_step="nominate")
        state = self._handle_hunter_shoot(state)
        if state.phase == Phase.DAY_PK:
            return state
        return self._finish_phase(state)

    def _record_sheriff_nominate_turn(
        self,
        state: GameState,
        output: AgentTurnOutput,
        *,
        before_candidates: set[int],
    ) -> None:
        from schema.agent import PassAction, SheriffRunAction

        assert self._recorder is not None
        pid = output.player_id
        if isinstance(output.action, SheriffRunAction) or (
            pid in state.sheriff_candidates and pid not in before_candidates
        ):
            self._recorder.record_sheriff_nominate(state, pid, running=True)
        elif isinstance(output.action, PassAction):
            self._recorder.record_sheriff_nominate(state, pid, running=False)

    def _day_speeches(self, state: GameState) -> GameState:
        for pid in self._speech_order(state):
            state, output = self._act(state, pid)
            state = self._try_apply(state, output)
            if state.self_destruct_today or state.phase == Phase.GAME_OVER:
                return (
                    self._finish_phase(state)
                    if state.phase != Phase.GAME_OVER
                    else state
                )
        return self._finish_phase(state)

    def _day_vote(self, state: GameState) -> GameState:
        for pid in self._day_voters(state):
            state, output = self._act(state, pid)
            state = self._try_apply(state, output)
            if state.self_destruct_today or state.phase == Phase.GAME_OVER:
                return (
                    self._finish_phase(state)
                    if state.phase != Phase.GAME_OVER
                    else state
                )
        before = state
        state = resolve_day_vote(state)
        self._record_vote_resolution(before, state)
        state = self._handle_hunter_shoot(state)
        if state.phase == Phase.DAY_PK:
            return state
        return self._finish_phase(state)

    def _day_pk(self, state: GameState) -> GameState:
        pk_set = set(state.pk_candidates)
        for pid in self._speech_order(state):
            if pid not in pk_set:
                continue
            state, output = self._act(state, pid)
            state = self._try_apply(state, output)
            if state.self_destruct_today or state.phase == Phase.GAME_OVER:
                return (
                    self._finish_phase(state)
                    if state.phase != Phase.GAME_OVER
                    else state
                )
        for pid in self._day_voters(state):
            state, output = self._act(state, pid)
            state = self._try_apply(state, output)
            if state.self_destruct_today or state.phase == Phase.GAME_OVER:
                return (
                    self._finish_phase(state)
                    if state.phase != Phase.GAME_OVER
                    else state
                )
        before = state
        if state.pk_candidates and state.sheriff_id is None and state.phase == Phase.DAY_PK:
            state = resolve_sheriff_pk(state)
            if self._recorder is not None and state.sheriff_id is not None:
                self._recorder.record_sheriff_elected(state)
        else:
            state = resolve_pk_vote(state)
            self._record_vote_resolution(before, state)
        state = self._handle_hunter_shoot(state)
        return self._finish_phase(state)

    def _record_vote_resolution(self, before: GameState, after: GameState) -> None:
        if self._recorder is None:
            return
        if after.phase == Phase.DAY_PK and after.pk_candidates:
            self._recorder.record_vote_result(
                after,
                eliminated=None,
                pk_candidates=after.pk_candidates,
                tied=True,
            )
            return
        eliminated = self._vote_outcome_player(before, after)
        self._recorder.record_vote_result(
            after,
            eliminated=eliminated,
            pk_candidates=(),
            tied=eliminated is None,
        )

    @staticmethod
    def _vote_outcome_player(before: GameState, after: GameState) -> int | None:
        for p in after.players:
            prev = before.player(p.player_id)
            if prev.alive and not p.alive:
                return p.player_id
            if not prev.in_soul_state and p.in_soul_state:
                return p.player_id
        return None

    def _handle_hunter_shoot(self, state: GameState) -> GameState:
        while state.hunter_can_shoot and state.phase != Phase.GAME_OVER:
            hunter = self._find_role_any(state, Role.HUNTER)
            if hunter is None or not state.hunter_can_shoot:
                break
            state, output = self._act(state, hunter.player_id)
            if not isinstance(output.action, HunterShootAction):
                output = AgentTurnOutput(
                    model=output.model,
                    player_id=output.player_id,
                    role=output.role,
                    speech=output.speech,
                    demeanor=output.demeanor,
                    action=HunterShootAction(target_id=None),
                )
            target_id = output.action.target_id
            if self._recorder is not None:
                self._recorder.record_hunter_shoot(
                    state, hunter.player_id, target_id
                )
            state = apply_action(state, output)
            state = apply_win_if_any(state, max_rounds=self._max_rounds)
        return state

    def _act(self, state: GameState, player_id: int) -> tuple[GameState, AgentTurnOutput]:
        view = Visibility.for_player(state, player_id)
        output = self._agents[player_id].act(view)
        state = append_speech(state, output)
        if self._recorder is not None:
            self._recorder.record_agent_turn(state, output)
        return state, output

    def _try_apply(self, state: GameState, output: AgentTurnOutput) -> GameState:
        try:
            return apply_action(state, output)
        except ValueError:
            if isinstance(output.action, SelfDestructAction):
                return state
            return state

    @staticmethod
    def _find_alive_role(state: GameState, role: Role):
        for p in state.living_players():
            if p.role == role:
                return p
        return None

    @staticmethod
    def _find_role_any(state: GameState, role: Role):
        for p in state.players:
            if p.role == role:
                return p
        return None

    @staticmethod
    def _living_ids(state: GameState) -> list[int]:
        return sorted(p.player_id for p in state.living_players())

    def _day_voters(self, state: GameState) -> list[int]:
        return sorted(
            p.player_id for p in state.living_players() if not p.in_soul_state
        )

    def _speech_order(self, state: GameState) -> list[int]:
        ids = self._living_ids(state)
        if not ids:
            return []
        start = state.sheriff_id or 1
        if start not in ids:
            start = ids[0]
        idx = ids.index(start)
        return ids[idx:] + ids[:idx]
