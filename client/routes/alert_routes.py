# client/routes/alert_routes.py

import logging
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from ..dependencies import db_manager, get_current_user
from ..realtime.alert_sse import sse_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

WS_SECRET_TOKEN = "idontthinkyoucancrackthiseverinlife:)haha"

@router.get("/stream")
async def alerts_sse_stream(request: Request, token: str = Query(...)):
    """Handles a single client's SSE connection, waiting for pushed events."""
    if token != WS_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid authentication token for SSE.")

    queue = sse_manager.add_client()

    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'system', 'data': 'Connection established.'})}\n\n"
            while True:
                message = await queue.get()
                if await request.is_disconnected():
                    break
                yield message
        except asyncio.CancelledError:
            logger.info("Client disconnected.")
        finally:
            sse_manager.remove_client(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/", response_class=JSONResponse)
async def get_all_alerts(user: dict = Depends(get_current_user)):
    """This endpoint remains for fetching the list of existing alerts on page load."""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        alerts_data = db_manager.get_alerts(limit=50)
        return JSONResponse(content={"success": True, "data": alerts_data})
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve alerts.")