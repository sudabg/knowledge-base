#!/usr/bin/env python3
"""
arXiv 自动抓取 — 获取最新 AI Agent 相关论文，输出到知识库
用法: python3 arxiv_fetcher.py [--count 5] [--output ../knowledge/arxiv_daily.md]
"""

import urllib.request, xml.etree.ElementTree as ET, json, os, sys
from datetime import datetime

QUERIES = [
    "all:LLM+AND+all:agent+AND+all:self-improving",
    "all:multi-agent+AND+all:collaboration",
    "all:LLM+AND+all:safety+AND+all:alignment",
    "all:reinforcement+AND+all:LLM+AND+all:reward",
]

def fetch_arxiv(query, max_results=3):
    """从 arXiv 获取论文"""
    url = f"https://export.arxiv.org/api/query?search_query={query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = r.read().decode()
        root = ET.fromstring(data)
        ns = {'a': 'http://www.w3.org/2005/Atom'}
        papers = []
        for entry in root.findall('a:entry', ns):
            title = entry.find('a:title', ns).text.strip().replace('\n', ' ')
            summary = entry.find('a:summary', ns).text.strip()
            link = entry.find('a:id', ns).text
            published = entry.find('a:published', ns).text[:10]
            authors = [a.find('a:name', ns).text for a in entry.findall('a:author', ns)]
            papers.append({
                'title': title, 'summary': summary, 'link': link,
                'published': published, 'authors': authors[:3]
            })
        return papers
    except Exception as e:
        return [{'error': str(e)}]

def format_paper(paper, idx):
    """格式化单篇论文"""
    if 'error' in paper:
        return f"### ❌ Error: {paper['error']}\n"
    
    authors = ', '.join(paper['authors'])
    if len(paper['authors']) < len(paper.get('authors', [])):
        authors += ' et al.'
    
    return f"""### {idx}. {paper['title']}

- **作者**: {authors}
- **日期**: {paper['published']}
- **链接**: {paper['link']}
- **摘要**: {paper['summary'][:300]}...

---

"""

def main():
    count = 3
    output = os.path.expanduser("~/workspace/agent/workspace/knowledge/arxiv_daily.md")
    
    if '--count' in sys.argv:
        count = int(sys.argv[sys.argv.index('--count') + 1])
    if '--output' in sys.argv:
        output = sys.argv[sys.argv.index('--output') + 1]
    
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"📚 Fetching arXiv papers for {today}...")
    
    all_papers = []
    seen_titles = set()
    
    for query in QUERIES:
        papers = fetch_arxiv(query, count)
        for p in papers:
            if 'error' not in p and p['title'] not in seen_titles:
                seen_titles.add(p['title'])
                all_papers.append(p)
    
    # 生成 Markdown
    md = f"""# arXiv Daily — {today}

> 自动抓取：LLM Agent 相关最新论文
> 共 {len(all_papers)} 篇

"""
    for i, paper in enumerate(all_papers, 1):
        md += format_paper(paper, i)
    
    # 写入文件
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, 'w') as f:
        f.write(md)
    
    print(f"✅ {len(all_papers)} papers saved to {output}")
    return all_papers

if __name__ == "__main__":
    main()
