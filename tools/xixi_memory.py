#!/usr/bin/env python3
"""
XiXi Memory Engine v1.0
三合一：搜索索引 + 学习闭环 + 自动衰减
"""
import os, json, hashlib, time, re, glob
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = os.environ.get("WORKSPACE", "/home/gem/workspace/agent/workspace")
MEMORY_DIR = os.path.join(WORKSPACE, "memory")
LEARNINGS_DIR = os.path.join(WORKSPACE, ".learnings")
INDEX_FILE = os.path.join(LEARNINGS_DIR, "memory_index.json")
LOOP_FILE = os.path.join(LEARNINGS_DIR, "learning_loop.json")

class MemoryIndex:
    """搜索索引：为所有 memory/*.md 建立关键词索引"""
    
    def __init__(self):
        self.index = {"version": 1, "updated": None, "entries": {}}
        self._load()
    
    def _load(self):
        if os.path.exists(INDEX_FILE):
            with open(INDEX_FILE) as f:
                self.index = json.load(f)
    
    def _save(self):
        os.makedirs(LEARNINGS_DIR, exist_ok=True)
        with open(INDEX_FILE, 'w') as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)
    
    def _extract_keywords(self, text):
        """提取关键词（中英文混合）"""
        en_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', text.lower()))
        cn_phrases = set(re.findall(r'[\u4e00-\u9fff]{2,4}', text))
        tech_terms = set(re.findall(r'\b[a-zA-Z]+[-_][a-zA-Z]+\b', text.lower()))
        return list(en_words | cn_phrases | tech_terms)
    
    def rebuild(self):
        """重建整个索引"""
        entries = {}
        md_files = glob.glob(os.path.join(MEMORY_DIR, "*.md"))
        md_files += glob.glob(os.path.join(MEMORY_DIR, "**/*.md"), recursive=True)
        
        for fpath in md_files:
            rel = os.path.relpath(fpath, WORKSPACE)
            try:
                with open(fpath) as f:
                    content = f.read()
                stat = os.stat(fpath)
                keywords = self._extract_keywords(content)
                entries[rel] = {
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "keywords": keywords[:50],
                    "keyword_count": len(keywords),
                    "sha256": hashlib.sha256(content.encode()).hexdigest()[:16]
                }
            except Exception as e:
                entries[rel] = {"error": str(e)}
        
        self.index["entries"] = entries
        self.index["updated"] = datetime.now().isoformat()
        self.index["file_count"] = len(entries)
        self._save()
        return f"✅ 索引已重建：{len(entries)} 个文件"
    
    def search(self, query, limit=5):
        """搜索记忆文件"""
        query_words = set(re.findall(r'[\u4e00-\u9fff]{2,}|\b[a-zA-Z]{3,}\b', query.lower()))
        scores = []
        
        for rel, meta in self.index.get("entries", {}).items():
            if "error" in meta:
                continue
            keywords = set(meta.get("keywords", []))
            matches = query_words & keywords
            if matches:
                score = len(matches) / len(query_words) if query_words else 0
                scores.append((rel, score, len(matches)))
        
        scores.sort(key=lambda x: (-x[1], -x[2]))
        results = []
        for rel, score, matches in scores[:limit]:
            results.append(f"  [{score:.0%}] {rel} ({matches} keywords)")
        return "\n".join(results) if results else "  无匹配结果"


