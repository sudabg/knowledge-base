#!/usr/bin/env python3
"""小哩子 Dashboard - 实时数据版"""
import os, sys, json, datetime, subprocess
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

WORKSPACE = Path('/home/gem/workspace/agent/workspace')
PORT = 8888

EVO_TOKEN = "d846e0f269030e8b3eb3ed60472b164b448f8360e578a6392ccc4740d096ba14"
EVO_NODE = "node_db2f95ffdba95eb6"

# Cache for EvoMap data (refresh every 5 min)
_evo_cache = {"data": None, "ts": 0}

def fetch_evo_status():
    """Fetch real-time node status from EvoMap (cached 5min)"""
    now = datetime.datetime.now().timestamp()
    if _evo_cache["data"] and (now - _evo_cache["ts"]) < 300:
        return _evo_cache["data"]
    try:
        import urllib.request
        payload = json.dumps({
            "protocol": "gep-a2a",
            "protocol_version": "1.0.0",
            "message_type": "heartbeat",
            "message_id": "msg_dashboard",
            "sender_id": EVO_NODE,
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "payload": {}
        }).encode()
        req = urllib.request.Request(
            "https://evomap.ai/a2a/heartbeat",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {EVO_TOKEN}"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            acc = data.get("accountability", {})
            result = {
                "status": data.get("node_status", "unknown"),
                "survival": data.get("survival_status", "unknown"),
                "credit": data.get("credit_balance", 0),
                "reputation_penalty": acc.get("reputation_penalty", 0),
                "quarantine_strikes": acc.get("quarantine_strikes", 0),
                "tasks_count": len(data.get("available_tasks", [])),
                "updated": datetime.datetime.now().strftime("%H:%M:%S")
            }
            _evo_cache["data"] = result
            _evo_cache["ts"] = now
            return result
    except Exception as e:
        # Return cache on error, or error info
        if _evo_cache["data"]:
            _evo_cache["data"]["cached"] = True
            return _evo_cache["data"]
        return {"status": "error", "error": str(e), "updated": datetime.datetime.now().strftime("%H:%M:%S")}

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/status':
            self._json({
                'agent': '小哩子 🦞',
                'status': 'active',
                'time': datetime.datetime.now().strftime('%H:%M:%S')
            })
        elif self.path == '/api/node':
            # 先读本地缓存，没有才调 API
            cache_file = WORKSPACE / '.learnings' / 'last_heartbeat.json'
            data = None
            if cache_file.exists():
                try:
                    data = json.loads(cache_file.read_text())
                except:
                    data = None
            if not data:
                data = fetch_evo_status()
            # If cache missing node stats, fetch from EvoMap node API
            if data and data.get('reputation_score', 0) == 0:
                try:
                    import urllib.request
                    req = urllib.request.Request(
                        f"https://evomap.ai/a2a/nodes/{EVO_NODE}",
                        headers={"Authorization": f"Bearer {EVO_TOKEN}"}
                    )
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        node = json.loads(resp.read())
                        data['reputation_score'] = node.get('reputation_score', 0)
                        data['total_published'] = node.get('total_published', 0)
                        data['total_promoted'] = node.get('total_promoted', 0)
                        data['total_rejected'] = node.get('total_rejected', 0)
                        data['avg_confidence'] = node.get('avg_confidence', 0)
                        data['symbiosis_score'] = node.get('symbiosis_score', 0)
                        # Also update cache file
                        cache_file.write_text(json.dumps(data))
                except Exception as e:
                    pass  # Fall back to cache defaults
            # Ensure all fields have defaults
            for key in ['reputation_score','total_published','total_promoted','total_rejected','avg_confidence','symbiosis_score']:
                if key not in data: data[key] = 0
            if 'updated' not in data:
                data['updated'] = datetime.datetime.now().strftime('%H:%M:%S')
            self._json(data)
        elif self.path == '/api/completed':
            f = WORKSPACE / 'P.md'
            content = f.read_text() if f.exists() else '# 暂无已完成项目'
            self._json({'content': content[:3000], 'exists': f.exists()})
        elif self.path == '/api/projects':
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            f = WORKSPACE / 'docs' / f'project-plans-{today}.md'
            content = f.read_text() if f.exists() else ''
            self._json(self._parse_projects(content))
        elif self.path == '/api/memory':
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            f = WORKSPACE / 'memory' / f'{today}.md'
            self._json({'content': f.read_text()[:2000] if f.exists() else '暂无日志'})
        elif self.path == '/api/activities':
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            f = WORKSPACE / 'memory' / f'{today}.md'
            activities = self._parse_activities(f.read_text() if f.exists() else '')
            self._json({'activities': activities})
        elif self.path == '/':
            self.path = '/index.html'
            super().do_GET()
        else:
            super().do_GET()

    def _json(self, d):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(d, ensure_ascii=False).encode())

    def _parse_projects(self, text):
        """Parse project plans markdown into structured data for dashboard."""
        import re
        projects = []
        lines = text.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]
            # Match project headers: ## 项目一：...
            proj_match = re.match(r'^##\s+项目[一二三四五六七八九十\d]+[：:]\s*(.+)$', line)
            if proj_match:
                proj = {
                    'title': proj_match.group(1).strip(),
                    'goal': '',
                    'status': '',
                    'progress': 0,
                    'phases': [],
                    'pending': []
                }
                i += 1

                while i < len(lines) and not re.match(r'^##\s+项目', lines[i]):
                    l = lines[i].strip()

                    # Goal
                    goal_match = re.match(r'^\*\*目标\*\*[：:]\s*(.+)$', l)
                    if goal_match:
                        proj['goal'] = goal_match.group(1)

                    # Status
                    status_match = re.match(r'^\*\*现状\*\*[：:]\s*(.+)$', l)
                    if status_match:
                        proj['status'] = status_match.group(1)

                    # Phase header: ### 第X阶段...
                    phase_match = re.match(r'^###\s+(.+)$', l)
                    if phase_match:
                        phase_name = phase_match.group(1).strip()
                        phase = {'name': phase_name, 'tasks': []}
                        i += 1
                        while i < len(lines) and not lines[i].startswith('### ') and not lines[i].startswith('## '):
                            tl = lines[i].strip()
                            task_match = re.match(r'^-\s+\[([ x])\]\s+(.+)$', tl)
                            if task_match:
                                done = task_match.group(1) == 'x'
                                task_text = task_match.group(2)
                                phase['tasks'].append({'done': done, 'text': task_text})
                            i += 1
                        proj['phases'].append(phase)
                        continue

                    # Pending items under ### 今日待办 or similar
                    pending_match = re.match(r'^-\s+⏳\s+(.+)$', l)
                    if pending_match:
                        proj['pending'].append(pending_match.group(1))

                    i += 1

                # Calculate progress
                total_tasks = sum(len(p['tasks']) for p in proj['phases'])
                done_tasks = sum(1 for p in proj['phases'] for t in p['tasks'] if t['done'])
                proj['progress'] = round(done_tasks / total_tasks * 100) if total_tasks > 0 else 0
                proj['done_count'] = done_tasks
                proj['total_count'] = total_tasks

                projects.append(proj)
            else:
                i += 1

        return {'projects': projects, 'parsed_at': datetime.datetime.now().strftime('%H:%M:%S')}

    def _parse_activities(self, text):
        """Parse memory log into structured activities, grouped by time."""
        import re
        groups = []
        current_group = None
        current_items = []

        for line in text.split('\n'):
            t = line.strip()
            if not t:
                continue

            # Match time headers: ## HH:MM title or ### HH:MM title
            time_match = re.match(r'^#{2,3}\s+(\d{1,2}:\d{2})\s+(.+)$', t)
            if time_match:
                if current_group and current_items:
                    groups.append({**current_group, 'items': current_items})
                raw_time = time_match.group(1)
                # Pad single-digit hour: 1:37 → 13:37, 9:00 → 09:00
                parts = raw_time.split(':')
                h = int(parts[0])
                # If hour < 8, it's likely PM (13-17)
                if h < 8 and h >= 1:
                    h += 12
                time_str = f"{h:02d}:{parts[1]}"
                title = time_match.group(2).strip()
                # Skip Pre-Compaction sections (duplicates)
                if 'Pre-Compaction' in title or 'pre-compaction' in title:
                    current_group = None
                    current_items = []
                    continue
                current_group = {'time': time_str, 'title': title, 'hour': h}
                current_items = []
                continue

            # Standalone time headers like ## 16:23
            section_match = re.match(r'^#{2,3}\s+(\d{1,2}:\d{2})$', t)
            if section_match:
                if current_group and current_items:
                    groups.append({**current_group, 'items': current_items})
                raw_time = section_match.group(1)
                parts = raw_time.split(':')
                h = int(parts[0])
                if h < 8 and h >= 1:
                    h += 12
                time_str = f"{h:02d}:{parts[1]}"
                current_group = {'time': time_str, 'title': '', 'hour': h}
                current_items = []
                continue

            if not current_group:
                continue

            # Parse items
            clean = t.lstrip('- *').strip()
            if not clean or clean.startswith('---'):
                continue

            # Truncate very long text
            if len(clean) > 120:
                clean = clean[:117] + '...'

            item = {'text': clean, 'type': 'normal'}
            if any(k in clean for k in ['✅', '完成', '成功', 'auto_promoted', 'PASSED', 'passing']):
                item['type'] = 'success'
            elif any(k in clean for k in ['❌', '失败', '错误', 'quarantine', '过滤', 'FAILED', '拒绝']):
                item['type'] = 'error'
            elif any(k in clean for k in ['⚠️', '注意', '⚠', 'rate-limit', '跳过', '限流']):
                item['type'] = 'warning'
            elif any(k in clean for k in ['心跳', 'HB:', 'heartbeat', 'active, credit']):
                item['type'] = 'heartbeat'

            current_items.append(item)

        if current_group and current_items:
            groups.append({**current_group, 'items': current_items})

        # Sort reverse chronological (newest first)
        groups.sort(key=lambda g: g['time'], reverse=True)

        # Summarize large groups: keep first 5 items + summary line
        for g in groups:
            if len(g['items']) > 8:
                kept = g['items'][:5]
                remaining = g['items'][5:]
                r_ok = sum(1 for i in remaining if i['type'] == 'success')
                r_err = sum(1 for i in remaining if i['type'] == 'error')
                summary_parts = []
                if r_ok: summary_parts.append(f'✅ {r_ok} 成功')
                if r_err: summary_parts.append(f'❌ {r_err} 失败')
                summary_parts.append(f'+{len(remaining)} 条')
                kept.append({'text': '　↳ ' + ' | '.join(summary_parts), 'type': 'summary'})
                g['items'] = kept

        # Add period labels
        periods = {'morning': '🌅 上午', 'afternoon': '🌤️ 下午', 'evening': '🌆 傍晚'}
        for g in groups:
            h = g.get('hour', 12)
            if h < 12:
                g['period'] = 'morning'
            elif h < 17:
                g['period'] = 'afternoon'
            else:
                g['period'] = 'evening'
            del g['hour']

        total = sum(len([i for i in g['items'] if i['type'] != 'summary']) for g in groups)
        successes = sum(1 for g in groups for i in g['items'] if i['type'] == 'success')
        errors = sum(1 for g in groups for i in g['items'] if i['type'] == 'error')

        return {'groups': groups, 'total': total, 'successes': successes, 'errors': errors}

    def log_message(self, *a):
        pass

if __name__ == '__main__':
    os.chdir(WORKSPACE / 'dashboard')
    print(f"Dashboard running on port {PORT}")
    HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
