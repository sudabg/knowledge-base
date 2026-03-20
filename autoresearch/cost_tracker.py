"""agent-cost-tracker: Track AI agent API costs in real-time.

Zero dependencies. Works with any LLM provider.

Usage:
    from cost_tracker import CostTracker
    
    tracker = CostTracker(budget_daily=10.00)
    
    with tracker.track("gpt-4o", tokens_in=1000, tokens_out=500):
        response = openai.chat.completions.create(...)
    
    print(tracker.summary())
    # Today: $3.42 / $10.00 budget (34%)
    # This session: 47 calls, 12.3K tokens in, 5.1K tokens out
"""
import json, time, os
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict

# Pricing per 1M tokens (as of March 2026)
PRICING = {
    # OpenAI
    "gpt-4o":           {"in": 2.50,  "out": 10.00},
    "gpt-4o-mini":      {"in": 0.15,  "out": 0.60},
    "gpt-4-turbo":      {"in": 10.00, "out": 30.00},
    "o1":               {"in": 15.00, "out": 60.00},
    "o1-mini":          {"in": 3.00,  "out": 12.00},
    # Anthropic
    "claude-3.5-sonnet": {"in": 3.00, "out": 15.00},
    "claude-3.5-haiku":  {"in": 0.80, "out": 4.00},
    "claude-3-opus":     {"in": 15.00,"out": 75.00},
    # Google
    "gemini-2.0-flash":  {"in": 0.10, "out": 0.40},
    "gemini-2.0-pro":    {"in": 1.25, "out": 5.00},
    # DeepSeek
    "deepseek-v3":       {"in": 0.27, "out": 1.10},
    "deepseek-r1":       {"in": 0.55, "out": 2.19},
}

@dataclass
class Call:
    model: str
    tokens_in: int
    tokens_out: int
    cost: float
    timestamp: float
    label: str = ""

@dataclass
class DayStats:
    date: str
    calls: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    cost: float = 0.0

class CostTracker:
    """Track LLM API costs across sessions."""
    
    def __init__(self, budget_daily: float = 10.0, state_file: str = ".cost_tracker.json"):
        self.budget_daily = budget_daily
        self.state_file = state_file
        self.calls: list = []
        self._load_state()
    
    def _load_state(self):
        if os.path.exists(self.state_file):
            data = json.loads(Path(self.state_file).read_text())
            self.calls = data.get("calls", [])
    
    def _save_state(self):
        Path(self.state_file).write_text(json.dumps({
            "calls": self.calls[-1000:]  # keep last 1000
        }))
    
    def calc_cost(self, model: str, tokens_in: int, tokens_out: int) -> float:
        """Calculate cost for a call."""
        pricing = PRICING.get(model)
        if not pricing:
            # Try partial match
            for key in PRICING:
                if key in model.lower():
                    pricing = PRICING[key]
                    break
        if not pricing:
            return 0.0  # unknown model
        return (tokens_in * pricing["in"] + tokens_out * pricing["out"]) / 1_000_000
    
    def log(self, model: str, tokens_in: int, tokens_out: int, label: str = ""):
        """Log a call."""
        cost = self.calc_cost(model, tokens_in, tokens_out)
        call = {
            "model": model, "tokens_in": tokens_in, "tokens_out": tokens_out,
            "cost": cost, "timestamp": time.time(), "label": label
        }
        self.calls.append(call)
        self._save_state()
        return cost
    
    @contextmanager
    def track(self, model: str, tokens_in: int = 0, tokens_out: int = 0, label: str = ""):
        """Context manager for tracking a call."""
        start = time.time()
        yield
        elapsed = time.time() - start
        self.log(model, tokens_in, tokens_out, label)
    
    def today(self) -> DayStats:
        """Get today's stats."""
        today = date.today().isoformat()
        stats = DayStats(date=today)
        for c in self.calls:
            if datetime.fromtimestamp(c["timestamp"]).date().isoformat() == today:
                stats.calls += 1
                stats.tokens_in += c["tokens_in"]
                stats.tokens_out += c["tokens_out"]
                stats.cost += c["cost"]
        return stats
    
    def summary(self) -> str:
        """Human-readable summary."""
        t = self.today()
        pct = (t.cost / self.budget_daily * 100) if self.budget_daily > 0 else 0
        bar_len = 20
        filled = int(bar_len * pct / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        
        lines = [
            f"💰 Cost Tracker",
            f"Today: ${t.cost:.2f} / ${self.budget_daily:.2f} [{bar}] {pct:.0f}%",
            f"Calls: {t.calls} | In: {t.tokens_in/1000:.1f}K | Out: {t.tokens_out/1000:.1f}K",
        ]
        
        if pct > 80:
            lines.append("⚠️  Approaching daily budget!")
        elif pct > 100:
            lines.append("🚨 Daily budget exceeded!")
        
        return "\n".join(lines)
    
    def by_model(self) -> Dict[str, float]:
        """Cost breakdown by model."""
        result = {}
        for c in self.calls:
            model = c["model"]
            result[model] = result.get(model, 0) + c["cost"]
        return result

# CLI
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(prog="agent-cost", description="Track AI agent API costs")
    sub = parser.add_subparsers(dest="cmd")
    
    log_p = sub.add_parser("log", help="Log a call")
    log_p.add_argument("--model", required=True)
    log_p.add_argument("--in", dest="tokens_in", type=int, default=0)
    log_p.add_argument("--out", dest="tokens_out", type=int, default=0)
    log_p.add_argument("--label", default="")
    
    sub.add_parser("summary", help="Show today's summary")
    
    models_p = sub.add_parser("models", help="Cost by model")
    models_p.add_argument("--last", type=int, default=7, help="Last N days")
    
    price_p = sub.add_parser("price", help="Show pricing table")
    
    args = parser.parse_args()
    tracker = CostTracker()
    
    if args.cmd == "log":
        cost = tracker.log(args.model, args.tokens_in, args.tokens_out, args.label)
        print(f"Logged: ${cost:.4f} for {args.model}")
    elif args.cmd == "summary":
        print(tracker.summary())
        print("\nBy model:")
        for model, cost in sorted(tracker.by_model().items(), key=lambda x: -x[1]):
            print(f"  {model}: ${cost:.2f}")
    elif args.cmd == "price":
        print("Model pricing ($/1M tokens):")
        for model, p in sorted(PRICING.items()):
            print(f"  {model:25s} in: ${p['in']:>7.2f}  out: ${p['out']:>7.2f}")
    else:
        parser.print_help()
