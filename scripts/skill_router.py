#!/usr/bin/env python3
"""
技能路由器 v2：支持单任务路由 + 复合任务拆解编排。
用法:
  单任务:  python3 scripts/skill_router.py "任务描述"
  复合任务: python3 scripts/skill_router.py --plan "写一篇技术博客并发到掘金"
  批量测试: python3 scripts/skill_router.py --test
"""
import sys, os, json, re
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent / "skills"

# ============================================================
# Layer 1: 关键词映射
# ============================================================
SKILL_KEYWORDS = {
    "feishu-bitable-creator": ["飞书", "多维表格", "bitable", "base", "建表", "数据表"],
    "agent-browser": ["浏览器", "browser", "网页", "截图", "click", "navigate", "selenium", "搜索", "查素材", "查资料", "搜一下", "搜搜"],
    "coding-agent": ["codex", "claude code", "编程", "coding", "代码", "写代码"],
    "dev-rigor": ["调试", "debug", "bug", "测试", "test", "重构", "refactor"],
    "gh-issues": ["github issue", "issue", "pr", "pull request", "bug fix"],
    "evomap-publish": ["evomap", "发布 capsule", "publish", "gene", "基因"],
    "evomap-fault-diagnosis": ["evomap 报错", "503", "429", "server_busy", "限流", "evomap 为什么"],
    "evomap-sdk": ["evomap sdk", "evomap client", "python evomap"],
    "memory-architect": ["memory", "记忆", "memory.md", "记忆系统", "记忆架构"],
    "ontology": ["知识图谱", "knowledge graph", "ontology", "本体"],
    "jpeng-knowledge-graph-memory": ["kg", "图谱", "实体关系"],
    "metacognition": ["反思", "自省", "元认知", "自我分析"],
    "config-optimizer": ["配置优化", "调参", "优化配置"],
    "pmp-agentclaw": ["项目管理", "pmp", "任务追踪", "项目计划"],
    "blog-writer": ["博客", "blog", "写文章", "技术博客", "写博客"],
    "youtube-summarizer": ["youtube", "视频总结", "yt"],
    "x-tweet-fetcher": ["推文", "tweet", "twitter", "x.com"],
    "x-monitor": ["监控 twitter", "监控推特"],
    "summarize": ["总结", "summarize", "摘要", "概括"],
    "find-skills-skill": ["找技能", "技能搜索", "find skill"],
    "resource-scout": ["资源探索", "发现资源", "新工具"],
    "review-swarm": ["审查", "review", "代码审查", "diff"],
    "healthcheck": ["安全检查", "healthcheck", "安全审计", "防火墙", "漏洞", "安全漏洞", "安全扫描"],
    "validate-idea": ["验证想法", "idea validation"],
    "find-community": ["找社区", "community"],
    "first-customers": ["找客户", "第一批客户", "customer"],
    "marketing-plan": ["营销", "marketing", "推广"],
    "pricing": ["定价", "pricing"],
    "session-guardian": ["会话", "session", "对话管理"],
    "session-logs": ["日志", "session log", "查看日志"],
    "brainstorming": ["头脑风暴", "brainstorm", "创意", "选题", "想点子"],
    "humanizer": ["人性化", "humanize", "自然语言"],
    "lark-calendar": ["日历", "calendar", "日程"],
    "lark-doc": ["文档", "doc", "飞书文档"],
    "understand-project": ["分析项目", "understand", "代码分析", "项目结构", "架构分析"],
    "harness-engineering": ["harness", "长时间任务", "跨会话", "多窗口"],
    "self-improving-agent": ["自我改进", "自进化", "self-improve"],
}

