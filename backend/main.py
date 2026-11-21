
from contextlib import asynccontextmanager
from routes import ws as ws_routes
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import models
from corrections import models as corrections_models
from tris import models as tris_models
from config import settings
from database import Base, engine
from routes import auth as auth_routes
from routes import corrections as corrections_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="RecyMind", version="1.2", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_routes.router, prefix="/api/v1")
app.include_router(ws_routes.router, prefix="/api/v1")
app.include_router(corrections_routes.router, prefix="/api/v1")


@app.get("/api/v1/sante")
def sante():
    return {"etat": "ok"}
