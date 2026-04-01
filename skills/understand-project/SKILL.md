---
name: understand-project
description: 深度分析任何代码项目，生成知识图谱、架构层、依赖关系图。触发词：分析项目、understand、代码分析、项目结构、架构分析、代码库分析
version: 1.0.0
metadata:
  tags: [code-analysis, knowledge-graph, architecture, understanding]
  related_skills: [browser-automation, dev-rigor]
---

# /understand-project

深度分析代码项目，生成完整的知识图谱，包括：
- 文件清单和语言检测
- 函数/类/节点提取
- 依赖关系（imports/calls）
- 架构层识别
- 关键文件排名

## 触发条件

当用户提到以下关键词时自动触发：
- `分析项目` / `analyze project`
- `understand` / `/understand`
- `代码分析` / `code analysis`
- `项目结构` / `project structure`
- `架构分析` / `architecture analysis`
- `代码库分析` / `codebase analysis`
- `理解代码` / `understand code`
- `知识图谱` / `knowledge graph`

## 使用方法

### 方法 1：分析当前目录
```bash
# 在项目目录下执行
python3 ~/.openclaw/skills/understand-project/run.py
```

### 方法 2：分析指定目录
```bash
python3 ~/.openclaw/skills/understand-project/run.py /path/to/project
```

### 方法 3：分析 GitHub 仓库
```bash
# 先克隆，再分析
git clone https://github.com/user/repo.git /tmp/repo
python3 ~/.openclaw/skills/understand-project/run.py /tmp/repo
```

## 输出文件

分析完成后，在项目目录下生成：
```
.understand-anything/
├── scan-result.json          # 文件扫描结果
├── knowledge-graph.json      # 知识图谱（节点+边）
├── analysis-report.txt       # 人类可读报告
└── meta.json                 # 元数据（时间、commit hash）
```

## 输出内容

### 1. 文件扫描（Phase 1）
- 文件总数和分类（code/config/docs/script/infra）
- 语言检测和代码行数统计
- 框架检测
- 复杂度评估

### 2. 知识图谱（Phase 2）
- **节点类型**：file, function, class, config, document, module
- **边类型**：contains, imports, calls, depends_on
- **节点数量**：通常 1000-10000 个
- **边数量**：通常 1000-10000 条

### 3. 架构层（Phase 3）
- 按目录/功能自动分层
- 每层包含的节点数
- 层间依赖关系

### 4. 关键指标
- 导入最多的文件（最复杂）
- 被导入最多的文件（最核心）
- 代码行数 Top 10
- 文件类别分布

## 分析流程

```
Phase 0: 预检
  ├── 检查项目目录是否存在
  ├── 获取 git commit hash
  └── 读取 README.md

Phase 1: 扫描
  ├── 发现所有文件（git ls-files 或 find）
  ├── 排除非源码文件（node_modules, .git, __pycache__）
  ├── 检测语言和框架
  └── 输出 scan-result.json

Phase 2: 分析
  ├── Python 文件：提取 imports, functions, classes
  ├── Markdown 文件：提取标题和摘要
  ├── 配置文件：标记为 config 节点
  ├── 创建 contains 边（文件→函数/类）
  ├── 创建 imports 边（文件→文件）
  └── 输出 knowledge-graph.json

Phase 3: 架构层
  ├── 按目录分组（agent/, tools/, gateway/, ...）
  ├── 创建架构层
  └── 输出带层的知识图谱

Phase 4: 报告
  ├── 生成人类可读摘要
  ├── 关键文件排名
  └── 输出 analysis-report.txt
```

## 示例输出

### 完整分析（默认）
```
📊 项目: hermes-agent
============================================================
📁 文件总数: 1,207
🔤 主要语言: python, markdown, json, shell, css
🔧 框架: Node.js, Python
📈 复杂度: high

🕸️ 知识图谱
------------------------------------------------------------
  节点总数: 5,886
  边总数: 6,050

📦 节点类型
------------------------------------------------------------
  function: 2,882
  class: 1,797
  file: 734
  document: 424
  config: 49

🔗 边类型
------------------------------------------------------------
  contains: 4,679
  imports: 1,371

🏛️ 架构层
------------------------------------------------------------
  Agent Core: 200 个节点
  Tools: 200 个节点
  Gateway: 200 个节点
  CLI: 200 个节点
  Scheduler: 34 个节点
  Environments: 92 个节点
  ACP Adapter: 32 个节点
  Tests: 200 个节点
  Root: 100 个节点

📊 导入最多的文件 (Top 5)
------------------------------------------------------------
  file:gateway/run.py: 60 个导入
  file:cli.py: 48 个导入
  file:run_agent.py: 35 个导入

📊 被导入最多的文件 (Top 5)
------------------------------------------------------------
  file:gateway/config.py: 99 次被导入
  file:hermes_cli/config.py: 71 次被导入
  file:gateway/platforms/base.py: 62 次被导入
```

### 快速分析（--no-functions）
```
节点总数: 1,207
边总数: 1,371
节点类型: file: 734, document: 424, config: 49
```

## 高级用法

### 自定义排除规则
编辑 `run.py` 中的 `EXCLUDE_DIRS` 和 `EXCLUDE_EXTS`。

### 增量分析
如果项目已分析过，只分析变更的文件：
```bash
python3 ~/.openclaw/skills/understand-project/run.py --incremental
```

### 导出为其他格式
```bash
# 导出为 GraphML（可用 Gephi 打开）
python3 ~/.openclaw/skills/understand-project/export.py --format graphml

# 导出为 Markdown 报告
python3 ~/.openclaw/skills/understand-project/export.py --format markdown
```

## 与原版 Understand-Anything 的区别

| 特性 | 原版 | 本 Skill |
|------|------|----------|
| 安装复杂度 | 需要克隆仓库+创建符号链接 | 已集成，无需额外安装 |
| 执行方式 | 需要 OpenClaw skill 系统 | 直接运行 Python 脚本 |
| 分析深度 | 7 阶段完整流水线 | 4 阶段简化版（够用） |
| 子代理支持 | 是（并行分析） | 否（单进程） |
| 输出格式 | JSON + 仪表盘 | JSON + 文本报告 |
| 触发词 | `/understand` | 多个中文/英文触发词 |

## 注意事项

1. **大项目**：>200 文件时分析可能较慢（1-5 分钟）
2. **二进制文件**：自动排除图片、视频、压缩包等
3. **非 Git 项目**：使用 find 代替 git ls-files，可能较慢
4. **编码问题**：使用 UTF-8，遇到乱码自动跳过

## 常见问题

**Q: 分析失败怎么办？**
A: 检查项目目录是否存在，是否有读取权限。

**Q: 如何提高分析速度？**
A: 使用 `--incremental` 只分析变更文件。

**Q: 可以分析远程仓库吗？**
A: 先 `git clone`，再分析本地目录。

**Q: 输出文件太大怎么办？**
A: 使用 `--no-functions` 不提取函数节点，只保留文件级节点。
