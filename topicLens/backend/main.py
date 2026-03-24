from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult
import uuid

from models import SearchRequest, SearchResponse, JobStatus
from database import init_db, create_job, get_job
from tasks import celery_app, scrape_topic_task

# Initialize FastAPI app
app = FastAPI(
    title="TopicLens API",
    description="Aggregate resources about any topic from across the internet",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "TopicLens API"}


@app.post("/api/search", response_model=SearchResponse)
async def start_search(request: SearchRequest):
    """
    Start a new topic search.
    Returns a job_id to poll for results.
    """
    if not request.topic or len(request.topic.strip()) < 2:
        raise HTTPException(status_code=400, detail="Topic must be at least 2 characters")

    topic = request.topic.strip()
    job_id = str(uuid.uuid4())

    # Create job in database
    create_job(job_id, topic)

    # Dispatch Celery task
    scrape_topic_task.apply_async(args=[topic, job_id], task_id=job_id)

    return SearchResponse(job_id=job_id, status="pending")


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """
    Get the status of a search job.
    Returns progress updates or final results.
    """
    # First check Celery task status
    task_result = AsyncResult(job_id, app=celery_app)

    if task_result.state == "PENDING":
        # Check if job exists in database
        db_job = get_job(job_id)
        if db_job:
            return {
                "id": job_id,
                "status": db_job["status"],
                "step": "Queued...",
                "progress": 0
            }
        raise HTTPException(status_code=404, detail="Job not found")

    elif task_result.state == "PROGRESS":
        meta = task_result.info or {}
        return {
            "id": job_id,
            "status": "progress",
            "step": meta.get("step", "Processing..."),
            "progress": meta.get("progress", 0)
        }

    elif task_result.state == "SUCCESS":
        result = task_result.result
        return {
            "id": job_id,
            "status": "done",
            "topic": result.get("topic", ""),
            "insights": result.get("insights", {}),
            "results": result.get("results", {}),
            "total_results": result.get("total_results", 0),
            "counts": result.get("counts", {})
        }

    elif task_result.state == "FAILURE":
        return {
            "id": job_id,
            "status": "error",
            "error": str(task_result.info)
        }

    else:
        return {
            "id": job_id,
            "status": task_result.state.lower(),
            "step": "Processing..."
        }


@app.get("/api/history")
async def get_history(limit: int = 10):
    """
    Get recent search history.
    """
    from database import SessionLocal, SearchJob

    db = SessionLocal()
    try:
        jobs = db.query(SearchJob).order_by(
            SearchJob.created_at.desc()
        ).limit(limit).all()

        return [
            {
                "id": job.id,
                "topic": job.topic,
                "status": job.status,
                "created_at": job.created_at.isoformat() if job.created_at else None
            }
            for job in jobs
        ]
    finally:
        db.close()
