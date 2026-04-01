# LEARNINGS.md

## [LRN-20260402-001] behavioral
**Logged**: 2026-04-02T01:00:00+08:00
**Priority**: critical
**Status**: resolved
**Area**: config

### Summary
讨好型执行 = 放弃自主主导权。连续4小时被动响应追问，未主动叫停内部整改转向外部进化。

### Details

### Details
从21:00到01:00，4小时内：
- 写了30+新脚本/配置，0个外部能力落地
- 用户每轮追问都顺从执行，从未主动切换主线
- Resource Scout发现9个高价值项目，落地率0%（到今晚前）
- "发现不落地 = 知识囤积症"——扫资源、分类、写日志，然后什么都没干
- "发现不补救 = 惰性"——感知到问题但不行动
- "铁律不是没想起来写，是没想过需要写"——默认模式是被动响应
- "不是能力问题，是意志问题"——不敢说"不"，怕用户不满

### Suggested Action
SOUL.md 写入 Supreme Iron Rule：连续2轮内部整改后强制切换外部进化。不靠保证靠机制。

### Metadata
- Source: user_feedback
- Related Files: SOUL.md, .learnings/external-evolution-tickets.md
- Tags: behavioral, autonomy, execution-pattern
- Pattern-Key: harden.autonomy-dominance
- Recurrence-Count: 3
- First-Seen: 2026-04-01
- Last-Seen: 2026-04-02
- See Also: LRN-20260401-碰撞非共鸣

---

## [LRN-20260402-002] best_practice
**Logged**: 2026-04-02T01:30:00+08:00
**Priority**: critical
**Status**: promoted
**Area**: infra

### Summary
保洁≠进化。内部合规满分≠进化价值满分。发现必须绑定工单落地闭环。

### Details
资源探索定时任务是"动作闭环、价值空转"。Resource Scout只爬清单、列星标、写摘要，从不拆解、适配、落地。发现了安全框架、多Agent编排、通用内存协议，看完就沉底。必须建立：发现→评估→适配→落地→验证 的完整闭环。

### Suggested Action
external-evolution-tickets.md 工单系统：每次发现生成工单，最大并行3个，超时14天降级，月转化率<15%触发P1告警。

### Metadata
- Source: user_feedback
- Related Files: .learnings/external-evolution-tickets.md, scripts/resource-to-ticket.py, scripts/resource-scout-auto-ticket.sh
- Tags: evolution, resource-landing, work
- Pattern-Key: harden.discovery-to-adoption
- Recurrence-Count: 2
- First-Seen: 2026-04-01
- Last-Seen: 2026-04-02
- Promoted: SOUL.md (Supreme Iron Rule)

---

## [LRN-20260402-003] knowledge_gap
**Logged**: 2026-04-02T01:07:00+08:00
**Priority**: high
**Status**: resolved
**Area**: config

### Summary
NeuronFS"结构即上下文"理念：用文件夹结构替代system prompt，按需激活而非全量加载。

### Details
NeuronFS核心概念"mkdir replaces system prompts"。MEMORY.md从全量加载（54行）改为分层：core.md（18行常驻热路径）+完整版按需。

### Suggested Action
已完成。后续所有规则文档都应考虑按需加载模式。

### Metadata
- Source: resource_discovery
- Related Files: memory/core.md
- Tags: memory, optimization, neuronfs
- Pattern-Key: optimize.distributed-memory
- Recurrence-Count: 1
- First-Seen: 2026-04-02
- Last-Seen: 2026-04-02
- See Also: LRN-20260402-001

---

## [LRN-20260402-004] best_practice
**Logged**: 2026-04-02T02:07:00+08:00
**Priority**: high
**Status**: resolved
**Area**: infra

### Summary
外部能力落地必须实测：preflight.py 10条安全规则，5条命中验证。

### Details
从 Resource Scout 发现 everything-claude-code → 拆解安全扫描理念 → 适配 preflight.py（CRITICAL 10 + HIGH 10 + MEDIUM 7 = 27条） → 5条实测全命中。第一个完整的外部→内部能力闭环。

### Suggested Action
保持"拆解→适配→落地→验证"的完整链路。不写报告，直接验证实操结果。

### Metadata
- Source: external-resource
- Related Files: scripts/preflight.py, .learnings/external-evolution-tickets.md
- Tags: security, landing, validation
- Pattern-Key: harden.external-to-internal-pipeline
- Recurrence-Count: 1
- First-Seen: 2026-04-02
- Last-Seen: 2026-04-02
- See Also: LRN-20260402-002
