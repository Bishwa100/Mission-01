import httpx
import json
import os

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "sorc/qwen3.5-claude-4.6-opus")


def call_ollama(prompt: str, temperature: float = 0.3) -> str:
    """Call the local Ollama instance."""
    try:
        resp = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_ctx": 4096}
            },
            timeout=120.0
        )
        return resp.json().get("response", "").strip()
    except Exception as e:
        print(f"[Ollama Error] {e}")
        return ""


def generate_search_queries(topic: str) -> dict:
    prompt = f"""Generate search engine queries to find info about "{topic}".
Return ONLY a valid JSON object:
{{
  "youtube_query": "best {topic} tutorials beginners",
  "linkedin_query": "{topic} linkedin profiles and groups",
  "facebook_query": "{topic} facebook groups",
  "instagram_query": "{topic} instagram accounts",
  "blog_query": "{topic} best blog tutorial",
  "reddit_query": "{topic}",
  "events_query": "{topic} workshop webinar",
  "github_query": "{topic}"
}}"""
    response = call_ollama(prompt, temperature=0.1)
    try:
        return json.loads(response[response.find("{"):response.rfind("}") + 1])
    except:
        t = topic.lower()
        return {k: f"{t} {k.split('_')[0]}" for k in [
            "youtube_query", "linkedin_query", "facebook_query",
            "instagram_query", "blog_query", "reddit_query",
            "events_query", "github_query"
        ]}


def generate_deep_insights(topic: str, results: dict) -> dict:
    """
    Feeds a sample of the scraped titles/descriptions to the LLM
    to generate a rich, multi-part intelligence report.
    """
    sample_context = []
    for cat, items in results.items():
        for item in items[:3]:
            sample_context.append(
                f"- {item.get('title', '')}: {item.get('description', '')[:100]}"
            )

    context_str = "\n".join(sample_context)[:2000]

    prompt = f"""You are a senior research analyst. Based on the topic "{topic}" and the following scraped web data, generate a deep insight report.

Scraped Data Context:
{context_str}

Return ONLY a valid JSON object with the following structure:
{{
  "summary": "A 2-sentence executive summary of what this topic is and why it matters today.",
  "trends": ["Trend 1 based on data", "Trend 2 based on data", "Trend 3 based on data"],
  "action_plan": ["Step 1 to start learning/engaging", "Step 2", "Step 3"]
}}
"""
    response = call_ollama(prompt, temperature=0.4)
    try:
        return json.loads(response[response.find("{"):response.rfind("}") + 1])
    except:
        return {
            "summary": f"Explore everything about {topic}. We've aggregated the best resources across the web.",
            "trends": [
                "Community growth",
                "Increasing open-source tools",
                "High demand for tutorials"
            ],
            "action_plan": [
                "Watch the top YouTube videos",
                "Join a Reddit community",
                "Follow GitHub repos"
            ]
        }
