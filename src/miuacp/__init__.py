"""
µACP (Micro Agent Communication Protocol) Library

A lightweight, agent-centric communication protocol for edge-native multi-agent systems.

Version: 1.0.0
Author: Arnab
License: MIT
"""

# Core protocol components
from .protocol import (
    UACPMessage, UACPHeader, UACPOption, UACPOptionType,
    UACPVerb, UACPContentType, UACPProtocol
)

# Client and server components
from .client import UACPClient
from .server import UACPServer
from .agent import UACPAgent
from .discovery import UACPDiscovery

# Transport layer
from .transport import (
    UACPTransport, TransportConfig, TransportType, ConnectionInfo
)

# Security framework
from .security import (
    UACPSecurity, SecurityConfig, SecurityContext, SecurityLevel, AuthMethod
)

# Protocol bridges
from .bridges import (
    UACPBridge, MQTTBridge, CoAPBridge, MCPBridge, BridgeManager, BridgeConfig, BridgeType
)

# Monitoring and debugging
from .monitoring import (
    UACPMonitoring, MetricsCollector, HealthMonitor, AlertManager, DebugLogger,
    Metric, Alert, HealthStatus, MetricType, AlertLevel
)

# RFC Compliance Components
from .layers import (
    UACPLayer, TransportLayer, MessageLayer, SemanticLayer, UACPLayerStack,
    LayerConfig, LayerType, TransportBinding
)

from .negotiation import (
    UACPNegotiation, CapabilityDiscovery, AgentCapabilities, NegotiationResult,
    CapabilityType, NegotiationState
)

from .status_codes import (
    UACPStatusCodes, StatusCodeCategory, StatusCodeInfo, UACPStatusCodeRegistry,
    get_status_code, is_success, is_client_error, is_server_error, is_negotiation
)

from .state_machines import (
    UACPStateMachine, ASKStateMachine, OBSERVEStateMachine, QoS2StateMachine,
    StateMachineManager, VerbState, StateTransition, StateMachineContext, StateTransitionEvent
)

from .profiles import (
    UACPCoreProfile, UACPAgentProfile, ProfileValidator, ProfileType, ProfileFeature,
    ProfileRequirement, ProfileSpecification, validate_agent_profile, get_profile_specification
)

from .iana_registry import (
    UACPIANARegistry, ExtensionMechanism, RegistryType, ExtensionCriticality,
    IANARegistry, IANARegistryEntry, get_iana_registry, get_registry_entry,
    export_registry_markdown, export_all_registries_json, register_extension, detect_features
)

from .congestion import (
    UACPCongestionControl, ResourceManager, TokenBucket, CongestionState, RateLimitPolicy,
    CongestionMetrics, RateLimitConfig, get_congestion_control, get_resource_manager, calculate_backoff
)

# Memory state components
from .routing import (
    UACPRouting, NeighborInfo, MulticastGroup, RouteEntry,
    RouteType, NATState
)
from .subscriptions import (
    UACPSubscriptions, Subscription, Dialogue, Correlation, Contract,
    SubscriptionState, DialogueState, CorrelationState, ContractState
)
from .reliability import (
    UACPReliability, MessageTracker, ACKTimer, ReassemblyBuffer, SlidingWindow,
    QoSLevel, MessageState, ReassemblyState
)
from .timers import (
    UACPTimers, Timer, ScheduledMessage, SessionTimer,
    TimerType, TimerState, MessagePriority
)
from .broker import (
    UACPBroker, TopicNode, RetainedMessage, FlowControlCredit, LoadBalancerTarget,
    ConnectionMapping, BrokerNodeType, MessageRetention, LoadBalancerStrategy
)
from .instrumentation import (
    UACPInstrumentation, LogEntry, Metric,
    LogLevel, MetricType, PolicyType
)
from .resources import (
    UACPResources, ResourceHandle, SocketResource, DMABuffer, CryptoContext,
    StorageHandle, ResourceType, ResourceState
)

