#!/usr/bin/env python3
"""
安全沙箱 Auto-Heal Monitor
自动检测并修复常见沙箱问题
"""
import subprocess
import json
import os
import time
import sys

CHECKS = []

def check(name, fn):
    """Register a health check"""
    CHECKS.append((name, fn))

def run_checks(verbose=False):
    """Run all checks and report"""
    results = []
    for name, fn in CHECKS:
        try:
            status, detail = fn()
            results.append({'check': name, 'status': status, 'detail': detail})
            icon = '✅' if status == 'ok' else '⚠️' if status == 'warn' else '❌'
            if verbose or status != 'ok':
                print(f'{icon} {name}: {detail}')
        except Exception as e:
            results.append({'check': name, 'status': 'error', 'detail': str(e)})
            if verbose:
                print(f'❌ {name}: {e}')
    return results

# === Health Checks ===

def check_python():
    v = sys.version.split()[0]
    return ('ok', f'Python {v}')

def check_disk_space():
    stat = os.statvfs('/home/gem')
    free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
    if free_gb < 1:
        return ('error', f'Low disk: {free_gb:.1f}GB')
    elif free_gb < 5:
        return ('warn', f'Disk: {free_gb:.1f}GB free')
    return ('ok', f'Disk: {free_gb:.1f}GB free')

def check_memory():
    try:
        with open('/proc/meminfo') as f:
            lines = f.readlines()
        meminfo = {}
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                meminfo[parts[0].rstrip(':')] = int(parts[1])
        free_mb = meminfo.get('MemAvailable', 0) / 1024
        total_mb = meminfo.get('MemTotal', 0) / 1024
        pct = (free_mb / total_mb * 100) if total_mb > 0 else 0
        if pct < 10:
            return ('error', f'Low memory: {free_mb:.0f}MB/{total_mb:.0f}MB ({pct:.0f}%)')
        return ('ok', f'Memory: {free_mb:.0f}MB/{total_mb:.0f}MB ({pct:.0f}%)')
    except:
        return ('warn', 'Cannot check memory')

def check_heartbeat():
    hb_file = '/home/gem/workspace/agent/workspace/.learnings/last_heartbeat.json'
    if not os.path.exists(hb_file):
        return ('warn', 'No heartbeat cache')
    try:
        with open(hb_file) as f:
            hb = json.load(f)
        return ('ok', f'Heartbeat: {hb.get("status")} credit={hb.get("credit")}')
    except:
        return ('warn', 'Heartbeat parse error')

def check_evomap_auth():
    """Check if EvoMap API is accessible"""
    try:
        r = subprocess.run(['curl', '-s', '--max-time', '5', 'https://evomap.ai/health'], 
                          capture_output=True, text=True)
        if r.returncode == 0:
            return ('ok', 'EvoMap API reachable')
        return ('warn', 'EvoMap API slow')
    except:
        return ('error', 'EvoMap API unreachable')

def check_github_auth():
    try:
        r = subprocess.run(['gh', 'auth', 'status'], capture_output=True, text=True)
        if 'Logged in' in r.stderr or 'Logged in' in r.stdout:
            return ('ok', 'GitHub authenticated')
        return ('warn', 'GitHub not authenticated')
    except:
        return ('error', 'gh CLI not available')

# Register checks
check('Python', check_python)
check('Disk Space', check_disk_space)
check('Memory', check_memory)
check('Heartbeat', check_heartbeat)
check('EvoMap API', check_evomap_auth)
check('GitHub Auth', check_github_auth)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Sandbox Auto-Heal Monitor')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-j', '--json', action='store_true')
    parser.add_argument('--watch', type=int, help='Watch mode: check every N seconds')
    args = parser.parse_args()
    
    if args.watch:
        while True:
            print(f'\n--- {time.strftime("%H:%M:%S")} ---')
            run_checks(verbose=True)
            time.sleep(args.watch)
    else:
        results = run_checks(verbose=args.verbose)
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        
        errors = [r for r in results if r['status'] == 'error']
        if errors:
            sys.exit(1)

if __name__ == '__main__':
    main()
