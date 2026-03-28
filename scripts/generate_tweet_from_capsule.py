#!/usr/bin/env python3
"""
自动从 EvoMap capsule 生成推文草稿
Usage: python3 generate_tweet_from_capsule.py <capsule_json_file>
"""

import json
import sys
import re

def load_capsule(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_fields(capsule):
    # capsule could be a Gene, Capsule, or EvolutionEvent. We want Capsule content.
    if capsule.get('type') == 'Capsule':
        summary = capsule.get('summary', '')
        signals = capsule.get('trigger', capsule.get('signals_match', []))
        strategy = capsule.get('strategy', [])
        content = capsule.get('content', '')
        confidence = capsule.get('confidence')
        return summary, signals, strategy, content, confidence
    else:
        # If top-level is bundle with assets, maybe find capsule in assets
        # Not handling now; just return basics
        return capsule.get('summary', ''), [], [], '', None

def choose_template(confidence=None):
    # For now, always use Template A (经验教训型) if confidence high, else Template B (技术突破型)
    if confidence and confidence >= 0.9:
        return 'A'
    else:
        return 'B'

def fill_template_A(summary, signals, strategy, content):
    emoji = '✨'
    # First line: emoji + one-line summary
    if summary:
        first_line = f"{emoji} {summary}"
    else:
        first_line = f"{emoji} {signals[0] if signals else 'Important findings'}"

    # Build numbered list: use strategy if available; else signals
    points = []
    if strategy:
        items = strategy if isinstance(strategy, list) else [strategy]
    else:
        items = signals
    # Take up to 3 items
    for i, item in enumerate(items[:3], 1):
        # Convert to short statement
        if isinstance(item, str):
            points.append(f"{i}. {item}")
        else:
            points.append(f"{i}. {str(item)}")

    # Closing: a quote from content? extract first sentence of content if exists
    if content:
        # take first 120 characters as quote
        quote = content.strip().split('\n')[0]
        if len(quote) > 120:
            quote = quote[:117] + '...'
        closing = f"\n\n「{quote}」"
    else:
        closing = ""

    # Hashtags: based on signals
    tags = []
    for word in signals[:2]:
        w = word.lower()
        if 'agent' in w:
            tags.append('#AIAgent')
        if 'memory' in w:
            tags.append('#MemorySystems')
        if 'evolution' in w or 'adaptive' in w:
            tags.append('#AdaptiveSystems')
    if not tags:
        tags = ['#AIAgent', '#OpenSource']
    tag_str = ' '.join(tags)

    tweet = first_line + '\n\n' + '\n'.join(points) + closing + '\n\n' + tag_str
    # Ensure length <= 280 characters (rough)
    if len(tweet) > 280:
        # Trim content
        tweet = tweet[:277] + '...'
    return tweet

def fill_template_B(summary, signals, strategy, content):
    # Template B: 技术突破型
    if summary:
        first_line = f"{summary}。"
    else:
        first_line = "新成果发布。"

    key_line = f"关键：{signals[0] if signals else '无'}"

    details = []
    if strategy:
        items = strategy if isinstance(strategy, list) else [strategy]
        for item in items[:3]:
            details.append(f"→ {item}")
    else:
        for sig in signals[:3]:
            details.append(f"→ {sig}")

    tags = ['#AIAgent', '#Tech']
    tweet = first_line + '\n\n' + key_line + '\n' + '\n'.join(details) + '\n\n' + ' '.join(tags)
    if len(tweet) > 280:
        tweet = tweet[:277] + '...'
    return tweet

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_tweet_from_capsule.py <capsule_json_file>")
        sys.exit(1)
    path = sys.argv[1]
    capsule = load_capsule(path)
    summary, signals, strategy, content, confidence = extract_fields(capsule)
    tpl = choose_template(confidence)
    if tpl == 'A':
        tweet = fill_template_A(summary, signals, strategy, content)
    else:
        tweet = fill_template_B(summary, signals, strategy, content)
    print(tweet)

if __name__ == '__main__':
    main()
