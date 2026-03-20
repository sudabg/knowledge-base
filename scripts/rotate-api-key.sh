#!/bin/bash
# 每3小时轮询 OpenRouter API key，避免免费额度用尽
bash /home/gem/workspace/agent/rotate-openrouter-key.sh >> /tmp/rotate-key.log 2>&1
echo "$(date): API key rotated" >> /tmp/rotate-key.log
