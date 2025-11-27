"""
µACP Interoperability Profiles

Implements:
- µACP-Core profile (tiny header, UDP+DTLS, CBOR only, QoS0/1)
- µACP-Agent profile (full Conv-ID, Corr-ID, OBSERVE, priority, bridging)
- MUST-support requirements for each profile
- Profile validation and compatibility checking
"""

import json
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from .protocol import UACPVerb, UACPOptionType, UACPContentType
from .layers import TransportBinding
from .security import SecurityLevel, AuthMethod


class ProfileType(Enum):
    """µACP profile types."""
    CORE = "core"
    AGENT = "agent"


class ProfileFeature(Enum):
    """Profile features."""
    # Core features
    BASIC_VERBS = "basic_verbs"
    SIMPLE_OPTIONS = "simple_options"
    UDP_TRANSPORT = "udp_transport"
    DTLS_SECURITY = "dtls_security"
    CBOR_CONTENT = "cbor_content"
    QOS_0_1 = "qos_0_1"
    
    # Agent features
    FULL_VERBS = "full_verbs"
    ALL_OPTIONS = "all_options"
    MULTI_TRANSPORT = "multi_transport"
    TLS_SECURITY = "tls_security"
    MULTI_CONTENT = "multi_content"
    QOS_2 = "qos_2"
    PRIORITY = "priority"
    BRIDGING = "bridging"
    MONITORING = "monitoring"


@dataclass
class ProfileRequirement:
    """Profile requirement specification."""
    feature: ProfileFeature
    mandatory: bool
    description: str
    min_version: str
    alternatives: List[str] = field(default_factory=list)


@dataclass
class ProfileSpecification:
    """Complete profile specification."""
    profile_type: ProfileType
    name: str
    version: str
    description: str
    target_use_cases: List[str]
    requirements: List[ProfileRequirement]
    transport_bindings: List[TransportBinding]
    security_levels: List[SecurityLevel]
    auth_methods: List[AuthMethod]
    content_types: List[UACPContentType]
    qos_levels: List[int]
    max_payload_size: int
    max_options: int
    features: List[str] = field(default_factory=list)


class UACPCoreProfile(ProfileSpecification):
    """µACP-Core profile for embedded/constrained devices."""
    
    def __init__(self):
        super().__init__(
            profile_type=ProfileType.CORE,
            name="µACP-Core",
            version="2.0.0",
            description="Lightweight profile for resource-constrained devices",
            target_use_cases=[
                "IoT sensors and actuators",
                "Embedded systems",
                "Constrained networks",
                "Battery-powered devices"
            ],
            requirements=[
                ProfileRequirement(
                    feature=ProfileFeature.BASIC_VERBS,
                    mandatory=True,
                    description="Must support PING and TELL verbs",
                    min_version="2.0.0"
                ),
                ProfileRequirement(
                    feature=ProfileFeature.SIMPLE_OPTIONS,
                    mandatory=True,
                    description="Must support Topic-Path and Content-Type options",
                    min_version="2.0.0"
                ),
                ProfileRequirement(
                    feature=ProfileFeature.UDP_TRANSPORT,
                    mandatory=True,
                    description="Must support UDP transport binding",
                    min_version="2.0.0"
                ),
                ProfileRequirement(
                    feature=ProfileFeature.DTLS_SECURITY,
                    mandatory=True,
                    description="Must support DTLS for security",
                    min_version="2.0.0"
                ),
                ProfileRequirement(
                    feature=ProfileFeature.CBOR_CONTENT,
                    mandatory=True,
                    description="Must support CBOR content type",
                    min_version="2.0.0"
                ),
                ProfileRequirement(
                    feature=ProfileFeature.QOS_0_1,
                    mandatory=True,
                    description="Must support QoS 0 and 1",
                    min_version="2.0.0"
                )
            ],
            transport_bindings=[TransportBinding.UDP, TransportBinding.UDP_DTLS],
            security_levels=[SecurityLevel.BASIC, SecurityLevel.ENCRYPTED],
            auth_methods=[AuthMethod.HMAC],
            content_types=[UACPContentType.CBOR],
            qos_levels=[0, 1],
            max_payload_size=1024,
            max_options=2,
            features=[
                "basic_verbs",
                "simple_options", 
                "udp_transport",
                "dtls_security",
                "cbor_content",
                "qos_0_1"
            ]
        )


