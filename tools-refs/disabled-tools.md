# 禁用工具清单

## 飞书插件工具（可按需开启）

### Task (任务)
- `feishu_task_task`
- `feishu_task_tasklist`
- `feishu_task_comment`
- `feishu_task_subtask`
- skill: `feishu-task`

### Base 视图
- `feishu_bitable_app_table_view`

### CCM 扩展
- `feishu_doc_comments`（文档评论）
- `feishu_doc_media`（文档媒体）
- `feishu_drive_file`（云空间文件）
- `feishu_wiki_space`（知识空间）
- `feishu_wiki_space_node`（知识库节点）
- `feishu_sheet`（电子表格）

## 开启方式
1. 工具：编辑 `openclaw.json`，从 `tools.deny` 数组中移除对应工具名
2. Skill：编辑 `openclaw.json`，将 `skills.entries` 中 `"feishu-task": { "enabled": false }` 改为 `true`
3. 执行 `sh scripts/restart.sh` 重启生效
