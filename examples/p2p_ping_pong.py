"""
µACP P2P Ping-Pong Example

Demonstrates two agents communicating directly in peer-to-peer mode.
No client/server distinction - both agents can send and receive.

Usage:
    Terminal 1: python3 examples/p2p_ping_pong.py --role ping --port 8001
    Terminal 2: python3 examples/p2p_ping_pong.py --role pong --port 8002
"""

import asyncio
import sys
import argparse
from src.miuacp.agent import UACPAgent
from src.miuacp.protocol import UACPVerb


async def run_ping_agent(port: int, peer_port: int):
    """Run agent in PING role."""
    agent = UACPAgent(
        agent_id="ping-agent",
        name="Ping Agent",
        host="0.0.0.0",
        port=port
    )
    
    pong_count = 0
    
    async def handle_tell(msg, sender_host, sender_port):
        nonlocal pong_count
        pong_count += 1
        print(f"  ← Received PONG #{pong_count} from {sender_host}:{sender_port}")
    
    agent.add_message_handler(UACPVerb.TELL, handle_tell)
    
    try:
        # Start agent
        success = await agent.start()
        if not success:
            print("Failed to start Ping agent")
            return
        
        print(f"🏓 Ping Agent started on port {agent.port}")
        print(f"   Sending PINGs to Pong Agent on port {peer_port}...\n")
        
        # Send 10 pings
        for i in range(1, 11):
            print(f"  → Sending PING #{i}")
            await agent.tell("127.0.0.1", peer_port, "ping", {"count": i})
            await asyncio.sleep(1.0)
        
        # Wait for final pongs
        await asyncio.sleep(2.0)
        
        # Show statistics
        stats = agent.get_stats()
        print(f"\n📊 Statistics:")
        print(f"   Messages sent: {stats['messages_sent']}")
        print(f"   Messages received: {stats['messages_received']}")
        print(f"   Pongs received: {pong_count}")
        print(f"   Bytes sent: {stats['bytes_sent']}")
        print(f"   Bytes received: {stats['bytes_received']}")
        
    finally:
        await agent.stop()


async def run_pong_agent(port: int, peer_port: int):
    """Run agent in PONG role."""
    agent = UACPAgent(
        agent_id="pong-agent",
        name="Pong Agent",
        host="0.0.0.0",
        port=port
    )
    
    ping_count = 0
    
    async def handle_tell(msg, sender_host, sender_port):
        nonlocal ping_count
        ping_count += 1
        print(f"  ← Received PING #{ping_count} from {sender_host}:{sender_port}")
        
        # Send PONG back
        print(f"  → Sending PONG #{ping_count}")
        await agent.tell(sender_host, sender_port, "pong", {"count": ping_count})
    
    agent.add_message_handler(UACPVerb.TELL, handle_tell)
    
    try:
        # Start agent
        success = await agent.start()
        if not success:
            print("Failed to start Pong agent")
            return
        
        print(f"🏓 Pong Agent started on port {agent.port}")
        print(f"   Waiting for PINGs from Ping Agent...\n")
        
        # Run for 15 seconds
        await asyncio.sleep(15.0)
        
        # Show statistics
        stats = agent.get_stats()
        print(f"\n📊 Statistics:")
        print(f"   Messages sent: {stats['messages_sent']}")
        print(f"   Messages received: {stats['messages_received']}")
        print(f"   Pings received: {ping_count}")
        print(f"   Bytes sent: {stats['bytes_sent']}")
        print(f"   Bytes received: {stats['bytes_received']}")
        
    finally:
        await agent.stop()


def main():
    parser = argparse.ArgumentParser(description="µACP P2P Ping-Pong Example")
    parser.add_argument("--role", choices=["ping", "pong"], required=True,
                       help="Role: ping (sends) or pong (responds)")
    parser.add_argument("--port", type=int, required=True,
                       help="Port for this agent")
    parser.add_argument("--peer-port", type=int,
                       help="Port of peer agent (required for ping role)")
    
    args = parser.parse_args()
    
    if args.role == "ping":
        if not args.peer_port:
            print("Error: --peer-port required for ping role")
            sys.exit(1)
        asyncio.run(run_ping_agent(args.port, args.peer_port))
    else:
        peer_port = args.peer_port or 8001  # Default to ping agent port
        asyncio.run(run_pong_agent(args.port, peer_port))


if __name__ == "__main__":
    main()