# Robustness Components
from .circuit_breaker import (
    CircuitBreaker, CircuitBreakerManager, CircuitBreakerConfig, CircuitBreakerMetrics,
    CircuitState
)
from .adaptive_timeout import (
    AdaptiveTimeout, TimeoutManager, TimeoutConfig, TimeoutHistory,
    TimeoutStrategy
)
from .resource_pool import (
    ResourcePool, PoolManager, PoolConfig, PoolMetrics, PooledResource,
    PoolState
)
from .error_recovery import (
    RetryManager, ErrorRecoveryManager, RobustnessManager, RetryConfig,
    ErrorContext, RecoveryAction, RetryStrategy, ErrorSeverity,
    retry_on_error
)
from .health_monitoring import (
    HealthMonitor, HealthCheck, HealthCheckResult, SystemMetrics,
    PerformanceProfile, HealthStatus, CheckType
)

# Utility functions
from .utils import UACPUtils, validate_message, debug_message, estimate_size

# Version information
__version__ = "1.0.0"
__author__ = "Arnab"
__email__ = "hello@arnab.wiki"
__license__ = "MIT"

# Library description
__description__ = "µACP: A lightweight agent communication protocol for edge-native multi-agent systems"

# All exported components
__all__ = [
    # Core protocol
    'UACPMessage', 'UACPHeader', 'UACPOption', 'UACPOptionType',
    'UACPVerb', 'UACPContentType', 'UACPProtocol',
    
    # Client/Server/Agent
    'UACPClient', 'UACPServer', 'UACPAgent', 'UACPDiscovery',
    
    # Transport layer
    'UACPTransport', 'TransportConfig', 'TransportType', 'ConnectionInfo',
    
    # Security framework
    'UACPSecurity', 'SecurityConfig', 'SecurityContext', 'SecurityLevel', 'AuthMethod',
    
    # Protocol bridges
    'UACPBridge', 'MQTTBridge', 'CoAPBridge', 'MCPBridge', 'BridgeManager', 'BridgeConfig', 'BridgeType',
    
    # Monitoring and debugging
    'UACPMonitoring', 'MetricsCollector', 'HealthMonitor', 'AlertManager', 'DebugLogger',
    'Metric', 'Alert', 'HealthStatus', 'MetricType', 'AlertLevel',
    
    # RFC Compliance - Protocol Layering
    'UACPLayer', 'TransportLayer', 'MessageLayer', 'SemanticLayer', 'UACPLayerStack',
    'LayerConfig', 'LayerType', 'TransportBinding',
    
    # RFC Compliance - Negotiation & Capability Discovery
    'UACPNegotiation', 'CapabilityDiscovery', 'AgentCapabilities', 'NegotiationResult',
    'CapabilityType', 'NegotiationState',
    
    # RFC Compliance - Status Codes Registry
    'UACPStatusCodes', 'StatusCodeCategory', 'StatusCodeInfo', 'UACPStatusCodeRegistry',
    'get_status_code', 'is_success', 'is_client_error', 'is_server_error', 'is_negotiation',
    
    # RFC Compliance - State Machines & Formal Semantics
    'UACPStateMachine', 'ASKStateMachine', 'OBSERVEStateMachine', 'QoS2StateMachine',
    'StateMachineManager', 'VerbState', 'StateTransition', 'StateMachineContext', 'StateTransitionEvent',
    
    # RFC Compliance - Interoperability Profiles
    'UACPCoreProfile', 'UACPAgentProfile', 'ProfileValidator', 'ProfileType', 'ProfileFeature',
    'ProfileRequirement', 'ProfileSpecification', 'validate_agent_profile', 'get_profile_specification',
    
    # RFC Compliance - IANA Registry & Extensions
    'UACPIANARegistry', 'ExtensionMechanism', 'RegistryType', 'ExtensionCriticality',
    'IANARegistry', 'IANARegistryEntry', 'get_iana_registry', 'get_registry_entry',
    'export_registry_markdown', 'export_all_registries_json', 'register_extension', 'detect_features',
    
    # RFC Compliance - Resource & Congestion Control
    'UACPCongestionControl', 'ResourceManager', 'TokenBucket', 'CongestionState', 'RateLimitPolicy',
    'CongestionMetrics', 'RateLimitConfig', 'get_congestion_control', 'get_resource_manager', 'calculate_backoff',
    
    # Memory State Components - Routing & Addressing
    'UACPRouting', 'NeighborInfo', 'MulticastGroup', 'RouteEntry', 'RouteType', 'NATState',
    
    # Memory State Components - Subscriptions & Dialogues
    'UACPSubscriptions', 'Subscription', 'Dialogue', 'Correlation', 'Contract',
    'SubscriptionState', 'DialogueState', 'CorrelationState', 'ContractState',
    
    # Memory State Components - Reliability & QoS
    'UACPReliability', 'MessageTracker', 'ACKTimer', 'ReassemblyBuffer', 'SlidingWindow',
    'QoSLevel', 'MessageState', 'ReassemblyState',
    
    # Memory State Components - Timers & Scheduling
    'UACPTimers', 'Timer', 'ScheduledMessage', 'SessionTimer',
    'TimerType', 'TimerState', 'MessagePriority',
    
    # Memory State Components - Broker & Middleware
    'UACPBroker', 'TopicNode', 'RetainedMessage', 'FlowControlCredit', 'LoadBalancerTarget',
    'ConnectionMapping', 'BrokerNodeType', 'MessageRetention', 'LoadBalancerStrategy',
    
    # Memory State Components - Instrumentation & Control
    'UACPInstrumentation', 'LogEntry', 'Metric', 'LogLevel', 'MetricType', 'PolicyType',
    
    # Memory State Components - Resource Binding
    'UACPResources', 'ResourceHandle', 'SocketResource', 'DMABuffer', 'CryptoContext',
    'StorageHandle', 'ResourceType', 'ResourceState',
    
    # Robustness Components - Circuit Breaker
    'CircuitBreaker', 'CircuitBreakerManager', 'CircuitBreakerConfig', 'CircuitBreakerMetrics',
    'CircuitState',
    
    # Robustness Components - Adaptive Timeout
    'AdaptiveTimeout', 'TimeoutManager', 'TimeoutConfig', 'TimeoutHistory',
    'TimeoutStrategy',
    
    # Robustness Components - Resource Pooling
    'ResourcePool', 'PoolManager', 'PoolConfig', 'PoolMetrics', 'PooledResource',
    'PoolState',
    
    # Robustness Components - Error Recovery
    'RetryManager', 'ErrorRecoveryManager', 'RobustnessManager', 'RetryConfig',
    'ErrorContext', 'RecoveryAction', 'RetryStrategy', 'ErrorSeverity',
    'retry_on_error',
    
    # Robustness Components - Health Monitoring
    'HealthMonitor', 'HealthCheck', 'HealthCheckResult', 'SystemMetrics',
    'PerformanceProfile', 'HealthStatus', 'CheckType',
    
    # Utilities
    'UACPUtils', 'validate_message', 'debug_message', 'estimate_size',
    
    # Version info
    '__version__', '__author__', '__email__', '__license__', '__description__'
]

