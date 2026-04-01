# Claw Compactor Skill

LLM Token Compression with 14-stage Fusion Pipeline — reduces token usage by 54% average, zero LLM inference cost, reversible.

## Usage
- `claw_compactor.compress(text)` → compressed result
- `claw_compactor.compress_messages(messages)` → compressed OpenAI format

## Config
None required. Uses FusionEngine defaults.

## Example
```json
{
  "text": "Long conversation history..."
}
```
