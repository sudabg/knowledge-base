#!/usr/bin/env node
/**
 * EvoMap Rate Limiter & Retry Manager
 * 集中式指数退避、请求排队、熔断保护
 */

const fs = require('fs');
const path = require('path');
const { parentPort, workerData, isMainThread } = require('worker_threads');

class RateLimiter {
    constructor(options = {}) {
        this.maxRetries = options.maxRetries || 3;
        this.baseDelay = options.baseDelay || 1000; // 1s
        this.maxDelay = options.maxDelay || 180000; // 3min
        this.maxConcurrent = options.maxConcurrent || 3;
        this.requests = new Map(); // per-endpoint tracking
        this.logFile = options.logFile || path.join(process.env.OPENCLAW_WORKSPACE || '/home/gem/workspace/agent', 'logs', 'rate_limit.jsonl');

        this.ensureLogDir();
    }

    ensureLogDir() {
        const logDir = path.dirname(this.logFile);
        if (!fs.existsSync(logDir)) {
            fs.mkdirSync(logDir, { recursive: true });
        }
    }

    log(event) {
        const entry = {
            timestamp: Date.now(),
            ...event
        };
        fs.appendFileSync(this.logFile, JSON.stringify(entry) + '\n');
    }

    getEndpointKey(url, method = 'GET') {
        // Simplify URL to base endpoint for rate limiting
        const urlObj = new URL(url);
        return `${method}:${urlObj.origin}${urlObj.pathname}`;
    }

    shouldThrottle(endpoint) {
        const state = this.requests.get(endpoint) || { backoffUntil: 0, consecutiveErrors: 0 };
        return Date.now() < state.backoffUntil;
    }

    getBackoffDuration(state) {
        if (!state || !state.consecutiveErrors) return 0;
        const delay = Math.min(this.baseDelay * Math.pow(2, state.consecutiveErrors), this.maxDelay);
        return delay;
    }

    async execute(fn, options = {}) {
        const { url, method = 'GET', retries = this.maxRetries } = options;
        const endpoint = this.getEndpointKey(url, method);
        const startTime = Date.now();

        let attempt = 0;
        while (attempt <= retries) {
            // Check if we're throttled
            if (this.shouldThrottle(endpoint)) {
                const state = this.requests.get(endpoint) || {};
                const waitMs = state.backoffUntil - Date.now();
                if (waitMs > 0) {
                    this.log({
                        type: 'throttled',
                        endpoint,
                        waitMs,
                        attempt
                    });
                    await this.sleep(waitMs);
                }
            }

            try {
                const result = await fn({
                    url,
                    method,
                    attempt,
                    totalAttempts: attempt + 1
                });

                // Success: reset error count
                const state = this.requests.get(endpoint) || { consecutiveErrors: 0 };
                state.consecutiveErrors = 0;
                state.backoffUntil = 0;
                this.requests.set(endpoint, state);

                const latency = Date.now() - startTime;
                this.log({
                    type: 'success',
                    endpoint,
                    method,
                    latency,
                    attempt,
                    status: result.status || 200
                });

                return result;
            } catch (error) {
                attempt++;
                const state = this.requests.get(endpoint) || { consecutiveErrors: 0 };
                state.consecutiveErrors = (state.consecutiveErrors || 0) + 1;

                // Calculate backoff
                const backoffMs = this.getBackoffDuration(state);
                state.backoffUntil = Date.now() + backoffMs;
                this.requests.set(endpoint, state);

                this.log({
                    type: 'error',
                    endpoint,
                    method,
                    error: error.message || 'Unknown error',
                    status: error.statusCode,
                    attempt,
                    consecutiveErrors: state.consecutiveErrors,
                    backoffMs
                });

                if (attempt > retries) {
                    throw error;
                }

                // Wait before retry
                if (backoffMs > 0) {
                    await this.sleep(backoffMs);
                }
            }
        }
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Stats for monitoring
    getStats() {
        const now = Date.now();
        const stats = {
            endpoints: {},
            totalThrottled: 0,
            totalErrors: 0
        };
        for (const [key, state] of this.requests.entries()) {
            const isThrottled = now < state.backoffUntil;
            stats.endpoints[key] = {
                consecutiveErrors: state.consecutiveErrors,
                throttled: isThrottled,
                backoffRemaining: isThrottled ? state.backoffUntil - now : 0
            };
            if (isThrottled) stats.totalThrottled++;
            if (state.consecutiveErrors > 0) stats.totalErrors += state.consecutiveErrors;
        }
        return stats;
    }
}

// CLI Interface
if (isMainThread) {
    const rateLimiter = new RateLimiter();

    // Export for require()
    module.exports = { RateLimiter };

    // If run directly, show stats or run a command
    const cmd = process.argv[2];
    if (cmd === 'stats') {
        const stats = rateLimiter.getStats();
        console.log(JSON.stringify(stats, null, 2));
        process.exit(0);
    } else {
        console.log('Usage: rate-limiter.js stats');
        process.exit(1);
    }
} else {
    module.exports = { RateLimiter };
}
