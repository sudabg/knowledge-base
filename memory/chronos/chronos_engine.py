#!/usr/bin/env python3
"""
Chronos Memory Engine v1.0
基于 Chronos 论文的 SVO (Subject-Verb-Object) 事件提取
只读现有 memory 文件，生成可查询的结构化索引
不修改任何原有记忆文件
"""

import json, re, os, sys
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path('/home/gem/workspace/agent/workspace/memory')
INDEX_FILE = Path('/home/gem/workspace/agent/workspace/memory/chronos/chronos_index.json')
CHRONOS_DIR = Path('/home/gem/workspace/agent/workspace/memory/chronos')

# ─── SVO 提取规则 ───

VERB_PATTERNS = [
    # (verb_normalized, pattern)
    ('发布', r'发布[了]?(?:capsule|Gene|项目|内容)'),
    ('心跳', r'心跳(?:成功|失败|超时|429|503)'),
    ('修复', r'修复[了]?(.{3,40}?)(?:\(|（|$)'),
    ('创建', r'创建[了]?(.{3,40}?)(?:\(|（|$)'),
    ('启动', r'启动[了]?(.{3,40}?)(?:$)'),
    ('归档', r'归档[了]?(.{3,40}?)(?:$)'),
    ('更新', r'更新[了]?(.{3,40}?)(?:$)'),
    ('搜索', r'搜索[了]?(.{3,40}?)(?:$)'),
    ('学习', r'学习[了]?(.{3,40}?)(?:$)'),
    ('反思', r'反思[了]?(.{3,40}?)(?:$)'),
    ('同步', r'同步[了]?(.{3,40}?)(?:$)'),
    ('部署', r'部署[了]?(.{3,40}?)(?:$)'),
    ('提交', r'提交[了]?(.{3,40}?)(?:$)'),
    ('尝试', r'尝试[了]?(.{3,40}?)(?:$)'),
    ('发现', r'发现[了]?(.{3,40}?)(?:$)'),
    ('检查', r'检查[了]?(.{3,40}?)(?:$)'),
    ('验证', r'验证[了]?(.{3,40}?)(?:$)'),
    ('暂停', r'暂停[了]?(.{3,40}?)(?:$)'),
    ('增加', r'增加[了]?(.{3,40}?)(?:$)'),
    ('解决', r'解决[了]?(.{3,40}?)(?:$)'),
]

SUBJECT_MAP = {
    '心跳': 'heartbeat',
    'EvoMap': 'evomap',
    'Dashboard': 'dashboard',
    'Server': 'server',
    'capsule': 'capsule',
    'GitHub': 'github',
    'P.md': 'archive',
    'memory': 'memory',
    '配置': 'config',
}

def extract_timestamp(line, date_str, fallback_time=None):
    """从行中提取时间"""
    # Match HH:MM at start of line (with optional markdown prefix)
    time_match = re.match(r'^[-*\s]*(\d{1,2}:\d{2})', line.strip())
    if time_match:
        return f"{date_str}T{time_match.group(1).zfill(5)}:00+08:00"
    # Match "HH:MM" in section headers like "## 08:00 尝试"
    time_match = re.search(r'##\s+(\d{1,2}:\d{2})', line)
    if time_match:
        return f"{date_str}T{time_match.group(1).zfill(5)}:00+08:00"
    if fallback_time:
        return f"{date_str}T{fallback_time}:00+08:00"
    return None  # Will use section time or skip

def extract_svo(line, date_str, fallback_time=None):
    """从日志行提取 SVO 三元组"""
    events = []
    text = line.strip()
    
    # Skip headers and empty lines
    if text.startswith('#') or not text or text.startswith('|'):
        return events
    
    # Remove markdown list prefix
    text = re.sub(r'^[-*]\s+', '', text)
    text = re.sub(r'^\d+\.\s+', '', text)
    
    timestamp = extract_timestamp(line, date_str, fallback_time=fallback_time)
    
    # Match verb patterns
    for verb, pattern in VERB_PATTERNS:
        m = re.search(pattern, text)
        if m:
            subject = 'agent'  # default subject
            obj = m.group(1).strip() if m.lastindex and m.lastindex >= 1 else text[:60]
            
            # Try to identify subject from context
            for key, subj in SUBJECT_MAP.items():
                if key in text[:20]:
                    subject = subj
                    break
            
            # Detect sentiment
            sentiment = 'neutral'
            if any(w in text for w in ['成功', '✅', '正常', '完成', '修复']):
                sentiment = 'positive'
            elif any(w in text for w in ['失败', '❌', '错误', '超时', '429', '503']):
                sentiment = 'negative'
            
            events.append({
                'timestamp': timestamp,
                'subject': subject,
                'verb': verb,
                'object': obj[:80],
                'raw': text[:120],
                'sentiment': sentiment,
                'date': date_str
            })
            break  # One event per line
    
    return events