class UACPAgentProfile(ProfileSpecification):
    """µACP-Agent profile for full-featured agents."""
    
    def __init__(self):
        super().__init__(
            profile_type=ProfileType.AGENT,
            name="µACP-Agent",
            version="2.0.0",
            description="Full-featured profile for agent systems",
            target_use_cases=[
                "Multi-agent systems",
                "Edge computing nodes",
                "Cloud services",
                "Research platforms",
                "Enterprise deployments"
            ],
            requirements=[
                ProfileRequirement(
                    feature=ProfileFeature.FULL_VERBS,
                    mandatory=True,
                    description="Must support all verbs: PING, TELL, ASK, OBSERVE",
                    min_version="2.0.0"
                ),
                ProfileRequirement(
                    feature=ProfileFeature.ALL_OPTIONS,
                    mandatory=True,
                    description="Must support all option types",
                    min_version="2.0.0"
                ),
                ProfileRequirement(
                    feature=ProfileFeature.MULTI_TRANSPORT,
                    mandatory=True,
                    description="Must support UDP, TCP, and WebSocket",
                    min_version="2.0.0"
                ),
                ProfileRequirement(
                    feature=ProfileFeature.TLS_SECURITY,
                    mandatory=True,
                    description="Must support TLS and advanced security",
                    min_version="2.0.0"
                ),
                ProfileRequirement(
                    feature=ProfileFeature.MULTI_CONTENT,
                    mandatory=True,
                    description="Must support CBOR, JSON, and Protobuf",
                    min_version="2.0.0"
                ),
                ProfileRequirement(
                    feature=ProfileFeature.QOS_2,
                    mandatory=True,
                    description="Must support QoS 2 (exactly-once)",
                    min_version="2.0.0"
                ),
                ProfileRequirement(
                    feature=ProfileFeature.PRIORITY,
                    mandatory=True,
                    description="Must support priority options",
                    min_version="2.0.0"
                ),
                ProfileRequirement(
                    feature=ProfileFeature.BRIDGING,
                    mandatory=True,
                    description="Must support protocol bridges",
                    min_version="2.0.0"
                ),
                ProfileRequirement(
                    feature=ProfileFeature.MONITORING,
                    mandatory=True,
                    description="Must support monitoring and metrics",
                    min_version="2.0.0"
                )
            ],
            transport_bindings=[
                TransportBinding.UDP, 
                TransportBinding.UDP_DTLS,
                TransportBinding.TCP,
                TransportBinding.TCP_TLS,
                TransportBinding.WEBSOCKET
            ],
            security_levels=[
                SecurityLevel.BASIC,
                SecurityLevel.ENCRYPTED,
                SecurityLevel.SIGNED,
                SecurityLevel.TLS
            ],
            auth_methods=[
                AuthMethod.HMAC,
                AuthMethod.JWT,
                AuthMethod.OAUTH2,
                AuthMethod.CERTIFICATE,
                AuthMethod.API_KEY
            ],
            content_types=[
                UACPContentType.CBOR,
                UACPContentType.JSON,
                UACPContentType.PROTOBUF,
                UACPContentType.TEXT
            ],
            qos_levels=[0, 1, 2],
            max_payload_size=65535,
            max_options=16,
            features=[
                "full_verbs",
                "all_options",
                "multi_transport",
                "tls_security",
                "multi_content",
                "qos_2",
                "priority",
                "bridging",
                "monitoring"
            ]
        )


