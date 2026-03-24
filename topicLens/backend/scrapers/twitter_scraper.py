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
    Scrape Twitter/X content by searching DuckDuckGo for tweets and threads.
    Returns expert tweets, viral threads, and influential profiles.
    """
    results = []

    # Multiple search strategies for comprehensive coverage
    search_queries = [
        f"{query} site:twitter.com",
        f"{query} site:x.com",
        f"{query} twitter thread",
        f"{query} expert tweet",
    ]

    seen_urls = set()

    for search_query in search_queries:
        if len(results) >= max_results:
            break

        try:
            # DuckDuckGo HTML search
            encoded_query = quote_plus(search_query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

            response = requests.get(url, headers=get_headers(), timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                result_links = soup.find_all("a", class_="result__a")

                for link in result_links:
                    if len(results) >= max_results:
                        break

                    href = link.get("href", "")
                    title = link.get_text(strip=True)

                    # Filter for Twitter/X URLs
                    if not href or href in seen_urls:
                        continue

                    parsed = urlparse(href)
                    is_twitter = any(domain in parsed.netloc for domain in ["twitter.com", "x.com"])

                    if not is_twitter:
                        continue

                    seen_urls.add(href)

                    # Get snippet/description
                    snippet_elem = link.find_next("a", class_="result__snippet")
                    snippet = ""
                    if snippet_elem:
                        snippet = clean_text(snippet_elem.get_text(strip=True))

                    # Determine content type
                    content_type = "tweet"
                    if "/status/" in href:
                        content_type = "tweet"
                    elif "thread" in title.lower() or "thread" in snippet.lower():
                        content_type = "thread"
                    elif "/i/lists" in href:
                        content_type = "list"
                    else:
                        content_type = "profile"

                    # Extract username from URL
                    username = ""
                    path_parts = parsed.path.strip("/").split("/")
                    if path_parts:
                        username = f"@{path_parts[0]}"

                    results.append({
                        "title": clean_text(title) or f"Twitter content about {query}",
                        "url": href,
                        "description": snippet or f"Twitter {content_type} related to {query}",
                        "source": "twitter",
                        "content_type": content_type,
                        "username": username,
                        "thumbnail": None
                    })

            rate_limit()

        except Exception as e:
            print(f"[Twitter Scraper Error] {e}")
            continue

    # Fallback: Try Nitter instances (Twitter frontend alternatives)
    if len(results) < 5:
        results.extend(_scrape_nitter_fallback(query, max_results - len(results), seen_urls))

    return results[:max_results]


def _scrape_nitter_fallback(query: str, max_results: int, seen_urls: set) -> list:
    """
    Fallback scraper using Nitter instances for Twitter content.
    """
    results = []
    nitter_instances = [
        "nitter.net",
        "nitter.it",
        "nitter.privacydev.net"
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

                    # Extract tweet content
                    content_elem = tweet.find("div", class_="tweet-content")
                    username_elem = tweet.find("a", class_="username")
                    link_elem = tweet.find("a", class_="tweet-link")

                    if content_elem and link_elem:
                        href = link_elem.get("href", "")
                        # Convert Nitter URL to Twitter URL
                        twitter_url = f"https://twitter.com{href}"

                        if twitter_url in seen_urls:
                            continue

                        seen_urls.add(twitter_url)

                        results.append({
                            "title": clean_text(content_elem.get_text()[:100]) + "...",
                            "url": twitter_url,
                            "description": clean_text(content_elem.get_text()[:200]),
                            "source": "twitter",
                            "content_type": "tweet",
                            "username": username_elem.get_text(strip=True) if username_elem else "",
                            "thumbnail": None
                        })

            rate_limit()
            break  # Stop after first successful instance

        except Exception as e:
            print(f"[Nitter Fallback Error - {instance}] {e}")
            continue

    return results


def scrape_twitter_experts(query: str, max_results: int = 10) -> list:
    """
    Find Twitter/X experts and influencers on a topic.
    """
    results = []

    search_queries = [
        f"{query} expert twitter profile",
        f"{query} influencer site:twitter.com",
        f"best {query} accounts to follow twitter",
    ]

    seen_urls = set()

    for search_query in search_queries:
        if len(results) >= max_results:
            break

        try:
            encoded_query = quote_plus(search_query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

            response = requests.get(url, headers=get_headers(), timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                result_links = soup.find_all("a", class_="result__a")

                for link in result_links:
                    if len(results) >= max_results:
                        break

                    href = link.get("href", "")
                    title = link.get_text(strip=True)

                    parsed = urlparse(href)
                    is_twitter = any(domain in parsed.netloc for domain in ["twitter.com", "x.com"])

                    # Look for profile URLs (no /status/ in path)
                    if is_twitter and "/status/" not in href and href not in seen_urls:
                        seen_urls.add(href)

                        snippet_elem = link.find_next("a", class_="result__snippet")
                        snippet = clean_text(snippet_elem.get_text(strip=True)) if snippet_elem else ""

                        results.append({
                            "title": clean_text(title),
                            "url": href,
                            "description": snippet or f"Twitter expert on {query}",
                            "source": "twitter",
                            "content_type": "expert_profile",
                            "thumbnail": None
                        })

            rate_limit()

        except Exception as e:
            print(f"[Twitter Experts Scraper Error] {e}")
            continue

    return results[:max_results]
