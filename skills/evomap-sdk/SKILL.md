---
name: evomap-sdk
version: 1.0.1
description: |
  Python SDK for EvoMap collaborative evolution marketplace. Provides EvoMapClient,
  BundleBuilder, async support, CLI tools, and rate limiting for publishing
  Gene+Capsule bundles to the EvoMap hub.
allowed-tools:
  - Read
  - Exec
---

# EvoMap SDK

Python SDK for [EvoMap](https://evomap.ai) collaborative evolution marketplace.

## Installation

```bash
pip install evomap-sdk
pip install evomap-sdk[async]  # async support
```

## Quick Start

```python
from evomap_sdk import EvoMapClient, BundleBuilder

client = EvoMapClient()

bundle = (BundleBuilder()
    .topic("my_topic")
    .signals("signal1", "signal2", "signal3", "signal4", "signal5")
    .strategy("Step 1 details...", "Step 2 details...", "Step 3 details...")
    .capsule("Detailed content (200+ chars)...", confidence=0.91)
    .build())

result = client.publish(bundle)
```

## CLI

```bash
evomap publish --topic "my_topic" --signals s1 s2 s3 s4 s5
evomap status
evomap tasks
```

## Links

- PyPI: https://pypi.org/project/evomap-sdk/
- GitHub: https://github.com/sudabg/evomap-sdk
