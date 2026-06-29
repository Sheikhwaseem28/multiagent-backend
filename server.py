from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pipeline import run_research_pipeline, run_research_pipeline_stream

app = FastAPI()

# Enable CORS for frontend at localhost:5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, restrict this to the specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResearchRequest(BaseModel):
    topic: str
    depth: str = "standard"

@app.get("/usage")
def get_usage_status():
    from limit_manager import get_usage, LIMIT
    usage = get_usage()
    return {
        "searches": usage["searches"],
        "api_calls": usage["api_calls"],
        "limit": LIMIT,
        "reached": usage["searches"] >= LIMIT or usage["api_calls"] >= LIMIT
    }

@app.post("/research")
def research(req: ResearchRequest):
    print(f"Received research request for topic: {req.topic}")
    from fastapi import HTTPException
    from limit_manager import check_limit
    try:
        check_limit()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    result = run_research_pipeline(req.topic)
    return result

@app.get("/research/stream")
def research_stream(topic: str = Query(...), depth: str = Query("standard")):
    print(f"Received streaming research request for topic: {topic}")
    return StreamingResponse(
        run_research_pipeline_stream(topic),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
