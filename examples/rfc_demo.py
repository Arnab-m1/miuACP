#!/usr/bin/env python3
"""
µACP RFC Compliance Demo

Demonstrates all RFC compliance features:
- Formal protocol layering
- Negotiation & capability discovery
- Status codes registry
- State machines
- Interoperability profiles
- IANA registry
- Extension mechanisms
- Congestion control
"""

import asyncio
import time
import json
from uacp_lib import (
    # Core components
    UACPMessage, UACPVerb, UACPContentType,
    
    # RFC Compliance components
    UACPLayerStack, LayerConfig, TransportBinding,
    UACPNegotiation, AgentCapabilities, CapabilityType,
    UACPStatusCodes, StatusCodeCategory,
    ASKStateMachine, StateMachineContext,
    UACPCoreProfile, UACPAgentProfile, ProfileType,
    UACPIANARegistry, RegistryType, ExtensionCriticality,
    UACPCongestionControl, RateLimitConfig, CongestionState,
    
    # Utility functions
    get_rfc_compliance_status, is_rfc_ready,
    export_all_registries_json, export_registry_markdown
)


async def demo_protocol_layering():
    """Demonstrate formal protocol layering."""
    print("\n🔧 === PROTOCOL LAYERING DEMO ===")
    
    # Create layer configuration
    config = LayerConfig(
        layer_type="transport",
        transport_binding=TransportBinding.UDP_DTLS,
        security_profile="mandatory_core",
        max_message_size=65535,
        timeout=30.0
    )
    
    # Create layer stack
    layer_stack = UACPLayerStack(config)
    print(f"✅ Created layer stack with {config.transport_binding.value} binding")
    
    # Start layers
    await layer_stack.start()
    print("✅ All layers started successfully")
    
    # Stop layers
    await layer_stack.stop()
    print("✅ All layers stopped successfully")
    
    return layer_stack


async def demo_capability_discovery():
    """Demonstrate capability discovery and negotiation."""
    print("\n🤝 === CAPABILITY DISCOVERY DEMO ===")
    
    # Create local agent capabilities
    local_caps = AgentCapabilities(
        agent_id="demo_agent",
        version="3.0.0",
        supported_verbs=["PING", "TELL", "ASK", "OBSERVE"],
        max_payload_size=65535,
        supported_qos=[0, 1, 2],
        supported_auth_methods=["HMAC", "JWT", "CERTIFICATE"],
        supported_content_types=["CBOR", "JSON", "PROTOBUF"],
        supported_security_levels=["BASIC", "ENCRYPTED", "SIGNED", "TLS"],
        supported_transport_bindings=["UDP", "TCP", "WEBSOCKET"],
        supported_features=["basic", "bridges", "monitoring", "priority", "qos2"]
    )
    
    print(f"✅ Created local capabilities for {local_caps.agent_id}")
    print(f"   Supported verbs: {local_caps.supported_verbs}")
    print(f"   Supported QoS: {local_caps.supported_qos}")
    print(f"   Security levels: {local_caps.supported_security_levels}")
    
    # Create negotiation instance
    negotiation = UACPNegotiation(local_caps)
    print("✅ Created negotiation instance")
    
    return negotiation, local_caps


async def demo_status_codes():
    """Demonstrate status codes registry."""
    print("\n📋 === STATUS CODES REGISTRY DEMO ===")
    
    # Get status code information
    ok_code = UACPStatusCodes.OK
    bad_request = UACPStatusCodes.BAD_REQUEST
    negotiation_required = UACPStatusCodes.NEGOTIATION_REQUIRED
    
    print(f"✅ OK status: {ok_code} (0x{ok_code:02X})")
    print(f"✅ Bad Request: {bad_request} (0x{bad_request:02X})")
    print(f"✅ Negotiation Required: {negotiation_required} (0x{negotiation_required:02X})")
    
    # Check categories
    from uacp_lib import is_success, is_client_error, is_negotiation
    
    print(f"✅ OK is success: {is_success(ok_code)}")
    print(f"✅ Bad Request is client error: {is_client_error(bad_request)}")
    print(f"✅ Negotiation Required is negotiation: {is_negotiation(negotiation_required)}")
    
    # Export registry
    registry_md = export_registry_markdown(RegistryType.STATUS_CODES)
    print(f"✅ Status codes registry exported ({len(registry_md)} characters)")
    
    return ok_code, bad_request, negotiation_required


