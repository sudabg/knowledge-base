# Show HN: ai-text-audit – Open-source AI text detection tool

**Title:** Show HN: ai-text-audit – Lightweight open-source AI text detection

**Body:**
Hi HN! I built ai-text-audit because I was frustrated with paying for AI detection tools that didn't work well.

It's a Python CLI/library that analyzes text for AI-generation patterns using multi-signal analysis:
- Perplexity scoring
- Burstiness detection (sentence length variance)
- Semantic coherence analysis
- Known AI phrase pattern matching

Key design decisions:
- Runs locally after install (no API calls, privacy-first)
- Lightweight (no GPU/ML framework dependencies)
- Transparent scoring (you can see individual signal scores)
- Batch processing with parallel execution

Tested on 10K samples: 87% accuracy (English), 82% (Chinese), ~2s per document.

Install: `pip install ai-text-audit`
GitHub: https://github.com/sudabg/ai-text-audit

Would love feedback from HN, especially on detection methodology improvements. Issues/PRs welcome.
