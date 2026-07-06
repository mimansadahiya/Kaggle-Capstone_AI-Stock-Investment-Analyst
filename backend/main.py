import os
import json
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import our orchestrator
try:
    from backend.orchestrator import run_analysis
except ModuleNotFoundError:
    from orchestrator import run_analysis

# Load environment variables from .env file if it exists
load_dotenv()

app = FastAPI(title="AI Stock Research Assistant Backend")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/analyze")
async def analyze_stock(query: str = Query(..., description="The stock ticker or company name to analyze")):
    """
    Server-Sent Events (SSE) endpoint to stream real-time analysis logs and reports.
    """
    async def sse_generator():
        try:
            async for event in run_analysis(query):
                # SSE format requires prepending "data: " and ending with double newlines "\n\n"
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            error_event = {
                "type": "log",
                "agent": "System",
                "message": f"Fatal server error during analysis: {str(e)}"
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

# Resolve static files path for frontend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

# Mount the static files (frontend dashboard) to serve on the root URL
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    # If frontend folder is not created yet, we'll create a dummy route so the server doesn't crash on startup
    @app.get("/")
    def index():
        return {"status": "Backend running. Frontend folder not found."}

if __name__ == "__main__":
    import uvicorn
    # Automatically get port from env or default to 8000
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