def demo_state_machines():
    """Demonstrate state machines and formal semantics."""
    print("\n🔄 === STATE MACHINES DEMO ===")
    
    # Create state machine context
    context = StateMachineContext(
        message_id="msg_001",
        verb=UACPVerb.ASK,
        qos=1,
        topic="/demo/request",
        payload=b"Hello World",
        source="demo_agent",
        destination="demo_server",
        timestamp=time.time()
    )
    
    # Create ASK state machine
    ask_machine = ASKStateMachine(context)
    print(f"✅ Created ASK state machine for message {context.message_id}")
    print(f"   Initial state: {ask_machine.get_current_state()}")
    
    # Simulate state transitions
    print("\n🔄 Simulating ASK message flow...")
    
    # Send message
    print("   📤 Sending ASK message...")

    # Receive ACK
    ask_machine.receive_ack()
    print(f"   ✅ ACK received, state: {ask_machine.get_current_state()}")

    # Receive response
    response_msg = UACPMessage(
        header=context.message_id,
        verb=UACPVerb.TELL,
        qos=0,
        status_code=UACPStatusCodes.OK,
        options=[],
        payload=b"Response received"
    )

    ask_machine.receive_response(response_msg)
    print(f"   🎯 Response received, state: {ask_machine.get_current_state()}")

    # Show state history
    history = ask_machine.get_state_history()
    print(f"   📊 State transitions: {len(history)}")
    for event in history:
        print(f"      {event.from_state} → {event.to_state} ({event.reason})")
    
    return ask_machine


async def demo_interoperability_profiles():
    """Demonstrate interoperability profiles."""
    print("\n📋 === INTEROPERABILITY PROFILES DEMO ===")
    
    # Get profile specifications
    core_profile = UACPCoreProfile()
    agent_profile = UACPAgentProfile()
    
    print(f"✅ Core Profile: {core_profile.name} v{core_profile.version}")
    print(f"   Target use cases: {', '.join(core_profile.target_use_cases[:2])}...")
    print(f"   Max payload: {core_profile.max_payload_size} bytes")
    print(f"   Max options: {core_profile.max_options}")
    
    print(f"\n✅ Agent Profile: {agent_profile.name} v{agent_profile.version}")
    print(f"   Target use cases: {', '.join(agent_profile.target_use_cases[:2])}...")
    print(f"   Max payload: {agent_profile.max_payload_size} bytes")
    print(f"   Max options: {agent_profile.max_options}")
    
    # Profile comparison
    print(f"\n📊 Profile Comparison:")
    print(f"   Transport bindings: Core={len(core_profile.transport_bindings)}, Agent={len(agent_profile.transport_bindings)}")
    print(f"   Security levels: Core={len(core_profile.security_levels)}, Agent={len(agent_profile.security_levels)}")
    print(f"   Auth methods: Core={len(core_profile.auth_methods)}, Agent={len(agent_profile.auth_methods)}")
    print(f"   Content types: Core={len(core_profile.content_types)}, Agent={len(agent_profile.content_types)}")
    print(f"   QoS levels: Core={len(core_profile.qos_levels)}, Agent={len(agent_profile.qos_levels)}")
    
    return core_profile, agent_profile


async def demo_iana_registry():
    """Demonstrate IANA registry and extension mechanisms."""
    print("\n📚 === IANA REGISTRY DEMO ===")
    
    # Get registry information
    from uacp_lib import get_iana_registry, RegistryType
    
    message_types_registry = get_iana_registry(RegistryType.MESSAGE_TYPES)
    option_codes_registry = get_iana_registry(RegistryType.OPTION_CODES)
    
    print(f"✅ Message Types Registry: {message_types_registry.registry_name}")
    print(f"   Total entries: {len(message_types_registry.entries)}")
    print(f"   Reference: {message_types_registry.reference}")
    
    print(f"\n✅ Option Codes Registry: {option_codes_registry.registry_name}")
    print(f"   Total entries: {len(option_codes_registry.entries)}")
    print(f"   Reference: {option_codes_registry.reference}")
    
    # Show some entries
    print(f"\n📋 Sample Message Types:")
    for code, entry in list(message_types_registry.entries.items())[:2]:
        print(f"   {code}: {entry.name} - {entry.description}")
    
    print(f"\n📋 Sample Option Codes:")
    for code, entry in list(option_codes_registry.entries.items())[:2]:
        print(f"   {code}: {entry.name} - {entry.description}")
    
    # Export all registries
    all_registries_json = export_all_registries_json()
    print(f"\n✅ All registries exported ({len(all_registries_json)} characters)")
    
    return message_types_registry, option_codes_registry


