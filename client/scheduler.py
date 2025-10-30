import logging
import requests 
from apscheduler.schedulers.background import BackgroundScheduler
from concurrent.futures import ThreadPoolExecutor
from .dependencies import db_manager

logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=2)
scheduler = BackgroundScheduler(daemon=True, executor=executor)
DEFAULT_SCRAPE_INTERVAL = 10
INTERNAL_TRIGGER_URL = "http://127.0.0.1:8001/internal/trigger-scrape"

def run_scheduled_task():
    """
    This function is executed by the scheduler. It simply makes an
    HTTP request to the internal trigger endpoint.
    """
    try:
        logger.info("Scheduler is triggering the internal scrape endpoint...")
        response = requests.post(INTERNAL_TRIGGER_URL, timeout=10)
        response.raise_for_status()
        logger.info(f"Scrape triggered successfully: {response.json().get('message')}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to trigger internal scrape endpoint: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the scheduler task: {e}", exc_info=True)


def initialize_scheduler():
    """Adds all background jobs to the scheduler and starts it."""
    try:
        interval_minutes = int(db_manager.get_setting("scrape_interval", DEFAULT_SCRAPE_INTERVAL))
    except (ValueError, TypeError):
        interval_minutes = DEFAULT_SCRAPE_INTERVAL

    logger.info(f"Initializing scheduler to run every {interval_minutes} minutes.")
    if not scheduler.get_job('scraping_job'):
        scheduler.add_job(run_scheduled_task, 'interval', minutes=interval_minutes, id='scraping_job')

    if not scheduler.running:
        scheduler.start(paused=True)
        logger.info("Scheduler started in a PAUSED state. Waiting for UI command.")

def resume_scheduler():
    if scheduler.running:
        scheduler.resume()
        logger.info("Scheduler has been RESUMED.")
        executor.submit(run_scheduled_task)


def pause_scheduler():
    if scheduler.running:
        scheduler.pause()
        logger.info("Scheduler has been PAUSED.")


def reschedule_job(minutes: int):
    if scheduler.running and scheduler.get_job('scraping_job'):
        scheduler.reschedule_job('scraping_job', trigger='interval', minutes=minutes)
        logger.info(f"Scraping job rescheduled to run every {minutes} minutes.")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler has been shut down.")
    executor.shutdown(wait=False)
    logger.info("Thread executor has been shut down.")


def get_scheduler_status() -> dict:
    is_active = scheduler.running and getattr(scheduler, 'state', 0) != 2
    return {"running": is_active}