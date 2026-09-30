"""WebSocket endpoint for real-time dashboard events.

Authenticates administrators via JWT token passed as a query parameter,
then streams real-time events to the connected dashboard.
"""

import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_access_token
from app.realtime.broadcaster import broadcaster

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(default=""),
) -> None:
    """Authenticated WebSocket for real-time dashboard updates.

    Connect with: ws://host:port/api/v1/ws?token=<JWT>
    """
    # Authenticate
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return

    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    username = payload.get("sub")
    if not username:
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    # Authorized — connect
    await broadcaster.connect(websocket)
    logger.info("WebSocket authenticated for user: %s", username)

    try:
        while True:
            # Keep connection alive; handle any incoming messages
            data = await websocket.receive_text()
            # Clients may send ping/pong or acknowledgements
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("WebSocket error: %s", exc)
    finally:
        await broadcaster.disconnect(websocket)
