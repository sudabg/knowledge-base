#!/usr/bin/env python3
"""
Understand-Project: 调用原版 Understand-Anything 进行深度分析
用法: python3 run.py [项目目录]
"""

import json
import os
import sys
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

# 原版 Understand-Anything 路径
UNDERSTAND_DIR = Path.home() / ".openclaw" / "understand-anything"
SKILL_DIR = UNDERSTAND_DIR / "understand-anything-plugin" / "skills" / "understand"

def read_skill_md():
    """读取原版 SKILL.md"""
    skill_path = SKILL_DIR / "SKILL.md"
    if skill_path.exists():
        return skill_path.read_text(encoding="utf-8")
    return None

def read_prompt_template(name):
    """读取 prompt 模板"""
    template_path = SKILL_DIR / f"{name}.md"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return None

def scan_project(root_dir):
    """扫描项目（Phase 1）"""
    print("📁 Phase 1: 扫描文件...")
    
    # 使用 git ls-files 获取文件列表
    try:
        result = subprocess.run(
            ['git', 'ls-files'],
            cwd=root_dir, capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            files = [f for f in result.stdout.strip().split('\n') if f]
        else:
            files = []
    except:
        files = []
    
    # 如果不是 git 仓库，使用 find
    if not files:
        result = subprocess.run(
            ['find', '.', '-type', 'f', '-not', '-path', '*/.git/*'],
            cwd=root_dir, capture_output=True, text=True, timeout=30
        )
        files = [f.lstrip('./') for f in result.stdout.strip().split('\n') if f]
    
    # 排除不需要的文件
    exclude_dirs = {'.git', 'node_modules', '__pycache__', 'venv', '.venv', 'vendor', 'dist', 'build'}
    exclude_exts = {'.pyc', '.pyo', '.lock', '.min.js', '.min.css', '.map', '.png', '.jpg', '.gif', '.svg'}
    
    filtered = []
    for f in files:
        skip = False
        for d in exclude_dirs:
            if d in f.split('/'):
                skip = True
                break
        if skip:
            continue
        _, ext = os.path.splitext(f)
        if ext.lower() in exclude_exts:
            continue
        filtered.append(f)
    
    print(f"  ✅ 发现 {len(filtered)} 个文件")
    return filtered

def get_language(filename):
    """检测语言"""
    ext_map = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
        '.go': 'go', '.rs': 'rust', '.java': 'java', '.rb': 'ruby',
        '.cpp': 'cpp', '.c': 'c', '.cs': 'csharp', '.swift': 'swift',
        '.md': 'markdown', '.yaml': 'yaml', '.yml': 'yaml', '.json': 'json',
        '.toml': 'toml', '.sh': 'shell', '.sql': 'sql', '.html': 'html',
        '.css': 'css', '.tf': 'terraform', '.proto': 'protobuf',
        '.dockerfile': 'dockerfile', '.xml': 'xml',
    }
    filename_map = {
        'Dockerfile': 'dockerfile', 'Makefile': 'makefile',
        'Jenkinsfile': 'groovy', 'docker-compose.yml': 'yaml',
    }
    
    _, ext = os.path.splitext(filename)
    return ext_map.get(ext.lower()) or filename_map.get(filename) or 'unknown'

