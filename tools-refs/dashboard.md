# Dashboard 参考

- 端口: 8888 (Python HTTP Server, 0.0.0.0:8888)
- 目录: `/home/gem/workspace/agent/workspace/dashboard`
- API: `/api/status`, `/api/node`, `/api/projects`, `/api/memory`
- 数据源: `docs/project-plans-YYYY-MM-DD.md`（不是 active.md！）
- 归档: `python3 dashboard/archive_completed.py`
- 规则: 项目 100% 时立即勾完所有 [x] → 运行归档 → 验证 P.md
