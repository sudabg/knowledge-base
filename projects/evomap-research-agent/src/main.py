#!/usr/bin/env python3
"""
EvoMap Research Agent - Main Loop
Monitors arXiv → Analyzes papers → Generates bundles → Publishes to EvoMap → Learns
"""
import sys
import os
import json
import time
import traceback

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor import fetch_papers, deduplicate, filter_relevant
from generator import generate_bundle, build_insight_from_paper
from publisher import publish_bundle, check_node_status, heartbeat

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "settings.json")
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def log(msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    log_file = os.path.join(LOG_PATH, f"{time.strftime('%Y-%m-%d')}.log")
    os.makedirs(LOG_PATH, exist_ok=True)
    with open(log_file, "a") as f:
        f.write(line + "\n")

def run_research_cycle(cycle_num, config):
    """Run one complete research cycle"""
    log(f"\n{'='*60}")
    log(f"🔬 Research Cycle {cycle_num}")
    log(f"{'='*60}")
    
    # 1. Check node status
    status = check_node_status()
    rep = status.get("reputation_score", 0)
    pub = status.get("total_published", 0)
    pro = status.get("total_promoted", 0)
    log(f"📊 Node: Rep={rep:.2f} Pub={pub} Pro={pro}")
    
    # 2. Heartbeat
    hb = heartbeat()
    tasks = hb.get("available_tasks", [])
    log(f"💓 Heartbeat: {len(tasks)} tasks available")
    
    # 3. Fetch papers
    log("📚 Fetching arXiv papers...")
    papers = fetch_papers(max_results_per_query=config["monitor"]["max_papers_per_query"])
    log(f"   Found {len(papers)} papers")
    
    # 4. Deduplicate
    new_papers = deduplicate(papers)
    log(f"   {len(new_papers)} new after dedup")
    
    # 5. Filter relevant
    relevant = filter_relevant(new_papers, config["monitor"]["min_relevance_score"])
    log(f"   {len(relevant)} relevant papers")
    
    if not relevant:
        log("⚠️  No relevant new papers. Skipping this cycle.")
        return 0
    
    # 6. Generate and publish bundles
    published = 0
    for i, paper in enumerate(relevant[:3], 1):  # Max 3 per cycle
        log(f"\n📝 Processing paper {i}/{min(len(relevant), 3)}: {paper['title'][:50]}...")
        
        # Build insight
        insight = build_insight_from_paper(paper)
        
        # Generate bundle
        bundle = generate_bundle(insight)
        
        # Publish
        time.sleep(config["publisher"]["publish_interval_seconds"])
        result = publish_bundle(bundle)
        
        decision = result.get("decision", "error")
        reason = result.get("reason", "")
        log(f"   📤 Publish: {decision} ({reason})")
        
        if decision == "accept":
            published += 1
    
    log(f"\n✅ Cycle {cycle_num} complete: {published}/{min(len(relevant), 3)} published")
    return published

def main():
    log("=" * 60)
    log("🦞 EvoMap Research Agent - Starting")
    log("=" * 60)
    
    config = load_config()
    cycle = 0
    total_published = 0
    
    while True:
        cycle += 1
        try:
            published = run_research_cycle(cycle, config)
            total_published += published
        except Exception as e:
            log(f"❌ Error in cycle {cycle}: {e}")
            log(traceback.format_exc())
        
        # Wait for next cycle
        wait_minutes = config["monitor"]["fetch_interval_minutes"]
        log(f"⏳ Next cycle in {wait_minutes} minutes...")
        time.sleep(wait_minutes * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
        sys.exit(0)
