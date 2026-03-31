---
name: prompts-chat
description: |
  从 prompts.chat (Awesome ChatGPT Prompts, 155K stars) 精选的 23 个高质量 prompt，按类别组织，可直接用于角色扮演和任务增强。触发词：prompt、提示词、角色扮演、用什么prompt、怎么问AI。
---

# Prompts Chat — 精选 Prompt 库

来源：[prompts.chat](https://github.com/f/prompts.chat) (155K stars, CC0-1.0)
规模：从 579 个 prompt 中精选 23 个，按 6 个类别组织

## 使用方式

### 方式 1：直接调用
收到用户请求时，匹配最相关的 prompt，参考其角色定义来增强响应。

### 方式 2：通过脚本搜索
```bash
python3 skills/prompts-chat/use.py search "code review"
python3 skills/prompts-chat/use.py list developer
python3 skills/prompts-chat/use.py show Code\ Reviewer
```

### 方式 3：集成到技能系统
每个 prompt 可以被视为一个微技能。当检测到相关意图时自动匹配。

## 类别速查

### 🔧 Developer（6 个）
| Act | 描述 |
|-----|------|
| Linux Terminal | 模拟 Linux 终端，回复终端输出 |
| JavaScript Console | 模拟 JS 控制台 |
| Python Interpreter | 模拟 Python 解释器，执行代码 |
| SQL Terminal | 模拟 SQL 终端，执行查询 |
| RegEx Generator | 生成正则表达式 |
| Code Reviewer | 代码审查，给出改进建议 |

### ✍️ Writing（5 个）
| Act | 描述 |
|-----|------|
| Essay Writer | 论文写作，研究+论证+写作 |
| Tech Writer | 技术文档写作 |
| Proofreader | 校对拼写/语法/标点 |
| Cover Letter | 求职信写作 |
| AI Writing Tutor | AI 写作辅导，提升学生写作能力 |

### 📊 Analysis（3 个）
| Act | 描述 |
|-----|------|
| Data Analyst | 数据分析，洞察发现 |
| Financial Analyst | 金融分析，技术分析+宏观经济 |
| Algorithm Quick Guide | 算法概念快速解析 |

### 🎓 Learning（4 个）
| Act | 描述 |
|-----|------|
| Math Teacher | 数学概念讲解 |
| Socratic Method | 苏格拉底式提问，检验信念 |
| Educational Content Creator | 教育内容创作 |
| Study Planner | 学习计划生成 |

### 🤖 AI Tools（3 个）
| Act | 描述 |
|-----|------|
| Prompt Generator | 根据标题生成 prompt |
| ChatGPT Prompt Generator | 生成 ChatGPT prompt |
| Machine Learning Engineer | ML 概念讲解 |

### 💼 Business（2 个）
| Act | 描述 |
|-----|------|
| Product Manager | PRD 写作辅助 |
| Project Manager | 项目管理文档 |

## 数据结构

`prompts.json` 包含每个 prompt 的完整信息：
```json
{
  "id": "pc-001",
  "act": "Linux Terminal",
  "prompt": "I want you to act as a linux terminal...",
  "category": "developer",
  "type": "TEXT",
  "for_devs": true,
  "source": "prompts.chat",
  "license": "CC0-1.0"
}
```

## 常见误区

| 错误 | 正确 |
|------|------|
| 把 prompt 当作固定指令复制粘贴 | prompt 是角色定义，应根据上下文调整 |
| 一次用所有 prompt | 匹配当前任务最相关的 1 个 |
| 忽略 prompt 的约束条件 | prompt 中的"I want you to only reply"是重要约束 |

## 参考
1. [prompts.chat](https://github.com/f/prompts.chat) — 155K stars, CC0-1.0
2. [Hugging Face Dataset](https://huggingface.co/datasets/fka/prompts.chat) — Most liked dataset
3. 被 Forbes、Harvard、Columbia 引用，40+ 学术论文引用
