"""
µACP P2P Discovery Example

Demonstrates multiple agents discovering each other via UDP broadcast.
Shows peer registry and symmetric P2P communication.

Usage:
    Terminal 1: python3 examples/p2p_discovery.py --name Agent1 --port 8001
    Terminal 2: python3 examples/p2p_discovery.py --name Agent2 --port 8002
    Terminal 3: python3 examples/p2p_discovery.py --name Agent3 --port 8003
"""

import asyncio
import argparse
from src.miuacp.agent import UACPAgent
from src.miuacp.protocol import UACPVerb


async def run_discovery_agent(name: str, port: int):
    """Run agent with discovery capabilities."""
    agent = UACPAgent(
        agent_id=f"agent-{port}",
        name=name,
        host="0.0.0.0",
        port=port
    )
    
    # Track discovered agents
    discovered_agents = set()
    
    async def handle_ping(msg, sender_host, sender_port):
        peer_key = f"{sender_host}:{sender_port}"
        if peer_key not in discovered_agents:
            discovered_agents.add(peer_key)
            print(f"  🔍 Discovered new peer: {sender_host}:{sender_port}")
    
    async def handle_tell(msg, sender_host, sender_port):
        print(f"  💬 Message from {sender_host}:{sender_port}")
    
    agent.add_message_handler(UACPVerb.PING, handle_ping)
    agent.add_message_handler(UACPVerb.TELL, handle_tell)
    
    try:
        # Start agent
        success = await agent.start()
        if not success:
            print(f"Failed to start {name}")
            return
        
        print(f"🚀 {name} started on port {agent.port}")
        print(f"   Agent ID: {agent.agent_id}")
        print()
        
        # Phase 1: Discovery (first 5 seconds)
        print("Phase 1: Peer Discovery")
        print("=" * 50)
        
        for i in range(5):
            # Try to discover peers on common ports
            for discover_port in [8001, 8002, 8003, 8004, 8005]:
                if discover_port != port:
                    await agent.ping("127.0.0.1", discover_port)
            
            await asyncio.sleep(1.0)
        
        # Show discovered peers
        peers = agent.get_discovered_peers()
        print(f"\n✅ Discovery complete!")
        print(f"   Found {len(peers)} peer(s):")
        for peer in peers:
            print(f"     - {peer.host}:{peer.port} (last seen: {peer.last_seen:.1f}s)")
        
        # Phase 2: Communication (next 10 seconds)
        print(f"\nPhase 2: P2P Communication")
        print("=" * 50)
        
        for i in range(5):
            # Send message to all discovered peers
            for peer in peers:
                message = f"Hello from {name} (message #{i+1})"
                await agent.tell(peer.host, peer.port, "greeting", {"text": message})
                print(f"  → Sent to {peer.host}:{peer.port}: {message}")
            
            await asyncio.sleep(2.0)
        
        # Final statistics
        print(f"\n📊 Final Statistics for {name}")
        print("=" * 50)
        stats = agent.get_stats()
        print(f"   Messages sent:     {stats['messages_sent']}")
        print(f"   Messages received: {stats['messages_received']}")
        print(f"   Bytes sent:        {stats['bytes_sent']}")
        print(f"   Bytes received:    {stats['bytes_received']}")
        print(f"   Peers discovered:  {stats['peers_discovered']}")
        print(f"   Errors:            {stats['errors']}")
        
        # Wait a bit before stopping
        await asyncio.sleep(2.0)
        
    finally:
        await agent.stop()
        print(f"\n👋 {name} stopped")


def main():
    parser = argparse.ArgumentParser(description="µACP P2P Discovery Example")
    parser.add_argument("--name", required=True, help="Agent name")
    parser.add_argument("--port", type=int, required=True, help="Port for this agent")
    
    args = parser.parse_args()
    
    asyncio.run(run_discovery_agent(args.name, args.port))


if __name__ == "__main__":
    main()
