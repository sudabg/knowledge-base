#!/usr/bin/env python3
"""
Compute EvoMap asset_id from an asset object.

Usage:
    python3 asset_id.py '{"type":"Gene","category":"optimize",...}'
    python3 asset_id.py --file asset.json

Or import:
    from asset_id import compute_asset_id
"""
import json, hashlib, sys

def compute_asset_id(asset: dict) -> str:
    """Compute SHA256 asset_id for an EvoMap asset (without asset_id field)."""
    # Remove asset_id if present
    clean = {k: v for k, v in asset.items() if k != 'asset_id'}
    canonical = json.dumps(clean, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return 'sha256:' + hashlib.sha256(canonical.encode()).hexdigest()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: asset_id.py '<json>' | asset_id.py --file <path>")
        sys.exit(1)
    
    if sys.argv[1] == '--file':
        with open(sys.argv[2]) as f:
            asset = json.load(f)
    else:
        asset = json.loads(sys.argv[1])
    
    aid = compute_asset_id(asset)
    print(aid)
