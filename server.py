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

@app.post("/research")
def research(req: ResearchRequest):
    print(f"Received research request for topic: {req.topic}")
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
