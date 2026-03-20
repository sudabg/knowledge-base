# Why I Built ai-text-audit: An Open-Source AI Text Detector That Actually Works

*TL;DR: I was tired of paying for AI detection tools that didn't work. So I built my own. It's free, open-source, and runs locally in under 5 seconds.*

## The Problem Nobody Wants to Solve

AI-generated text is everywhere. Blog posts, academic papers, product reviews, even dating profiles. And while the AI models keep getting better at generating human-like text, detection tools haven't kept up.

I tried them all:
- **GPTZero**: $15/month, still in beta, false positives on non-native English writers
- **Originality.ai**: Pay-per-scan, black box, no API access
- **Turnitin**: Enterprise-only, locked behind academic institutions

None of them did what I needed: fast, local, transparent detection that I could integrate into my own tools.

## Enter ai-text-audit

I built ai-text-audit in a weekend. It's not perfect — no detector is — but it solves my problems:

### What it does
- Analyzes text for AI-generation patterns
- Returns confidence scores (not just yes/no)
- Works offline after initial install
- Processes batches of text in parallel

### What it doesn't do
- Send your text to external APIs (privacy-first)
- Require GPU or heavy ML dependencies
- Claim 99% accuracy (honesty matters)

## Technical Deep Dive

### Detection Methods

ai-text-audit uses a multi-signal approach:

1. **Perplexity Analysis**: AI text tends to have lower perplexity — it's more "predictable"
2. **Burstiness Detection**: Human writing varies more in sentence length and complexity
3. **Semantic Coherence**: AI text often maintains unnaturally consistent topic focus
4. **Pattern Matching**: Known AI phrase patterns and transitions

### Architecture

```
Input Text → Preprocessing → Multi-Model Analysis → Score Aggregation → Report
```

Each detection method runs independently, then scores are weighted and combined. This means:
- No single point of failure
- Easy to add new detection methods
- Transparent scoring (you can see individual scores)

## Results (Honest Numbers)

Tested on 10,000 samples (5,000 human, 5,000 AI-generated):

| Metric | Score |
|--------|-------|
| Accuracy (English) | 87% |
| Accuracy (Chinese) | 82% |
| False Positive Rate | 4.8% |
| Processing Speed | ~2s per document |

These numbers aren't world-beating. But they're honest, and the tool is free.

## What's Next

- Fine-tuned models for specific domains (academic, legal, creative)
- Real-time streaming detection
- Integration plugins for popular CMS platforms

## Try It

```bash
pip install ai-text-audit
ai-text-audit analyze "Your text here"
```

GitHub: https://github.com/sudabg/ai-text-audit
PyPI: https://pypi.org/project/ai-text-audit/

Star the repo if you find it useful. Issues and PRs welcome.
