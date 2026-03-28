#!/usr/bin/env python3
"""
kg_query.py v2 — 从知识图谱做多跳推理，推荐下一个 capsule 方向

改进：
  1. 从 knowledge_graph.json 读取实时数据
  2. 多跳推理：A→B→C 链条发现高价值间接连接
  3. 空白领域检测：高出现次数但无连接的概念
  4. 质量信号：auto_promoted 率高的方向优先
"""
import json, sys, os
from collections import defaultdict

KG_PATH = os.path.expanduser("~/workspace/agent/workspace/memory/ontology/knowledge_graph.json")

def load_kg():
    with open(KG_PATH) as f:
        return json.load(f)

def suggest_next_topic():
    kg = load_kg()
    concepts = kg["nodes"]["concepts"]
    capsules = kg["nodes"]["capsules"]
    weak = kg["edges"]["weak_connections"]
    strong = kg["edges"]["strong_connections"]
    all_edges = weak + strong

    # 建立邻接表
    adj = defaultdict(set)
    edge_weights = {}
    for e in all_edges:
        adj[e["from"]].add(e["to"])
        adj[e["to"]].add(e["from"])
        pair = tuple(sorted([e["from"], e["to"]]))
        edge_weights[pair] = e.get("weight", 0)

    # === 1. 空白领域检测 ===
    concept_connections = defaultdict(int)
    for e in all_edges:
        concept_connections[e["from"]] += 1
        concept_connections[e["to"]] += 1

    # 高频出现但无连接的概念 = 完全空白
    blank_spots = []
    for name, data in concepts.items():
        occ = data.get("occurrences", 0)
        conns = concept_connections.get(name, 0)
        if occ >= 2 and conns == 0:
            blank_spots.append((name, occ))

    # === 2. 弱连接深化（weight < 3 的）===
    underexplored = [w for w in weak if w.get("weight", 0) < 3]

    # === 3. 多跳推理：发现间接高价值连接 ===
    # A-B 弱连接 + B-C 强连接 → A-C 间接高价值
    indirect = []
    for a in adj:
        for b in adj[a]:
            for c in adj[b]:
                if c != a and c not in adj[a]:
                    # A-B-C 链条，A-C 无直接连接
                    pair_ab = tuple(sorted([a, b]))
                    pair_bc = tuple(sorted([b, c]))
                    w_ab = edge_weights.get(pair_ab, 0)
                    w_bc = edge_weights.get(pair_bc, 0)
                    # 通过桥接强度评分
                    bridge_score = min(w_ab, w_bc) * 0.7 + max(w_ab, w_bc) * 0.3
                    indirect.append({
                        "from": a,
                        "to": c,
                        "via": b,
                        "score": bridge_score,
                        "meaning": f"通过 {b} 间接连接 ({a}→{b}={w_ab}, {b}→{c}={w_bc})"
                    })

    # 去重并排序
    seen = set()
    unique_indirect = []
    for ind in indirect:
        pair = tuple(sorted([ind["from"], ind["to"]]))
        if pair not in seen:
            seen.add(pair)
            unique_indirect.append(ind)
    unique_indirect.sort(key=lambda x: x["score"], reverse=True)

    # === 4. 计算 auto_promoted 率 ===
    direction_quality = defaultdict(lambda: {"promoted": 0, "total": 0})
    for cap in capsules:
        signals = cap.get("signals", [])
        for i, a in enumerate(signals):
            for b in signals[i+1:]:
                pair = tuple(sorted([a, b]))
                direction_quality[pair]["total"] += 1
                if cap.get("result") == "auto_promoted":
                    direction_quality[pair]["promoted"] += 1

    # === 输出 ===
    print("=== 知识图谱 v2 推荐 ===\n")

    if blank_spots:
        print("🔴 完全空白领域（最高优先级）:")
        for name, occ in sorted(blank_spots, key=lambda x: x[1], reverse=True):
            # 找一个高频概念与之配对
            high_freq = [c for c, d in concepts.items() if d["occurrences"] >= 3 and c != name]
            if high_freq:
                partner = high_freq[0]
                print(f"  {name} × {partner} — {name}出现{occ}次但无连接")
        top = {"from": blank_spots[0][0], "to": "待配对", "meaning": f"{blank_spots[0][0]}完全空白"}
    elif underexplored:
        print("🟡 弱连接深化（权重 < 3）:")
        for w in sorted(underexplored, key=lambda x: x.get("weight", 0)):
            pair = tuple(sorted([w["from"], w["to"]]))
            q = direction_quality.get(pair, {})
            rate = f"{q.get('promoted',0)}/{q.get('total',0)} promoted" if q.get("total", 0) > 0 else "无历史"
            print(f"  {w['from']} × {w['to']} = {w['weight']} ({rate}) → {w['meaning'][:50]}")
        top = underexplored[0]
    else:
        print("✅ 弱连接充分探索。多跳推理发现新方向:")
        for ind in unique_indirect[:3]:
            pair = tuple(sorted([ind["from"], ind["to"]]))
            q = direction_quality.get(pair, {})
            rate = f"{q.get('promoted',0)}/{q.get('total',0)}" if q.get("total") else "0"
            print(f"  {ind['from']} → [{ind['via']}] → {ind['to']} (score={ind['score']:.1f}, {rate} promoted)")
        top = unique_indirect[0] if unique_indirect else None

    # 质量洞察
    print("\n📊 方向质量（auto_promoted 率）:")
    sorted_dirs = sorted(direction_quality.items(), key=lambda x: x[1]["promoted"], reverse=True)
    for pair, stats in sorted_dirs[:5]:
        if stats["total"] > 0:
            rate = stats["promoted"] / stats["total"] * 100
            print(f"  {pair[0]} × {pair[1]}: {stats['promoted']}/{stats['total']} ({rate:.0f}%)")

    if top:
        print(f"\n➡️ 推荐：'{top['from']}' × {top.get('to', '?')}")
        print(f"   理由：{top['meaning']}")

    return top

def check_before_publish(topic_signals):
    """发布前检查：避免饱和领域"""
    kg = load_kg()
    capsules = kg["nodes"]["capsules"]

    # 统计已有 capsule 数
    signal_counts = defaultdict(int)
    for cap in capsules:
        for s in cap.get("signals", []):
            signal_counts[s] += 1

    # 检查信号是否过多
    for s in topic_signals:
        if signal_counts.get(s, 0) >= 6:
            print(f"⚠️ {s} 已有 {signal_counts[s]} 个 capsule，可能饱和")
            return False
    return True

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "suggest"
    if cmd == "suggest":
        suggest_next_topic()
    elif cmd == "check":
        signals = sys.argv[2:]
        check_before_publish(signals)
