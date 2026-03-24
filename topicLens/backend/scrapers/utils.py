import requests
import time
import random
from fake_useragent import UserAgent

ua = UserAgent()


def get_headers() -> dict:
    """Generate random browser headers to avoid detection."""
    return {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def rate_limit(min_delay: float = 0.5, max_delay: float = 2.0):
    """Add random delay between requests to avoid rate limiting."""
    time.sleep(random.uniform(min_delay, max_delay))


def safe_request(url: str, timeout: int = 10) -> requests.Response | None:
    """Make a safe HTTP request with error handling."""
    try:
        response = requests.get(url, headers=get_headers(), timeout=timeout)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"[Request Error] {url}: {e}")
        return None


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    if not text:
        return ""
    return " ".join(text.split()).strip()
