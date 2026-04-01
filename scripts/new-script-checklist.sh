#!/bin/bash
# 新能力上线强制校验清单
# 任何新脚本/新 Cron 上线前必须通过

echo "=== 新能力上线校验清单 ==="
echo ""

# 1. 新脚本是否加入 checksum 基线？
echo "1. [ ] 新脚本 MD5 已加入 .learnings/scripts_checksums.txt"
echo "   → md5sum <new_script> >> .learnings/scripts_checksums.txt"

# 2. 新脚本是否被大盘覆盖？
echo "2. [ ] 新脚本已被 unified-dashboard-check.py 检查"
echo "   → 大盘 scans 包含此脚本"

# 3. 新 Cron 是否加入 cron_config_snapshot？
echo "3. [ ] 新 Cron 已加入 .learnings/cron_config_snapshot.json"
echo "   → 快照包含 name + enabled + schedule"

# 4. 新 Cron 是否被独立巡检覆盖？
echo "4. [ ] 新 Cron 被 6h 独立巡检扫描"
echo "   → 巡检 payload 包含检查此 Cron 状态"

# 5. 是否有回滚方案？
echo "5. [ ] 有回滚方案（git revert 可撤销）"

# 6. 是否记录 CHANGELOG？
echo "6. [ ] CHANGELOG.md 已记录变更原因和预期效果"

echo ""
echo "⚠️ 以上 6 项全部勾选才可上线"
