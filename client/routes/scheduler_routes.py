from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse

from ..scheduler import (
    resume_scheduler,
    pause_scheduler,
    reschedule_job,
    get_scheduler_status,
    DEFAULT_SCRAPE_INTERVAL
)
from ..dependencies import get_current_user
from ..dependencies import db_manager

router = APIRouter(
    prefix="/api/scheduler",
    tags=["Scheduler"],
    dependencies=[Depends(get_current_user)] 
)

class ReschedulePayload(BaseModel):
    interval: int

@router.post("/start")
async def start_scraping_endpoint():
    """Endpoint to start/resume the scraping job."""
    try:
        resume_scheduler()
        return {"success": True, "message": "System started successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_scraping_endpoint():
    """Endpoint to stop/pause the scraping job."""
    try:
        pause_scheduler()
        return {"success": True, "message": "System stopped successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reschedule")
async def reschedule_endpoint(payload: ReschedulePayload):
    """Endpoint to change the scraping interval."""
    try:
        reschedule_job(payload.interval)
        db_manager.save_setting("scrape_interval", str(payload.interval))
        return {"success": True, "message": f"Rescheduled to every {payload.interval} minutes."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/interval")
async def get_interval_endpoint():
    """Endpoint to get the currently saved scraping interval."""
    try:
        interval = db_manager.get_setting("scrape_interval", str(DEFAULT_SCRAPE_INTERVAL))
        content = {"success": True, "data": {"interval": int(interval)}}
        return JSONResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def status_endpoint():
    """Endpoint to get the current status of the scheduler (running/paused)."""
    try:
        status = get_scheduler_status()
        return {"success": True, "data": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))