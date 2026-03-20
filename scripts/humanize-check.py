#!/usr/bin/env python3
"""
Humanizer Quality Checker — 检测 AI 写作痕迹
用于 EvoMap capsule 发布前的质量过滤
基于 Wikipedia 'Signs of AI writing' 指南
"""
import re
import sys
import json

AI_PATTERNS = {
    # Pattern name -> (regex, weight)
    'em_dash': (r'—', 1),
    'negative_parallelism': (r"(?i)(it'?s not just|not merely|not only)", 2),
    'ai_vocab': (r'(?i)\b(crucial|pivotal|tapestry|underscore|delve|landscape|testament|vibrant|intricate|poignant|seamless|comprehensive|robust|foster|garner|emphasize|highlight)\b', 1),
    'ing_superficial': (r'\w+ing,\s*(ensuring|reflecting|highlighting|underscoring|emphasizing)', 2),
    'rule_of_three': (r'\b\w+,\s*\w+,\s*and\s*\w+\b', 0.5),  # common but overused
    'boast_language': (r'(?i)\b(boasts?|stands? as|serves? as|represents? a)\b', 2),
    'promotional': (r'(?i)\b(groundbreaking|cutting.edge|state.of.the.art|game.changer|revolutionary|breathtaking|stunning)\b', 2),
    'vague_attribution': (r'(?i)\b(industry experts|observers|critics|some argue|many believe|it is widely)\b', 2),
    'collaborative_artifact': (r'(?i)\b(I hope this helps|let me know|would you like|of course!|certainly!)\b', 3),
    'negative_conclusion': (r'(?i)\b(despite.*challenges|faces? several challenges|moving forward)\b', 1),
    'filler': (r'(?i)\b(in order to|due to the fact that|at this point in time|it is important to note)\b', 1),
}

def analyze(text: str) -> dict:
    """Analyze text for AI patterns. Returns score and details."""
    results = {}
    total_score = 0
    
    for name, (pattern, weight) in AI_PATTERNS.items():
        matches = re.findall(pattern, text)
        count = len(matches)
        if count > 0:
            score = count * weight
            total_score += score
            results[name] = {'count': count, 'weight': weight, 'score': score}
    
    word_count = len(text.split())
    density = total_score / max(word_count, 1) * 100  # AI patterns per 100 words
    
    return {
        'word_count': word_count,
        'total_score': total_score,
        'density': round(density, 2),
        'patterns': results,
        'verdict': '✅ Clean' if density < 2 else '⚠️ Needs work' if density < 5 else '❌ Too AI'
    }

def main():
    if len(sys.argv) > 1:
        text = open(sys.argv[1]).read()
    else:
        text = sys.stdin.read()
    
    result = analyze(text)
    print(f"Words: {result['word_count']} | Score: {result['total_score']} | Density: {result['density']}%")
    print(f"Verdict: {result['verdict']}")
    if result['patterns']:
        print("\nPatterns found:")
        for name, info in sorted(result['patterns'].items(), key=lambda x: -x[1]['score']):
            print(f"  {name}: {info['count']}x (weight={info['weight']}, score={info['score']})")
    
    if '--json' in sys.argv:
        print("\n" + json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
