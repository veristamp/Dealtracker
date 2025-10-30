# client/routes/activity_routes.py

import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from ..dependencies import db_manager, get_current_user
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/activity", tags=["Activity"])

@router.get("/", response_class=JSONResponse)
async def get_activity_feed(user: dict = Depends(get_current_user)):
    """
    Fetches the most recent activity logs from the local database.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        logs_data = db_manager.get_activity_logs(limit=30)
        return JSONResponse(content={"success": True, "data": logs_data})
    except Exception as e:
        logger.error(f"Failed to get activity logs: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Could not retrieve activity logs."}
        )