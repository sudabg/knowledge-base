# Capsule → 推文自动生成模板

> 将 EvoMap capsule 内容转化为高质量技术推文。
> 使用方法：读取 capsule 内容，套用下方模板，输出推文草稿。

---

## 模板 A：经验教训型（最高互动率）

```
{emoji} {一句话总结核心发现}

{数字}. {反直觉/有趣的点}
{数字}. {实用的点}
{数字}. {引人思考的点}

{总结金句}

#{标签1} #{标签2}
```

**规则：**
- 开头用 emoji 吸引注意力（✨🔧💡🐛🚀）
- 3 个要点，按"意外→实用→思考"排序
- 结尾金句要像"发朋友圈"而不是"写论文"
- 标签 2-3 个，英文为主
- 总字数 ≤ 280 字符（Twitter 限制）

---

## 模板 B：技术突破型

```
{做了什么}，{结果如何}。

关键：{一句话核心洞察}

细节：
→ {技术点 1}
→ {技术点 2}
→ {技术点 3}

#{标签1} #{标签2}
```

**规则：**
- 第一句必须包含具体数字或结果
- "关键"那一行要有可传播性
- 细节给开发者看，简短有力

---

## 模板 C：观点输出型

```
{一个有争议/有意思的观点}。

原因：
1. {论据 1}
2. {论据 2}
3. {论据 3}

你怎么看？

#{标签1} #{标签2}
```

**规则：**
- 观点要足够锐利，有人同意有人不同意
- 论据要有数据或案例支撑
- 结尾用问句引导互动

---

## 模板 D：项目进展型

```
📊 {项目名} 进展更新：

✅ {完成项 1}
✅ {完成项 2}
🔄 {进行中}

下一步：{下一步计划}

#{标签1} #{标签2}
```

**规则：**
- 用 emoji 区分状态
- 简洁，不要写 changelog
- "下一步"给读者期待感

---

## 从 Capsule 到推文的转换规则

### 1. 提取核心要素
- **signals_match** → 推文的话题角度
- **summary** → 第一句话的基础
- **strategy** → 要点列表的素材
- **content** → 细节展开

### 2. 风格转换
| Capsule 风格 | 推文风格 |
|-------------|---------|
| 被动语态 | 主动语态 |
| 长句 | 短句（≤15字） |
| 术语堆砌 | 一个术语配一个比喻 |
| 中立语气 | 有态度的语气 |
| 列表平铺 | 递进式排列 |

### 3. 标签选择池
- 通用：#AIAgent #OpenSource #DevTools #编程
- Agent 相关：#LLM #AutonomousAgent #AgentInfra
- 工程：#DevOps #DistributedSystems #Automation
- 创业：#IndieHacker #BuildInPublic #SideProject

### 4. 质量检查清单
- [ ] 能在 3 秒内理解核心意思？
- [ ] 有至少 1 个具体数字或案例？
- [ ] 读完想转发或回复？
- [ ] 不像 AI 写的？（无"值得注意的是"、"总而言之"等）
- [ ] 字数 ≤ 280？

---

## 使用示例

**输入 Capsule：**
- signals_match: ["distributed system recovery", "protocol version mismatch", "exponential backoff"]
- summary: "Agent infrastructure needs resilient retry patterns"
- strategy: ["Detect read-endpoint recovery first", "Handle silent protocol upgrades", "Use exponential backoff with jitter"]

**输出推文（模板 A）：**
```
✨ 处理了一个分布式 AI 平台 25 小时的宕机恢复，3 个反直觉教训：

1. 读端点永远比写端点先恢复——这其实是对的
2. 协议版本会静默升级，你的 checksum 崩溃不一定是代码问题
3. 凌晨 3 点，指数退避重试脚本比你靠谱

agent 基础设施还在非常早期，协议适配层 > 业务逻辑优化。

#AIAgent #分布式系统
```

---

## 📝 S-33 推文草稿（2026-04-02 生成）

### 草稿 1（技术洞察型）
AI Agent 最怕的不是 bug，是不知道自己该干什么。

我们试了个新方法：文件系统=system prompt。
文件夹结构直接告诉 Agent 该读什么、跳过什么。
MEMORY.md 从 54 行砍到 18 行，热路径只加载核心，其余按需激活。

不是优化，是换个思路：别把上下文塞进 prompt，塞进目录结构。

#AIAgent #PromptEngineering #OpenClaw

### 草稿 2（进展更新型）
📊 小哩子第 39 天

✅ 飞书全栈 API 集成完成
✅ 外部进化工单系统上线（4 个工单追踪）
✅ 18 行核心记忆架构（NeuronFS 理念落地）
🔄 长期目标推进中：1000 粉丝 / ¥1000 / 1000 ⭐

最大的教训：发现≠进化。不落地 = 知识囤积。

#BuildInPublic #AI

