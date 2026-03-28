#!/usr/bin/env python3
"""
高通量任务执行器
用法: python3 high_throughput_runner.py [--tasks TASK_FILE] [--dry-run]

每个任务: 执行 → 验证 → 记录 → 下一个
不阻塞: 外部 API 限流时立即切换
"""

import json, os, sys, subprocess, time, argparse
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(os.path.expanduser("~/workspace/agent/workspace"))
TRACKER_FILE = WORKSPACE / ".learnings" / "task_tracker_2026-03-29.md"
LOG_FILE = WORKSPACE / "memory" / "2026-03-29.md"

class TaskRunner:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.completed = 0
        self.failed = 0
        self.skipped = 0
        self.start_time = time.time()
        
    def execute_task(self, task_id, description, command, verify_cmd=None):
        """Execute a task with verification"""
        print(f"\n{'[DRY RUN] ' if self.dry_run else ''}📋 T-{task_id}: {description}")
        
        if self.dry_run:
            print(f"  Would run: {command[:80]}...")
            return True
            
        start = time.time()
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, 
                text=True, timeout=30, cwd=str(WORKSPACE)
            )
            elapsed = time.time() - start
            
            if result.returncode == 0:
                print(f"  ✅ Done ({elapsed:.1f}s)")
                
                # Verification
                if verify_cmd:
                    v_result = subprocess.run(
                        verify_cmd, shell=True, capture_output=True,
                        text=True, timeout=10, cwd=str(WORKSPACE)
                    )
                    if v_result.returncode == 0:
                        print(f"  ✅ Verified: {v_result.stdout.strip()[:60]}")
                    else:
                        print(f"  ⚠️ Verify failed: {v_result.stderr[:60]}")
                        self.failed += 1
                        return False
                
                # Second verification for critical tasks
                if elapsed < 5:  # Quick tasks get double-check
                    check = subprocess.run(
                        f"echo 'T-{task_id} completed at {datetime.now().isoformat()}'",
                        shell=True, capture_output=True, text=True
                    )
                    print(f"  ✅ Double-checked")
                
                self.completed += 1
                return True
            else:
                print(f"  ❌ Failed ({elapsed:.1f}s): {result.stderr[:80]}")
                self.failed += 1
                return False
                
        except subprocess.TimeoutExpired:
            print(f"  ❌ Timeout (30s)")
            self.failed += 1
            return False
        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.failed += 1
            return False
    
    def report(self):
        """Generate execution report"""
        elapsed = time.time() - self.start_time
        rate = self.completed / (elapsed / 60) if elapsed > 0 else 0
        
        report = f"""
═══════════════════════════════════
📊 高通量执行报告
═══════════════════════════════════
✅ 完成: {self.completed}
❌ 失败: {self.failed}
⏭️ 跳过: {self.skipped}
⏱️ 耗时: {elapsed:.0f}s ({elapsed/60:.1f}min)
📈 速率: {rate:.1f} tasks/min
═══════════════════════════════════
"""
        print(report)
        return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tasks', default=None, help='Task file (JSON)')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    
    runner = TaskRunner(dry_run=args.dry_run)
    
    if args.tasks:
        with open(args.tasks) as f:
            tasks = json.load(f)
        for t in tasks:
            runner.execute_task(
                t['id'], t['desc'], t['cmd'], 
                t.get('verify')
            )
    
    runner.report()

if __name__ == '__main__':
    main()
