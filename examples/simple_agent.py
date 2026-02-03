#!/usr/bin/env python3
"""
Simple µACP Agent Example

This example demonstrates:
1. Creating a µACP agent
2. Adding capabilities and handlers
3. Starting the agent
4. Basic communication patterns
"""

import asyncio
import time
from uacp_lib import UACPAgent, UACPCapability, UACPVerb, UACPOptionType


async def main():
    """Main example function."""
    print("🚀 Starting Simple µACP Agent Example")
    
    # Create agent capabilities
    sensor_capability = UACPCapability(
        name="sensor_reading",
        description="Read sensor data from environment",
        topics=["sensors/temperature", "sensors/humidity", "sensors/pressure"],
        input_format="JSON",
        output_format="JSON"
    )
    
    computation_capability = UACPCapability(
        name="data_processing",
        description="Process and analyze sensor data",
        topics=["compute/analysis", "compute/statistics"],
        input_format="JSON",
        output_format="JSON"
    )
    
    # Create the agent
    agent = UACPAgent(
        name="Simple Sensor Agent",
        port=8888,
        capabilities=[sensor_capability, computation_capability]
    )
    
    # Add topic handlers
    @agent.add_topic_handler("sensors/temperature")
    async def handle_temperature(message, client_host, client_port, topic, conversation_id):
        """Handle temperature sensor requests."""
        print(f"🌡️  Handling temperature request from {client_host}:{client_port}")
        
        # Simulate temperature reading
        temperature = 22.5 + (time.time() % 10)  # Varying temperature
        response = {
            "sensor": "temperature",
            "value": round(temperature, 1),
            "unit": "°C",
            "timestamp": time.time()
        }
        
        return response
    
    @agent.add_topic_handler("sensors/humidity")
    async def handle_humidity(message, client_host, client_port, topic, conversation_id):
        """Handle humidity sensor requests."""
        print(f"💧 Handling humidity request from {client_host}:{client_port}")
        
        # Simulate humidity reading
        humidity = 45.0 + (time.time() % 20)  # Varying humidity
        response = {
            "sensor": "humidity",
            "value": round(humidity, 1),
            "unit": "%",
            "timestamp": time.time()
        }
        
        return response
    
    @agent.add_topic_handler("compute/analysis")
    async def handle_analysis(message, client_host, client_port, topic, conversation_id):
        """Handle data analysis requests."""
        print(f"🧮 Handling analysis request from {client_host}:{client_port}")
        
        # Simulate data analysis
        response = {
            "analysis": "statistical_summary",
            "result": {
                "mean": 23.4,
                "std_dev": 2.1,
                "min": 20.1,
                "max": 26.8
            },
            "timestamp": time.time()
        }
        
        return response
    
    # Add custom verb handlers
    @agent.add_verb_handler(UACPVerb.PING)
    async def custom_ping_handler(message, client_host, client_port):
        """Custom PING handler."""
        print(f"🏓 Custom PING from {client_host}:{client_port}")
    
    # Start the agent
    print(f"📡 Starting agent on port {agent.server.port}")
    await agent.start()
    
    try:
        print("✅ Agent is running! Press Ctrl+C to stop.")
        print("\n📋 Agent Information:")
        agent_info = agent.get_agent_info()
        print(f"   ID: {agent_info.agent_id}")
        print(f"   Name: {agent_info.name}")
        print(f"   Capabilities: {[cap.name for cap in agent_info.capabilities]}")
        print(f"   Topics: {agent_info.topics}")
        
        print("\n🔄 Agent is listening for messages...")
        print("   - Send PING to check liveness")
        print("   - Send ASK to sensors/temperature for temperature data")
        print("   - Send ASK to sensors/humidity for humidity data")
        print("   - Send ASK to compute/analysis for data analysis")
        
        # Keep the agent running
        while True:
            await asyncio.sleep(1)
            
            # Print stats every 10 seconds
            if int(time.time()) % 10 == 0:
                stats = agent.get_stats()
                print(f"\n📊 Stats: {stats['messages_received']} received, {stats['messages_sent']} sent")
    
    except KeyboardInterrupt:
        print("\n🛑 Stopping agent...")
    finally:
        await agent.stop()
        print("✅ Agent stopped")


if __name__ == "__main__":
    asyncio.run(main())
