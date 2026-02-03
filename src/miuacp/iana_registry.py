"""
µACP IANA Registry & Extension Mechanisms

Implements:
- Complete IANA registry for all code spaces
- Extension mechanisms for future evolution
- Criticality bits for options
- Feature detection and negotiation
"""

import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from .protocol import UACPVerb, UACPOptionType, UACPContentType
from .status_codes import UACPStatusCodes, StatusCodeCategory
import time


class RegistryType(Enum):
    """IANA registry types."""
    MESSAGE_TYPES = "message_types"
    OPTION_CODES = "option_codes"
    STATUS_CODES = "status_codes"
    CONTENT_TYPES = "content_types"
    ERROR_CODES = "error_codes"
    FEATURE_CODES = "feature_codes"


class ExtensionCriticality(Enum):
    """Option extension criticality levels."""
    ELECTIVE = "elective"      # Can be ignored if not understood
    CRITICAL = "critical"      # Must be understood and processed
    DEPRECATED = "deprecated"  # Should not be used in new implementations


@dataclass
class IANARegistryEntry:
    """IANA registry entry."""
    code: int
    name: str
    description: str
    reference: str
    registration_procedure: str
    criticality: ExtensionCriticality = ExtensionCriticality.ELECTIVE
    deprecated: bool = False
    replacement: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class IANARegistry:
    """Complete IANA registry for µACP."""
    registry_name: str
    reference: str
    registration_procedure: str
    note: str
    ranges: List[Dict[str, str]]
    entries: Dict[str, IANARegistryEntry]


