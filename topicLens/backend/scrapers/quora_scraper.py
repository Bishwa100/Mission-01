"""
Quora Scraper using Universal Search Engine approach.
Extracts Q&A content, answers from experts, and topic spaces.
"""
import requests
from urllib.parse import quote_plus, urlparse, parse_qs
from bs4 import BeautifulSoup
from .utils import get_headers, rate_limit, clean_text


def scrape_quora(query: str, max_results: int = 15) -> list:
    """
    Scrape Quora Q&A content using multiple search strategies.
    Returns questions, answers, and topic spaces related to the query.
    """
    results = []
    seen_urls = set()

    # Strategy 1: DuckDuckGo site-specific search
    ddg_results = _search_quora_duckduckgo(query, max_results, seen_urls)
    results.extend(ddg_results)

    # Strategy 2: Broader DuckDuckGo search
    if len(results) < 5:
        broad_results = _search_quora_broad(query, max_results - len(results), seen_urls)
        results.extend(broad_results)

    return results[:max_results]


def _search_quora_duckduckgo(query: str, max_results: int, seen_urls: set) -> list:
    """Search DuckDuckGo for Quora content."""
    results = []

    search_queries = [
        f'"{query}" site:quora.com',
        f"what is {query} site:quora.com",
        f"how to learn {query} site:quora.com",
        f"{query} best answer quora",
    ]

    for search_query in search_queries:
        if len(results) >= max_results:
            break

        try:
            encoded_query = quote_plus(search_query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

            response = requests.get(url, headers=get_headers(), timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                result_divs = soup.find_all("div", class_="result")

                for div in result_divs:
                    if len(results) >= max_results:
                        break

                    link = div.find("a", class_="result__a")
                    if not link:
                        continue

                    href = link.get("href", "")
                    title = link.get_text(strip=True)

                    # Handle DuckDuckGo URL wrapping
                    href = _unwrap_ddg_url(href)

                    if not href or href in seen_urls:
                        continue

                    parsed = urlparse(href)
                    if "quora.com" not in parsed.netloc.lower():
                        continue

                    seen_urls.add(href)

                    # Get snippet
                    snippet_elem = div.find("a", class_="result__snippet")
                    snippet = clean_text(snippet_elem.get_text(strip=True)) if snippet_elem else ""

                    # Determine content type
                    content_type = _determine_quora_type(href)

                    # Clean title
                    clean_title = title.replace(" - Quora", "").strip()

                    results.append({
                        "title": clean_title or f"Quora Q&A about {query}",
                        "url": href,
                        "description": snippet or f"Quora {content_type} related to {query}",
                        "source": "quora",
                        "content_type": content_type,
                        "thumbnail": None
                    })

            rate_limit()

        except Exception as e:
            print(f"[Quora DDG Error] {e}")
            continue

    return results


def _search_quora_broad(query: str, max_results: int, seen_urls: set) -> list:
    """Broader search to find Quora links from any source."""
    results = []

    search_queries = [
        f"{query} questions answers quora",
        f"best {query} explanations quora",
        f"{query} guide quora",
    ]

    for search_query in search_queries:
        if len(results) >= max_results:
            break

        try:
            encoded_query = quote_plus(search_query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

            response = requests.get(url, headers=get_headers(), timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")

                # Look for all links that might point to Quora
                all_links = soup.find_all("a", href=True)

                for link in all_links:
                    if len(results) >= max_results:
                        break

                    href = link.get("href", "")
                    href = _unwrap_ddg_url(href)

                    if not href or href in seen_urls:
                        continue

                    parsed = urlparse(href)
                    if "quora.com" not in parsed.netloc.lower():
                        continue

                    seen_urls.add(href)

                    title = link.get_text(strip=True) or "Quora Q&A"
                    content_type = _determine_quora_type(href)

                    results.append({
                        "title": title.replace(" - Quora", "").strip()[:100],
                        "url": href,
                        "description": f"Quora {content_type} about {query}",
                        "source": "quora",
                        "content_type": content_type,
                        "thumbnail": None
                    })

            rate_limit()

        except Exception as e:
            print(f"[Quora Broad Error] {e}")
            continue

    return results


def _unwrap_ddg_url(url: str) -> str:
    """Unwrap DuckDuckGo redirect URLs."""
    if "uddg=" in url:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        return params.get("uddg", [url])[0]
    return url


def _determine_quora_type(url: str) -> str:
    """Determine the type of Quora content from URL."""
    url_lower = url.lower()

    if "/topic/" in url_lower:
        return "topic"
    elif "/profile/" in url_lower:
        return "profile"
    elif "/space/" in url_lower or "/q/" in url_lower:
        return "space"
    elif "/answer/" in url_lower:
        return "answer"
    else:
        return "question"


def scrape_quora_topics(query: str, max_results: int = 10) -> list:
    """Find Quora topic spaces and communities for a subject."""
    results = []
    seen_urls = set()

    search_queries = [
        f'"{query}" topic site:quora.com',
        f"{query} space site:quora.com",
    ]

    for search_query in search_queries:
        if len(results) >= max_results:
            break

        try:
            encoded_query = quote_plus(search_query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

            response = requests.get(url, headers=get_headers(), timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                result_divs = soup.find_all("div", class_="result")

                for div in result_divs:
                    if len(results) >= max_results:
                        break

                    link = div.find("a", class_="result__a")
                    if not link:
                        continue

                    href = link.get("href", "")
                    title = link.get_text(strip=True)

                    href = _unwrap_ddg_url(href)

                    parsed = urlparse(href)
                    if "quora.com" not in parsed.netloc.lower():
                        continue

                    # Only include topic/space URLs
                    if "/topic/" not in href and "/space/" not in href:
                        continue

                    if href in seen_urls:
                        continue

                    seen_urls.add(href)

                    snippet_elem = div.find("a", class_="result__snippet")
                    snippet = clean_text(snippet_elem.get_text(strip=True)) if snippet_elem else ""

                    results.append({
                        "title": title.replace(" - Quora", "").strip(),
                        "url": href,
                        "description": snippet or f"Quora topic space for {query}",
                        "source": "quora",
                        "content_type": "topic_space",
                        "thumbnail": None
                    })

            rate_limit()

        except Exception as e:
            print(f"[Quora Topics Error] {e}")
            continue

    return results[:max_results]


def scrape_quora_experts(query: str, max_results: int = 10) -> list:
    """Find Quora experts and top writers on a topic."""
    results = []
    seen_urls = set()

    search_queries = [
        f"{query} expert quora profile",
        f"{query} top writer site:quora.com/profile",
        f"best {query} answers quora",
    ]

    for search_query in search_queries:
        if len(results) >= max_results:
            break

        try:
            encoded_query = quote_plus(search_query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

            response = requests.get(url, headers=get_headers(), timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                result_divs = soup.find_all("div", class_="result")

                for div in result_divs:
                    if len(results) >= max_results:
                        break

                    link = div.find("a", class_="result__a")
                    if not link:
                        continue

                    href = link.get("href", "")
                    title = link.get_text(strip=True)

                    href = _unwrap_ddg_url(href)

                    parsed = urlparse(href)
                    if "quora.com" not in parsed.netloc.lower():
                        continue

                    if href in seen_urls:
                        continue

                    seen_urls.add(href)

                    snippet_elem = div.find("a", class_="result__snippet")
                    snippet = clean_text(snippet_elem.get_text(strip=True)) if snippet_elem else ""

                    # Check if it's a profile or an answer with expert content
                    content_type = "expert_answer"
                    if "/profile/" in href:
                        content_type = "expert_profile"

                    results.append({
                        "title": title.replace(" - Quora", "").strip(),
                        "url": href,
                        "description": snippet or f"Quora expert on {query}",
                        "source": "quora",
                        "content_type": content_type,
                        "thumbnail": None
                    })

            rate_limit()

        except Exception as e:
            print(f"[Quora Experts Error] {e}")
            continue

    return results[:max_results]