class LearningLoop:
    """学习闭环：感知→分析→决策→行动→验证→固化"""
    
    def __init__(self):
        self.state = self._load()
    
    def _load(self):
        if os.path.exists(LOOP_FILE):
            with open(LOOP_FILE) as f:
                return json.load(f)
        return {"cycles": [], "current": None}
    
    def _save(self):
        os.makedirs(LEARNINGS_DIR, exist_ok=True)
        with open(LOOP_FILE, 'w') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
    
    def start_cycle(self, observation):
        """开始新学习周期：感知"""
        cycle = {
            "id": hashlib.md5(f"{time.time()}".encode()).hexdigest()[:8],
            "started": datetime.now().isoformat(),
            "phase": "observed",
            "observation": observation,
            "analysis": None,
            "decision": None,
            "action": None,
            "verified": None,
            "solidified": False
        }
        self.state["current"] = cycle
        self._save()
        return f"🔄 新学习周期 [{cycle['id']}]: {observation[:80]}"
    
    def analyze(self, analysis):
        """分析阶段"""
        if not self.state.get("current"):
            return "❌ 没有活跃的学习周期"
        self.state["current"]["analysis"] = analysis
        self.state["current"]["phase"] = "analyzed"
        self._save()
        return f"📊 分析完成: {analysis[:80]}"
    
    def decide(self, decision):
        """决策阶段"""
        if not self.state.get("current"):
            return "❌ 没有活跃的学习周期"
        self.state["current"]["decision"] = decision
        self.state["current"]["phase"] = "decided"
        self._save()
        return f"🎯 决策: {decision[:80]}"
    
    def act(self, action_result):
        """行动阶段"""
        if not self.state.get("current"):
            return "❌ 没有活跃的学习周期"
        self.state["current"]["action"] = action_result
        self.state["current"]["phase"] = "acted"
        self._save()
        return f"⚡ 行动: {action_result[:80]}"
    
    def verify(self, success, notes=""):
        """验证阶段"""
        if not self.state.get("current"):
            return "❌ 没有活跃的学习周期"
        self.state["current"]["verified"] = success
        self.state["current"]["verify_notes"] = notes
        self.state["current"]["phase"] = "verified"
        self._save()
        status = "✅ 成功" if success else "❌ 失败"
        return f"🔍 验证: {status} - {notes[:60]}"
    
    def solidify(self, target_file=None):
        """固化阶段：写入 LEARNINGS.md 或指定文件"""
        if not self.state.get("current"):
            return "❌ 没有活跃的学习周期"
        
        cycle = self.state["current"]
        if not cycle.get("verified"):
            return "⚠️ 还未验证，不能固化"
        
        entry = f"\n### [{cycle['id']}] {cycle['observation'][:60]}\n"
        entry += f"- 分析: {cycle.get('analysis', 'N/A')}\n"
        entry += f"- 决策: {cycle.get('decision', 'N/A')}\n"
        entry += f"- 结果: {cycle.get('action', 'N/A')}\n"
        entry += f"- 验证: {'✅' if cycle.get('verified') else '❌'} {cycle.get('verify_notes', '')}\n"
        entry += f"- 时间: {cycle['started']}\n"
        
        target = target_file or os.path.join(LEARNINGS_DIR, "LEARNINGS.md")
        with open(target, 'a') as f:
            f.write(entry)
        
        cycle["solidified"] = True
        cycle["phase"] = "solidified"
        cycle["completed"] = datetime.now().isoformat()
        self.state["cycles"].append(cycle)
        self.state["current"] = None
        self._save()
        return f"💾 固化完成 → {os.path.basename(target)}"
    
    def status(self):
        """查看当前状态"""
        cur = self.state.get("current")
        if not cur:
            total = len(self.state.get("cycles", []))
            return f"📊 学习循环：空闲（已完成 {total} 个周期）"
        return f"📊 当前 [{cur['id']}] 阶段: {cur['phase']}\n   观察: {cur['observation'][:60]}"


class MemoryDecay:
    """自动衰减：基于时间戳和访问频率"""
    
    @staticmethod
    def scan(days_threshold=7, min_size=100):
        """扫描需要衰减的记忆"""
        results = []
        cutoff = datetime.now() - timedelta(days=days_threshold)
        
        for fpath in glob.glob(os.path.join(MEMORY_DIR, "*.md")):
            stat = os.stat(fpath)
            modified = datetime.fromtimestamp(stat.st_mtime)
            
            if modified < cutoff and stat.st_size > min_size:
                rel = os.path.relpath(fpath, MEMORY_DIR)
                age_days = (datetime.now() - modified).days
                results.append({
                    "file": rel,
                    "age_days": age_days,
                    "size": stat.st_size,
                    "action": "compress" if stat.st_size > 5000 else "review"
                })
        return results
    
    @staticmethod
    def apply_decay(file_path, mode="compress"):
        """应用衰减：压缩或归档"""
        full_path = os.path.join(MEMORY_DIR, file_path) if not file_path.startswith("/") else file_path
        
        if not os.path.exists(full_path):
            return f"❌ 文件不存在: {file_path}"
        
        with open(full_path) as f:
            content = f.read()
        
        original_size = len(content)
        
        if mode == "compress":
            lines = content.split('\n')
            compressed = []
            for line in lines:
                if line.startswith('#') or line.startswith('-') or line.startswith('*'):
                    compressed.append(line)
                elif any(kw in line for kw in ['✅', '❌', '⚠️', '重要', '关键', '教训']):
                    compressed.append(line)
                elif len(line.strip()) > 100:
                    compressed.append(line[:100] + '...')
            
            new_content = '\n'.join(compressed)
            backup_path = full_path + '.bak'
            os.rename(full_path, backup_path)
            
            with open(full_path, 'w') as f:
                f.write(new_content)
            
            ratio = len(new_content) / original_size * 100
            return f"🗜️ 压缩完成: {file_path} ({original_size}→{len(new_content)} chars, {ratio:.0f}%)"
        
        elif mode == "archive":
            archive_dir = os.path.join(MEMORY_DIR, "archive")
            os.makedirs(archive_dir, exist_ok=True)
            dest = os.path.join(archive_dir, os.path.basename(file_path))
            os.rename(full_path, dest)
            return f"📦 归档完成: {file_path} → archive/"
        
        return f"⚠️ 未知模式: {mode}"


