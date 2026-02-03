"""
µACP Status Codes Registry

Implements:
- Complete status code registry (success, client error, server error, negotiation)
- IANA registry definitions for future extension
- Status code categories and ranges
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import IntEnum


class StatusCodeCategory(IntEnum):
    """Status code categories."""
    SUCCESS = 0x00        # 0-63: Success responses
    CLIENT_ERROR = 0x40   # 64-127: Client errors
    SERVER_ERROR = 0x80   # 128-191: Server errors
    NEGOTIATION = 0xC0    # 192-255: Negotiation and capability codes


class UACPStatusCodes(IntEnum):
    """µACP status codes registry."""
    
    # ===== SUCCESS CODES (0-63) =====
    OK = 0x00                    # Request completed successfully
    CREATED = 0x01              # Resource created successfully
    ACCEPTED = 0x02             # Request accepted for processing
    NO_CONTENT = 0x03           # Request completed, no content to return
    RESET_CONTENT = 0x04        # Request completed, content reset
    
    # ===== CLIENT ERROR CODES (64-127) =====
    BAD_REQUEST = 0x40          # Request syntax error or invalid
    UNAUTHORIZED = 0x41         # Authentication required
    FORBIDDEN = 0x42            # Access forbidden
    NOT_FOUND = 0x43            # Resource not found
    METHOD_NOT_ALLOWED = 0x44   # Verb not allowed for this resource
    NOT_ACCEPTABLE = 0x45       # Requested format not available
    REQUEST_TIMEOUT = 0x46      # Request timed out
    CONFLICT = 0x47             # Request conflicts with current state
    GONE = 0x48                 # Resource no longer available
    LENGTH_REQUIRED = 0x49      # Content-Length required
    PAYLOAD_TOO_LARGE = 0x4A    # Payload exceeds maximum size
    URI_TOO_LONG = 0x4B         # URI exceeds maximum length
    UNSUPPORTED_CONTENT_TYPE = 0x4C  # Content type not supported
    UNSUPPORTED_QOS = 0x4D      # QoS level not supported
    UNSUPPORTED_VERB = 0x4E     # Verb not supported
    INVALID_OPTION = 0x4F       # Invalid option value
    
    # ===== SERVER ERROR CODES (128-191) =====
    INTERNAL_ERROR = 0x80       # Internal server error
    NOT_IMPLEMENTED = 0x81      # Feature not implemented
    BAD_GATEWAY = 0x82          # Bad gateway response
    SERVICE_UNAVAILABLE = 0x83  # Service temporarily unavailable
    GATEWAY_TIMEOUT = 0x84      # Gateway timeout
    VERSION_NOT_SUPPORTED = 0x85 # Protocol version not supported
    INSUFFICIENT_STORAGE = 0x86 # Insufficient storage space
    LOOP_DETECTED = 0x87        # Loop detected in routing
    
    # ===== NEGOTIATION CODES (192-255) =====
    NEGOTIATION_REQUIRED = 0xC0 # Capability negotiation required
    CAPABILITY_UNSUPPORTED = 0xC1  # Requested capability not supported
    AUTH_METHOD_UNSUPPORTED = 0xC2 # Authentication method not supported
    SECURITY_LEVEL_UNSUPPORTED = 0xC3  # Security level not supported
    TRANSPORT_UNSUPPORTED = 0xC4  # Transport binding not supported
    FEATURE_NEGOTIATION_FAILED = 0xC5  # Feature negotiation failed
    SECURITY_NEGOTIATION_FAILED = 0xC6  # Security negotiation failed
    VERSION_MISMATCH = 0xC7     # Version compatibility issue
    
    # ===== RESERVED CODES =====
    # 0xC8-0xFF: Reserved for future use


@dataclass
class StatusCodeInfo:
    """Status code information structure."""
    code: int
    name: str
    description: str
    category: StatusCodeCategory
    http_equivalent: Optional[str] = None
    coap_equivalent: Optional[str] = None
    mqtt_equivalent: Optional[str] = None
    retry_allowed: bool = False
    user_actionable: bool = False


class UACPStatusCodeRegistry:
    """µACP status code registry with IANA definitions."""
    
    def __init__(self):
        self.registry: Dict[int, StatusCodeInfo] = {}
        self._initialize_registry()
    
    def _initialize_registry(self):
        """Initialize the status code registry."""
        # Success codes
        self._register_code(0x00, "OK", "Request completed successfully", 
                           StatusCodeCategory.SUCCESS, "200 OK", "2.01 Created", None)
        self._register_code(0x01, "CREATED", "Resource created successfully", 
                           StatusCodeCategory.SUCCESS, "201 Created", "2.01 Created", None)
        self._register_code(0x02, "ACCEPTED", "Request accepted for processing", 
                           StatusCodeCategory.SUCCESS, "202 Accepted", "2.02 Valid", None)
        self._register_code(0x03, "NO_CONTENT", "Request completed, no content to return", 
                           StatusCodeCategory.SUCCESS, "204 No Content", "2.04 Changed", None)
        self._register_code(0x04, "RESET_CONTENT", "Request completed, content reset", 
                           StatusCodeCategory.SUCCESS, "205 Reset Content", "2.04 Changed", None)
        
        # Client error codes
        self._register_code(0x40, "BAD_REQUEST", "Request syntax error or invalid", 
                           StatusCodeCategory.CLIENT_ERROR, "400 Bad Request", "4.00 Bad Request", None, 
                           retry_allowed=True, user_actionable=True)
        self._register_code(0x41, "UNAUTHORIZED", "Authentication required", 
                           StatusCodeCategory.CLIENT_ERROR, "401 Unauthorized", "4.01 Unauthorized", None, 
                           retry_allowed=True, user_actionable=True)
        self._register_code(0x42, "FORBIDDEN", "Access forbidden", 
                           StatusCodeCategory.CLIENT_ERROR, "403 Forbidden", "4.03 Forbidden", None, 
                           retry_allowed=False, user_actionable=True)
        self._register_code(0x43, "NOT_FOUND", "Resource not found", 
                           StatusCodeCategory.CLIENT_ERROR, "404 Not Found", "4.04 Not Found", None, 
                           retry_allowed=True, user_actionable=True)
        self._register_code(0x44, "METHOD_NOT_ALLOWED", "Verb not allowed for this resource", 
                           StatusCodeCategory.CLIENT_ERROR, "405 Method Not Allowed", "4.05 Method Not Allowed", None, 
                           retry_allowed=False, user_actionable=True)
        self._register_code(0x45, "NOT_ACCEPTABLE", "Requested format not available", 
                           StatusCodeCategory.CLIENT_ERROR, "406 Not Acceptable", "4.06 Not Acceptable", None, 
                           retry_allowed=True, user_actionable=True)
        self._register_code(0x46, "REQUEST_TIMEOUT", "Request timed out", 
                           StatusCodeCategory.CLIENT_ERROR, "408 Request Timeout", "4.08 Request Entity Incomplete", None, 
                           retry_allowed=True, user_actionable=False)
        self._register_code(0x47, "CONFLICT", "Request conflicts with current state", 
                           StatusCodeCategory.CLIENT_ERROR, "409 Conflict", "4.09 Conflict", None, 
                           retry_allowed=True, user_actionable=True)
        self._register_code(0x48, "GONE", "Resource no longer available", 
                           StatusCodeCategory.CLIENT_ERROR, "410 Gone", "4.10 Gone", None, 
                           retry_allowed=False, user_actionable=True)
        self._register_code(0x49, "LENGTH_REQUIRED", "Content-Length required", 
                           StatusCodeCategory.CLIENT_ERROR, "411 Length Required", "4.11 Request Entity Incomplete", None, 
                           retry_allowed=True, user_actionable=True)
        self._register_code(0x4A, "PAYLOAD_TOO_LARGE", "Payload exceeds maximum size", 
                           StatusCodeCategory.CLIENT_ERROR, "413 Payload Too Large", "4.13 Request Entity Too Large", None, 
                           retry_allowed=True, user_actionable=True)
        self._register_code(0x4B, "URI_TOO_LONG", "URI exceeds maximum length", 
                           StatusCodeCategory.CLIENT_ERROR, "414 URI Too Long", "4.14 Request Entity Too Large", None, 
                           retry_allowed=True, user_actionable=True)
        self._register_code(0x4C, "UNSUPPORTED_CONTENT_TYPE", "Content type not supported", 
                           StatusCodeCategory.CLIENT_ERROR, "415 Unsupported Media Type", "4.15 Unsupported Content-Format", None, 
                           retry_allowed=True, user_actionable=True)
        self._register_code(0x4D, "UNSUPPORTED_QOS", "QoS level not supported", 
                           StatusCodeCategory.CLIENT_ERROR, None, None, "QoS not supported", 
                           retry_allowed=True, user_actionable=True)
        self._register_code(0x4E, "UNSUPPORTED_VERB", "Verb not supported", 
                           StatusCodeCategory.CLIENT_ERROR, "405 Method Not Allowed", "4.05 Method Not Allowed", None, 
                           retry_allowed=False, user_actionable=True)
        self._register_code(0x4F, "INVALID_OPTION", "Invalid option value", 
                           StatusCodeCategory.CLIENT_ERROR, "400 Bad Request", "4.00 Bad Request", None, 
                           retry_allowed=True, user_actionable=True)
        
        # Server error codes
        self._register_code(0x80, "INTERNAL_ERROR", "Internal server error", 
                           StatusCodeCategory.SERVER_ERROR, "500 Internal Server Error", "5.00 Internal Server Error", None, 
                           retry_allowed=True, user_actionable=False)
        self._register_code(0x81, "NOT_IMPLEMENTED", "Feature not implemented", 
                           StatusCodeCategory.SERVER_ERROR, "501 Not Implemented", "5.01 Not Implemented", None, 
                           retry_allowed=False, user_actionable=False)
        self._register_code(0x82, "BAD_GATEWAY", "Bad gateway response", 
                           StatusCodeCategory.SERVER_ERROR, "502 Bad Gateway", "5.02 Bad Gateway", None, 
                           retry_allowed=True, user_actionable=False)
        self._register_code(0x83, "SERVICE_UNAVAILABLE", "Service temporarily unavailable", 
                           StatusCodeCategory.SERVER_ERROR, "503 Service Unavailable", "5.03 Service Unavailable", None, 
                           retry_allowed=True, user_actionable=False)
        self._register_code(0x84, "GATEWAY_TIMEOUT", "Gateway timeout", 
                           StatusCodeCategory.SERVER_ERROR, "504 Gateway Timeout", "5.04 Gateway Timeout", None, 
                           retry_allowed=True, user_actionable=False)
        self._register_code(0x85, "VERSION_NOT_SUPPORTED", "Protocol version not supported", 
                           StatusCodeCategory.SERVER_ERROR, "505 HTTP Version Not Supported", "5.05 Proxying Not Supported", None, 
                           retry_allowed=False, user_actionable=False)
        self._register_code(0x86, "INSUFFICIENT_STORAGE", "Insufficient storage space", 
                           StatusCodeCategory.SERVER_ERROR, "507 Insufficient Storage", "5.07 Insufficient Storage", None, 
                           retry_allowed=True, user_actionable=False)
        self._register_code(0x87, "LOOP_DETECTED", "Loop detected in routing", 
                           StatusCodeCategory.SERVER_ERROR, "508 Loop Detected", "5.08 Hop Limit Reached", None, 
                           retry_allowed=False, user_actionable=False)
        
        # Negotiation codes
        self._register_code(0xC0, "NEGOTIATION_REQUIRED", "Capability negotiation required", 
                           StatusCodeCategory.NEGOTIATION, "426 Upgrade Required", "4.26 Upgrade Required", None, 
                           retry_allowed=True, user_actionable=False)
        self._register_code(0xC1, "CAPABILITY_UNSUPPORTED", "Requested capability not supported", 
                           StatusCodeCategory.NEGOTIATION, "501 Not Implemented", "5.01 Not Implemented", None, 
                           retry_allowed=False, user_actionable=True)
        self._register_code(0xC2, "AUTH_METHOD_UNSUPPORTED", "Authentication method not supported", 
                           StatusCodeCategory.NEGOTIATION, "401 Unauthorized", "4.01 Unauthorized", None, 
                           retry_allowed=True, user_actionable=True)
        self._register_code(0xC3, "SECURITY_LEVEL_UNSUPPORTED", "Security level not supported", 
                           StatusCodeCategory.NEGOTIATION, "403 Forbidden", "4.03 Forbidden", None, 
                           retry_allowed=True, user_actionable=True)
        self._register_code(0xC4, "TRANSPORT_UNSUPPORTED", "Transport binding not supported", 
                           StatusCodeCategory.NEGOTIATION, "426 Upgrade Required", "4.26 Upgrade Required", None, 
                           retry_allowed=True, user_actionable=False)
        self._register_code(0xC5, "FEATURE_NEGOTIATION_FAILED", "Feature negotiation failed", 
                           StatusCodeCategory.NEGOTIATION, "400 Bad Request", "4.00 Bad Request", None, 
                           retry_allowed=True, user_actionable=False)
        self._register_code(0xC6, "SECURITY_NEGOTIATION_FAILED", "Security negotiation failed", 
                           StatusCodeCategory.NEGOTIATION, "400 Bad Request", "4.00 Bad Request", None, 
                           retry_allowed=True, user_actionable=False)
        self._register_code(0xC7, "VERSION_MISMATCH", "Version compatibility issue", 
                           StatusCodeCategory.NEGOTIATION, "426 Upgrade Required", "4.26 Upgrade Required", None, 
                           retry_allowed=False, user_actionable=False)
    
    def _register_code(self, code: int, name: str, description: str, 
                      category: StatusCodeCategory, http_equivalent: Optional[str] = None,
                      coap_equivalent: Optional[str] = None, mqtt_equivalent: Optional[str] = None,
                      retry_allowed: bool = False, user_actionable: bool = False):
        """Register a status code."""
        self.registry[code] = StatusCodeInfo(
            code=code,
            name=name,
            description=description,
            category=category,
            http_equivalent=http_equivalent,
            coap_equivalent=coap_equivalent,
            mqtt_equivalent=mqtt_equivalent,
            retry_allowed=retry_allowed,
            user_actionable=user_actionable
        )
    
    def get_status_code(self, code: int) -> Optional[StatusCodeInfo]:
        """Get status code information."""
        return self.registry.get(code)
    
    def get_status_codes_by_category(self, category: StatusCodeCategory) -> List[StatusCodeInfo]:
        """Get all status codes in a category."""
        return [info for info in self.registry.values() if info.category == category]
    
    def get_retry_allowed_codes(self) -> List[StatusCodeInfo]:
        """Get status codes that allow retry."""
        return [info for info in self.registry.values() if info.retry_allowed]
    
    def get_user_actionable_codes(self) -> List[StatusCodeInfo]:
        """Get status codes that are user actionable."""
        return [info for info in self.registry.values() if info.user_actionable]
    
    def is_success(self, code: int) -> bool:
        """Check if status code indicates success."""
        return 0x00 <= code <= 0x3F
    
    def is_client_error(self, code: int) -> bool:
        """Check if status code indicates client error."""
        return 0x40 <= code <= 0x7F
    
    def is_server_error(self, code: int) -> bool:
        """Check if status code indicates server error."""
        return 0x80 <= code <= 0xBF
    
    def is_negotiation(self, code: int) -> bool:
        """Check if status code indicates negotiation."""
        return 0xC0 <= code <= 0xFF
    
    def get_category(self, code: int) -> Optional[StatusCodeCategory]:
        """Get the category of a status code."""
        if self.is_success(code):
            return StatusCodeCategory.SUCCESS
        elif self.is_client_error(code):
            return StatusCodeCategory.CLIENT_ERROR
        elif self.is_server_error(code):
            return StatusCodeCategory.SERVER_ERROR
        elif self.is_negotiation(code):
            return StatusCodeCategory.NEGOTIATION
        else:
            return None
    
    def get_iana_registry(self) -> Dict[str, Any]:
        """Get IANA registry format."""
        registry = {
            'registry_name': 'µACP Status Codes',
            'reference': 'RFC-XXXX (µACP Protocol)',
            'registration_procedure': 'Standards Action',
            'note': 'Status codes for the Micro Agent Communication Protocol',
            'ranges': [
                {
                    'range': '0x00-0x3F',
                    'description': 'Success responses',
                    'reference': 'RFC-XXXX Section X.X'
                },
                {
                    'range': '0x40-0x7F',
                    'description': 'Client error responses',
                    'reference': 'RFC-XXXX Section X.X'
                },
                {
                    'range': '0x80-0xBF',
                    'description': 'Server error responses',
                    'reference': 'RFC-XXXX Section X.X'
                },
                {
                    'range': '0xC0-0xFF',
                    'description': 'Negotiation and capability responses',
                    'reference': 'RFC-XXXX Section X.X'
                }
            ],
            'codes': {}
        }
        
        for code, info in self.registry.items():
            registry['codes'][f"0x{code:02X}"] = {
                'name': info.name,
                'description': info.description,
                'reference': 'RFC-XXXX Section X.X'
            }
        
        return registry
    
    def export_markdown(self) -> str:
        """Export registry as Markdown table."""
        lines = [
            "# µACP Status Codes Registry",
            "",
            "| Code | Name | Description | Category | HTTP Equivalent | CoAP Equivalent | Retry Allowed |",
            "|------|------|-------------|----------|-----------------|-----------------|---------------|"
        ]
        
        for code in sorted(self.registry.keys()):
            info = self.registry[code]
            http_eq = info.http_equivalent or "-"
            coap_eq = info.coap_equivalent or "-"
            retry = "Yes" if info.retry_allowed else "No"
            
            lines.append(
                f"| 0x{code:02X} | {info.name} | {info.description} | {info.category.name} | {http_eq} | {coap_eq} | {retry} |"
            )
        
        return "\n".join(lines)
    
    def export_json(self) -> str:
        """Export registry as JSON."""
        import json
        
        export_data = {
            'registry_name': 'µACP Status Codes',
            'version': '2.0.0',
            'total_codes': len(self.registry),
            'categories': {
                'success': len(self.get_status_codes_by_category(StatusCodeCategory.SUCCESS)),
                'client_error': len(self.get_status_codes_by_category(StatusCodeCategory.CLIENT_ERROR)),
                'server_error': len(self.get_status_codes_by_category(StatusCodeCategory.SERVER_ERROR)),
                'negotiation': len(self.get_status_codes_by_category(StatusCodeCategory.NEGOTIATION))
            },
            'codes': {}
        }
        
        for code, info in self.registry.items():
            export_data['codes'][f"0x{code:02X}"] = {
                'name': info.name,
                'description': info.description,
                'category': info.category.name,
                'http_equivalent': info.http_equivalent,
                'coap_equivalent': info.coap_equivalent,
                'mqtt_equivalent': info.mqtt_equivalent,
                'retry_allowed': info.retry_allowed,
                'user_actionable': info.user_actionable
            }
        
        return json.dumps(export_data, indent=2)


# Global registry instance
status_code_registry = UACPStatusCodeRegistry()


def get_status_code(code: int) -> Optional[StatusCodeInfo]:
    """Get status code information from global registry."""
    return status_code_registry.get_status_code(code)


def is_success(code: int) -> bool:
    """Check if status code indicates success."""
    return status_code_registry.is_success(code)


def is_client_error(code: int) -> bool:
    """Check if status code indicates client error."""
    return status_code_registry.is_client_error(code)


def is_server_error(code: int) -> bool:
    """Check if status code indicates server error."""
    return status_code_registry.is_server_error(code)


def is_negotiation(code: int) -> bool:
    """Check if status code indicates negotiation."""
    return status_code_registry.is_negotiation(code)
