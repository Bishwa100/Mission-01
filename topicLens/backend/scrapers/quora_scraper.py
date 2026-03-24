"""
Quora Scraper using Universal Search Engine approach.
Extracts Q&A content, answers from experts, and topic spaces.
"""
import requests
from urllib.parse import quote_plus, urlparse
from bs4 import BeautifulSoup
from .utils import get_headers, rate_limit, clean_text


def scrape_quora(query: str, max_results: int = 15) -> list:
    """
    Scrape Quora Q&A content by searching DuckDuckGo.
    Returns questions, answers, and topic spaces related to the query.
    """
    results = []

    # Multiple search strategies
    search_queries = [
        f"{query} site:quora.com",
        f"what is {query} site:quora.com",
        f"how to {query} site:quora.com",
        f"best {query} quora answers",
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

                    # Filter for Quora URLs
                    if not href or href in seen_urls:
                        continue

                    parsed = urlparse(href)
                    if "quora.com" not in parsed.netloc:
                        continue

                    seen_urls.add(href)

                    # Get snippet/description
                    snippet_elem = link.find_next("a", class_="result__snippet")
                    snippet = ""
                    if snippet_elem:
                        snippet = clean_text(snippet_elem.get_text(strip=True))

                    # Determine content type from URL
                    content_type = "question"
                    if "/topic/" in href:
                        content_type = "topic"
                    elif "/profile/" in href:
                        content_type = "profile"
                    elif "/space/" in href or "/q/" in href:
                        content_type = "space"
                    elif "/answer/" in href:
                        content_type = "answer"

                    # Clean up title (remove "- Quora" suffix)
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
            print(f"[Quora Scraper Error] {e}")
            continue

    return results[:max_results]


def scrape_quora_topics(query: str, max_results: int = 10) -> list:
    """
    Find Quora topic spaces and communities for a subject.
    """
    results = []

    search_queries = [
        f"{query} topic site:quora.com/topic",
        f"{query} space site:quora.com",
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
                    if "quora.com" not in parsed.netloc:
                        continue

                    # Only include topic/space URLs
                    if "/topic/" not in href and "/space/" not in href:
                        continue

                    if href in seen_urls:
                        continue

                    seen_urls.add(href)

                    snippet_elem = link.find_next("a", class_="result__snippet")
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
    """
    Find Quora experts and top writers on a topic.
    """
    results = []

    search_queries = [
        f"{query} expert quora profile",
        f"{query} top writer site:quora.com/profile",
        f"best {query} answers quora",
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
                    if "quora.com" not in parsed.netloc:
                        continue

                    if href in seen_urls:
                        continue

                    seen_urls.add(href)

                    snippet_elem = link.find_next("a", class_="result__snippet")
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
