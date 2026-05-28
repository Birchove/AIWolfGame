# Information Visibility

Authoritative matrix lives in [CLAUDE.md](../CLAUDE.md#信息可见性详见-docsvisibilitymd).

## Design rules

1. **Only** `Visibility.for_player(game_state, player_id)` constructs agent-facing views.
2. Agents never receive `GameState` references (enforce via types + tests).
3. **Public**: `player_id`, `speech`, `demeanor`, votes, deaths, explosions, sheriff badge holder.
4. **Private**: own role, wolf teammates, seer results, witch night-death notice, hunter shoot eligibility.
5. **Dead players**: `DeadView` — public log only; cannot act; not omniscient.

## Spectator modes

- **GodView** — all roles, all night actions (judge perspective).
- **PublicView** — same as a living villager with no special knowledge.
