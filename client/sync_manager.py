import logging
from .client_auth import SecureAuthManager
from .database import DatabaseManager
from .remote_api import ApiClient

logger = logging.getLogger(__name__)

class SyncManager:
    def __init__(self, auth_manager: SecureAuthManager, api_client: ApiClient, db_manager: DatabaseManager):
        self.auth_manager = auth_manager
        self.api_client = api_client
        self.db_manager = db_manager
        self.is_syncing = False

    async def verify_session_with_server(self) -> bool:
        if not self.auth_manager.is_authenticated():
            return False

        self.api_client.set_auth_token(self.auth_manager.get_access_token())
        user_response = self.api_client.get_current_user()

        if user_response.success and user_response.data and user_response.data.get('is_active'):
            logger.info("Session verified successfully with server.")
            return True
        else:
            logger.warning(f"Session verification failed: {user_response.message}. Clearing local session.")
            self.auth_manager.clear_session()
            self.api_client.set_auth_token(None)
            return False

    async def sync_products(self) -> bool:
        if self.is_syncing:
            return True

        if not await self.verify_session_with_server():
            return False

        self.is_syncing = True
        logger.info("🚀 Starting full product sync...")
        try:
            response = self.api_client.get_products()
            if not response.success or not isinstance(response.data, list):
                logger.error(f"Sync failed: Could not get products from server. Reason: {response.message}")
                return False
            
            vps_products = response.data
            vps_product_ids = {p['id'] for p in vps_products}
            local_products = self.db_manager.get_cached_products()
            local_product_ids = {p['product_id'] for p in local_products}
            ids_to_delete = list(local_product_ids - vps_product_ids)
            if ids_to_delete:
                for product_id in ids_to_delete:
                    self.db_manager.delete_alerts_for_product(product_id)
                self.db_manager.delete_products_by_id(ids_to_delete)
            for product_data in vps_products:
                self.db_manager.cache_product(product_data)

            logger.info("✅ Full product sync completed successfully.")
            return True
        except Exception as e:
            logger.error(f"An unexpected error occurred during sync: {e}", exc_info=True)
            return False
        finally:
            self.is_syncing = False