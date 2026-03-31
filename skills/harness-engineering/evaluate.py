#!/usr/bin/env python3
"""
Harness Engineering — 独立评估者工具 (Mode 11)
生成-评估解耦：用隔离 sub-agent 对抗自评偏差

用法:
  # 评估文件/项目
  python3 evaluate.py --target /path/to/artifact --spec "功能要求..."
  
  # 评估任务描述（无文件时）
  python3 evaluate.py --task "实现一个命令行待办事项应用" --criteria "支持add/done/list"
"""

import json
import subprocess
import sys
from pathlib import Path

# 加载评分维度（来自 config.json）
CONFIG_PATH = Path(__file__).parent.parent / ".harness" / "config.json"
try:
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    SCORING_DIMS = cfg.get("scoring_dimensions", {})
except:
    SCORING_DIMS = {
        "correctness": {"weight": 0.3, "threshold": "must_pass"},
        "completeness": {"weight": 0.25, "threshold": "must_pass"},
        "consistency": {"weight": 0.2, "threshold": "should_pass"},
        "elegance": {"weight": 0.15, "threshold": "nice_to_have"},
        "performance": {"weight": 0.1, "threshold": "nice_to_have"}
    }

EVALUATOR_PROMPT_TEMPLATE = """你是一个严格的质量评估者（Evaluator）。你的工作是对提交的产出进行批评性检查，给出 PASS/FAIL 结论。

# 评分维度（权重）
{dimensions}

# 交付物
{delivery}

# 验收要求
- 从 Generator 的角度：它应该交付"可用的、完整的、符合规格"的产出
- 在你的评估中：找出具体问题，给出修复建议，不要"自我说服"

输出格式：
```json
{
  "overall_score": "0.0-1.0", 
  "dimension_scores": {
    "correctness": {"score": 0.0, "notes": "..."},
    "completeness": {"score": 0.0, "notes": "..."},
    "consistency": {"score": 0.0, "notes": "..."},
    "elegance": {"score": 0.0, "notes": "..."},
    "performance": {"score": 0.0, "notes": "..."}
  },
  "failures": ["具体的验收失败条目"],
  "recommendations": ["修复建议"],
  "verdict": "PASS|FAIL"
}
```

开始评估。
"""

def format_dimensions():
    lines = []
    for dim, meta in SCORING_DIMS.items():
        lines.append(f"- **{dim}** (权重={meta['weight']}, 门槛={meta['threshold']}): {meta.get('description','')}")
    return "\n".join(lines)

def spawn_evaluator(target_path=None, task_desc=None, acceptance_criteria=None):
    """生成评估 prompt 并调用 sub-agent 执行独立评估"""
    
    if target_path:
        delivery = f"请评估以下文件内容：\n```\n{Path(target_path).read_text()[:2000]}\n```\n（超过2000字符被截断）"
    else:
        delivery = f"请评估以下任务描述：\n{task_desc}\n\n验收标准：{acceptance_criteria or '无'}"
    
    prompt = EVALUATOR_PROMPT_TEMPLATE.format(
        dimensions=format_dimensions(),
        delivery=delivery
    )
    
    # 调用 sub-agent（独立 session）
    print(f"⚡ 启动独立评估者 (sub-agent)...")
    result = subprocess.run(
        ["python3", "-c", f"""
import os, sys
from openclaw import agents
agents.run(prompt='''{prompt}''')
"""],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode != 0:
        print(f"❌ 评估失败: {result.stderr}")
        return None
    
    output = result.stdout.strip()
    # 尝试提取 JSON
    try:
        # 查找 json 块
        if '```json' in output:
            json_text = output.split('```json')[1].split('```')[0].strip()
        elif output.startswith('{'):
            json_text = output
        else:
            json_text = None
        if json_text:
            assessment = json.loads(json_text)
            print(f"📊 评估完成: {assessment['verdict']} (overall={assessment['overall_score']})")
            return assessment
    except:
        print(f"⚠️ 无法解析评估输出，原始输出：\n{output[:500]}")
    
    return output

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Mode 11: 独立评估者")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--target", help="要评估的文件路径")
    group.add_argument("--task", help="任务描述")
    parser.add_argument("--criteria", help="验收标准")
    parser.add_argument("--output", help="评估结果保存路径（JSON）")
    args = parser.parse_args()
    
    assessment = spawn_evaluator(
        target_path=args.target,
        task_desc=args.task,
        acceptance_criteria=args.criteria
    )
    
    if assessment and args.output:
        with open(args.output, 'w') as f:
            json.dump(assessment, f, indent=2, ensure_ascii=False)
        print(f"✅ 评估结果已保存: {args.output}")
    elif assessment:
        print(json.dumps(assessment, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
