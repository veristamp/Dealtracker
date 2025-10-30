# client/routes/internal_routes.py (Corrected)

import logging
import asyncio
import platform
from fastapi import APIRouter, BackgroundTasks

from ..scraper import ProductScraper
from ..dependencies import db_manager, sync_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/internal", tags=["Internal"], include_in_schema=False)

def run_the_scrape():
    """
    Executes the scraping logic in an isolated event loop, ensuring the user is
    still active and authenticated on the server before proceeding.
    """
    async def inner_scrape():
        try:
            logger.info("Verifying session with server before scraping...")
            is_session_valid = await sync_manager.verify_session_with_server()

            if not is_session_valid:
                logger.warning("Aborting scrape cycle: User session is no longer valid or active.")
                return

            active_products = db_manager.get_cached_products(active_only=True)
            if not active_products:
                logger.info("No active products to scrape. Task finished.")
                return

            logger.info("Session is valid. Starting internal scrape task.")
            product_scraper = ProductScraper()
            await product_scraper.run_scraping_cycle(active_products)
            logger.info("Internal scrape task completed successfully.")
            
        except Exception as e:
            logger.error(f"An error occurred during the internal scraping task: {e}", exc_info=True)

    if platform.system() == "Windows":
        policy = asyncio.WindowsProactorEventLoopPolicy()
        asyncio.set_event_loop_policy(policy)
    
    try:
        asyncio.run(inner_scrape())
    except Exception as e:
        logger.error(f"Failed to run the async scraping loop: {e}")

@router.post("/trigger-scrape")
async def trigger_scrape_endpoint(background_tasks: BackgroundTasks):
    """
    An internal-only endpoint that the scheduler will call.
    It runs the scrape as a background task to avoid tying up the scheduler's request.
    """
    background_tasks.add_task(run_the_scrape)
    return {"success": True, "message": "Scraping cycle triggered in the background."}