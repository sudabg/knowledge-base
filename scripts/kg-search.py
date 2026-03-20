#!/usr/bin/env python3
"""知识图谱语义搜索 — 基于关键词匹配+相关度排序"""
import json, sys, re

GRAPH = '/home/gem/workspace/agent/workspace/memory/ontology/graph.jsonl'

def load():
    entities, edges = {}, []
    with open(GRAPH) as f:
        for line in f:
            op = json.loads(line)
            if op['op'] == 'create':
                entities[op['entity']['id']] = op['entity']
            elif op['op'] == 'relate':
                edges.append(op['edge'])
            elif op['op'] == 'delete':
                entities.pop(op['id'], None)
    return entities, edges

def search(query, limit=5):
    entities, edges = load()
    query_lower = query.lower()
    words = set(re.findall(r'\w+', query_lower))
    
    scored = []
    for eid, e in entities.items():
        score = 0
        props = e.get('properties', {})
        searchable = ' '.join([
            eid, e.get('type',''),
            props.get('name',''), props.get('content',''),
            props.get('summary',''), props.get('title','')
        ]).lower()
        
        for w in words:
            if w in searchable:
                score += 1
        
        # Boost for relationships
        rels = [ed for ed in edges if ed.get('from') == eid or ed.get('to') == eid]
        score += len(rels) * 0.5
        
        if score > 0:
            scored.append((score, eid, e, len(rels)))
    
    scored.sort(key=lambda x: -x[0])
    
    results = []
    for score, eid, e, rel_count in scored[:limit]:
        props = e.get('properties', {})
        name = props.get('name', props.get('content', eid))[:60]
        results.append({
            'id': eid,
            'type': e.get('type'),
            'name': name,
            'score': round(score, 1),
            'relationships': rel_count
        })
    
    return results

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: kg-search.py <query>")
        sys.exit(1)
    
    query = ' '.join(sys.argv[1:])
    results = search(query)
    
    if not results:
        print(f"No results for: {query}")
    else:
        print(f"Results for: {query}")
        for r in results:
            print(f"  [{r['score']}] {r['type']:10} {r['id']:25} {r['name']}")
            print(f"       {r['relationships']} relationships")
