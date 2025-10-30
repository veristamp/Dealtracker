from fastapi import Request, HTTPException

from .client_auth import SecureAuthManager
from .database import DatabaseManager
from .remote_api import ApiClient
from .sync_manager import SyncManager

# --- Create single, shared instances for the entire application ---
auth_manager = SecureAuthManager()
db_manager = DatabaseManager()
api_client = ApiClient(auth_manager=auth_manager)
sync_manager = SyncManager(auth_manager, api_client, db_manager)

class ActivityLogger:
    def log(self, action_type: str, details: dict = None):
        """A simple wrapper to call the db_manager method."""
        try:
            db_manager.add_activity_log(action_type, details)
        except Exception as e:
            print(f"Failed to log activity: {e}")

activity_logger = ActivityLogger()


# --- Authentication Dependency Functions ---
async def get_current_user(request: Request):
    """
    Dependency for API routes. Raises an exception if the user is not authenticated.
    """
    if not auth_manager.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = auth_manager.get_session_info()
    if not session or 'user_data' not in session:
        raise HTTPException(status_code=401, detail="Invalid session")
        
    return session.get('user_data')

async def get_current_user_for_page(request: Request):
    """
    Dependency for web pages. Returns None if the user is not authenticated, 
    allowing the page to render a login form.
    """
    if not auth_manager.is_authenticated():
        return None
    session = auth_manager.get_session_info()
    return session.get('user_data') if session else None