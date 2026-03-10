"""FastAPI application — video upload, analysis, and dashboard."""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiofiles
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import (
    APP_HOST,
    APP_PORT,
    INFERENCE_PROVIDER,
    INSTAGRAM_CREATORS,
    MAX_VIDEO_SIZE_MB,
    RESULTS_DIR,
    VIDEOS_DIR,
)
from server.video_processor import extract_frames, frames_to_base64, get_video_metadata
from server.inference_client import analyze_video_frames, check_health

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Instagram Reel Analyzer", version="1.0.0")

# Mount static files and templates
BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# ── Health ───────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    inference_status = await check_health()
    return {"app": "ok", "inference": inference_status}


# ── Dashboard ────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    results = _load_all_results()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "creators": INSTAGRAM_CREATORS,
        "results": results,
        "stats": _compute_stats(results),
    })


# ── Upload & Analyze ─────────────────────────────────────────────────
@app.post("/api/analyze")
async def analyze_video(file: UploadFile = File(...)):
    """Upload a video and run Qwen3-VL analysis."""
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
        raise HTTPException(400, f"Unsupported format: {ext}")

    # Save uploaded video
    video_id = str(uuid.uuid4())[:8]
    save_path = VIDEOS_DIR / f"{video_id}{ext}"
    content = await file.read()

    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_VIDEO_SIZE_MB:
        raise HTTPException(413, f"File too large ({size_mb:.1f}MB). Max: {MAX_VIDEO_SIZE_MB}MB")

    async with aiofiles.open(save_path, "wb") as f:
        await f.write(content)

    logger.info("Saved video %s (%.1f MB)", save_path.name, size_mb)

    # Process
    try:
        metadata = get_video_metadata(save_path)
        frames = extract_frames(save_path)
        base64_frames = frames_to_base64(frames)
        result = await analyze_video_frames(base64_frames)
    except Exception as e:
        logger.exception("Analysis failed for %s", save_path.name)
        raise HTTPException(500, f"Analysis failed: {e}")

    # Persist result
    record = {
        "video_id": video_id,
        "filename": file.filename,
        "metadata": metadata,
        "analysis": result.get("analysis"),
        "raw_response": result.get("raw"),
        "status": result["status"],
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }
    result_path = RESULTS_DIR / f"{video_id}.json"
    async with aiofiles.open(result_path, "w") as f:
        await f.write(json.dumps(record, indent=2))

    return JSONResponse(record)


# ── Results API ──────────────────────────────────────────────────────
@app.get("/api/results")
async def list_results():
    return _load_all_results()


@app.get("/api/results/{video_id}")
async def get_result(video_id: str):
    path = RESULTS_DIR / f"{video_id}.json"
    if not path.exists():
        raise HTTPException(404, "Result not found")
    return json.loads(path.read_text())


@app.get("/api/creators")
async def list_creators():
    return INSTAGRAM_CREATORS


@app.get("/api/stats")
async def get_stats():
    results = _load_all_results()
    return _compute_stats(results)


# ── Helpers ──────────────────────────────────────────────────────────
def _load_all_results() -> list[dict]:
    results = []
    for p in sorted(RESULTS_DIR.glob("*.json"), reverse=True):
        try:
            results.append(json.loads(p.read_text()))
        except Exception:
            continue
    return results


def _compute_stats(results: list[dict]) -> dict:
    if not results:
        return {
            "total_analyzed": 0,
            "avg_virality": 0,
            "top_hooks": [],
            "top_emotions": [],
            "format_distribution": {},
        }

    analyses = [r["analysis"] for r in results if r.get("analysis")]
    total = len(analyses)
    if total == 0:
        return {
            "total_analyzed": len(results),
            "avg_virality": 0,
            "top_hooks": [],
            "top_emotions": [],
            "format_distribution": {},
        }

    avg_virality = sum(a.get("virality_score", 0) for a in analyses) / total

    hooks: dict[str, int] = {}
    emotions: dict[str, int] = {}
    formats: dict[str, int] = {}
    for a in analyses:
        h = a.get("hook_type", "unknown")
        hooks[h] = hooks.get(h, 0) + 1
        e = a.get("emotional_trigger", "unknown")
        emotions[e] = emotions.get(e, 0) + 1
        f = a.get("content_format", "unknown")
        formats[f] = formats.get(f, 0) + 1

    return {
        "total_analyzed": total,
        "avg_virality": round(avg_virality, 1),
        "top_hooks": sorted(hooks.items(), key=lambda x: x[1], reverse=True)[:5],
        "top_emotions": sorted(emotions.items(), key=lambda x: x[1], reverse=True)[:5],
        "format_distribution": formats,
    }


def main():
    import uvicorn
    uvicorn.run("server.app:app", host=APP_HOST, port=APP_PORT, reload=True)


if __name__ == "__main__":
    main()
