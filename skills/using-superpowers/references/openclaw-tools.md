# OpenClaw 工具映射

其他平台（Claude Code、Codex、Gemini CLI）的技能引用不同工具名。遇到时查此表。

## 核心映射

| 外部平台工具 | OpenClaw 工具 |
|------------|--------------|
| `Skill` tool | `read`（读 SKILL.md） |
| `TodoWrite` | 写文件 `memory/YYYY-MM-DD.md` |
| `EnterPlanMode` | 对话中规划 或 `sessions_spawn` |
| `Bash` | `exec` |
| `Read` | `read` |
| `Write` | `write` |
| `Edit` | `edit` |
| `Task`（子代理） | `sessions_spawn` |
| `Glob` / `Grep` | `exec` + find/grep |
| `WebFetch` | `exec` + curl 或 `camofox_navigate` |
| `WebSearch` | `exec` + 搜索命令 |

## 飞书专用工具

| 操作 | OpenClaw 工具 |
|------|--------------|
| 创建/查询文档 | `feishu_create_doc` / `feishu_fetch_doc` / `feishu_update_doc` |
| 多维表格 | `feishu_bitable_app` / `feishu_bitable_app_table` / `feishu_bitable_app_table_field` / `feishu_bitable_app_table_record` |
| 日历/日程 | `feishu_calendar_calendar` / `feishu_calendar_event` |
| 消息 | `feishu_im_user_message` / `message` |
| 搜索用户 | `feishu_search_user` |

## 子代理调度

Claude Code 的 `Task` tool 在 OpenClaw 中用 `sessions_spawn`：
- `mode: "run"` — 一次性任务
- `mode: "session"` — 持久会话
- `runtime: "acp"` — 编码代理会话
