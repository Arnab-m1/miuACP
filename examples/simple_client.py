#!/usr/bin/env python3
"""
Simple µACP Client Example

This example demonstrates:
1. Creating a µACP client
2. Connecting to agents
3. Sending different types of messages
4. Handling responses
"""

import asyncio
import time
from uacp_lib import UACPClient, UACPVerb, UACPOptionType


async def main():
    """Main example function."""
    print("🚀 Starting Simple µACP Client Example")
    
    # Create client
    client = UACPClient(default_timeout=10.0, max_retries=2)
    
    # Agent to connect to
    agent_host = "127.0.0.1"  # Localhost
    agent_port = 8888
    
    try:
        print(f"🔌 Connecting to agent at {agent_host}:{agent_port}")
        
        # Connect to agent
        if await client.connect(agent_host, agent_port):
            print("✅ Connected to agent!")
        else:
            print("❌ Failed to connect to agent")
            return
        
        # Test PING
        print("\n🏓 Testing PING...")
        if await client.ping(agent_host, agent_port):
            print("✅ PING successful")
        else:
            print("❌ PING failed")
        
        # Test ASK for temperature
        print("\n🌡️  Testing ASK for temperature...")
        response = await client.ask_agent(
            agent_host, agent_port, 
            topic="sensors/temperature",
            data={"request": "current_temperature"}
        )
        
        if response:
            print("✅ Temperature response received:")
            if response.payload:
                try:
                    import cbor2
                    data = cbor2.loads(response.payload)
                    print(f"   Temperature: {data.get('value', 'N/A')} {data.get('unit', 'N/A')}")
                    print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
                except Exception as e:
                    print(f"   Raw payload: {response.payload}")
        else:
            print("❌ No temperature response")
        
        # Test ASK for humidity
        print("\n💧 Testing ASK for humidity...")
        response = await client.ask_agent(
            agent_host, agent_port, 
            topic="sensors/humidity",
            data={"request": "current_humidity"}
        )
        
        if response:
            print("✅ Humidity response received:")
            if response.payload:
                try:
                    import cbor2
                    data = cbor2.loads(response.payload)
                    print(f"   Humidity: {data.get('value', 'N/A')} {data.get('unit', 'N/A')}")
                    print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
                except Exception as e:
                    print(f"   Raw payload: {response.payload}")
        else:
            print("❌ No humidity response")
        
        # Test ASK for analysis
        print("\n🧮 Testing ASK for analysis...")
        response = await client.ask_agent(
            agent_host, agent_port, 
            topic="compute/analysis",
            data={"request": "statistical_analysis", "data_points": 100}
        )
        
        if response:
            print("✅ Analysis response received:")
            if response.payload:
                try:
                    import cbor2
                    data = cbor2.loads(response.payload)
                    result = data.get('result', {})
                    print(f"   Analysis: {data.get('analysis', 'N/A')}")
                    print(f"   Mean: {result.get('mean', 'N/A')}")
                    print(f"   Std Dev: {result.get('std_dev', 'N/A')}")
                    print(f"   Range: {result.get('min', 'N/A')} - {result.get('max', 'N/A')}")
                except Exception as e:
                    print(f"   Raw payload: {response.payload}")
        else:
            print("❌ No analysis response")
        
        # Test TELL (inform)
        print("\n📢 Testing TELL (inform)...")
        if await client.tell_agent(
            agent_host, agent_port,
            topic="system/status",
            data={"status": "client_test_complete", "timestamp": time.time()}
        ):
            print("✅ TELL message sent successfully")
        else:
            print("❌ Failed to send TELL message")
        
        # Test OBSERVE (subscribe)
        print("\n👁️  Testing OBSERVE (subscribe)...")
        if await client.observe_agent(
            agent_host, agent_port,
            topic="sensors/alerts"
        ):
            print("✅ OBSERVE subscription successful")
        else:
            print("❌ Failed to subscribe")
        
        # Wait a bit for any incoming messages
        print("\n⏳ Waiting for incoming messages...")
        await asyncio.sleep(5)
        
        # Print client statistics
        print("\n📊 Client Statistics:")
        stats = client.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Print connection information
        print("\n🔗 Connection Information:")
        connections = client.get_connection_info()
        for conn in connections:
            print(f"   {conn['host']}:{conn['port']} - {conn['message_count']} messages")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Clean up
        print("\n🧹 Cleaning up...")
        await client.close()
        print("✅ Client closed")


if __name__ == "__main__":
    asyncio.run(main())
