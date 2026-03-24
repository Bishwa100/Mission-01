import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, rate_limit, clean_text


def scrape_youtube(query: str, max_results: int = 10) -> list:
    """
    Scrape YouTube search results via HTML parsing.
    Returns list of video info dicts.
    """
    results = []
    try:
        search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        response = requests.get(search_url, headers=get_headers(), timeout=15)

        if response.status_code != 200:
            return results

        # YouTube embeds data in script tags as JSON
        html = response.text

        # Find video IDs and titles from the page
        soup = BeautifulSoup(html, "lxml")

        # Extract from script containing ytInitialData
        import re
        import json

        pattern = r'var ytInitialData = ({.*?});'
        match = re.search(pattern, html)

        if match:
            try:
                data = json.loads(match.group(1))
                contents = data.get("contents", {}).get("twoColumnSearchResultsRenderer", {}).get("primaryContents", {}).get("sectionListRenderer", {}).get("contents", [])

                for section in contents:
                    items = section.get("itemSectionRenderer", {}).get("contents", [])
                    for item in items:
                        video = item.get("videoRenderer", {})
                        if video:
                            video_id = video.get("videoId", "")
                            title = video.get("title", {}).get("runs", [{}])[0].get("text", "")
                            channel = video.get("ownerText", {}).get("runs", [{}])[0].get("text", "")
                            description_snippets = video.get("detailedMetadataSnippets", [])
                            description = ""
                            if description_snippets:
                                desc_runs = description_snippets[0].get("snippetText", {}).get("runs", [])
                                description = "".join([r.get("text", "") for r in desc_runs])

                            if video_id and title:
                                results.append({
                                    "title": clean_text(title),
                                    "url": f"https://www.youtube.com/watch?v={video_id}",
                                    "description": clean_text(description) or f"Video by {channel}",
                                    "thumbnail": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
                                    "source": "youtube",
                                    "channel": channel
                                })

                            if len(results) >= max_results:
                                break
                    if len(results) >= max_results:
                        break
            except json.JSONDecodeError:
                pass

        # Fallback: parse links directly
        if not results:
            links = soup.find_all("a", href=True)
            for link in links:
                href = link.get("href", "")
                if "/watch?v=" in href:
                    video_id = href.split("v=")[1].split("&")[0] if "v=" in href else ""
                    title = link.get("title", "") or link.get_text(strip=True)
                    if video_id and title and len(title) > 5:
                        results.append({
                            "title": clean_text(title),
                            "url": f"https://www.youtube.com/watch?v={video_id}",
                            "description": f"YouTube video about {query}",
                            "thumbnail": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
                            "source": "youtube"
                        })
                        if len(results) >= max_results:
                            break

        rate_limit()

    except Exception as e:
        print(f"[YouTube Scraper Error] {e}")

    return results[:max_results]
