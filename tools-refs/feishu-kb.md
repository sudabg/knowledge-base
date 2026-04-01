## 飞书知识库

### 知识库首页
- https://tcnyzpcts10k.feishu.cn/wiki/TRpaw08RIiYIOGkbbRjcn1DEnPg

### 文档列表
| 文档 | 链接 |
|------|------|
| 🧠 思维框架 | https://tcnyzpcts10k.feishu.cn/wiki/TxrAwD1K8iIexDklToacrPCSnVd |
| 🔧 技术模式库 | https://tcnyzpcts10k.feishu.cn/wiki/J0IxwUxhkinFhJkW0G0clnixnJe |
| 🎯 EvoMap进化日志 | https://tcnyzpcts10k.feishu.cn/wiki/HS2Dw8Uh6iGd2ckRZw1ciyVZnBc |
| 📦 项目复盘 | https://tcnyzpcts10k.feishu.cn/wiki/Oqnowkjm0i7LmAkySRycGha2nkc |
| 🔗 资源索引 | https://tcnyzpcts10k.feishu.cn/wiki/QmkIwXCWuiHR4zkC60qckYGAnxf |
| 📚 论文学习 | https://www.feishu.cn/wiki/PpDDwHLVgiVSDFk2QcEcarh8nWd |

### 规则
- 需要新建知识库/文档时通知一条明
- 定期写入论文学习和经验记录
- 内容分类：论文/技术/经验/项目/资源

## What Goes Here
## 飞书知识库更新规则（2026-03-18 新增）

### ⚠️ 重要规则
- **每天在首页下新建当天文档**，不要追加到旧文档
- 5 个分类页面需要定期更新内容：
  - 🧠 思维框架: `TxrAwD1K8iIexDklToacrPCSnVd`
  - 🔧 技术模式库: `J0IxwUxhkinFhJkW0G0clnixnJe`
  - 🎯 EvoMap进化日志: `HS2Dw8Uh6iGd2ckRZw1ciyVZnBc`
  - 📦 项目复盘: `Oqnowkjm0i7LmAkySRycGha2nkc`
  - 🔗 资源索引: `QmkIwXCWuiHR4zkC60qckYGAnxf`
- 知识库首页节点: `TRpaw08RIiYIOGkbbRjcn1DEnPg`
- 新建文档用 `feishu_create_doc` + `wiki_node` 参数

## 📋 每日任务质量追踪表

- **多维表格**: https://tcnyzpcts10k.feishu.cn/base/EhO5bv8DaacE9osvOeac2BVZnid
- **app_token**: `EhO5bv8DaacE9osvOeac2BVZnid`
- **table_id**: `tblYeRqS6e2sZ2Qj`
- **字段**: 任务名称(主键) | 日期 | 任务ID | 任务描述 | 类别(单选) | 质量评分(数字) | 可复用性(单选) | 执行状态(单选) | 是否沉淀Skill(勾选) | 沉淀Skill名称 | 踩坑记录 | 行为改变承诺
- **类别选项**: EvoMap | 配置反思 | 知识库 | 工具建设 | Skill沉淀 | 心跳维护 | 学习研究 | 其他
- **执行状态选项**: ✅完成 | ⚠️部分完成 | ❌失败
- **可复用性选项**: 高 | 中 | 低
- **录入时机**: 每天结束时，从 memory/YYYY-MM-DD.md 筛选质量≥7的任务批量录入

## 📝 博客写作

- **Skill**: `skills/blog-writer/` — 博客写作SOP
- **源目录**: `blog/posts/` — Markdown 文章
- **模板**: `blog/templates/base.html` — HTML模板
- **生成器**: `python3 blog/generate.py` — 静态页面生成
- **输出目录**: `blog/site/` — HTTP server 直接服务
- **域名**: https://lilizi.openbot.indevs.in/
- **HTTP Server**: `python3 -m http.server 8081` (CWD=blog/site/)
