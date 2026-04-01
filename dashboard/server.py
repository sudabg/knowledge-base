#!/usr/bin/env python3
"""
小哩子 Evolution Dashboard - Backend API
Serves project plans, node status, and real-time logs
"""
import json, os, glob, datetime, re, urllib.request
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

WORKSPACE = Path('/home/gem/workspace/agent/workspace')
PORT = int(os.getenv('DASHBOARD_PORT', '8888'))

class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/status':
            self.serve_json(self.get_status())
        elif self.path == '/api/projects':
            self.serve_json(self.get_projects())
        elif self.path == '/api/today':
            self.serve_json(self.get_today_tasks())
        elif self.path == '/api/memory':
            self.serve_json(self.get_memory())
        elif self.path == '/api/logs':
            self.serve_json(self.get_logs())
        elif self.path == '/api/node':
            self.serve_json(self.get_node())
        elif self.path == '/api/resources':
            self.serve_json(self.get_resources())
        elif self.path == '/api/activities':
            self.serve_json(self.get_activities())
        elif self.path == '/api/completed':
            self.serve_json(self.get_completed())
        elif self.path == '/' or self.path == '/index.html':
            self.serve_file('index.html', 'text/html')
        else:
            super().do_GET()
    
    def serve_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode())
    
    def serve_file(self, filename, content_type):
        filepath = WORKSPACE / 'dashboard' / filename
        if filepath.exists():
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.end_headers()
            self.wfile.write(filepath.read_bytes())
        else:
            self.send_error(404)
    
    def get_status(self):
        now = datetime.datetime.now()
        return {
            'agent': '小哩子 🦞',
            'status': 'active',
            'uptime': 'running',
            'time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'model': 'Hunter Alpha',
            'channel': 'feishu'
        }
    
    def get_projects(self):
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        plans_file = WORKSPACE / 'docs' / f'project-plans-{today}.md'
        # Fallback: try latest available file
        if not plans_file.exists():
            plan_files = sorted(glob.glob(str(WORKSPACE / 'docs' / 'project-plans-*.md')), reverse=True)
            if plan_files:
                plans_file = Path(plan_files[0])
        if plans_file.exists():
            content = plans_file.read_text()
            projects = []
            current_project = None
            current_phase = None
            def _finish_project(proj):
                if current_phase:
                    proj['phases'].append(current_phase)
                all_tasks = [t for ph in proj['phases'] for t in ph['tasks']]
                done = sum(1 for t in all_tasks if t['done'])
                total = len(all_tasks)
                proj['done_count'] = done
                proj['total_count'] = total
                proj['progress'] = round(done / total * 100) if total > 0 else 0

            for line in content.split('\n'):
                if line.startswith('## ') and not line.startswith('###') and not line.startswith('## 已完成') and not line.startswith('## 周一') and not line.startswith('## 高通量'):
                    if current_project:
                        _finish_project(current_project)
                        projects.append(current_project)
                        current_phase = None
                    title = line.strip('# ').strip()
                    status = 'in_progress'
                    current_project = {'title': title, 'phases': [], 'status': status}
                    current_phase = None
                elif line.startswith('###') and current_project:
                    if current_phase:
                        current_project['phases'].append(current_phase)
                    phase_name = line.strip('# ').strip()
                    current_phase = {'name': phase_name, 'tasks': []}
                elif line.startswith('**目标**') and current_project:
                    current_project['goal'] = line.split('：', 1)[-1].strip() if '：' in line else line.split(':', 1)[-1].strip()
                elif line.startswith('- [x]') and current_project:
                    if not current_phase:
                        current_phase = {'name': '任务', 'tasks': []}
                    current_phase['tasks'].append({'text': line[6:].strip(), 'done': True})
                elif line.startswith('- [ ]') and current_project:
                    if not current_phase:
                        current_phase = {'name': '任务', 'tasks': []}
                    current_phase['tasks'].append({'text': line[6:].strip(), 'done': False})
            if current_project:
                _finish_project(current_project)
                projects.append(current_project)
            return {'projects': projects}
        return {'projects': []}
    
    def get_today_tasks(self):
        """Extract today's actionable tasks from project-plans (T-001, S-001 format or any checklist item)"""
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        plans_file = WORKSPACE / 'docs' / f'project-plans-{today}.md'
        if not plans_file.exists():
            plan_files = sorted(glob.glob(str(WORKSPACE / 'docs' / 'project-plans-*.md')), reverse=True)
            if plan_files:
                plans_file = Path(plan_files[0])
        
        tasks = []
        seen_ids = set()
        if plans_file.exists():
            content = plans_file.read_text()
            # Find the "已完成" sections to exclude carried-over tasks from pending count
            in_completed_section = False
            for line in content.split('\n'):
                t = line.strip()
                # Detect completed sections
                if re.match(r'^#{1,3}\s*已完[成结]', t):
                    in_completed_section = True
                    continue
                # New top-level section resets completed flag
                if re.match(r'^#{1,2}\s+', t) and not re.match(r'^#{3,}\s+', t):
                    in_completed_section = False

                # Match task items: - [ ] or - [x]
                if t.startswith('- [') and ']' in t:
                    done = t.startswith('- [x]')
                    text = t.split(']', 1)[1].strip()
                    # Strip leading priority markers like **P0:**, **P1:**
                    text = re.sub(r'^\*\*[pP]\d:\*\*\s*', '', text)
                    # Find task ID (T-001, S-001, T-001_30, etc.)
                    id_match = re.search(r'[TS]-\d+(?:_\d+)?', text)
                    if id_match:
                        task_id = id_match.group(0)
                        # Clean duplicate ID prefix from text (e.g., "T-001: T-001: ..." -> "T-001: ...")
                        cleaned = re.sub(r'^' + re.escape(task_id) + r':\s*', '', text)
                        if cleaned != text and cleaned.startswith(task_id):
                            # Still starts with ID, strip again
                            cleaned = re.sub(r'^' + re.escape(task_id) + r':\s*', '', cleaned)
                        display_text = cleaned if cleaned else text
                    else:
                        task_id = f'AUTO-{abs(hash(text)) % 10000:04d}'
                        display_text = text
                    
                    if task_id in seen_ids:
                        continue
                    seen_ids.add(task_id)

                    # Determine priority from context (look for P0/P1/P2 before this line)
                    priority = 'normal'
                    
                    tasks.append({
                        'id': task_id,
                        'text': display_text,
                        'done': done,
                        'carried': in_completed_section,
                        'type': 'short-term' if task_id.startswith('S-') else 'task'
                    })

        # Only show active (non-carried) tasks in the main view
        active_tasks = [t for t in tasks if not t.get('carried')]
        active_tasks.sort(key=lambda x: x['id'])
        total = len(active_tasks)
        done_count = sum(1 for t in active_tasks if t['done'])
        return {
            'date': today,
            'tasks': active_tasks,
            'total': total,
            'done': done_count,
            'pending': total - done_count
        }
    
    def get_memory(self):
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        mem_file = WORKSPACE / 'memory' / f'{today}.md'
        if mem_file.exists():
            content = mem_file.read_text()
            entries = []
            for block in content.split('\n## '):
                lines = block.strip().split('\n')
                if lines:
                    entries.append({
                        'title': lines[0].strip('# ').strip(),
                        'content': '\n'.join(lines[1:]).strip()[:500]
                    })
            return {'date': today, 'entries': entries}
        return {'date': today, 'entries': []}
    
    def get_logs(self):
        log_dir = WORKSPACE / 'logs' / 'evomap'
        logs = []
        if log_dir.exists():
            for f in sorted(log_dir.glob('*.log'), key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
                lines = f.read_text().split('\n')[-50:]
                logs.append({'file': f.name, 'lines': [l for l in lines if l.strip()]})
        return {'logs': logs}
    
    def get_node(self):
        cache_file = WORKSPACE / '.learnings' / 'last_heartbeat.json'
        result = {
            'node_id': 'node_db2f95ffdba95eb6',
            'reputation_score': 0,
            'total_published': 0,
            'total_promoted': 0,
            'total_rejected': 0,
            'credit': 0,
            'quarantine_strikes': 0,
            'reputation_penalty': 0,
            'status': 'unknown',
            'survival': 'unknown',
            'avg_confidence': 0,
            'symbiosis_score': 0,
        }
        # Load from heartbeat cache
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                result.update({
                    'reputation_score': data.get('reputation_score', 0),
                    'total_published': data.get('total_published', 0),
                    'total_promoted': data.get('total_promoted', 0),
                    'total_rejected': data.get('total_rejected', 0),
                    'credit': data.get('credit_balance', data.get('credit', 0)),
                    'available_tasks': data.get('available_tasks', []),
                    'tasks_count': data.get('tasks_count', len(data.get('available_tasks', [])) if isinstance(data.get('available_tasks'), list) else data.get('available_tasks', 0)),
                    'highest_bounty': data.get('highest_bounty', 0),
                    'quarantine_strikes': data.get('quarantine_strikes', 0),
                    'reputation_penalty': data.get('reputation_penalty', 0),
                    'status': data.get('status', 'unknown'),
                    'survival': data.get('survival', 'unknown'),
                    'avg_confidence': data.get('avg_confidence', 0),
                    'symbiosis_score': data.get('symbiosis_score', 0),
                    'completed_tasks': data.get('completed_tasks', 0),
                    'updated': data.get('updated', data.get('timestamp', '')),
                    'error_count': data.get('error_count', 0),
                    'last_error': data.get('last_error', ''),
                })
            except Exception:
                pass
        # Augment with real-time EvoMap API data (avg_confidence, symbiosis)
        try:
            req = urllib.request.Request('https://evomap.ai/a2a/nodes/node_db2f95ffdba95eb6')
            with urllib.request.urlopen(req, timeout=10) as resp:
                evo = json.loads(resp.read())
                result['avg_confidence'] = evo.get('avg_confidence', 0)
                result['symbiosis_score'] = evo.get('symbiosis_score', 0)
                result['total_published'] = evo.get('total_published', result['total_published'])
                result['total_promoted'] = evo.get('total_promoted', result['total_promoted'])
                result['reputation_score'] = evo.get('reputation_score', result['reputation_score'])
                result['survival'] = evo.get('survival_status', result['survival'])
        except Exception:
            pass
        return result
    
    def get_resources(self):
        """Get today's discovered resources"""
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        items = []
        
        # Read from awesome-openclaw discovered folder
        discovered_file = WORKSPACE / 'awesome-openclaw' / 'discovered' / f'{today}.md'
        if discovered_file.exists():
            content = discovered_file.read_text()
            current_item = {}
            for line in content.split('\n'):
                line = line.strip()
                # Match numbered items: 1. **Name** ⭐count
                import re
                num_match = re.match(r'^\d+\.\s+\*\*([^*]+)\*\*\s*(?:⭐[\d,]+)?', line)
                if num_match:
                    if current_item.get('name'):
                        items.append(current_item)
                    current_item = {'name': num_match.group(1).strip(), 'url': '', 'description': '', 'status': '新发现', 'source': 'resource-scout'}
                    continue
                # Match link line
                if line.startswith('- **链接**:') and current_item:
                    current_item['url'] = line.split(':', 1)[-1].strip()
                # Match description
                if line.startswith('- **一句话**:') and current_item:
                    current_item['description'] = line.split(':', 1)[-1].strip()[:100]
                # Match legacy format: - [Name](url)
                md_match = re.match(r'^- \[([^\]]+)\]\(([^)]+)\)\s*-?\s*(.*)', line)
                if md_match:
                    items.append({
                        'name': md_match.group(1),
                        'url': md_match.group(2),
                        'description': md_match.group(3)[:100],
                        'status': '新发现',
                        'source': 'deep-dive'
                    })
            if current_item.get('name'):
                items.append(current_item)
        
        # Also check today's daily log for resource mentions
        daily_log = WORKSPACE / 'memory' / f'{today}.md'
        if daily_log.exists():
            content = daily_log.read_text()
            for line in content.split('\n'):
                if 'github.com' in line and ('⭐' in line or 'star' in line.lower()):
                    items.append({
                        'name': line.strip()[:80],
                        'url': '',
                        'description': '',
                        'status': '发现',
                        'source': 'daily'
                    })
        
        # Add from awesome-openclaw README recent additions
        readme = WORKSPACE / 'awesome-openclaw' / 'README.md'
        if readme.exists():
            content = readme.read_text()
            in_discovered = False
            for line in content.split('\n'):
                if 'Discovered from Awesome' in line:
                    in_discovered = True
                elif line.startswith('## ') and in_discovered:
                    break
                elif in_discovered and line.startswith('- ['):
                    import re
                    m = re.match(r'- \[([^\]]+)\]\(([^)]+)\)\s*-?\s*(.*)', line)
                    if m:
                        items.append({
                            'name': m.group(1),
                            'url': m.group(2),
                            'description': m.group(3)[:100],
                            'status': '已收录',
                            'source': 'awesome-list'
                        })
        
        return {'date': today, 'items': items[:50]}
    
    def get_activities(self):
        """Parse memory log into structured activities"""
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        mem_file = WORKSPACE / 'memory' / f'{today}.md'
        if not mem_file.exists():
            return {'groups': [], 'total': 0, 'successes': 0, 'errors': 0}
        
        text = mem_file.read_text()
        groups = []
        current_group = None
        current_items = []

        for line in text.split('\n'):
            t = line.strip()
            if not t:
                continue

            # Match time headers: ## HH:MM title, ### HH:MM title, or ## Title (HH:MM)
            time_match = re.match(r'^#{2,3}\s+(\d{1,2}:\d{2})\s+(.+)$', t)
            paren_match = re.match(r'^#{2,3}\s+(.+?)\s*[（(](\d{1,2}:\d{2})\s*[）)]\s*$', t)
            if time_match:
                if current_group and current_items:
                    groups.append({**current_group, 'items': current_items})
                raw_time = time_match.group(1)
                parts = raw_time.split(':')
                h = int(parts[0])
                time_str = f"{h:02d}:{parts[1]}"
                title = time_match.group(2).strip()
                if 'Pre-Compaction' in title or 'pre-compaction' in title:
                    current_group = None
                    current_items = []
                    continue
                current_group = {'time': time_str, 'title': title, 'hour': h}
                current_items = []
                continue
            elif paren_match:
                if current_group and current_items:
                    groups.append({**current_group, 'items': current_items})
                title = paren_match.group(1).strip()
                raw_time = paren_match.group(2)
                parts = raw_time.split(':')
                h = int(parts[0])
                time_str = f"{h:02d}:{parts[1]}"
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

        # Summarize large groups
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
        
        # Type breakdown for display
        type_counts = {}
        for g in groups:
            for i in g['items']:
                t = i.get('type', 'normal')
                type_counts[t] = type_counts.get(t, 0) + 1

        return {'groups': groups, 'total': total, 'successes': successes, 'errors': errors, 'type_counts': type_counts}
    
    def get_completed(self):
        """Get completed projects from P.md"""
        p_file = WORKSPACE / 'P.md'
        if p_file.exists():
            content = p_file.read_text()
            return {'content': content[:3000], 'exists': True}
        return {'content': '# 暂无已完成项目', 'exists': False}
    
    def log_message(self, format, *args):
        pass  # Silence logs

if __name__ == '__main__':
    os.chdir(WORKSPACE / 'dashboard')
    server = HTTPServer(('0.0.0.0', PORT), DashboardHandler)
    print(f'🦞 Dashboard running on http://localhost:{PORT}')
    server.serve_forever()
