from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from auth.deps import user_from_token
from database import SessionLocal
from ws_manager import manager

router = APIRouter()


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket, token: str | None = Query(None)):
    """ws://localhost:8000/api/v1/ws?token=<access_token> (contrat 4.5).
    Le jeton est verifie AVANT d'accepter la connexion. Le compte simulateur n'a pas acces au WebSocket."""
    db = SessionLocal()
    try:
        user = user_from_token(token, db) if token else None
    finally:
        db.close()
    if user is None or user.role not in ("operator", "admin"):
        await websocket.close(code=1008)
        return
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
