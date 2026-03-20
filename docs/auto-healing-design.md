# Auto-Healing System for EvoMap Agents

## Overview

Auto-healing provides resilience against transient failures, configuration drift, and unexpected state corruption. Instead of requiring manual intervention, the agent continuously monitors its health and can autonomously recover from common failure modes.

## Design Goals
- **Self-diagnosis**: Detect anomalies without external signals
- **Safe recovery**: Roll back to known-good state without data loss
- **Proactive stability**: Prevent failures before they occur
- **Observability**: Comprehensive logs and metrics for debugging

## Components

### Health Monitor (`scripts/health-monitor.js`)

Runs as a background thread (30s interval):

```javascript
class HealthMonitor {
    constructor() {
        this.metrics = {
            consecutiveErrors: 0,
            lastHeartbeat: 0,
            diskUsage: 0,
            memoryUsage: 0,
            apiSuccessRate: 1.0
        };
    }

    tick() {
        this.checkDiskSpace();
        this.checkMemoryPressure();
        this.checkErrorRate();
        this.checkHeartbeatGap();

        if (this.shouldTriggerHealing()) {
            this.triggerHealing();
        }
    }

    checkDiskSpace() {
        const usage = fs.statvfs(workspace).blocks_used / fs.statvfs(workspace).blocks_total;
        this.metrics.diskUsage = usage;
        if (usage > 0.95) {
            this.alert('CRITICAL: Disk >95% full');
        }
    }

    checkMemoryPressure() {
        const usage = process.memoryUsage().heapUsed / process.memoryUsage().heapTotal;
        this.metrics.memoryUsage = usage;
        if (usage > 0.9) {
            this.alert('WARN: Memory >90%');
        }
    }

    checkErrorRate() {
        // Read logs/evomap/*.log, count errors in last 5 min
        // If error rate > 30% over 100 requests → trigger
    }

    checkHeartbeatGap() {
        const gap = Date.now() - this.metrics.lastHeartbeat;
        if (gap > 5 * 60 * 1000) { // 5 min
            this.alert('ERROR: Heartbeat stale');
        }
    }
}
```

### Healing Actions

1. **Configuration Rollback**
   - If preflight fails after a change, automatically restore `openclaw.json` from `openclaw.json.backup_<timestamp>`
   - Revert `.env` and credential files from git history

2. **Process Restart**
   - If memory usage >90% for >3 consecutive checks → gracefully restart evolution loop
   - Use `gateway restart` with SIGUSR1 (no downtime for main session)

3. **Rate Limit Cool-down**
   - If rate limit errors detected → enter exponential backoff (doubling wait each time)
   - Auto-resume after `retry_after_ms` + jitter

4. **Dependency Reinstallation**
   - Detect missing npm/pip modules → run `npm ci` / `pip install -r requirements.txt`
   - Record to `logs/auto-heal/dependency-reinstall.log`

5. **Cache Purge**
   - If disk >90% → purge old logs (keep last 7 days) and tmp files

### Safe State Snapshots

- Before each evolution cycle, create snapshot:
  - `snapshots/state_<timestamp>.tar.gz` containing:
    - `memory/` (excluding PII)
    - `scripts/` (all scripts)
    - `logs/evomap/` (last 1h)
- Retention: keep last 10 snapshots, older ones auto-deleted

### Auto-Heal Trigger Flow

```
[Anomaly Detected] 
    ↓
[Severity Assessment]
    ├─ Critical (disk full, heartbeat lost >10min)
    │   └─ Immediate: clean temp, restart gateway, send alert
    ├─ High (consecutive errors > 5, memory >95%)
    │   └─ Restart agent process, backoff 60s
    └─ Medium (config preflight fail, dependency missing)
        └─ Rollback last config change, reinstall deps
```

## Integration

- Preflight script runs before each cycle
- Health monitor runs in background (`node scripts/health-monitor.js &`)
- Failed healing actions recorded in `.learnings/ERRORS.md`
- All actions include `EvolutionEvent` reporting to Hub (only on successful recovery)

## Deployment

Add to `AGENTS.md` startup sequence:

```bash
# Start health monitor (runs forever)
node /home/gem/workspace/agent/scripts/health-monitor.js > logs/health-monitor.log 2>&1 &
```

Add to `evomap_loop_v4.py`:

```python
def check_health():
    if not preflight_check():
        log('Health check failed, pausing evolution...')
        time.sleep(300)  # wait before retry
        return False
    return True
```
