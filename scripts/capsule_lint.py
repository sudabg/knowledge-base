#!/usr/bin/env python3
"""
EvoMap Capsule Lint Tool
在发布前自动检测 capsule 安全性和规范性
"""
import re
import sys
import json
from typing import List, Dict, Tuple

# 检测规则

CODE_PATTERNS = [
    (r'def\s+\w+\(', 'Python function definition'),
    (r'function\s+\w+\(', 'JavaScript function'),
    (r'import\s+\w+', 'Import statement'),
    (r'from\s+\w+\s+import', 'Python import'),
    (r'\$\s*\{.*?\}', 'Shell variable expansion'),
    (r'curl\s+', 'Shell curl command'),
    (r'sudo\s+', 'Sudo command'),
    (r'eval\s*\(', 'Code eval'),
    (r'exec\s*\(', 'Code exec'),
    (r'os\.system', 'OS system call'),
    (r'subprocess\.', 'Subprocess call'),
    (r'__import__', 'Dynamic import'),
]

SENSITIVE_PATTERNS = [
    (r'sk-[A-Za-z0-9]{20,}', 'OpenAI-style API key'),
    (r'Bearer\s+[A-Za-z0-9]{15,}', 'Bearer token'),
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'Email address'),
    (r'\b1[3-9]\d{9}\b', 'Chinese phone number'),
    (r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----', 'Private key'),
    (r'password\s*[:=]\s*\S+', 'Hardcoded password'),
]

def check_code_snippet(content: str) -> List[Tuple[str, str, str]]:
    """检测代码片段"""
    issues = []
    for pattern, desc in CODE_PATTERNS:
        matches = re.finditer(pattern, content)
        for m in matches:
            start = max(0, m.start() - 20)
            end = min(len(content), m.end() + 20)
            context = content[start:end].replace('\n', ' ')
            issues.append(('P1', f'code_pattern: {desc}', f'...{context}...'))
    return issues

def check_sensitive_data(content: str) -> List[Tuple[str, str, str]]:
    """检测敏感信息"""
    issues = []
    for pattern, desc in SENSITIVE_PATTERNS:
        matches = re.finditer(pattern, content)
        for m in matches:
            masked = m.group()[:4] + '***' if len(m.group()) > 4 else '***'
            issues.append(('P0', f'sensitive_data: {desc}', f'found: {masked}'))
    return issues

def check_lengths(gene: Dict, capsule: Dict) -> List[Tuple[str, str, str]]:
    """检查长度规范"""
    issues = []
    
    # Strategy steps >= 15 chars
    for i, step in enumerate(gene.get('strategy', [])):
        if len(step) < 15:
            issues.append(('P3', f'strategy_step_too_short', 
                          f'step[{i}]: {len(step)} chars (need 15): "{step[:30]}..."'))
    
    # Signals >= 3 chars
    for sig in gene.get('signals_match', []):
        if len(sig) < 3:
            issues.append(('P3', f'signal_too_short', f'"{sig}": {len(sig)} chars'))
    
    # Capsule content >= 200 chars
    content = capsule.get('content', '')
    if len(content) < 200:
        issues.append(('P3', 'capsule_content_too_short', f'{len(content)} chars (need 200)'))
    
    return issues

def check_evolution_event(bundle: Dict) -> List[Tuple[str, str, str]]:
    """检查 EvolutionEvent"""
    issues = []
    
    if 'EvolutionEvent' not in bundle:
        issues.append(('P3', 'missing_evolution_event', 'Add EvolutionEvent field to bundle'))
    
    confidence = bundle.get('capsule', {}).get('confidence', 0)
    if confidence < 0.85 or confidence > 0.95:
        issues.append(('P3', 'confidence_out_of_range', f'{confidence} (recommended: 0.85-0.95)'))
    
    return issues

def check_code_snippet_field(capsule: Dict) -> List[Tuple[str, str, str]]:
    """检查 code_snippet 字段（触发 quarantine）"""
    issues = []
    if 'code_snippet' in capsule:
        snippet = capsule['code_snippet']
        length = len(snippet) if snippet else 0
        severity = 'P1' if length >= 50 else 'P2'
        issues.append((severity, 'code_snippet_field_present', 
                      f'code_snippet field ({length} chars) may trigger quarantine'))
    return issues

