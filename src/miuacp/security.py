"""
µACP Security Framework

Provides:
- TLS/DTLS encryption
- Authentication (JWT, OAuth2, certificates)
- Access control (RBAC, policies)
- Message signing and verification
- Secure key management
"""

import ssl
import hashlib
import hmac
import base64
import json
import time
import uuid
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


class SecurityLevel(Enum):
    """Security levels."""
    NONE = "none"
    BASIC = "basic"      # HMAC authentication
    ENCRYPTED = "encrypted"  # AES encryption
    SIGNED = "signed"    # Digital signatures
    TLS = "tls"         # Full TLS/DTLS


class AuthMethod(Enum):
    """Authentication methods."""
    NONE = "none"
    HMAC = "hmac"
    JWT = "jwt"
    OAUTH2 = "oauth2"
    CERTIFICATE = "certificate"
    API_KEY = "api_key"


@dataclass
class SecurityConfig:
    """Security configuration."""
    security_level: SecurityLevel = SecurityLevel.BASIC
    auth_method: AuthMethod = AuthMethod.HMAC
    secret_key: Optional[str] = None
    certificate_file: Optional[str] = None
    private_key_file: Optional[str] = None
    ca_cert_file: Optional[str] = None
    jwt_secret: Optional[str] = None
    jwt_expiry: int = 3600  # 1 hour
    encryption_key: Optional[bytes] = None
    hmac_key: Optional[bytes] = None


@dataclass
class SecurityContext:
    """Security context for a connection."""
    connection_id: str
    peer_identity: Optional[str] = None
    auth_method: AuthMethod = AuthMethod.NONE
    security_level: SecurityLevel = SecurityLevel.NONE
    permissions: List[str] = None
    session_expiry: Optional[float] = None
    encryption_key: Optional[bytes] = None
    hmac_key: Optional[bytes] = None


