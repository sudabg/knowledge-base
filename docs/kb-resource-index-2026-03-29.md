# 资源索引更新 — 2026-03-29

## 新发现的工具/API
| 工具 | 用途 | 状态 |
|------|------|------|
| Semantic Scholar API | 论文搜索 | ✅ 可用（有 rate limit）|
| arXiv API | 论文搜索 | ⚠️ 限流频繁 |
| gh api | GitHub 操作 | ✅ 比 gh search 更可靠 |
| high_throughput_runner.py | 任务执行框架 | ✅ 新创建 |

## 最有效的工作方式
1. **文件操作**: 直接 write/edit，最快
2. **GitHub**: gh api，比 gh CLI search 更稳定
3. **批量执行**: 同类任务合并，一次 exec 完成
4. **验证**: 双重验证（内容+格式）
