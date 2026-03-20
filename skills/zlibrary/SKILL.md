# Z-Library Skill

Search and download books from Z-Library via `zlibrary` Python package.

## Usage

```bash
# Search
python3 skills/zlibrary/zlib.py search "query" [count] [lang]

# Download
python3 skills/zlibrary/zlib.py download <book_url_or_id> [output_dir]

# Check limits
python3 skills/zlibrary/zlib.py limits
```

## Requirements
- `zlibrary` pip package
- Env vars: `ZLIBRARY_EMAIL`, `ZLIBRARY_PASSWORD`
- Proxy: auto-detects `ALL_PROXY` or falls back to `socks5://127.0.0.1:10808`

## Notes
- Mirrors rotate automatically on failure
- Free account: 10 downloads/day
- If broken, run: `pip install --upgrade zlibrary`