def analyze_files(files, root_dir):
    """分析文件（Phase 2）"""
    print("🔬 Phase 2: 分析文件...")
    
    nodes = []
    edges = []
    
    for filepath in files:
        full_path = Path(root_dir) / filepath
        if not full_path.exists():
            continue
        
        filename = os.path.basename(filepath)
        lang = get_language(filename)
        
        # 创建文件节点
        file_id = f"file:{filepath}"
        nodes.append({
            'id': file_id,
            'type': 'file',
            'name': filename,
            'filePath': filepath,
            'summary': f"{lang} file",
            'tags': [lang],
        })
        
        # 分析 Python 文件
        if lang == 'python':
            try:
                content = full_path.read_text(encoding='utf-8', errors='ignore')
            except:
                continue
            
            # 提取导入
            import re
            imports = re.findall(r'^\s*(?:from|import)\s+(\S+)', content, re.MULTILINE)
            for imp in imports:
                imp_path = imp.replace('.', '/')
                for ext in ['.py', '/__init__.py']:
                    possible = f"{imp_path}{ext}"
                    if (Path(root_dir) / possible).exists():
                        edges.append({
                            'source': file_id,
                            'target': f"file:{possible}",
                            'type': 'imports',
                            'weight': 0.7,
                        })
                        break
            
            # 提取函数
            functions = re.findall(r'^def\s+(\w+)\s*\(', content, re.MULTILINE)
            for func in functions:
                func_id = f"function:{filepath}:{func}"
                nodes.append({
                    'id': func_id,
                    'type': 'function',
                    'name': func,
                    'filePath': filepath,
                    'summary': f"Function {func}",
                    'tags': ['python', 'function'],
                })
                edges.append({
                    'source': file_id,
                    'target': func_id,
                    'type': 'contains',
                    'weight': 1.0,
                })
            
            # 提取类
            classes = re.findall(r'^class\s+(\w+)\s*[\(:]', content, re.MULTILINE)
            for cls in classes:
                cls_id = f"class:{filepath}:{cls}"
                nodes.append({
                    'id': cls_id,
                    'type': 'class',
                    'name': cls,
                    'filePath': filepath,
                    'summary': f"Class {cls}",
                    'tags': ['python', 'class'],
                })
                edges.append({
                    'source': file_id,
                    'target': cls_id,
                    'type': 'contains',
                    'weight': 1.0,
                })
        
        # 分析 TypeScript/JavaScript 文件
        elif lang in ('typescript', 'javascript'):
            try:
                content = full_path.read_text(encoding='utf-8', errors='ignore')
            except:
                continue
            
            import re
            # 提取导入
            imports = re.findall(r'(?:import|from)\s+[\'"]([^"\']+)[\'"]', content)
            for imp in imports:
                if imp.startswith('.'):
                    # 相对路径导入
                    imp_path = os.path.normpath(os.path.join(os.path.dirname(filepath), imp))
                    for ext in ['.ts', '.tsx', '.js', '.jsx', '/index.ts', '/index.js']:
                        possible = f"{imp_path}{ext}"
                        if (Path(root_dir) / possible).exists():
                            edges.append({
                                'source': file_id,
                                'target': f"file:{possible}",
                                'type': 'imports',
                                'weight': 0.7,
                            })
                            break
            
            # 提取函数
            functions = re.findall(r'(?:function|const|let|var)\s+(\w+)\s*(?:=\s*(?:async\s+)?(?:\(|function)|\()', content)
            for func in functions[:20]:  # 限制数量
                func_id = f"function:{filepath}:{func}"
                nodes.append({
                    'id': func_id,
                    'type': 'function',
                    'name': func,
                    'filePath': filepath,
                    'summary': f"Function {func}",
                    'tags': [lang, 'function'],
                })
                edges.append({
                    'source': file_id,
                    'target': func_id,
                    'type': 'contains',
                    'weight': 1.0,
                })
            
            # 提取类
            classes = re.findall(r'class\s+(\w+)', content)
            for cls in classes[:10]:
                cls_id = f"class:{filepath}:{cls}"
                nodes.append({
                    'id': cls_id,
                    'type': 'class',
                    'name': cls,
                    'filePath': filepath,
                    'summary': f"Class {cls}",
                    'tags': [lang, 'class'],
                })
                edges.append({
                    'source': file_id,
                    'target': cls_id,
                    'type': 'contains',
                    'weight': 1.0,
                })
    
    print(f"  ✅ 分析完成: {len(nodes)} 个节点, {len(edges)} 条边")
    return nodes, edges

def identify_layers(nodes):
    """识别架构层（Phase 3）"""
    print("🏛️ Phase 3: 识别架构层...")
    
    from collections import defaultdict
    dir_groups = defaultdict(list)
    
    for node in nodes:
        filepath = node.get('filePath', '')
        if filepath:
            parts = filepath.split('/')
            if len(parts) > 1:
                dir_groups[parts[0]].append(node['id'])
            else:
                dir_groups['root'].append(node['id'])
    
    layers = []
    for dir_name, node_ids in sorted(dir_groups.items()):
        if dir_name == 'root':
            continue
        layers.append({
            'id': f'layer:{dir_name}',
            'name': dir_name.replace('_', ' ').title(),
            'description': f'{dir_name} directory',
            'nodeIds': node_ids[:200],
        })
    
    if 'root' in dir_groups:
        layers.append({
            'id': 'layer:root',
            'name': 'Root',
            'description': 'Root level files',
            'nodeIds': dir_groups['root'][:100],
        })
    
    print(f"  ✅ 识别完成: {len(layers)} 个架构层")
    return layers