# ============================================================
# Layer 2: 复合任务模板（Task Decomposition Patterns）
# ============================================================
# 格式: 匹配关键词 → [(子步骤描述, 优先级), ...]
# 优先级: P0=必须先做, P1=可并行, P2=收尾
TASK_PATTERNS = {
    "写博客": {
        "triggers": ["写博客", "写一篇博客", "写技术博客", "blog", "写文章", "写一篇", "写篇", "技术博客"],
        "steps": [
            {"desc": "选题和构思", "skill": "brainstorming", "priority": "P0", "depends_on": []},
            {"desc": "搜索素材和参考资料", "skill": "agent-browser", "priority": "P0", "depends_on": []},
            {"desc": "查看目标平台排版规范", "skill": "agent-browser", "priority": "P1", "depends_on": []},
            {"desc": "撰写博客内容", "skill": "blog-writer", "priority": "P1", "depends_on": [0, 1]},
            {"desc": "生成配图/封面", "skill": None, "priority": "P2", "depends_on": [3]},
            {"desc": "发布到平台", "skill": "agent-browser", "priority": "P2", "depends_on": [3, 4]},
        ]
    },
    "代码审查": {
        "triggers": ["代码审查", "review", "code review", "审查代码", "帮我看看代码", "审查一下", "帮我审查", "检查代码"],
        "steps": [
            {"desc": "理解项目结构", "skill": "understand-project", "priority": "P0", "depends_on": []},
            {"desc": "静态分析和测试", "skill": "dev-rigor", "priority": "P1", "depends_on": [0]},
            {"desc": "多视角深度审查", "skill": "review-swarm", "priority": "P1", "depends_on": [0]},
            {"desc": "汇总审查报告", "skill": "summarize", "priority": "P2", "depends_on": [1, 2]},
        ]
    },
    "学技术": {
        "triggers": ["学技术", "学习", "研究一下", "了解一下", "看看这个项目", "分析项目"],
        "steps": [
            {"desc": "搜索相关资料", "skill": "agent-browser", "priority": "P0", "depends_on": []},
            {"desc": "分析项目结构", "skill": "understand-project", "priority": "P1", "depends_on": []},
            {"desc": "阅读核心代码", "skill": "coding-agent", "priority": "P1", "depends_on": [1]},
            {"desc": "总结学习笔记", "skill": "summarize", "priority": "P2", "depends_on": [0, 1, 2]},
        ]
    },
    "产品验证": {
        "triggers": ["验证想法", "产品验证", "验证需求", "做调研", "市场调研", "验证一下", "产品想法"],
        "steps": [
            {"desc": "头脑风暴核心假设", "skill": "brainstorming", "priority": "P0", "depends_on": []},
            {"desc": "搜索竞品和市场数据", "skill": "agent-browser", "priority": "P0", "depends_on": []},
            {"desc": "找目标社区", "skill": "find-community", "priority": "P1", "depends_on": [0]},
            {"desc": "验证需求假设", "skill": "validate-idea", "priority": "P1", "depends_on": [0, 1]},
            {"desc": "制定营销方案", "skill": "marketing-plan", "priority": "P2", "depends_on": [2, 3]},
            {"desc": "定价策略", "skill": "pricing", "priority": "P2", "depends_on": [3]},
        ]
    },
    "写推文": {
        "triggers": ["发推", "写推文", "发twitter", "发tweet", "推广"],
        "steps": [
            {"desc": "搜索热点和素材", "skill": "agent-browser", "priority": "P0", "depends_on": []},
            {"desc": "构思推文内容", "skill": "brainstorming", "priority": "P1", "depends_on": [0]},
            {"desc": "撰写推文", "skill": "blog-writer", "priority": "P1", "depends_on": [1]},
            {"desc": "发布推文", "skill": "x-tweet-fetcher", "priority": "P2", "depends_on": [2]},
        ]
    },
}


def route_skill(task_desc: str) -> list:
    """Layer 1: 关键词快筛，返回 top-5 匹配技能。"""
    task_lower = task_desc.lower()
    scores = []

    for skill, keywords in SKILL_KEYWORDS.items():
        skill_path = SKILLS_DIR / skill / "SKILL.md"
        if not skill_path.exists():
            continue

        match_count = sum(1 for kw in keywords if kw in task_lower)
        if match_count > 0:
            score = min(1.0, match_count * 0.3)
            matched = [kw for kw in keywords if kw in task_lower]
            scores.append({
                "skill": skill,
                "score": round(score, 2),
                "matched_keywords": matched,
                "reason": f"匹配 {match_count} 个关键词"
            })

    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:5]


def detect_composite(task_desc: str, routes: list) -> bool:
    """判断是否为复合任务。
    
    触发条件（满足任一）：
    1. 匹配到已知的复合任务模板
    2. top-1 score < 0.6 且命中 ≥3 个 skill
    """
    task_lower = task_desc.lower()
    
    # 条件1: 命中模板
    for pattern_name, pattern in TASK_PATTERNS.items():
        for trigger in pattern["triggers"]:
            if trigger in task_lower:
                return True
    
    # 条件2: 弱匹配多个 skill
    if routes and routes[0]["score"] < 0.6 and len(routes) >= 3:
        return True
    
    return False