class UACPIANARegistry:
    """µACP IANA registry implementation."""
    
    def __init__(self):
        self.registries: Dict[RegistryType, IANARegistry] = {}
        self._initialize_registries()
    
    def _initialize_registries(self):
        """Initialize all IANA registries."""
        self._init_message_types_registry()
        self._init_option_codes_registry()
        self._init_status_codes_registry()
        self._init_content_types_registry()
        self._init_error_codes_registry()
        self._init_feature_codes_registry()
    
    def _init_message_types_registry(self):
        """Initialize message types registry."""
        entries = {
            "0x0": IANARegistryEntry(
                code=0x0,
                name="PING",
                description="Liveness check and clock synchronization",
                reference="RFC-XXXX Section 4.1",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0x1": IANARegistryEntry(
                code=0x1,
                name="TELL",
                description="Inform message (publish/subscribe)",
                reference="RFC-XXXX Section 4.2",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0x2": IANARegistryEntry(
                code=0x2,
                name="ASK",
                description="Request/response message",
                reference="RFC-XXXX Section 4.3",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0x3": IANARegistryEntry(
                code=0x3,
                name="OBSERVE",
                description="Subscription to future events",
                reference="RFC-XXXX Section 4.4",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            )
        }
        
        self.registries[RegistryType.MESSAGE_TYPES] = IANARegistry(
            registry_name="µACP Message Types",
            reference="RFC-XXXX (µACP Protocol)",
            registration_procedure="Standards Action",
            note="Message types for the Micro Agent Communication Protocol",
            ranges=[
                {
                    'range': '0x0-0x3',
                    'description': 'Standard message types',
                    'reference': 'RFC-XXXX Section 4'
                },
                {
                    'range': '0x4-0xF',
                    'description': 'Reserved for future use',
                    'reference': 'RFC-XXXX Section 4'
                }
            ],
            entries=entries
        )
    
    def _init_option_codes_registry(self):
        """Initialize option codes registry."""
        entries = {
            "0x01": IANARegistryEntry(
                code=0x01,
                name="Conv-ID",
                description="Conversation identifier for multi-turn dialogues",
                reference="RFC-XXXX Section 5.1",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0x02": IANARegistryEntry(
                code=0x02,
                name="Corr-ID",
                description="Correlation identifier for request/response pairs",
                reference="RFC-XXXX Section 5.2",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0x03": IANARegistryEntry(
                code=0x03,
                name="Topic-Path",
                description="Topic or path for message routing",
                reference="RFC-XXXX Section 5.3",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.CRITICAL
            ),
            "0x04": IANARegistryEntry(
                code=0x04,
                name="Content-Type",
                description="Content type of the message payload",
                reference="RFC-XXXX Section 5.4",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.CRITICAL
            ),
            "0x05": IANARegistryEntry(
                code=0x05,
                name="ETag",
                description="Entity tag for cache validation",
                reference="RFC-XXXX Section 5.5",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0x06": IANARegistryEntry(
                code=0x06,
                name="Max-Age",
                description="Maximum age of the message in seconds",
                reference="RFC-XXXX Section 5.6",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0x07": IANARegistryEntry(
                code=0x07,
                name="Block",
                description="Block transfer descriptor",
                reference="RFC-XXXX Section 5.7",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0x08": IANARegistryEntry(
                code=0x08,
                name="Auth",
                description="Authentication token identifier",
                reference="RFC-XXXX Section 5.8",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.CRITICAL
            ),
            "0x09": IANARegistryEntry(
                code=0x09,
                name="Priority",
                description="Message priority level (0-7)",
                reference="RFC-XXXX Section 5.9",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0x0A": IANARegistryEntry(
                code=0x0A,
                name="Timeout",
                description="Message timeout in seconds",
                reference="RFC-XXXX Section 5.10",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0x0B": IANARegistryEntry(
                code=0x0B,
                name="Retry-Count",
                description="Number of retry attempts",
                reference="RFC-XXXX Section 5.11",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0x0C": IANARegistryEntry(
                code=0x0C,
                name="Sequence-Number",
                description="Sequence number for ordering",
                reference="RFC-XXXX Section 5.12",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0x0D": IANARegistryEntry(
                code=0x0D,
                name="Compression",
                description="Compression algorithm identifier",
                reference="RFC-XXXX Section 5.13",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0x0E": IANARegistryEntry(
                code=0x0E,
                name="Encryption",
                description="Encryption algorithm identifier",
                reference="RFC-XXXX Section 5.14",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.CRITICAL
            ),
            "0x0F": IANARegistryEntry(
                code=0x0F,
                name="Signature",
                description="Digital signature algorithm identifier",
                reference="RFC-XXXX Section 5.15",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.CRITICAL
            )
        }
        
        self.registries[RegistryType.OPTION_CODES] = IANARegistry(
            registry_name="µACP Option Codes",
            reference="RFC-XXXX (µACP Protocol)",
            registration_procedure="Standards Action",
            note="Option codes for the Micro Agent Communication Protocol",
            ranges=[
                {
                    'range': '0x01-0x0F',
                    'description': 'Standard option codes',
                    'reference': 'RFC-XXXX Section 5'
                },
                {
                    'range': '0x10-0x1F',
                    'description': 'Reserved for future use',
                    'reference': 'RFC-XXXX Section 5'
                },
                {
                    'range': '0x20-0x3F',
                    'description': 'Experimental use',
                    'reference': 'RFC-XXXX Section 5'
                },
                {
                    'range': '0x40-0xFF',
                    'description': 'Vendor-specific use',
                    'reference': 'RFC-XXXX Section 5'
                }
            ],
            entries=entries
        )
    
    def _init_status_codes_registry(self):
        """Initialize status codes registry."""
        entries = {}
        
        # Success codes (0x00-0x3F)
        for code in range(0x00, 0x40):
            if code in UACPStatusCodes.__members__.values():
                status_name = UACPStatusCodes(code).name
                entries[f"0x{code:02X}"] = IANARegistryEntry(
                    code=code,
                    name=status_name,
                    description=f"Success response: {status_name.lower().replace('_', ' ')}",
                    reference="RFC-XXXX Section 6.1",
                    registration_procedure="Standards Action",
                    criticality=ExtensionCriticality.ELECTIVE
                )
        
        # Client error codes (0x40-0x7F)
        for code in range(0x40, 0x80):
            if code in UACPStatusCodes.__members__.values():
                status_name = UACPStatusCodes(code).name
                entries[f"0x{code:02X}"] = IANARegistryEntry(
                    code=code,
                    name=status_name,
                    description=f"Client error: {status_name.lower().replace('_', ' ')}",
                    reference="RFC-XXXX Section 6.2",
                    registration_procedure="Standards Action",
                    criticality=ExtensionCriticality.ELECTIVE
                )
        
        # Server error codes (0x80-0xBF)
        for code in range(0x80, 0xC0):
            if code in UACPStatusCodes.__members__.values():
                status_name = UACPStatusCodes(code).name
                entries[f"0x{code:02X}"] = IANARegistryEntry(
                    code=code,
                    name=status_name,
                    description=f"Server error: {status_name.lower().replace('_', ' ')}",
                    reference="RFC-XXXX Section 6.3",
                    registration_procedure="Standards Action",
                    criticality=ExtensionCriticality.ELECTIVE
                )
        
        # Negotiation codes (0xC0-0xFF)
        for code in range(0xC0, 0x100):
            if code in UACPStatusCodes.__members__.values():
                status_name = UACPStatusCodes(code).name
                entries[f"0x{code:02X}"] = IANARegistryEntry(
                    code=code,
                    name=status_name,
                    description=f"Negotiation: {status_name.lower().replace('_', ' ')}",
                    reference="RFC-XXXX Section 6.4",
                    registration_procedure="Standards Action",
                    criticality=ExtensionCriticality.ELECTIVE
                )
        
        self.registries[RegistryType.STATUS_CODES] = IANARegistry(
            registry_name="µACP Status Codes",
            reference="RFC-XXXX (µACP Protocol)",
            registration_procedure="Standards Action",
            note="Status codes for the Micro Agent Communication Protocol",
            ranges=[
                {
                    'range': '0x00-0x3F',
                    'description': 'Success responses',
                    'reference': 'RFC-XXXX Section 6.1'
                },
                {
                    'range': '0x40-0x7F',
                    'description': 'Client error responses',
                    'reference': 'RFC-XXXX Section 6.2'
                },
                {
                    'range': '0x80-0xBF',
                    'description': 'Server error responses',
                    'reference': 'RFC-XXXX Section 6.3'
                },
                {
                    'range': '0xC0-0xFF',
                    'description': 'Negotiation and capability responses',
                    'reference': 'RFC-XXXX Section 6.4'
                }
            ],
            entries=entries
        )
    
    def _init_content_types_registry(self):
        """Initialize content types registry."""
        entries = {
            "0x0": IANARegistryEntry(
                code=0x0,
                name="CBOR",
                description="Concise Binary Object Representation",
                reference="RFC 8949",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.CRITICAL
            ),
            "0x1": IANARegistryEntry(
                code=0x1,
                name="JSON",
                description="JavaScript Object Notation",
                reference="RFC 8259",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0x2": IANARegistryEntry(
                code=0x2,
                name="Protobuf",
                description="Protocol Buffers",
                reference="Google Protocol Buffers",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0x3": IANARegistryEntry(
                code=0x3,
                name="Text",
                description="Plain text (UTF-8)",
                reference="RFC 3629",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            )
        }
        
        self.registries[RegistryType.CONTENT_TYPES] = IANARegistry(
            registry_name="µACP Content Types",
            reference="RFC-XXXX (µACP Protocol)",
            registration_procedure="Standards Action",
            note="Content types for the Micro Agent Communication Protocol",
            ranges=[
                {
                    'range': '0x0-0x3',
                    'description': 'Standard content types',
                    'reference': 'RFC-XXXX Section 7'
                },
                {
                    'range': '0x4-0xF',
                    'description': 'Reserved for future use',
                    'reference': 'RFC-XXXX Section 7'
                }
            ],
            entries=entries
        )
    
    def _init_error_codes_registry(self):
        """Initialize error codes registry."""
        entries = {
            "0xE000": IANARegistryEntry(
                code=0xE000,
                name="PROTOCOL_ERROR",
                description="Protocol violation or malformed message",
                reference="RFC-XXXX Section 8.1",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.CRITICAL
            ),
            "0xE001": IANARegistryEntry(
                code=0xE001,
                name="INTERNAL_ERROR",
                description="Internal implementation error",
                reference="RFC-XXXX Section 8.2",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0xE002": IANARegistryEntry(
                code=0xE002,
                name="FLOW_CONTROL_ERROR",
                description="Flow control violation",
                reference="RFC-XXXX Section 8.3",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.CRITICAL
            ),
            "0xE003": IANARegistryEntry(
                code=0xE003,
                name="SETTINGS_ERROR",
                description="Settings frame error",
                reference="RFC-XXXX Section 8.4",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.CRITICAL
            ),
            "0xE004": IANARegistryEntry(
                code=0xE004,
                name="STREAM_CLOSED",
                description="Stream closed",
                reference="RFC-XXXX Section 8.5",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0xE005": IANARegistryEntry(
                code=0xE005,
                name="FRAME_SIZE_ERROR",
                description="Frame size error",
                reference="RFC-XXXX Section 8.6",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.CRITICAL
            ),
            "0xE006": IANARegistryEntry(
                code=0xE006,
                name="REFUSED_STREAM",
                description="Stream refused",
                reference="RFC-XXXX Section 8.7",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0xE007": IANARegistryEntry(
                code=0xE007,
                name="CANCEL",
                description="Stream cancelled",
                reference="RFC-XXXX Section 8.8",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0xE008": IANARegistryEntry(
                code=0xE008,
                name="COMPRESSION_ERROR",
                description="Compression error",
                reference="RFC-XXXX Section 8.9",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0xE009": IANARegistryEntry(
                code=0xE009,
                name="CONNECT_ERROR",
                description="Connection error",
                reference="RFC-XXXX Section 8.10",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.CRITICAL
            ),
            "0xE00A": IANARegistryEntry(
                code=0xE00A,
                name="ENHANCE_YOUR_CALM",
                description="Excessive load",
                reference="RFC-XXXX Section 8.11",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0xE00B": IANARegistryEntry(
                code=0xE00B,
                name="INADEQUATE_SECURITY",
                description="Inadequate security",
                reference="RFC-XXXX Section 8.12",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.CRITICAL
            ),
            "0xE00C": IANARegistryEntry(
                code=0xE00C,
                name="HTTP_1_1_REQUIRED",
                description="HTTP/1.1 required",
                reference="RFC-XXXX Section 8.13",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.CRITICAL
            )
        }
        
        self.registries[RegistryType.ERROR_CODES] = IANARegistry(
            registry_name="µACP Error Codes",
            reference="RFC-XXXX (µACP Protocol)",
            registration_procedure="Standards Action",
            note="Error codes for the Micro Agent Communication Protocol",
            ranges=[
                {
                    'range': '0xE000-0xE00F',
                    'description': 'Standard error codes',
                    'reference': 'RFC-XXXX Section 8'
                },
                {
                    'range': '0xE010-0xEFFF',
                    'description': 'Reserved for future use',
                    'reference': 'RFC-XXXX Section 8'
                }
            ],
            entries=entries
        )
    
    def _init_feature_codes_registry(self):
        """Initialize feature codes registry."""
        entries = {
            "0xF000": IANARegistryEntry(
                code=0xF000,
                name="BRIDGING",
                description="Protocol bridging support",
                reference="RFC-XXXX Section 9.1",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0xF001": IANARegistryEntry(
                code=0xF001,
                name="MONITORING",
                description="Monitoring and metrics support",
                reference="RFC-XXXX Section 9.2",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0xF002": IANARegistryEntry(
                code=0xF002,
                name="STREAMING",
                description="Streaming data support",
                reference="RFC-XXXX Section 9.3",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0xF003": IANARegistryEntry(
                code=0xF003,
                name="COMPRESSION",
                description="Data compression support",
                reference="RFC-XXXX Section 9.4",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0xF004": IANARegistryEntry(
                code=0xF004,
                name="ENCRYPTION",
                description="End-to-end encryption support",
                reference="RFC-XXXX Section 9.5",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.CRITICAL
            ),
            "0xF005": IANARegistryEntry(
                code=0xF005,
                name="SIGNING",
                description="Digital signature support",
                reference="RFC-XXXX Section 9.6",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.CRITICAL
            ),
            "0xF006": IANARegistryEntry(
                code=0xF006,
                name="PRIORITY",
                description="Message priority support",
                reference="RFC-XXXX Section 9.7",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            ),
            "0xF007": IANARegistryEntry(
                code=0xF007,
                name="QOS2",
                description="QoS level 2 (exactly-once) support",
                reference="RFC-XXXX Section 9.8",
                registration_procedure="Standards Action",
                criticality=ExtensionCriticality.ELECTIVE
            )
        }
        
        self.registries[RegistryType.FEATURE_CODES] = IANARegistry(
            registry_name="µACP Feature Codes",
            reference="RFC-XXXX (µACP Protocol)",
            registration_procedure="Standards Action",
            note="Feature codes for the Micro Agent Communication Protocol",
            ranges=[
                {
                    'range': '0xF000-0xF00F',
                    'description': 'Standard feature codes',
                    'reference': 'RFC-XXXX Section 9'
                },
                {
                    'range': '0xF010-0xFFFF',
                    'description': 'Vendor-specific features',
                    'reference': 'RFC-XXXX Section 9'
                }
            ],
            entries=entries
        )
    
    def get_registry(self, registry_type: RegistryType) -> Optional[IANARegistry]:
        """Get specific registry."""
        return self.registries.get(registry_type)
    
    def get_all_registries(self) -> Dict[RegistryType, IANARegistry]:
        """Get all registries."""
        return self.registries.copy()
    
    def get_registry_entry(self, registry_type: RegistryType, code: int) -> Optional[IANARegistryEntry]:
        """Get specific registry entry."""
        registry = self.get_registry(registry_type)
        if not registry:
            return None
        
        return registry.entries.get(f"0x{code:02X}")
    
    def export_registry_markdown(self, registry_type: RegistryType) -> str:
        """Export registry as Markdown."""
        registry = self.get_registry(registry_type)
        if not registry:
            return f"Registry {registry_type.value} not found"
        
        lines = [
            f"# {registry.registry_name}",
            "",
            f"**Reference:** {registry.reference}",
            f"**Registration Procedure:** {registry.registration_procedure}",
            f"**Note:** {registry.note}",
            "",
            "## Ranges",
            ""
        ]
        
        for range_info in registry.ranges:
            lines.append(f"- **{range_info['range']}:** {range_info['description']} ({range_info['reference']})")
        
        lines.extend([
            "",
            "## Entries",
            "",
            "| Code | Name | Description | Reference | Criticality |",
            "|------|------|-------------|-----------|-------------|"
        ])
        
        for code, entry in sorted(registry.entries.items()):
            criticality = entry.criticality.value.upper()
            lines.append(
                f"| {code} | {entry.name} | {entry.description} | {entry.reference} | {criticality} |"
            )
        
        return "\n".join(lines)
    
    def export_all_registries_json(self) -> str:
        """Export all registries as JSON."""
        export_data = {
            'iana_registries': {
                'protocol_name': 'µACP (Micro Agent Communication Protocol)',
                'version': '2.0.0',
                'total_registries': len(self.registries),
                'registries': {}
            }
        }
        
        for registry_type, registry in self.registries.items():
            export_data['iana_registries']['registries'][registry_type.value] = {
                'registry_name': registry.registry_name,
                'reference': registry.reference,
                'registration_procedure': registry.registration_procedure,
                'note': registry.note,
                'ranges': registry.ranges,
                'total_entries': len(registry.entries),
                'entries': {}
            }
            
            for code, entry in registry.entries.items():
                export_data['iana_registries']['registries'][registry_type.value]['entries'][code] = {
                    'name': entry.name,
                    'description': entry.description,
                    'reference': entry.reference,
                    'criticality': entry.criticality.value,
                    'deprecated': entry.deprecated,
                    'replacement': entry.replacement,
                    'notes': entry.notes
                }
        
        return json.dumps(export_data, indent=2)


