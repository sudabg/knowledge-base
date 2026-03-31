#!/usr/bin/env python3
"""
Harness Engineering - 完成脚本
记录完成的任务
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

def find_harness_dir(start_dir):
    """查找 .harness 目录"""
    current = Path(start_dir)
    while current != current.parent:
        harness_dir = current / ".harness"
        if harness_dir.exists():
            return harness_dir
        current = current.parent
    return None

def append_progress(harness_dir, message):
    """追加进度记录"""
    progress_path = harness_dir / "progress.txt"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    with open(progress_path, 'a', encoding='utf-8') as f:
        f.write(f"\n- ✅ {message} ({timestamp})")

def update_feature(harness_dir, feature_desc, passes=True):
    """更新功能状态"""
    features_path = harness_dir / "features.json"
    
    if features_path.exists():
        with open(features_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for feature in data.get('features', []):
            if feature.get('description') == feature_desc:
                feature['passes'] = passes
                if passes:
                    feature['completedAt'] = datetime.now().isoformat()
                break
        
        with open(features_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
    return False

def complete_task(message, feature_desc=None, project_dir=None):
    """完成任务"""
    if project_dir is None:
        project_dir = os.getcwd()
    
    harness_dir = find_harness_dir(project_dir)
    if harness_dir is None:
        print("❌ 未找到 .harness 目录")
        sys.exit(1)
    
    print(f"✅ 标记任务完成: {message}")
    
    # 追加进度
    append_progress(harness_dir, message)
    print(f"  📄 已更新 progress.txt")
    
    # 更新功能状态
    if feature_desc:
        if update_feature(harness_dir, feature_desc, passes=True):
            print(f"  📋 已更新 features.json")
        else:
            print(f"  ⚠️ 未找到功能: {feature_desc}")
    
    print(f"\n✅ 完成!")

def main():
    if len(sys.argv) < 2:
        print("用法: python3 complete.py <message> [feature_description]")
        sys.exit(1)
    
    message = sys.argv[1]
    feature_desc = sys.argv[2] if len(sys.argv) > 2 else None
    
    complete_task(message, feature_desc)

if __name__ == '__main__':
    main()
