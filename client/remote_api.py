import requests
import json
import time
import logging
import os
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from contextlib import contextmanager
import threading
from dataclasses import dataclass
from .client_auth import SecureAuthManager
import dotenv

dotenv.load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ApiResponse:
    """Structured API response object."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    status_code: Optional[int] = None

class ApiClient:
    """Production-grade API client with connection pooling, retry logic, and security."""

    # This is the new, correct version
    def __init__(self, auth_manager: SecureAuthManager, base_url: str = os.getenv("SERVER_BASE_URL", "http://localhost:8000")):
        self.base_url = base_url.rstrip('/')
        self.session = self._create_session()
        self._lock = threading.Lock()
        self.auth_manager = auth_manager

    def _create_session(self) -> requests.Session:
        """Create optimized session with connection pooling and retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=5,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=20,
            pool_maxsize=50,
            pool_block=True
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'DealTracker-Client/3.0',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        })
        return session

    def set_auth_token(self, token: Optional[str]):
        """Securely sets or removes the Authorization header for the entire session."""
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
            logger.info("Authorization token has been set for the session.")
        elif "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
            logger.info("Authorization token has been removed from the session.")
    def refresh_tokens(self) -> bool:
        """
        Attempts to refresh the access token using the stored refresh token.
        This is a new method to handle the refresh logic.
        """
        logger.info("Access token may have expired. Attempting to refresh...")
        refresh_token = self.auth_manager.get_refresh_token()
        if not refresh_token:
            logger.error("No refresh token available. Cannot refresh session.")
            return False

        # Make a direct, non-intercepted request to the refresh endpoint
        url = urljoin(f"{self.base_url}/", 'users/refresh')
        try:
            response = self.session.post(url, json={"refresh_token": refresh_token}, timeout=15)
            response.raise_for_status()
            data = response.json()
            new_access_token = data.get('access_token')

            if not new_access_token:
                raise ValueError("Refresh response did not contain a new access token.")

            # Securely save the new token and update the session
            # Note: The server currently doesn't issue a new refresh token, so we reuse the old one.
            session_info = self.auth_manager.load_session()
            if session_info:
                self.auth_manager.save_session(
                    access_token=new_access_token,
                    refresh_token=session_info['refresh_token'],
                    user_data=session_info['user_data']
                )
                self.set_auth_token(new_access_token)
                logger.info("Token refresh successful. New access token is active.")
                return True
            return False
        except Exception as e:
            logger.error(f"Token refresh failed: {e}. Clearing session.")
            self.auth_manager.clear_session()
            return False

    # Replace the entire _make_request function with this new version

    def _make_request(self, method: str, endpoint: str, **kwargs) -> ApiResponse:
        """
        Thread-safe request handler with automatic token refresh and retry logic using a loop.
        """
        url = urljoin(f"{self.base_url}/", endpoint.lstrip('/'))

        # Loop allows for one initial attempt and one retry after a token refresh.
        for attempt in range(2):
            try:
                # We use the lock here to ensure the request is atomic.
                with self._lock:
                    response = self.session.request(method, url, timeout=30, **kwargs)
                    response.raise_for_status()

                if response.status_code == 204:
                    return ApiResponse(success=True, message="Operation completed", status_code=204)

                data = response.json() if response.content else {}
                return ApiResponse(success=True, data=data, status_code=response.status_code)

            except requests.exceptions.HTTPError as e:
                # Check for 401 Unauthorized on the FIRST attempt only
                if e.response.status_code == 401 and attempt == 0:
                    logger.warning("Caught 401 Unauthorized. Initiating token refresh.")
                    # The refresh_tokens function is thread-safe due to the outer lock
                    if self.refresh_tokens():
                        logger.info("Retrying the original request with the new token...")
                        continue  # Go to the next iteration of the loop to retry
                    else:
                        # If refresh fails, break the loop and handle the error
                        break
                
                # If it's not a 401, or it's the second attempt, handle as a final error
                error_msg = self._extract_error_message(e.response)
                logger.error(f"HTTP Error {e.response.status_code} for {url}: {error_msg}")
                return ApiResponse(success=False, message=error_msg, status_code=e.response.status_code)

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                logger.error(f"Connection error for {url}: {e}")
                return ApiResponse(success=False, message="Backend server unavailable.")
            except Exception as e:
                logger.error(f"An unexpected error occurred for {url}: {e}", exc_info=True)
                return ApiResponse(success=False, message=f"A system error occurred: {str(e)}")

        # This part is reached only if the refresh fails and the loop breaks
        return ApiResponse(success=False, message="Authentication failed after token refresh attempt.", status_code=401)

    def _extract_error_message(self, response) -> str:
        """Extract meaningful error message from response."""
        try:
            error_data = response.json()
            return error_data.get('detail', 'Unknown error')
        except:
            return response.text or f"HTTP {response.status_code} Error"

    # --- Authentication Methods ---
    def register_user(self, username: str, password: str) -> ApiResponse:
        """Register new user account."""
        return self._make_request('POST', 'users/', json={"username": username, "password": password})

    def login_user(self, username: str, password: str, device_fingerprint: str) -> ApiResponse:
        """Authenticate user and update the session with tokens."""
        response = self._make_request(
            'POST',
            'users/token',
            json={"username": username, "password": password, "device_fingerprint": device_fingerprint}
        )
        if response.success and response.data and response.data.get('access_token'):
            self.set_auth_token(response.data.get('access_token'))
            logger.info(f"User authenticated: {username}")
        return response

    def logout_user(self) -> ApiResponse:
        """Logout user and clear the authentication token."""
        # Clear the token from the session header first
        self.set_auth_token(None)
        logger.info("User logged out and local token cleared.")
        # This endpoint revokes all tokens on the server for the user
        return self._make_request('POST', 'users/logout-all')

    def get_current_user(self) -> ApiResponse:
        """Get current user information."""
        # No 'headers' argument needed, as the token is now part of the session
        return self._make_request('GET', 'users/me/')

    # --- Product Management Methods ---
    def get_products(self) -> ApiResponse:
        """Get user's tracked products."""
        return self._make_request('GET', 'products/me')

    def add_product(self, url: str, price_threshold: float) -> ApiResponse:
        """Add new product to track."""
        return self._make_request('POST', 'products/', json={"url": url, "price_threshold": price_threshold})

    def get_product(self, product_id: int) -> ApiResponse:
        """Get specific product details."""
        return self._make_request('GET', f'products/{product_id}')

    def delete_product(self, product_id: int) -> ApiResponse:
        """Delete tracked product."""
        return self._make_request('DELETE', f'products/{product_id}')

    def update_product(self, product_id: int, details: Dict[str, Any]) -> ApiResponse:
        """Updates a product's details on the remote server."""
        return self._make_request('PUT', f'products/{product_id}', json=details)

    # --- System Methods ---
    def health_check(self) -> ApiResponse:
        """Check backend health."""
        return self._make_request('GET', 'health')

    def get_api_info(self) -> ApiResponse:
        """Get API information."""
        return self._make_request('GET', 'info')

    def is_authenticated(self) -> bool:
        """Check if client is authenticated by seeing if the auth header is set."""
        return "Authorization" in self.session.headers