from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import models  # noqa: F401  (enregistre la table utilisateurs)
from config import settings
from database import Base, engine
from routes import auth as auth_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="RecyMind", version="1.2", lifespan=lifespan)

# CORS : origines limitees au frontend (contrat v1.2, section 2.4)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_routes.router, prefix="/api/v1")


@app.get("/api/v1/sante")
def sante():
    return {"etat": "ok"}
