#!/usr/bin/env python3
"""知识图谱查询接口"""
import json
import sys

GRAPH_PATH = '/home/gem/workspace/agent/workspace/memory/ontology/graph.jsonl'

def load_graph():
    entities = {}
    edges = []
    with open(GRAPH_PATH) as f:
        for line in f:
            op = json.loads(line)
            if op['op'] == 'create':
                e = op['entity']
                entities[e['id']] = e
            elif op['op'] == 'relate':
                edges.append(op['edge'])
            elif op['op'] == 'delete':
                entities.pop(op['id'], None)
    return entities, edges

def query(cmd, *args):
    entities, edges = load_graph()
    
    if cmd == 'list':
        for eid, e in entities.items():
            print(f"  {e['type']:10} {eid:25} {e.get('properties',{}).get('name','')}")
    
    elif cmd == 'get':
        eid = args[0] if args else ''
        if eid in entities:
            e = entities[eid]
            print(json.dumps(e, ensure_ascii=False, indent=2))
            # Show relationships
            rels = [ed for ed in edges if ed.get('from') == eid or ed.get('to') == eid]
            if rels:
                print(f"\nRelationships ({len(rels)}):")
                for r in rels:
                    print(f"  {r.get('from')} --[{r.get('type')}]--> {r.get('to')}")
        else:
            print(f"Not found: {eid}")
    
    elif cmd == 'related':
        eid = args[0] if args else ''
        rels = [ed for ed in edges if ed.get('from') == eid or ed.get('to') == eid]
        for r in rels:
            other = r.get('to') if r.get('from') == eid else r.get('from')
            direction = '→' if r.get('from') == eid else '←'
            print(f"  {direction} [{r.get('type')}] {other} ({entities.get(other,{}).get('properties',{}).get('name','?')})")
    
    elif cmd == 'stats':
        types = {}
        for e in entities.values():
            t = e.get('type', '?')
            types[t] = types.get(t, 0) + 1
        print(f"Entities: {len(entities)}")
        print(f"Edges: {len(edges)}")
        print(f"Types: {dict(types)}")
    
    else:
        print("Commands: list | get <id> | related <id> | stats")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: kg-query.py <command> [args]")
        print("Commands: list, get <id>, related <id>, stats")
    else:
        query(sys.argv[1], *sys.argv[2:])