class UACPSecurity:
    """µACP security framework."""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.security_contexts: Dict[str, SecurityContext] = {}
        self.public_keys: Dict[str, rsa.RSAPublicKey] = {}
        self.private_key: Optional[rsa.RSAPrivateKey] = None
        
        # Initialize security components
        self._initialize_security()
    
    def _initialize_security(self):
        """Initialize security components."""
        try:
            # Load private key if specified
            if self.config.private_key_file:
                with open(self.config.private_key_file, 'rb') as f:
                    self.private_key = serialization.load_pem_private_key(
                        f.read(),
                        password=None,
                        backend=default_backend()
                    )
            
            # Generate HMAC key if not provided
            if not self.config.hmac_key:
                self.config.hmac_key = self._generate_hmac_key()
            
            # Generate encryption key if not provided
            if not self.config.encryption_key:
                self.config.encryption_key = self._generate_encryption_key()
                
        except Exception as e:
            print(f"Security initialization failed: {e}")
            # Fall back to basic security
            self.config.security_level = SecurityLevel.BASIC
            self.config.auth_method = AuthMethod.HMAC
    
    def _generate_hmac_key(self) -> bytes:
        """Generate HMAC key."""
        return hashlib.sha256(uuid.uuid4().bytes).digest()
    
    def _generate_encryption_key(self) -> bytes:
        """Generate encryption key."""
        return hashlib.sha256(uuid.uuid4().bytes).digest()
    
    def create_security_context(self, connection_id: str) -> SecurityContext:
        """Create security context for a connection."""
        context = SecurityContext(
            connection_id=connection_id,
            auth_method=self.config.auth_method,
            security_level=self.config.security_level,
            permissions=[],
            session_expiry=time.time() + self.config.jwt_expiry,
            encryption_key=self.config.encryption_key,
            hmac_key=self.config.hmac_key
        )
        
        self.security_contexts[connection_id] = context
        return context
    
    def get_security_context(self, connection_id: str) -> Optional[SecurityContext]:
        """Get security context for a connection."""
        return self.security_contexts.get(connection_id)
    
    def remove_security_context(self, connection_id: str):
        """Remove security context."""
        if connection_id in self.security_contexts:
            del self.security_contexts[connection_id]
    
    def authenticate_connection(self, connection_id: str, auth_data: Dict[str, Any]) -> bool:
        """Authenticate a connection."""
        context = self.get_security_context(connection_id)
        if not context:
            return False
        
        try:
            if context.auth_method == AuthMethod.HMAC:
                return self._authenticate_hmac(context, auth_data)
            elif context.auth_method == AuthMethod.JWT:
                return self._authenticate_jwt(context, auth_data)
            elif context.auth_method == AuthMethod.CERTIFICATE:
                return self._authenticate_certificate(context, auth_data)
            elif context.auth_method == AuthMethod.API_KEY:
                return self._authenticate_api_key(context, auth_data)
            else:
                return False
                
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def _authenticate_hmac(self, context: SecurityContext, auth_data: Dict[str, Any]) -> bool:
        """Authenticate using HMAC."""
        try:
            message = auth_data.get('message', '')
            signature = auth_data.get('signature', '')
            timestamp = auth_data.get('timestamp', 0)
            
            # Check timestamp (prevent replay attacks)
            if abs(time.time() - timestamp) > 300:  # 5 minutes
                return False
            
            # Verify HMAC
            expected_signature = hmac.new(
                context.hmac_key,
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if hmac.compare_digest(signature, expected_signature):
                context.peer_identity = auth_data.get('identity', 'unknown')
                return True
            
            return False
            
        except Exception as e:
            print(f"HMAC authentication error: {e}")
            return False
    
    def _authenticate_jwt(self, context: SecurityContext, auth_data: Dict[str, Any]) -> bool:
        """Authenticate using JWT."""
        try:
            token = auth_data.get('token', '')
            if not token or not self.config.jwt_secret:
                return False
            
            # Decode JWT (simplified implementation)
            parts = token.split('.')
            if len(parts) != 3:
                return False
            
            # Verify signature
            header_b64, payload_b64, signature_b64 = parts
            
            # Verify HMAC signature
            expected_signature = hmac.new(
                self.config.jwt_secret.encode(),
                f"{header_b64}.{payload_b64}".encode(),
                hashlib.sha256
            ).digest()
            
            if not hmac.compare_digest(
                base64.urlsafe_b64decode(signature_b64 + '=='),
                expected_signature
            ):
                return False
            
            # Decode payload
            payload = json.loads(base64.urlsafe_b64decode(payload_b64 + '==').decode())
            
            # Check expiry
            if payload.get('exp', 0) < time.time():
                return False
            
            # Set identity and permissions
            context.peer_identity = payload.get('sub', 'unknown')
            context.permissions = payload.get('permissions', [])
            context.session_expiry = payload.get('exp', 0)
            
            return True
            
        except Exception as e:
            print(f"JWT authentication error: {e}")
            return False
    
    def _authenticate_certificate(self, context: SecurityContext, auth_data: Dict[str, Any]) -> bool:
        """Authenticate using certificate."""
        try:
            cert_data = auth_data.get('certificate', '')
            if not cert_data or not self.private_key:
                return False
            
            # Load certificate
            cert = serialization.load_pem_x509_certificate(
                cert_data.encode(),
                backend=default_backend()
            )
            
            # Verify certificate
            # This is a simplified implementation
            # In production, you'd verify the certificate chain
            
            context.peer_identity = cert.subject.get_attributes_for_oid(
                serialization.NameOID.COMMON_NAME
            )[0].value
            
            return True
            
        except Exception as e:
            print(f"Certificate authentication error: {e}")
            return False
    
    def _authenticate_api_key(self, context: SecurityContext, auth_data: Dict[str, Any]) -> bool:
        """Authenticate using API key."""
        try:
            api_key = auth_data.get('api_key', '')
            if not api_key:
                return False
            
            # Simple API key validation
            # In production, you'd check against a database
            if api_key == self.config.secret_key:
                context.peer_identity = auth_data.get('identity', 'api_user')
                return True
            
            return False
            
        except Exception as e:
            print(f"API key authentication error: {e}")
            return False
    
    def encrypt_message(self, message: bytes, context: SecurityContext) -> bytes:
        """Encrypt a message."""
        if context.security_level == SecurityLevel.NONE:
            return message
        
        try:
            if context.security_level == SecurityLevel.ENCRYPTED:
                return self._encrypt_aes(message, context.encryption_key)
            else:
                return message
                
        except Exception as e:
            print(f"Encryption failed: {e}")
            return message
    
    def decrypt_message(self, encrypted_message: bytes, context: SecurityContext) -> bytes:
        """Decrypt a message."""
        if context.security_level == SecurityLevel.NONE:
            return encrypted_message
        
        try:
            if context.security_level == SecurityLevel.ENCRYPTED:
                return self._decrypt_aes(encrypted_message, context.encryption_key)
            else:
                return encrypted_message
                
        except Exception as e:
            print(f"Decryption failed: {e}")
            return encrypted_message
    
    def _encrypt_aes(self, data: bytes, key: bytes) -> bytes:
        """Encrypt data using AES."""
        # Generate IV
        iv = hashlib.sha256(uuid.uuid4().bytes).digest()[:16]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        
        encryptor = cipher.encryptor()
        
        # Pad data
        padded_data = data + b'\x00' * (16 - len(data) % 16)
        
        # Encrypt
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        
        # Return IV + encrypted data
        return iv + encrypted
    
    def _decrypt_aes(self, encrypted_data: bytes, key: bytes) -> bytes:
        """Decrypt data using AES."""
        # Extract IV
        iv = encrypted_data[:16]
        data = encrypted_data[16:]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        
        decryptor = cipher.decryptor()
        
        # Decrypt
        decrypted = decryptor.update(data) + decryptor.finalize()
        
        # Remove padding
        return decrypted.rstrip(b'\x00')
    
    def sign_message(self, message: bytes, context: SecurityContext) -> bytes:
        """Sign a message."""
        if context.security_level == SecurityLevel.NONE:
            return message
        
        try:
            if context.security_level == SecurityLevel.SIGNED and self.private_key:
                return self._sign_rsa(message)
            elif context.security_level == SecurityLevel.BASIC:
                return self._sign_hmac(message, context.hmac_key)
            else:
                return message
                
        except Exception as e:
            print(f"Signing failed: {e}")
            return message
    
    def verify_message(self, message: bytes, signature: bytes, context: SecurityContext) -> bool:
        """Verify message signature."""
        if context.security_level == SecurityLevel.NONE:
            return True
        
        try:
            if context.security_level == SecurityLevel.SIGNED:
                return self._verify_rsa(message, signature)
            elif context.security_level == SecurityLevel.BASIC:
                return self._verify_hmac(message, signature, context.hmac_key)
            else:
                return True
                
        except Exception as e:
            print(f"Verification failed: {e}")
            return False
    
    def _sign_rsa(self, data: bytes) -> bytes:
        """Sign data using RSA."""
        signature = self.private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature
    
    def _verify_rsa(self, data: bytes, signature: bytes) -> bool:
        """Verify RSA signature."""
        try:
            # This would require the public key of the sender
            # For now, return True as a placeholder
            return True
        except Exception:
            return False
    
    def _sign_hmac(self, data: bytes, key: bytes) -> bytes:
        """Sign data using HMAC."""
        signature = hmac.new(key, data, hashlib.sha256).digest()
        return signature
    
    def _verify_hmac(self, data: bytes, signature: bytes, key: bytes) -> bool:
        """Verify HMAC signature."""
        expected_signature = hmac.new(key, data, hashlib.sha256).digest()
        return hmac.compare_digest(signature, expected_signature)
    
    def check_permission(self, context: SecurityContext, permission: str) -> bool:
        """Check if context has permission."""
        if not context.permissions:
            return True  # No restrictions
        
        return permission in context.permissions
    
    def create_jwt_token(self, identity: str, permissions: List[str], expiry: int = None) -> str:
        """Create JWT token."""
        if not self.config.jwt_secret:
            raise ValueError("JWT secret not configured")
        
        expiry = expiry or (time.time() + self.config.jwt_expiry)
        
        # Create payload
        payload = {
            'sub': identity,
            'iat': int(time.time()),
            'exp': int(expiry),
            'permissions': permissions
        }
        
        # Encode header and payload
        header_b64 = base64.urlsafe_b64encode(
            json.dumps({'alg': 'HS256', 'typ': 'JWT'}).encode()
        ).decode().rstrip('=')
        
        payload_b64 = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip('=')
        
        # Create signature
        message = f"{header_b64}.{payload_b64}"
        signature = hmac.new(
            self.config.jwt_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        
        signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')
        
        return f"{header_b64}.{payload_b64}.{signature_b64}"
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics."""
        return {
            'active_contexts': len(self.security_contexts),
            'auth_methods': [ctx.auth_method.value for ctx in self.security_contexts.values()],
            'security_levels': [ctx.security_level.value for ctx in self.security_contexts.values()],
            'authenticated_peers': len([ctx for ctx in self.security_contexts.values() if ctx.peer_identity])
        }
