from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
clients = set()


async def diffuser(message):
    """Envoie un message à tous les clients WebSocket connectés."""
    for c in list(clients):
        try:
            await c.send_json(message)
        except Exception:
            clients.discard(c)


@router.websocket("/ws")
async def ws(websocket: WebSocket):
    # La vérification du jeton sera ajoutée plus tard
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()   # garde la connexion ouverte
    except WebSocketDisconnect:
        pass
    finally:
        clients.discard(websocket)