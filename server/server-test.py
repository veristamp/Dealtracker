# server-test.py
import requests
import hashlib
import uuid
import time
import os
import psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse
from typing import Optional

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000"

# --- Database Helper Functions ---
def get_db_connection() -> Optional[psycopg2.extensions.connection]:
    dotenv_path = os.path.join(os.path.dirname(__file__), 'server', '.env')
    load_dotenv(dotenv_path=dotenv_path, override=True)
    database_url = os.getenv("DATABASE_URL")
    if not database_url: raise ValueError("DATABASE_URL not found in .env file.")
    try:
        result = urlparse(database_url)
        return psycopg2.connect(
            dbname=result.path[1:], user=result.username, password=result.password,
            host=result.hostname, port=result.port
        )
    except Exception as e:
        print(f"[DB_ERROR] Could not connect to the database: {e}")
        return None

def db_execute(query, params=None, fetch=None):
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if fetch == 'one': return cur.fetchone()
            if fetch == 'all': return cur.fetchall()
            conn.commit()
    except Exception as e:
        print(f"  [!] DB Error during execute: {e}")
    finally:
        if conn: conn.close()

def cleanup_users(usernames):
    print(f"\n--- [AUTO] Cleaning up test users: {usernames} ---")
    for username in usernames:
        user = db_execute("SELECT id FROM users WHERE username = %s", (username,), fetch='one')
        if user:
            user_id = user[0]
            db_execute("DELETE FROM refresh_tokens WHERE user_id = %s", (user_id,))
            db_execute("DELETE FROM tracked_products WHERE owner_id = %s", (user_id,))
            db_execute("DELETE FROM users WHERE id = %s", (user_id,))
    print("  [+] Cleanup complete.")

def set_user_state(username, is_active=True, tier=None):
    print(f"--- [AUTO] Setting state for '{username}' (Active: {is_active}, Tier: {tier or 'Default'}) ---")
    if tier:
        db_execute("UPDATE users SET is_active = %s, tier = %s WHERE username = %s", (is_active, tier, username))
    else:
        db_execute("UPDATE users SET is_active = %s WHERE username = %s", (is_active, username))

# --- API CLIENT ---
class ApiClient:
    def __init__(self, base_url, username):
        self.base_url = base_url
        self.username = username
        self.session = requests.Session()
        self.access_token = None
        self.device_fingerprint = hashlib.sha256(f"{self.username}-{uuid.uuid4()}".encode()).hexdigest()

    def _make_request(self, method, endpoint, **kwargs):
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        try:
            return self.session.request(method, f"{self.base_url}{endpoint}", headers=headers, timeout=5, **kwargs)
        except requests.exceptions.RequestException as e:
            print(f"  [!] Request Error: {e}")
            return None

    def register(self, password): return self._make_request("POST", "/users/", json={"username": self.username, "password": password})
    def login(self, password, fp=None):
        res = self._make_request("POST", "/users/token", json={"username": self.username, "password": password, "device_fingerprint": fp})
        if res and res.ok:
            self.access_token = res.json().get("access_token")
        return res
    def register_device(self): return self._make_request("POST", "/users/me/register-device", json={"device_fingerprint": self.device_fingerprint})
    def get_me(self): return self._make_request("GET", "/users/me/")
    def create_product(self, url, price): return self._make_request("POST", "/products/", json={"url": url, "price_threshold": price})
    def get_all_products(self): return self._make_request("GET", "/products/")


# --- TEST CASES ---
def run_all_tests():
    print("="*80 + "\n            DEALTRACKER API PRODUCTION-GRADE TEST SUITE\n" + "="*80)
    
    # Define users for all tests
    happy_user, admin_user, error_user, conflict_user_A, conflict_user_B = "happy", "admin", "error", "conflictA", "conflictB"
    all_users = [happy_user, admin_user, error_user, conflict_user_A, conflict_user_B]
    
    # Centralized cleanup at the start and end
    cleanup_users(all_users)
    
    try:
        # == Test 1: Happy Path Workflow ==
        print(f"\n{'='*70}\n=> TEST: Standard User Happy Path Workflow\n{'='*70}")
        client = ApiClient(BASE_URL, happy_user)
        assert client.register("Pass123!").ok
        set_user_state(happy_user, is_active=True)
        assert client.login("Pass123!").ok
        assert client.register_device().ok
        assert client.login("Pass123!", fp=client.device_fingerprint).ok
        assert client.get_me().json()['username'] == happy_user
        product_res = client.create_product("https://www.myntra.com/p1", 100)
        assert product_res.ok
        assert client.get_all_products().status_code == 403, "Standard user must be forbidden from seeing all products"
        print("[SUCCESS] Standard User Workflow passed.")

        # == Test 2: Admin Tier Workflow ==
        print(f"\n{'='*70}\n=> TEST: Admin-Tier User Workflow\n{'='*70}")
        admin_client = ApiClient(BASE_URL, admin_user)
        assert admin_client.register("Pass123!").ok
        set_user_state(admin_user, is_active=True, tier="admin") # Correctly set to 'admin'
        assert admin_client.login("Pass123!").ok
        assert admin_client.get_all_products().ok, "Admin user must be able to see all products"
        print("[SUCCESS] Admin-Tier User Workflow passed.")

        # == Test 3: Security and Error Cases ==
        print(f"\n{'='*70}\n=> TEST: Security and Error Cases\n{'='*70}")
        error_client = ApiClient(BASE_URL, error_user)
        assert error_client.register("Pass123!").ok
        assert error_client.login("Pass123!").status_code == 403, "Login with inactive account"
        set_user_state(error_user, is_active=True)
        assert error_client.login("WrongPass").status_code == 401, "Login with bad password"
        assert error_client.login("Pass123!").ok # Successful login to get token
        assert error_client.register_device().ok # Register the correct device
        assert error_client.login("Pass123!", fp="wrong-fingerprint").status_code == 403, "Login with bad fingerprint"
        assert error_client.create_product("http://badurl.com", 100).status_code == 422, "Invalid product URL"
        print("[SUCCESS] Security and Error Cases passed.")
        
        # == Test 4: Multi-User Conflicts ==
        print(f"\n{'='*70}\n=> TEST: Multi-User Device Conflicts\n{'='*70}")
        client_A = ApiClient(BASE_URL, conflict_user_A)
        client_B = ApiClient(BASE_URL, conflict_user_B)
        assert client_A.register("Pass123!").ok and client_B.register("Pass123!").ok
        set_user_state(conflict_user_A, True); set_user_state(conflict_user_B, True)
        assert client_A.login("Pass123!").ok and client_B.login("Pass123!").ok
        assert client_A.register_device().ok, "User A registers device"
        res = client_B._make_request("POST", "/users/me/register-device", json={"device_fingerprint": client_A.device_fingerprint})
        assert res.status_code == 409, "User B fails to register same device"
        print("[SUCCESS] Multi-User Device Conflict test passed.")

    except AssertionError as e:
        print(f"\n[CRITICAL FAIL] An assertion failed: {e}. Stopping tests.")
    except Exception as e:
        print(f"\n[CRITICAL FAIL] An unexpected error occurred: {e}. Stopping tests.")
    finally:
        # Final cleanup
        cleanup_users(all_users)
        print("\n" + "="*80 + "\n                 COMPREHENSIVE TEST SUITE COMPLETED\n" + "="*80)

if __name__ == "__main__":
    run_all_tests()