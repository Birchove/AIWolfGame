"""In-memory game registry for API."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum

from schema.events import GameEvent

from aiwerewolf.engine.loop import GameResult
from aiwerewolf.logging.recorder import EventLog, Recorder


class GameStatus(str, Enum):
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class GameSession:
    game_id: str
    recorder: Recorder
    status: GameStatus = GameStatus.RUNNING
    result: GameResult | None = None
    error: str | None = None
    subscribers: list[asyncio.Queue[GameEvent | None]] = field(default_factory=list)

    @property
    def event_log(self) -> EventLog:
        return self.recorder.event_log


class GameRegistry:
    def __init__(self) -> None:
        self._games: dict[str, GameSession] = {}
        self._lock = asyncio.Lock()

    async def create(self, session: GameSession) -> None:
        async with self._lock:
            self._games[session.game_id] = session

    async def get(self, game_id: str) -> GameSession | None:
        async with self._lock:
            return self._games.get(game_id)

    async def mark_complete(
        self, game_id: str, result: GameResult
    ) -> None:
        async with self._lock:
            session = self._games.get(game_id)
            if session is None:
                return
            session.status = GameStatus.COMPLETE
            session.result = result

    async def mark_failed(self, game_id: str, error: str) -> None:
        async with self._lock:
            session = self._games.get(game_id)
            if session is None:
                return
            session.status = GameStatus.FAILED
            session.error = error

    def subscribe(self, session: GameSession) -> asyncio.Queue[GameEvent | None]:
        queue: asyncio.Queue[GameEvent | None] = asyncio.Queue()
        session.subscribers.append(queue)
        return queue

    async def broadcast(self, game_id: str, event: GameEvent) -> None:
        async with self._lock:
            session = self._games.get(game_id)
            if session is None:
                return
            for queue in session.subscribers:
                await queue.put(event)

    async def close_subscribers(self, game_id: str) -> None:
        async with self._lock:
            session = self._games.get(game_id)
            if session is None:
                return
            for queue in session.subscribers:
                await queue.put(None)
