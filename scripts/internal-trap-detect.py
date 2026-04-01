# 内部→外部切换强制脚本 (2026-04-02)
# 用途: 心跳检查是否陷入"无限内部整改"模式
# 检测: 如果最近的 session 活动全是内部操作且持续 >2 轮 → 标记需切换

import os, re, json
from datetime import datetime, timedelta

BASE = "/home/gem/workspace/agent/workspace"
MEMORY_LOG = os.path.join(BASE, "memory", "2026-04-02.md")
ALERT_FILE = os.path.join(BASE, ".learnings", "internal_trap_alert.json")

def check():
    """检查是否陷入内部整改循环"""
    # 简单方法：检查今日 memory log 中"内部整改" vs "外部落地"的关键词频率
    if not os.path.isfile(MEMORY_LOG):
        return True  # 无日志 = 无问题
    
    with open(MEMORY_LOG) as f:
        content = f.read()
    
    internal_keywords = ['审计', '清理', '校验', 'checksum', '大盘', '防篡改', '瘦身', '红线']
    external_keywords = ['外部', '落地', '适应', '工单', 'Resource', 'NeuronFS', 'everything']
    
    internal_count = sum(content.count(kw) for kw in internal_keywords)
    external_count = sum(content.count(kw) for kw in external_keywords)
    
    ratio = internal_count / max(external_count, 1)
    
    if ratio > 5:
        alert = {
            "detected": datetime.now().isoformat(),
            "ratio": ratio,
            "internal_mentions": internal_count,
            "external_mentions": external_count,
            "message": "内部整改/外部进化 = {:.1f}:1，极度失衡。强制切换到外部资源落地。".format(ratio)
        }
        os.makedirs(os.path.dirname(ALERT_FILE), exist_ok=True)
        with open(ALERT_FILE, 'w') as f:
            json.dump(alert, f, indent=2, ensure_ascii=False)
        
        print(f"🔴 内部陷阱告警: 内部/外部 = {ratio:.1f}:1")
        print(f"   内部提及: {internal_count}, 外部提及: {external_count}")
        print(f"   建议: 立即停止内部整改，切换到外部进化")
        return False
    else:
        # Clear alert if exists
        if os.path.isfile(ALERT_FILE):
            os.remove(ALERT_FILE)
        print(f"✅ 内外平衡正常: 内部/外部 = {ratio:.1f}:1")
        return True

if __name__ == "__main__":
    import sys
    ok = check()
    sys.exit(0 if ok else 1)
