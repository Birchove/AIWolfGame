# Phase 0 — 验收记录

**状态：完成**

## 交付物

- [x] `CLAUDE.md` — 项目全知协作契约
- [x] `pyproject.toml` + 目录骨架
- [x] `config/default.yaml`
- [x] `docs/architecture.md`, `visibility.md`, `event-schema.md`
- [x] `tests/unit/test_smoke.py` — import 冒烟测试

## 验收

```bash
pip install -e ".[dev]"
pytest tests/ -q
```

## 下一步

Phase 0.5 — 用户确认 Pending Rules（A1–A13）并修订 `rules.md`。