async def demo_congestion_control():
    """Demonstrate congestion control and resource management."""
    print("\n🚦 === CONGESTION CONTROL DEMO ===")
    
    # Create congestion control configuration
    config = RateLimitConfig(
        max_messages_per_second=100,
        burst_size=20,
        policy="throttle",
        fairness_enabled=True,
        per_agent_limits=True
    )
    
    # Create congestion control instance
    congestion_control = UACPCongestionControl(config)
    print(f"✅ Created congestion control with {config.max_messages_per_second} msg/s limit")
    
    # Simulate message sending
    print("\n📤 Simulating message sending...")
    
    for i in range(25):  # Try to send more than burst size
        agent_id = f"agent_{i % 5}"  # 5 different agents
        
        if congestion_control.can_send_message(agent_id):
            congestion_control.record_message_sent(agent_id, latency=0.01)
            print(f"   ✅ Message {i+1} sent by {agent_id}")
        else:
            congestion_control.record_message_dropped(agent_id, "Rate limit exceeded")
            print(f"   ❌ Message {i+1} dropped for {agent_id} (rate limit)")
    
    # Get congestion summary
    summary = congestion_control.get_congestion_summary()
    print(f"\n📊 Congestion Summary:")
    print(f"   State: {summary['congestion_state']}")
    print(f"   Level: {summary['congestion_level']:.2f}")
    print(f"   Window: {summary['congestion_window']}")
    print(f"   Message rate: {summary['metrics']['message_rate']:.2f} msg/s")
    print(f"   Drop rate: {summary['metrics']['drop_rate']:.2f} msg/s")
    
    # Show fairness scores
    print(f"\n⚖️  Fairness Scores:")
    for agent_id in range(5):
        agent_name = f"agent_{agent_id}"
        fairness_score = congestion_control.get_fairness_score(agent_name)
        should_throttle = congestion_control.should_throttle_agent(agent_name)
        print(f"   {agent_name}: {fairness_score:.2f} {'🚫' if should_throttle else '✅'}")
    
    return congestion_control


async def main():
    """Main demo function."""
    print("🚀 µACP RFC Compliance Demo")
    print("=" * 50)
    
    # Check RFC readiness
    rfc_status = get_rfc_compliance_status()
    rfc_ready = is_rfc_ready()
    
    print(f"\n📋 RFC Compliance Status:")
    for feature, status in rfc_status.items():
        if feature != "rfc_readiness":
            print(f"   {feature.replace('_', ' ').title()}: {status}")
    
    print(f"\n🎯 RFC Readiness: {'✅ COMPLETE' if rfc_ready else '❌ INCOMPLETE'}")
    
    if not rfc_ready:
        print("❌ Some RFC requirements are not implemented!")
        return
    
    print("✅ All RFC requirements are implemented!")
    
    # Run demos
    try:
        # Protocol layering demo
        await demo_protocol_layering()
        
        # Capability discovery demo
        await demo_capability_discovery()
        
        # Status codes demo
        await demo_status_codes()
        
        # State machines demo
        await demo_state_machines()
        
        # Interoperability profiles demo
        await demo_interoperability_profiles()
        
        # IANA registry demo
        await demo_iana_registry()
        
        # Congestion control demo
        await demo_congestion_control()
        
        print("\n🎉 All RFC compliance demos completed successfully!")
        print("\n📚 µACP is now RFC-ready with:")
        print("   • Formal protocol layering")
        print("   • Negotiation & capability discovery")
        print("   • Complete status codes registry")
        print("   • Formal state machines")
        print("   • Interoperability profiles")
        print("   • IANA registry definitions")
        print("   • Extension mechanisms")
        print("   • Resource & congestion control")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
