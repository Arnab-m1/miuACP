"""
µACP Negotiation & Capability Discovery

Implements:
- Standard agent handshake protocol
- Capability exchange (verbs, payload size, QoS, auth methods)
- Feature negotiation and compatibility checking
"""

import asyncio
import json
import time
import hashlib
from typing import Dict, List, Optional, Callable, Any, Union, Set
from dataclasses import dataclass, asdict
from enum import Enum
from .protocol import UACPVerb, UACPOptionType, UACPMessage, UACPHeader


class CapabilityType(Enum):
    """Capability types."""
    VERBS = "verbs"
    PAYLOAD_SIZE = "payload_size"
    QOS_LEVELS = "qos_levels"
    AUTH_METHODS = "auth_methods"
    CONTENT_TYPES = "content_types"
    SECURITY_LEVELS = "security_levels"
    TRANSPORT_BINDINGS = "transport_bindings"
    FEATURES = "features"


class NegotiationState(Enum):
    """Negotiation states."""
    INIT = "init"
    CAPABILITIES_EXCHANGED = "capabilities_exchanged"
    FEATURES_NEGOTIATED = "features_negotiated"
    SECURITY_ESTABLISHED = "security_established"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentCapabilities:
    """Agent capabilities structure."""
    agent_id: str
    version: str = "2.0.0"
    supported_verbs: List[str] = None
    max_payload_size: int = 65535
    supported_qos: List[int] = None
    supported_auth_methods: List[str] = None
    supported_content_types: List[str] = None
    supported_security_levels: List[str] = None
    supported_transport_bindings: List[str] = None
    supported_features: List[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.supported_verbs is None:
            self.supported_verbs = ["PING", "TELL", "ASK", "OBSERVE"]
        if self.supported_qos is None:
            self.supported_qos = [0, 1, 2]
        if self.supported_auth_methods is None:
            self.supported_auth_methods = ["HMAC", "JWT"]
        if self.supported_content_types is None:
            self.supported_content_types = ["CBOR", "JSON"]
        if self.supported_security_levels is None:
            self.supported_security_levels = ["BASIC", "ENCRYPTED"]
        if self.supported_transport_bindings is None:
            self.supported_transport_bindings = ["UDP", "TCP"]
        if self.supported_features is None:
            self.supported_features = ["basic", "bridges", "monitoring"]
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentCapabilities':
        """Create from dictionary."""
        return cls(**data)
    
    def get_capability(self, capability_type: CapabilityType) -> Any:
        """Get specific capability."""
        capability_map = {
            CapabilityType.VERBS: self.supported_verbs,
            CapabilityType.PAYLOAD_SIZE: self.max_payload_size,
            CapabilityType.QOS_LEVELS: self.supported_qos,
            CapabilityType.AUTH_METHODS: self.supported_auth_methods,
            CapabilityType.CONTENT_TYPES: self.supported_content_types,
            CapabilityType.SECURITY_LEVELS: self.supported_security_levels,
            CapabilityType.TRANSPORT_BINDINGS: self.supported_transport_bindings,
            CapabilityType.FEATURES: self.supported_features
        }
        return capability_map.get(capability_type)


@dataclass
class NegotiationResult:
    """Negotiation result structure."""
    success: bool
    negotiated_capabilities: Optional[AgentCapabilities] = None
    common_features: List[str] = None
    security_established: bool = False
    error_message: Optional[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.common_features is None:
            self.common_features = []
        if self.timestamp is None:
            self.timestamp = time.time()


class UACPNegotiation:
    """µACP negotiation and capability discovery."""
    
    def __init__(self, local_capabilities: AgentCapabilities):
        self.local_capabilities = local_capabilities
        self.negotiation_state = NegotiationState.INIT
        self.peer_capabilities: Optional[AgentCapabilities] = None
        self.negotiated_features: List[str] = []
        self.negotiation_handlers: Dict[str, Callable] = {}
        
        # Initialize negotiation handlers
        self._init_handlers()
    
    def _init_handlers(self):
        """Initialize negotiation handlers."""
        self.negotiation_handlers['capabilities_exchange'] = self._handle_capabilities_exchange
        self.negotiation_handlers['feature_negotiation'] = self._handle_feature_negotiation
        self.negotiation_handlers['security_establishment'] = self._handle_security_establishment
    
    async def start_negotiation(self, peer_info: Dict[str, Any]) -> NegotiationResult:
        """Start negotiation with peer."""
        try:
            print(f"🤝 Starting negotiation with peer: {peer_info.get('agent_id', 'unknown')}")
            
            # Step 1: Exchange capabilities
            await self._exchange_capabilities(peer_info)
            if self.negotiation_state == NegotiationState.FAILED:
                return NegotiationResult(success=False, error_message="Capabilities exchange failed")
            
            # Step 2: Negotiate features
            await self._negotiate_features()
            if self.negotiation_state == NegotiationState.FAILED:
                return NegotiationResult(success=False, error_message="Feature negotiation failed")
            
            # Step 3: Establish security
            await self._establish_security()
            if self.negotiation_state == NegotiationState.FAILED:
                return NegotiationResult(success=False, error_message="Security establishment failed")
            
            # Negotiation completed successfully
            self.negotiation_state = NegotiationState.COMPLETED
            
            return NegotiationResult(
                success=True,
                negotiated_capabilities=self.peer_capabilities,
                common_features=self.negotiated_features,
                security_established=True
            )
            
        except Exception as e:
            self.negotiation_state = NegotiationState.FAILED
            return NegotiationResult(success=False, error_message=str(e))
    
    async def _exchange_capabilities(self, peer_info: Dict[str, Any]):
        """Exchange capabilities with peer."""
        try:
            print("📋 Exchanging capabilities...")
            
            # Send our capabilities
            await self._send_capabilities(peer_info)
            
            # Receive peer capabilities
            peer_caps = await self._receive_capabilities(peer_info)
            if not peer_caps:
                self.negotiation_state = NegotiationState.FAILED
                return
            
            self.peer_capabilities = peer_caps
            self.negotiation_state = NegotiationState.CAPABILITIES_EXCHANGED
            
            print(f"✅ Capabilities exchanged with {peer_caps.agent_id}")
            
        except Exception as e:
            print(f"❌ Capabilities exchange failed: {e}")
            self.negotiation_state = NegotiationState.FAILED
    
    async def _negotiate_features(self):
        """Negotiate common features."""
        try:
            print("🔧 Negotiating features...")
            
            if not self.peer_capabilities:
                raise ValueError("Peer capabilities not available")
            
            # Find common features
            local_features = set(self.local_capabilities.supported_features)
            peer_features = set(self.peer_capabilities.supported_features)
            common_features = local_features.intersection(peer_features)
            
            # Find common capabilities
            common_verbs = self._find_common_capability(CapabilityType.VERBS)
            common_qos = self._find_common_capability(CapabilityType.QOS_LEVELS)
            common_auth = self._find_common_capability(CapabilityType.AUTH_METHODS)
            common_content = self._find_common_capability(CapabilityType.CONTENT_TYPES)
            common_security = self._find_common_capability(CapabilityType.SECURITY_LEVELS)
            common_transport = self._find_common_capability(CapabilityType.TRANSPORT_BINDINGS)
            
            # Validate minimum requirements
            if not self._validate_minimum_requirements(common_verbs, common_qos, common_auth):
                raise ValueError("Minimum requirements not met")
            
            # Store negotiated features
            self.negotiated_features = list(common_features)
            self.negotiated_features.extend([
                f"verbs:{','.join(common_verbs)}",
                f"qos:{','.join(map(str, common_qos))}",
                f"auth:{','.join(common_auth)}",
                f"content:{','.join(common_content)}",
                f"security:{','.join(common_security)}",
                f"transport:{','.join(common_transport)}"
            ])
            
            self.negotiation_state = NegotiationState.FEATURES_NEGOTIATED
            print(f"✅ Features negotiated: {len(self.negotiated_features)} common features")
            
        except Exception as e:
            print(f"❌ Feature negotiation failed: {e}")
            self.negotiation_state = NegotiationState.FAILED
    
    async def _establish_security(self):
        """Establish security context."""
        try:
            print("🔐 Establishing security...")
            
            # Find common security level
            common_security = self._find_common_capability(CapabilityType.SECURITY_LEVELS)
            if not common_security:
                raise ValueError("No common security levels")
            
            # Find common auth method
            common_auth = self._find_common_capability(CapabilityType.AUTH_METHODS)
            if not common_auth:
                raise ValueError("No common auth methods")
            
            # Establish security context (simplified)
            # In production, this would involve actual key exchange, certificate validation, etc.
            await self._perform_security_handshake(common_auth[0], common_security[0])
            
            self.negotiation_state = NegotiationState.SECURITY_ESTABLISHED
            print(f"✅ Security established: {common_auth[0]} + {common_security[0]}")
            
        except Exception as e:
            print(f"❌ Security establishment failed: {e}")
            self.negotiation_state = NegotiationState.FAILED
    
    def _find_common_capability(self, capability_type: CapabilityType) -> List[Any]:
        """Find common capability between local and peer."""
        local_cap = self.local_capabilities.get_capability(capability_type)
        peer_cap = self.peer_capabilities.get_capability(capability_type)
        
        if isinstance(local_cap, list) and isinstance(peer_cap, list):
            return list(set(local_cap).intersection(set(peer_cap)))
        elif local_cap == peer_cap:
            return [local_cap]
        else:
            return []
    
    def _validate_minimum_requirements(self, verbs: List[str], qos: List[int], auth: List[str]) -> bool:
        """Validate minimum requirements are met."""
        # Must support at least PING and TELL
        if not all(verb in verbs for verb in ["PING", "TELL"]):
            return False
        
        # Must support at least QoS 0
        if 0 not in qos:
            return False
        
        # Must support at least one auth method
        if not auth:
            return False
        
        return True
    
    async def _perform_security_handshake(self, auth_method: str, security_level: str):
        """Perform security handshake (simplified)."""
        # In production, this would implement actual security protocols
        print(f"🔐 Performing {auth_method} + {security_level} handshake...")
        await asyncio.sleep(0.1)  # Simulate handshake time
    
    async def _send_capabilities(self, peer_info: Dict[str, Any]):
        """Send capabilities to peer."""
        # In production, this would send actual µACP messages
        print(f"📤 Sending capabilities to {peer_info.get('agent_id', 'unknown')}")
        await asyncio.sleep(0.1)  # Simulate network delay
    
    async def _receive_capabilities(self, peer_info: Dict[str, Any]) -> Optional[AgentCapabilities]:
        """Receive capabilities from peer."""
        # In production, this would receive actual µACP messages
        print(f"📥 Receiving capabilities from {peer_info.get('agent_id', 'unknown')}")
        await asyncio.sleep(0.1)  # Simulate network delay
        
        # Return mock capabilities for demonstration
        return AgentCapabilities(
            agent_id=peer_info.get('agent_id', 'peer_agent'),
            version="2.0.0",
            supported_verbs=["PING", "TELL", "ASK", "OBSERVE"],
            max_payload_size=32768,
            supported_qos=[0, 1],
            supported_auth_methods=["HMAC", "JWT"],
            supported_content_types=["CBOR", "JSON"],
            supported_security_levels=["BASIC", "ENCRYPTED"],
            supported_transport_bindings=["UDP", "TCP"],
            supported_features=["basic", "monitoring"]
        )
    
    def get_negotiation_status(self) -> Dict[str, Any]:
        """Get current negotiation status."""
        return {
            'state': self.negotiation_state.value,
            'local_capabilities': self.local_capabilities.to_dict(),
            'peer_capabilities': self.peer_capabilities.to_dict() if self.peer_capabilities else None,
            'negotiated_features': self.negotiated_features,
            'timestamp': time.time()
        }
    
    def is_compatible(self, peer_capabilities: AgentCapabilities) -> bool:
        """Check if peer is compatible without full negotiation."""
        try:
            # Quick compatibility check
            common_verbs = self._find_common_capability(CapabilityType.VERBS)
            common_qos = self._find_common_capability(CapabilityType.QOS_LEVELS)
            common_auth = self._find_common_capability(CapabilityType.AUTH_METHODS)
            
            return self._validate_minimum_requirements(common_verbs, common_qos, common_auth)
            
        except Exception:
            return False


class CapabilityDiscovery:
    """Capability discovery service."""
    
    def __init__(self):
        self.known_agents: Dict[str, AgentCapabilities] = {}
        self.discovery_handlers: List[Callable] = []
    
    def register_agent(self, agent_id: str, capabilities: AgentCapabilities):
        """Register agent capabilities."""
        self.known_agents[agent_id] = capabilities
        print(f"📝 Registered agent: {agent_id}")
    
    def unregister_agent(self, agent_id: str):
        """Unregister agent."""
        if agent_id in self.known_agents:
            del self.known_agents[agent_id]
            print(f"🗑️  Unregistered agent: {agent_id}")
    
    def get_agent_capabilities(self, agent_id: str) -> Optional[AgentCapabilities]:
        """Get agent capabilities."""
        return self.known_agents.get(agent_id)
    
    def find_compatible_agents(self, required_features: List[str]) -> List[str]:
        """Find agents with required features."""
        compatible_agents = []
        
        for agent_id, capabilities in self.known_agents.items():
            agent_features = set(capabilities.supported_features)
            required_set = set(required_features)
            
            if required_set.issubset(agent_features):
                compatible_agents.append(agent_id)
        
        return compatible_agents
    
    def get_agent_summary(self) -> Dict[str, Any]:
        """Get summary of all known agents."""
        summary = {
            'total_agents': len(self.known_agents),
            'agents': {}
        }
        
        for agent_id, capabilities in self.known_agents.items():
            summary['agents'][agent_id] = {
                'version': capabilities.version,
                'features': capabilities.supported_features,
                'verbs': capabilities.supported_verbs,
                'qos': capabilities.supported_qos,
                'auth_methods': capabilities.supported_auth_methods
            }
        
        return summary
