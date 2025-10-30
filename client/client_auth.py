import json
import hashlib
import os
import time
import platform
import uuid
import secrets
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging

logger = logging.getLogger(__name__)

class SecureAuthManager:
    """Military-grade authentication manager with advanced security features."""
    
    def __init__(self):
        self.app_dir = Path.home() / ".dealtracker_secure"
        self.app_dir.mkdir(mode=0o700, exist_ok=True)
        
        self.session_file = self.app_dir / "session.vault"
        self.key_file = self.app_dir / "master.key"
        self.device_file = self.app_dir / "device.sig"
        self.salt_file = self.app_dir / "salt.bin"
        
        self._initialize_security()
    
    def _initialize_security(self):
        """Initialize security infrastructure."""
        if not self.key_file.exists():
            self._generate_master_key()
        
        if not self.salt_file.exists():
            salt = os.urandom(32)
            self.salt_file.write_bytes(salt)
            os.chmod(self.salt_file, 0o600)
        
        for file_path in [self.key_file, self.salt_file]:
            if file_path.exists():
                os.chmod(file_path, 0o600)
    
    def _generate_master_key(self):
        """Generate cryptographically secure master key."""
        key_material = secrets.token_bytes(64)
        salt = os.urandom(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=300000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(key_material))
        
        self.key_file.write_bytes(key)
        self.salt_file.write_bytes(salt)
        
        os.chmod(self.key_file, 0o600)
        os.chmod(self.salt_file, 0o600)
    
    def _get_cipher(self) -> Fernet:
        """Get encryption cipher with master key."""
        key = self.key_file.read_bytes()
        return Fernet(key)
    
    def save_session(self, access_token: str, refresh_token: str, 
                    expires_in: int = 86400, user_data: Dict = None) -> bool:
        """Save encrypted session data."""
        try:
            session_data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": expires_in,
                "created_at": int(time.time()),
                "user_data": user_data or {},
                "device_fingerprint": self.get_device_fingerprint(),
                "session_id": secrets.token_hex(16)
            }
            
            cipher = self._get_cipher()
            encrypted_data = cipher.encrypt(json.dumps(session_data).encode())
            
            self.session_file.write_bytes(encrypted_data)
            os.chmod(self.session_file, 0o600)
            
            logger.info("Session saved securely")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False
    
    def load_session(self) -> Optional[Dict[str, Any]]:
        """Load and validate encrypted session."""
        if not self.session_file.exists():
            return None
        
        try:
            cipher = self._get_cipher()
            encrypted_data = self.session_file.read_bytes()
            decrypted_data = cipher.decrypt(encrypted_data)
            
            session_data = json.loads(decrypted_data.decode())
            
            if not self._validate_session(session_data):
                logger.warning("Session validation failed")
                self.clear_session()
                return None
            
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            self.clear_session()
            return None
    
    def _validate_session(self, session_data: Dict) -> bool:
        try:
            required_fields = ['access_token', 'refresh_token', 'created_at', 'expires_in']
            if not all(field in session_data for field in required_fields):
                return False
            stored_fingerprint = session_data.get('device_fingerprint')
            current_fingerprint = self.get_device_fingerprint()
            
            if stored_fingerprint != current_fingerprint:
                logger.warning("Device fingerprint mismatch")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return False
    
    def get_access_token(self) -> Optional[str]:
        """Get current access token."""
        session = self.load_session()
        return session.get('access_token') if session else None
    
    def get_refresh_token(self) -> Optional[str]:
        """Get current refresh token."""
        session = self.load_session()
        return session.get('refresh_token') if session else None
    
    def clear_session(self):
        try:
            if self.session_file.exists():
                file_size = self.session_file.stat().st_size
                with open(self.session_file, 'wb') as f:
                    f.write(os.urandom(file_size))
                
                self.session_file.unlink()
            
            logger.info("Session cleared securely")
            
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
    
    def get_device_fingerprint(self) -> str:
        if self.device_file.exists():
            return self.device_file.read_text().strip()
        
        system_info = {
            'platform': platform.platform(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'system': platform.system(),
            'release': platform.release(),
            'mac_address': self._get_mac_address(),
            'hostname': platform.node(),
            'random_seed': secrets.token_hex(16)
        }
        
        fingerprint_data = json.dumps(system_info, sort_keys=True)
        fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()[:32]
        
        self.device_file.write_text(fingerprint)
        os.chmod(self.device_file, 0o600)
        
        return fingerprint
    
    def _get_mac_address(self) -> str:
        """Get MAC address in consistent format."""
        mac = uuid.getnode()
        return ':'.join(['{:02x}'.format((mac >> elements) & 0xff) 
                        for elements in range(0, 2*6, 2)][::-1])
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated with valid session."""
        return self.get_access_token() is not None
    
    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """Get current session information."""
        session = self.load_session()
        if not session:
            return None
        
        return {
            'session_id': session.get('session_id'),
            'created_at': session.get('created_at'),
            'expires_in': session.get('expires_in'),
            'user_data': session.get('user_data', {}),
            'device_fingerprint': session.get('device_fingerprint')
        }
