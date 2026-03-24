import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse
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

        for div in result_divs[:max_results]:
            try:
                # Title and URL
                title_link = div.find("a", class_="result__a")
                if not title_link:
                    continue

                title = clean_text(title_link.get_text())
                url = title_link.get("href", "")

                # Clean the URL (DuckDuckGo wraps URLs)
                if "uddg=" in url:
                    from urllib.parse import parse_qs, urlparse
                    parsed = urlparse(url)
                    params = parse_qs(parsed.query)
                    url = params.get("uddg", [url])[0]

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
            except Exception:
                continue

        rate_limit()

    except Exception as e:
        print(f"[DuckDuckGo Search Error] {e}")

    return results


def scrape_linkedin(query: str, max_results: int = 8) -> list:
    """
    Find LinkedIn profiles/groups via search engine.
    We search for "query site:linkedin.com" to get LinkedIn results safely.
    """
    search_query = f"{query} site:linkedin.com"
    results = search_duckduckgo(search_query, max_results)

    # Filter to only LinkedIn URLs and categorize
    linkedin_results = []
    for r in results:
        url = r.get("url", "")
        if "linkedin.com" in url:
            # Determine type
            if "/in/" in url:
                r["type"] = "profile"
            elif "/company/" in url:
                r["type"] = "company"
            elif "/groups/" in url:
                r["type"] = "group"
            else:
                r["type"] = "page"

            r["source"] = "linkedin"
            linkedin_results.append(r)

    return linkedin_results[:max_results]


def scrape_facebook(query: str, max_results: int = 8) -> list:
    """
    Find Facebook groups/pages via search engine.
    """
    search_query = f"{query} facebook groups site:facebook.com"
    results = search_duckduckgo(search_query, max_results)

    facebook_results = []
    for r in results:
        url = r.get("url", "")
        if "facebook.com" in url:
            if "/groups/" in url:
                r["type"] = "group"
            elif "/pages/" in url or not any(x in url for x in ["/groups/", "/events/", "/marketplace/"]):
                r["type"] = "page"
            else:
                r["type"] = "other"

            r["source"] = "facebook"
            facebook_results.append(r)

    return facebook_results[:max_results]


def scrape_instagram(query: str, max_results: int = 8) -> list:
    """
    Find Instagram accounts/hashtags via search engine.
    """
    search_query = f"{query} instagram accounts site:instagram.com"
    results = search_duckduckgo(search_query, max_results)

    instagram_results = []
    for r in results:
        url = r.get("url", "")
        if "instagram.com" in url:
            # Try to identify the handle
            parsed = urlparse(url)
            path_parts = [p for p in parsed.path.split("/") if p]

            if path_parts:
                if path_parts[0] == "explore" and len(path_parts) > 2:
                    r["type"] = "hashtag"
                    r["handle"] = f"#{path_parts[2]}" if path_parts[1] == "tags" else path_parts[0]
                else:
                    r["type"] = "account"
                    r["handle"] = f"@{path_parts[0]}"

            r["source"] = "instagram"
            instagram_results.append(r)

    return instagram_results[:max_results]


def scrape_blogs(query: str, max_results: int = 10) -> list:
    """
    Find blog articles and tutorials via search engine.
    Excludes major social platforms to get actual blog content.
    """
    search_query = f"{query} tutorial blog guide"
    results = search_duckduckgo(search_query, max_results * 2)

    # Filter out social media sites
    excluded_domains = [
        "facebook.com", "instagram.com", "linkedin.com",
        "twitter.com", "x.com", "youtube.com", "reddit.com",
        "tiktok.com", "pinterest.com"
    ]

    blog_results = []
    for r in results:
        url = r.get("url", "")
        domain = urlparse(url).netloc.lower()

        if not any(excluded in domain for excluded in excluded_domains):
            r["source"] = "blog"

            # Try to identify the site name
            domain_parts = domain.replace("www.", "").split(".")
            r["site"] = domain_parts[0] if domain_parts else "Unknown"

            blog_results.append(r)

            if len(blog_results) >= max_results:
                break

    return blog_results
