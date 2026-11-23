from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routes import tris, stats, ws, test_dev, simulation
app = FastAPI(title="RecyMind API (test local)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)
IMAGES = Path(__file__).parent / "images"
IMAGES.mkdir(exist_ok=True)
app.mount("/images", StaticFiles(directory=IMAGES), name="images")
app.include_router(tris.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")
app.include_router(ws.router, prefix="/api/v1")
app.include_router(test_dev.router, prefix="/api/v1")
app.include_router(simulation.router, prefix="/api/v1")