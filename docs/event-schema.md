# Event Schema (draft)

Append-only JSON lines. Each event has:

```json
{
  "seq": 1,
  "timestamp": "ISO-8601",
  "phase": "night_wolf | night_witch | ... | day_vote",
  "round": 1,
  "type": "speech | vote | skill | death | sheriff | explosion | ...",
  "visibility": "public | private:{player_id} | god_only",
  "payload": {}
}
```

## Agent turn payload (public fields)

| Field | Visibility |
|-------|------------|
| model | public (log/spectator) |
| player_id | public |
| role | private (agent + god log) |
| speech | public |
| demeanor | public |
| action | depends on rule timing |

Reserved for Phase 7: replay, evaluation metrics, leaderboard.
