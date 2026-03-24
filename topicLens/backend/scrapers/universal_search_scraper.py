"""
Universal Search Engine Scraper.
Uses search engines to find content from walled-garden platforms.
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse, parse_qs
from .utils import get_headers, rate_limit, clean_text


def search_duckduckgo(query: str, max_results: int = 10) -> list:
    """
    Search DuckDuckGo HTML version to extract results.
    This is the core of our "Universal Search Engine" approach.
    """
    results = []
    try:
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        response = requests.get(search_url, headers=get_headers(), timeout=15)

        if response.status_code != 200:
            return results

        soup = BeautifulSoup(response.text, "lxml")

        # DuckDuckGo HTML results are in .result class
        result_divs = soup.find_all("div", class_="result")

        for div in result_divs[:max_results * 2]:  # Get more to filter
            try:
                # Title and URL
                title_link = div.find("a", class_="result__a")
                if not title_link:
                    continue

                title = clean_text(title_link.get_text())
                url = title_link.get("href", "")

                # Clean the URL (DuckDuckGo wraps URLs)
                url = _unwrap_ddg_url(url)

                # Description/snippet
                snippet_div = div.find("a", class_="result__snippet")
                description = clean_text(snippet_div.get_text()) if snippet_div else ""

                if title and url:
                    results.append({
                        "title": title,
                        "url": url,
                        "description": description,
                        "source": "search"
                    })

                if len(results) >= max_results:
                    break

            except Exception:
                continue

        rate_limit()

    except Exception as e:
        print(f"[DuckDuckGo Search Error] {e}")

    return results


def _unwrap_ddg_url(url: str) -> str:
    """Unwrap DuckDuckGo redirect URLs."""
    if "uddg=" in url:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        return params.get("uddg", [url])[0]
    return url


def _search_with_multiple_queries(queries: list, domain_filter: str, max_results: int) -> list:
    """Run multiple search queries and filter for a specific domain."""
    results = []
    seen_urls = set()

    for query in queries:
        if len(results) >= max_results:
            break

        try:
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            response = requests.get(search_url, headers=get_headers(), timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                result_divs = soup.find_all("div", class_="result")

                for div in result_divs:
                    if len(results) >= max_results:
                        break

                    link = div.find("a", class_="result__a")
                    if not link:
                        continue

                    href = _unwrap_ddg_url(link.get("href", ""))
                    title = link.get_text(strip=True)

                    if not href or href in seen_urls:
                        continue

                    # Check if URL matches domain filter
                    if domain_filter not in href.lower():
                        continue

                    seen_urls.add(href)

                    snippet_elem = div.find("a", class_="result__snippet")
                    snippet = clean_text(snippet_elem.get_text(strip=True)) if snippet_elem else ""

                    results.append({
                        "title": clean_text(title),
                        "url": href,
                        "description": snippet,
                        "source": "search"
                    })

            rate_limit()

        except Exception as e:
            print(f"[Multi-Query Search Error] {e}")
            continue

    return results


def scrape_linkedin(query: str, max_results: int = 10) -> list:
    """
    Find LinkedIn profiles/groups/companies via search engine.
    """
    search_queries = [
        f'"{query}" site:linkedin.com',
        f"{query} site:linkedin.com/in",
        f"{query} linkedin profile",
        f"{query} linkedin company",
        f"{query} linkedin group",
    ]

    raw_results = _search_with_multiple_queries(search_queries, "linkedin.com", max_results * 2)

    linkedin_results = []
    seen_urls = set()

    for r in raw_results:
        url = r.get("url", "")

        if url in seen_urls:
            continue
        seen_urls.add(url)

        if "linkedin.com" in url.lower():
            # Determine type
            if "/in/" in url:
                r["type"] = "profile"
            elif "/company/" in url:
                r["type"] = "company"
            elif "/groups/" in url:
                r["type"] = "group"
            elif "/pulse/" in url or "/posts/" in url:
                r["type"] = "post"
            else:
                r["type"] = "page"

            r["source"] = "linkedin"
            linkedin_results.append(r)

            if len(linkedin_results) >= max_results:
                break

    return linkedin_results


def scrape_facebook(query: str, max_results: int = 10) -> list:
    """
    Find Facebook groups/pages via search engine.
    """
    search_queries = [
        f'"{query}" site:facebook.com',
        f"{query} facebook group",
        f"{query} facebook community",
        f"{query} site:facebook.com/groups",
        f"best {query} facebook groups",
    ]

    raw_results = _search_with_multiple_queries(search_queries, "facebook.com", max_results * 2)

    facebook_results = []
    seen_urls = set()

    for r in raw_results:
        url = r.get("url", "")

        if url in seen_urls:
            continue
        seen_urls.add(url)

        if "facebook.com" in url.lower():
            if "/groups/" in url:
                r["type"] = "group"
            elif "/events/" in url:
                r["type"] = "event"
            elif "/pages/" in url:
                r["type"] = "page"
            else:
                r["type"] = "page"

            r["source"] = "facebook"
            facebook_results.append(r)

            if len(facebook_results) >= max_results:
                break

    return facebook_results


def scrape_instagram(query: str, max_results: int = 10) -> list:
    """
    Find Instagram accounts/hashtags via search engine.
    """
    search_queries = [
        f'"{query}" site:instagram.com',
        f"{query} instagram account",
        f"{query} instagram profile",
        f"best {query} instagram accounts to follow",
        f"{query} hashtag instagram",
    ]

    raw_results = _search_with_multiple_queries(search_queries, "instagram.com", max_results * 2)

    instagram_results = []
    seen_urls = set()

    for r in raw_results:
        url = r.get("url", "")

        if url in seen_urls:
            continue
        seen_urls.add(url)

        if "instagram.com" in url.lower():
            parsed = urlparse(url)
            path_parts = [p for p in parsed.path.strip("/").split("/") if p]

            if path_parts:
                if path_parts[0] == "explore" and len(path_parts) > 2 and path_parts[1] == "tags":
                    r["type"] = "hashtag"
                    r["handle"] = f"#{path_parts[2]}"
                elif path_parts[0] in ["p", "reel", "reels"]:
                    r["type"] = "post"
                    r["handle"] = ""
                else:
                    r["type"] = "account"
                    r["handle"] = f"@{path_parts[0]}"
            else:
                r["type"] = "account"
                r["handle"] = ""

            r["source"] = "instagram"
            instagram_results.append(r)

            if len(instagram_results) >= max_results:
                break

    return instagram_results


def scrape_blogs(query: str, max_results: int = 10) -> list:
    """
    Find blog articles and tutorials via search engine.
    Excludes major social platforms to get actual blog content.
    """
    search_queries = [
        f"{query} tutorial blog guide",
        f"{query} complete guide",
        f"{query} how to learn",
        f"best {query} resources blog",
    ]

    results = []
    seen_urls = set()

    # Excluded domains
    excluded_domains = [
        "facebook.com", "instagram.com", "linkedin.com",
        "twitter.com", "x.com", "youtube.com", "reddit.com",
        "tiktok.com", "pinterest.com", "quora.com"
    ]

    for query_str in search_queries:
        if len(results) >= max_results:
            break

        try:
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query_str)}"
            response = requests.get(search_url, headers=get_headers(), timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                result_divs = soup.find_all("div", class_="result")

                for div in result_divs:
                    if len(results) >= max_results:
                        break

                    link = div.find("a", class_="result__a")
                    if not link:
                        continue

                    href = _unwrap_ddg_url(link.get("href", ""))
                    title = link.get_text(strip=True)

                    if not href or href in seen_urls:
                        continue

                    # Check if it's an excluded domain
                    parsed = urlparse(href)
                    domain = parsed.netloc.lower()

                    if any(excl in domain for excl in excluded_domains):
                        continue

                    seen_urls.add(href)

                    snippet_elem = div.find("a", class_="result__snippet")
                    snippet = clean_text(snippet_elem.get_text(strip=True)) if snippet_elem else ""

                    # Get site name
                    domain_parts = domain.replace("www.", "").split(".")
                    site_name = domain_parts[0] if domain_parts else "Unknown"

                    results.append({
                        "title": clean_text(title),
                        "url": href,
                        "description": snippet or f"Article about {query}",
                        "source": "blog",
                        "site": site_name,
                        "domain": domain
                    })

            rate_limit()

        except Exception as e:
            print(f"[Blog Search Error] {e}")
            continue

    return results
