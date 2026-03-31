#!/usr/bin/env python3
"""
Harness Engineering - 恢复脚本
读取进度并显示当前状态
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

def read_progress(harness_dir):
    """读取进度文件"""
    progress_path = harness_dir / "progress.txt"
    if progress_path.exists():
        return progress_path.read_text(encoding='utf-8')
    return None

def read_features(harness_dir):
    """读取功能清单"""
    features_path = harness_dir / "features.json"
    if features_path.exists():
        with open(features_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def read_config(harness_dir):
    """读取配置"""
    config_path = harness_dir / "config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def update_session(harness_dir):
    """更新会话计数"""
    config_path = harness_dir / "config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        config['sessions'] = config.get('sessions', 0) + 1
        config['lastSession'] = datetime.now().isoformat()
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

def resume(project_dir=None):
    """恢复工作"""
    if project_dir is None:
        project_dir = os.getcwd()
    
    harness_dir = find_harness_dir(project_dir)
    if harness_dir is None:
        print("❌ 未找到 .harness 目录")
        print("  请先运行: python3 init.py")
        sys.exit(1)
    
    print("🔄 恢复 Harness 工作")
    print("=" * 60)
    
    # 读取配置
    config = read_config(harness_dir)
    if config:
        print(f"📁 项目: {Path(config.get('projectRoot', '')).name}")
        print(f"📊 会话数: {config.get('sessions', 0)}")
        print(f"⏰ 上次会话: {config.get('lastSession', 'Unknown')}")
    
    print()
    
    # 读取功能清单
    features = read_features(harness_dir)
    if features and features.get('features'):
        total = len(features['features'])
        completed = sum(1 for f in features['features'] if f.get('passes'))
        pending = total - completed
        
        print(f"📋 功能清单")
        print(f"  总计: {total}")
        print(f"  ✅ 完成: {completed}")
        print(f"  ⏳ 待完成: {pending}")
        
        # 显示待完成的功能
        if pending > 0:
            print(f"\n📝 待完成功能:")
            for i, feature in enumerate(features['features']):
                if not feature.get('passes'):
                    desc = feature.get('description', 'Unknown')
                    steps = feature.get('steps', [])
                    print(f"  {i+1}. {desc}")
                    if steps:
                        print(f"     步骤: {len(steps)} 个")
    else:
        print("📋 功能清单为空")
    
    print()
    
    # 读取进度
    progress = read_progress(harness_dir)
    if progress:
        # 只显示最后几行
        lines = progress.strip().split('\n')
        print("📄 最近进度:")
        for line in lines[-10:]:
            print(f"  {line}")
    
    print()
    print("=" * 60)
    
    # 更新会话
    update_session(harness_dir)
    
    return harness_dir

def main():
    project_dir = sys.argv[1] if len(sys.argv) > 1 else None
    resume(project_dir)

if __name__ == '__main__':
    main()