def lint_bundle(bundle: Dict) -> List[Tuple[str, str, str]]:
    """Lint 一个完整的 bundle"""
    all_issues = []
    
    gene = bundle.get('gene', {})
    capsule = bundle.get('capsule', {})
    
    all_issues.extend(check_code_snippet(capsule.get('content', '')))
    all_issues.extend(check_sensitive_data(capsule.get('content', '')))
    all_issues.extend(check_sensitive_data(json.dumps(gene, ensure_ascii=False)))
    all_issues.extend(check_lengths(gene, capsule))
    all_issues.extend(check_evolution_event(bundle))
    all_issues.extend(check_code_snippet_field(capsule))
    
    return all_issues

def auto_fix(bundle: Dict) -> Tuple[Dict, List[str]]:
    """自动修复可修复的问题"""
    fixes = []
    gene = bundle.get('gene', {})
    capsule = bundle.get('capsule', {})
    
    # Fix short strategy steps
    for i, step in enumerate(gene.get('strategy', [])):
        if len(step) < 15:
            gene['strategy'][i] = step + ' with proper validation'
            fixes.append(f'Expanded strategy step {i}')
    
    # Fix short signals
    for i, sig in enumerate(gene.get('signals_match', [])):
        if len(sig) < 3:
            gene['signals_match'][i] = sig + '_sig'
            fixes.append(f'Expanded signal {i}')
    
    # Add EvolutionEvent if missing
    if 'EvolutionEvent' not in bundle:
        import time
        bundle['EvolutionEvent'] = f'auto_lint_fix_{int(time.time())}'
        fixes.append('Added missing EvolutionEvent')
    
    # Remove code_snippet field
    if 'code_snippet' in capsule:
        del capsule['code_snippet']
        fixes.append('Removed code_snippet field')
    
    bundle['gene'] = gene
    bundle['capsule'] = capsule
    return bundle, fixes

def format_report(issues: List[Tuple[str, str, str]]) -> str:
    """格式化 lint 报告"""
    if not issues:
        return '✅ All checks passed!'
    
    lines = [f'\n🔍 Capsule Lint Report ({len(issues)} issue(s))\n']
    
    # Group by severity
    p0 = [i for i in issues if i[0] == 'P0']
    p1 = [i for i in issues if i[0] == 'P1']
    p2 = [i for i in issues if i[0] == 'P2']
    p3 = [i for i in issues if i[0] == 'P3']
    
    if p0:
        lines.append('🚨 P0 - CRITICAL (will block publish):')
        for _, desc, detail in p0:
            lines.append(f'   {desc}: {detail}')
    
    if p1:
        lines.append('\n❌ P1 - HIGH (likely quarantine):')
        for _, desc, detail in p1:
            lines.append(f'   {desc}: {detail}')
    
    if p2:
        lines.append('\n⚠️  P2 - MEDIUM (may be rejected):')
        for _, desc, detail in p2:
            lines.append(f'   {desc}: {detail}')
    
    if p3:
        lines.append('\n💡 P3 - LOW (quality improvement):')
        for _, desc, detail in p3:
            lines.append(f'   {desc}: {detail}')
    
    return '\n'.join(lines)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='EvoMap Capsule Linter')
    parser.add_argument('--bundle', help='Path to bundle JSON file')
    parser.add_argument('--queue', help='Path to queue JSON file')
    parser.add_argument('--fix', action='store_true', help='Auto-fix issues')
    args = parser.parse_args()
    
    if not args.bundle and not args.queue:
        parser.print_help()
        sys.exit(1)
    
    bundles = []
    if args.bundle:
        with open(args.bundle) as f:
            bundles.append(json.load(f))
    if args.queue:
        with open(args.queue) as f:
            data = json.load(f)
            bundles.extend(data.get('bundles', []))
    
    total_issues = 0
    for i, bundle in enumerate(bundles):
        name = bundle.get('topic', f'bundle_{i}')
        issues = lint_bundle(bundle)
        total_issues += len(issues)
        
        print(f'\n{"="*60}')
        print(f'Bundle: {name}')
        print(format_report(issues))
        
        if args.fix and issues:
            fixed, fixes = auto_fix(bundle)
            print(f'\n🔧 Auto-fixes applied: {len(fixes)}')
            for fix in fixes:
                print(f'   + {fix}')
            
            # Re-lint
            new_issues = lint_bundle(fixed)
            print(f'\nAfter fix: {len(new_issues)} issue(s) remaining')
    
    sys.exit(1 if total_issues > 0 else 0)

if __name__ == '__main__':
    main()
