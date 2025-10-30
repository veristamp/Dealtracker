import datetime
import json
import logging
import re
from typing import Any, Dict, List, Optional

from crawl4ai import (AsyncWebCrawler, BrowserConfig, CacheMode,
                        CrawlerRunConfig, JsonCssExtractionStrategy,
                        MemoryAdaptiveDispatcher, RateLimiter)
from .dependencies import db_manager
from .realtime.alert_sse import sse_manager


logger = logging.getLogger(__name__)
EXTRACTION_SCHEMA = {
    "name": "ProductPrice",
    "baseSelector": "div.pdp-description-container",
    "fields": [
        {"name": "price", "selector": "span.pdp-price > strong", "type": "text"},
        {"name": "product_name_suffix", "selector": "h1.pdp-name", "type": "text"},
        {"name": "brand", "selector": "h1.pdp-title", "type": "text"}
    ]
}

def clean_price(price_str: Optional[str]) -> Optional[float]:
    """Removes currency symbols and converts price string to float."""
    if not price_str:
        return None
    price_digits = re.findall(r'[\d.]+', price_str)
    if not price_digits:
        return None
    return float("".join(price_digits))


class ProductScraper:
    """Handles the entire scraping lifecycle for a given list of products."""

    def __init__(self):
        self.browser_config = BrowserConfig(headless=True, user_agent_mode="random")
        self.run_config = CrawlerRunConfig(
            override_navigator=True,
            magic=True,
            simulate_user=True,
            page_timeout=45000,
            wait_for="css:span.pdp-price > strong",
            extraction_strategy=JsonCssExtractionStrategy(schema=EXTRACTION_SCHEMA),
            stream=True,
            cache_mode=CacheMode.BYPASS
        )
        self.dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=80.0,
            max_session_permit=10,
            rate_limiter=RateLimiter(base_delay=(1.5, 3.5), max_retries=2),
        )

    async def run_scraping_cycle(self, products_to_scrape: List[Dict[str, Any]]):
        """Runs the scraping process for a provided list of active products."""
        logger.info(f"🚀 Starting new scraping cycle for {len(products_to_scrape)} products...")

        if not products_to_scrape:
            logger.info("No products provided to scrape. Cycle finished.")
            return
        urls = [p['url'] for p in products_to_scrape]
        url_to_product_map = {p['url']: p for p in products_to_scrape}

        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            async for result in await crawler.arun_many(
                urls=urls,
                config=self.run_config,
                dispatcher=self.dispatcher
            ):
                product = url_to_product_map.get(result.url)
                if not product:
                    continue

                if result.success and result.extracted_content:
                    await self._process_successful_scrape(result, product)
                else:
                    await self._process_failed_scrape(result, product)

        logger.info("✅ Scraping cycle complete.")
    
    async def _process_successful_scrape(self, result, product: Dict[str, Any]):
        """Processes a successful scrape, updates the database, and creates alerts."""
        try:
            data = json.loads(result.extracted_content)
            if not data:
                raise ValueError("Extracted content is empty.")

            info = data[0]
            scraped_price = clean_price(info.get("price"))
            product_name = f"{info.get('brand', '')} {info.get('product_name_suffix', '')}".strip()

            if scraped_price is None:
                raise ValueError("Price could not be extracted or cleaned.")

            db_manager.add_price_history_entry(product['product_id'], scraped_price)
            
            db_manager.update_product_details(
                product_id=product['product_id'],
                details={
                    "current_price": scraped_price,
                    "name": product_name,
                    "last_scrape_status": "success"
                }
            )

            if scraped_price < product['threshold_price']:
                logger.info(f"🎉 Price drop for '{product_name}'! New: ₹{scraped_price}, Target: ₹{product['threshold_price']}")
                db_manager.add_alert(
                    product_id=product['product_id'],
                    product_name=product_name,
                    scraped_price=scraped_price,
                    threshold_price=product['threshold_price']
                )
                
                alert_event = {
                    "type": "price_drop",
                    "data": {
                        "product_name": product_name,
                        "scraped_price": scraped_price,
                        "threshold_price": product['threshold_price'],
                        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
                    }
                }
                await sse_manager.broadcast(alert_event)

        except (json.JSONDecodeError, IndexError, ValueError, Exception) as e:
            logger.error(f"Error processing result for {result.url}: {e}")
            await self._process_failed_scrape(result, product, str(e))
            
    async def _process_failed_scrape(self, result, product: Dict[str, Any], error: str = None):
        """Logs a failed scrape and updates the product status in the database."""
        error_message = error or result.error_message or "Unknown crawl failure"
        logger.warning(f"❌ Failed to scrape {result.url}: {error_message}")

        db_manager.update_product_details(
            product_id=product['product_id'],
            details={"last_scrape_status": "failed"}
        )