class ProfileValidator:
    """Validates agent capabilities against profile requirements."""
    
    def __init__(self):
        self.profiles = {
            ProfileType.CORE: UACPCoreProfile(),
            ProfileType.AGENT: UACPAgentProfile()
        }
    
    def validate_agent(self, agent_capabilities: Dict[str, Any], 
                      target_profile: ProfileType) -> Dict[str, Any]:
        """Validate agent capabilities against target profile."""
        profile = self.profiles[target_profile]
        
        validation_result = {
            'profile': profile.name,
            'compatible': True,
            'missing_requirements': [],
            'optional_features': [],
            'validation_details': {}
        }
        
        # Check each requirement
        for requirement in profile.requirements:
            if requirement.mandatory:
                if not self._check_requirement(agent_capabilities, requirement):
                    validation_result['compatible'] = False
                    validation_result['missing_requirements'].append({
                        'feature': requirement.feature.value,
                        'description': requirement.description
                    })
        
        # Check optional features
        for feature in profile.features:
            if feature not in agent_capabilities.get('supported_features', []):
                validation_result['optional_features'].append(feature)
        
        # Detailed validation
        validation_result['validation_details'] = {
            'transport_bindings': self._validate_transport_bindings(
                agent_capabilities, profile
            ),
            'security_levels': self._validate_security_levels(
                agent_capabilities, profile
            ),
            'auth_methods': self._validate_auth_methods(
                agent_capabilities, profile
            ),
            'content_types': self._validate_content_types(
                agent_capabilities, profile
            ),
            'qos_levels': self._validate_qos_levels(
                agent_capabilities, profile
            ),
            'payload_size': self._validate_payload_size(
                agent_capabilities, profile
            )
        }
        
        return validation_result
    
    def _check_requirement(self, capabilities: Dict[str, Any], 
                          requirement: ProfileRequirement) -> bool:
        """Check if a specific requirement is met."""
        feature = requirement.feature
        
        if feature == ProfileFeature.BASIC_VERBS:
            supported_verbs = capabilities.get('supported_verbs', [])
            return all(verb in supported_verbs for verb in ['PING', 'TELL'])
        
        elif feature == ProfileFeature.FULL_VERBS:
            supported_verbs = capabilities.get('supported_verbs', [])
            return all(verb in supported_verbs for verb in ['PING', 'TELL', 'ASK', 'OBSERVE'])
        
        elif feature == ProfileFeature.UDP_TRANSPORT:
            transport_bindings = capabilities.get('supported_transport_bindings', [])
            return any(binding in transport_bindings for binding in ['UDP', 'udp'])
        
        elif feature == ProfileFeature.DTLS_SECURITY:
            security_levels = capabilities.get('supported_security_levels', [])
            return any(level in security_levels for level in ['BASIC', 'ENCRYPTED'])
        
        elif feature == ProfileFeature.CBOR_CONTENT:
            content_types = capabilities.get('supported_content_types', [])
            return 'CBOR' in content_types
        
        elif feature == ProfileFeature.QOS_0_1:
            qos_levels = capabilities.get('supported_qos', [])
            return all(qos in qos_levels for qos in [0, 1])
        
        elif feature == ProfileFeature.QOS_2:
            qos_levels = capabilities.get('supported_qos', [])
            return 2 in qos_levels
        
        elif feature == ProfileFeature.BRIDGING:
            features = capabilities.get('supported_features', [])
            return 'bridges' in features
        
        elif feature == ProfileFeature.MONITORING:
            features = capabilities.get('supported_features', [])
            return 'monitoring' in features
        
        return True
    
    def _validate_transport_bindings(self, capabilities: Dict[str, Any], 
                                   profile: ProfileSpecification) -> Dict[str, Any]:
        """Validate transport binding compatibility."""
        supported = capabilities.get('supported_transport_bindings', [])
        required = [binding.value for binding in profile.transport_bindings]
        
        return {
            'supported': supported,
            'required': required,
            'compatible': all(binding in supported for binding in required),
            'missing': [binding for binding in required if binding not in supported]
        }
    
    def _validate_security_levels(self, capabilities: Dict[str, Any], 
                                profile: ProfileSpecification) -> Dict[str, Any]:
        """Validate security level compatibility."""
        supported = capabilities.get('supported_security_levels', [])
        required = [level.value for level in profile.security_levels]
        
        return {
            'supported': supported,
            'required': required,
            'compatible': all(level in supported for level in required),
            'missing': [level for level in required if level not in supported]
        }
    
    def _validate_auth_methods(self, capabilities: Dict[str, Any], 
                             profile: ProfileSpecification) -> Dict[str, Any]:
        """Validate authentication method compatibility."""
        supported = capabilities.get('supported_auth_methods', [])
        required = [method.value for method in profile.auth_methods]
        
        return {
            'supported': supported,
            'required': required,
            'compatible': all(method in supported for method in required),
            'missing': [method for method in required if method not in supported]
        }
    
    def _validate_content_types(self, capabilities: Dict[str, Any], 
                              profile: ProfileSpecification) -> Dict[str, Any]:
        """Validate content type compatibility."""
        supported = capabilities.get('supported_content_types', [])
        required = [ct.value for ct in profile.content_types]
        
        return {
            'supported': supported,
            'required': required,
            'compatible': all(ct in supported for ct in required),
            'missing': [ct for ct in required if ct not in supported]
        }
    
    def _validate_qos_levels(self, capabilities: Dict[str, Any], 
                           profile: ProfileSpecification) -> Dict[str, Any]:
        """Validate QoS level compatibility."""
        supported = capabilities.get('supported_qos', [])
        required = profile.qos_levels
        
        return {
            'supported': supported,
            'required': required,
            'compatible': all(qos in supported for qos in required),
            'missing': [qos for qos in required if qos not in supported]
        }
    
    def _validate_payload_size(self, capabilities: Dict[str, Any], 
                             profile: ProfileSpecification) -> Dict[str, Any]:
        """Validate payload size compatibility."""
        max_size = capabilities.get('max_payload_size', 0)
        required_size = profile.max_payload_size
        
        return {
            'supported': max_size,
            'required': required_size,
            'compatible': max_size >= required_size,
            'sufficient': max_size >= required_size
        }
    
    def get_profile_summary(self) -> Dict[str, Any]:
        """Get summary of all profiles."""
        summary = {
            'profiles': {},
            'comparison': {}
        }
        
        for profile_type, profile in self.profiles.items():
            summary['profiles'][profile_type.value] = {
                'name': profile.name,
                'version': profile.version,
                'description': profile.description,
                'target_use_cases': profile.target_use_cases,
                'features': profile.features,
                'requirements_count': len(profile.requirements),
                'mandatory_requirements': len([r for r in profile.requirements if r.mandatory])
            }
        
        # Compare profiles
        core_profile = self.profiles[ProfileType.CORE]
        agent_profile = self.profiles[ProfileType.AGENT]
        
        summary['comparison'] = {
            'core_vs_agent': {
                'transport_bindings': {
                    'core': len(core_profile.transport_bindings),
                    'agent': len(agent_profile.transport_bindings)
                },
                'security_levels': {
                    'core': len(core_profile.security_levels),
                    'agent': len(agent_profile.security_levels)
                },
                'auth_methods': {
                    'core': len(core_profile.auth_methods),
                    'agent': len(agent_profile.auth_methods)
                },
                'content_types': {
                    'core': len(core_profile.content_types),
                    'agent': len(agent_profile.content_types)
                },
                'qos_levels': {
                    'core': len(core_profile.qos_levels),
                    'agent': len(agent_profile.qos_levels)
                },
                'max_payload_size': {
                    'core': core_profile.max_payload_size,
                    'agent': agent_profile.max_payload_size
                },
                'max_options': {
                    'core': core_profile.max_options,
                    'agent': agent_profile.max_options
                }
            }
        }
        
        return summary
    
    def export_profile_markdown(self, profile_type: ProfileType) -> str:
        """Export profile specification as Markdown."""
        profile = self.profiles[profile_type]
        
        lines = [
            f"# {profile.name} Profile Specification",
            "",
            f"**Version:** {profile.version}",
            f"**Type:** {profile.profile_type.value}",
            "",
            f"## Description",
            f"{profile.description}",
            "",
            f"## Target Use Cases",
        ]
        
        for use_case in profile.target_use_cases:
            lines.append(f"- {use_case}")
        
        lines.extend([
            "",
            "## Requirements",
            "",
            "| Feature | Mandatory | Description | Min Version |",
            "|---------|-----------|-------------|-------------|"
        ])
        
        for requirement in profile.requirements:
            mandatory = "Yes" if requirement.mandatory else "No"
            lines.append(
                f"| {requirement.feature.value} | {mandatory} | {requirement.description} | {requirement.min_version} |"
            )
        
        lines.extend([
            "",
            "## Technical Specifications",
            "",
            f"- **Transport Bindings:** {', '.join(binding.value for binding in profile.transport_bindings)}",
            f"- **Security Levels:** {', '.join(level.value for level in profile.security_levels)}",
            f"- **Auth Methods:** {', '.join(method.value for method in profile.auth_methods)}",
            f"- **Content Types:** {', '.join(ct.value for ct in profile.content_types)}",
            f"- **QoS Levels:** {', '.join(map(str, profile.qos_levels))}",
            f"- **Max Payload Size:** {profile.max_payload_size} bytes",
            f"- **Max Options:** {profile.max_options}",
            "",
            "## Features",
        ])
        
        for feature in profile.features:
            lines.append(f"- {feature}")
        
        return "\n".join(lines)


# Global profile validator instance
profile_validator = ProfileValidator()


def validate_agent_profile(agent_capabilities: Dict[str, Any], 
                          target_profile: ProfileType) -> Dict[str, Any]:
    """Validate agent capabilities against target profile."""
    return profile_validator.validate_agent(agent_capabilities, target_profile)


def get_profile_specification(profile_type: ProfileType) -> ProfileSpecification:
    """Get profile specification."""
    return profile_validator.profiles[profile_type]


def get_profile_summary() -> Dict[str, Any]:
    """Get summary of all profiles."""
    return profile_validator.get_profile_summary()
