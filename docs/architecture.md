# Architecture

See [CLAUDE.md](../CLAUDE.md) for the authoritative overview.

## Layer order

```
Engine (deterministic) → Protocol (visibility + actions) → Agents (LangGraph) → Logging → API/UI
```

## Module contracts

- **engine/** — Owns `GameState`, phase machine, win checks. No LLM imports.
- **protocol/** — `PlayerView`, `Action`, `Visibility.for_player()`. Single choke-point for info isolation.
- **roles/** — Role-specific skill resolution; called by engine during night/day.
- **agents/** — LangGraph graphs; input `PlayerView`, output validated `Action`.
- **logging/** — Append-only `GameEvent` stream; replay reconstructs state timeline.
- **api/** — Read-only WebSocket fan-out of events (Phase 7+).

## Extension points (future)

| Feature | Hook |
|---------|------|
| Evaluation / Leaderboard | `logging/recorder.py` + `docs/event-schema.md` |
| Self-evolution | Post-game analysis on event logs |
| Generic Agent | Replace `agents/base.py`; keep engine/protocol |