# CLI 入口
if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    
    idx = MemoryIndex()
    loop = LearningLoop()
    decay = MemoryDecay()
    
    if cmd == "index":
        print(idx.rebuild())
    elif cmd == "search" and len(sys.argv) > 2:
        query = " ".join(sys.argv[2:])
        print(f"🔍 搜索: {query}")
        print(idx.search(query))
    elif cmd == "loop":
        sub = sys.argv[2] if len(sys.argv) > 2 else "status"
        if sub == "start" and len(sys.argv) > 3:
            print(loop.start_cycle(" ".join(sys.argv[3:])))
        elif sub == "status":
            print(loop.status())
        elif sub == "solidify":
            print(loop.solidify())
        else:
            print("用法: loop [start <观察>|status|solidify]")
    elif cmd == "decay":
        results = decay.scan()
        if not results:
            print("✅ 没有需要衰减的记忆")
        else:
            for r in results:
                print(f"  [{r['age_days']}天] {r['file']} ({r['size']}B) → {r['action']}")
    elif cmd == "boot":
        """启动身份加载：一键输出 session 所需上下文"""
        parts = []
        
        # SOUL.md 核心身份
        soul_path = os.path.join(WORKSPACE, "SOUL.md")
        if os.path.exists(soul_path):
            with open(soul_path) as f:
                lines = [l for l in f.readlines() if l.strip() and not l.startswith('#')]
            parts.append("=== SOUL ===")
            parts.extend(lines[:15])
        
        # USER.md 用户信息
        user_path = os.path.join(WORKSPACE, "USER.md")
        if os.path.exists(user_path):
            with open(user_path) as f:
                lines = [l for l in f.readlines() if l.strip() and l.startswith('-')]
            parts.append("\n=== USER ===")
            parts.extend(lines[:10])
        
        # 今日记忆
        today = datetime.now().strftime("%Y-%m-%d")
        today_path = os.path.join(MEMORY_DIR, f"{today}.md")
        if os.path.exists(today_path):
            with open(today_path) as f:
                content = f.read()
            parts.append(f"\n=== TODAY ({today}) ===")
            parts.extend(content.split('\n')[:30])
        else:
            parts.append(f"\n=== TODAY ({today}) === (无记录)")
        
        # MEMORY.md 快速上下文
        mem_path = os.path.join(WORKSPACE, "MEMORY.md")
        if os.path.exists(mem_path):
            with open(mem_path) as f:
                lines = f.readlines()
            in_ctx = False
            for l in lines:
                if 'Quick Context' in l:
                    in_ctx = True
                elif in_ctx and l.startswith('##'):
                    break
                elif in_ctx:
                    parts.append(l.rstrip())
        
        print('\n'.join(parts))
    elif cmd == "help":
        print("""
XiXi Memory Engine v1.0
命令:
  index              重建搜索索引
  search <关键词>     搜索记忆
  boot               启动身份加载
  loop start <观察>  开始学习周期
  loop status        查看学习状态
  loop solidify      固化当前学习
  decay              扫描需要衰减的记忆
        """)
    else:
        print(f"未知命令: {cmd}，用 help 查看帮助")
