import requests
from urllib.parse import quote_plus
from .utils import get_headers, rate_limit, clean_text


def scrape_github_repos(query: str, max_results: int = 10) -> list:
    """
    Scrape GitHub repositories using the public API.
    No authentication needed for basic search.
    """
    results = []

    try:
        # GitHub Search API
        search_url = f"https://api.github.com/search/repositories?q={quote_plus(query)}&sort=stars&order=desc&per_page={max_results}"

        headers = get_headers()
        headers["Accept"] = "application/vnd.github.v3+json"

        response = requests.get(search_url, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])

            for item in items:
                name = item.get("full_name", "")
                description = item.get("description", "")
                url = item.get("html_url", "")
                stars = item.get("stargazers_count", 0)
                language = item.get("language", "")
                forks = item.get("forks_count", 0)

                if name and url:
                    results.append({
                        "title": name,
                        "url": url,
                        "description": clean_text(description) or f"GitHub repository for {query}",
                        "source": "github",
                        "stars": stars,
                        "language": language,
                        "forks": forks,
                        "thumbnail": f"https://opengraph.githubassets.com/1/{name}"
                    })

        rate_limit()

    except Exception as e:
        print(f"[GitHub Scraper Error] {e}")

    # Fallback: get trending if search fails
    if not results:
        try:
            # Try scraping GitHub trending page
            from bs4 import BeautifulSoup
            trending_url = f"https://github.com/search?q={quote_plus(query)}&type=repositories"
            response = requests.get(trending_url, headers=get_headers(), timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                repo_links = soup.find_all("a", class_="v-align-middle")

                for link in repo_links[:max_results]:
                    href = link.get("href", "")
                    title = link.get_text(strip=True)

                    if href and title and "/" in href:
                        results.append({
                            "title": href.strip("/"),
                            "url": f"https://github.com{href}",
                            "description": f"GitHub repository related to {query}",
                            "source": "github"
                        })

            rate_limit()

        except Exception as e:
            print(f"[GitHub Fallback Error] {e}")

    return results[:max_results]
