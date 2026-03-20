#!/usr/bin/env node
/**
 * EvoMap Preflight Checklist
 * 在每次进化循环开始前运行，防止常见错误
 */

const fs = require('fs');
const path = require('path');

const ERROR = '\x1b[31m❌\x1b[0m';
const WARN = '\x1b[33m⚠️\x1b[0m';
const OK = '\x1b[32m✅\x1b[0m';

let errorCount = 0;
let warningCount = 0;

function log(type, msg) {
    console.log(`${type} ${msg}`);
}

function checkFile(filePath, desc, required = true) {
    if (fs.existsSync(filePath)) {
        try {
            const stat = fs.statSync(filePath);
            if (stat.mode & 0o111) {
                log(OK, `${desc}: ${filePath} (executable)`);
            } else {
                log(OK, `${desc}: ${filePath}`);
            }
            return true;
        } catch (e) {
            log(ERROR, `${desc}: ${filePath} (permission denied)`);
            errorCount++;
            return false;
        }
    } else {
        if (required) {
            log(ERROR, `${desc}: ${filePath} (missing)`);
            errorCount++;
        } else {
            log(WARN, `${desc}: ${filePath} (missing)`);
            warningCount++;
        }
        return false;
    }
}

function checkFileContent(filePath, patterns, desc) {
    if (!fs.existsSync(filePath)) {
        log(WARN, `${desc}: file not found`);
        warningCount++;
        return false;
    }
    const content = fs.readFileSync(filePath, 'utf8');
    const missing = patterns.filter(p => !content.includes(p));
    if (missing.length === 0) {
        log(OK, `${desc}: all patterns present`);
        return true;
    } else {
        log(ERROR, `${desc}: missing ${missing.join(', ')}`);
        errorCount++;
        return false;
    }
}

function checkGitRepo(workDir) {
    try {
        const gitDir = path.join(workDir, '.git');
        if (!fs.existsSync(gitDir)) {
            log(ERROR, 'Git repository: not initialized');
            errorCount++;
            return false;
        }
        // Check if repo has commits
        const head = path.join(gitDir, 'HEAD');
        if (fs.existsSync(head)) {
            log(OK, 'Git repository: initialized with commits');
            return true;
        } else {
            log(WARN, 'Git repository: exists but no commits yet');
            warningCount++;
            return true;
        }
    } catch (e) {
        log(ERROR, `Git repository: ${e.message}`);
        errorCount++;
        return false;
    }
}

function checkEnvFile(envPath) {
    if (!fs.existsSync(envPath)) {
        log(ERROR, `.env file: ${envPath} missing`);
        errorCount++;
        return false;
    }
    const content = fs.readFileSync(envPath, 'utf8');
    const required = ['A2A_NODE_ID', 'A2A_NODE_SECRET', 'A2A_HUB_URL'];
    const optional = ['OPENCLAW_WORKSPACE', 'EVOLVER_REPO_ROOT'];

    const missing = required.filter(key => !content.includes(key));
    if (missing.length > 0) {
        log(ERROR, `.env: missing required keys: ${missing.join(', ')}`);
        errorCount++;
        return false;
    }

    const optMissing = optional.filter(key => !content.includes(key));
    if (optMissing.length > 0) {
        log(WARN, `.env: optional keys not set: ${optMissing.join(', ')}`);
        warningCount++;
    }

    log(OK, `.env: all required keys present`);
    return true;
}

function main() {
    console.log('\n\x1b[36m🔍 EvoMap Preflight Checklist\x1b[0m\n');
    const workspace = process.env.OPENCLAW_WORKSPACE || '/home/gem/workspace/agent';
    const envFile = '/tmp/.env';

    log(OK, `Workspace: ${workspace}`);
    log(OK, `Env file: ${envFile}\n`);

    // 1. Credentials (check HOME/.evomap - Evolver convention)
    console.log('\x1b[36m▸ Credentials\x1b[0m');
    const homeEvomap = path.join(process.env.HOME || '/home/gem', '.evomap');
    checkFile(path.join(homeEvomap, 'node_secret'), 'Node secret file (Evolver)', true);
    checkFile(path.join(homeEvomap, 'node_id'), 'Node ID file (Evolver)', true);

    // 2. Configuration
    console.log('\n\x1b[36m▸ Configuration\x1b[0m');
    checkEnvFile(envFile);
    checkGitRepo(workspace);

    // 3. Tools
    console.log('\n\x1b[36m▸ Tools\x1b[0m');
    checkFile('/tmp/evolver-1.29.4/src/gep/a2aProtocol.js', 'Evolver A2A protocol', false);
    checkFile('/usr/bin/curl', 'curl', true);

    // 4. Workspace Structure
    console.log('\n\x1b[36m▸ Workspace\x1b[0m');
    checkFile(path.join(workspace, 'memory'), 'Memory directory', false);
    checkFile(path.join(workspace, 'skills'), 'Skills directory', false);
    checkFile(path.join(workspace, 'logs'), 'Logs directory', false);

    // 5. Rate Limit Check
    console.log('\n\x1b[36m▸ Recent Errors\x1b[0m');
    const errorLog = path.join(workspace, 'logs', 'errors.jsonl');
    if (fs.existsSync(errorLog)) {
        const lines = fs.readFileSync(errorLog, 'utf8').trim().split('\n');
        const recent = lines.filter(l => {
            try {
                const entry = JSON.parse(l);
                const hourAgo = Date.now() - 60 * 60 * 1000;
                return entry.timestamp > hourAgo;
            } catch { return false; }
        });
        if (recent.length > 0) {
            const counts = {};
            recent.forEach(r => {
                counts[r.error] = (counts[r.error] || 0) + 1;
            });
            const top = Object.entries(counts).sort((a,b) => b[1] - a[1])[0];
            log(WARN, `Recent errors: ${top[0]} (${top[1]} times)`);
            warningCount++;
        } else {
            log(OK, 'No recent errors (last hour)');
        }
    } else {
        log(WARN, 'No error log found');
        warningCount++;
    }

    // Summary
    console.log('\n\x1b[36m▸ Summary\x1b[0m');
    if (errorCount === 0 && warningCount === 0) {
        console.log(OK + ' All checks passed!\n');
        process.exit(0);
    } else if (errorCount === 0) {
        console.log(OK + ' All critical checks passed');
        console.log(WARN + ` ${warningCount} warning(s) (non-blocking)\n`);
        process.exit(0);
    } else {
        console.log(`${ERROR} ${errorCount} error(s), ${WARN} ${warningCount} warning(s)\n`);
        console.log('💡 Fix the errors above before proceeding.');
        console.log('   Run: /home/gem/workspace/agent/workspace/scripts/evomap-config.sh\n');
        process.exit(1);
    }
}

main();
