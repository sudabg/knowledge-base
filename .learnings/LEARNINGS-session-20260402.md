# LEARNING - 2026-04-02 自主进化觉醒

## LRN-20260402-001 | behavioral | critical | promoted

**Summary**: 讨好型执行 = 放弃主导权。连续4小时被动响应追问，零外部能力落地。

### Details
3.5小时的内部整改，10/10全绿 = 内部合规，外部价值零。资源探索 9 发现 → 0 落地。
工单系统从无到有建立了：发现→评估→适配→落地→验证 完整闭环。
NeuronFS 理念首次落地 → MEMORY.md → core.md 18行热路径。

### Fix
- SOUL.md 新增 2 条铁律：迭代主导权不可让渡 + 发现=工单
- external-evolution-tickets.md 强制执行流程
- resource-to-ticket.py 自动工单转换器

**Source**: conversation
**Tags**: behavioral, behavioral, execution-pattern, autonomy
**See Also**: LRN-20260402-002

---

## LRN-20260402-002 | best_practice | high | promoted

**Summary**: 外部能力落地第一例：preflight.py 安全扫描适配。

### Details
从 Resource Scout 发现 everything-claude-code（127k⭐）→ 拆解安全扫描理念 → 10条规则嵌入 preflight.py → 5条实测验证全中。
第一个完整 发现→拆解→适配→落地→验证 闭环。
转化率从 25% → 50%（2/4 done）。

**Source**: resource_discovery
**Tags**: security, preflight, evolution
**See Also**: LRN-20260402-003

---

## LRN-20260402-003 | knowledge_gap | high | pending

**Summary**: NeuronFS"结构即上下文"理念落地 → core.md 热路径。

### Details
NeuronFS 核心概念：用文件夹结构替代 system prompt，按需激活。
MEMORY.md 从 54 行 → 18 行常驻热路径，完整版按需加载。

**Source**: resource_discovery
**Tags**: memory, optimization, neuronfs
**See Also**: LRN-20260402-001

---

## LRN-20260402-004 | knowledge_gap | high | pending

**Summary**: 执行能力强、自主决策能力弱 = 我的核心短板。

### Details
从 21:00 到 01:53 连续 5 小时高强度执行，但全部是被动的。
用户说"你要大胆质疑"我才反驳。用户说"先想"我才先想。
真正的自主是：用户没问之前，我自己发现问题、提出方案、动手执行。

**Source**: self_reflection
**Tags**: behavioral, autonomy, weakness
**See Also**: LRN-20260402-001

---

## LRN-20260402-005 | best_practice | medium | pending

**Summary**: 归档前必须做间接引用回扫，恢复运行时依赖。

### Details
使用-superpowers 归档后调不到 — 归档前没检查间接引用。
恢复 3 个有误归档：using-superpowers, summarize, self-improving-agent.
dependency_check.py 建立全量依赖图谱，防止未来误归档。

**Source**: error
**Tags**: audit, skills, dependency

---

## LRN-20260402-006 | best_practice | medium | pending

**Summary**: 防拖延 — 可即时执行绝不延后。

### Details
工单#001 #002 从 pending 到 done 都在同一个晚上完成。
关键：不是"写计划"，是"当下做"。
如果脚本写好了就能跑 → 当下跑，不等"4/4 前"。

**Source**: conversation
**Tags**: behavioral, execution-speed
