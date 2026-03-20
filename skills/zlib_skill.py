#!/usr/bin/env python3
"""
Z-Library Skill for OpenClaw
Direct API integration without relying on zlibrary package (which has broken parsers).
"""

import os
import asyncio
import aiohttp
from aiohttp_socks import ChainProxyConnector
from urllib.parse import quote_plus
import re
import json

class ZLibError(Exception):
    pass

class AsyncZlibSkill:
    """Z-Library autonomous access skill"""
    
    def __init__(self, email=None, password=None, proxy_list=None):
        self.email = email or os.environ.get("ZLIBRARY_EMAIL")
        self.password = password or os.environ.get("ZLIBRARY_PASSWORD")
        self.proxy_list = proxy_list or ["socks5://127.0.0.1:10808"]
        self.mirror = "https://singlelogin.re"  # Will auto-detect
        self.session = None
        self.cookies = {}
        
    async def __aenter__(self):
        await self.login()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def login(self):
        """Login to Z-Library with credentials"""
        if not self.email or not self.password:
            raise ZLibError("Missing ZLIBRARY_EMAIL or ZLIBRARY_PASSWORD")
        
        connector = ChainProxyConnector.from_urls(self.proxy_list)
        
        # Custom headers to look like a real browser
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, headers=headers, timeout=timeout)
        
        # Step 1: Get main page to set initial cookies
        try:
            async with self.session.get(self.mirror) as resp:
                await resp.text()
                self.cookies.update(resp.cookies)
        except Exception as e:
            raise ZLibError(f"Failed to access {self.mirror}: {e}")
        
        # Step 2: Try API login endpoint
        login_url = f"{self.mirror}/rpc.php"
        payload = {
            "isModal": "true",
            "email": self.email,
            "password": self.password,
            "site_mode": "books",
            "action": "login",
            "isSinglelogin": "1",
            "redirectUrl": ""
        }
        
        try:
            async with self.session.post(login_url, data=payload) as resp:
                text = await resp.text()
                
                # Check if login succeeded via JSON response
                try:
                    data = json.loads(text)
                    if data.get("payload", {}).get("user"):
                        print("✅ Login successful via API")
                        return True
                except json.JSONDecodeError:
                    pass
                
                # Check for login failure in response
                if "Invalid" in text or "incorrect" in text.lower():
                    raise ZLibError("Login failed: invalid credentials")
                
                # If we got a 200 with cookies, likely successful
                if resp.status == 200:
                    print("✅ Login successful (session established)")
                    return True
                else:
                    raise ZLibError(f"Login failed with status {resp.status}")
                    
        except Exception as e:
            raise ZLibError(f"Login error: {e}")
    
    async def search(self, query, count=10, lang=None, extensions=None):
        """
        Search for books
        
        Args:
            query: Search term
            count: Max number of results
            lang: Language filter (e.g., "english", "chinese")
            extensions: Format filter (e.g., "pdf", "epub")
        
        Returns: List of book dicts
        """
        # Build search URL
        search_url = f"{self.mirror}/s/{quote_plus(query)}"
        params = []
        if lang:
            params.append(f"lang={lang}")
        if extensions:
            if isinstance(extensions, list):
                extensions = ",".join(extensions)
            params.append(f"ext={extensions}")
        
        if params:
            search_url += "?" + "&".join(params)
        
        try:
            async with self.session.get(search_url) as resp:
                if resp.status != 200:
                    raise ZLibError(f"Search failed: {resp.status}")
                
                html = await resp.text()
                
                # Parse search results - looking for the current Z-Library structure
                books = []
                
                # Method 1: Look for z-bookcard elements (modern Z-Library)
                bookcard_pattern = r'<z-bookcard[^>]*>(.*?)</z-bookcard>'
                bookcards = re.findall(bookcard_pattern, html, re.DOTALL)
                
                if bookcards:
                    for card_html in bookcards[:count]:
                        book = self._parse_bookcard(card_html)
                        if book:
                            books.append(book)
                else:
                    # Method 2: Look for JSON data in script tags
                    json_data = re.search(r'var\s+\w+\s*=\s*(\[.*?\]);', html, re.DOTALL)
                    if json_data:
                        try:
                            data = json.loads(json_data.group(1))
                            for item in data[:count]:
                                book = self._parse_json_book(item)
                                if book:
                                    books.append(book)
                        except json.JSONDecodeError:
                            pass
                
                if not books:
                    # Method 3: Basic regex fallback
                    # Look for book IDs and titles in the HTML
                    id_pattern = r'data-book-id="([^"]+)"'
                    title_pattern = r'<div[^>]*slot="title"[^>]*>([^<]+)</div>'
                    
                    ids = re.findall(id_pattern, html)
                    titles = re.findall(title_pattern, html)
                    
                    for i, (book_id, title) in enumerate(zip(ids, titles)):
                        if i >= count:
                            break
                        books.append({
                            "id": book_id,
                            "title": title.strip(),
                            "author": "",
                            "year": "",
                            "format": "",
                            "size": "",
                            "url": f"{self.mirror}/book/{book_id}"
                        })
                
                return books[:count]
                
        except Exception as e:
            raise ZLibError(f"Search error: {e}")
    
    def _parse_bookcard(self, html):
        """Parse a z-bookcard HTML element"""
        try:
            # Extract attributes
            book_id_match = re.search(r'id="([^"]+)"', html)
            isbn_match = re.search(r'isbn="([^"]+)"', html)
            year_match = re.search(r'year="([^"]+)"', html)
            ext_match = re.search(r'extension="([^"]+)"', html)
            size_match = re.search(r'filesize="([^"]+)"', html)
            lang_match = re.search(r'language="([^"]+)"', html)
            publisher_match = re.search(r'publisher="([^"]+)"', html)
            pages_match = re.search(r'pages="([^"]+)"', html)
            
            # Extract nested content
            title_match = re.search(r'<div[^>]*slot="title"[^>]*>([^<]+)</div>', html)
            author_match = re.search(r'<div[^>]*slot="author"[^>]*>([^<]+)</div>', html)
            
            # Extract URL
            url_match = re.search(r'href="([^"]+)"', html)
            
            return {
                "id": book_id_match.group(1) if book_id_match else "",
                "title": title_match.group(1).strip() if title_match else "",
                "author": author_match.group(1).strip() if author_match else "",
                "year": year_match.group(1) if year_match else "",
                "format": ext_match.group(1) if ext_match else "",
                "size": size_match.group(1) if size_match else "",
                "language": lang_match.group(1) if lang_match else "",
                "publisher": publisher_match.group(1) if publisher_match else "",
                "pages": pages_match.group(1) if pages_match else "",
                "isbn": isbn_match.group(1) if isbn_match else "",
                "url": f"{self.mirror}{url_match.group(1)}" if url_match and url_match.group(1).startswith('/') else (url_match.group(1) if url_match else "")
            }
        except Exception:
            return None
    
    def _parse_json_book(self, item):
        """Parse a book from JSON data"""
        try:
            return {
                "id": item.get("id", ""),
                "title": item.get("title", ""),
                "author": item.get("author", ""),
                "year": item.get("year", ""),
                "format": item.get("extension", ""),
                "size": item.get("filesize", ""),
                "language": item.get("language", ""),
                "publisher": item.get("publisher", ""),
                "pages": item.get("pages", ""),
                "isbn": item.get("isbn", ""),
                "url": item.get("url", "")
            }
        except Exception:
            return None
    
    async def get_book(self, book_id):
        """Get detailed information about a book"""
        # First try the book page
        book_url = f"{self.mirror}/book/{book_id}"
        
        try:
            async with self.session.get(book_url) as resp:
                if resp.status != 200:
                    raise ZLibError(f"Book page not found: {resp.status}")
                
                html = await resp.text()
                
                # Parse book details from page
                # Look for meta tags or embedded JSON
                json_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        return {
                            "id": book_id,
                            "title": data.get("name", ""),
                            "author": ", ".join([a.get("name", "") for a in data.get("author", [])]),
                            "year": data.get("datePublished", ""),
                            "description": data.get("description", ""),
                            "cover": data.get("image", ""),
                            "publisher": "",  # JSON-LD may not have publisher
                            "language": "",
                            "pages": "",
                            "isbn": "",
                            "extension": "",
                            "size": ""
                        }
                    except json.JSONDecodeError:
                        pass
                
                # Fallback: extract from HTML with regex
                title_match = re.search(r'<h1[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</h1>', html)
                desc_match = re.search(r'<div[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
                
                return {
                    "id": book_id,
                    "title": title_match.group(1).strip() if title_match else "",
                    "author": "",
                    "year": "",
                    "description": desc_match.group(1).strip()[:500] if desc_match else "",
                    "cover": "",
                    "publisher": "",
                    "language": "",
                    "pages": "",
                    "isbn": "",
                    "extension": "",
                    "size": ""
                }
        except Exception as e:
            raise ZLibError(f"Get book error: {e}")
    
    async def get_download_url(self, book_id):
        """Get the actual download URL for a book"""
        book_url = f"{self.mirror}/book/{book_id}"
        
        try:
            async with self.session.get(book_url) as resp:
                html = await resp.text()
                
                # Look for download button/link
                dl_match = re.search(r'href="([^"]+)"[^>]*class="[^"]*download[^"]*"', html)
                if dl_match:
                    url = dl_match.group(1)
                    if url.startswith('/'):
                        url = self.mirror + url
                    return url
                
                # Alternative: look for any link containing /dl/
                dl_match2 = re.search(r'href="([^"]*/dl/[^"]+)"', html)
                if dl_match2:
                    url = dl_match2.group(1)
                    if url.startswith('/'):
                        url = self.mirror + url
                    return url
                
                raise ZLibError("Download URL not found")
        except Exception as e:
            raise ZLibError(f"Get download URL error: {e}")
    
    async def download(self, book_id, output_dir="./downloads"):
        """
        Download a book
        
        Returns: path to downloaded file
        """
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Get book details first to know filename
        book = await self.get_book(book_id)
        title = book.get("title", f"book_{book_id}")
        safe_title = re.sub(r'[^\w\-_.]', '_', title)
        
        # Get download URL
        dl_url = await self.get_download_url(book_id)
        if not dl_url:
            raise ZLibError("Cannot obtain download URL")
        
        # Download the file
        filename = f"{safe_title}"
        if book.get("extension"):
            filename += f".{book['extension']}"
        filepath = os.path.join(output_dir, filename)
        
        try:
            async with self.session.get(dl_url) as resp:
                if resp.status != 200:
                    raise ZLibError(f"Download failed: {resp.status}")
                
                # Check content-disposition for filename
                cd = resp.headers.get('Content-Disposition', '')
                if 'filename=' in cd:
                    import cgi
                    _, params = cgi.parse_header(cd)
                    if 'filename' in params:
                        filename = params['filename']
                        filepath = os.path.join(output_dir, filename)
                
                # Write file
                with open(filepath, 'wb') as f:
                    async for chunk in resp.content.iter_chunked(8192):
                        f.write(chunk)
            
            print(f"✅ Downloaded: {filepath}")
            return filepath
            
        except Exception as e:
            raise ZLibError(f"Download error: {e}")
    
    async def get_limits(self):
        """Check download limits"""
        # Try to access the downloads page
        limits_url = f"{self.mirror}/users/downloads"
        
        try:
            async with self.session.get(limits_url) as resp:
                if resp.status != 200:
                    return {"error": f"Cannot access limits page: {resp.status}"}
                
                html = await resp.text()
                
                # Try to find limit info (this is fragile and may need updating)
                # Common patterns in Z-Library's download limits page
                patterns = [
                    r'(\d+)\s*(?:/|of)\s*(\d+)',  # "X / Y" pattern
                    r'(\d+)\s+remaining',
                    r'Daily limit:\s*(\d+)'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        return {
                            "daily_limit_reached": False,
                            "remaining": int(match.group(1)),
                            "total": int(match.group(2)) if len(match.groups()) > 1 else None
                        }
                
                return {"status": "Limits info not found in page"}
        except Exception as e:
            return {"error": str(e)}


# Convenience functions for OpenClaw to call
async def search_books(query, count=10, lang=None, extensions=None):
    """
    Search Z-Library for books
    
    Args:
        query: Search term (title, author, ISBN)
        count: Number of results (default 10)
        lang: Language filter (e.g., "chinese", "english")
        extensions: Format filter (e.g., "pdf", "epub")
    
    Returns: List of book dictionaries
    """
    async with AsyncZlibSkill() as lib:
        return await lib.search(query, count=count, lang=lang, extensions=extensions)

async def get_book_details(book_id):
    """Get detailed metadata for a book"""
    async with AsyncZlibSkill() as lib:
        return await lib.get_book(book_id)

async def download_book(book_id, output_dir="./downloads"):
    """Download a book by ID"""
    async with AsyncZlibSkill() as lib:
        return await lib.download(book_id, output_dir)

async def get_download_limits():
    """Check current account's download limits"""
    async with AsyncZlibSkill() as lib:
        return await lib.get_limits()


# If run directly, test the connection
if __name__ == "__main__":
    import sys
    
    async def test():
        try:
            async with AsyncZlibSkill() as lib:
                print("✅ Login successful")
                
                # Test search
                print("\n🔍 Testing search for 'machine learning'...")
                results = await lib.search("machine learning", count=3)
                print(f"Found {len(results)} results:")
                for i, book in enumerate(results):
                    print(f"  [{i+1}] {book.get('title')} - {book.get('author')} ({book.get('year')}) [{book.get('format')}]")
                
                # Test limits
                print("\n📊 Checking download limits...")
                limits = await lib.get_limits()
                print(f"  Limits: {limits}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    asyncio.run(test())