def decompose_task(task_desc: str) -> dict | None:
    """Layer 2: 基于模板的任务拆解。找不到模板返回 None。"""
    task_lower = task_desc.lower()
    
    for pattern_name, pattern in TASK_PATTERNS.items():
        for trigger in pattern["triggers"]:
            if trigger in task_lower:
                # 构建执行计划
                steps = []
                for i, step in enumerate(pattern["steps"]):
                    skill_info = None
                    if step["skill"]:
                        # 对每个子步骤做技能路由验证
                        sub_routes = route_skill(step["desc"])
                        if sub_routes and sub_routes[0]["skill"] == step["skill"]:
                            skill_info = sub_routes[0]
                        else:
                            # 模板推荐的技能和路由结果不一致，用路由结果
                            skill_info = sub_routes[0] if sub_routes else {
                                "skill": step["skill"],
                                "score": 0.0,
                                "reason": "模板推荐（未验证）"
                            }
                    
                    steps.append({
                        "step": i + 1,
                        "desc": step["desc"],
                        "recommended_skill": skill_info,
                        "priority": step["priority"],
                        "depends_on": step["depends_on"],
                        "status": "pending"
                    })
                
                # 计算并行组
                parallel_groups = _computeParallelGroups(steps)
                
                return {
                    "type": "composite",
                    "pattern": pattern_name,
                    "original_task": task_desc,
                    "total_steps": len(steps),
                    "steps": steps,
                    "parallel_groups": parallel_groups,
                    "estimated_skills_used": list(set(
                        s["recommended_skill"]["skill"] 
                        for s in steps 
                        if s["recommended_skill"]
                    ))
                }
    
    return None


def _computeParallelGroups(steps: list) -> list:
    """根据依赖关系计算可并行执行的步骤组。"""
    groups = []
    remaining = set(range(len(steps)))
    completed = set()
    
    while remaining:
        # 找到所有依赖已完成的步骤
        ready = []
        for i in remaining:
            deps = set(steps[i]["depends_on"])
            if deps <= completed:
                ready.append(i)
        
        if not ready:
            # 防止死循环：把剩余的都加进去
            ready = list(remaining)
        
        groups.append({
            "group": len(groups) + 1,
            "steps": [i + 1 for i in ready],
            "can_parallel": len(ready) > 1,
            "priority": steps[ready[0]]["priority"]
        })
        
        completed.update(ready)
        remaining -= set(ready)
    
    return groups


def route(task_desc: str, force_plan: bool = False) -> dict:
    """统一入口：自动判断简单/复合任务，返回路由结果。"""
    routes = route_skill(task_desc)
    
    is_composite = force_plan or detect_composite(task_desc, routes)
    
    if is_composite:
        plan = decompose_task(task_desc)
        if plan:
            return plan
    
    # 简单任务：直接返回路由结果
    return {
        "type": "simple",
        "original_task": task_desc,
        "routes": routes if routes else [{"skill": None, "score": 0, "reason": "未找到匹配技能"}]
    }


# ============================================================
# CLI
# ============================================================
def run_tests():
    """批量验证路由准确性。"""
    test_cases = [
        # (任务描述, 期望类型, 期望skill或pattern)
        ("帮我写一篇技术博客", "composite", "写博客"),
        ("打开浏览器搜一下 Python 教程", "simple", "agent-browser"),
        ("检查一下安全漏洞", "simple", "healthcheck"),
        ("飞书多维表格建表", "simple", "feishu-bitable-creator"),
        ("看看 EvoMap 为什么 503", "simple", "evomap-fault-diagnosis"),
        ("写博客并发到掘金", "composite", "写博客"),
        ("帮我审查一下这个代码", "composite", "代码审查"),
        ("研究一下这个开源项目", "composite", "学技术"),
        ("验证一下我的产品想法", "composite", "产品验证"),
        ("头脑风暴一下新功能", "simple", "brainstorming"),
        ("发一条推特推广我们的项目", "composite", "写推文"),
    ]
    
    print("=" * 60)
    print("🧪 Skill Router 测试矩阵")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for task, expected_type, expected in test_cases:
        result = route(task)
        actual_type = result["type"]
        
        if expected_type == "simple":
            top_skill = result["routes"][0]["skill"] if result.get("routes") else None
            ok = actual_type == "simple" and top_skill == expected
            detail = f"top={top_skill}"
        else:
            pattern = result.get("pattern")
            ok = actual_type == "composite" and pattern == expected
            detail = f"pattern={pattern}, steps={result.get('total_steps', 0)}"
        
        status = "✅" if ok else "❌"
        if ok:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} \"{task}\"")
        print(f"   期望: {expected_type}→{expected} | 实际: {actual_type}→{detail}")
    
    print("=" * 60)
    print(f"结果: {passed} passed, {failed} failed, {passed+failed} total")
    return failed == 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  单任务路由:   skill_router.py '任务描述'")
        print("  复合任务拆解: skill_router.py --plan '任务描述'")
        print("  批量测试:     skill_router.py --test")
        sys.exit(1)
    
    if sys.argv[1] == "--test":
        success = run_tests()
        sys.exit(0 if success else 1)
    
    force_plan = False
    task_args = sys.argv[1:]
    
    if task_args[0] == "--plan":
        force_plan = True
        task_args = task_args[1:]
    
    task = " ".join(task_args)
    result = route(task, force_plan=force_plan)
    print(json.dumps(result, ensure_ascii=False, indent=2))