class ExtensionMechanism:
    """Extension mechanism for µACP."""
    
    def __init__(self):
        self.extensions: Dict[str, Dict[str, Any]] = {}
        self.feature_detection: Dict[str, bool] = {}
    
    def register_extension(self, name: str, version: str, 
                          criticality: ExtensionCriticality,
                          description: str, 
                          implementation: Any = None) -> bool:
        """Register a new extension."""
        try:
            self.extensions[name] = {
                'name': name,
                'version': version,
                'criticality': criticality.value,
                'description': description,
                'implementation': implementation,
                'registered_at': time.time()
            }
            
            print(f"✅ Extension registered: {name} v{version}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to register extension {name}: {e}")
            return False
    
    def unregister_extension(self, name: str) -> bool:
        """Unregister an extension."""
        if name in self.extensions:
            del self.extensions[name]
            print(f"🗑️  Extension unregistered: {name}")
            return True
        return False
    
    def get_extension(self, name: str) -> Optional[Dict[str, Any]]:
        """Get extension information."""
        return self.extensions.get(name)
    
    def list_extensions(self) -> List[str]:
        """List all registered extensions."""
        return list(self.extensions.keys())
    
    def detect_features(self, agent_capabilities: Dict[str, Any]) -> Dict[str, bool]:
        """Detect supported features from agent capabilities."""
        features = {}
        
        # Check for bridging support
        features['bridging'] = 'bridges' in agent_capabilities.get('supported_features', [])
        
        # Check for monitoring support
        features['monitoring'] = 'monitoring' in agent_capabilities.get('supported_features', [])
        
        # Check for streaming support
        features['streaming'] = 'streaming' in agent_capabilities.get('supported_features', [])
        
        # Check for compression support
        features['compression'] = 'compression' in agent_capabilities.get('supported_features', [])
        
        # Check for encryption support
        features['encryption'] = 'ENCRYPTED' in agent_capabilities.get('supported_security_levels', [])
        
        # Check for signing support
        features['signing'] = 'SIGNED' in agent_capabilities.get('supported_security_levels', [])
        
        # Check for priority support
        features['priority'] = 'priority' in agent_capabilities.get('supported_features', [])
        
        # Check for QoS2 support
        features['qos2'] = 2 in agent_capabilities.get('supported_qos', [])
        
        self.feature_detection = features
        return features
    
    def negotiate_features(self, local_features: Dict[str, bool], 
                         remote_features: Dict[str, bool]) -> Dict[str, bool]:
        """Negotiate common features between agents."""
        negotiated = {}
        
        for feature in local_features:
            if feature in remote_features:
                # Both agents support the feature
                negotiated[feature] = local_features[feature] and remote_features[feature]
            else:
                # Remote agent doesn't support the feature
                negotiated[feature] = False
        
        return negotiated
    
    def get_extension_summary(self) -> Dict[str, Any]:
        """Get summary of all extensions."""
        summary = {
            'total_extensions': len(self.extensions),
            'by_criticality': {},
            'extensions': {}
        }
        
        # Count by criticality
        for ext in self.extensions.values():
            criticality = ext['criticality']
            summary['by_criticality'][criticality] = summary['by_criticality'].get(criticality, 0) + 1
        
        # Extension details
        for name, ext in self.extensions.items():
            summary['extensions'][name] = {
                'version': ext['version'],
                'criticality': ext['criticality'],
                'description': ext['description']
            }
        
        return summary


# Global instances
iana_registry = UACPIANARegistry()
extension_mechanism = ExtensionMechanism()


def get_iana_registry(registry_type: RegistryType) -> Optional[IANARegistry]:
    """Get IANA registry."""
    return iana_registry.get_registry(registry_type)


def get_registry_entry(registry_type: RegistryType, code: int) -> Optional[IANARegistryEntry]:
    """Get registry entry."""
    return iana_registry.get_registry_entry(registry_type, code)


def export_registry_markdown(registry_type: RegistryType) -> str:
    """Export registry as Markdown."""
    return iana_registry.export_registry_markdown(registry_type)


def export_all_registries_json() -> str:
    """Export all registries as JSON."""
    return iana_registry.export_all_registries_json()


def register_extension(name: str, version: str, criticality: ExtensionCriticality,
                      description: str, implementation: Any = None) -> bool:
    """Register extension."""
    return extension_mechanism.register_extension(name, version, criticality, description, implementation)


def detect_features(agent_capabilities: Dict[str, Any]) -> Dict[str, bool]:
    """Detect supported features."""
    return extension_mechanism.detect_features(agent_capabilities)
