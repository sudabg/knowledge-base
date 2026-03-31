#!/usr/bin/env python3
"""
Harness Engineering - 初始化脚本
在项目目录下创建 .harness 目录和初始文件
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

def init_harness(project_dir):
    """初始化 Harness 结构"""
    project = Path(project_dir)
    harness_dir = project / ".harness"
    
    print(f"🔧 初始化 Harness: {project.name}")
    
    # 创建 .harness 目录
    harness_dir.mkdir(exist_ok=True)
    
    # 1. 创建 progress.txt
    progress_path = harness_dir / "progress.txt"
    if not progress_path.exists():
        progress_content = f"""# Project Progress Log
# 项目: {project.name}
# 初始化时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Session 1 ({datetime.now().strftime('%Y-%m-%d %H:%M')})
- 🔧 Harness 初始化完成
- 📝 下一步：分析项目结构，创建功能清单
"""
        progress_path.write_text(progress_content, encoding='utf-8')
        print(f"  ✅ 创建 progress.txt")
    else:
        print(f"  ⏭️ progress.txt 已存在")
    
    # 2. 创建 features.json
    features_path = harness_dir / "features.json"
    if not features_path.exists():
        features = {
            "projectName": project.name,
            "createdAt": datetime.now().isoformat(),
            "features": []
        }
        features_path.write_text(json.dumps(features, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f"  ✅ 创建 features.json")
    else:
        print(f"  ⏭️ features.json 已存在")
    
    # 3. 创建 config.json
    config_path = harness_dir / "config.json"
    if not config_path.exists():
        config = {
            "version": "1.0.0",
            "projectRoot": str(project),
            "harnessDir": str(harness_dir),
            "createdAt": datetime.now().isoformat(),
            "sessions": 1,
            "lastSession": datetime.now().isoformat()
        }
        config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f"  ✅ 创建 config.json")
    else:
        print(f"  ⏭️ config.json 已存在")
    
    # 4. 创建 session log 目录
    sessions_dir = harness_dir / "sessions"
    sessions_dir.mkdir(exist_ok=True)
    print(f"  ✅ 创建 sessions/ 目录")
    
    print(f"\n✅ Harness 初始化完成!")
    print(f"  📁 Harness 目录: {harness_dir}")
    print(f"  📄 进度文件: {progress_path}")
    print(f"  📋 功能清单: {features_path}")
    print(f"  ⚙️ 配置文件: {config_path}")
    
    return harness_dir

def main():
    if len(sys.argv) > 1:
        project_dir = sys.argv[1]
    else:
        project_dir = os.getcwd()
    
    if not os.path.isdir(project_dir):
        print(f"❌ 目录不存在: {project_dir}")
        sys.exit(1)
    
    init_harness(project_dir)

if __name__ == '__main__':
    main()
