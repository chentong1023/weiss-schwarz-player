# weiss-schwarz-player

一个面向中文对话的黑白双翼（Weiß Schwarz）牌手技能。它能从零讲解规则，为一份完整牌表写打法，也能通过游戏提供的 MCP 对战服务操作一个玩家席位。[技能入口](SKILL.md)

## 开始使用

同一刀正攻，为什么对手受了 2 点，自己攻击的角色却倒置了？入门用双方各自翻的牌走完这刀，并解释换牌、升级、颜色、库存、回合与重洗。[基本规则与正攻算例](references/basic-rules.md)

在 Codex 项目中使用时，将含有 `SKILL.md`、`agents/`、`references/`、`scripts/` 的技能目录放到该项目的 `.agents/skills/weiss-schwarz-player/`。也可以让能读取本地文件的模型直接阅读本仓库的 `SKILL.md`。分析牌表只需要完整的 50 张清单。要实际出牌，从游戏网页「单人游戏 → 大语言模型 → MCP」复制服务器地址，把它作为 Streamable HTTP 服务接入客户端。

下面两条指令分别用于学规则和实战。

> 用 $weiss-schwarz-player 教我打一回合，从换牌讲到攻击伤害结算。

> 用 $weiss-schwarz-player 为这份 50 张牌表写打法，再用我提供的 MCP 席位码打到终局。

## 牌表与实战工具

每份打法的第一章都保存完整构筑，每次复用前逐卡核对官方卡号及张数。公主连接范例展示了怎样用一级联动补手、为三级斩杀留颜色和库存。[打法模板](references/deck-plans/_template.md) · [公主连接范例](references/deck-plans/priconne-kokkoro-pecorine.md)

有 Python 3.8 或更新版本时，可在本项目根目录执行以下命令。`my-deck.txt` 是本次导出的牌表，`state.json` 是 MCP 席位快照，`info.json` 是可见牌的卡文查询结果。两个脚本都只用 Python 标准库。[记牌与数潮方法](references/table-reading.md)

```sh
python3 scripts/match_deck.py references/deck-plans/priconne-kokkoro-pecorine.md my-deck.txt
python3 scripts/count_cx.py state.json info.json --damage 2
```