# RFC Compliance Status
RFC_COMPLIANCE_STATUS = {
    "formal_protocol_layering": "IMPLEMENTED",
    "negotiation_capability_discovery": "IMPLEMENTED", 
    "error_status_codes_registry": "IMPLEMENTED",
    "security_trust_model": "IMPLEMENTED",
    "extension_versioning_mechanism": "IMPLEMENTED",
    "formal_semantics_state_machines": "IMPLEMENTED",
    "interoperability_profiles": "IMPLEMENTED",
    "resource_congestion_control": "IMPLEMENTED",
    "formal_iana_considerations": "IMPLEMENTED",
    "rfc_readiness": "COMPLETE"
}

def get_rfc_compliance_status():
    """Get RFC compliance status."""
    return RFC_COMPLIANCE_STATUS.copy()

def is_rfc_ready():
    """Check if µACP is RFC ready."""
    return all(status == "IMPLEMENTED" for key, status in RFC_COMPLIANCE_STATUS.items() if key != "rfc_readiness")

# Quick start function
def create_agent(agent_id: str, capabilities: dict = None):
    """Quick start function to create a µACP agent."""
    from .agent import UACPAgent
    from .negotiation import AgentCapabilities
    
    if capabilities is None:
        capabilities = AgentCapabilities(agent_id=agent_id)
    
    return UACPAgent(agent_id, capabilities)

def create_client(server_address: str = "localhost", server_port: int = 8080):
    """Quick start function to create a µACP client."""
    from .client import UACPClient
    
    return UACPClient(server_address, server_port)

def create_server(host: str = "0.0.0.0", port: int = 8080):
    """Quick start function to create a µACP server."""
    from .server import UACPServer
    
    return UACPServer(host, port)
