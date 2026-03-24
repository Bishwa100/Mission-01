from celery import Celery
import os

from scrapers.youtube_scraper import scrape_youtube
from scrapers.universal_search_scraper import scrape_blogs, scrape_linkedin, scrape_facebook, scrape_instagram
from scrapers.reddit_scraper import scrape_reddit_communities
from scrapers.eventbrite_scraper import scrape_eventbrite
from scrapers.github_scraper import scrape_github_repos
from scrapers.twitter_scraper import scrape_twitter
from scrapers.quora_scraper import scrape_quora
from scrapers.blog_scraper import scrape_blog_articles
from llm import generate_search_queries, generate_deep_insights
from database import save_results

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_extended=True,
)


@celery_app.task(bind=True, name="scrape_topic")
def scrape_topic_task(self, topic: str, job_id: str):
    """
    Main task that orchestrates all scraping and LLM operations.
    """
    try:
        # Step 1: Generate search queries using LLM
        self.update_state(
            state="PROGRESS",
            meta={"step": "Local LLM generating queries...", "progress": 10}
        )
        q = generate_search_queries(topic)

        results = {}

        # Step 2: Scrape Video & Code platforms
        self.update_state(
            state="PROGRESS",
            meta={"step": "Scraping Video & Code...", "progress": 30}
        )
        results["youtube"] = scrape_youtube(q.get("youtube_query", topic))
        results["github"] = scrape_github_repos(q.get("github_query", topic))

        # Step 3: Scrape Social platforms via search engine
        self.update_state(
            state="PROGRESS",
            meta={"step": "Scraping Socials via Search Engine...", "progress": 45}
        )
        results["linkedin"] = scrape_linkedin(q.get("linkedin_query", f"{topic} linkedin"))
        results["facebook"] = scrape_facebook(q.get("facebook_query", f"{topic} facebook groups"))
        results["instagram"] = scrape_instagram(q.get("instagram_query", f"{topic} instagram"))

        # Step 4: Scrape Twitter/X and Quora
        self.update_state(
            state="PROGRESS",
            meta={"step": "Scraping Twitter & Quora...", "progress": 60}
        )
        results["twitter"] = scrape_twitter(q.get("twitter_query", f"{topic} expert tweets"))
        results["quora"] = scrape_quora(q.get("quora_query", f"{topic} questions answers"))

        # Step 5: Scrape Forums, Blogs & Events
        self.update_state(
            state="PROGRESS",
            meta={"step": "Scraping Blogs, Forums & Events...", "progress": 75}
        )
        results["blogs"] = scrape_blog_articles(q.get("blog_query", f"{topic} tutorial blog"))
        results["reddit"] = scrape_reddit_communities(q.get("reddit_query", topic))
        results["events"] = scrape_eventbrite(q.get("events_query", f"{topic} workshop"))

        # Step 6: Generate deep insights using LLM
        self.update_state(
            state="PROGRESS",
            meta={"step": "Local LLM generating deep insights...", "progress": 90}
        )
        insights = generate_deep_insights(topic, results)

        # Calculate totals
        counts = {k: len(v) for k, v in results.items()}

        final_data = {
            "topic": topic,
            "insights": insights,
            "results": results,
            "total_results": sum(counts.values()),
            "counts": counts
        }

        # Save to database
        save_results(job_id, topic, final_data)

        return final_data

    except Exception as e:
        print(f"[Task Error] {e}")
        # Return minimal data on error
        error_data = {
            "topic": topic,
            "insights": {
                "summary": f"An error occurred while researching {topic}. Please try again.",
                "trends": ["Unable to fetch trends"],
                "action_plan": ["Try searching again"]
            },
            "results": {},
            "total_results": 0,
            "error": str(e)
        }
        save_results(job_id, topic, error_data)
        return error_data
