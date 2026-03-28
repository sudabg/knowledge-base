#!/usr/bin/env python3
"""
kg_auto_update.py — capsule 发布后自动更新知识图谱

用法：
  python3 scripts/kg_auto_update.py --signals "记忆系统,推理/CoT" --topic "某个 capsule" --bundle_id "bundle_xxx"

功能：
  1. 更新 concept 出现次数
  2. 更新边权重（共现次数）
  3. 检测是否应升级弱连接→强连接
  4. 写回 knowledge_graph.json
"""
import json, argparse, os
from datetime import datetime

KG_PATH = os.path.expanduser("~/workspace/agent/workspace/memory/ontology/knowledge_graph.json")

STRONG_THRESHOLD = 4  # 边权重达到此值时升级为强连接

def load_kg():
    with open(KG_PATH) as f:
        return json.load(f)

def save_kg(kg):
    kg["generated_at"] = datetime.now().astimezone().isoformat()
    with open(KG_PATH, "w") as f:
        json.dump(kg, f, indent=2, ensure_ascii=False)

def update_after_publish(signals: list, topic: str, bundle_id: str = "", result: str = "auto_promoted"):
    kg = load_kg()

    # 1. 添加 capsule 记录
    capsule = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "topic": topic,
        "signals": signals,
        "result": result,
        "bundle_id": bundle_id
    }
    kg["nodes"]["capsules"].append(capsule)
    # 只保留最近 50 个
    kg["nodes"]["capsules"] = kg["nodes"]["capsules"][-50:]

    # 2. 更新 concept 出现次数
    for s in signals:
        if s in kg["nodes"]["concepts"]:
            kg["nodes"]["concepts"][s]["occurrences"] += 1
        else:
            kg["nodes"]["concepts"][s] = {"occurrences": 1, "type": "capability"}

    # 3. 更新边权重（信号之间的共现）
    for i, a in enumerate(signals):
        for b in signals[i+1:]:
            # 标准化排序
            pair = tuple(sorted([a, b]))
            found = False
            for w in kg["edges"]["weak_connections"]:
                edge_pair = tuple(sorted([w["from"], w["to"]]))
                if edge_pair == pair:
                    w["weight"] = w.get("weight", 0) + 1
                    found = True
                    break
            if not found:
                for s in kg["edges"]["strong_connections"]:
                    edge_pair = tuple(sorted([s["from"], s["to"]]))
                    if edge_pair == pair:
                        s["weight"] = s.get("weight", 0) + 1
                        found = True
                        break
            if not found:
                # 全新边
                kg["edges"]["weak_connections"].append({
                    "from": pair[0],
                    "to": pair[1],
                    "weight": 1,
                    "meaning": f"新交叉领域: {pair[0]}×{pair[1]}"
                })

    # 4. 检测升级
    upgraded = []
    remaining_weak = []
    for w in kg["edges"]["weak_connections"]:
        if w.get("weight", 0) >= STRONG_THRESHOLD:
            upgraded.append(w)
            kg["edges"]["strong_connections"].append(w)
        else:
            remaining_weak.append(w)
    kg["edges"]["weak_connections"] = remaining_weak

    # 5. 更新洞察
    kg["insights"] = _generate_insights(kg)

    save_kg(kg)

    print(f"✅ 图谱更新: {topic}")
    print(f"   concepts: {len(kg['nodes']['concepts'])}, capsules: {len(kg['nodes']['capsules'])}")
    print(f"   weak: {len(kg['edges']['weak_connections'])}, strong: {len(kg['edges']['strong_connections'])}")
    if upgraded:
        for u in upgraded:
            print(f"   🔗 升级: {u['from']} × {u['to']} → 强连接 (weight={u['weight']})")

def _generate_insights(kg):
    """根据当前图谱状态生成洞察"""
    insights = []
    concepts = kg["nodes"]["concepts"]
    weak = kg["edges"]["weak_connections"]
    strong = kg["edges"]["strong_connections"]

    # 找出现次数最多但连接最少的概念
    concept_connections = {}
    for c in concepts:
        count = 0
        for w in weak + strong:
            if w["from"] == c or w["to"] == c:
                count += 1
        concept_connections[c] = count

    # 低估的概念（高频出现但低连接）
    undervalued = [(c, concepts[c]["occurrences"], concept_connections[c])
                   for c in concepts
                   if concepts[c]["occurrences"] >= 3 and concept_connections.get(c, 0) <= 2]
    undervalued.sort(key=lambda x: x[1], reverse=True)
    for name, occ, conns in undervalued[:2]:
        insights.append(f"{name}被低估：{occ}次出现但仅{conns}个连接")

    # 高质量方向（强连接中 auto_promoted 率高的）
    for s in strong:
        insights.append(f"{s['from']}×{s['to']}={s['weight']}次共现，强连接方向")

    # 最大空白（出现次数 ≥2 但无连接的概念）
    for c, data in concepts.items():
        if data["occurrences"] >= 2 and concept_connections.get(c, 0) == 0:
            insights.append(f"{c}出现{data['occurrences']}次但无连接——潜在空白领域")

    return insights[:8]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--signals", required=True, help="逗号分隔的信号列表")
    parser.add_argument("--topic", required=True, help="capsule 主题")
    parser.add_argument("--bundle_id", default="", help="bundle ID")
    parser.add_argument("--result", default="auto_promoted")
    args = parser.parse_args()
    signals = [s.strip() for s in args.signals.split(",")]
    update_after_publish(signals, args.topic, args.bundle_id, args.result)
