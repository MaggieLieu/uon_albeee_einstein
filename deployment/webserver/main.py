# uvicorn main:app --host 0.0.0.0 --port 8963 --workers 8

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
import uvicorn

app = FastAPI(title="Einstein Web Interface")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve the Single Page Application (SPA) for all routes (client-side routing)"""
    return FileResponse("static/index.html")