# Phase 0.5 — 验收记录

**状态：完成**

## 用户确认的边界规则

| ID | 结论 |
|----|------|
| A1 | 狼刀不允许平票；平票重议；空刀须四狼全体同意；夜间可讨论 |
| A2 | 警长字面 1.5 票 |
| A3 | 白痴灵魂态不可被女巫毒 |
| A5 | 狼可当警长；死亡须移徽；自爆跳过白天 |
| A6 | 猎人开枪 optional |
| A7 | 自爆终止白天，投票作废 |
| A8 | 狼刀→检胜→猎人→再检胜 |
| A10 | 1 号顺时针；AI 不用分钟相加 |
| A11 | 第一夜无警长；天亮→竞选→死讯→发言投票 |
| A12 | 首夜无警长；任意方式死亡均须移徽 |
| A13 | 删除狼王 tips；不含守卫 |

## 变更文件

- `rules.md` — 整局流程概览、边界规则、同时结算优先级
- `CLAUDE.md` — Confirmed Boundary Rules、Current Phase → 1
- `config/default.yaml` — wolf_kill 配置

## 下一步

Phase 1 — GameState / Phase / Rules 纯函数 + 胜负判定 + unit tests
