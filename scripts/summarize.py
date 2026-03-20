#!/usr/bin/env python3
"""Simple text summarizer using OpenRouter API"""
import sys
import json
import urllib.request
import os

def summarize(text, max_words=200):
    """Summarize text using OpenRouter"""
    api_key = os.environ.get('OPENROUTER_API_KEY', '')
    if not api_key:
        return "Error: OPENROUTER_API_KEY not set"
    
    payload = json.dumps({
        "model": "openrouter/hunter-alpha",
        "messages": [{"role": "user", "content": f"Summarize the following text in {max_words} words or less:\n\n{text}"}],
        "max_tokens": 500
    }).encode()
    
    req = urllib.request.Request(
        'https://openrouter.ai/api/v1/chat/completions',
        data=payload,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    )
    
    try:
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        return data['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {e}"

if __name__ == '__main__':
    text = sys.stdin.read()
    print(summarize(text))
