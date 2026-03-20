#!/usr/bin/env python3
"""Z-Library CLI - search, download, check limits."""
import asyncio, os, sys

MIRRORS = [
    "https://z-library.im",
    "https://singlelogin.re",
]

async def login():
    import zlibrary
    proxy = os.environ.get("ALL_PROXY", "socks5://127.0.0.1:10808")
    email = os.environ.get("ZLIBRARY_EMAIL", "")
    pwd = os.environ.get("ZLIBRARY_PASSWORD", "")
    if not email or not pwd:
        print("Error: Set ZLIBRARY_EMAIL and ZLIBRARY_PASSWORD env vars", file=sys.stderr)
        sys.exit(1)
    
    lib = zlibrary.AsyncZlib(proxy_list=[proxy])
    for mirror in MIRRORS:
        try:
            lib.mirror = mirror
            await lib.login(email, pwd)
            return lib
        except Exception as e:
            print(f"  {mirror} failed: {e}", file=sys.stderr)
    raise RuntimeError("All mirrors failed")

async def search(query, count=10, lang=None):
    lib = await login()
    kwargs = {"q": query, "count": count}
    if lang:
        kwargs["lang"] = [lang]
    paginator = await lib.search(**kwargs)
    await paginator.init()
    results = paginator.result[:count]
    for i, b in enumerate(results):
        print(f"{i+1}. {b.get('name','?')} | {b.get('author','?')} | {b.get('extension','?')} | {b.get('size','?')}")
        print(f"   {b.get('url','')}")
    return results

async def download(url_or_id, out_dir="."):
    lib = await login()
    if "http" in url_or_id:
        book = await lib.get_by_url(url_or_id)
    else:
        book = await lib.get_by_id(url_or_id)
    os.makedirs(out_dir, exist_ok=True)
    path = await book.download(out_dir)
    print(f"Downloaded: {path}")
    return path

async def limits():
    lib = await login()
    lim = await lib.get_limits()
    print(lim)

CMD = {"search": search, "download": download, "limits": limits}

async def main():
    if len(sys.argv) < 2 or sys.argv[1] not in CMD:
        print("Usage: zlib.py search|download|limits [args...]", file=sys.stderr)
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "search":
        q = sys.argv[2] if len(sys.argv) > 2 else ""
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        lang = sys.argv[4] if len(sys.argv) > 4 else None
        if not q:
            print("Usage: zlib.py search <query> [count] [lang]", file=sys.stderr)
            sys.exit(1)
        await search(q, n, lang)
    elif cmd == "download":
        url = sys.argv[2] if len(sys.argv) > 2 else ""
        out = sys.argv[3] if len(sys.argv) > 3 else "./books"
        if not url:
            print("Usage: zlib.py download <book_url_or_id> [output_dir]", file=sys.stderr)
            sys.exit(1)
        await download(url, out)
    elif cmd == "limits":
        await limits()

if __name__ == "__main__":
    asyncio.run(main())
