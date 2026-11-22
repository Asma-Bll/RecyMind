
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from auth import models
from corrections import models as corrections_models
from tris import models as tris_models
from routes import ia as ia_routes
from config import settings
from database import Base, engine
from routes import auth as auth_routes
from routes import corrections as corrections_routes
from routes import ws as ws_routes
from routes import tris as tris_routes



@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


logger = logging.getLogger("recymind")
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
app.include_router(tris_routes.router, prefix="/api/v1")
app.include_router(ia_routes.router, prefix="/api/v1")


@app.get("/api/v1/sante")
def sante():
    return {"etat": "ok"}


@app.exception_handler(RequestValidationError)
async def erreur_validation(request: Request, exc: RequestValidationError):
    detail = [
        {"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]}
        for e in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": detail})


@app.exception_handler(Exception)
async def erreur_interne(request: Request, exc: Exception):
    logger.exception(
        "Erreur interne sur %s %s", request.method, request.url.path
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Erreur interne du serveur."},
    )