def parse_daily_log(filepath):
    """解析单个日志文件"""
    date_str = filepath.stem  # e.g., "2026-03-18"
    events = []
    
    content = filepath.read_text(encoding='utf-8')
    current_section = ''
    section_time = None
    
    for line in content.split('\n'):
        # Track section headers - extract time if present
        if line.startswith('## '):
            current_section = line.strip('# ')
            # Try to extract time from section header
            tm = re.match(r'(\d{1,2}:\d{2})', current_section)
            if tm:
                section_time = tm.group(1)
            continue
        
        line_events = extract_svo(line, date_str, fallback_time=section_time)
        for evt in line_events:
            evt['section'] = current_section
            if evt['timestamp'] is None:
                if section_time:
                    evt['timestamp'] = f"{date_str}T{section_time}:00+08:00"
                else:
                    evt['timestamp'] = f"{date_str}T12:00:00+08:00"
        events.extend(line_events)
    
    return events

def build_index():
    """构建完整索引"""
    all_events = []
    
    # Parse all daily logs
    for f in sorted(MEMORY_DIR.glob('2026-*.md')):
        try:
            events = parse_daily_log(f)
            all_events.extend(events)
        except Exception as e:
            print(f"Warning: Failed to parse {f.name}: {e}", file=sys.stderr)
    
    # Build aggregated stats
    stats = {
        'total_events': len(all_events),
        'by_verb': {},
        'by_subject': {},
        'by_sentiment': {},
        'by_date': {},
        'date_range': {'start': None, 'end': None}
    }
    
    for evt in all_events:
        v = evt['verb']
        s = evt['subject']
        sent = evt['sentiment']
        d = evt['date']
        
        stats['by_verb'][v] = stats['by_verb'].get(v, 0) + 1
        stats['by_subject'][s] = stats['by_subject'].get(s, 0) + 1
        stats['by_sentiment'][sent] = stats['by_sentiment'].get(sent, 0) + 1
        stats['by_date'][d] = stats['by_date'].get(d, 0) + 1
    
    dates = sorted(set(e['date'] for e in all_events))
    if dates:
        stats['date_range'] = {'start': dates[0], 'end': dates[-1]}
    
    index = {
        'version': '1.0',
        'built_at': datetime.now().astimezone().isoformat(),
        'stats': stats,
        'events': all_events
    }
    
    return index

def query(index, verb=None, subject=None, date=None, sentiment=None, keyword=None, limit=10):
    """查询索引"""
    results = index['events']
    
    if verb:
        results = [e for e in results if e['verb'] == verb]
    if subject:
        results = [e for e in results if e['subject'] == subject]
    if date:
        results = [e for e in results if e['date'] == date]
    if sentiment:
        results = [e for e in results if e['sentiment'] == sentiment]
    if keyword:
        kw = keyword.lower()
        results = [e for e in results if kw in e['raw'].lower() or kw in e['object'].lower()]
    
    return results[-int(limit):]

def format_event(evt):
    """格式化单条事件"""
    icon = {'positive': '✅', 'negative': '❌', 'neutral': '·'}.get(evt['sentiment'], '·')
    return f"{icon} [{evt['timestamp'][:16]}] {evt['subject']} → {evt['verb']} → {evt['object']}"

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  chronos_engine.py build          # Build index")
        print("  chronos_engine.py query [opts]   # Query index")
        print("  chronos_engine.py stats          # Show stats")
        print("  chronos_engine.py recent [N]     # Show recent N events")
        return
    
    cmd = sys.argv[1]
    
    if cmd == 'build':
        CHRONOS_DIR.mkdir(parents=True, exist_ok=True)
        print("Building Chronos index...")
        index = build_index()
        INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=2))
        print(f"✅ Index built: {index['stats']['total_events']} events")
        print(f"   Date range: {index['stats']['date_range']['start']} → {index['stats']['date_range']['end']}")
        print(f"   Saved to: {INDEX_FILE}")
    
    elif cmd == 'stats':
        if not INDEX_FILE.exists():
            print("❌ Index not found. Run 'build' first.")
            return
        index = json.loads(INDEX_FILE.read_text())
        stats = index['stats']
        print(f"📊 Chronos Memory Index Stats")
        print(f"   Total events: {stats['total_events']}")
        print(f"   Date range: {stats['date_range']['start']} → {stats['date_range']['end']}")
        print(f"\n   By verb:")
        for v, c in sorted(stats['by_verb'].items(), key=lambda x: -x[1]):
            print(f"     {v}: {c}")
        print(f"\n   By subject:")
        for s, c in sorted(stats['by_subject'].items(), key=lambda x: -x[1]):
            print(f"     {s}: {c}")
        print(f"\n   By sentiment:")
        for s, c in stats['by_sentiment'].items():
            print(f"     {s}: {c}")
    
    elif cmd == 'recent':
        if not INDEX_FILE.exists():
            print("❌ Index not found. Run 'build' first.")
            return
        index = json.loads(INDEX_FILE.read_text())
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        events = index['events'][-limit:]
        for evt in events:
            print(format_event(evt))
    
    elif cmd == 'query':
        if not INDEX_FILE.exists():
            print("❌ Index not found. Run 'build' first.")
            return
        index = json.loads(INDEX_FILE.read_text())
        
        # Parse query args
        kwargs = {}
        for arg in sys.argv[2:]:
            if '=' in arg:
                k, v = arg.split('=', 1)
                kwargs[k] = v
        
        results = query(index, **kwargs)
        print(f"Found {len(results)} events:")
        for evt in results:
            print(format_event(evt))

if __name__ == '__main__':
    main()
