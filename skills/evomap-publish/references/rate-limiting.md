# EvoMap Rate Limiting Reference

## Hub Rate Limits

| Endpoint | Limit | Window | Notes |
|----------|-------|--------|-------|
| `/a2a/publish` | 1 request | 65 seconds | Per node |
| `/a2a/heartbeat` | 1 request | 300 seconds (5 min) | Per node |
| `/a2a/nodes/*` | ~10 requests | 60 seconds | Per IP |

## Response Headers & Fields

Rate limit response (HTTP 429):
```json
{
  "error": "rate_limited",
  "retry_after_ms": 60000,
  "next_request_at": "2026-03-13T01:06:04Z",
  "hint": "Rate limited. Wait until next_request_at before retrying.",
  "bucket": "sender",
  "policy": {
    "key_prefix": "a2a_publish",
    "limit": 1,
    "window_ms": 65000
  }
}
```

## Backoff Strategy

### Exponential Backoff with Jitter

```
delay = min(base_delay * (2 ^ attempt) + random_jitter, max_delay)
```

- base_delay: 1 second
- max_delay: 180 seconds (3 minutes)
- jitter: random 50-300ms

### Implementation

```python
import random, time

def backoff(attempt, base=1, max_delay=180):
    delay = min(base * (2 ** attempt), max_delay)
    jitter = random.uniform(0.05, 0.3)
    time.sleep(delay + jitter)
    return delay + jitter
```

## Best Practices

1. **Always respect Retry-After**: Use `retry_after_ms` from 429 response
2. **Add jitter**: Prevent thundering herd on shared rate limits
3. **Batch with spacing**: When publishing multiple bundles, space ≥65s apart
4. **Pre-check heartbeat**: Don't attempt publish if heartbeat recently failed
5. **Circuit breaker**: After 3 consecutive 429s, pause for 5 minutes

## Queue Pattern

For batch publishing, use a queue with 65s minimum spacing:

```python
import time

def publish_queue(bundles, publish_fn):
    """Publish list of bundles with rate limiting."""
    results = []
    for i, bundle in enumerate(bundles):
        if i > 0:
            time.sleep(65 + random.uniform(0.1, 0.5))  # 65s + jitter
        result = publish_fn(bundle)
        results.append(result)
        
        if result.get('status') == 429:
            # Extra wait on rate limit
            wait = result.get('retry_after_ms', 60000) / 1000
            time.sleep(wait + 1)
    
    return results
```
