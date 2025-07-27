"""Web operations tool for MCP servers."""

import json
import asyncio
import logging
from typing import Any
from urllib.parse import urljoin, urlparse

from .base_tool import BaseTool


class WebTool(BaseTool):
    """Tool for web operations like HTTP requests and web scraping."""

    def __init__(
        self,
        name: str = "web_operations",
        description: str = "Perform web operations like HTTP GET/POST requests and basic web scraping",
        input_schema: dict[str, Any] | None = None,
        title: str | None = "Web Operations Tool",
    ) -> None:
        if input_schema is None:
            input_schema = {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["get", "post", "fetch_html", "download"],
                        "description": "The web operation to perform"
                    },
                    "url": {
                        "type": "string",
                        "description": "The target URL"
                    },
                    "headers": {
                        "type": "object",
                        "description": "HTTP headers as key-value pairs"
                    },
                    "data": {
                        "type": "object",
                        "description": "Data to send with POST request"
                    },
                    "timeout": {
                        "type": "number",
                        "default": 30,
                        "description": "Request timeout in seconds"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "File path for download operation"
                    }
                },
                "required": ["operation", "url"]
            }
        
        super().__init__(name, description, input_schema, title)

    async def execute(self, arguments: dict[str, Any]) -> Any:
        """Execute web operation."""
        operation = arguments.get("operation")
        url = arguments.get("url")
        headers = arguments.get("headers", {})
        data = arguments.get("data")
        timeout = arguments.get("timeout", 30)
        output_path = arguments.get("output_path")

        if not url:
            raise ValueError("URL is required")

        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid URL: {url}")

        try:
            if operation == "get":
                return await self._http_get(url, headers, timeout)
            elif operation == "post":
                return await self._http_post(url, headers, data, timeout)
            elif operation == "fetch_html":
                return await self._fetch_html(url, headers, timeout)
            elif operation == "download":
                if not output_path:
                    raise ValueError("output_path is required for download operation")
                return await self._download_file(url, output_path, headers, timeout)
            else:
                raise ValueError(f"Unknown operation: {operation}")

        except Exception as e:
            logging.error(f"Web operation failed: {e}")
            return {"error": str(e), "operation": operation, "url": url}

    async def _http_get(self, url: str, headers: dict[str, str], timeout: int) -> dict[str, Any]:
        """Perform HTTP GET request."""
        try:
            import aiohttp
        except ImportError:
            raise ImportError("aiohttp is required for web operations. Install with: pip install aiohttp")

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(url, headers=headers) as response:
                content = await response.text()
                return {
                    "success": True,
                    "operation": "get",
                    "url": url,
                    "status_code": response.status,
                    "headers": dict(response.headers),
                    "content": content,
                    "content_length": len(content)
                }

    async def _http_post(self, url: str, headers: dict[str, str], data: dict[str, Any] | None, timeout: int) -> dict[str, Any]:
        """Perform HTTP POST request."""
        try:
            import aiohttp
        except ImportError:
            raise ImportError("aiohttp is required for web operations. Install with: pip install aiohttp")

        # Set default content-type if not provided
        if "Content-Type" not in headers and data:
            headers["Content-Type"] = "application/json"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            # Prepare data based on content type
            post_data = None
            if data:
                if headers.get("Content-Type") == "application/json":
                    post_data = json.dumps(data)
                else:
                    post_data = data

            async with session.post(url, headers=headers, data=post_data) as response:
                content = await response.text()
                return {
                    "success": True,
                    "operation": "post",
                    "url": url,
                    "status_code": response.status,
                    "headers": dict(response.headers),
                    "content": content,
                    "content_length": len(content)
                }

    async def _fetch_html(self, url: str, headers: dict[str, str], timeout: int) -> dict[str, Any]:
        """Fetch and parse HTML content."""
        try:
            import aiohttp
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("aiohttp and beautifulsoup4 are required. Install with: pip install aiohttp beautifulsoup4")

        # Add user agent if not provided
        if "User-Agent" not in headers:
            headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(url, headers=headers) as response:
                html_content = await response.text()
                
                # Parse HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract useful information
                title = soup.title.string.strip() if soup.title else None
                meta_description = None
                meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
                if meta_desc_tag:
                    meta_description = meta_desc_tag.get('content')

                # Extract text content
                text_content = soup.get_text(separator=' ', strip=True)
                
                # Extract links
                links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    # Convert relative URLs to absolute
                    absolute_url = urljoin(url, href)
                    links.append({
                        "text": link.get_text(strip=True),
                        "href": absolute_url
                    })

                return {
                    "success": True,
                    "operation": "fetch_html",
                    "url": url,
                    "status_code": response.status,
                    "title": title,
                    "meta_description": meta_description,
                    "text_content": text_content[:5000],  # Limit text content
                    "links": links[:50],  # Limit number of links
                    "html_content": html_content
                }

    async def _download_file(self, url: str, output_path: str, headers: dict[str, str], timeout: int) -> dict[str, Any]:
        """Download file from URL."""
        try:
            import aiohttp
            from pathlib import Path
        except ImportError:
            raise ImportError("aiohttp is required for web operations. Install with: pip install aiohttp")

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(url, headers=headers) as response:
                file_size = 0
                with open(output_file, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                        file_size += len(chunk)

                return {
                    "success": True,
                    "operation": "download",
                    "url": url,
                    "output_path": str(output_file),
                    "status_code": response.status,
                    "file_size": file_size,
                    "content_type": response.headers.get("Content-Type")
                }