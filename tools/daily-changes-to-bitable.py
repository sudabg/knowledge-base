#!/usr/bin/env python3
"""Daily Git Changes → Feishu Bitable
用 git log 提取今日变更，写入资源发现看板
"""
import subprocess, json, datetime, urllib.request, os, sys

# 配置
APP_TOKEN = "Z2lqb8s6waIQi7s90BdcV64SnGh"
TABLE_ID = "tblzAozxbRKUjiIX"
WORKSPACE = "/home/gem/workspace/agent/workspace"

def get_today_changes():
    """获取今日 git 变更摘要"""
    os.chdir(WORKSPACE)
    
    # 获取今日commits
    today = datetime.date.today().isoformat()
    log_cmd = f'git log --since="{today} 00:00:00" --pretty=format:"%h|%s|%an" --stat'
    result = subprocess.run(log_cmd, shell=True, capture_output=True, text=True)
    
    if not result.stdout.strip():
        return []
    
    commits = []
    current = {}
    for line in result.stdout.split('\n'):
        if '|' in line and not line.startswith(' '):
            if current:
                commits.append(current)
            parts = line.strip().split('|', 2)
            current = {"hash": parts[0], "subject": parts[1], "author": parts[2] if len(parts)>2 else "", "files": [], "stats": ""}
        elif line.strip():
            current["stats"] = line.strip()
            if '|' in line:
                fname = line.split('|')[0].strip()
                current["files"].append(fname)
    if current:
        commits.append(current)
    
    return commits

def get_file_diff_summary():
    """获取今日文件变更统计"""
    os.chdir(WORKSPACE)
    today = datetime.date.today().isoformat()
    cmd = f'git log --since="{today} 00:00:00" --numstat --pretty=format:""'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    file_stats = {}
    for line in result.stdout.split('\n'):
        if not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) == 3:
            added, deleted, fname = parts
            if fname not in file_stats:
                file_stats[fname] = {"added": 0, "deleted": 0}
            try:
                file_stats[fname]["added"] += int(added) if added != '-' else 0
                file_stats[fname]["deleted"] += int(deleted) if deleted != '-' else 0
            except ValueError:
                pass
    
    return file_stats

def write_to_bitable(records):
    """写入飞书多维表格（需要通过feishu工具调用，这里生成JSON）"""
    output_path = f"/tmp/daily-changes-{datetime.date.today().isoformat()}.json"
    with open(output_path, 'w') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"✅ Records written to {output_path}")
    return output_path

def main():
    print(f"📊 Daily Changes Report — {datetime.date.today().isoformat()}")
    print("=" * 50)
    
    commits = get_today_changes()
    file_stats = get_file_diff_summary()
    
    if not commits:
        print("No commits today yet.")
        return
    
    print(f"\n📝 Commits: {len(commits)}")
    total_added = sum(s["added"] for s in file_stats.values())
    total_deleted = sum(s["deleted"] for s in file_stats.values())
    print(f"📊 Changes: +{total_added} -{total_deleted} across {len(file_stats)} files")
    
    print("\n📋 Commit Summary:")
    for c in commits:
        print(f"  {c['hash']} {c['subject']}")
        print(f"    Files: {', '.join(c['files'][:5])}")
        if len(c['files']) > 5:
            print(f"    ...and {len(c['files'])-5} more")
    
    # 生成看板记录
    records = []
    today_ts = int(datetime.datetime.now().timestamp() * 1000)
    
    # 按文件类型分组
    categories = {
        "skills": [], "awesome-openclaw": [], "self-model": [],
        "autoresearch": [], "dashboard": [], "other": []
    }
    for fname, stats in file_stats.items():
        placed = False
        for cat in ["skills", "awesome-openclaw", "self-model", "autoresearch", "dashboard"]:
            if cat in fname:
                categories[cat].append(f"{fname} (+{stats['added']}/-{stats['deleted']})")
                placed = True
                break
        if not placed:
            categories["other"].append(f"{fname} (+{stats['added']}/-{stats['deleted']})")
    
    for cat, files in categories.items():
        if files:
            records.append({
                "资源名称": f"[{datetime.date.today().isoformat()}] {cat} 变更",
                "分类": "开发工具" if cat in ["autoresearch", "dashboard"] else "学习资源",
                "发现来源": "Git变更",
                "置信度": "high",
                "状态": "已验证",
                "为什么有用": f"{len(files)}个文件变更: " + "; ".join(files[:3]),
                "发现日期": today_ts,
                "已汇报": False
            })
    
    # 写入文件
    path = write_to_bitable(records)
    
    print(f"\n✅ Generated {len(records)} bitable records")
    print(f"   Run feishu_bitable_app_table_record batch_create to sync")

if __name__ == "__main__":
    main()
