# agent-cost-tracker 💰

Track AI agent API costs in real-time. Zero dependencies.

## The Problem

AI agents make hundreds of API calls. You wake up to a $50 bill. Sound familiar?

## Install

```bash
pip install agent-cost-tracker
```

## Usage

```python
from cost_tracker import CostTracker

tracker = CostTracker(budget_daily=10.0)

# Log calls manually
tracker.log("gpt-4o", tokens_in=1000, tokens_out=500)

# Or use context manager
with tracker.track("claude-3.5-sonnet", tokens_in=2000, tokens_out=1000):
    response = llm.chat(...)

# Check budget
print(tracker.summary())
# 💰 Cost Tracker
# Today: $3.42 / $10.00 [████░░░░░░░░░░░░░░░░] 34%
# Calls: 47 | In: 12.3K | Out: 5.1K
```

## CLI

```bash
# Log a call
agent-cost log --model gpt-4o --in 1000 --out 500

# See today's summary
agent-cost summary

# Pricing table
agent-cost price
```

## Supported Models

OpenAI (GPT-4o, GPT-4o-mini, o1), Anthropic (Claude 3.5 Sonnet/Haiku, Opus), Google (Gemini 2.0 Flash/Pro), DeepSeek (V3, R1). Add custom pricing easily.

## Why Not LangSmith / OpenRouter?

This is **local-first**, **zero-dependency**, and **works offline**. No account needed. Your data stays on your machine. Perfect for personal agents that run 24/7.

## License

MIT