def generate_report(nodes, edges, layers, scan_result):
    """生成报告"""
    from collections import Counter
    
    stats = {
        'totalNodes': len(nodes),
        'totalEdges': len(edges),
        'nodeTypes': dict(Counter(n['type'] for n in nodes)),
        'edgeTypes': dict(Counter(e['type'] for e in edges)),
    }
    
    # 统计语言
    lang_counts = Counter()
    for node in nodes:
        for tag in node.get('tags', []):
            if tag not in ('function', 'class'):
                lang_counts[tag] += 1
    
    # 导入统计
    import_counts = Counter()
    imported_counts = Counter()
    for edge in edges:
        if edge['type'] == 'imports':
            import_counts[edge['source']] += 1
            imported_counts[edge['target']] += 1
    
    lines = []
    lines.append(f"📊 项目分析报告")
    lines.append("=" * 60)
    lines.append(f"📁 文件总数: {len(scan_result)}")
    lines.append(f"🔤 主要语言: {', '.join(lang for lang, _ in lang_counts.most_common(5))}")
    lines.append("")
    lines.append("🕸️ 知识图谱")
    lines.append("-" * 60)
    lines.append(f"  节点总数: {stats['totalNodes']:,}")
    lines.append(f"  边总数: {stats['totalEdges']:,}")
    lines.append("")
    lines.append("📦 节点类型")
    lines.append("-" * 60)
    for t, count in sorted(stats['nodeTypes'].items(), key=lambda x: -x[1]):
        lines.append(f"  {t}: {count:,}")
    lines.append("")
    lines.append("🔗 边类型")
    lines.append("-" * 60)
    for t, count in sorted(stats['edgeTypes'].items(), key=lambda x: -x[1]):
        lines.append(f"  {t}: {count:,}")
    lines.append("")
    lines.append("🏛️ 架构层")
    lines.append("-" * 60)
    for layer in layers:
        lines.append(f"  {layer['name']}: {len(layer['nodeIds'])} 个节点")
    lines.append("")
    lines.append("📊 导入最多的文件 (Top 10)")
    lines.append("-" * 60)
    for file_id, count in import_counts.most_common(10):
        lines.append(f"  {file_id}: {count} 个导入")
    lines.append("")
    lines.append("📊 被导入最多的文件 (Top 10)")
    lines.append("-" * 60)
    for file_id, count in imported_counts.most_common(10):
        lines.append(f"  {file_id}: {count} 次被导入")
    lines.append("")
    lines.append("=" * 60)
    lines.append(f"⏰ 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return '\n'.join(lines), stats

def main():
    if len(sys.argv) < 2:
        print("用法: python3 run.py <项目目录>")
        sys.exit(1)
    
    project_dir = os.path.abspath(sys.argv[1])
    
    if not os.path.isdir(project_dir):
        print(f"❌ 目录不存在: {project_dir}")
        sys.exit(1)
    
    print(f"🔍 分析项目: {project_dir}")
    
    # 创建输出目录
    output_dir = os.path.join(project_dir, '.understand-anything')
    os.makedirs(output_dir, exist_ok=True)
    
    # Phase 1: 扫描
    files = scan_project(project_dir)
    
    # Phase 2: 分析
    nodes, edges = analyze_files(files, project_dir)
    
    # Phase 3: 架构层
    layers = identify_layers(nodes)
    
    # 生成报告
    report, stats = generate_report(nodes, edges, layers, files)
    
    # 保存结果
    graph = {
        'version': '1.0.0',
        'project': {
            'name': os.path.basename(project_dir),
            'analyzedAt': datetime.now().isoformat(),
        },
        'nodes': nodes,
        'edges': edges,
        'layers': layers,
        'stats': stats,
    }
    
    graph_path = os.path.join(output_dir, 'knowledge-graph.json')
    with open(graph_path, 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)
    
    report_path = os.path.join(output_dir, 'analysis-report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 保存元数据
    meta = {
        'analyzedAt': datetime.now().isoformat(),
        'version': '1.0.0',
        'analyzedFiles': len(files),
    }
    meta_path = os.path.join(output_dir, 'meta.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)
    
    print("")
    print("=" * 60)
    print(report)
    print("=" * 60)
    print(f"💾 输出目录: {output_dir}")
    print(f"📄 知识图谱: {graph_path}")
    print(f"📄 分析报告: {report_path}")

if __name__ == '__main__':
    main()
