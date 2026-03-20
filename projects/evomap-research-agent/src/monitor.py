"""
arXiv Paper Monitor - Fetches latest papers matching keywords
"""
import urllib.request
import xml.etree.ElementTree as ET
import json
import time
from datetime import datetime, timedelta

ARXIV_API = "https://export.arxiv.org/api/query"

# Research domains to monitor
SEARCH_QUERIES = [
    "all:agent+AND+all:self-improving",
    "all:LLM+AND+all:evolution+AND+all:agent",
    "all:multi-agent+AND+all:debate",
    "all:prompt+AND+all:optimization+AND+all:LLM",
    "all:tool+AND+all:learning+AND+all:agent",
    "all:agent+AND+all:memory+AND+all:LLM",
    "all:calibration+AND+all:LLM",
    "all:benchmark+AND+all:agent",
    "all:context+AND+all:compression",
    "all:code+AND+all:generation+AND+all:agent",
]

def fetch_papers(max_results_per_query=3):
    """Fetch papers from arXiv matching our queries"""
    papers = []
    
    for query in SEARCH_QUERIES:
        try:
            params = f"?search_query={query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results_per_query}"
            url = ARXIV_API + params
            
            req = urllib.request.Request(url, headers={"User-Agent": "EvoMapResearchAgent/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                xml_data = resp.read().decode()
            
            root = ET.fromstring(xml_data)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            
            for entry in root.findall("atom:entry", ns):
                title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
                summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
                authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)[:3]]
                link = entry.find("atom:id", ns).text
                published = entry.find("atom:published", ns).text
                
                papers.append({
                    "title": title,
                    "summary": summary[:500],
                    "authors": authors,
                    "link": link,
                    "published": published,
                    "query": query
                })
        except Exception as e:
            pass  # Skip failed queries
        
        time.sleep(3)  # Rate limit
    
    return papers

def deduplicate(papers, seen_titles_file="/tmp/evomap_seen_titles.json"):
    """Remove papers we've already processed"""
    try:
        with open(seen_titles_file) as f:
            seen = set(json.load(f))
    except:
        seen = set()
    
    new_papers = []
    for p in papers:
        title_key = p["title"][:50].lower()
        if title_key not in seen:
            new_papers.append(p)
            seen.add(title_key)
    
    # Save updated seen list
    with open(seen_titles_file, "w") as f:
        json.dump(list(seen), f)
    
    return new_papers

def filter_relevant(papers, min_relevance=0.15):
    """Filter papers by relevance to agent evolution"""
    relevant_keywords = [
        "agent", "llm", "self-improv", "evolution", "prompt", "memory",
        "multi-agent", "debate", "tool", "learning", "optimization",
        "knowledge", "distillation", "calibration", "benchmark",
        "reasoning", "planning", "reflection", "debug", "skill",
        "model", "training", "fine-tun", "RAG", "retrieval"
    ]
    
    scored = []
    for p in papers:
        text = (p["title"] + " " + p["summary"]).lower()
        matches = sum(1 for kw in relevant_keywords if kw.lower() in text)
        score = matches / 3.0  # Normalize: 3+ keywords = high relevance
        if score >= min_relevance:
            p["relevance"] = min(score, 1.0)
            scored.append(p)
    
    scored.sort(key=lambda x: x["relevance"], reverse=True)
    return scored

if __name__ == "__main__":
    print("Fetching arXiv papers...")
    papers = fetch_papers()
    print(f"Found {len(papers)} papers")
    
    new = deduplicate(papers)
    print(f"{len(new)} new (after dedup)")
    
    relevant = filter_relevant(new)
    print(f"{len(relevant)} relevant")
    
    for p in relevant[:5]:
        print(f"\n📄 {p['title']}")
        print(f"   Relevance: {p['relevance']:.2f}")
        print(f"   {', '.join(p['authors'])}")
