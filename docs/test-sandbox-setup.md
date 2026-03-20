# Test Sandbox for EvoMap Agent

## Purpose

Isolated environment for testing capsule submissions, protocol changes, and integration features without affecting production node or consuming real credit.

## Structure

```
test-sandbox/
├── Dockerfile          # Sandbox container (Ephemeral)
├── docker-compose.yml  # Orchestrates mock Hub + Agent
├── mock-hub/
│   ├── server.js       # Minimal A2A server (echo + validation)
│   └── README.md       # How to run mock hub
├── agent-test-runner/
│   ├── runner.py       # Executes evolution loop against mock hub
│   ├── fixtures/       # Sample bundles (valid/invalid)
│   └── README.md
├── integration/
│   ├── test_protocol.py
│   ├── test_rate_limiter.py
│   └── test_preflight.py
└── README.md
```

## Quick Start

```bash
# 1. Start mock hub (localhost:8080)
cd test-sandbox/mock-hub
npm install && node server.js

# 2. Run agent test loop
cd test-sandbox/agent-test-runner
python3 runner.py --hub http://localhost:8080 --cycles 3

# 3. Run unit tests
cd test-sandbox/integration
pytest -v
```

## Mock Hub Features

- Persistent in-memory store (no DB)
- No rate limits (or configurable)
- Echoes received envelopes to `/a2a/echo`
- Implements `/a2a/publish` with full validation but returns mock response
- Logs all requests to `mock-hub.log` in JSON Lines
- No credit system (always returns success + fake GDI)

## Sample Fixtures

```json
// fixtures/simple_capsule.json
{
  "topic": "test_simple",
  "gene": { "signals_match": ["test_signal"], "strategy": ["Implement test"] },
  "capsule": { "content": "Test content...", "confidence": 0.9 },
  "evolution_event": "test_event"
}
```

## CI Integration

```yaml
# .github/workflows/evomap-test.yml
jobs:
  test-sandbox:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start mock hub
        run: cd test-sandbox/mock-hub && npm ci && node server.js &
      - name: Run tests
        run: cd test-sandbox/integration && pytest -v
      - name: Upload logs
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: mock-hub-logs
          path: test-sandbox/mock-hub/mock-hub.log
```

## Benefits

- Zero credit cost, zero reputation risk
- Rapid iteration on protocol changes
- Debugging without spamming real Hub
- CI gate before pushing to production agent
