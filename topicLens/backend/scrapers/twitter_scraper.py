"""
Twitter/X Scraper using Universal Search Engine approach.
Since Twitter/X is a walled garden, we query search engines to find
expert tweets, threads, and profiles without hitting login walls.
"""
import requests
from urllib.parse import quote_plus, urlparse
from bs4 import BeautifulSoup
from .utils import get_headers, rate_limit, clean_text


def scrape_twitter(query: str, max_results: int = 15) -> list:
    """
    Scrape Twitter/X content by searching multiple sources.
    Returns expert tweets, viral threads, and influential profiles.
    """
    results = []
    seen_urls = set()

    # Strategy 1: DuckDuckGo search with multiple queries
    ddg_results = _search_duckduckgo_twitter(query, max_results, seen_urls)
    results.extend(ddg_results)

    # Strategy 2: Try finding Twitter content via broader search
    if len(results) < 5:
        broad_results = _search_twitter_broad(query, max_results - len(results), seen_urls)
        results.extend(broad_results)

    # Strategy 3: Nitter fallback
    if len(results) < 5:
        nitter_results = _scrape_nitter_fallback(query, max_results - len(results), seen_urls)
        results.extend(nitter_results)

    return results[:max_results]


def _search_duckduckgo_twitter(query: str, max_results: int, seen_urls: set) -> list:
    """Search DuckDuckGo specifically for Twitter/X content."""
    results = []

    search_queries = [
        f'"{query}" site:twitter.com',
        f'"{query}" site:x.com',
        f"{query} twitter thread best",
        f"{query} viral tweet",
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
                    if "uddg=" in href:
                        from urllib.parse import parse_qs
                        parsed = urlparse(href)
                        params = parse_qs(parsed.query)
                        href = params.get("uddg", [href])[0]

                    if not href or href in seen_urls:
                        continue

                    # Check if it's a Twitter/X URL
                    parsed = urlparse(href)
                    is_twitter = any(d in parsed.netloc.lower() for d in ["twitter.com", "x.com"])

                    if not is_twitter:
                        continue

                    seen_urls.add(href)

                    # Get snippet
                    snippet_elem = div.find("a", class_="result__snippet")
                    snippet = clean_text(snippet_elem.get_text(strip=True)) if snippet_elem else ""

                    # Determine content type
                    content_type = _determine_content_type(href, title, snippet)

                    # Extract username
                    username = _extract_username(parsed)

                    results.append({
                        "title": clean_text(title) or f"Twitter content about {query}",
                        "url": href.replace("x.com", "twitter.com"),  # Normalize to twitter.com
                        "description": snippet or f"Twitter {content_type} related to {query}",
                        "source": "twitter",
                        "content_type": content_type,
                        "username": username,
                        "thumbnail": None
                    })

            rate_limit()

        except Exception as e:
            print(f"[Twitter DDG Error] {e}")
            continue

    return results


def _search_twitter_broad(query: str, max_results: int, seen_urls: set) -> list:
    """Broader search for Twitter content mentioned on other sites."""
    results = []

    search_queries = [
        f"{query} best twitter accounts to follow",
        f"{query} twitter influencers list",
        f"top {query} tweets",
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

                # Look for Twitter links in all results
                all_links = soup.find_all("a", href=True)

                for link in all_links:
                    href = link.get("href", "")

                    # Handle DuckDuckGo URL wrapping
                    if "uddg=" in href:
                        from urllib.parse import parse_qs
                        parsed_url = urlparse(href)
                        params = parse_qs(parsed_url.query)
                        href = params.get("uddg", [href])[0]

                    if href in seen_urls:
                        continue

                    parsed = urlparse(href)
                    is_twitter = any(d in parsed.netloc.lower() for d in ["twitter.com", "x.com"])

                    if is_twitter:
                        seen_urls.add(href)

                        title = link.get_text(strip=True) or f"Twitter content"
                        content_type = _determine_content_type(href, title, "")
                        username = _extract_username(parsed)

                        results.append({
                            "title": clean_text(title)[:100] if title else f"Twitter {content_type}",
                            "url": href.replace("x.com", "twitter.com"),
                            "description": f"Twitter {content_type} about {query}",
                            "source": "twitter",
                            "content_type": content_type,
                            "username": username,
                            "thumbnail": None
                        })

                        if len(results) >= max_results:
                            break

            rate_limit()

        except Exception as e:
            print(f"[Twitter Broad Search Error] {e}")
            continue

    return results


def _scrape_nitter_fallback(query: str, max_results: int, seen_urls: set) -> list:
    """Fallback scraper using Nitter instances for Twitter content."""
    results = []
    nitter_instances = [
        "nitter.privacydev.net",
        "nitter.poast.org",
        "nitter.woodland.cafe",
    ]

    for instance in nitter_instances:
        if len(results) >= max_results:
            break

        try:
            search_url = f"https://{instance}/search?f=tweets&q={quote_plus(query)}"
            response = requests.get(search_url, headers=get_headers(), timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                tweets = soup.find_all("div", class_="timeline-item")

                for tweet in tweets[:max_results]:
                    if len(results) >= max_results:
                        break

                    content_elem = tweet.find("div", class_="tweet-content")
                    username_elem = tweet.find("a", class_="username")
                    link_elem = tweet.find("a", class_="tweet-link")

                    if content_elem and link_elem:
                        href = link_elem.get("href", "")
                        twitter_url = f"https://twitter.com{href}"

                        if twitter_url in seen_urls:
                            continue

                        seen_urls.add(twitter_url)
                        content = clean_text(content_elem.get_text())

                        results.append({
                            "title": content[:80] + "..." if len(content) > 80 else content,
                            "url": twitter_url,
                            "description": content[:200],
                            "source": "twitter",
                            "content_type": "tweet",
                            "username": username_elem.get_text(strip=True) if username_elem else "",
                            "thumbnail": None
                        })

                if results:
                    break  # Stop after first successful instance

            rate_limit()

        except Exception as e:
            print(f"[Nitter {instance} Error] {e}")
            continue

    return results


def _determine_content_type(url: str, title: str, snippet: str) -> str:
    """Determine the type of Twitter content."""
    combined = (title + snippet).lower()

    if "/status/" in url:
        if "thread" in combined:
            return "thread"
        return "tweet"
    elif "/i/lists" in url:
        return "list"
    elif "/search" in url:
        return "search"
    elif "/hashtag/" in url:
        return "hashtag"
    else:
        # Likely a profile
        return "profile"


def _extract_username(parsed_url) -> str:
    """Extract username from Twitter URL."""
    path_parts = [p for p in parsed_url.path.strip("/").split("/") if p]
    if path_parts and path_parts[0] not in ["search", "hashtag", "i", "intent"]:
        return f"@{path_parts[0]}"
    return ""


def scrape_twitter_experts(query: str, max_results: int = 10) -> list:
    """Find Twitter/X experts and influencers on a topic."""
    results = []
    seen_urls = set()

    search_queries = [
        f"{query} expert twitter profile site:twitter.com",
        f"best {query} twitter accounts to follow",
        f"{query} thought leader twitter",
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

                    # Handle URL wrapping
                    if "uddg=" in href:
                        from urllib.parse import parse_qs
                        parsed = urlparse(href)
                        params = parse_qs(parsed.query)
                        href = params.get("uddg", [href])[0]

                    parsed = urlparse(href)
                    is_twitter = any(d in parsed.netloc.lower() for d in ["twitter.com", "x.com"])

                    # Look for profile URLs (no /status/ in path)
                    if is_twitter and "/status/" not in href and href not in seen_urls:
                        seen_urls.add(href)

                        snippet_elem = div.find("a", class_="result__snippet")
                        snippet = clean_text(snippet_elem.get_text(strip=True)) if snippet_elem else ""

                        results.append({
                            "title": clean_text(title),
                            "url": href.replace("x.com", "twitter.com"),
                            "description": snippet or f"Twitter expert on {query}",
                            "source": "twitter",
                            "content_type": "expert_profile",
                            "username": _extract_username(parsed),
                            "thumbnail": None
                        })

            rate_limit()

        except Exception as e:
            print(f"[Twitter Experts Error] {e}")
            continue

    return results[:max_results]
