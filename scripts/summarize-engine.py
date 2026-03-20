#!/usr/bin/env python3
"""
内容智能摘要引擎 v1.0
支持多种摘要算法：lex-rank, lsa, text-rank, luhn, sum-basic
"""
import sys
import argparse
import json
import subprocess
import tempfile
import os

ALGORITHMS = ['lex-rank', 'lsa', 'text-rank', 'luhn', 'sum-basic']
FORMATS = ['plaintext', 'markdown', 'html']

def summarize_text(text, algorithm='lex-rank', sentences=3, language='english'):
    """Summarize text using sumy"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(text)
        tmpfile = f.name
    
    try:
        cmd = ['sumy', algorithm, f'--length={sentences}', f'--language={language}', '--format=plaintext']
        result = subprocess.run(cmd, input=text, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            # Fallback: extract first N sentences
            sentences_list = text.split('. ')[:sentences]
            return '. '.join(sentences_list) + '.'
    except Exception as e:
        return f"Error: {e}"
    finally:
        os.unlink(tmpfile)

def summarize_file(filepath, algorithm='lex-rank', sentences=3):
    """Summarize a file"""
    with open(filepath) as f:
        text = f.read()
    return summarize_text(text, algorithm, sentences)

def batch_summarize(texts, algorithm='lex-rank', sentences=3):
    """Batch summarize multiple texts"""
    results = []
    for i, text in enumerate(texts):
        summary = summarize_text(text, algorithm, sentences)
        results.append({'index': i, 'summary': summary, 'original_length': len(text), 'summary_length': len(summary)})
    return results

def main():
    parser = argparse.ArgumentParser(description='内容智能摘要引擎')
    parser.add_argument('input', nargs='?', help='输入文件路径（不传则从stdin读取）')
    parser.add_argument('-a', '--algorithm', choices=ALGORITHMS, default='lex-rank', help='摘要算法')
    parser.add_argument('-n', '--sentences', type=int, default=3, help='摘要句子数')
    parser.add_argument('-l', '--language', default='english', help='语言')
    parser.add_argument('-f', '--format', choices=FORMATS, default='plaintext', help='输出格式')
    parser.add_argument('-j', '--json', action='store_true', help='JSON输出')
    parser.add_argument('--batch', nargs='+', help='批量摘要多个文件')
    
    args = parser.parse_args()
    
    if args.batch:
        texts = []
        for f in args.batch:
            with open(f) as fp:
                texts.append(fp.read())
        results = batch_summarize(texts, args.algorithm, args.sentences)
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    
    if args.input:
        summary = summarize_file(args.input, args.algorithm, args.sentences)
    else:
        text = sys.stdin.read()
        summary = summarize_text(text, args.algorithm, args.sentences)
    
    if args.json:
        print(json.dumps({'summary': summary, 'algorithm': args.algorithm, 'sentences': args.sentences}, ensure_ascii=False))
    else:
        print(summary)

if __name__ == '__main__':
    main()
