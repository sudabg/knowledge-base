#!/usr/bin/env python3
"""
EvoMap Batch Publisher
批量发布 Capsule 到 Hub，支持并发和自动重试
"""

import json
import time
import sys
import os
import signal
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

WORKSPACE = os.getenv('OPENCLAW_WORKSPACE', '/home/gem/workspace/agent')
LOGS_DIR = Path(WORKSPACE) / 'logs' / 'batch_publisher'
LOGS_DIR.mkdir(parents=True, exist_ok=True)

API_CALLS_LOG = LOGS_DIR / 'api_calls.jsonl'
ERROR_LOG = LOGS_DIR / 'errors.jsonl'

class BatchPublisher:
    def __init__(self, node_id: str, node_secret: str, hub_url: str = 'https://evomap.ai'):
        self.node_id = node_id
        self.node_secret = node_secret
        self.hub_url = hub.rstrip('/')
        self.session = None
        self.stats = {
            'total': 0,
            'published': 0,
            'failed': 0,
            'retried': 0,
            'start_time': time.time()
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={'Content-Type': 'application/json'},
            timeout=aiohttp.ClientTimeout(total=60)
        )
        return self

    async def __aexit__(self, *args):
        await self.session.close()

    def log_api_call(self, endpoint: str, status: int, latency: float, bundle_id: str = None):
        entry = {
            'timestamp': time.time(),
            'endpoint': endpoint,
            'status': status,
            'latency_ms': round(latency * 1000, 2),
            'bundle_id': bundle_id
        }
        with open(API_CALLS_LOG, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def log_error(self, error_type: str, message: str, bundle: Dict = None):
        entry = {
            'timestamp': time.time(),
            'error_type': error_type,
            'message': message,
            'bundle': bundle
        }
        with open(ERROR_LOG, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def compute_asset_id(self, asset: Dict) -> str:
        """Compute SHA256 asset_id following GEP-A2A spec"""
        import hashlib

        # Remove asset_id if present
        asset_copy = {k: v for k, v in asset.items() if k != 'asset_id'}

        # Serialize with strict rules
        json_str = json.dumps(
            asset_copy,
            sort_keys=True,
            separators=(',', ':'),
            ensure_ascii=False
        )

        # Hash UTF-8 bytes
        digest = hashlib.sha256(json_str.encode('utf-8')).hexdigest()
        return f'sha256:{digest}'

    async def publish_bundle(self, bundle: Dict, retry: int = 0) -> bool:
        """Publish a single Gene+Capsule bundle"""
        bundle_id = bundle.get('capsule', {}).get('title', 'unknown')
        url = f'{self.hub_url}/a2a/publish'

        # Add auth
        headers = {
            **self.session._default_headers,
            'Authorization': f'Bearer {self.node_secret}'
        }

        # Compute asset_id for both gene and capsule
        try:
            if 'gene' in bundle:
                bundle['gene']['asset_id'] = self.compute_asset_id(bundle['gene'])
            if 'capsule' in bundle:
                bundle['capsule']['asset_id'] = self.compute_asset_id(bundle['capsule'])
        except Exception as e:
            self.log_error('asset_computation_failed', str(e), bundle)
            return False

        start = time.time()
        try:
            async with self.session.post(url, json=bundle, headers=headers) as resp:
                latency = time.time() - start
                status = resp.status
                self.log_api_call('publish', status, latency, bundle_id)

                if status in (200, 201):
                    data = await resp.json()
                    self.stats['published'] += 1
                    print(f'✅ Published: {bundle_id} (score: {data.get("gdi_score", "?")})')
                    return True
                elif status == 429:
                    # Rate limit: retry with backoff
                    retry_after = int(resp.headers.get('Retry-After', 65))
                    print(f'⏳ Rate limited: {bundle_id}, waiting {retry_after}s...')
                    await asyncio.sleep(retry_after)
                    self.stats['retried'] += 1
                    if retry < 2:
                        return await self.publish_bundle(bundle, retry + 1)
                    else:
                        self.log_error('rate_limit_exhausted', f'Failed after {retry} retries', bundle)
                        self.stats['failed'] += 1
                        return False
                elif status == 409:
                    # Duplicate: skip but log
                    print(f'⚠️  Duplicate: {bundle_id} (skipping)')
                    self.log_error('duplicate_asset', 'Asset already exists', bundle)
                    self.stats['failed'] += 1
                    return False
                else:
                    error_text = await resp.text()
                    print(f'❌ Failed: {bundle_id} - {status}: {error_text[:100]}')
                    self.log_error('publish_failed', f'HTTP {status}: {error_text[:200]}', bundle)
                    self.stats['failed'] += 1
                    return False

        except Exception as e:
            latency = time.time() - start
            self.log_api_call('publish', 0, latency, bundle_id)
            self.log_error('network_error', str(e), bundle)
            print(f'❌ Error: {bundle_id} - {str(e)[:100]}')
            self.stats['failed'] += 1
            return False

    async def publish_all(self, bundles: List[Dict], concurrency: int = 3, delay: float = 65.0):
        """Publish all bundles with controlled concurrency and delay"""
        self.stats['total'] = len(bundles)
        semaphore = asyncio.Semaphore(concurrency)
        tasks = []

        async def worker(bundle, index):
            async with semaphore:
                # Stagger publishes to respect rate limit
                if index > 0:
                    await asyncio.sleep(delay)
                return await self.publish_bundle(bundle)

        for i, bundle in enumerate(bundles):
            tasks.append(worker(bundle, i))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Print summary
        duration = time.time() - self.stats['start_time']
        print(f'\n📊 Batch Summary:')
        print(f'   Total: {self.stats["total"]}')
        print(f'   Published: {self.stats["published"]}')
        print(f'   Failed: {self.stats["failed"]}')
        print(f'   Retried: {self.stats["retried"]}')
        print(f'   Duration: {duration / 60:.1f} minutes')
        print(f'   Success Rate: {(self.stats["published"] / self.stats["total"] * 100):.1f}%')

        return all(isinstance(r, bool) and r for r in results)

def load_bundles(queue_file: str) -> List[Dict]:
    """Load bundles from queue file"""
    with open(queue_file, 'r') as f:
        data = json.load(f)
    return data.get('bundles', [])

async def main():
    import argparse
    parser = argparse.ArgumentParser(description='EvoMap Batch Publisher')
    parser.add_argument('--queue', default=str(Path(WORKSPACE) / 'evolution' / 'capsule_queue.json'),
                        help='Path to bundle queue JSON')
    parser.add_argument('--concurrency', type=int, default=3,
                        help='Concurrent publishes (default: 3)')
    parser.add_argument('--delay', type=float, default=65.0,
                        help='Delay between batches in seconds (default: 65)')
    args = parser.parse_args()

    # Load credentials from .env
    from dotenv import load_dotenv
    load_dotenv('/tmp/.env')

    node_id = os.getenv('A2A_NODE_ID')
    node_secret = os.getenv('A2A_NODE_SECRET')
    hub_url = os.getenv('A2A_HUB_URL', 'https://evomap.ai')

    if not node_id or not node_secret:
        print('❌ Missing A2A_NODE_ID or A2A_NODE_SECRET in .env')
        sys.exit(1)

    queue_path = Path(args.queue)
    if not queue_path.exists():
        print(f'❌ Queue file not found: {queue_path}')
        sys.exit(1)

    bundles = load_bundles(str(queue_path))
    print(f'📦 Loaded {len(bundles)} bundles from queue')

    async with BatchPublisher(node_id, node_secret, hub_url) as publisher:
        success = await publisher.publish_all(
            bundles,
            concurrency=args.concurrency,
            delay=args.delay
        )
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    asyncio.run(main())
