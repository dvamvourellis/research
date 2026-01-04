"""
Data Fetcher Module
Fetches and parses content from AI trend sources.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import json
import time
from markdownify import markdownify as md


class AITrendsFetcher:
    """Fetches content from various AI trends sources."""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # NOTE: These sources are specific URLs that should contain substantive AI trend analysis.
        # For sites with multiple articles, you should update these URLs to point to specific
        # research pieces or aggregate pages (e.g., blog sections, research hubs).
        #
        # Epoch AI options:
        #   - Blog/Research: https://epoch.ai/blog
        #   - Specific reports on compute trends, training costs, etc.
        #   - Their published research papers and analysis
        #
        # You can add multiple Epoch AI sources by adding entries like:
        #   'epoch_ai_blog': 'https://epoch.ai/blog',
        #   'epoch_ai_compute': 'https://epoch.ai/[specific-compute-article]',
        self.sources = {
            'epoch_ai_blog': 'https://epoch.ai/blog',  # Epoch AI research blog
            'dwarkesh_buildout': 'https://www.dwarkesh.com/p/thoughts-on-the-ai-buildout',
            'dwarkesh_progress': 'https://www.dwarkesh.com/p/thoughts-on-ai-progress-dec-2025',
            'ai_2027': 'https://ai-2027.com/'
        }

    def fetch_url(self, url: str, retry_count: int = 3) -> Optional[str]:
        """
        Fetch content from a URL with retries.

        Args:
            url: URL to fetch
            retry_count: Number of retries on failure

        Returns:
            HTML content or None if failed
        """
        for attempt in range(retry_count):
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                print(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"Failed to fetch {url} after {retry_count} attempts")
                    return None

    def parse_html_to_text(self, html: str) -> str:
        """
        Parse HTML to clean text content.

        Args:
            html: Raw HTML content

        Returns:
            Cleaned text content
        """
        soup = BeautifulSoup(html, 'lxml')

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text

    def parse_article_content(self, html: str, url: str) -> Dict[str, str]:
        """
        Parse article content with better structure preservation.

        Args:
            html: Raw HTML content
            url: Source URL for context

        Returns:
            Dictionary with title, content, and metadata
        """
        soup = BeautifulSoup(html, 'lxml')

        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        # Try to find the main content area
        article = soup.find('article') or soup.find('main') or soup.find('div', class_='post-content')
        if not article:
            # Fallback to body
            article = soup.find('body')

        # Extract title
        title_tag = soup.find('h1') or soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else "Untitled"

        # Convert to markdown for better structure
        content_html = str(article) if article else html
        content_md = md(content_html)

        return {
            'title': title,
            'content': content_md,
            'url': url,
            'fetched_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }

    def fetch_all_sources(self) -> Dict[str, Dict[str, str]]:
        """
        Fetch content from all configured sources.

        Returns:
            Dictionary mapping source names to their content
        """
        results = {}

        for source_name, url in self.sources.items():
            print(f"Fetching {source_name} from {url}...")
            html = self.fetch_url(url)

            if html:
                parsed_content = self.parse_article_content(html, url)
                results[source_name] = parsed_content
                print(f"✓ Successfully fetched {source_name}")
            else:
                print(f"✗ Failed to fetch {source_name}")
                results[source_name] = {
                    'title': 'Failed to fetch',
                    'content': '',
                    'url': url,
                    'fetched_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }

        return results

    def save_to_file(self, data: Dict[str, Dict[str, str]], filename: str = 'data/fetched_content.json'):
        """
        Save fetched content to a JSON file.

        Args:
            data: Content data to save
            filename: Output filename
        """
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Content saved to {filename}")


if __name__ == "__main__":
    fetcher = AITrendsFetcher()
    content = fetcher.fetch_all_sources()
    fetcher.save_to_file(content)

    # Print summary
    print("\n=== Fetch Summary ===")
    for source, data in content.items():
        print(f"{source}: {data['title']}")
        print(f"  Content length: {len(data['content'])} characters")
