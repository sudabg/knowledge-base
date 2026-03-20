# Resource Tracker — 看板写入规范

## 飞书多维表格
- **链接**: https://tcnyzpcts10k.feishu.cn/base/Z2lqb8s6waIQi7s90BdcV64SnGh
- **app_token**: Z2lqb8s6waIQi7s90BdcV64SnGh
- **table_id**: tblzAozxbRKUjiIX

## 字段
- 资源名称 (text)
- 链接 (url)
- 分类 (single_select): 进化框架/Agent框架/记忆系统/推理/提示工程/评估/安全/开发工具/学习资源/基础设施
- ⭐星标 (number)
- 发现来源 (single_select): GitHub搜索/HN/arXiv/技术博客/用户分享/自建项目
- 置信度 (single_select): high/medium/low
- 状态 (single_select): 待验证/已验证/已收录/已废弃
- 为什么有用 (text)
- 发现日期 (datetime, ms timestamp)
- 已汇报 (checkbox)

## 写入流程
1. 资源探索完成后，用 feishu_bitable_app_table_record batch_create 写入
2. 每条记录必填：资源名称、分类、发现来源、为什么有用、发现日期
3. 如果已汇报给用户，勾选"已汇报"
4. 状态默认"待验证"，验证通过后改为"已验证"

## Cron 任务
- 每6小时自动探索 → 写入看板 → 汇报给用户
- 任务ID: 22afeb2a-e96f-4fe2-9058-0b444bfc5388
